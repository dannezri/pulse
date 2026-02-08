# 🔬 Données Brutes Oura - Guide Complet

## Vue d'ensemble

L'API Oura fournit **deux niveaux de données** :
1. **Scores calculés** (ex: sleep_score = 72)
2. **Données brutes et contributeurs** (ex: deep_sleep_score = 54, efficiency = 76, etc.)

Ce guide documente **toutes les données brutes disponibles**.

---

## 📊 Types de Données Disponibles

### 1. 🏃 Activity - Données Granulaires

#### Séries temporelles MET (Minute par Minute)

| Métrique | Type | Description |
|----------|------|-------------|
| `met_timeseries_avg` | float | Moyenne des valeurs MET sur 24h |
| `raw_data.met_items[]` | array | **1440 valeurs** (1 par minute pendant 24h) |
| `raw_data.interval` | float | Intervalle en secondes (60.0 = 1 min) |

**Exemple d'utilisation :**
```sql
SELECT 
    recorded_at,
    value as avg_met,
    raw_data->'met_items' as minute_by_minute_met
FROM biometrics
WHERE metric_type = 'met_timeseries_avg'
  AND user_id = 'your-user-id';
```

#### Classification d'activité (5 minutes)

| Métrique | Type | Description |
|----------|------|-------------|
| `activity_class_5min` | string | **288 caractères** (24h ÷ 5min = 288 périodes) |

**Classes :**
- `0` = Non-wear (bague non portée)
- `1` = Rest (repos)
- `2` = Inactive (inactif)
- `3` = Low activity (activité légère)
- `4` = Medium activity (activité modérée)
- `5` = High activity (activité intense)

**Exemple :**
```
"111111111111...222...333...444...555"
```
= 1h de repos, puis inactif, puis activité légère, modérée, intense

#### Temps d'activité par niveau

| Métrique | Unité | Description |
|----------|-------|-------------|
| `high_activity_time_seconds` | secondes | Temps en activité intense |
| `high_activity_met_minutes` | MET-min | MET cumulés activité intense |
| `medium_activity_time_seconds` | secondes | Temps en activité modérée |
| `medium_activity_met_minutes` | MET-min | MET cumulés activité modérée |
| `low_activity_time_seconds` | secondes | Temps en activité légère |
| `low_activity_met_minutes` | MET-min | MET cumulés activité légère |
| `sedentary_time_seconds` | secondes | Temps sédentaire |
| `resting_time_seconds` | secondes | Temps de repos |
| `non_wear_time_seconds` | secondes | Temps sans porter la bague |
| `average_met_minutes` | MET-min | MET moyen |

#### Contributeurs de score d'activité

| Métrique | Unité | Description |
|----------|-------|-------------|
| `activity_daily_targets_score` | 0-100 | Atteinte objectifs quotidiens |
| `activity_move_hourly_score` | 0-100 | Bouger chaque heure |
| `activity_recovery_time_score` | 0-100 | Temps de récupération |
| `activity_stay_active_score` | 0-100 | Rester actif |
| `activity_training_freq_score` | 0-100 | Fréquence d'entraînement |
| `activity_training_vol_score` | 0-100 | Volume d'entraînement |

**Formule :**
```
activity_score = moyenne pondérée des 6 contributeurs
```

---

### 2. 😴 Sleep - Contributeurs Détaillés

#### Contributeurs de score de sommeil

| Métrique | Unité | Description |
|----------|-------|-------------|
| `sleep_deep_score` | 0-100 | Qualité du sommeil profond |
| `sleep_efficiency_score` | 0-100 | Efficacité du sommeil (temps dormeur / temps au lit) |
| `sleep_latency_score` | 0-100 | Temps pour s'endormir |
| `sleep_rem_score` | 0-100 | Qualité du sommeil REM |
| `sleep_restfulness_score` | 0-100 | Tranquillité du sommeil |
| `sleep_timing_score` | 0-100 | Timing circadien (alignement avec horloge biologique) |
| `sleep_total_score` | 0-100 | Durée totale de sommeil |

**Formule :**
```
sleep_score = moyenne pondérée des 7 contributeurs
```

**Interprétation :**
- **sleep_timing_score faible** → Dormez à des heures irrégulières
- **sleep_latency_score faible** → Vous mettez trop de temps à vous endormir
- **sleep_efficiency_score faible** → Vous vous réveillez souvent la nuit

---

### 3. ⚡ Readiness - Contributeurs Détaillés

#### Contributeurs de score de préparation

| Métrique | Unité | Description |
|----------|-------|-------------|
| `readiness_activity_balance_score` | 0-100 | Équilibre entre activité et repos |
| `readiness_body_temp_score` | 0-100 | Température corporelle (déviation) |
| `readiness_hrv_balance_score` | 0-100 | Variabilité cardiaque |
| `readiness_prev_day_activity_score` | 0-100 | Impact activité jour précédent |
| `readiness_prev_night_score` | 0-100 | Impact sommeil nuit précédente |
| `readiness_recovery_index_score` | 0-100 | Indice de récupération |
| `readiness_resting_hr_score` | 0-100 | Fréquence cardiaque au repos |
| `readiness_sleep_balance_score` | 0-100 | Équilibre sommeil sur plusieurs jours |

**Formule :**
```
readiness_score = moyenne pondérée des 8 contributeurs
```

---

## 🔍 Requêtes SQL Utiles

### Analyser l'activité minute par minute

```sql
-- Extraire les valeurs MET minute par minute
SELECT 
    recorded_at::date as day,
    jsonb_array_elements_text(raw_data->'met_items')::float as met_value,
    generate_series(0, 1439) as minute_of_day
FROM biometrics
WHERE metric_type = 'met_timeseries_avg'
  AND user_id = 'your-user-id'
ORDER BY day, minute_of_day;
```

### Analyser la classification d'activité 5-min

```sql
-- Extraire la classification toutes les 5 minutes
WITH activity_class AS (
    SELECT 
        recorded_at::date as day,
        raw_data->>'class_5_min' as class_string
    FROM biometrics
    WHERE metric_type = 'activity_class_5min'
      AND user_id = 'your-user-id'
)
SELECT 
    day,
    substring(class_string from pos for 1)::int as activity_level,
    (pos - 1) * 5 as minute_of_day,
    CASE substring(class_string from pos for 1)
        WHEN '0' THEN 'non-wear'
        WHEN '1' THEN 'rest'
        WHEN '2' THEN 'inactive'
        WHEN '3' THEN 'low'
        WHEN '4' THEN 'medium'
        WHEN '5' THEN 'high'
    END as activity_label
FROM activity_class,
     generate_series(1, 288) as pos
ORDER BY day, pos;
```

### Comparer tous les contributeurs de sommeil

```sql
-- Vue complète des contributeurs de sommeil
SELECT 
    recorded_at::date as night,
    MAX(CASE WHEN metric_type = 'sleep_score' THEN value END) as overall_score,
    MAX(CASE WHEN metric_type = 'sleep_deep_score' THEN value END) as deep_sleep,
    MAX(CASE WHEN metric_type = 'sleep_efficiency_score' THEN value END) as efficiency,
    MAX(CASE WHEN metric_type = 'sleep_latency_score' THEN value END) as latency,
    MAX(CASE WHEN metric_type = 'sleep_rem_score' THEN value END) as rem_sleep,
    MAX(CASE WHEN metric_type = 'sleep_restfulness_score' THEN value END) as restfulness,
    MAX(CASE WHEN metric_type = 'sleep_timing_score' THEN value END) as timing,
    MAX(CASE WHEN metric_type = 'sleep_total_score' THEN value END) as total_sleep
FROM biometrics
WHERE user_id = 'your-user-id'
  AND metric_type LIKE 'sleep_%'
  AND source = 'oura'
GROUP BY recorded_at::date
ORDER BY night DESC;
```

### Identifier les patterns d'activité

```sql
-- Temps passé à chaque niveau d'activité
SELECT 
    recorded_at::date as day,
    MAX(CASE WHEN metric_type = 'high_activity_time_seconds' THEN value/3600 END) as high_hours,
    MAX(CASE WHEN metric_type = 'medium_activity_time_seconds' THEN value/3600 END) as medium_hours,
    MAX(CASE WHEN metric_type = 'low_activity_time_seconds' THEN value/3600 END) as low_hours,
    MAX(CASE WHEN metric_type = 'sedentary_time_seconds' THEN value/3600 END) as sedentary_hours,
    MAX(CASE WHEN metric_type = 'resting_time_seconds' THEN value/3600 END) as resting_hours,
    MAX(CASE WHEN metric_type = 'non_wear_time_seconds' THEN value/3600 END) as non_wear_hours
FROM biometrics
WHERE user_id = 'your-user-id'
  AND metric_type LIKE '%_time_seconds'
  AND source = 'oura'
GROUP BY day
ORDER BY day DESC;
```

---

## 🎯 Cas d'usage

### 1. Machine Learning / IA

**Prédire la qualité du sommeil** :
- Features : MET minute par minute, classification 5-min, contributeurs readiness
- Target : sleep_score

### 2. Visualisations

**Heatmap d'activité 24h** :
- X = heure de la journée
- Y = jour
- Couleur = niveau d'activité (class_5_min)

**Graphique MET en temps réel** :
- Afficher les 1440 valeurs MET sur 24h
- Identifier les pics d'activité

### 3. Insights personnalisés

**Corrélations** :
- `sleep_timing_score` faible → Recommander routine sommeil régulière
- `activity_move_hourly_score` faible → Rappels pour bouger chaque heure
- `readiness_hrv_balance_score` faible → Suggérer jour de récupération

---

## 📚 Scripts disponibles

### Import complet (données brutes)

```bash
./run_oura_import_full.sh
```

**Importe** :
- ✅ Scores calculés (sleep_score, activity_score, etc.)
- ✅ Contributeurs détaillés (tous les sous-scores)
- ✅ Séries temporelles (MET minute par minute, classification 5-min)
- ✅ Temps d'activité granulaires

### Import basique (scores uniquement)

```bash
./run_oura_import.sh
```

**Importe seulement** :
- ✅ Scores calculés
- ❌ Contributeurs détaillés
- ❌ Séries temporelles

---

## 🎉 Résumé

Avec l'import COMPLET, vous avez maintenant accès à :

1. **📈 1440 valeurs MET par jour** (1 par minute)
2. **🏃 288 classifications d'activité par jour** (toutes les 5 min)
3. **💤 7 contributeurs de sommeil** (au lieu d'un seul score)
4. **🏋️ 6 contributeurs d'activité** (au lieu d'un seul score)
5. **⚡ 8 contributeurs de readiness** (au lieu d'un seul score)

**Total : 158 métriques** contre 12 dans la version basique !

---

## 🔗 Références

- [Oura API Documentation](https://cloud.ouraring.com/v2/docs)
- `import_oura_data_full.py` - Script d'import complet
- `import_oura_data.py` - Script d'import basique
