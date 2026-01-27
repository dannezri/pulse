# Stratégie de Normalisation : Open Wearables vs Pulse

## 📋 Principe Fondamental

**Séparation claire des responsabilités** pour éviter les doublons et centraliser la logique "santé" :

- **Open Wearables** : Unifie les **structures de données** (formats providers → format commun)
- **Pulse** : Transforme en **métriques santé** (unités, agrégats, baselines, anomalies, contexte)

**Règle d'or** : La logique "santé" (baselines, anomalies, contexte) vit **uniquement** dans Pulse.

## 🔄 Flux de Normalisation

```
┌─────────────────────────────────────────────────────────────┐
│                    PROVIDERS                                 │
│  Apple Health │ Garmin │ Polar │ Suunto │ Oura │ ...       │
│  (Formats différents : JSON, XML, API spécifiques)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OPEN WEARABLES                                │
│  Rôle : Unification des structures                         │
│                                                             │
│  ✅ Normalise les structures JSON                          │
│  ✅ Unifie les timestamps (ISO 8601)                      │
│  ✅ Mappe les champs (ex: "heart_rate" vs "hr")           │
│  ✅ Format commun : {"hr": [...], "sleep": {...}}         │
│                                                             │
│  ❌ NE FAIT PAS :                                          │
│     - Calcul de baselines                                  │
│     - Détection d'anomalies                                │
│     - Agrégation par jour                                  │
│     - Contexte santé                                       │
│     - Conversion d'unités (déjà cohérentes)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ Format unifié Open Wearables
                       │
┌─────────────────────────────────────────────────────────────┐
│              PULSE (DataNormalizer)                         │
│  Rôle : Transformation en métriques santé                  │
│                                                             │
│  ✅ Convertit en unités standard (bpm, ms, minutes)        │
│  ✅ Agrège les données (moyennes, min, max, resting)       │
│  ✅ Calcule les baselines (7j → 14j → 30j avec fallback)   │
│  ✅ Détecte les anomalies (HRV drop, sleep deficit)        │
│  ✅ Construit le contexte (heure, jour, tendances)         │
│  ✅ Gère la qualité des données (low/medium/high)          │
│  ✅ Crée le profil santé JSON pour l'IA                    │
│                                                             │
│  ❌ NE FAIT PAS :                                          │
│     - Parsing des formats providers                        │
│     - Mapping des champs providers                         │
│     - Gestion des timestamps providers                     │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Exemple Concret

### Étape 1 : Open Wearables (Unification Structure)

**Input** : Format Garmin
```json
{
  "heartRate": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
  "sleepDuration": 28800,
  "sleepStart": "2024-01-15T22:00:00Z"
}
```

**Output** : Format unifié Open Wearables
```json
{
  "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
  "sleep": {
    "duration_seconds": 28800,
    "start_time": "2024-01-15T22:00:00Z"
  }
}
```

**Ce que fait Open Wearables** :
- ✅ Mappe `heartRate` → `hr`
- ✅ Structure `sleep` en objet avec `duration_seconds`
- ✅ Normalise les timestamps en ISO 8601
- ✅ Format JSON cohérent

### Étape 2 : Pulse (Transformation Santé)

**Input** : Format unifié Open Wearables (ci-dessus)

**Output** : Profil de santé JSON
```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {
    "heart_rate": {
      "average_bpm": 72,
      "resting_bpm": 58,
      "max_bpm": 145,
      "min_bpm": 58
    },
    "sleep": {
      "duration_minutes": 480,
      "quality_score": 85,
      "deep_sleep_minutes": 120,
      "rem_sleep_minutes": 90
    }
  },
  "baselines": {
    "hrv_baseline": 68,
    "hr_baseline": 60,
    "sleep_baseline": 450,
    "hrv_baseline_metadata": {
      "actual_days": 7,
      "data_points": 6,
      "data_quality": "high",
      "fallback_used": false
    }
  },
  "anomalies": [
    {
      "type": "hrv_drop",
      "severity": "medium",
      "confidence": "high",
      "current": 62,
      "baseline": 68,
      "drop_percentage": 8.82
    }
  ],
  "context": {
    "current_time": "14:30",
    "day_of_week": "Monday",
    "time_of_day": "afternoon",
    "trends": {
      "hrv": "declining",
      "sleep": "stable"
    }
  },
  "data_quality": "high"
}
```

**Ce que fait Pulse** :
- ✅ Convertit `duration_seconds` → `duration_minutes`
- ✅ Agrège HR : moyenne, min, max, resting
- ✅ Calcule baselines avec fallback
- ✅ Détecte anomalies avec confiance
- ✅ Construit contexte (heure, jour, tendances)
- ✅ Évalue qualité des données

## 🎯 Responsabilités Détaillées

### Open Wearables : Unification Structure

#### ✅ Fait

1. **Parsing des formats providers**
   - Garmin API → JSON
   - Apple Health XML → JSON
   - Polar API → JSON
   - Suunto API → JSON

2. **Unification des structures**
   - `heartRate` (Garmin) → `hr` (format commun)
   - `heart_rate` (Apple) → `hr` (format commun)
   - `sleepDuration` (Garmin) → `sleep.duration_seconds` (format commun)

3. **Normalisation des timestamps**
   - Tous les timestamps en ISO 8601
   - Timezone UTC

4. **Format commun cohérent**
   ```json
   {
     "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
     "hrv": [{"value": 65, "timestamp": "2024-01-15T10:00:00Z"}],
     "sleep": {
       "duration_seconds": 28800,
       "start_time": "2024-01-15T22:00:00Z"
     },
     "steps": [{"value": 8500, "timestamp": "2024-01-15T10:00:00Z"}]
   }
   ```

#### ❌ Ne Fait Pas

- Calcul de baselines
- Détection d'anomalies
- Agrégation par jour (moyennes, min, max)
- Contexte santé (heure, jour, tendances)
- Conversion d'unités (reçoit déjà des unités cohérentes)

### Pulse : Transformation Santé

#### ✅ Fait

1. **Conversion d'unités** (si nécessaire)
   - `duration_seconds` → `duration_minutes`
   - Vérification que HR est en bpm
   - Vérification que HRV est en ms

2. **Agrégation des données**
   - HR : moyenne, min, max, resting
   - HRV : moyenne, min, max, latest
   - Sleep : durée, qualité, phases
   - Activity : pas, distance, calories

3. **Calcul des baselines**
   - Moyenne glissante sur 7 jours (cible)
   - Fallback automatique : 7j → 14j → 30j
   - Gestion des trous de données
   - Métadonnées de qualité

4. **Détection d'anomalies**
   - HRV drop (>20%)
   - Sleep deficit (>1h)
   - Elevated resting HR (>10 bpm)
   - Niveau de confiance (high/low)

5. **Construction du contexte**
   - Heure actuelle
   - Jour de la semaine
   - Période de la journée
   - Tendances (improving/declining/stable)

6. **Évaluation de la qualité**
   - Disponibilité des métriques
   - Qualité des baselines
   - Qualité globale (low/medium/high)

7. **Création du profil santé**
   - Format JSON standardisé
   - Prêt pour l'IA
   - Versioning inclus

#### ❌ Ne Fait Pas

- Parsing des formats providers (Garmin, Apple, etc.)
- Mapping des champs providers
- Gestion des timestamps providers
- OAuth flows
- Synchronisation avec providers

## 🔍 Vérification : Pas de Doublon

### Ce qui pourrait être un doublon (mais ne l'est pas)

| Aspect | Open Wearables | Pulse | Doublon ? |
|--------|----------------|-------|-----------|
| **Structures JSON** | Unifie formats providers | Reçoit format unifié | ❌ Non |
| **Timestamps** | Normalise en ISO 8601 | Utilise timestamps normalisés | ❌ Non |
| **Champs** | Mappe "heartRate" → "hr" | Utilise "hr" directement | ❌ Non |
| **Unités** | Reçoit unités cohérentes | Convertit si nécessaire (ex: seconds → minutes) | ❌ Non (conversion, pas normalisation) |
| **Agrégation** | Ne fait pas | Fait (moyennes, min, max) | ❌ Non |
| **Baselines** | Ne fait pas | Fait (logique santé) | ❌ Non |
| **Anomalies** | Ne fait pas | Fait (logique santé) | ❌ Non |

### Exemple de Doublon Évité

**Si Open Wearables calculait les baselines** :
- ❌ Doublon : Logique santé dans deux endroits
- ❌ Problème : Difficile de maintenir la cohérence
- ❌ Problème : Impossible d'ajouter d'autres sources (Apple Health direct)

**Avec la séparation actuelle** :
- ✅ Pas de doublon : Logique santé uniquement dans Pulse
- ✅ Cohérence : Un seul endroit pour les baselines
- ✅ Extensibilité : Peut ajouter Apple Health direct sans modifier Open Wearables

## 🚀 Avantages de cette Séparation

### 1. Maintenabilité

- **Un seul endroit** pour la logique santé
- Modifications de baselines/anomalies → Un seul fichier
- Pas de risque de désynchronisation

### 2. Extensibilité

- Ajouter un nouveau provider → Open Wearables uniquement
- Ajouter une nouvelle métrique santé → Pulse uniquement
- Ajouter Apple Health direct → Pulse peut traiter directement

### 3. Testabilité

- Open Wearables : Tests d'unification structure
- Pulse : Tests de logique santé
- Pas de dépendances croisées

### 4. Performance

- Open Wearables : Optimisé pour ingestion
- Pulse : Optimisé pour transformation santé
- Pas de traitement redondant

## 📝 Code Exemple

### Open Wearables (Format Unifié)

```python
# Open Wearables reçoit Garmin
garmin_data = {
    "heartRate": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
    "sleepDuration": 28800
}

# Open Wearables unifie
unified_data = {
    "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
    "sleep": {"duration_seconds": 28800}
}

# Envoie à Pulse via webhook
```

### Pulse (Transformation Santé)

```python
# Pulse reçoit format unifié
unified_data = {
    "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
    "sleep": {"duration_seconds": 28800}
}

# Pulse transforme en métriques santé
normalizer = DataNormalizer()
normalized = normalizer.normalize_open_wearables_data(unified_data)

# Résultat : Métriques santé
# {
#   "metrics": {
#     "heart_rate": {
#       "average_bpm": 72,
#       "resting_bpm": 58,
#       "max_bpm": 145
#     },
#     "sleep": {
#       "duration_minutes": 480,
#       "quality_score": 85
#     }
#   }
# }

# Puis calcul baselines, anomalies, contexte...
```

## ✅ Checklist de Vérification

### Open Wearables

- [x] Unifie les structures JSON
- [x] Normalise les timestamps (ISO 8601)
- [x] Mappe les champs providers
- [x] Format commun cohérent
- [x] Ne calcule PAS les baselines
- [x] Ne détecte PAS les anomalies
- [x] Ne construit PAS le contexte santé

### Pulse

- [x] Reçoit format unifié Open Wearables
- [x] Convertit en unités standard (si nécessaire)
- [x] Agrège les données (moyennes, min, max)
- [x] Calcule les baselines (logique santé)
- [x] Détecte les anomalies (logique santé)
- [x] Construit le contexte (logique santé)
- [x] Évalue la qualité des données
- [x] Ne parse PAS les formats providers
- [x] Ne mappe PAS les champs providers

## 🔮 Évolutions Futures

### Ajouter un Nouveau Provider

**Modification** : Open Wearables uniquement
- Ajouter le parsing du nouveau provider
- Mapper vers le format commun
- Aucune modification dans Pulse

### Ajouter une Nouvelle Métrique Santé

**Modification** : Pulse uniquement
- Ajouter la transformation dans `normalize_open_wearables_data()`
- Ajouter le calcul de baseline
- Ajouter la détection d'anomalies
- Aucune modification dans Open Wearables

### Ajouter Apple Health Direct

**Modification** : Pulse uniquement
- Créer un nouveau normalizer pour Apple Health direct
- Utiliser la même logique santé (baselines, anomalies, contexte)
- Réutiliser `calculate_baseline()`, `_detect_anomalies()`, etc.

---

*Document créé le : 2024*
*Principe : Un seul endroit pour la logique "santé" = Pulse*
