# 🌅 Fix : Heure de réveil réelle depuis Oura

## 📋 Résumé du problème

**Problème initial :** La courbe d'énergie commençait à une heure de réveil **estimée** (7h ou 8h UTC) au lieu de l'heure de réveil **réelle** enregistrée par Oura.

**Cause :** Les timestamps `bedtime_start` et `bedtime_end` n'étaient **jamais parsés** lors de l'import des données Oura. Seuls les scores agrégés (sleep_score, readiness_score) étaient stockés.

---

## ✅ Corrections appliquées

### 1️⃣ Backend : Import Oura (`import_oura_data.py` et `import_oura_data_full.py`)

**Modifications :**
- Ajout du parsing de `bedtime_start` (heure de coucher)
- Ajout du parsing de `bedtime_end` (heure de réveil) ✅

**Format stocké :**
- `metric_type: "bedtime_end"`
- `value`: Heure décimale (ex: 10.5 = 10h30)
- `recorded_at`: Timestamp ISO 8601 avec timezone
- `raw_data`: JSON avec le timestamp brut

### 2️⃣ Database : Migration SQL (`032_add_bedtime_to_health_profile.sql`)

**Modifications :**
- Mise à jour de la fonction RPC `get_today_health_profile()`
- Récupération automatique de `bedtime_end` depuis la table `biometrics`
- Fallback intelligent : si pas de donnée aujourd'hui, prend celle d'hier

**Retour de la fonction :**
```json
{
  "readiness_score": 85,
  "hrv_ms": 65,
  "anomalies": [],
  "profile_date": "2026-01-31",
  "bedtime_end": "2026-01-31T10:00:00+00:00"  ← NOUVEAU
}
```

### 3️⃣ Backend : Service énergie (`pulse_energy_decay_service.py`)

**Modifications :**
- Lecture de `bedtime_end` depuis `health_profile`
- Utilisation du timestamp **réel** pour calculer `wake_time`
- Fallback à 10h UTC (11h Paris) si aucune donnée disponible

**Logs améliorés :**
```
✅ Wake time from Oura bedtime_end: 2026-01-31T10:00:00+00:00 (10:00 UTC)
```

### 4️⃣ Script de réimport (`reimport_oura_sleep_times.py`)

**Fonctionnalité :**
- Récupère les données de sommeil Oura des X derniers jours (défaut: 30)
- Parse et stocke `bedtime_start` et `bedtime_end` dans Supabase
- Détecte les doublons et les ignore

---

## 🚀 Déploiement

### Étape 1 : Redémarrer le backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

### Étape 2 : Réimporter les timestamps de sommeil

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Rendre le script exécutable
chmod +x reimport_oura_sleep_times.py

# Exécuter le réimport (remplacer USER_ID par votre UUID)
python reimport_oura_sleep_times.py --user-id c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd --days 30
```

**Sortie attendue :**
```
🔄 RÉIMPORT DES TIMESTAMPS DE SOMMEIL OURA
Found 30 sleep records
📅 Processing sleep record for 2026-01-31
  ✅ Inserted bedtime_end: 2026-01-31T10:00:00+00:00 (hour: 10)
...
✅ RÉIMPORT TERMINÉ
Timestamps inserted: 60
Timestamps skipped: 0
```

### Étape 3 : Tester dans l'app mobile

1. Ouvrir l'app Pulse
2. Aller sur l'onglet **Énergie**
3. Appuyer sur **🔄** (refresh)
4. Vérifier que la courbe commence à **11h** (votre heure de réveil)

**Logs attendus :**
```
[PulseEnergyDecay] ✅ Wake time from Oura bedtime_end: 2026-01-31T10:00:00+00:00
[PulseEnergyDecay] Generating 26 points from 10:00 to 23:59
[EnergyAnalysis] Total points: 26, Wake hour: 10
```

---

## 🔍 Vérification dans Supabase

### Vérifier les données importées

```sql
SELECT 
  metric_type,
  value as hour_decimal,
  recorded_at,
  raw_data->>'bedtime_end' as wake_time
FROM biometrics 
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND metric_type IN ('bedtime_start', 'bedtime_end')
ORDER BY recorded_at DESC
LIMIT 10;
```

**Résultat attendu :**
| metric_type | hour_decimal | recorded_at | wake_time |
|-------------|--------------|-------------|-----------|
| bedtime_end | 10.0 | 2026-01-31 10:00:00+00 | 2026-01-31T10:00:00Z |
| bedtime_start | 23.5 | 2026-01-30 23:30:00+00 | 2026-01-30T23:30:00Z |

### Tester la fonction RPC

```sql
SELECT get_today_health_profile('c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd');
```

**Résultat attendu :**
```json
{
  "readiness_score": 85,
  "bedtime_end": "2026-01-31T10:00:00+00:00",
  "profile_date": "2026-01-31"
}
```

---

## 📊 Avant / Après

### ❌ Avant

- Heure de réveil : **Estimée à 8h UTC** (fixe)
- Courbe d'énergie : Commence à 8h (incorrect)
- Logs : `wake_time=2026-01-31T08:00:00+00:00` (faux)

### ✅ Après

- Heure de réveil : **Lue depuis Oura bedtime_end = 10h UTC** (11h Paris)
- Courbe d'énergie : Commence à 10h UTC (correct !)
- Logs : `✅ Wake time from Oura bedtime_end: 2026-01-31T10:00:00+00:00`

---

## 🔄 Synchronisation automatique

À partir de maintenant, **chaque nouvelle synchronisation Oura** parsera automatiquement `bedtime_start` et `bedtime_end`.

Les nouveaux imports incluront ces données grâce aux modifications dans :
- `import_oura_data.py`
- `import_oura_data_full.py`

---

## 🐛 Troubleshooting

### Problème : La courbe commence toujours à 10h UTC

**Solution :** Exécutez le script de réimport pour récupérer les données historiques :

```bash
python reimport_oura_sleep_times.py --user-id <YOUR_USER_ID> --days 30
```

### Problème : Aucun bedtime_end trouvé dans les logs

**Vérification :**
```sql
-- Vérifier si des données bedtime_end existent
SELECT COUNT(*) 
FROM biometrics 
WHERE user_id = '<YOUR_USER_ID>' 
  AND metric_type = 'bedtime_end';
```

Si le résultat est **0**, cela signifie que :
1. Le script de réimport n'a pas été exécuté
2. Ou les données Oura ne contiennent pas `bedtime_end` (rare)

### Problème : Fuseau horaire incorrect

Le backend utilise **UTC** en interne. Les conversions timezone se font automatiquement :
- **10h UTC** = **11h heure de Paris** (UTC+1)
- Oura envoie toujours les timestamps en UTC avec le suffixe `Z`

---

## 📚 Fichiers modifiés

| Fichier | Type | Description |
|---------|------|-------------|
| `backend/import_oura_data.py` | Backend | Parse bedtime_start/end |
| `backend/import_oura_data_full.py` | Backend | Parse bedtime_start/end (version full) |
| `backend/pulse_energy_decay_service.py` | Backend | Lit bedtime_end depuis health_profile |
| `database/migrations/032_add_bedtime_to_health_profile.sql` | SQL | Migration pour étendre get_today_health_profile |
| `backend/reimport_oura_sleep_times.py` | Script | Réimporte les timestamps historiques |

---

## ✅ Checklist de déploiement

- [x] Migration SQL appliquée (`032_add_bedtime_to_health_profile.sql`)
- [x] Code backend modifié
- [ ] Backend redémarré (`./restart_api_server.sh`)
- [ ] Script de réimport exécuté (`python reimport_oura_sleep_times.py`)
- [ ] App mobile testée (courbe commence à l'heure de réveil réelle)
- [ ] Vérification Supabase (données bedtime_end présentes)

---

## 📞 Support

Si vous rencontrez des problèmes, vérifiez les logs :
- Backend : `tail -f /Users/dannezri/Desktop/Pulse/backend/logs/api.log`
- Mobile : Console Metro dans le terminal

**Logs clés à chercher :**
- `✅ Wake time from Oura bedtime_end` → OK
- `⚠️ No bedtime_end found, using default` → Exécuter le script de réimport
