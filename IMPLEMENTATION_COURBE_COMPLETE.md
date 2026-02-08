# Implémentation Courbe Énergétique depuis le Réveil ✅

## Date
2026-02-01

## Contexte
L'utilisateur voyait la courbe d'énergie commencer à **21h** au lieu du réveil, ce qui empêchait de visualiser le déclin énergétique sur toute la journée.

## Problèmes Identifiés

### 1. Ancien Code partait de "Maintenant" (UTC)
```python
# Ancien code
now = datetime.now(timezone.utc)
current_time = now  # Commençait à l'heure actuelle
```

**Résultat** : Si appelé à 20h58 UTC, la courbe commençait à 20h30 UTC (arrondi), soit **21h30 heure locale Paris**.

### 2. Pas de Gestion du Timezone Utilisateur
- Le code utilisait UTC partout
- Affichait 7h UTC au lieu de 7h local
- Confusion entre heure serveur et heure utilisateur

### 3. Métadonnées de Sommeil Vides
```sql
SELECT metadata FROM biometrics WHERE metric_type = 'sleep_duration'
-- Résultat: metadata = null
```
- Impossible d'extraire `bedtime_end` depuis Oura
- Fallback sur valeur par défaut nécessaire

## Solution Implémentée

### 1. Utilisation du Timezone Europe/Paris
```python
from zoneinfo import ZoneInfo

user_tz = ZoneInfo("Europe/Paris")
now = datetime.now(user_tz)
target_datetime = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=user_tz)
```

### 2. Heure de Réveil par Défaut (7h LOCAL)
```python
wake_time_hour = 7  # 7h du matin heure locale (Paris)
wake_time = target_datetime.replace(hour=wake_time_hour, minute=0, second=0, microsecond=0)
```

### 3. Conversion des Événements en Timezone Local
```python
event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00')).astimezone(user_tz)
event_end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00')).astimezone(user_tz)
```

### 4. Génération de la Courbe depuis le Réveil
```python
current_time = wake_time  # Commence à 7h local
while current_time <= end_of_day:  # Jusqu'à 23:59 local
    # ... calcul de l'énergie ...
    points.append({'t': current_time.isoformat(), 'energy': energy})
    current_time += timedelta(minutes=INTERVAL_MINUTES)
```

## Fichiers Modifiés

### `backend/intraday_energy_service.py`
- **Fonction** : `generate_intraday_curve()`
- **Lignes** : 176-266
- **Changements** :
  - Import de `zoneinfo.ZoneInfo`
  - Utilisation de `Europe/Paris` comme timezone
  - Début de courbe à `wake_time` (7h local) au lieu de `now`
  - Conversion des événements en heure locale

## Résultat Attendu

### Avant
```json
{
  "points": [
    {"t": "2026-02-01T20:30:00+00:00", "energy": 38},  // 21h30 Paris
    {"t": "2026-02-01T21:00:00+00:00", "energy": 36},
    ...
  ]
}
```

### Après
```json
{
  "points": [
    {"t": "2026-02-01T07:00:00+01:00", "energy": 52},  // 7h00 Paris (réveil)
    {"t": "2026-02-01T07:30:00+01:00", "energy": 51},
    {"t": "2026-02-01T08:00:00+01:00", "energy": 50},
    ...
    {"t": "2026-02-01T21:00:00+01:00", "energy": 35, "is_now": true},  // Maintenant
    {"t": "2026-02-01T21:30:00+01:00", "energy": 33},
    ...
  ]
}
```

## Bénéfices Utilisateur

### 1. Visualisation Complète du Déclin
- **Avant** : "Je ne vois que la fin de ma journée"
- **Après** : "Je vois toute ma pente énergétique depuis 7h"

### 2. Compréhension de l'Impact
> "Si je vois que j'ai perdu 40% en 4h, je comprends l'urgence de ralentir"

### 3. Contexte Temporel Clair
- Point "Maintenant" marqué avec `is_now: true`
- Courbe commence au réveil (7h local)
- Affichage en heure locale utilisateur

## Prochaines Améliorations

### 1. Extraction Réelle de l'Heure de Réveil
```python
# Actuellement: metadata = null dans biometrics
# TODO: Enrichir les métadonnées Oura pour inclure bedtime_end
```

### 2. Timezone Dynamique par Utilisateur
```sql
-- Ajouter colonne timezone au profile
ALTER TABLE profiles ADD COLUMN timezone TEXT DEFAULT 'Europe/Paris';
```

### 3. Persistance de l'Heure de Réveil
```python
# Stocker l'heure de réveil calculée pour éviter recalcul
# Utiliser comme fallback si metadata manquant
```

## Validation

### 1. Cache Supprimé
```sql
DELETE FROM intraday_energy_forecast 
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd' 
  AND forecast_date = '2026-02-01'
```

### 2. Backend Redémarré
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test Mobile
- Rafraîchir la page Énergie (pull-to-refresh)
- Vérifier que la courbe commence à 7h local
- Vérifier le marqueur "Maintenant"

## Notes Techniques

### Python zoneinfo
```python
from zoneinfo import ZoneInfo
# Disponible Python 3.9+
# Utilise la base de données IANA timezone
```

### Conversion UTC → Local
```python
utc_dt = datetime.fromisoformat("2026-02-01T06:00:00+00:00")  # 6h UTC
paris_dt = utc_dt.astimezone(ZoneInfo("Europe/Paris"))        # 7h Paris (hiver: UTC+1)
```

### Heure Locale → UTC
```python
paris_dt = datetime(2026, 2, 1, 7, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))  # 7h Paris
utc_dt = paris_dt.astimezone(timezone.utc)                                  # 6h UTC
```

## Statut
✅ **IMPLÉMENTÉ** - En attente de test utilisateur après redémarrage backend

---

**Auteur** : Assistant AI  
**Review** : En attente  
**Tags** : #energy #intraday #timezone #UX
