# ⚠️ CHECKLIST VALIDATION CRITIQUE - Avant Production

**Date:** 30 Janvier 2026  
**Branche:** feature/robust-baselines-corrections  
**Reviewer:** À compléter

---

## A) Migration 020 : Approximation mean/std → median/IQR

### ✅ Vérifications Code

**Status dans migration SQL:**
```sql
-- Ligne 237-238 de 020_robust_baselines.sql
model_version = 'baseline_v2_robust_migrated',      -- ✅ Version spéciale pour migration
```

**✅ CORRECT:** Les rows migrées sont bien marquées en `baseline_v2_robust_migrated`

### ⚠️ Actions Requises

#### 1. Vérifier en Staging après Migration

```sql
-- Compter baselines par version
SELECT 
    model_version,
    COUNT(*) as count,
    MIN(calculated_at) as oldest,
    MAX(calculated_at) as newest
FROM user_baselines
GROUP BY model_version
ORDER BY model_version;

-- Résultat attendu:
-- baseline_v2_robust_migrated | <count> | <date_migration> | <date_migration>
-- OU si cron déjà passé:
-- baseline_v2_robust          | <count> | <date_cron>      | <date_cron>
```

#### 2. Forcer Recalcul Immédiat (Recommandé)

**Option A: Via cron manuel**
```bash
# Sur le serveur backend
cd backend
python cron_calculate_baselines.py --force-all
```

**Option B: Via API pour un user spécifique**
```bash
curl -X POST https://api.pulse.com/api/baselines/calculate/{user_id} \
  -H "Authorization: Bearer $CRON_SECRET"
```

#### 3. Valider Version Consommée par App

```typescript
// Mobile: Vérifier dans useRobustBaselines.ts
const { data } = await supabase.rpc('get_user_baselines_robust', {
  p_user_id: userId,
  p_model_version: 'baseline_v2_robust'  // ✅ Version cible (pas _migrated)
});
```

**Check:** Si app demande `baseline_v2_robust` mais seul `_migrated` existe → app doit fallback ou recalculer.

### 📋 Checklist A

- [ ] Migration 020 exécutée en staging
- [ ] Query COUNT baselines par version → résultats cohérents
- [ ] Cron de recalcul forcé exécuté (ou planifié sous 24h)
- [ ] App mobile charge bien les baselines (avec fallback si besoin)
- [ ] Logs backend: aucune erreur calcul baselines
- [ ] Validation: au moins 1 user avec `baseline_v2_robust` (pas _migrated)

---

## B) Z-score robuste : clamp / NaN / Inf / iqr=0

### ✅ Vérifications Code

**1. Filtrage NaN/Inf dans lib/stats.py:**
```python
# Lignes 42-47 de lib/stats.py
clean_values = [v for v in values if v is not None and np.isfinite(v)]

if len(clean_values) < 2:
    logger.warning(f"Not enough valid values after filtering: {len(clean_values)}")
    return None
```
**✅ CORRECT:** NaN/Inf filtrés avant calcul

**2. Gestion iqr=0 dans lib/stats.py:**
```python
# Lignes 63-66 de lib/stats.py
if iqr == 0:
    iqr = max(median * 0.01, 0.1)  # 1% de la médiane ou 0.1 minimum
    logger.warning(f"IQR was 0, using minimum: {iqr}")
```
**✅ CORRECT:** iqr=0 géré

**3. Z-score avec iqr=0 dans lib/stats.py:**
```python
# Lignes 117-120 de lib/stats.py
def z_score_robust(value: float, baseline: RobustStats) -> float:
    if baseline.iqr == 0:
        logger.warning("IQR is 0, cannot calculate z-score")
        return 0.0
```
**✅ CORRECT:** Double protection

### ⚠️ Amélioration Optionnelle: Clamp Z-Scores

**Raison:** Z-scores > 4 sigma sont très rares (probabilité < 0.00006). Clamper améliore l'UX.

**Fichier à modifier:** `backend/lib/stats.py`

```python
def z_score_robust(
    value: float,
    baseline: RobustStats,
    clamp_range: tuple = (-4.0, 4.0)  # Nouveau paramètre optionnel
) -> float:
    """
    Calcule Z-Score robuste avec clamping optionnel
    """
    if baseline.iqr == 0:
        logger.warning("IQR is 0, cannot calculate z-score")
        return 0.0
    
    sigma_equivalent = baseline.iqr / IQR_TO_SIGMA
    z = (value - baseline.median) / sigma_equivalent
    
    # Clamp optionnel (pour UX)
    if clamp_range:
        z = max(clamp_range[0], min(clamp_range[1], z))
    
    return z
```

**Mobile:** Même logique dans `RobustZScoreCalculator.ts`

### 📋 Checklist B

- [ ] Tests unitaires passent (filtrage NaN/Inf)
- [ ] Test edge case: Toutes valeurs identiques (iqr=0) → Z-score = 0
- [ ] Test edge case: Valeur avec NaN → filtrée
- [ ] Test edge case: Valeur avec Inf → filtrée
- [ ] (Optionnel) Implémenter clamping Z-scores à [-4, 4]
- [ ] Valider en staging: aucun crash sur données edge case

---

## C) Triggers food_log_totals : comportement sur DELETE

### ✅ Vérifications Code

**Trigger dans migration 021:**
```sql
-- Lignes 264-268 de 021_food_logs_extensible.sql
IF TG_OP = 'DELETE' THEN
    log_id := OLD.food_log_id;  -- ✅ CORRECT: utilise OLD sur DELETE
ELSE
    log_id := NEW.food_log_id;
END IF;
```

**✅ CORRECT:** Le trigger gère bien DELETE avec OLD.food_log_id

### ⚠️ Test Critique en Staging

```sql
-- Test 1: INSERT → totaux augmentent
BEGIN;
INSERT INTO food_logs (user_id, meal_type) 
VALUES ('test-user-id', 'breakfast')
RETURNING id;

-- Supposons id retourné = 'log-123'

INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'log-123', 'Test Food', 100, 'g',
    250, 10, 30, 8, 'manual'
);

SELECT total_calories FROM food_logs WHERE id = 'log-123';
-- Attendu: 250

-- Test 2: DELETE → totaux diminuent
DELETE FROM food_log_items WHERE food_log_id = 'log-123';

SELECT total_calories FROM food_logs WHERE id = 'log-123';
-- Attendu: 0

ROLLBACK;  -- Annuler le test
```

### 📋 Checklist C

- [ ] Migration 021 exécutée en staging
- [ ] Test INSERT item → totaux mis à jour ✅
- [ ] Test UPDATE item → totaux recalculés ✅
- [ ] Test DELETE item → totaux recalculés ✅ (critique)
- [ ] Test DELETE all items → totaux = 0
- [ ] Logs: Aucune erreur trigger

---

## D) RLS sur food_log_items / food_photos

### ✅ Vérifications Code

**Policies héritées via food_logs:**
```sql
-- INSERT policy (lignes 145-152 de 021_food_logs_extensible.sql)
CREATE POLICY "Users can insert own food log items" ON food_log_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()  -- ✅ Vérifie propriété
        )
    );
```

**✅ CORRECT:** Policies vérifient bien la propriété via JOIN

### ⚠️ Tests RLS Critiques en Staging

#### Test 1: INSERT sur food_log d'un autre user (doit REFUSER)

```sql
-- En tant que user A
SET request.jwt.claims.sub = 'user-a-id';

INSERT INTO food_logs (user_id, meal_type) 
VALUES ('user-a-id', 'breakfast')
RETURNING id;
-- Supposons id = 'log-a'

-- Tenter insertion en tant que user B sur log de A
SET request.jwt.claims.sub = 'user-b-id';

INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'log-a', 'Hack Food', 100, 'g',
    999, 99, 99, 99, 'manual'
);
-- Attendu: ERROR - new row violates row-level security policy
```

#### Test 2: SELECT jointure (doit retourner seulement own logs)

```sql
-- En tant que user A
SET request.jwt.claims.sub = 'user-a-id';

SELECT 
    fl.id,
    fl.meal_type,
    fli.food_name,
    fli.calories
FROM food_logs fl
JOIN food_log_items fli ON fli.food_log_id = fl.id;

-- Attendu: Seulement les logs de user A (jamais ceux de user B)
```

### 📋 Checklist D

- [ ] Test RLS: INSERT item sur log autre user → REFUS ✅
- [ ] Test RLS: UPDATE item sur log autre user → REFUS
- [ ] Test RLS: DELETE item sur log autre user → REFUS
- [ ] Test RLS: SELECT jointure → seulement own logs
- [ ] Test RLS: INSERT photo sur log autre user → REFUS
- [ ] Logs: Aucune erreur RLS policy violation en production

---

## E) Breaking change côté mobile : compat UI

### ✅ Vérifications Code

**Helpers de conversion dans baselines.ts:**
```typescript
// Lignes 60-83 de mobile/src/types/baselines.ts
export function robustToLegacy(robust: RobustBaseline): LegacyBaseline { ... }
export function legacyToRobust(legacy: LegacyBaseline): RobustBaseline { ... }
```
**✅ CORRECT:** Helpers disponibles

### ⚠️ Vérifications UI Critiques

#### 1. Écrans à tester avec baselines manquantes

**Liste écrans utilisant baselines:**
- `app/(tabs)/index.tsx` - Dashboard (Orb + anomalies)
- `app/(tabs)/profil.tsx` - Profil (section baselines)
- `app/(tabs)/tendances.tsx` - Tendances (si calcul percentiles)
- `app/details.tsx` - Détails métriques

**Code à vérifier:**
```typescript
// Exemple: Dashboard
const { baselines, loading, error } = useRobustBaselines(userId);

// ⚠️ VÉRIFIER: Que se passe-t-il si baselines === undefined ?
// ⚠️ VÉRIFIER: Que se passe-t-il si baselines === {} (objet vide) ?
// ⚠️ VÉRIFIER: Que se passe-t-il si sample_count < 10 ?
```

#### 2. Protection à ajouter

**Fichier:** `mobile/src/hooks/useRobustBaselines.ts`

```typescript
// Ajouter helper de validation
export function hasValidBaselines(baselines: RobustBaselines | undefined): boolean {
  if (!baselines) return false;
  
  // Au moins une baseline avec sample_count suffisant
  return Object.values(baselines).some(
    baseline => baseline.sample_count >= 10 && baseline.confidence !== 'low'
  );
}
```

**Utilisation dans Dashboard:**
```typescript
const { baselines } = useRobustBaselines(userId);
const hasData = hasValidBaselines(baselines);

if (!hasData) {
  return <EmptyState message="Collecte de données en cours... (min 10 jours)" />;
}
```

#### 3. Migration z_score → z_score_robust

**Fichier à vérifier:** Tous les composants qui affichent des anomalies

```typescript
// Ancien (DEPRECATED)
anomaly.z_score  // ❌ N'existe plus

// Nouveau
anomaly.z_score_robust  // ✅ Nouveau nom
```

**Grep à faire:**
```bash
cd mobile
grep -r "\.z_score" src/  # Chercher anciennes références
grep -r "z_score_robust" src/  # Vérifier nouvelles références
```

### 📋 Checklist E

- [ ] Grep mobile: aucune référence à `.z_score` (ancien)
- [ ] Grep mobile: toutes anomalies utilisent `.z_score_robust`
- [ ] Dashboard: Affichage correct si baselines manquantes
- [ ] Dashboard: Affichage correct si sample_count < 10
- [ ] Profil: Affichage correct si baselines vides
- [ ] Test device réel: Nouveau user (0 baseline) → pas de crash
- [ ] Test device réel: User avec <10 jours données → message explicite
- [ ] Helper `hasValidBaselines()` ajouté et utilisé

---

## 🚨 Validation Finale

### Checklist Globale

- [ ] **A) Migration 020:** Baselines recalculées en `baseline_v2_robust` (pas _migrated)
- [ ] **B) Z-score:** Aucun crash sur NaN/Inf/iqr=0
- [ ] **C) Triggers:** DELETE item met bien à jour totaux
- [ ] **D) RLS:** Impossible d'insérer sur food_log d'un autre user
- [ ] **E) Mobile UI:** Aucun crash si baselines manquantes

### Tests E2E Critiques

1. **Nouveau User (0 données)**
   - [ ] Créer compte → mobile ne crash pas
   - [ ] Dashboard affiche "Collecte en cours"
   - [ ] Profil affiche "Baselines en attente"

2. **User avec données partielles (<10 jours)**
   - [ ] Dashboard affiche anomalies avec confidence faible
   - [ ] Message explicite: "Données insuffisantes pour X"

3. **User avec données complètes (>60 jours)**
   - [ ] Baselines chargées en `baseline_v2_robust`
   - [ ] Anomalies détectées avec Z-score robuste
   - [ ] Orb affiche état correct (calm/warning/alert)

4. **Food Diary**
   - [ ] Créer repas → totaux calculés automatiquement
   - [ ] Ajouter item → totaux mis à jour
   - [ ] Supprimer item → totaux recalculés
   - [ ] Impossible d'éditer repas d'un autre user

### Monitoring Post-Production (48h)

- [ ] Logs backend: Aucune erreur calcul baselines
- [ ] Logs Supabase: RPC `get_user_baselines_robust` < 100ms
- [ ] Sentry/Firebase: 0 crashes liés à baselines
- [ ] Métriques: % users avec baselines valides
- [ ] Feedback: Anomalies détectées sont pertinentes (pas trop de faux positifs)

---

## 🔥 Actions Immédiates Requises

### Avant Merge PR

1. **Ajouter helper `hasValidBaselines()`** dans `mobile/src/hooks/useRobustBaselines.ts`
2. **Protéger Dashboard** contre baselines manquantes
3. **Grep `.z_score`** dans mobile et remplacer par `.z_score_robust`
4. **(Optionnel) Ajouter clamping Z-scores** à [-4, 4]

### En Staging

1. **Exécuter migrations** 020 + 021
2. **Forcer recalcul baselines** (cron manuel)
3. **Tester tous les scénarios RLS** (INSERT/UPDATE/DELETE)
4. **Tester triggers** (INSERT/UPDATE/DELETE items)
5. **Tester mobile** avec nouveau user (0 données)

### En Production

1. **Backup complet** avant migration
2. **Exécuter migrations** en heures creuses
3. **Forcer recalcul baselines** sous 24h
4. **Monitoring intensif** 48h

---

**Reviewer:** ________________  
**Date validation:** ________________  
**Signature:** ________________

---

*Checklist créée le 30 Janvier 2026*  
*Basée sur review de dannezri*
