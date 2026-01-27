# Guide de Vérification du Schéma Supabase

Ce guide explique comment vérifier et corriger le schéma de votre base de données Supabase.

## 🔍 Problème détecté

Vous avez mentionné que la base de données Supabase n'a peut-être pas été mise à jour correctement avec les champs nécessaires. Ce guide vous aide à identifier et corriger les problèmes.

## 📋 Champs requis par le code

### Table `profiles`
- ✅ `id` (UUID, PRIMARY KEY)
- ✅ `open_wearables_user_id` (TEXT, UNIQUE) - **CRITIQUE**
- ✅ `health_goal` (TEXT, DEFAULT 'energy')
- ✅ `baseline_hrv` (INTEGER, nullable)
- ✅ `baseline_resting_hr` (INTEGER, nullable)

### Table `biometrics`
- ✅ `id` (BIGSERIAL, PRIMARY KEY)
- ✅ `user_id` (UUID, FOREIGN KEY vers profiles)
- ✅ `metric_type` (TEXT, NOT NULL)
- ✅ `value` (FLOAT, NOT NULL)
- ✅ `recorded_at` (TIMESTAMP WITH TIME ZONE, NOT NULL)
- ✅ `raw_data` (JSONB, nullable)
- ✅ `source` (TEXT, nullable)

### Table `health_profiles`
- ✅ `id` (UUID, PRIMARY KEY)
- ✅ `user_id` (UUID, FOREIGN KEY vers profiles)
- ✅ `profile_data` (JSONB, NOT NULL)
- ✅ `date` (DATE, NOT NULL)
- ✅ UNIQUE constraint sur `(user_id, date)`

## 🛠️ Méthode 1 : Vérification automatique (Recommandé)

Exécutez le script de vérification qui teste automatiquement tous les champs :

```bash
cd backend
python verify_schema.py
```

Ce script va :
1. ✅ Se connecter à Supabase
2. ✅ Vérifier la structure de chaque table
3. ✅ Tester les insertions/requêtes
4. ✅ Générer un SQL de migration si nécessaire

**Exemple de sortie :**
```
============================================================
VÉRIFICATION DU SCHÉMA SUPABASE
============================================================
✅ Connexion à Supabase réussie

============================================================
Vérification de la table: profiles
============================================================
✅ Tous les champs attendus sont présents

============================================================
Vérification de la table: biometrics
============================================================
❌ Champs manquants: source
```

## 🛠️ Méthode 2 : Correction manuelle avec SQL

Si des champs manquent, exécutez la migration SQL dans Supabase :

1. **Ouvrez Supabase Dashboard** → SQL Editor
2. **Copiez le contenu** de `database/migrations/002_fix_schema.sql`
3. **Exécutez le SQL**

Cette migration :
- ✅ Ajoute les champs manquants
- ✅ Convertit les types si nécessaire (ex: TEXT → JSONB)
- ✅ Ajoute les contraintes UNIQUE
- ✅ Crée les index nécessaires
- ✅ Configure les politiques RLS pour le service role

## 🔍 Vérification manuelle dans Supabase

### Via l'interface Supabase

1. **Table Editor** → Sélectionnez une table
2. Vérifiez que toutes les colonnes listées ci-dessus sont présentes
3. Vérifiez les types de données

### Via SQL

```sql
-- Vérifier les colonnes de profiles
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'profiles'
ORDER BY ordinal_position;

-- Vérifier les colonnes de biometrics
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'biometrics'
ORDER BY ordinal_position;

-- Vérifier les colonnes de health_profiles
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'health_profiles'
ORDER BY ordinal_position;
```

## ⚠️ Problèmes courants et solutions

### Problème 1 : "Column 'open_wearables_user_id' does not exist"

**Symptôme :** Erreur lors de `get_user_by_open_wearables_id()`

**Solution :**
```sql
ALTER TABLE profiles ADD COLUMN open_wearables_user_id TEXT;
ALTER TABLE profiles ADD CONSTRAINT profiles_open_wearables_user_id_key UNIQUE (open_wearables_user_id);
CREATE INDEX idx_profiles_open_wearables_user_id ON profiles(open_wearables_user_id);
```

### Problème 2 : "Column 'source' does not exist"

**Symptôme :** Erreur lors de l'insertion dans `biometrics`

**Solution :**
```sql
ALTER TABLE biometrics ADD COLUMN source TEXT;
```

### Problème 3 : "raw_data is not JSONB"

**Symptôme :** Erreur de type lors de l'insertion

**Solution :**
```sql
ALTER TABLE biometrics ALTER COLUMN raw_data TYPE JSONB USING raw_data::jsonb;
```

### Problème 4 : "RLS policy violation"

**Symptôme :** Erreur "new row violates row-level security policy"

**Solution :** Exécutez la section RLS de la migration :
```sql
CREATE POLICY "Service role can insert biometrics" ON biometrics
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can insert health profiles" ON health_profiles
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update profiles" ON profiles
    FOR UPDATE USING (true);
```

### Problème 5 : "Duplicate key value violates unique constraint"

**Symptôme :** Erreur lors de l'upsert dans `health_profiles`

**Solution :**
```sql
ALTER TABLE health_profiles ADD CONSTRAINT health_profiles_user_id_date_key UNIQUE (user_id, date);
```

## ✅ Checklist de vérification

Après avoir exécuté la migration, vérifiez :

- [ ] `profiles.open_wearables_user_id` existe et est UNIQUE
- [ ] `profiles.baseline_hrv` existe (INTEGER, nullable)
- [ ] `profiles.baseline_resting_hr` existe (INTEGER, nullable)
- [ ] `profiles.health_goal` existe (TEXT, default 'energy')
- [ ] `biometrics.source` existe (TEXT, nullable)
- [ ] `biometrics.raw_data` est de type JSONB
- [ ] `health_profiles.profile_data` est de type JSONB
- [ ] Contrainte UNIQUE sur `health_profiles(user_id, date)`
- [ ] Index sur `profiles.open_wearables_user_id`
- [ ] Policies RLS pour le service role

## 🧪 Test après correction

Une fois la migration exécutée, testez avec :

```bash
# Test complet du flux
python test_webhook_flow.py

# Ou vérification du schéma
python verify_schema.py
```

## 📝 Notes importantes

1. **Service Role Key** : Assurez-vous d'utiliser la `SUPABASE_SERVICE_KEY` (pas l'anon key) dans votre `.env` pour contourner RLS
2. **Backup** : Faites un backup avant d'exécuter les migrations en production
3. **Downtime** : Les migrations sont généralement instantanées, mais évitez les heures de pointe

## 🆘 Besoin d'aide ?

Si vous rencontrez des problèmes :

1. Vérifiez les logs dans Supabase Dashboard → Logs
2. Exécutez `verify_schema.py` pour un diagnostic détaillé
3. Vérifiez que vous utilisez la bonne clé API (service role)
4. Consultez les erreurs spécifiques dans les logs Python
