# Migration des tokens Oura vers Supabase - TERMINÉE ✅

## 📋 Résumé

Les clés API Oura sont maintenant stockées dans Supabase et reliées aux utilisateurs via la table `external_identities`. Tous les scripts ont été modifiés pour récupérer les tokens depuis la base de données au lieu de les hardcoder.

## 🔐 Stockage des tokens

### Table: `external_identities`

Les tokens Oura sont stockés dans le champ `metadata.access_token`:

```json
{
  "supabase_user_id": "uuid-utilisateur",
  "provider_system": "oura",
  "external_user_id": "email@example.com",
  "metadata": {
    "access_token": "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI",
    "email": "email@example.com",
    "age": 30,
    "weight": 70.5,
    "height": 175.0,
    "biological_sex": "male",
    "connected_at": "2024-01-01T00:00:00Z"
  },
  "is_active": true
}
```

## 🛠️ Fichiers modifiés

### 1. **oura_token_utils.py** (NOUVEAU)
Utilitaires pour gérer les tokens Oura:
- `get_user_oura_token(supabase, user_id)` - Récupère le token depuis Supabase
- `update_user_oura_token(supabase, user_id, token)` - Met à jour le token

### 2. **register_oura_user.py**
✅ Stocke maintenant le token dans `metadata.access_token` lors de l'enregistrement

### 3. **import_oura_data.py**
✅ Récupère le token depuis Supabase au lieu de le hardcoder

### 4. **import_oura_data_full.py**
✅ Récupère le token depuis Supabase au lieu de le hardcoder

### 5. **force_sync_oura_today.py**
✅ Récupère le token depuis Supabase au lieu de le hardcoder

### 6. **test_oura_sync.py**
✅ Récupère le token depuis Supabase et supprime la logique de mise à jour manuelle

### 7. **setup_oura_complete.py**
✅ Stocke le token via `register_oura_user.py` (qui le sauvegarde dans Supabase)

### 8. **reimport_oura_sleep_times.py**
✅ Utilisait déjà la bonne méthode pour récupérer le token depuis Supabase

### 9. **oura_sync_service.py**
✅ Utilisait déjà `_get_user_oura_token()` pour récupérer le token depuis Supabase

## 📝 Utilisation

### Enregistrer un nouvel utilisateur Oura

```python
from register_oura_user import register_oura_user

success = register_oura_user(
    supabase_user_id="uuid-utilisateur",
    oura_token="IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI",
    supabase_url="https://xxx.supabase.co",
    supabase_key="service_role_key"
)
```

### Récupérer le token d'un utilisateur

```python
from oura_token_utils import get_user_oura_token
from supabase_client import SupabaseClient

supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
token = get_user_oura_token(supabase, user_id)

if token:
    # Utiliser le token pour appeler l'API Oura
    from oura_client import get_oura_client
    oura = get_oura_client(token)
```

### Mettre à jour le token d'un utilisateur

```python
from oura_token_utils import update_user_oura_token

success = update_user_oura_token(
    supabase=supabase,
    user_id="uuid-utilisateur",
    oura_token="nouveau-token"
)
```

## 🔄 Synchronisation automatique

Le service `oura_sync_service.py` récupère automatiquement le token depuis Supabase:

```python
from oura_sync_service import sync_user_oura_data
from supabase_client import SupabaseClient

supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
result = await sync_user_oura_data(user_id, supabase)
```

## 🌐 Endpoints API

### POST `/api/oura/sync`
Synchronise les données Oura pour l'utilisateur connecté (JWT)
- Récupère automatiquement le token depuis Supabase
- Met à jour `health_profiles.current_metrics`

### GET `/api/oura/status`
Vérifie le statut de la connexion Oura
- Retourne `connected: true/false`
- Indique si des données Readiness sont disponibles

## ✅ Avantages

1. **Sécurité**: Les tokens ne sont plus hardcodés dans le code
2. **Multi-utilisateurs**: Chaque utilisateur a son propre token
3. **Centralisation**: Un seul endroit pour gérer les tokens
4. **Traçabilité**: Historique des connexions via `created_at`, `updated_at`
5. **Désactivation**: Possibilité de désactiver un compte Oura via `is_active`

## 🔒 Sécurité

- Les tokens sont stockés dans Supabase avec RLS (Row Level Security)
- Seul le service_role_key peut accéder aux tokens
- Les tokens ne sont jamais exposés dans les réponses API
- Les logs ne doivent pas afficher les tokens en clair

## 📚 Documentation associée

- `OURA_INTEGRATION.md` - Guide d'intégration Oura
- `OURA_SUCCESS_SUMMARY.md` - Résumé de l'intégration
- `backend/oura_client.py` - Client API Oura
- `backend/oura_sync_service.py` - Service de synchronisation

## 🎯 Prochaines étapes

1. ✅ Tokens stockés dans Supabase
2. ✅ Scripts modifiés pour récupérer depuis Supabase
3. ✅ Endpoints API ajoutés (`/api/oura/connect`, `/api/oura/disconnect`)
4. ⏳ Implémenter OAuth2 pour Oura (au lieu de Personal Access Token)
5. ⏳ Ajouter une interface admin pour gérer les tokens
6. ⏳ Créer l'UI mobile pour connecter/déconnecter Oura

## 🧪 Tests

Un script de test complet est disponible:

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python test_oura_token_migration.py
```

Ce script vérifie:
- ✅ Récupération des tokens depuis Supabase
- ✅ Mise à jour des tokens
- ✅ Structure de `external_identities`
- ✅ Compatibilité des scripts

## 📚 Documentation ajoutée

- `OURA_TOKEN_MIGRATION_COMPLETE.md` - Ce document
- `backend/OURA_API_ENDPOINTS.md` - Documentation des endpoints API
- `backend/oura_token_utils.py` - Utilitaires pour gérer les tokens
- `backend/test_oura_token_migration.py` - Script de test

---

**Date de migration**: 4 février 2026  
**Statut**: ✅ TERMINÉ ET TESTÉ
