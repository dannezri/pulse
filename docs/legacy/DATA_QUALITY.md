# Gestion de la Qualité des Données et Baselines

## 📋 Vue d'Ensemble

Le système gère automatiquement les **trous dans les données** (jours sans wearable, provider qui n'envoie pas certaines métriques) pour éviter des recommandations absurdes basées sur des baselines peu fiables.

## 🔄 Règles de Fallback pour les Baselines

### Stratégie de Fallback Automatique

Le système essaie automatiquement plusieurs périodes jusqu'à avoir assez de données :

1. **7 jours** (cible) : Si ≥3 points de données → Utilisé
2. **14 jours** (fallback 1) : Si pas assez sur 7j → Étend à 14j
3. **30 jours** (fallback 2) : Si pas assez sur 14j → Étend à 30j

### Exemple

```python
# Cas 1 : Données complètes (7 jours)
# HRV : 7 points de données sur 7 jours → baseline calculée sur 7j
baseline, metadata = normalizer.calculate_baseline(historical_data, "hrv", days=7)
# metadata = {
#     "actual_days": 7,
#     "data_points": 7,
#     "data_quality": "high",
#     "fallback_used": False
# }

# Cas 2 : Trous dans les données (2 jours sans wearable)
# HRV : 5 points de données sur 7 jours → fallback à 14j
# HRV : 8 points de données sur 14 jours → baseline calculée sur 14j
baseline, metadata = normalizer.calculate_baseline(historical_data, "hrv", days=7)
# metadata = {
#     "actual_days": 14,
#     "data_points": 8,
#     "data_quality": "medium",
#     "fallback_used": True
# }

# Cas 3 : Données très fragmentées
# HRV : 3 points de données sur 30 jours → baseline calculée mais qualité faible
baseline, metadata = normalizer.calculate_baseline(historical_data, "hrv", days=7)
# metadata = {
#     "actual_days": 30,
#     "data_points": 3,
#     "data_quality": "low",
#     "fallback_used": True
# }
```

## 📊 Qualité des Données

### Niveaux de Qualité

La qualité est déterminée par le **ratio de couverture** :

- **High** : ≥70% de couverture (ex: 5+ jours sur 7)
- **Medium** : ≥40% de couverture (ex: 3-4 jours sur 7, ou 6+ jours sur 14)
- **Low** : <40% de couverture (ex: 2 jours sur 7, ou 3 jours sur 30)

### Qualité Globale du Profil

Le champ `data_quality` dans le profil combine :

1. **Disponibilité des métriques du jour** :
   - High : 3-4 métriques disponibles (HR, HRV, sleep, activity)
   - Medium : 2 métriques disponibles
   - Low : 1 métrique ou moins

2. **Qualité des baselines** :
   - Basé sur la moyenne des qualités des baselines individuelles

3. **Qualité globale** : Minimum des deux (conservatif)

### Format du Profil

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {...},
  "baselines": {
    "hrv_baseline": 65,
    "hr_baseline": 60,
    "sleep_baseline": 450,
    "hrv_baseline_metadata": {
      "actual_days": 14,
      "data_points": 8,
      "data_quality": "medium",
      "fallback_used": true
    },
    "hr_baseline_metadata": {
      "actual_days": 7,
      "data_points": 6,
      "data_quality": "high",
      "fallback_used": false
    },
    "sleep_baseline_metadata": {
      "actual_days": 7,
      "data_points": 7,
      "data_quality": "high",
      "fallback_used": false
    }
  },
  "anomalies": [...],
  "data_quality": "medium",  // Qualité globale
  ...
}
```

## 🚨 Confiance des Anomalies

### Niveau de Confiance

Chaque anomalie inclut un champ `confidence` basé sur la qualité de la baseline utilisée :

- **High** : Baseline de qualité "high" → Anomalie fiable
- **Low** : Baseline de qualité "medium" ou "low" → Anomalie à interpréter avec prudence

### Format des Anomalies

```json
{
  "type": "hrv_drop",
  "severity": "medium",
  "confidence": "low",  // Basé sur baseline_quality
  "current": 55,
  "baseline": 68,
  "drop_percentage": 19.12,
  "baseline_quality": "medium",  // Qualité de la baseline utilisée
  "baseline_data_points": 5      // Nombre de points utilisés
}
```

### Utilisation par l'IA

L'IA peut adapter ses recommandations selon la confiance :

```python
def generate_insight(profile: Dict):
    data_quality = profile.get("data_quality", "low")
    anomalies = profile.get("anomalies", [])
    
    # Filtrer les anomalies peu fiables si qualité faible
    if data_quality == "low":
        reliable_anomalies = [
            a for a in anomalies 
            if a.get("confidence") == "high"
        ]
        if not reliable_anomalies:
            return "Données insuffisantes pour générer une recommandation fiable."
    
    # Générer l'insight avec les anomalies fiables
    ...
```

## 📈 Exemples de Scénarios

### Scénario 1 : Données Complètes

```
Jour 1-7 : HRV mesurée chaque jour (7 points)
→ Baseline calculée sur 7 jours
→ Qualité : High
→ Confiance anomalies : High
```

### Scénario 2 : 2 Jours Sans Wearable

```
Jour 1-5 : HRV mesurée (5 points)
Jour 6-7 : Pas de données (wearable oublié)
→ Fallback à 14 jours
→ Baseline calculée sur 14 jours avec 8 points
→ Qualité : Medium
→ Confiance anomalies : Low
```

### Scénario 3 : Provider Sans HRV

```
Jour 1-7 : HR mesurée chaque jour (7 points)
Jour 1-7 : HRV jamais mesurée (provider ne supporte pas)
→ HR baseline : High quality
→ HRV baseline : None (pas de données)
→ Qualité globale : Medium (HRV manquante)
```

### Scénario 4 : Données Très Fragmentées

```
Jour 1-30 : Seulement 3 jours avec HRV
→ Fallback à 30 jours
→ Baseline calculée avec 3 points seulement
→ Qualité : Low
→ Confiance anomalies : Low
→ Recommandation : Éviter de générer des insights basés sur HRV
```

## 🛠️ Configuration

### Paramètres du Normalizer

```python
class DataNormalizer:
    # Périodes de fallback (en jours)
    FALLBACK_PERIODS = [7, 14, 30]
    
    # Minimum de points de données requis
    MIN_DATA_POINTS = 3
    
    # Seuils de qualité
    HIGH_QUALITY_THRESHOLD = 0.7  # 70% de couverture
    MEDIUM_QUALITY_THRESHOLD = 0.4  # 40% de couverture
```

### Ajuster les Seuils

```python
# Pour être plus strict (nécessite plus de données)
normalizer.MIN_DATA_POINTS = 5
normalizer.HIGH_QUALITY_THRESHOLD = 0.8  # 80% de couverture

# Pour être plus permissif (accepte moins de données)
normalizer.MIN_DATA_POINTS = 2
normalizer.HIGH_QUALITY_THRESHOLD = 0.6  # 60% de couverture
```

## 📝 Bonnes Pratiques

### 1. Toujours Vérifier la Qualité

```python
# ✅ CORRECT
profile = supabase_client.get_latest_health_profile(user_id)
data_quality = profile.get("data_quality", "low")

if data_quality == "low":
    # Avertir l'utilisateur ou utiliser des recommandations génériques
    return generate_generic_insight()
else:
    return generate_personalized_insight(profile)
```

### 2. Filtrer les Anomalies par Confiance

```python
# ✅ CORRECT
anomalies = profile.get("anomalies", [])
reliable_anomalies = [
    a for a in anomalies 
    if a.get("confidence") == "high"
]

if not reliable_anomalies and data_quality == "low":
    # Ne pas générer d'insight basé sur des anomalies peu fiables
    return None
```

### 3. Informer l'Utilisateur

```python
# ✅ CORRECT
if data_quality == "low":
    insight = generate_insight(profile)
    insight["warning"] = "Données limitées. Recommandation basée sur peu de données."
    return insight
```

## 🔍 Monitoring

### Vérifier la Distribution de Qualité

```sql
-- Distribution de la qualité des profils
SELECT 
    data_quality,
    COUNT(*) as count
FROM health_profiles
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY data_quality;

-- Profils avec baselines utilisant fallback
SELECT 
    user_id,
    date,
    profile_data->'baselines'->'hrv_baseline_metadata'->>'fallback_used' as hrv_fallback,
    profile_data->'baselines'->'hr_baseline_metadata'->>'fallback_used' as hr_fallback
FROM health_profiles
WHERE profile_data->'baselines'->'hrv_baseline_metadata'->>'fallback_used' = 'true'
   OR profile_data->'baselines'->'hr_baseline_metadata'->>'fallback_used' = 'true';
```

### Identifier les Utilisateurs avec Données Fragmentées

```sql
-- Utilisateurs avec qualité faible récurrente
SELECT 
    user_id,
    COUNT(*) as low_quality_days
FROM health_profiles
WHERE profile_data->>'data_quality' = 'low'
  AND date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id
HAVING COUNT(*) > 10
ORDER BY low_quality_days DESC;
```

## 🚀 Améliorations Futures

### Suggestions

1. **Alertes utilisateur** : Notifier si qualité faible pendant plusieurs jours
2. **Recommandations adaptatives** : Ajuster les seuils selon la qualité
3. **Apprentissage** : Ajuster les baselines selon les patterns historiques
4. **Multi-provider** : Combiner les données de plusieurs sources

---

*Document créé le : 2024*
*Version normalizer : 1.0.0*
