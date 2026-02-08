# Résumé: Migration des tokens Oura vers Supabase ✅

## 🎯 Objectif

Faire en sorte que les clés API Oura soient enregistrées dans Supabase et reliées à un utilisateur, puis modifier tous les scripts pour qu'ils puissent les récupérer via Supabase.

## ✅ Travail effectué

### 1. Stockage des tokens dans Supabase

**Table utilisée**: `external_identities`

Structure:
```sql
external_identities (
  id uuid PRIMARY KEY,
  supabase_user_id uuid REFERENCES profiles(id),
  provider_system text,  -- 'oura'
  external_user_id text,  -- email Oura
  metadata jsonb,  -- Contient access_token + infos utilisateur
  is_active boolean,
  created_at timestamptz,
  updated_at timestamptz
)
```

Le token est stocké dans `metadata.access_token`.

### 2. Création d'utilitaires

**Fichier**: `backend/oura_token_utils.py`

Fonctions:
- `get_user_oura_token(supabase, user_id)` - Récupère le token
- `update_user_oura_token(supabase, user_id, token)` - Met à jour le token

### 3. Modification des scripts

Tous les scripts ont été modifiés pour utiliser `oura_token_utils`:

| Script | Statut | Changement |
|--------|--------|------------|
| `register_oura_user.py` | ✅ | Stocke le token dans `metadata.access_token` |
| `import_oura_data.py` | ✅ | Récupère le token via `get_user_oura_token()` |
| `import_oura_data_full.py` | ✅ | Récupère le token via `get_user_oura_token()` |
| `force_sync_oura_today.py` | ✅ | Récupère le token via `get_user_oura_token()` |
| `test_oura_sync.py` | ✅ | Récupère le token via `get_user_oura_token()` |
| `setup_oura_complete.py` | ✅ | Utilise `register_oura_user()` qui stocke le token |
| `reimport_oura_sleep_times.py` | ✅ | Utilisait déjà la bonne méthode |
| `oura_sync_service.py` | ✅ | Utilisait déjà `_get_user_oura_token()` |

### 4. Nouveaux endpoints API

**Fichier**: `backend/api_server.py`

Endpoints ajoutés:

#### POST `/api/oura/connect`
Connecte un compte Oura à l'utilisateur.

```bash
curl -X POST "http://localhost:8000/api/oura/connect" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"}'
```

#### POST `/api/oura/disconnect`
Déconnecte le compte Oura (met `is_active` à `false`).

```bash
curl -X POST "http://localhost:8000/api/oura/disconnect" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

#### GET `/api/oura/status`
Vérifie le statut de la connexion Oura (existait déjà).

```bash
curl -X GET "http://localhost:8000/api/oura/status" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 5. Documentation

Fichiers créés:
- `OURA_TOKEN_MIGRATION_COMPLETE.md` - Documentation complète de la migration
- `backend/OURA_API_ENDPOINTS.md` - Documentation des endpoints API
- `backend/test_oura_token_migration.py` - Script de test automatisé
- `RESUME_MIGRATION_OURA_TOKENS.md` - Ce fichier

## 🧪 Tests

Pour tester la migration:

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python test_oura_token_migration.py
```

Le script vérifie:
1. ✅ Récupération des tokens depuis Supabase
2. ✅ Mise à jour des tokens
3. ✅ Structure de `external_identities`
4. ✅ Compatibilité des scripts

## 📱 Intégration mobile

### Exemple d'utilisation dans l'app React Native

```typescript
// Vérifier si Oura est connecté
const checkOuraConnection = async () => {
  const response = await fetch('/api/oura/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.connected;
};

// Connecter Oura
const connectOura = async (ouraToken: string) => {
  const response = await fetch('/api/oura/connect', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ access_token: ouraToken })
  });
  
  if (!response.ok) throw new Error('Failed to connect');
  return await response.json();
};

// Synchroniser les données
const syncOura = async () => {
  const response = await fetch('/api/oura/sync', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

## 🔐 Sécurité

- ✅ Les tokens ne sont plus hardcodés dans le code
- ✅ Les tokens sont stockés dans Supabase avec RLS
- ✅ Seul le service_role_key peut accéder aux tokens
- ✅ Les tokens ne sont jamais exposés dans les réponses API
- ✅ Les logs ne doivent pas afficher les tokens en clair

## 📊 Flux de données

```
1. Utilisateur entre son token Oura dans l'app mobile
   ↓
2. App mobile appelle POST /api/oura/connect
   ↓
3. Backend valide le token via l'API Oura
   ↓
4. Backend stocke le token dans external_identities.metadata.access_token
   ↓
5. Lors de la sync, backend récupère le token via get_user_oura_token()
   ↓
6. Backend appelle l'API Oura avec le token
   ↓
7. Données Oura stockées dans biometrics et health_profiles
```

## 🎯 Prochaines étapes

### Court terme (recommandé)
1. ⏳ Créer l'UI mobile pour connecter/déconnecter Oura
2. ⏳ Ajouter un bouton "Synchroniser maintenant" dans l'app
3. ⏳ Afficher le statut de la dernière sync

### Moyen terme
4. ⏳ Implémenter OAuth2 pour Oura (meilleure UX)
5. ⏳ Ajouter un système de refresh automatique quotidien
6. ⏳ Gérer l'expiration des tokens

### Long terme
7. ⏳ Interface admin pour gérer les connexions Oura
8. ⏳ Support de plusieurs providers (Garmin, Fitbit, etc.)

## 📝 Notes importantes

### Pour les développeurs

- **Ne jamais hardcoder les tokens** dans le code
- **Toujours utiliser** `get_user_oura_token()` pour récupérer les tokens
- **Ne jamais logger** les tokens en clair
- **Tester** avec `test_oura_token_migration.py` après modification

### Pour les utilisateurs

- Le token Oura est un **Personal Access Token** obtenu depuis [Oura Cloud](https://cloud.ouraring.com/)
- Le token est stocké de manière **sécurisée** dans Supabase
- La déconnexion ne supprime **pas les données** déjà synchronisées
- La synchronisation peut être **manuelle** ou **automatique**

## 🐛 Dépannage

### Erreur: "No Oura token found for user"
→ L'utilisateur n'a pas encore connecté son compte Oura  
→ Appeler `/api/oura/connect` avec un token valide

### Erreur: "Failed to connect Oura account"
→ Le token Oura est invalide ou expiré  
→ Générer un nouveau token depuis Oura Cloud

### Erreur: "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
→ Variables d'environnement manquantes  
→ Vérifier le fichier `.env`

## 📞 Support

Pour toute question ou problème:
1. Consulter `OURA_TOKEN_MIGRATION_COMPLETE.md`
2. Consulter `backend/OURA_API_ENDPOINTS.md`
3. Exécuter `test_oura_token_migration.py`
4. Vérifier les logs du backend

---

**Date de migration**: 4 février 2026  
**Auteur**: Assistant IA  
**Statut**: ✅ TERMINÉ ET DOCUMENTÉ
