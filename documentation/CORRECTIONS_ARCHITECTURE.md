# 🔧 Corrections Architecture Pulse - Standardisation

> **Date:** 30 Janvier 2026  
> **Statut:** CRITIQUE - À implémenter avant toute nouvelle feature  
> **Version:** 3.1.0

---

## 📋 Résumé Exécutif

Ce document corrige les **incohérences majeures** identifiées dans l'architecture et standardise les approches sur :
1. ✅ **Baselines robustes** (median/IQR au lieu de mean/std)
2. ✅ **Z-Score robuste** partout (pas de mix classique/robuste)
3. ✅ **Architecture food diary extensible** (logs + items + photos)
4. ✅ **FatSecret comme provider** (pas comme dépendance critique)
5. ✅ **5 améliorations rapides** (versioning, quality flags, etc.)

---

## A) Standardisation Baselines : Median/IQR (Robust Statistics)

### ❌ Problème Identifié

**Incohérence actuelle :**
- Documentation décrit `mean` + `std` (statistiques classiques)
- Code des états latents utilise `median` + `IQR` (statistiques robustes)
- Risque : anomalies détectées différemment selon le contexte

**Pourquoi c'est critique :**
Les statistiques classiques (mean/std) sont sensibles aux outliers. Si un utilisateur a eu 2 jours avec HRV anormale sur 90 jours, le `mean` sera faussé. Les statistiques robustes (median/IQR) ignorent les outliers.

### ✅ Solution : Baselines Robustes Partout

**Nouveau Schéma Table `user_baselines` :**

```sql
CREATE TABLE IF NOT EXISTS user_baselines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    baseline_type TEXT NOT NULL, -- 'hrv', 'heart_rate', 'sleep_duration', etc.
    
    -- Statistiques ROBUSTES (principal)
    median FLOAT NOT NULL,       -- Médiane (Q2)
    iqr FLOAT NOT NULL,          -- Interquartile Range (Q3 - Q1)
    p25 FLOAT NOT NULL,          -- Percentile 25 (Q1)
    p75 FLOAT NOT NULL,          -- Percentile 75 (Q3)
    
    -- Statistiques CLASSIQUES (optionnel, pour graphiques)
    mean FLOAT,                  -- Moyenne arithmétique
    std FLOAT,                   -- Écart-type
    
    -- Métadonnées
    sample_count INTEGER NOT NULL,
    confidence TEXT NOT NULL,    -- 'low' | 'medium' | 'high'
    model_version TEXT NOT NULL DEFAULT 'baseline_v2_robust',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE(user_id, baseline_type, model_version)
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_baselines_user_type 
    ON user_baselines(user_id, baseline_type);

-- Constraint de confiance basée sur sample_count
ALTER TABLE user_baselines ADD CONSTRAINT check_confidence
    CHECK (
        (sample_count >= 60 AND confidence = 'high') OR
        (sample_count >= 30 AND sample_count < 60 AND confidence = 'medium') OR
        (sample_count >= 10 AND sample_count < 30 AND confidence = 'low')
    );
```

**Calcul des Baselines Robustes :**

```python
# backend/services/baseline_calculator.py

import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class RobustBaselineCalculator:
    """
    Calcule les baselines avec statistiques robustes (median/IQR)
    """
    
    def calculate_baselines(
        self, 
        user_id: str, 
        lookback_days: int = 90
    ) -> Dict[str, Dict]:
        """
        Calcule toutes les baselines pour un utilisateur
        
        Returns:
            {
                'hrv': {
                    'median': 65.2,
                    'iqr': 12.5,
                    'p25': 58.5,
                    'p75': 71.0,
                    'mean': 64.8,  # optionnel
                    'std': 8.3,    # optionnel
                    'sample_count': 85,
                    'confidence': 'high'
                },
                ...
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Récupérer données brutes
        biometrics = self.get_user_biometrics(
            user_id, 
            start_date, 
            end_date
        )
        
        baselines = {}
        
        # Grouper par metric_type
        for metric_type, values in self._group_by_metric(biometrics).items():
            if len(values) < 10:  # Minimum 10 points
                continue
            
            # Calculer statistiques robustes
            values_array = np.array(values)
            
            median = float(np.median(values_array))
            p25 = float(np.percentile(values_array, 25))
            p75 = float(np.percentile(values_array, 75))
            iqr = p75 - p25
            
            # Statistiques classiques (optionnel)
            mean = float(np.mean(values_array))
            std = float(np.std(values_array))
            
            # Confiance
            sample_count = len(values)
            if sample_count >= 60:
                confidence = 'high'
            elif sample_count >= 30:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            baselines[metric_type] = {
                'median': round(median, 2),
                'iqr': round(iqr, 2),
                'p25': round(p25, 2),
                'p75': round(p75, 2),
                'mean': round(mean, 2),
                'std': round(std, 2),
                'sample_count': sample_count,
                'confidence': confidence
            }
        
        return baselines
    
    def _group_by_metric(self, biometrics: List[Dict]) -> Dict[str, List[float]]:
        """Groupe les biometrics par metric_type"""
        grouped = {}
        for b in biometrics:
            metric_type = b['metric_type']
            if metric_type not in grouped:
                grouped[metric_type] = []
            grouped[metric_type].append(b['value'])
        return grouped
```

**Migration SQL :**

```sql
-- migrations/020_robust_baselines.sql

-- Renommer ancienne table (backup)
ALTER TABLE user_baselines RENAME TO user_baselines_old;

-- Créer nouvelle table avec structure robuste
CREATE TABLE user_baselines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    baseline_type TEXT NOT NULL,
    median FLOAT NOT NULL,
    iqr FLOAT NOT NULL,
    p25 FLOAT NOT NULL,
    p75 FLOAT NOT NULL,
    mean FLOAT,
    std FLOAT,
    sample_count INTEGER NOT NULL,
    confidence TEXT NOT NULL,
    model_version TEXT NOT NULL DEFAULT 'baseline_v2_robust',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, baseline_type, model_version)
);

-- Migrer données existantes (si possible)
-- Note: Si anciennes baselines utilisent mean/std, on peut les garder
-- mais calculer median/IQR approximatifs ou forcer recalcul complet

-- Option 1: Forcer recalcul complet (recommandé)
-- Les baselines seront recalculées au prochain cron

-- Option 2: Migrer avec approximations (si besoin de continuité)
INSERT INTO user_baselines (
    user_id, 
    baseline_type, 
    median, 
    iqr, 
    p25, 
    p75,
    mean,
    std,
    sample_count, 
    confidence, 
    model_version
)
SELECT 
    user_id,
    baseline_type,
    mean as median,  -- Approximation: mean ≈ median si distribution normale
    std * 1.35 as iqr,  -- Approximation: IQR ≈ 1.35 * std pour distribution normale
    mean - (std * 0.675) as p25,  -- Q1 ≈ mean - 0.675*std
    mean + (std * 0.675) as p75,  -- Q3 ≈ mean + 0.675*std
    mean,
    std,
    sample_count,
    confidence,
    'baseline_v2_robust_migrated'
FROM user_baselines_old;

-- Indexer
CREATE INDEX idx_baselines_user_type 
    ON user_baselines(user_id, baseline_type);

-- RLS
ALTER TABLE user_baselines ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own baselines" ON user_baselines
    FOR SELECT USING (auth.uid() = user_id);
```

---

## B) Z-Score Robuste Partout (Pas de Mix)

### ❌ Problème Identifié

**Incohérence actuelle :**
- Documentation anomalies : `Z = (x - mean) / std` (classique)
- États latents : `Z_robust = (x - median) / IQR` (robust)
- Risque : Une métrique peut être "anomalie" mais "recovery OK" → confusion utilisateur

### ✅ Solution : Z-Score Robuste Unifié

**Formule Standardisée :**

```javascript
// Z-Score Robuste
Z_robust = (x - baseline_median) / (baseline_iqr / 1.349)

// Explication du diviseur 1.349:
// Pour une distribution normale, IQR ≈ 1.349 * σ
// Donc IQR / 1.349 ≈ σ
// Cela rend Z_robust comparable à Z_classique
```

**Implémentation Backend :**

```python
# backend/services/anomaly_detector.py

class RobustAnomalyDetector:
    """
    Détection d'anomalies avec Z-Score robuste
    """
    
    WEIGHTS = {
        'hrv': 3,
        'heart_rate': 2,
        'sleep_duration': 2,
        'body_temperature': 2,
        'spo2': 2,
        'stress': 1,
        'glucose': 1,
        'steps': 1
    }
    
    def detect_anomalies(
        self,
        user_id: str,
        current_metrics: Dict[str, float],
        baselines: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Détecte anomalies avec Z-Score robuste
        
        Args:
            current_metrics: {'hrv': 45.2, 'heart_rate': 72, ...}
            baselines: {
                'hrv': {
                    'median': 65.2,
                    'iqr': 12.5,
                    'p25': 58.5,
                    'p75': 71.0
                },
                ...
            }
        
        Returns:
            [
                {
                    'metric': 'hrv',
                    'value': 45.2,
                    'z_score_robust': -2.38,
                    'weight': 3,
                    'priority': 7.14,
                    'direction': 'below',
                    'baseline': {...}
                },
                ...
            ]
        """
        anomalies = []
        
        for metric, value in current_metrics.items():
            if metric not in baselines:
                continue
            
            baseline = baselines[metric]
            median = baseline['median']
            iqr = baseline['iqr']
            
            # Éviter division par zéro
            if iqr == 0:
                continue
            
            # Z-Score ROBUSTE
            # Diviseur 1.349 pour rendre comparable à Z classique
            z_score_robust = (value - median) / (iqr / 1.349)
            
            # Filtrer: |Z| > 2σ
            if abs(z_score_robust) > 2.0:
                weight = self.WEIGHTS.get(metric, 1)
                priority = abs(z_score_robust) * weight
                direction = 'above' if z_score_robust > 0 else 'below'
                
                anomalies.append({
                    'metric': metric,
                    'value': round(value, 2),
                    'z_score_robust': round(z_score_robust, 2),
                    'weight': weight,
                    'priority': round(priority, 2),
                    'direction': direction,
                    'baseline': {
                        'median': median,
                        'iqr': iqr,
                        'p25': baseline['p25'],
                        'p75': baseline['p75']
                    }
                })
        
        # Trier par priorité décroissante
        anomalies.sort(key=lambda x: x['priority'], reverse=True)
        
        return anomalies
```

**Implémentation Mobile :**

```typescript
// mobile/src/services/ZScoreCalculator.ts

export class RobustZScoreCalculator {
  /**
   * Calcule le Z-Score ROBUSTE
   * Z = (x - median) / (IQR / 1.349)
   */
  calculateZScoreRobust(
    value: number,
    median: number,
    iqr: number
  ): number {
    if (iqr === 0) return 0;
    
    // Normalisation IQR → σ équivalent
    const sigma_equivalent = iqr / 1.349;
    
    return (value - median) / sigma_equivalent;
  }

  /**
   * Détecte anomalies avec Z-Score robuste
   */
  detectAnomalies(
    currentMetrics: CurrentMetrics,
    baselines: RobustBaselines
  ): Anomaly[] {
    const anomalies: Anomaly[] = [];
    
    // Mapper currentMetrics vers array
    const metricsMap: Record<string, number | null> = {
      hrv: currentMetrics.hrv,
      heart_rate: currentMetrics.heart_rate,
      sleep_duration: currentMetrics.sleep?.duration,
      body_temperature: currentMetrics.body_temperature,
      spo2: currentMetrics.spo2,
      // ... autres métriques
    };
    
    // Calculer Z-Score robuste pour chaque métrique
    for (const [metricKey, value] of Object.entries(metricsMap)) {
      if (value === null || value === undefined) continue;
      
      const baseline = baselines[metricKey as keyof RobustBaselines];
      if (!baseline) continue;
      
      const { median, iqr, weight } = baseline;
      
      if (iqr === 0) continue;
      
      const zScoreRobust = this.calculateZScoreRobust(value, median, iqr);
      
      // Filtrer: |Z| > 2
      if (Math.abs(zScoreRobust) > 2.0) {
        const priority = Math.abs(zScoreRobust) * weight;
        const direction: 'above' | 'below' = zScoreRobust > 0 ? 'above' : 'below';
        
        anomalies.push({
          metric: metricKey,
          value: Math.round(value * 100) / 100,
          z_score_robust: Math.round(zScoreRobust * 100) / 100,
          weight,
          priority: Math.round(priority * 100) / 100,
          direction,
          baseline: {
            median: Math.round(median * 100) / 100,
            iqr: Math.round(iqr * 100) / 100,
            p25: baseline.p25,
            p75: baseline.p75
          }
        });
      }
    }
    
    // Trier par priorité
    anomalies.sort((a, b) => b.priority - a.priority);
    
    return anomalies;
  }
}
```

**Types TypeScript :**

```typescript
// mobile/src/types/baselines.ts

export interface RobustBaseline {
  median: number;
  iqr: number;
  p25: number;
  p75: number;
  mean?: number;    // Optionnel, pour graphiques
  std?: number;     // Optionnel, pour graphiques
  sample_count: number;
  confidence: 'low' | 'medium' | 'high';
}

export interface RobustBaselines {
  hrv?: RobustBaseline;
  heart_rate?: RobustBaseline;
  sleep_duration?: RobustBaseline;
  body_temperature?: RobustBaseline;
  spo2?: RobustBaseline;
  // ... autres métriques
}

export interface Anomaly {
  metric: string;
  value: number;
  z_score_robust: number;  // Changé de z_score à z_score_robust
  weight: number;
  priority: number;
  direction: 'above' | 'below';
  baseline: {
    median: number;
    iqr: number;
    p25: number;
    p75: number;
  };
}
```

---

## C) Architecture Food Diary Extensible

### ❌ Problème Identifié

**Schéma actuel trop simple :**
```sql
food_diary_entries (
    id,
    user_id,
    meal_type,      -- breakfast/lunch/dinner/snack
    food_name,      -- UN SEUL aliment par ligne
    calories,
    ...
)
```

**Limitations :**
- ❌ Pas de photo de repas
- ❌ Pas de repas multi-items (ex: "Poulet + riz + légumes")
- ❌ Pas d'édition de repas complet
- ❌ Pas de regroupement logique

### ✅ Solution : Architecture 3 Tables

**Nouveau Schéma :**

```sql
-- ============================================
-- 1. FOOD_LOGS : Un repas / un événement
-- ============================================

CREATE TABLE IF NOT EXISTS food_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    meal_type TEXT NOT NULL,  -- 'breakfast' | 'lunch' | 'dinner' | 'snack'
    logged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes TEXT,               -- Notes utilisateur
    
    -- Agrégation automatique (mise à jour par trigger)
    total_calories FLOAT DEFAULT 0,
    total_protein FLOAT DEFAULT 0,
    total_carbs FLOAT DEFAULT 0,
    total_fat FLOAT DEFAULT 0,
    total_fiber FLOAT DEFAULT 0,
    total_sugar FLOAT DEFAULT 0,
    total_sodium FLOAT DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index
CREATE INDEX idx_food_logs_user_date 
    ON food_logs(user_id, logged_at DESC);

CREATE INDEX idx_food_logs_user_meal 
    ON food_logs(user_id, meal_type, logged_at DESC);

-- RLS
ALTER TABLE food_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food logs" ON food_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own food logs" ON food_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own food logs" ON food_logs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own food logs" ON food_logs
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================
-- 2. FOOD_LOG_ITEMS : Items individuels
-- ============================================

CREATE TABLE IF NOT EXISTS food_log_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    food_log_id UUID REFERENCES food_logs(id) ON DELETE CASCADE NOT NULL,
    
    -- Source
    source TEXT NOT NULL,     -- 'fatsecret' | 'manual' | 'photo_analysis'
    fatsecret_id TEXT,        -- ID FatSecret (si applicable)
    
    -- Description
    food_name TEXT NOT NULL,
    serving_size FLOAT NOT NULL,
    serving_unit TEXT NOT NULL,  -- 'g' | 'ml' | 'pièce' | 'tasse' | etc.
    
    -- Nutrition (par portion)
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL DEFAULT 0,
    carbs FLOAT NOT NULL DEFAULT 0,
    fat FLOAT NOT NULL DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    sugar FLOAT DEFAULT 0,
    sodium FLOAT DEFAULT 0,
    
    -- Ordre d'affichage
    display_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index
CREATE INDEX idx_food_log_items_log 
    ON food_log_items(food_log_id, display_order);

-- RLS (hérité via food_logs)
ALTER TABLE food_log_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food log items" ON food_log_items
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own food log items" ON food_log_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own food log items" ON food_log_items
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own food log items" ON food_log_items
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );


-- ============================================
-- 3. FOOD_PHOTOS : Photos de repas
-- ============================================

CREATE TABLE IF NOT EXISTS food_photos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    food_log_id UUID REFERENCES food_logs(id) ON DELETE CASCADE NOT NULL,
    
    -- Stockage
    storage_path TEXT NOT NULL,  -- Chemin dans Supabase Storage
    thumbnail_path TEXT,         -- Thumbnail (optionnel)
    
    -- Analyse IA (optionnel, future)
    analysis_status TEXT DEFAULT 'pending',  -- 'pending' | 'analyzed' | 'failed'
    analysis_result JSONB,       -- Résultat GPT-4 Vision (future)
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index
CREATE INDEX idx_food_photos_log 
    ON food_photos(food_log_id);

-- RLS
ALTER TABLE food_photos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food photos" ON food_photos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own food photos" ON food_photos
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );


-- ============================================
-- 4. TRIGGERS : Mise à jour automatique totaux
-- ============================================

CREATE OR REPLACE FUNCTION update_food_log_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Recalculer les totaux du food_log
    UPDATE food_logs
    SET
        total_calories = COALESCE((
            SELECT SUM(calories)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_protein = COALESCE((
            SELECT SUM(protein)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_carbs = COALESCE((
            SELECT SUM(carbs)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_fat = COALESCE((
            SELECT SUM(fat)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_fiber = COALESCE((
            SELECT SUM(fiber)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_sugar = COALESCE((
            SELECT SUM(sugar)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        total_sodium = COALESCE((
            SELECT SUM(sodium)
            FROM food_log_items
            WHERE food_log_id = NEW.food_log_id
        ), 0),
        updated_at = now()
    WHERE id = NEW.food_log_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer trigger sur INSERT/UPDATE/DELETE
CREATE TRIGGER trigger_update_food_log_totals_insert
    AFTER INSERT ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();

CREATE TRIGGER trigger_update_food_log_totals_update
    AFTER UPDATE ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();

CREATE TRIGGER trigger_update_food_log_totals_delete
    AFTER DELETE ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();


-- ============================================
-- 5. VIEW : Compatibilité avec ancien schéma
-- ============================================

-- Si besoin de garder compatibilité avec food_diary_entries
CREATE VIEW food_diary_entries AS
SELECT
    fli.id,
    fl.user_id,
    fl.meal_type,
    fli.food_name,
    fli.serving_size,
    fli.serving_unit,
    fli.calories,
    fli.protein,
    fli.carbs,
    fli.fat,
    fli.fiber,
    fli.sugar,
    fli.sodium,
    fl.logged_at,
    fli.source,
    fli.fatsecret_id
FROM food_log_items fli
JOIN food_logs fl ON fl.id = fli.food_log_id
ORDER BY fl.logged_at DESC, fli.display_order;
```

**Avantages du nouveau schéma :**
- ✅ Un repas peut avoir plusieurs aliments
- ✅ Photos attachées au repas
- ✅ Édition facile (update du log ou des items)
- ✅ Regroupement logique
- ✅ Totaux calculés automatiquement (trigger)
- ✅ Extensible pour analyse photo IA (future)
- ✅ Compatibilité rétro via VIEW

---

## D) FatSecret comme Provider (pas dépendance critique)

### ❌ Problème Identifié

**Risque actuel :**
- FatSecret = système critique
- Si FatSecret down → Pulse bloqué
- Couplage fort entre Pulse et FatSecret

### ✅ Solution : Architecture Découplée

**Principes :**
1. **Supabase = Source of Truth**
2. **FatSecret = Provider de données nutritionnelles**
3. **Mode dégradé = Entrées manuelles**

**Flow Découplé :**

```
┌─────────────────────────────────────────┐
│  User cherche "poulet"                  │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  App Mobile                             │
│  1. Essaie FatSecret API                │
│  2. Si succès → affiche résultats       │
│  3. Si échec → mode "entrée manuelle"   │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  FatSecret API (optionnel)              │
│  - /foods/search                        │
│  - /food/get                            │
└────────────┬────────────────────────────┘
             │
             ↓ (Si succès)
┌─────────────────────────────────────────┐
│  User sélectionne aliment               │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  Insertion dans Supabase                │
│  INSERT INTO food_log_items (           │
│    food_log_id,                         │
│    source: 'fatsecret',                 │
│    fatsecret_id: '12345',               │
│    food_name,                           │
│    calories,                            │
│    ...                                  │
│  )                                      │
└─────────────────────────────────────────┘
             │
             ↓ (Si échec FatSecret)
┌─────────────────────────────────────────┐
│  Mode Manuel                            │
│  User saisit:                           │
│  - Nom aliment                          │
│  - Calories                             │
│  - Macros (optionnel)                   │
│                                         │
│  INSERT INTO food_log_items (           │
│    source: 'manual',                    │
│    food_name,                           │
│    calories,                            │
│    ...                                  │
│  )                                      │
└─────────────────────────────────────────┘
```

**Implémentation Mobile :**

```typescript
// mobile/src/services/FoodSearchService.ts

export class FoodSearchService {
  private fatSecretAvailable = true;
  
  /**
   * Recherche aliments avec fallback gracieux
   */
  async searchFood(query: string): Promise<SearchResult> {
    try {
      // Essayer FatSecret d'abord
      if (this.fatSecretAvailable) {
        const results = await this.searchFatSecret(query);
        return {
          source: 'fatsecret',
          items: results,
          fallbackToManual: false
        };
      }
    } catch (error) {
      console.warn('[FoodSearch] FatSecret error, falling back to manual', error);
      this.fatSecretAvailable = false;
      
      // Réessayer dans 5 minutes
      setTimeout(() => {
        this.fatSecretAvailable = true;
      }, 5 * 60 * 1000);
    }
    
    // Fallback : mode manuel
    return {
      source: 'manual',
      items: [],
      fallbackToManual: true,
      message: 'Base de données temporairement indisponible. Saisissez manuellement.'
    };
  }
  
  private async searchFatSecret(query: string): Promise<FoodItem[]> {
    const response = await fetch('/api/fatsecret/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
      throw new Error('FatSecret API error');
    }
    
    const data = await response.json();
    return data.foods || [];
  }
}

interface SearchResult {
  source: 'fatsecret' | 'manual';
  items: FoodItem[];
  fallbackToManual: boolean;
  message?: string;
}
```

**Backend avec Cache Local :**

```python
# backend/services/fatsecret_service.py

import redis
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FatSecretService:
    """
    Service FatSecret avec cache et fallback
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600 * 24 * 7  # 7 jours
    
    def search_food(self, query: str) -> List[Dict]:
        """
        Recherche aliments avec cache Redis
        """
        # 1. Essayer cache d'abord
        cache_key = f"fatsecret:search:{query.lower()}"
        cached = self.redis_client.get(cache_key)
        
        if cached:
            logger.info(f"FatSecret cache hit: {query}")
            return json.loads(cached)
        
        # 2. Appeler FatSecret API
        try:
            results = self._call_fatsecret_api(query)
            
            # Mettre en cache
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(f"FatSecret API error: {e}")
            
            # 3. Fallback: retourner cache périmé si disponible
            cached_stale = self.redis_client.get(cache_key)
            if cached_stale:
                logger.warning(f"Using stale cache for {query}")
                return json.loads(cached_stale)
            
            # 4. Pas de cache: retourner vide (mobile passera en mode manuel)
            return []
    
    def _call_fatsecret_api(self, query: str) -> List[Dict]:
        """
        Appel direct à FatSecret API
        """
        # Implémentation OAuth + API call
        # ...
        pass
```

**Bénéfices :**
- ✅ Pulse fonctionne même si FatSecret down
- ✅ Cache local (Redis) pour résilience
- ✅ Mode manuel toujours disponible
- ✅ Pas de lock-in vendor
- ✅ Source of truth = Supabase

---

## E) 5 Améliorations "Petit Effort / Gros Gain"

### 1. Versionner Tous les Modèles

**Pourquoi :**
- Permet d'invalider le cache quand formule change
- Facilite migrations/rollbacks
- Debugging plus facile

**Implémentation :**

```sql
-- Ajouter model_version partout

ALTER TABLE user_baselines ADD COLUMN IF NOT EXISTS 
    model_version TEXT NOT NULL DEFAULT 'baseline_v2_robust';

ALTER TABLE daily_state ADD COLUMN IF NOT EXISTS 
    model_version TEXT NOT NULL DEFAULT 'latent_v1';

-- Nouvelle table pour anomalies (si pas déjà créée)
CREATE TABLE IF NOT EXISTS anomaly_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    anomalies JSONB NOT NULL,  -- Array d'anomalies
    model_version TEXT NOT NULL DEFAULT 'anomaly_v2_robust',
    INDEX idx_anomaly_logs_user_date (user_id, detected_at DESC)
);
```

**Constants Backend :**

```python
# backend/constants.py

# Versions des modèles
MODEL_VERSIONS = {
    'baseline': 'baseline_v2_robust',
    'anomaly': 'anomaly_v2_robust',
    'latent_state': 'latent_v1',
    'readiness': 'readiness_v1',
    'pulse_score': 'pulse_score_v1'
}

def get_model_version(model_type: str) -> str:
    return MODEL_VERSIONS.get(model_type, 'unknown')
```

### 2. Data Quality Flags dans Biometrics

**Pourquoi :**
- Sommeil incomplet (réveil nocturne)
- Voyage (timezone différent)
- Alcool/médicaments (impact sur métriques)
- Améliore confidence des baselines

**Implémentation :**

```sql
ALTER TABLE biometrics ADD COLUMN IF NOT EXISTS 
    quality_flags TEXT[];  -- Array de flags

-- Exemples de flags:
-- 'incomplete_sleep'
-- 'timezone_change'
-- 'alcohol_consumed'
-- 'medication_taken'
-- 'outlier_detected'
-- 'sensor_error'
```

**Usage dans calcul baselines :**

```python
def calculate_baselines(self, user_id: str, lookback_days: int = 90):
    # Récupérer biometrics
    biometrics = self.get_user_biometrics(user_id, lookback_days)
    
    # Filtrer les données de mauvaise qualité
    clean_biometrics = [
        b for b in biometrics
        if not b.get('quality_flags') or 
           'sensor_error' not in b.get('quality_flags', [])
    ]
    
    # Calculer baselines sur données propres
    baselines = self._compute_robust_stats(clean_biometrics)
    
    # Ajuster confidence selon % de données filtrées
    filtered_percent = (len(biometrics) - len(clean_biometrics)) / len(biometrics)
    if filtered_percent > 0.2:  # > 20% filtré
        # Réduire confidence
        for baseline in baselines.values():
            if baseline['confidence'] == 'high':
                baseline['confidence'] = 'medium'
    
    return baselines
```

### 3. Une Seule Librairie de Calcul (stats.py)

**Pourquoi :**
- Évite duplication de code
- Un seul endroit à maintenir
- Cohérence garantie

**Implémentation :**

```python
# backend/lib/stats.py

import numpy as np
from typing import List, Dict, Tuple

class RobustStats:
    """
    Bibliothèque centralisée pour statistiques robustes
    Utilisée par: baselines, anomalies, latent states
    """
    
    @staticmethod
    def compute_robust_stats(values: List[float]) -> Dict:
        """
        Calcule statistiques robustes (median/IQR)
        
        Returns:
            {
                'median': float,
                'iqr': float,
                'p25': float,
                'p75': float,
                'mean': float,  # optionnel
                'std': float,   # optionnel
                'count': int
            }
        """
        if not values or len(values) < 2:
            return None
        
        arr = np.array(values)
        
        return {
            'median': float(np.median(arr)),
            'iqr': float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            'p25': float(np.percentile(arr, 25)),
            'p75': float(np.percentile(arr, 75)),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'count': len(values)
        }
    
    @staticmethod
    def z_score_robust(
        value: float,
        median: float,
        iqr: float
    ) -> float:
        """
        Calcule Z-Score robuste
        Z = (x - median) / (IQR / 1.349)
        """
        if iqr == 0:
            return 0.0
        
        sigma_equivalent = iqr / 1.349
        return (value - median) / sigma_equivalent
    
    @staticmethod
    def sigmoid(z: float, scale: float = 1.0) -> float:
        """
        Sigmoid transformation pour normaliser Z-scores
        Utilisé par états latents
        """
        return 1.0 / (1.0 + np.exp(-z / scale))
    
    @staticmethod
    def ema(
        current: float,
        previous: float,
        alpha: float = 0.3
    ) -> float:
        """
        Exponential Moving Average
        Utilisé pour lisser scores latents
        """
        return alpha * current + (1 - alpha) * previous
```

**Usage :**

```python
# backend/services/baseline_calculator.py
from lib.stats import RobustStats

class BaselineCalculator:
    def calculate(self, values: List[float]):
        return RobustStats.compute_robust_stats(values)

# backend/services/anomaly_detector.py
from lib.stats import RobustStats

class AnomalyDetector:
    def detect(self, value: float, baseline: Dict):
        z = RobustStats.z_score_robust(
            value,
            baseline['median'],
            baseline['iqr']
        )
        return abs(z) > 2.0

# backend/services/latent_states.py
from lib.stats import RobustStats

class LatentStateCalculator:
    def calculate_recovery(self, ...):
        z_hrv = RobustStats.z_score_robust(hrv, baseline_hrv, iqr_hrv)
        recovery_raw = RobustStats.sigmoid(z_hrv, scale=1.5)
        recovery_smoothed = RobustStats.ema(recovery_raw, previous)
        return recovery_smoothed
```

### 4. Contract JSON Unique pour Brief Cards

**Pourquoi :**
- Cohérence Backend ↔ Mobile
- Validation facile
- Documentation auto-générée

**Implémentation :**

```typescript
// shared/types/briefCard.ts (partagé backend + mobile)

export type BriefCardType = 
  | 'recovery_state'
  | 'sleep_debt'
  | 'overtrain_risk'
  | 'infection_like'
  | 'insight_ai'
  | 'recommendation';

export interface BriefCard {
  // Identité
  id: string;
  type: BriefCardType;
  title: string;
  
  // Contenu
  content: string;
  
  // Score (si applicable)
  score?: number;          // 0-100
  smoothed_score?: number; // 0-100
  
  // Métadonnées
  priority: number;        // 0-10 (tri des cartes)
  confidence: 'low' | 'medium' | 'high';
  
  // Facteurs contributifs
  factors: BriefFactor[];
  
  // Tendance
  trend?: 'improving' | 'worsening' | 'stable';
  
  // Recommandation
  recommendation?: string;
  
  // Visuel
  color: string;           // Hex color
  icon: string;            // Lucide icon name
  
  // Métadonnées techniques
  model_version: string;
  calculated_at: string;   // ISO timestamp
}

export interface BriefFactor {
  factor: string;          // ID du facteur
  display_name: string;    // Nom affiché
  weight: number;          // 0-1
  direction: 'up' | 'down' | 'neutral';
  evidence: Record<string, any>;  // Preuves (valeurs, delta, etc.)
}

// Validation Zod (runtime)
import { z } from 'zod';

export const BriefCardSchema = z.object({
  id: z.string().uuid(),
  type: z.enum([
    'recovery_state',
    'sleep_debt',
    'overtrain_risk',
    'infection_like',
    'insight_ai',
    'recommendation'
  ]),
  title: z.string(),
  content: z.string(),
  score: z.number().min(0).max(100).optional(),
  smoothed_score: z.number().min(0).max(100).optional(),
  priority: z.number().min(0).max(10),
  confidence: z.enum(['low', 'medium', 'high']),
  factors: z.array(z.object({
    factor: z.string(),
    display_name: z.string(),
    weight: z.number().min(0).max(1),
    direction: z.enum(['up', 'down', 'neutral']),
    evidence: z.record(z.any())
  })),
  trend: z.enum(['improving', 'worsening', 'stable']).optional(),
  recommendation: z.string().optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  icon: z.string(),
  model_version: z.string(),
  calculated_at: z.string().datetime()
});
```

**Usage Backend :**

```python
# backend/services/brief_generator.py

def generate_brief_card_recovery(
    user_id: str,
    daily_state: Dict
) -> Dict:
    """
    Génère une carte Brief pour Recovery State
    Respecte le contract BriefCard
    """
    return {
        'id': str(uuid.uuid4()),
        'type': 'recovery_state',
        'title': 'Recovery State',
        'content': 'Excellente récupération détectée',
        'score': int(daily_state['score'] * 100),
        'smoothed_score': int(daily_state['smoothed_score'] * 100),
        'priority': 8,
        'confidence': daily_state['confidence'],
        'factors': [
            {
                'factor': 'hrv_above_baseline',
                'display_name': 'HRV au-dessus baseline',
                'weight': 0.40,
                'direction': 'up',
                'evidence': {
                    'current': 68.5,
                    'baseline': 59.6,
                    'delta_percent': 15
                }
            }
        ],
        'trend': 'improving',
        'recommendation': 'Profitez pour entraînement intense',
        'color': '#34C759',
        'icon': 'activity',
        'model_version': 'latent_v1',
        'calculated_at': datetime.now().isoformat()
    }
```

### 5. MVP Photo-Food : Stockage d'abord, Analyse après

**Pourquoi :**
- Évite complexité immédiate
- Permet de lancer MVP rapidement
- Analyse IA = feature v2

**Plan MVP :**

**Phase 1 : Stockage Photo Simple (MVP)**
```
User prend photo
  ↓
Upload vers Supabase Storage
  ↓
Lien photo avec food_log
  ↓
User saisit manuellement aliments
  ↓
Photo = référence visuelle uniquement
```

**Phase 2 : Analyse IA (Post-MVP)**
```
User prend photo
  ↓
Upload vers Supabase Storage
  ↓
Appel GPT-4 Vision API
  ↓
Extraction aliments + estimation calories
  ↓
User confirme/édite
  ↓
Enregistrement final
```

**Implémentation MVP (Phase 1) :**

```typescript
// mobile/src/hooks/useFoodPhoto.ts

export function useFoodPhoto() {
  const uploadPhoto = async (
    foodLogId: string,
    imageUri: string
  ): Promise<string> => {
    // 1. Compresser image
    const compressed = await compressImage(imageUri);
    
    // 2. Upload vers Supabase Storage
    const fileName = `${foodLogId}_${Date.now()}.jpg`;
    const { data, error } = await supabase.storage
      .from('food-photos')
      .upload(fileName, compressed, {
        contentType: 'image/jpeg',
        cacheControl: '3600'
      });
    
    if (error) throw error;
    
    // 3. Récupérer URL publique
    const { data: { publicUrl } } = supabase.storage
      .from('food-photos')
      .getPublicUrl(fileName);
    
    // 4. Enregistrer dans food_photos
    await supabase
      .from('food_photos')
      .insert({
        food_log_id: foodLogId,
        storage_path: fileName,
        analysis_status: 'manual'  // Pas d'analyse IA en MVP
      });
    
    return publicUrl;
  };
  
  return { uploadPhoto };
}
```

**Avantages :**
- ✅ MVP rapide (juste upload)
- ✅ Photo visible dans journal
- ✅ Pas de dépendance Vision AI
- ✅ Extensible pour Phase 2

---

## 📝 Plan de Migration

### Priorité 1 : Baselines Robustes (Breaking Change)

1. Créer migration SQL `020_robust_baselines.sql`
2. Déployer en base de données
3. Forcer recalcul toutes baselines (cron nocturne)
4. Mettre à jour backend `baseline_calculator.py`
5. Mettre à jour mobile `useBaselines.ts`
6. Tests E2E

**Timeline : 2-3 jours**

### Priorité 2 : Z-Score Robuste (Breaking Change)

1. Mettre à jour `anomaly_detector.py`
2. Mettre à jour `ZScoreCalculator.ts`
3. Mettre à jour types TypeScript
4. Tests unitaires
5. Tests E2E

**Timeline : 1-2 jours**

### Priorité 3 : Food Diary Extensible (New Feature)

1. Créer migration SQL `021_food_logs_extensible.sql`
2. Implémenter backend endpoints
3. Mettre à jour hooks mobile
4. Mettre à jour UI journal
5. Tests

**Timeline : 3-4 jours**

### Priorité 4 : FatSecret Provider (Refactoring)

1. Ajouter Redis cache
2. Implémenter fallback gracieux
3. Tests de résilience
4. Documentation

**Timeline : 1-2 jours**

### Priorité 5 : 5 Améliorations Rapides

1. Ajouter `model_version` partout (1 jour)
2. Ajouter `quality_flags` (1 jour)
3. Créer `lib/stats.py` (1 jour)
4. Standardiser `BriefCard` contract (1 jour)
5. MVP photo simple (1 jour)

**Timeline : 5 jours**

---

## ✅ Checklist de Validation

- [ ] Migration baselines robustes déployée
- [ ] Tous calculs utilisent median/IQR
- [ ] Z-Score robuste unifié partout
- [ ] Food diary extensible en production
- [ ] FatSecret avec fallback fonctionnel
- [ ] `model_version` sur toutes les tables
- [ ] `quality_flags` dans biometrics
- [ ] `lib/stats.py` créée et utilisée
- [ ] `BriefCard` contract validé (Zod)
- [ ] MVP photo fonctionnel
- [ ] Documentation mise à jour
- [ ] Tests E2E passants

---

## 📚 Documentation à Mettre à Jour

1. **ARCHITECTURE_COMPLETE.md**
   - Remplacer mean/std par median/IQR
   - Mettre à jour formules Z-Score
   - Ajouter nouveau schéma food_logs

2. **MOBILE_SCREENS_GUIDE.md**
   - Mettre à jour affichage baselines
   - Mettre à jour journal alimentaire

3. **API Documentation**
   - Endpoints food_logs
   - Contract BriefCard

---

*Document de corrections critique*  
*À implémenter AVANT toute nouvelle feature*  
*Version 3.1.0 - 30 Janvier 2026*
