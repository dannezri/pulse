# External Identities : Mapping d'Identité Multi-Providers

## 📋 Vue d'Ensemble

La table `external_identities` formalise le mapping entre les identifiants externes (providers) et les utilisateurs Supabase. Cela permet de :

- ✅ **Gérer plusieurs providers** : Open Wearables, Apple Health direct, imports de fichiers, etc.
- ✅ **Éviter les bricolages** : Structure claire et extensible
- ✅ **Traçabilité** : Historique des connexions avec métadonnées
- ✅ **Désactivation propre** : `is_active` au lieu de suppression

## 🏗️ Structure

### Table `external_identities`

```sql
CREATE TABLE external_identities (
    id UUID PRIMARY KEY,
    supabase_user_id UUID REFERENCES profiles(id),
    provider_system TEXT NOT NULL,        -- 'open_wearables', 'apple_health', etc.
    external_user_id TEXT NOT NULL,       -- ID dans le système externe
    metadata JSONB,                        -- Tokens, permissions, dates, etc.
    is_active BOOLEAN DEFAULT TRUE,        -- Permet de désactiver sans supprimer
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    UNIQUE(supabase_user_id, provider_system, external_user_id)
);
```

### Contrainte Unique

Un utilisateur peut avoir **un seul ID par provider**, mais peut avoir **plusieurs providers** :

```
user_123 → open_wearables:ow_user_456
user_123 → apple_health:ah_user_789
user_123 → file_import:import_2024_01_15
```

## 🔧 Utilisation

### Récupérer un utilisateur par ID externe

```python
from supabase_client import SupabaseClient

supabase = SupabaseClient(url, key)

# Méthode générique
user_id = supabase.get_user_by_external_id(
    external_user_id="ow_user_456",
    provider_system="open_wearables"
)

# Méthode de compatibilité (Open Wearables)
user_id = supabase.get_user_by_open_wearables_id("ow_user_456")
```

### Créer/Mettre à jour une identité externe

```python
# Lors de la connexion d'un nouveau provider
supabase.create_or_update_external_identity(
    supabase_user_id="uuid-supabase",
    provider_system="apple_health",
    external_user_id="ah_user_789",
    metadata={
        "oauth_token": "token_xyz",
        "connected_at": "2024-01-15T10:00:00Z",
        "permissions": ["heart_rate", "sleep"]
    }
)
```

### Récupérer toutes les identités d'un utilisateur

```python
identities = supabase.get_external_identities("uuid-supabase")

# Résultat:
# [
#     {
#         "provider_system": "open_wearables",
#         "external_user_id": "ow_user_456",
#         "is_active": True,
#         "metadata": {...}
#     },
#     {
#         "provider_system": "apple_health",
#         "external_user_id": "ah_user_789",
#         "is_active": True,
#         "metadata": {...}
#     }
# ]
```

### Désactiver une connexion

```python
# Désactiver une connexion spécifique
supabase.deactivate_external_identity(
    supabase_user_id="uuid-supabase",
    provider_system="open_wearables",
    external_user_id="ow_user_456"
)

# Ou désactiver toutes les connexions d'un provider
supabase.deactivate_external_identity(
    supabase_user_id="uuid-supabase",
    provider_system="open_wearables"
)
```

## 📊 Providers Supportés

### `open_wearables`
- **Description** : Open Wearables Ingestion Engine
- **external_user_id** : UUID Open Wearables
- **metadata** : Optionnel (API keys, etc.)

### `apple_health`
- **Description** : Apple Health direct (sans Open Wearables)
- **external_user_id** : ID Apple Health
- **metadata** : Tokens OAuth, permissions HealthKit

### `file_import`
- **Description** : Import de fichiers (XML, CSV, etc.)
- **external_user_id** : ID d'import unique
- **metadata** : Chemin fichier, date import, format

### `garmin_direct`
- **Description** : Garmin direct (sans Open Wearables)
- **external_user_id** : ID Garmin
- **metadata** : Tokens OAuth Garmin

## 🔄 Migration depuis `profiles.open_wearables_user_id`

La migration 005 a automatiquement migré les données existantes :

```sql
-- Avant (profiles)
SELECT id, open_wearables_user_id FROM profiles;

-- Après (external_identities)
SELECT supabase_user_id, external_user_id 
FROM external_identities 
WHERE provider_system = 'open_wearables';
```

**Note** : `profiles.open_wearables_user_id` existe toujours pour la rétrocompatibilité, mais les nouvelles insertions devraient utiliser `external_identities`.

## 🛠️ Fonctions SQL Utilitaires

### `get_supabase_user_by_external_id(provider_system, external_user_id)`

```sql
SELECT get_supabase_user_by_external_id('open_wearables', 'ow_user_456');
-- Retourne: UUID Supabase
```

### `get_external_identities(supabase_user_id)`

```sql
SELECT * FROM get_external_identities('uuid-supabase');
-- Retourne: Toutes les identités externes de l'utilisateur
```

## 📈 Cas d'Usage

### 1. Ajouter un nouveau provider

```python
# Lors de la connexion Apple Health
def connect_apple_health(supabase_user_id: str, apple_health_id: str, token: str):
    supabase.create_or_update_external_identity(
        supabase_user_id=supabase_user_id,
        provider_system="apple_health",
        external_user_id=apple_health_id,
        metadata={"oauth_token": token, "connected_at": datetime.now().isoformat()}
    )
```

### 2. Traiter un webhook multi-provider

```python
def handle_webhook(payload: Dict, provider: str):
    external_user_id = payload.get("user_id")
    
    # Récupérer l'utilisateur Supabase
    supabase_user_id = supabase.get_user_by_external_id(
        external_user_id=external_user_id,
        provider_system=provider  # 'open_wearables', 'apple_health', etc.
    )
    
    if not supabase_user_id:
        return {"error": "User not found"}
    
    # Traiter le webhook...
```

### 3. Lister les sources de données d'un utilisateur

```python
def get_user_data_sources(supabase_user_id: str):
    identities = supabase.get_external_identities(supabase_user_id)
    
    active_providers = [
        identity["provider_system"] 
        for identity in identities 
        if identity["is_active"]
    ]
    
    return active_providers
# Retourne: ['open_wearables', 'apple_health']
```

## 🔐 Sécurité

### Row Level Security (RLS)

- **Service role** : Peut tout faire (insertions, mises à jour)
- **Utilisateurs** : Peuvent voir et mettre à jour leurs propres identités

### Bonnes Pratiques

1. **Ne jamais exposer les tokens** dans les réponses API
2. **Valider les permissions** avant d'utiliser une identité externe
3. **Désactiver au lieu de supprimer** pour garder l'historique
4. **Chiffrer les tokens sensibles** dans `metadata` si nécessaire

## 📊 Requêtes Utiles

### Compter les utilisateurs par provider

```sql
SELECT 
    provider_system,
    COUNT(DISTINCT supabase_user_id) as user_count
FROM external_identities
WHERE is_active = TRUE
GROUP BY provider_system;
```

### Trouver les utilisateurs avec plusieurs providers

```sql
SELECT 
    supabase_user_id,
    COUNT(*) as provider_count,
    array_agg(provider_system) as providers
FROM external_identities
WHERE is_active = TRUE
GROUP BY supabase_user_id
HAVING COUNT(*) > 1;
```

### Vérifier les connexions inactives

```sql
SELECT 
    provider_system,
    COUNT(*) as inactive_count
FROM external_identities
WHERE is_active = FALSE
GROUP BY provider_system;
```

## 🚀 Évolutions Futures

### Ajout d'un nouveau provider

1. **Définir le `provider_system`** : Ex: `'fitbit_direct'`
2. **Utiliser `create_or_update_external_identity`** lors de la connexion
3. **Utiliser `get_user_by_external_id`** pour récupérer l'utilisateur
4. **Aucune modification de schéma nécessaire** ✅

### Exemple : Ajouter Fitbit

```python
# Connexion Fitbit
supabase.create_or_update_external_identity(
    supabase_user_id=user_id,
    provider_system="fitbit_direct",
    external_user_id=fitbit_user_id,
    metadata={"fitbit_token": token}
)

# Récupération
user_id = supabase.get_user_by_external_id(
    external_user_id=fitbit_user_id,
    provider_system="fitbit_direct"
)
```

---

*Document créé le : 2024*
*Migration : 005_add_external_identities.sql*
