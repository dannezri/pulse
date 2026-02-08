# Comment appliquer les migrations Supabase

## 🎯 Migration 032: Table medications

### Option 1 : Via Supabase Dashboard (Recommandé)

1. Ouvrir [Supabase Dashboard](https://app.supabase.com)
2. Sélectionner votre projet Pulse
3. Aller dans **SQL Editor** (icône </> dans la barre latérale)
4. Cliquer sur **New Query**
5. Copier-coller le contenu de `032_medications.sql`
6. Cliquer sur **Run** (ou `Cmd+Enter`)
7. Vérifier que "Success. No rows returned" s'affiche

### Option 2 : Via psql en ligne de commande

```bash
# Depuis le dossier database/migrations
cd /Users/dannezri/Desktop/Pulse/database/migrations

# Appliquer la migration
psql $DATABASE_URL -f 032_medications.sql

# Ou si vous avez les variables d'environnement
psql "postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres" \
  -f 032_medications.sql
```

### Option 3 : Via le backend Python (si disponible)

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Avec supabase CLI
supabase db push

# Ou manuellement
python apply_migration.py migrations/032_medications.sql
```

---

## ✅ Vérification

### 1. Vérifier que la table existe

```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'medications';
```

**Résultat attendu :**
```
table_name  | table_type
medications | BASE TABLE
```

### 2. Vérifier les colonnes

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'medications'
ORDER BY ordinal_position;
```

**Colonnes attendues :**
- id (uuid)
- user_id (uuid)
- name (text)
- dosage (text)
- unit (text)
- pills_per_intake (double precision)
- frequency (text)
- intake_times (ARRAY)
- daily_frequency (integer)
- notes (text)
- taken_at (timestamp with time zone)
- created_at (timestamp with time zone)
- updated_at (timestamp with time zone)

### 3. Vérifier les index

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'medications';
```

**Index attendus :**
- idx_medications_user_id
- idx_medications_user_taken_at
- idx_medications_user_created_at

### 4. Vérifier les policies RLS

```sql
SELECT policyname, cmd, qual
FROM pg_policies
WHERE tablename = 'medications';
```

**Policies attendues :**
- Users can view own medications (SELECT)
- Users can insert own medications (INSERT)
- Users can update own medications (UPDATE)
- Users can delete own medications (DELETE)

### 5. Test d'insertion

```sql
-- Remplacer [USER_ID] par un vrai UUID d'utilisateur
INSERT INTO medications (
  user_id, name, dosage, unit, taken_at
) VALUES (
  '[USER_ID]',
  'Test Medication',
  '500',
  'mg',
  NOW()
);

-- Vérifier
SELECT * FROM medications WHERE name = 'Test Medication';

-- Nettoyer
DELETE FROM medications WHERE name = 'Test Medication';
```

---

## 🚨 En cas d'erreur

### Erreur : "relation medications already exists"

La table existe déjà. Vous pouvez :
- Ignorer (la migration a déjà été appliquée)
- Ou supprimer et recréer :

```sql
DROP TABLE IF EXISTS medications CASCADE;
-- Puis ré-exécuter la migration
```

### Erreur : "permission denied"

Vérifiez que vous utilisez le bon utilisateur postgres :

```sql
-- Vérifier l'utilisateur actuel
SELECT current_user;

-- Devrait être 'postgres' ou avoir les droits CREATE TABLE
```

### Erreur : "column already exists"

Si vous avez modifié la migration, supprimez et recréez :

```sql
DROP TABLE IF EXISTS medications CASCADE;
-- Puis ré-exécuter la migration complète
```

---

## 📊 Monitoring post-migration

### Surveiller les premières insertions

```sql
-- Voir les derniers médicaments ajoutés
SELECT id, user_id, name, created_at
FROM medications
ORDER BY created_at DESC
LIMIT 10;

-- Compter par utilisateur
SELECT user_id, COUNT(*) as total_medications
FROM medications
GROUP BY user_id
ORDER BY total_medications DESC;
```

### Vérifier les performances

```sql
-- Analyser les query plans
EXPLAIN ANALYZE
SELECT * FROM medications
WHERE user_id = '[USER_ID]'
ORDER BY taken_at DESC;

-- Devrait utiliser l'index idx_medications_user_taken_at
```

---

## 🔄 Rollback (si nécessaire)

Si vous devez annuler la migration :

```sql
-- Supprimer la table
DROP TABLE IF EXISTS medications CASCADE;

-- Supprimer les policies (déjà fait par CASCADE)
-- Supprimer les index (déjà fait par CASCADE)
-- Supprimer les triggers (déjà fait par CASCADE)
```

⚠️ **Attention** : Cela supprimera toutes les données de la table !

---

## ✅ Checklist finale

- [ ] Migration SQL exécutée sans erreur
- [ ] Table `medications` existe
- [ ] Toutes les colonnes présentes
- [ ] Index créés (3 index)
- [ ] Policies RLS actives (4 policies)
- [ ] Trigger `updated_at` fonctionnel
- [ ] Test d'insertion réussi
- [ ] App mobile teste la sync
- [ ] Logs confirment la synchronisation

---

## 📞 Support

En cas de problème :
1. Vérifier les logs Supabase Dashboard → Logs
2. Vérifier les logs mobile → Console
3. Consulter la documentation : `MEDICATION_SUPABASE_SYNC.md`

**Status actuel : Migration prête à être appliquée ! 🚀**
