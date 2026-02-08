# ✅ PRE-MERGE CHECKLIST - Non-Négociable

**Branche:** `feature/robust-baselines-corrections`  
**Date:** 30 Janvier 2026  
**Reviewer:** dannezri

---

## 🚨 3 Checks NON-NÉGOCIABLES

### ✅ 1. Migration Baselines → model_version clair + recalcul programmé

**Status:** À valider en staging

#### Vérification SQL

```sql
-- Après migration 020 en staging
SELECT 
    model_version,
    COUNT(*) as count,
    MIN(calculated_at) as oldest,
    MAX(calculated_at) as newest
FROM user_baselines
GROUP BY model_version;

-- Résultat attendu:
-- baseline_v2_robust_migrated | N | <date_migration> | <date_migration>
-- (Temporaire, sera remplacé par baseline_v2_robust après cron)
```

#### Recalcul Programmé

```bash
# Option A: Cron forcé immédiat (RECOMMANDÉ)
cd backend
python cron_calculate_baselines.py --force-all

# Option B: Vérifier cron planifié (dans les 24h)
crontab -l | grep baseline

# Validation: Au moins 1 user avec baseline_v2_robust (pas _migrated)
SELECT COUNT(DISTINCT user_id) 
FROM user_baselines 
WHERE model_version = 'baseline_v2_robust';
-- Attendu: > 0 après recalcul
```

#### ✅ Checklist
- [ ] Migration 020 exécutée en staging
- [ ] model_version = `baseline_v2_robust_migrated` pour migrations
- [ ] Cron de recalcul planifié OU exécuté manuellement
- [ ] Au moins 1 user avec `baseline_v2_robust` après recalcul
- [ ] Logs: Aucune erreur calcul baselines

---

### ✅ 2. Triggers totals OK sur DELETE (NEW vs OLD)

**Status:** Code correct, à valider en staging

#### Code Critique (Migration 021)

```sql
-- Ligne 264-268 de 021_food_logs_extensible.sql
IF TG_OP = 'DELETE' THEN
    log_id := OLD.food_log_id;  -- ✅ CORRECT: OLD sur DELETE
ELSE
    log_id := NEW.food_log_id;
END IF;
```

#### Test Validation

```sql
-- Test complet INSERT → UPDATE → DELETE
BEGIN;

-- 1. Créer food_log
INSERT INTO food_logs (user_id, meal_type) 
VALUES (auth.uid(), 'breakfast')
RETURNING id;
-- Supposons id = 'test-log-123'

-- 2. Ajouter item (INSERT)
INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'test-log-123', 'Test Food', 100, 'g',
    250, 10, 30, 8, 'manual'
) RETURNING id;
-- Supposons id = 'test-item-456'

-- Vérifier totaux après INSERT
SELECT total_calories, total_protein, total_carbs, total_fat 
FROM food_logs WHERE id = 'test-log-123';
-- Attendu: 250, 10, 30, 8

-- 3. Modifier item (UPDATE)
UPDATE food_log_items 
SET calories = 300, protein = 15 
WHERE id = 'test-item-456';

-- Vérifier totaux après UPDATE
SELECT total_calories, total_protein 
FROM food_logs WHERE id = 'test-log-123';
-- Attendu: 300, 15

-- 4. Supprimer item (DELETE) ⚠️ CHECK CRITIQUE
DELETE FROM food_log_items WHERE id = 'test-item-456';

-- Vérifier totaux après DELETE
SELECT total_calories, total_protein, total_carbs, total_fat 
FROM food_logs WHERE id = 'test-log-123';
-- Attendu: 0, 0, 0, 0 ✅ SI TRIGGER FONCTIONNE

ROLLBACK;  -- Annuler le test
```

#### ✅ Checklist
- [ ] Migration 021 exécutée en staging
- [ ] Test INSERT item → totaux mis à jour ✅
- [ ] Test UPDATE item → totaux recalculés ✅
- [ ] **Test DELETE item → totaux mis à jour à 0** ✅ (CRITIQUE)
- [ ] Logs: Aucune erreur trigger

---

### ✅ 3. RLS Validée (anti-leak)

**Status:** Code correct, à valider en staging

#### Code Critique (Migration 021)

```sql
-- Ligne 145-152 de 021_food_logs_extensible.sql
CREATE POLICY "Users can insert own food log items" ON food_log_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()  -- ✅ Vérifie propriété
        )
    );
```

#### Test Validation (CRITIQUE SÉCURITÉ)

```sql
-- Scénario: User B tente d'insérer item sur food_log de User A
BEGIN;

-- 1. User A crée un food_log
SET request.jwt.claims.sub = 'user-a-uuid';

INSERT INTO food_logs (user_id, meal_type) 
VALUES ('user-a-uuid', 'breakfast')
RETURNING id;
-- Supposons id = 'log-user-a'

-- 2. User B tente d'insérer item sur log de A
SET request.jwt.claims.sub = 'user-b-uuid';

-- ⚠️ CETTE REQUÊTE DOIT ÉCHOUER
INSERT INTO food_log_items (
    food_log_id, food_name, serving_size, serving_unit,
    calories, protein, carbs, fat, source
) VALUES (
    'log-user-a', 'Hacked Food', 100, 'g',
    999, 99, 99, 99, 'manual'
);

-- Attendu: 
-- ERROR: new row violates row-level security policy for table "food_log_items"

ROLLBACK;
```

#### Test SELECT Jointure

```sql
-- User A ne doit voir QUE ses propres logs
SET request.jwt.claims.sub = 'user-a-uuid';

SELECT 
    fl.id as log_id,
    fl.user_id,
    fli.food_name,
    fli.calories
FROM food_logs fl
JOIN food_log_items fli ON fli.food_log_id = fl.id;

-- Attendu: SEULEMENT les logs de user-a-uuid
-- JAMAIS de logs d'autres users
```

#### ✅ Checklist
- [ ] Migration 021 exécutée en staging
- [ ] **Test INSERT cross-user → REFUSÉ** ✅ (CRITIQUE)
- [ ] **Test UPDATE cross-user → REFUSÉ** ✅
- [ ] **Test DELETE cross-user → REFUSÉ** ✅
- [ ] Test SELECT jointure → seulement own logs ✅
- [ ] Test food_photos cross-user → REFUSÉ ✅
- [ ] Logs: Aucune erreur RLS policy violation

---

## 📋 Checklist Globale Rapide

### Review Code (30 min)
- [ ] Backend: lib/stats.py (robustesse)
- [ ] Backend: priority_engine.py (Z-Score robuste)
- [ ] SQL: Migration 020 (baselines)
- [ ] SQL: Migration 021 (food diary + triggers + RLS)
- [ ] Mobile: Types et hooks robustes
- [ ] Script: smoke-test-post-migration.sh

### Staging Migrations (1h)
- [ ] **CHECK 1:** model_version + recalcul ✅
- [ ] **CHECK 2:** Triggers DELETE ✅
- [ ] **CHECK 3:** RLS anti-leak ✅
- [ ] Smoke tests: `./backend/smoke-test-post-migration.sh https://staging.pulse.com`
- [ ] Mobile test: Device réel avec nouveau user

### Production (après validation staging)
- [ ] Backup complet DB
- [ ] Exécuter migrations (020 puis 021)
- [ ] **CHECK 1:** Forcer recalcul baselines
- [ ] **CHECK 2:** Valider triggers
- [ ] **CHECK 3:** Valider RLS
- [ ] Smoke tests: `./backend/smoke-test-post-migration.sh https://api.pulse.com`
- [ ] Monitoring 48h

---

## 🚀 Validation Rapide (Copy-Paste)

### Check 1: model_version

```sql
SELECT model_version, COUNT(*) FROM user_baselines GROUP BY model_version;
```

### Check 2: Trigger DELETE

```sql
BEGIN;
INSERT INTO food_logs (user_id, meal_type) VALUES (auth.uid(), 'test') RETURNING id;
INSERT INTO food_log_items (food_log_id, food_name, serving_size, serving_unit, calories, protein, carbs, fat, source) VALUES ('REPLACE-WITH-ID', 'Test', 100, 'g', 250, 10, 30, 8, 'manual') RETURNING id;
SELECT total_calories FROM food_logs WHERE id = 'REPLACE-WITH-ID';  -- Attendu: 250
DELETE FROM food_log_items WHERE id = 'REPLACE-WITH-ITEM-ID';
SELECT total_calories FROM food_logs WHERE id = 'REPLACE-WITH-ID';  -- Attendu: 0
ROLLBACK;
```

### Check 3: RLS

```sql
-- Doit échouer (cross-user insert)
BEGIN;
SET request.jwt.claims.sub = 'user-a';
INSERT INTO food_logs (user_id, meal_type) VALUES ('user-a', 'test') RETURNING id;
SET request.jwt.claims.sub = 'user-b';
INSERT INTO food_log_items (food_log_id, food_name, serving_size, serving_unit, calories, protein, carbs, fat, source) VALUES ('REPLACE-WITH-ID', 'Hack', 100, 'g', 999, 99, 99, 99, 'manual');
-- Attendu: ERROR - new row violates row-level security policy
ROLLBACK;
```

---

## ✅ Feu Vert pour Merge

Conditions:
- [ ] 3 checks non-négociables validés en staging
- [ ] Smoke tests passent en staging
- [ ] Review code complétée
- [ ] PR approuvée

**Merge autorisé après validation de ces 3 checks critiques.**

---

*Checklist validée par: ________________*  
*Date: ________________*  
*Signature: ________________*
