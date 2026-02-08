# 🔄 Synchroniser les Données Oura Maintenant

**Problème**: Les données sont dans l'app Oura mais pas encore dans Pulse  
**Solution**: Forcer une synchronisation manuelle via l'API Oura

---

## 🚀 Procédure (2 minutes)

### Étape 1: Forcer la Synchronisation Oura

Ouvre un terminal et exécute :

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 force_sync_oura_today.py
```

**Ce script va** :
- ✅ Se connecter à l'API Oura avec ton token
- ✅ Récupérer les données des **7 derniers jours**
- ✅ Les insérer dans Supabase (table `biometrics`)
- ✅ Afficher des statistiques détaillées

**Durée** : 30-60 secondes

---

### Étape 2: Vérifier que les Données Sont Arrivées

```bash
python3 inspect_biometrics.py
```

Tu devrais maintenant voir :
```
📋 Liste des metric_type:
   - hr                             : 1000 entrée(s)
   - hrv                            : X entrée(s)  ✅ NOUVEAU
   - sleep_score                    : X entrée(s)  ✅ NOUVEAU
   - readiness_score                : X entrée(s)  ✅ NOUVEAU
   - activity_score                 : X entrée(s)  ✅ NOUVEAU
   - steps                          : X entrée(s)  ✅ NOUVEAU
```

---

### Étape 3: Redémarrer le Backend

```bash
cd /Users/dannezri/Desktop/Pulse
./restart_api_server.sh
```

---

### Étape 4: Tester dans l'App

1. Ouvre l'app Pulse sur ton iPhone
2. Va sur la page **Énergie**
3. Fais un **pull-to-refresh** (tire vers le bas)
4. Vérifie que Gemini mentionne maintenant :
   - ✅ HRV
   - ✅ Sleep Score
   - ✅ Readiness Score
   - ✅ Activity Score

---

## 📊 Ce Qui Va Être Importé

Le script `force_sync_oura_today.py` va récupérer depuis l'API Oura :

### Données de Sommeil
- `sleep_score` (score global)
- `sleep_deep_score` (sommeil profond)
- `sleep_efficiency_score` (efficacité)
- `sleep_latency_score` (temps d'endormissement)
- `sleep_rem_score` (sommeil paradoxal)
- `sleep_restfulness_score` (qualité du repos)
- `sleep_timing_score` (timing du sommeil)
- `bedtime_start`, `bedtime_end` (heures de coucher/réveil)

### Données d'Activité
- `activity_score` (score global)
- `steps` (pas)
- `active_calories` (calories actives)
- `total_calories` (calories totales)
- `high_activity_time_seconds` (temps activité intense)
- `medium_activity_time_seconds` (temps activité moyenne)
- `low_activity_time_seconds` (temps activité légère)
- `sedentary_time_seconds` (temps sédentaire)

### Données de Préparation (Readiness)
- `readiness_score` (score global)
- `readiness_activity_balance_score` (équilibre activité)
- `readiness_body_temp_score` (température corporelle)
- `readiness_hrv_balance_score` (équilibre HRV)
- `readiness_resting_hr_score` (fréquence cardiaque au repos)

### Données Cardiaques
- `hr` (fréquence cardiaque minute par minute)
- `hrv` (variabilité de fréquence cardiaque)

### Autres
- `spo2` (saturation en oxygène)

---

## 🎯 Résultat Attendu

**Avant la sync** (confidence = 27%) :
- ❌ HRV : Manquant
- ❌ Sleep Score : Manquant
- ✅ RHR : 92 bpm
- ✅ États latents : OK

**Après la sync** (confidence attendue: 70-85%) :
- ✅ HRV : Récupéré
- ✅ Sleep Score : Récupéré
- ✅ Readiness Score : Récupéré
- ✅ Activity Score : Récupéré
- ✅ Steps : Récupéré
- ✅ RHR : 92 bpm
- ✅ États latents : OK

---

## ⚠️ En Cas de Problème

### Erreur "Invalid token"
→ Vérifie que ton token Oura est valide dans le script

### Erreur "SUPABASE_URL not set"
→ Assure-toi que le fichier `.env` existe dans `backend/`

### Aucune donnée importée
→ Vérifie dans l'app Oura que les données sont bien présentes pour les 7 derniers jours

---

## 💡 Automatisation Future

Une fois que ça fonctionne, le backend va synchroniser automatiquement les données Oura :
- ✅ Toutes les 6 heures via le cron job `cron_oura_daily_sync.py`
- ✅ Au démarrage du serveur

Tu n'auras plus besoin de forcer la sync manuellement.

---

**Prochaine action** : Lance `python3 force_sync_oura_today.py` maintenant ! 🚀
