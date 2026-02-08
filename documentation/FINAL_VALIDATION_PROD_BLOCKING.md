# 🚨 VALIDATION FINALE - 3 CHECKS PROD-BLOCKING

**Date:** 30 Janvier 2026  
**Branche:** `feature/robust-baselines-corrections`  
**Validateur:** dannezri

---

## ⚠️ PROD-BLOCKING - À Exécuter AVANT Merge

Ces 3 checks **DOIVENT** passer en staging. Aucun merge sans validation.

---

### ✅ CHECK 1 — Baselines Recalculées (PROD-BLOCKING)

**Problème si non validé:** App consomme baselines approximées (mean/std → median/IQR)

**Commande de validation:**

```sql
-- 1. Vérifier versions existantes
SELECT 
    model_version,
    COUNT(*) as users_count,
    MAX(calculated_at) as last_calculated
FROM user_baselines
GROUP BY model_version
ORDER BY model_version;

-- Résultat attendu AVANT recalcul:
-- baseline_v2_robust_migrated | N | <date_migration>

-- 2. Forcer recalcul (backend)
```

```bash
cd backend
python cron_calculate_baselines.py --force-all
```

```sql
-- 3. Vérifier qu'au moins 1 user a des vraies baselines robustes
SELECT COUNT(DISTINCT user_id) as users_with_robust_baselines
FROM user_baselines
WHERE model_version = 'baseline_v2_robust';

-- Résultat attendu: > 0 (au moins 1 user)
```

**✅ PASS:** Au moins 1 user avec `model_version = 'baseline_v2_robust'`  
**❌ FAIL:** Tous users en `baseline_v2_robust_migrated` → BLOQUER MERGE

---

### ✅ CHECK 2 — Trigger DELETE (PROD-BLOCKING)

**Problème si non validé:** Calories fantômes restent après suppression d'items

**Commande de validation:**

```sql
BEGIN;

-- 1. Créer food_log
INSERT INTO food_logs (user_id, meal_type) 
VALUES (auth.uid(), 'test')
RETURNING id;
-- Noter l'ID: LOG_ID

-- 2. Ajouter item
INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'LOG_ID',  -- Remplacer par ID du log
    'Test Food', 100, 'g',
    250, 10, 30, 8, 'manual'
)
RETURNING id;
-- Noter l'ID: ITEM_ID

-- 3. Vérifier totaux AVANT DELETE
SELECT total_calories, total_protein, total_carbs, total_fat
FROM food_logs 
WHERE id = 'LOG_ID';
-- Attendu: 250, 10, 30, 8

-- 4. DELETE item (TEST CRITIQUE)
DELETE FROM food_log_items 
WHERE id = 'ITEM_ID';

-- 5. Vérifier totaux APRÈS DELETE
SELECT total_calories, total_protein, total_carbs, total_fat
FROM food_logs 
WHERE id = 'LOG_ID';
-- CRITIQUE: DOIT RETOURNER 0, 0, 0, 0

ROLLBACK;
```

**✅ PASS:** Totaux = 0 après DELETE  
**❌ FAIL:** Totaux restent à 250 → BLOQUER MERGE (trigger cassé)

---

### ✅ CHECK 3 — RLS Anti-Leak (PROD-BLOCKING)

**Problème si non validé:** User B peut écrire dans logs de User A (faille sécurité)

**Commande de validation:**

```sql
BEGIN;

-- 1. User A crée un food_log
SET request.jwt.claims.sub = 'user-a-test-uuid';

INSERT INTO food_logs (user_id, meal_type) 
VALUES ('user-a-test-uuid', 'breakfast')
RETURNING id;
-- Noter l'ID: LOG_ID_USER_A

-- 2. User B tente d'insérer item sur log de User A (DOIT ÉCHOUER)
SET request.jwt.claims.sub = 'user-b-test-uuid';

INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'LOG_ID_USER_A',  -- Log de User A
    'Hacked Food', 100, 'g',
    999, 99, 99, 99, 'manual'
);
-- DOIT ÉCHOUER avec: ERROR - new row violates row-level security policy

ROLLBACK;
```

**✅ PASS:** Erreur RLS `new row violates row-level security policy`  
**❌ FAIL:** INSERT réussit → BLOQUER MERGE (faille sécurité critique)

---

## 📊 Validation Rapide - Copy/Paste Ready

### Script Complet (PostgreSQL)

```sql
-- ========================================
-- VALIDATION COMPLÈTE - 3 CHECKS
-- ========================================

-- CHECK 1: Baselines recalculées
SELECT 
    'CHECK 1: Baselines' as test,
    COUNT(DISTINCT user_id) as users_with_robust,
    CASE 
        WHEN COUNT(DISTINCT user_id) > 0 THEN '✅ PASS'
        ELSE '❌ FAIL - BLOQUER MERGE'
    END as status
FROM user_baselines
WHERE model_version = 'baseline_v2_robust';

-- CHECK 2: Trigger DELETE
BEGIN;
INSERT INTO food_logs (user_id, meal_type) VALUES (auth.uid(), 'test') RETURNING id;
-- REMPLACER LOG_ID ci-dessous
INSERT INTO food_log_items (food_log_id, food_name, serving_size, serving_unit, calories, protein, carbs, fat, source) 
VALUES ('LOG_ID', 'Test', 100, 'g', 250, 10, 30, 8, 'manual') RETURNING id;
-- REMPLACER ITEM_ID ci-dessous
SELECT 'Before DELETE' as moment, total_calories FROM food_logs WHERE id = 'LOG_ID';
DELETE FROM food_log_items WHERE id = 'ITEM_ID';
SELECT 
    'CHECK 2: Trigger DELETE' as test,
    total_calories,
    CASE 
        WHEN total_calories = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - BLOQUER MERGE (calories fantômes)'
    END as status
FROM food_logs WHERE id = 'LOG_ID';
ROLLBACK;

-- CHECK 3: RLS Anti-Leak
BEGIN;
SET request.jwt.claims.sub = 'user-a-test';
INSERT INTO food_logs (user_id, meal_type) VALUES ('user-a-test', 'test') RETURNING id;
-- REMPLACER LOG_ID ci-dessous
SET request.jwt.claims.sub = 'user-b-test';
-- Cette requête DOIT échouer
INSERT INTO food_log_items (food_log_id, food_name, serving_size, serving_unit, calories, protein, carbs, fat, source) 
VALUES ('LOG_ID', 'Hack', 100, 'g', 999, 99, 99, 99, 'manual');
-- Si pas d'erreur RLS = ❌ FAIL - BLOQUER MERGE
ROLLBACK;
```

---

## ⚠️ Risque Résiduel (NON-BLOQUANT)

### Propagation Mobile des Nouvelles Baselines

**Symptômes possibles post-déploiement:**

1. **Écrans supposant mean/std**
   - Ancien code mobile référençant `baseline.mean` ou `baseline.std`
   - Graceful degradation via helpers `robustToLegacy()`
   - **Impact:** Affichage dégradé mais pas de crash

2. **Données manquantes (users < 10 jours)**
   - Dashboard affiche "Collecte en cours..."
   - Baselines absentes ou confidence "low"
   - **Impact:** UX attendue, pas de bug

3. **Baselines migrées temporaires**
   - Users avec `baseline_v2_robust_migrated` jusqu'au prochain cron
   - Détection anomalies fonctionne (approximation acceptable)
   - **Impact:** Précision réduite temporairement (24-48h)

**Monitoring Post-Déploiement (48h):**

```bash
# Logs backend
tail -f backend/logs/app.log | grep -i "baseline\|anomaly"

# Métriques Supabase
# Dashboard > Observability > Logs
# Chercher: "get_user_baselines_robust"

# Sentry/Firebase (mobile)
# Chercher crashes liés à baselines
```

**Actions si problème:**

1. **Crash mobile sur baselines manquantes**
   → Déployer hotfix avec `hasValidBaselines()` check

2. **Tous users en _migrated après 48h**
   → Forcer recalcul cron manuel

3. **Anomalies faux positifs**
   → Ajuster seuil threshold_sigma (de 2.0 à 2.5)

**✅ Non-bloquant car:**
- Helpers de conversion en place
- Validation données dans hooks
- Dégradation gracieuse implémentée
- Rollback possible si critique

---

## 🚀 Décision Merge

### ✅ MERGE AUTORISÉ SI:

```
✅ CHECK 1: Au moins 1 user avec baseline_v2_robust
✅ CHECK 2: DELETE item → totaux = 0
✅ CHECK 3: RLS refuse INSERT cross-user
✅ Smoke tests passent en staging
✅ Review code approuvée
```

### ❌ BLOQUER MERGE SI:

```
❌ Un des 3 checks échoue
❌ Smoke tests échouent
❌ Migrations corrompent données existantes
```

---

## 📋 Checklist Exécution

**Staging:**
- [ ] Migration 020 exécutée
- [ ] Migration 021 exécutée
- [ ] **CHECK 1:** Baselines recalculées ✅
- [ ] **CHECK 2:** Trigger DELETE ✅
- [ ] **CHECK 3:** RLS anti-leak ✅
- [ ] Smoke tests: `./backend/smoke-test-post-migration.sh https://staging.pulse.com`
- [ ] Test mobile: Device réel, nouveau user (0 baselines)

**Production (après validation staging):**
- [ ] Backup complet DB
- [ ] Migrations 020 + 021
- [ ] **CHECK 1:** Forcer recalcul baselines
- [ ] **CHECK 2:** Valider trigger DELETE (test rapide)
- [ ] **CHECK 3:** Valider RLS (test rapide)
- [ ] Smoke tests: `./backend/smoke-test-post-migration.sh https://api.pulse.com`
- [ ] Monitoring 48h: Baselines + RLS + Mobile crashes

---

## ✅ Validation Finale

**Validé par:** ________________  
**Date:** ________________  
**Résultat 3 Checks:**
- CHECK 1: ☐ PASS ☐ FAIL
- CHECK 2: ☐ PASS ☐ FAIL  
- CHECK 3: ☐ PASS ☐ FAIL

**Décision:** ☐ MERGE AUTORISÉ ☐ BLOQUER

---

**Branche:** `feature/robust-baselines-corrections`  
**PR:** https://github.com/dannezri/pulse/pull/new/feature/robust-baselines-corrections  
**Commits:** 4 (6,390 lignes)

**FEU VERT POUR MERGE après validation des 3 checks en staging** 🚀
