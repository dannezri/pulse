# Intégration Oura Ring

Ce document explique comment intégrer les données Oura Ring dans Pulse.

## 📋 Vue d'ensemble

L'intégration Oura permet de récupérer automatiquement :
- **Données de sommeil** : score, durée, efficacité, sommeil profond, REM, FC au repos, HRV
- **Données d'activité** : score, pas, calories actives/totales, distance de marche, temps sédentaire
- **Données de préparation (Readiness)** : score, température corporelle, indice de récupération
- **Données vitales** : SpO2, fréquence cardiaque
- **Entraînements** : durée, calories, intensité

## 🚀 Configuration initiale

### 1. Obtenir un token d'accès Oura

1. Connectez-vous à [Oura Cloud](https://cloud.ouraring.com/)
2. Allez dans **Personal Access Tokens**
3. Créez un nouveau token avec les scopes nécessaires
4. Copiez le token (format: `IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI`)

### 2. Configuration de l'environnement

Ajoutez le token Oura dans votre fichier `.env` :

```bash
# Oura Configuration (optionnel - peut être passé en paramètre)
OURA_ACCESS_TOKEN=your_oura_token_here
```

## 📊 Structure des données

### Table `external_identities`

L'utilisateur Oura est enregistré dans `external_identities` :

```json
{
  "supabase_user_id": "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd",
  "provider_system": "oura",
  "external_user_id": "user@example.com",
  "metadata": {
    "email": "user@example.com",
    "age": 30,
    "weight": 70.5,
    "height": 175.0,
    "biological_sex": "male"
  },
  "is_active": true
}
```

### Table `biometrics`

Les données Oura sont stockées avec `source = 'oura'` et des `metric_type` spécifiques :

| Metric Type | Description | Unité |
|------------|-------------|-------|
| `sleep_score` | Score de sommeil Oura | 0-100 |
| `sleep_duration` | Durée totale de sommeil | heures |
| `sleep_efficiency` | Efficacité du sommeil | % |
| `deep_sleep_minutes` | Sommeil profond | minutes |
| `rem_sleep_minutes` | Sommeil paradoxal | minutes |
| `resting_hr` | Fréquence cardiaque au repos | bpm |
| `hrv` | Variabilité de la fréquence cardiaque | ms |
| `activity_score` | Score d'activité Oura | 0-100 |
| `steps` | Nombre de pas | pas |
| `active_calories` | Calories actives | kcal |
| `total_calories` | Calories totales | kcal |
| `walking_distance_km` | Distance de marche | km |
| `sedentary_hours` | Heures sédentaires | heures |
| `readiness_score` | Score de préparation | 0-100 |
| `body_temperature_deviation` | Déviation de température | °C |
| `recovery_index` | Indice de récupération | 0-100 |
| `spo2` | Saturation en oxygène | % |
| `hr` | Fréquence cardiaque | bpm |
| `workout_duration_minutes` | Durée d'entraînement | minutes |
| `workout_calories` | Calories brûlées | kcal |
| `workout_intensity` | Intensité (1=easy, 3=moderate, 5=hard) | 1-5 |

## 🔧 Scripts disponibles

### 1. Enregistrer un utilisateur Oura

Enregistre l'utilisateur dans `external_identities` :

```bash
cd backend
./run_register_oura.sh
```

Ou manuellement :

```bash
python3 register_oura_user.py
```

**Configuration** : Modifiez les constantes dans `register_oura_user.py` :
```python
OURA_TOKEN = "your_token_here"
USER_UUID = "your_supabase_user_uuid"
```

### 2. Importer les données Oura

Récupère toutes les données disponibles et les insère dans Supabase :

```bash
cd backend
./run_oura_import.sh
```

Ou manuellement :

```bash
python3 import_oura_data.py
```

**Configuration** : Modifiez les constantes dans `import_oura_data.py` :
```python
OURA_TOKEN = "your_token_here"
USER_UUID = "your_supabase_user_uuid"
```

Par défaut, le script récupère **90 jours** de données. Pour modifier :

```python
importer.import_all_data(
    user_id=USER_UUID,
    days_back=30  # Récupérer seulement 30 jours
)
```

## 📝 Utilisation programmatique

### Client Oura

```python
from oura_client import get_oura_client

# Initialiser le client
oura = get_oura_client("YOUR_TOKEN")

# Récupérer les données de sommeil
sleep_data = oura.get_daily_sleep("2026-01-01", "2026-01-28")

# Récupérer les données d'activité
activity_data = oura.get_daily_activity("2026-01-01", "2026-01-28")

# Récupérer toutes les données
all_data = oura.get_all_data("2026-01-01", "2026-01-28")
```

### Importeur de données

```python
from import_oura_data import OuraDataImporter
from supabase_client import SupabaseClient

# Initialiser l'importeur
importer = OuraDataImporter(
    oura_token="YOUR_TOKEN",
    supabase_url="YOUR_SUPABASE_URL",
    supabase_key="YOUR_SUPABASE_KEY"
)

# Importer les données
importer.import_all_data(
    user_id="c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd",
    start_date="2026-01-01",
    end_date="2026-01-28"
)

# Afficher les stats
importer._print_stats()
```

## 🔄 Idempotence

Les imports sont **idempotents** grâce à `source_event_id` unique :
- Format : `oura_{metric}_{record_id}`
- Exemple : `oura_sleep_score_0981cb8b-f0ef-4ac8-9742-a813df8a7572`

Si vous exécutez le script plusieurs fois, les doublons seront automatiquement détectés et ignorés.

## 🎯 Cas d'usage

### Import initial complet

```bash
# Enregistrer l'utilisateur
./run_register_oura.sh

# Importer 90 jours de données
./run_oura_import.sh
```

### Mise à jour quotidienne (cron)

Créez un cron job pour importer les nouvelles données chaque jour :

```bash
0 2 * * * cd /path/to/backend && ./run_oura_import.sh
```

Le script récupère automatiquement les derniers jours et ignore les doublons.

### Import personnalisé

Modifiez `import_oura_data.py` pour personnaliser :

```python
# Import d'une période spécifique
importer.import_all_data(
    user_id=USER_UUID,
    start_date="2025-12-01",
    end_date="2026-01-28"
)

# Import seulement du sommeil
sleep_data = oura_client.get_daily_sleep("2026-01-01", "2026-01-28")
importer.normalize_sleep_data(sleep_data, USER_UUID)
```

## ⚠️ Limitations de l'API Oura

1. **Heart Rate (fréquence cardiaque)** : Limitée à **1 jour maximum** par requête
2. **Rate limiting** : L'API Oura a des limites de taux (consultez la doc officielle)
3. **Données historiques** : Certaines données ne sont pas disponibles avant une certaine date

## 🐛 Dépannage

### Erreur "400 Bad Request" sur heart rate

C'est normal si la période est > 1 jour. Le client gère automatiquement cette limitation en récupérant seulement le dernier jour.

### Erreur "SUPABASE_URL not set"

Assurez-vous que votre fichier `.env` contient :

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

### Pas de données récupérées

Vérifiez que :
1. Le token Oura est valide
2. L'utilisateur a des données dans la période demandée
3. Les scopes du token incluent les permissions nécessaires

### Doublons dans la base

Si `source_event_id` est correctement défini, les doublons sont impossibles grâce à la contrainte unique dans PostgreSQL.

## 📚 Références

- [Oura API Documentation](https://cloud.ouraring.com/v2/docs)
- [Oura Cloud](https://cloud.ouraring.com/)
- [Schema Pulse](./database/schema.sql)
- [Supabase Client](./supabase_client.py)

## 🎉 Exemple de résultat

```
INFO:__main__:============================================================
INFO:__main__:IMPORT STATISTICS
INFO:__main__:============================================================
INFO:__main__:Total metrics inserted: 11
INFO:__main__:Total duplicates skipped: 0
INFO:__main__:Total errors: 0
INFO:__main__:
INFO:__main__:By metric type:
INFO:__main__:  sleep_score: Inserted: 1, Duplicates: 0
INFO:__main__:  activity_score: Inserted: 1, Duplicates: 0
INFO:__main__:  steps: Inserted: 1, Duplicates: 0
INFO:__main__:  readiness_score: Inserted: 1, Duplicates: 0
INFO:__main__:  spo2: Inserted: 1, Duplicates: 0
INFO:__main__:============================================================
```
