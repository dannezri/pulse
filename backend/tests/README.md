# Tests Unitaires - Backend Pulse

## 📋 Vue d'Ensemble

Ce dossier contient les tests unitaires pour le backend Pulse, en particulier pour la logique santé du `DataNormalizer`.

## 🧪 Tests Disponibles

### `test_idempotence.py`

Tests d'intégrité pour vérifier l'idempotence et le dédoublonnage des webhooks :

1. **Idempotence au niveau API** (`TestWebhookIdempotence`)
   - Envoi du même webhook deux fois → pas de doublons dans `biometrics`
   - Vérification que `insert_biometric` détecte les doublons via `source_event_id`
   - Vérification que des mesures avec des `source_event_id` différents sont bien insérées séparément
   - Simulation du traitement d'un webhook par le worker deux fois (retry) → pas de doublons

2. **Génération de `source_event_id`** (`TestSourceEventIdGeneration`)
   - Génération avec `base_event_id` fourni
   - Génération sans `base_event_id` (fallback hash)
   - Consistance : même entrée → même `source_event_id`

**Scénario principal** : Open Wearables envoie deux fois le même webhook à 1 seconde d'intervalle. Le système doit détecter les doublons grâce à `source_event_id` et ne pas créer de doublons dans la table `biometrics`.

### `test_normalizer.py`

Tests unitaires pour `DataNormalizer` qui vérifient :

1. **Calcul de baseline avec fallback** (`TestCalculateBaseline`)
   - Baseline avec 5 jours de données (pas de fallback nécessaire)
   - Baseline avec 7 jours complets
   - Fallback à 14 jours quand données insuffisantes sur 7 jours
   - Cas sans données
   - Cas avec données insuffisantes même avec fallback
   - Tests pour différentes métriques (HRV, HR, sleep)

2. **Détection d'anomalies** (`TestAnomalyDetection`)
   - Chute brutale de HRV avec confiance high/low
   - Déficit de sommeil
   - Fréquence cardiaque au repos élevée
   - Pas d'anomalie quand valeurs normales
   - Gestion des données manquantes

3. **Qualité des données** (`TestDataQuality`)
   - Qualité high avec données complètes
   - Qualité low avec données manquantes

4. **Profil de santé** (`TestHealthProfile`)
   - Création d'un profil de santé complet avec versioning

## 🚀 Exécution des Tests

### Installation des dépendances

```bash
cd backend
pip install -r requirements.txt
```

### Exécuter tous les tests

```bash
python3 -m pytest tests/ -v
```

### Exécuter un fichier de test spécifique

```bash
# Tests de normalisation
python3 -m pytest tests/test_normalizer.py -v

# Tests d'idempotence
python3 -m pytest tests/test_idempotence.py -v
```

### Exécuter une classe de tests spécifique

```bash
python3 -m pytest tests/test_normalizer.py::TestCalculateBaseline -v
```

### Exécuter un test spécifique

```bash
# Test de normalisation
python3 -m pytest tests/test_normalizer.py::TestCalculateBaseline::test_calculate_baseline_with_5_days -v

# Test d'idempotence
python3 -m pytest tests/test_idempotence.py::TestWebhookIdempotence::test_webhook_idempotence_at_api_level -v
```

**Note** : Utilisez `python3 -m pytest` au lieu de `pytest` directement si la commande `pytest` n'est pas trouvée dans votre PATH.

## 📝 Format des Données de Test

Les tests utilisent le format de données attendu par `calculate_baseline`, qui correspond au format retourné par `get_historical_biometrics` :

```python
historical_data = [
    {
        "date": "2024-01-15",  # Format ISO date "YYYY-MM-DD"
        "metrics": {
            "hrv": 60.0,      # Float directement (moyenne du jour)
            "hr": 72.0,       # Float directement
            "sleep_duration": 450.0  # Float directement (en minutes)
        }
    },
    ...
]
```

## ✅ Scénarios Testés

### Fallback 7j → 14j → 30j

Le système utilise automatiquement un fallback si pas assez de données :

- **5 jours de données sur 7 jours demandés** : Pas de fallback (5 ≥ min_data_points=3)
- **2 jours sur 7, mais 5 jours entre 8-14** : Fallback à 14 jours
- **Données insuffisantes même sur 30 jours** : Baseline = None

### Détection d'Anomalies avec Confiance

- **HRV chute de 50%** (60 → 30) : Anomalie détectée
  - Confiance `high` si baseline de qualité `high`
  - Confiance `low` si baseline de qualité `low`
- **Sommeil déficit > 1h** : Anomalie détectée
- **HR au repos +15 bpm** : Anomalie détectée

## 🔍 Vérification Manuelle

Pour tester manuellement un scénario :

```python
from data_normalizer import DataNormalizer
from datetime import datetime, timedelta

normalizer = DataNormalizer()

# Données sur 5 jours
historical_data = [
    {
        "date": (datetime.now() - timedelta(days=i)).date().isoformat(),
        "metrics": {"hrv": 60.0 + i}
    }
    for i in range(1, 6)
]

baseline, metadata = normalizer.calculate_baseline(historical_data, metric_type="hrv", days=7)
print(f"Baseline: {baseline}")
print(f"Metadata: {metadata}")
```

## 📚 Documentation Complémentaire

- `../data_normalizer.py` : Implémentation du normalizer
- `../DATA_QUALITY.md` : Documentation sur la gestion de la qualité des données
- `../IDEMPOTENCE.md` : Documentation sur l'idempotence et le dédoublonnage
- `../ARCHITECTURE.md` : Architecture globale du projet
