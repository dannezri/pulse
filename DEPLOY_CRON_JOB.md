# Déploiement du Cron Job Quotidien - Historique des Médicaments 🕐

## Ce qui a été créé

### 1. **Fonction SQL** ✅
- `daily_medication_sync()` : Fonction qui génère l'historique pour tous les utilisateurs
- `cron_medication_sync_logs` : Table pour logger les exécutions
- Cron job `pg_cron` configuré pour s'exécuter **chaque jour à minuit UTC**

### 2. **Edge Function** ✅
- `daily-medication-sync` : Alternative pour déclencher manuellement ou via webhook
- Fichiers créés dans `supabase/functions/daily-medication-sync/`

---

## 🚀 Déploiement

### Option A: Utiliser pg_cron (Déjà activé)

Le cron job est **déjà configuré** et s'exécutera automatiquement chaque jour à **00:00 UTC** (01:00 heure de Paris en hiver, 02:00 en été).

**Vérifier que le cron est actif :**
```sql
-- Dans Supabase SQL Editor
SELECT * FROM cron.job WHERE jobname = 'daily_medication_history_sync';
```

**Résultat attendu :**
```
jobid | schedule    | command                          | nodename  | ...
------|-------------|----------------------------------|-----------|----
  1   | 0 0 * * *   | SELECT daily_medication_sync();  | localhost | ...
```

**Tester manuellement le cron :**
```sql
-- Exécuter immédiatement (pour tester)
SELECT daily_medication_sync();
```

**Voir les logs d'exécution :**
```sql
-- Dernières exécutions
SELECT * FROM cron_medication_sync_logs 
ORDER BY execution_time DESC 
LIMIT 10;
```

---

### Option B: Déployer l'Edge Function (Facultatif)

Si vous voulez pouvoir déclencher manuellement ou via webhook :

```bash
cd /Users/dannezri/Desktop/Pulse

# 1. Déployer la fonction
supabase functions deploy daily-medication-sync

# 2. Tester la fonction
curl -X POST "https://YOUR_PROJECT_REF.supabase.co/functions/v1/daily-medication-sync" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

---

## 📊 Monitoring

### Vérifier les dernières exécutions
```sql
SELECT 
  execution_time,
  users_processed,
  success_count,
  error_count,
  duration_ms,
  status
FROM cron_medication_sync_logs
ORDER BY execution_time DESC
LIMIT 20;
```

### Voir les détails d'une exécution
```sql
SELECT 
  execution_time,
  details
FROM cron_medication_sync_logs
WHERE status != 'success'
ORDER BY execution_time DESC;
```

### Statistiques
```sql
SELECT 
  DATE(execution_time) as date,
  SUM(users_processed) as total_users,
  SUM(success_count) as total_success,
  SUM(error_count) as total_errors,
  AVG(duration_ms) as avg_duration_ms
FROM cron_medication_sync_logs
GROUP BY DATE(execution_time)
ORDER BY date DESC;
```

---

## ⚙️ Configuration

### Changer l'heure d'exécution

Par défaut : **00:00 UTC** (minuit)

Pour changer (par exemple à 02:00 UTC) :
```sql
-- Supprimer l'ancien cron
SELECT cron.unschedule('daily_medication_history_sync');

-- Créer le nouveau cron à 02:00 UTC
SELECT cron.schedule(
  'daily_medication_history_sync',
  '0 2 * * *',  -- ← Modifié
  'SELECT daily_medication_sync();'
);
```

**Format cron :**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Jour de la semaine (0-7, 0 et 7 = Dimanche)
│ │ │ └───── Mois (1-12)
│ │ └─────── Jour du mois (1-31)
│ └───────── Heure (0-23)
└─────────── Minute (0-59)
```

**Exemples :**
- `0 0 * * *` : Tous les jours à minuit
- `0 2 * * *` : Tous les jours à 02:00
- `30 8 * * *` : Tous les jours à 08:30
- `0 0 * * 0` : Tous les dimanches à minuit
- `0 0 1 * *` : Le premier de chaque mois à minuit

---

## 🐛 Dépannage

### Le cron ne s'exécute pas

**1. Vérifier que pg_cron est activé :**
```sql
SELECT * FROM pg_extension WHERE extname = 'pg_cron';
```

Si vide, l'activer :
```sql
CREATE EXTENSION pg_cron;
```

**2. Vérifier que le cron existe :**
```sql
SELECT * FROM cron.job;
```

**3. Voir les erreurs dans les logs :**
```sql
SELECT * FROM cron_medication_sync_logs 
WHERE status != 'success' 
ORDER BY execution_time DESC;
```

### Erreur "permission denied"

Si pg_cron n'a pas les permissions :
```sql
-- Donner les permissions à pg_cron
GRANT USAGE ON SCHEMA public TO cron;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO cron;
```

### Le cron s'exécute mais rien ne se passe

**Vérifier que la fonction SQL fonctionne :**
```sql
-- Test manuel
SELECT * FROM auto_populate_medication_history('USER_ID_TEST');
```

**Vérifier les utilisateurs actifs :**
```sql
SELECT DISTINCT user_id 
FROM user_medications 
WHERE is_active = true;
```

---

## 🔄 Désactiver/Réactiver le Cron

### Désactiver temporairement
```sql
SELECT cron.unschedule('daily_medication_history_sync');
```

### Réactiver
```sql
SELECT cron.schedule(
  'daily_medication_history_sync',
  '0 0 * * *',
  'SELECT daily_medication_sync();'
);
```

---

## 📈 Optimisations Futures

### 1. Alertes en cas d'échec
Créer une notification Slack/Email si `error_count > 0`

### 2. Retry automatique
Ajouter une logique de retry pour les utilisateurs en erreur

### 3. Traitement par batch
Si beaucoup d'utilisateurs, traiter par batch de 100

### 4. Métriques avancées
- Temps moyen de génération par utilisateur
- Taux de succès sur 30 jours
- Nombre d'entrées générées par jour

---

## ✅ Checklist de Vérification

- [ ] pg_cron est activé (`SELECT * FROM pg_extension WHERE extname = 'pg_cron';`)
- [ ] Le cron job existe (`SELECT * FROM cron.job;`)
- [ ] La fonction `daily_medication_sync()` fonctionne manuellement
- [ ] La table `cron_medication_sync_logs` existe
- [ ] Les logs sont bien créés après exécution
- [ ] Pas d'erreurs dans les logs récents

---

## 🎉 Résultat

**À partir de maintenant :**
- ✅ Chaque jour à minuit UTC, l'historique est automatiquement généré
- ✅ Une entrée par médicament actif, par heure de prise prévue
- ✅ Les logs permettent de suivre les exécutions
- ✅ Pas besoin d'intervention manuelle

**Dans l'app mobile :**
- L'onglet "Historique" se remplit automatiquement chaque jour
- Les utilisateurs voient leur historique complet sans rien faire

---

**Besoin d'aide ?** Consultez les logs ou testez manuellement la fonction.
