# 🚀 Guide de Déploiement - Corrections Architecture

> **Date:** 30 Janvier 2026  
> **Version:** 3.1.0  
> **Statut:** PRÊT POUR PRODUCTION

---

## 📋 Vue d'Ensemble

Ce guide vous accompagne étape par étape pour déployer les corrections d'architecture :
1. ✅ Baselines robustes (median/IQR)
2. ✅ Z-Score robuste unifié
3. ✅ Food diary extensible
4. ✅ FatSecret comme provider
5. ✅ 5 améliorations rapides

**Durée totale estimée:** 2-3 heures (avec tests)

---

## 🎯 Prérequis

### Environnement

- [ ] Python 3.11+
- [ ] Node.js 20.19.4+
- [ ] PostgreSQL (via Supabase)
- [ ] Accès admin Supabase
- [ ] Git configuré

### Outils

```bash
# Backend
pip install pytest pytest-cov numpy

# Mobile
cd mobile
npm install

# Base de données
# Accès au dashboard Supabase
```

### Backups

⚠️ **CRITIQUE : Faire un backup complet avant toute migration**

```bash
# Backup base de données
supabase db dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup code
git checkout -b backup/pre-corrections
git push origin backup/pre-corrections
```

---

## 📦 Phase 1 : Préparation (15 min)

### 1.1 Créer branche de travail

```bash
cd /Users/dannezri/Desktop/Pulse

# Créer branche feature
git checkout -b feature/robust-baselines-corrections

# Vérifier status
git status
```

### 1.2 Installer dépendances backend

```bash
cd backend

# Créer virtualenv si nécessaire
python3 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou
# venv\Scripts\activate  # Sur Windows

# Installer/mettre à jour dépendances
pip install --upgrade pip
pip install numpy pytest pytest-cov

# Vérifier imports
python -c "import numpy; print('NumPy:', numpy.__version__)"
```

### 1.3 Vérifier connexion Supabase

```bash
# Tester connexion
cd backend
python -c "
from supabase_client import get_supabase_client
client = get_supabase_client()
result = client.table('profiles').select('count').execute()
print('✅ Supabase connected')
"
```

---

## 🗄️ Phase 2 : Migrations Base de Données (30 min)

### 2.1 Migration 020 : Baselines Robustes

**Fichier:** `database/migrations/020_robust_baselines.sql`

#### Étape 1 : Validation SQL

```bash
# Vérifier syntaxe SQL (dry-run)
psql -h your-supabase-host \
     -U postgres \
     -d postgres \
     --dry-run \
     -f database/migrations/020_robust_baselines.sql
```

#### Étape 2 : Exécution en STAGING

```bash
# Dans le dashboard Supabase:
# 1. Aller dans SQL Editor
# 2. Copier/coller le contenu de 020_robust_baselines.sql
# 3. Exécuter
# 4. Vérifier logs pour "Migration completed"
```

#### Étape 3 : Validation

```sql
-- Vérifier que la nouvelle table existe
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name IN ('user_baselines', 'user_baselines_legacy');

-- Vérifier les colonnes
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_baselines'
ORDER BY ordinal_position;

-- Vérifier la migration des données
SELECT 
    model_version,
    COUNT(*) as count
FROM user_baselines
GROUP BY model_version;

-- Devrait retourner:
-- baseline_v2_robust_migrated | <count>
```

#### Étape 4 : Test RPC

```sql
-- Tester fonction RPC
SELECT * FROM get_user_baselines_robust(
    'YOUR-TEST-USER-ID',
    'baseline_v2_robust_migrated'
) LIMIT 5;

-- Devrait retourner des baselines avec median, iqr, p25, p75
```

### 2.2 Migration 021 : Food Diary Extensible

**Fichier:** `database/migrations/021_food_logs_extensible.sql`

#### Étape 1 : Exécution

```bash
# Dans le dashboard Supabase:
# 1. SQL Editor
# 2. Copier/coller 021_food_logs_extensible.sql
# 3. Exécuter
```

#### Étape 2 : Validation

```sql
-- Vérifier tables créées
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('food_logs', 'food_log_items', 'food_photos');

-- Vérifier triggers
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE trigger_name LIKE '%food_log%';

-- Devrait retourner 3 triggers (INSERT, UPDATE, DELETE)

-- Test trigger : Créer un food_log
INSERT INTO food_logs (user_id, meal_type) 
VALUES ('YOUR-USER-ID', 'breakfast')
RETURNING id, total_calories;

-- total_calories devrait être 0

-- Ajouter un item
INSERT INTO food_log_items (
    food_log_id, 
    food_name, 
    serving_size, 
    serving_unit, 
    calories, 
    protein, 
    carbs, 
    fat, 
    source
) VALUES (
    'FOOD-LOG-ID-FROM-ABOVE',
    'Test Food',
    100,
    'g',
    250,
    10,
    30,
    8,
    'manual'
);

-- Vérifier que total_calories a été mis à jour
SELECT id, total_calories, total_protein, total_carbs, total_fat
FROM food_logs
WHERE id = 'FOOD-LOG-ID-FROM-ABOVE';

-- Devrait retourner: total_calories=250, total_protein=10, etc.
```

---

## 🐍 Phase 3 : Backend - lib/stats.py (20 min)

### 3.1 Copier fichier

```bash
cd backend

# Créer dossier lib/ si nécessaire
mkdir -p lib
touch lib/__init__.py

# Le fichier lib/stats.py est déjà créé
# Vérifier qu'il est présent
ls -la lib/stats.py
```

### 3.2 Tests unitaires

```bash
# Créer dossier tests/ si nécessaire
mkdir -p tests
touch tests/__init__.py

# Le fichier tests/test_robust_stats.py est déjà créé
# Lancer les tests
pytest tests/test_robust_stats.py -v

# Tous les tests doivent passer ✅
```

### 3.3 Test interactif

```bash
# Test rapide
python lib/stats.py

# Devrait afficher:
# === Test RobustStats ===
# Median: 62.5
# IQR: 18.75
# ...
# === Tests completed ===
```

### 3.4 Intégration dans calculateurs existants

#### A) Mettre à jour baseline_calculator.py

```python
# backend/services/baseline_calculator.py

from lib.stats import (
    compute_robust_stats,
    RobustStats,
    log_baseline_stats
)

class BaselineCalculator:
    def calculate_baselines(
        self, 
        user_id: str, 
        lookback_days: int = 90
    ) -> Dict[str, Dict]:
        """
        Calcule les baselines robustes pour un utilisateur
        """
        # Récupérer biometrics
        biometrics = self._get_biometrics(user_id, lookback_days)
        
        # Grouper par metric_type
        grouped = self._group_by_metric(biometrics)
        
        baselines = {}
        
        for metric_type, values in grouped.items():
            # Utiliser la nouvelle fonction
            stats = compute_robust_stats(values, include_classical=True)
            
            if stats:
                # Convertir en dict pour insertion DB
                baselines[metric_type] = stats.to_dict()
                
                # Log
                log_baseline_stats(metric_type, stats)
        
        return baselines
```

#### B) Mettre à jour anomaly_detector.py

```python
# backend/services/anomaly_detector.py

from lib.stats import (
    z_score_robust,
    is_anomaly,
    detect_anomalies,
    RobustStats,
    log_anomaly
)

class AnomalyDetector:
    def detect(
        self,
        user_id: str,
        current_metrics: Dict[str, float],
        baselines: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Détecte les anomalies avec Z-Score robuste
        """
        # Convertir baselines dict → RobustStats objects
        baselines_objects = {}
        for metric, baseline_dict in baselines.items():
            baselines_objects[metric] = RobustStats(
                median=baseline_dict['median'],
                iqr=baseline_dict['iqr'],
                p25=baseline_dict['p25'],
                p75=baseline_dict['p75'],
                mean=baseline_dict.get('mean'),
                std=baseline_dict.get('std'),
                count=baseline_dict['count'],
                confidence=baseline_dict['confidence']
            )
        
        # Utiliser la fonction centralisée
        anomalies = detect_anomalies(
            current_metrics,
            baselines_objects,
            weights=self.WEIGHTS,
            threshold_sigma=2.0
        )
        
        # Log
        for anomaly in anomalies:
            log_anomaly(anomaly)
        
        return anomalies
```

#### C) Tester l'intégration

```bash
# Test avec un utilisateur réel
python -c "
from services.baseline_calculator import BaselineCalculator
from services.anomaly_detector import AnomalyDetector

calc = BaselineCalculator()
detector = AnomalyDetector()

# Calculer baselines
user_id = 'YOUR-TEST-USER-ID'
baselines = calc.calculate_baselines(user_id)

print('✅ Baselines calculées:', len(baselines))

# Détecter anomalies
current = {'hrv': 45, 'heart_rate': 85}
anomalies = detector.detect(user_id, current, baselines)

print('✅ Anomalies détectées:', len(anomalies))
"
```

---

## 📱 Phase 4 : Mobile - Types et Hooks (30 min)

### 4.1 Mettre à jour types TypeScript

```typescript
// mobile/src/types/baselines.ts

export interface RobustBaseline {
  median: number;
  iqr: number;
  p25: number;
  p75: number;
  mean?: number;    // Optionnel
  std?: number;     // Optionnel
  sample_count: number;
  confidence: 'low' | 'medium' | 'high';
  calculated_at: string;
  model_version: string;
}

export interface RobustBaselines {
  [metric: string]: RobustBaseline;
}

export interface Anomaly {
  metric: string;
  value: number;
  z_score_robust: number;  // Changé!
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

### 4.2 Mettre à jour ZScoreCalculator.ts

```typescript
// mobile/src/services/ZScoreCalculator.ts

// Constante IQR → Sigma
const IQR_TO_SIGMA = 1.349;

export class RobustZScoreCalculator {
  /**
   * Calcule Z-Score ROBUSTE
   */
  calculateZScoreRobust(
    value: number,
    median: number,
    iqr: number
  ): number {
    if (iqr === 0) return 0;
    
    const sigmaEquivalent = iqr / IQR_TO_SIGMA;
    return (value - median) / sigmaEquivalent;
  }
  
  /**
   * Détecte anomalies
   */
  detectAnomalies(
    currentMetrics: CurrentMetrics,
    baselines: RobustBaselines
  ): Anomaly[] {
    // ... voir CORRECTIONS_ARCHITECTURE.md pour implémentation complète
  }
}
```

### 4.3 Mettre à jour useBaselines hook

```typescript
// mobile/src/hooks/useBaselines.ts

export function useBaselines(userId: string | null) {
  return useQuery({
    queryKey: ['baselines', userId],
    queryFn: async () => {
      if (!userId) return null;
      
      const { data, error } = await supabase
        .rpc('get_user_baselines_robust', {
          p_user_id: userId,
          p_model_version: 'baseline_v2_robust'
        });
      
      if (error) throw error;
      
      // Transformer en RobustBaselines
      const baselines: RobustBaselines = {};
      for (const row of data) {
        baselines[row.baseline_type] = {
          median: row.median,
          iqr: row.iqr,
          p25: row.p25,
          p75: row.p75,
          mean: row.mean,
          std: row.std,
          sample_count: row.sample_count,
          confidence: row.confidence,
          calculated_at: row.calculated_at,
          model_version: 'baseline_v2_robust'
        };
      }
      
      return baselines;
    },
    enabled: !!userId
  });
}
```

### 4.4 Tests mobile

```bash
cd mobile

# Build TypeScript
npx tsc --noEmit

# Lancer tests (si configurés)
npm test

# Lancer app en mode dev
npm start
```

---

## ✅ Phase 5 : Validation Complète (30 min)

### 5.1 Tests Backend

```bash
cd backend

# Tous les tests unitaires
pytest tests/ -v --cov=lib --cov=services

# Test integration baseline calculator
python tests/integration/test_baseline_calculator.py

# Test integration anomaly detector
python tests/integration/test_anomaly_detector.py
```

### 5.2 Tests Mobile

```bash
cd mobile

# Test sur simulateur iOS
npm run ios

# Vérifier:
# ✅ Dashboard affiche correctement
# ✅ Baselines chargées (voir Profil)
# ✅ Anomalies détectées (voir Dashboard)
# ✅ Graphiques Tendances fonctionnent
```

### 5.3 Tests E2E

#### Scénario 1 : Calcul Baselines

```bash
# Via API backend
curl -X POST http://localhost:8000/api/baselines/calculate \
  -H "Authorization: Bearer YOUR-TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "YOUR-USER-ID"}'

# Vérifier réponse:
# {
#   "success": true,
#   "baselines": {
#     "hrv": {
#       "median": 65.2,
#       "iqr": 12.5,
#       ...
#     }
#   }
# }
```

#### Scénario 2 : Détection Anomalie

```bash
# Via mobile app
# 1. Ouvrir Dashboard
# 2. Vérifier Orb (couleur selon état)
# 3. Taper Orb → Bottom Drawer
# 4. Vérifier anomalies listées avec z_score_robust
```

#### Scénario 3 : Food Diary

```bash
# Via mobile app
# 1. Onglet Journal
# 2. Ajouter un repas
# 3. Ajouter 2-3 aliments
# 4. Vérifier totaux calculés automatiquement
# 5. Ajouter une photo (optionnel)
```

### 5.4 Smoke Tests Post-Migration

#### Objectif
Vérifier que les endpoints critiques (Dashboard/Brief) ne crashent pas avec:
- Baselines en version `baseline_v2_robust_migrated` (approximation)
- Baselines manquantes (nouveau user)
- Baselines partielles (< 10 jours de données)

#### Scénario 1: User avec Baselines Migrées

```bash
# Via cURL ou Postman
curl -X GET "http://localhost:8000/api/ambient/dashboard" \
  -H "Authorization: Bearer USER-TOKEN-WITH-MIGRATED-BASELINES" \
  -H "Content-Type: application/json"

# Résultat attendu:
# - HTTP 200 OK
# - JSON valide
# - Champ "anomalies" présent (peut être vide)
# - Pas d'erreur "KeyError" ou "NoneType"
# - Log backend: "Using baseline_v2_robust_migrated" (acceptable temporairement)
```

**Validation:**
```bash
# Vérifier logs backend
tail -f backend/logs/app.log | grep -i "baseline\|anomaly"

# Attendu: Aucune erreur, warnings possibles sur version migrée
```

#### Scénario 2: Nouveau User (0 Baselines)

```bash
# Créer un nouveau user de test
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test-new-user@pulse.com","password":"testpass123"}'

# Récupérer token
NEW_USER_TOKEN="..."

# Appeler dashboard
curl -X GET "http://localhost:8000/api/ambient/dashboard" \
  -H "Authorization: Bearer $NEW_USER_TOKEN" \
  -H "Content-Type: application/json"

# Résultat attendu:
# - HTTP 200 OK
# - anomalies: []
# - state: "calm"
# - message: "Collecte de données en cours..." (ou similaire)
# - PAS DE CRASH
```

**Mobile Smoke Test:**
```bash
# En mobile (simulateur/device)
# 1. Login avec nouveau user
# 2. Ouvrir Dashboard
# 3. Vérifier:
#    - Pas de crash app
#    - Orb affiche état "calm" (gris)
#    - Message: "Collecte de données en cours..."
#    - Aucune anomalie affichée
```

#### Scénario 3: User avec Données Partielles (<10 jours)

```bash
# Via backend: Seed 5 jours de données pour test user
python backend/tests/seed_baseline_data.py --user-id TEST-USER-ID --days 5

# Appeler dashboard
curl -X GET "http://localhost:8000/api/ambient/dashboard" \
  -H "Authorization: Bearer TEST-USER-TOKEN" \
  -H "Content-Type: application/json"

# Résultat attendu:
# - HTTP 200 OK
# - anomalies: [] OU anomalies présentes mais confidence "low"
# - message: "Données insuffisantes pour certaines métriques"
# - PAS DE CRASH
```

#### Scénario 4: Endpoint Brief avec Baselines Manquantes

```bash
# Appeler endpoint brief
curl -X GET "http://localhost:8000/api/brief/today" \
  -H "Authorization: Bearer NEW-USER-TOKEN" \
  -H "Content-Type: application/json"

# Résultat attendu:
# - HTTP 200 OK OU 204 No Content
# - brief: null OU brief avec message "En attente de données..."
# - PAS D'ERREUR 500
```

#### Scénario 5: RPC get_user_baselines_robust

```sql
-- Tester RPC avec user qui n'a PAS de baselines
SELECT * FROM get_user_baselines_robust(
    'user-id-without-baselines',
    'baseline_v2_robust'
);

-- Résultat attendu:
-- 0 rows (table vide, pas d'erreur)

-- Tester RPC avec user qui a baselines migrées
SELECT * FROM get_user_baselines_robust(
    'user-id-with-migrated-baselines',
    'baseline_v2_robust_migrated'  -- Version migrée
);

-- Résultat attendu:
-- N rows avec median, iqr, p25, p75 (valeurs approximatives mais valides)
```

#### Checklist Smoke Tests

**Backend:**
- [ ] Dashboard endpoint avec baselines migrées → 200 OK
- [ ] Dashboard endpoint avec 0 baselines → 200 OK (anomalies vides)
- [ ] Dashboard endpoint avec <10 jours → 200 OK (confidence low)
- [ ] Brief endpoint avec baselines manquantes → 200/204 (pas de crash)
- [ ] Logs backend: Aucune erreur 500 ou traceback Python

**Base de Données:**
- [ ] RPC avec user sans baselines → 0 rows (pas d'erreur)
- [ ] RPC avec user baselines migrées → N rows valides
- [ ] Query baseline par version → retourne correct model_version

**Mobile:**
- [ ] Login nouveau user → Pas de crash
- [ ] Dashboard nouveau user → Message "Collecte en cours"
- [ ] Dashboard user <10 jours → Message "Données insuffisantes"
- [ ] Profil baselines vides → Section affiche "En attente"
- [ ] Orb avec 0 anomalies → Affiche "calm" (gris)

#### Temps Estimé
- 15-20 minutes par environnement (staging/production)
- Automatisable avec script de smoke test

#### Script Automatisé (Optionnel)

```bash
#!/bin/bash
# smoke-test-post-migration.sh

echo "=== SMOKE TEST POST-MIGRATION ==="

# Config
API_URL="${1:-http://localhost:8000}"
NEW_USER_EMAIL="smoke-test-$(date +%s)@pulse.com"

echo "1. Testing with new user (0 baselines)..."
# Créer user
SIGNUP_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$NEW_USER_EMAIL\",\"password\":\"testpass123\"}")

TOKEN=$(echo $SIGNUP_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ]; then
  echo "❌ Failed to create test user"
  exit 1
fi

# Test dashboard
DASHBOARD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/ambient/dashboard" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$DASHBOARD_RESPONSE" | tail -n 1)
BODY=$(echo "$DASHBOARD_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Dashboard endpoint OK (HTTP $HTTP_CODE)"
  
  # Vérifier structure JSON
  ANOMALIES_COUNT=$(echo $BODY | jq -r '.anomalies | length')
  echo "   Anomalies detected: $ANOMALIES_COUNT (expected: 0)"
  
  if [ "$ANOMALIES_COUNT" == "0" ]; then
    echo "✅ No anomalies for new user (correct)"
  else
    echo "⚠️  Anomalies found for new user (unexpected but not critical)"
  fi
else
  echo "❌ Dashboard endpoint failed (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""
echo "2. Testing brief endpoint..."
BRIEF_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/brief/today" \
  -H "Authorization: Bearer $TOKEN")

BRIEF_HTTP_CODE=$(echo "$BRIEF_RESPONSE" | tail -n 1)

if [ "$BRIEF_HTTP_CODE" == "200" ] || [ "$BRIEF_HTTP_CODE" == "204" ]; then
  echo "✅ Brief endpoint OK (HTTP $BRIEF_HTTP_CODE)"
else
  echo "❌ Brief endpoint failed (HTTP $BRIEF_HTTP_CODE)"
  exit 1
fi

echo ""
echo "=== ALL SMOKE TESTS PASSED ✅ ==="
```

**Usage:**
```bash
chmod +x smoke-test-post-migration.sh

# Staging
./smoke-test-post-migration.sh https://staging.pulse.com

# Production
./smoke-test-post-migration.sh https://api.pulse.com
```

---

## 🚨 Phase 6 : Rollback Plan (Si besoin)

### En cas de problème

#### A) Rollback Base de Données

```sql
-- Restaurer ancienne table baselines
DROP TABLE IF EXISTS user_baselines;
ALTER TABLE user_baselines_legacy RENAME TO user_baselines;

-- Restaurer anciennes policies
-- (voir backup_policies.sql si créé)
```

#### B) Rollback Code

```bash
# Revenir au code précédent
git checkout main
git branch -D feature/robust-baselines-corrections

# Restaurer depuis backup
git checkout backup/pre-corrections
```

#### C) Notification Équipe

```
⚠️ ROLLBACK EFFECTUÉ

Raison: [DÉCRIRE PROBLÈME]
Impact: [DÉCRIRE IMPACT]
Prochaines étapes: [PLAN D'ACTION]
```

---

## 🎉 Phase 7 : Mise en Production (Si tout OK)

### 7.1 Merge en main

```bash
# Vérifier que tous les tests passent
pytest tests/ -v
cd mobile && npm test

# Commit final
git add .
git commit -m "feat: implement robust baselines (median/IQR) and extensible food diary

- Migrate baselines to robust statistics (median/IQR)
- Implement unified z-score robust algorithm
- Add extensible food diary (food_logs + items + photos)
- Centralize stats calculations in lib/stats.py
- Add comprehensive unit tests

BREAKING CHANGE: Baselines now use median/IQR instead of mean/std"

# Push feature branch
git push origin feature/robust-baselines-corrections

# Créer Pull Request
# Attendre review
```

### 7.2 Déploiement Production

```bash
# Après merge en main

# 1. Backup production
supabase db dump --project-ref YOUR-PROJECT > backup_prod_$(date +%Y%m%d).sql

# 2. Exécuter migrations en prod
# Via Supabase Dashboard SQL Editor

# 3. Déployer backend
# (Selon votre setup: Vercel, AWS, etc.)

# 4. Déployer mobile
# (Build & submit à App Store / Play Store si nécessaire)
```

### 7.3 Monitoring Post-Déploiement

```bash
# Surveiller logs backend
tail -f backend/logs/app.log | grep -i "baseline\|anomaly"

# Surveiller métriques Supabase
# Dashboard > Observability > Logs

# Surveiller erreurs mobile
# Sentry / Firebase Crashlytics
```

---

## 📊 Phase 8 : Cleanup (1 semaine après)

### Après validation complète en production

```sql
-- Supprimer ancienne table legacy
DROP TABLE IF EXISTS user_baselines_legacy CASCADE;

-- Supprimer ancienne view food_diary_entries (si non utilisée)
-- DROP VIEW IF EXISTS food_diary_entries CASCADE;
```

```bash
# Supprimer branche backup
git branch -d backup/pre-corrections
git push origin --delete backup/pre-corrections
```

---

## 📝 Checklist Finale

### Avant Déploiement

- [ ] Backup base de données créé
- [ ] Backup code (branche) créé
- [ ] Migrations SQL validées en staging
- [ ] Tests unitaires passent (100%)
- [ ] Tests E2E passent
- [ ] Documentation mise à jour
- [ ] Équipe informée

### Pendant Déploiement

- [ ] Migrations exécutées en ordre (020 puis 021)
- [ ] Validation tables et triggers
- [ ] Backend déployé
- [ ] Mobile déployé
- [ ] Smoke tests passés

### Après Déploiement

- [ ] Monitoring actif
- [ ] Logs surveillés (24h)
- [ ] Métriques normales
- [ ] Utilisateurs testent
- [ ] Feedback collecté
- [ ] Documentation finale

---

## 🆘 Support

### En cas de problème

**Contact :**
- Tech Lead: [email/slack]
- DevOps: [email/slack]
- On-call: [phone]

**Ressources :**
- Documentation: `/docs`
- Runbook: `/docs/runbook.md`
- Slack: `#pulse-engineering`

---

## 📚 Références

- [CORRECTIONS_ARCHITECTURE.md](/CORRECTIONS_ARCHITECTURE.md)
- [ARCHITECTURE_COMPLETE.md](/ARCHITECTURE_COMPLETE.md)
- [Migration 020](/database/migrations/020_robust_baselines.sql)
- [Migration 021](/database/migrations/021_food_logs_extensible.sql)
- [lib/stats.py](/backend/lib/stats.py)
- [Tests](/backend/tests/test_robust_stats.py)

---

*Guide de déploiement v3.1.0*  
*Corrections Architecture - 30 Janvier 2026*  
*Prêt pour Production ✅*
