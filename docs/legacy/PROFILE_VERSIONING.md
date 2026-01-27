# Versioning du Profil de Santé

## 📋 Vue d'Ensemble

Le système de versioning permet d'évoluer le format JSON du profil de santé sans casser l'application existante. Chaque profil inclut des métadonnées de version pour permettre :

- ✅ **Évolution du schéma** : Ajouter/modifier des champs sans casser l'IA
- ✅ **Recalcul** : Recalculer les profils d'une version spécifique
- ✅ **Compatibilité** : L'application peut gérer plusieurs versions simultanément
- ✅ **Traçabilité** : Savoir quel normalizer a généré chaque profil

## 🏗️ Structure

### Champs de Version dans `health_profiles`

```sql
CREATE TABLE health_profiles (
    ...
    profile_version INTEGER DEFAULT 1,      -- Version du format JSON (1, 2, 3, ...)
    normalizer_version TEXT,                -- Version du normalizer ("1.0.0", "1.1.0", ...)
    schema_version TEXT                     -- Version du schéma source (optionnel)
);
```

### Métadonnées dans le JSON

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {...},
  "baselines": {...},
  "anomalies": [...],
  "context": {...},
  "_version": {
    "profile_version": 1,
    "normalizer_version": "1.0.0",
    "schema_version": "1.0"
  }
}
```

## 🔧 Utilisation

### Créer un Profil avec Version

```python
from data_normalizer import DataNormalizer

normalizer = DataNormalizer()

# Le normalizer inclut automatiquement les versions
profile = normalizer.create_health_profile(
    today_data=today_data,
    baseline_data=baseline_data,
    user_goal="energy"
)

# Le profil contient _version avec les métadonnées
print(profile["_version"])
# {
#     "profile_version": 1,
#     "normalizer_version": "1.0.0",
#     "schema_version": "1.0"
# }

# Sauvegarder (les versions sont extraites automatiquement)
supabase_client.save_health_profile(user_id, profile)
```

### Récupérer les Versions

```python
# Obtenir les informations de version du normalizer
version_info = normalizer.get_version_info()
# {
#     "profile_version": 1,
#     "normalizer_version": "1.0.0",
#     "schema_version": "1.0"
# }
```

### Filtrer par Version

```sql
-- Récupérer tous les profils version 1 d'un utilisateur
SELECT * FROM health_profiles
WHERE user_id = '...'
  AND profile_version = 1
ORDER BY date DESC;

-- Compter les profils par version
SELECT profile_version, COUNT(*) 
FROM health_profiles
WHERE user_id = '...'
GROUP BY profile_version;
```

## 📊 Évolution du Schéma

### Exemple : Passage de Version 1 à Version 2

#### Version 1 (Actuelle)

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {
    "heart_rate": {
      "average_bpm": 72,
      "resting_bpm": 58
    }
  },
  "_version": {
    "profile_version": 1,
    "normalizer_version": "1.0.0"
  }
}
```

#### Version 2 (Future)

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {
    "heart_rate": {
      "average_bpm": 72,
      "resting_bpm": 58,
      "variability": 12.5,  // NOUVEAU CHAMP
      "zones": {            // NOUVEAU CHAMP
        "fat_burn": 120,
        "cardio": 150
      }
    }
  },
  "trends": {               // NOUVEAU CHAMP
    "7_day_hrv_trend": "improving"
  },
  "_version": {
    "profile_version": 2,
    "normalizer_version": "1.1.0"
  }
}
```

### Migration de Version

```python
# 1. Mettre à jour le normalizer
class DataNormalizer:
    PROFILE_VERSION = 2  # Nouvelle version
    NORMALIZER_VERSION = "1.1.0"
    
    def create_health_profile(self, ...):
        # Nouveau format avec champs additionnels
        profile = {
            ...
            "current_metrics": {
                "heart_rate": {
                    "average_bpm": 72,
                    "resting_bpm": 58,
                    "variability": self._calculate_variability(...),  # NOUVEAU
                    "zones": self._calculate_zones(...)               # NOUVEAU
                }
            },
            "trends": self._calculate_7day_trends(...),  # NOUVEAU
            "_version": {
                "profile_version": 2,
                "normalizer_version": "1.1.0"
            }
        }
        return profile

# 2. L'application peut gérer les deux versions
def generate_insight(user_id: str):
    profile = supabase_client.get_latest_health_profile(user_id)
    
    if profile.get("_version", {}).get("profile_version") == 1:
        # Traitement pour version 1
        return generate_insight_v1(profile)
    elif profile.get("_version", {}).get("profile_version") == 2:
        # Traitement pour version 2 (avec nouveaux champs)
        return generate_insight_v2(profile)
```

### Recalcul des Profils

```python
# Recalculer tous les profils version 1 en version 2
def recalculate_profiles_to_v2(user_id: str):
    # Récupérer tous les profils version 1
    old_profiles = supabase_client.client.table("health_profiles").select("*").eq(
        "user_id", user_id
    ).eq("profile_version", 1).execute()
    
    # Mettre à jour le normalizer
    normalizer.PROFILE_VERSION = 2
    normalizer.NORMALIZER_VERSION = "1.1.0"
    
    for old_profile in old_profiles.data:
        # Récupérer les données brutes de la date
        date = old_profile["date"]
        raw_data = get_raw_data_for_date(user_id, date)
        
        # Recalculer avec le nouveau normalizer
        new_profile = normalizer.create_health_profile(
            today_data=raw_data,
            baseline_data=compute_baselines(user_id, date),
            user_goal=old_profile["profile_data"]["user_goal"]
        )
        
        # Sauvegarder (écrase l'ancien profil grâce à UNIQUE(user_id, date))
        supabase_client.save_health_profile(user_id, new_profile)
```

## 🔍 Fonctions SQL Utilitaires

### `get_profiles_by_version(user_id, profile_version)`

```sql
SELECT * FROM get_profiles_by_version('uuid-user', 1);
-- Retourne tous les profils version 1 de l'utilisateur
```

### `count_profiles_by_version(user_id)`

```sql
SELECT * FROM count_profiles_by_version('uuid-user');
-- Retourne:
-- profile_version | count
-- ----------------|-------
-- 1               | 100
-- 2               | 50
```

## 📝 Bonnes Pratiques

### 1. Toujours inclure les versions

```python
# ✅ CORRECT
profile = normalizer.create_health_profile(...)
# Le profil inclut automatiquement _version

# ❌ INCORRECT
profile = {
    "timestamp": "...",
    "current_metrics": {...}
    # Pas de _version !
}
```

### 2. Vérifier la version avant traitement

```python
# ✅ CORRECT
def process_profile(profile: Dict):
    version = profile.get("_version", {}).get("profile_version", 1)
    
    if version == 1:
        return process_v1(profile)
    elif version == 2:
        return process_v2(profile)
    else:
        raise ValueError(f"Version non supportée: {version}")
```

### 3. Compatibilité ascendante

```python
# ✅ CORRECT : Gérer plusieurs versions
def get_heart_rate(profile: Dict):
    version = profile.get("_version", {}).get("profile_version", 1)
    hr = profile["current_metrics"]["heart_rate"]
    
    if version >= 2:
        # Utiliser les nouveaux champs si disponibles
        return {
            "average": hr.get("average_bpm"),
            "variability": hr.get("variability"),  # Nouveau en v2
            "zones": hr.get("zones")               # Nouveau en v2
        }
    else:
        # Fallback pour version 1
        return {
            "average": hr.get("average_bpm"),
            "variability": None,
            "zones": None
        }
```

### 4. Incrémenter la version lors de changements majeurs

- **Version mineure** (1.0.0 → 1.1.0) : Ajout de champs optionnels
- **Version majeure** (1.0.0 → 2.0.0) : Changement de structure, passage à `profile_version = 2`

## 🚀 Migration de Version

### Plan de Migration

1. **Développer la nouvelle version** dans le normalizer
2. **Tester** avec quelques utilisateurs
3. **Déployer** le nouveau normalizer
4. **Recalculer progressivement** les profils existants (optionnel)
5. **Mettre à jour l'application** pour gérer les deux versions
6. **Déprécier l'ancienne version** après un délai raisonnable

### Script de Migration

```python
def migrate_profiles_to_v2():
    """
    Migre tous les profils version 1 vers version 2
    """
    # Récupérer tous les utilisateurs avec des profils v1
    users = supabase_client.client.table("health_profiles").select(
        "user_id"
    ).eq("profile_version", 1).execute()
    
    unique_users = set(profile["user_id"] for profile in users.data)
    
    for user_id in unique_users:
        try:
            recalculate_profiles_to_v2(user_id)
            logger.info(f"Migré user {user_id}")
        except Exception as e:
            logger.error(f"Erreur migration user {user_id}: {e}")
```

## 📊 Monitoring

### Vérifier la Distribution des Versions

```sql
-- Distribution globale
SELECT 
    profile_version,
    COUNT(*) as count,
    COUNT(DISTINCT user_id) as unique_users
FROM health_profiles
GROUP BY profile_version
ORDER BY profile_version;

-- Par utilisateur
SELECT 
    user_id,
    profile_version,
    COUNT(*) as count
FROM health_profiles
GROUP BY user_id, profile_version
ORDER BY user_id, profile_version;
```

### Identifier les Profils à Recalculer

```sql
-- Profils version 1 créés après le déploiement de la v2
SELECT 
    user_id,
    date,
    created_at
FROM health_profiles
WHERE profile_version = 1
  AND created_at > '2024-02-01'  -- Date de déploiement v2
ORDER BY created_at DESC;
```

---

*Document créé le : 2024*
*Migration : 007_add_profile_versioning.sql*
*Version actuelle : profile_version = 1, normalizer_version = "1.0.0"*
