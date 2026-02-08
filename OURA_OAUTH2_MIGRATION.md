# Migration Oura vers OAuth2 ✅

## 🎯 Objectif

Passer de l'authentification par Personal Access Token (PAT) à OAuth2 pour une meilleure expérience utilisateur et une gestion automatique des tokens.

## ✅ Travail effectué

### 1. Configuration des credentials OAuth2

**Variables d'environnement ajoutées** (dans `backend/.env`):

```bash
# Oura OAuth2 Configuration
OURA_CLIENT_ID=d0bf5c0a-f150-4112-adbd-408fecde8ad4
OURA_CLIENT_SECRET=ROMfYYnIXn3Vq1GckwsXkp-A2LSm4Rt85ADG-uZ4pxE
OURA_REDIRECT_URI=http://localhost:8000/api/oura/oauth/callback
```

### 2. Service OAuth2 créé

**Fichier**: `backend/oura_oauth2_service.py`

Fonctionnalités:
- ✅ Génération de l'URL d'autorisation
- ✅ Échange du code contre access_token + refresh_token
- ✅ Rafraîchissement automatique des tokens expirés
- ✅ Stockage sécurisé dans Supabase
- ✅ Révocation des tokens

### 3. Nouveaux endpoints API

**Fichier**: `backend/api_server.py`

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/oura/oauth/authorize` | GET | Génère l'URL d'autorisation OAuth2 |
| `/api/oura/oauth/callback` | GET | Callback après autorisation Oura |
| `/api/oura/oauth/complete` | POST | Complète le flux et stocke les tokens |

### 4. Mise à jour des utilitaires

**Fichier**: `backend/oura_token_utils.py`

- ✅ Support des deux méthodes (PAT et OAuth2)
- ✅ Rafraîchissement automatique des tokens OAuth2
- ✅ Détection de l'expiration (5 min avant)
- ✅ Backward compatible avec les PAT existants

### 5. Structure Supabase

Les tokens OAuth2 sont stockés dans `external_identities.metadata`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def50200a1b2c3d4e5f6...",
  "expires_at": "2026-02-05T12:00:00Z",
  "token_type": "Bearer",
  "auth_method": "oauth2"  // "pat" ou "oauth2"
}
```

## 🔄 Flux OAuth2

### Flux complet

```
1. App mobile appelle GET /api/oura/oauth/authorize
   ↓
2. Backend génère l'URL d'autorisation Oura
   ↓
3. App mobile ouvre l'URL dans un navigateur
   ↓
4. Utilisateur autorise l'accès sur Oura Cloud
   ↓
5. Oura redirige vers /api/oura/oauth/callback?code=xxx
   ↓
6. App mobile récupère le code depuis l'URL
   ↓
7. App mobile appelle POST /api/oura/oauth/complete avec le code
   ↓
8. Backend échange le code contre access_token + refresh_token
   ↓
9. Backend stocke les tokens dans Supabase
   ↓
10. Tokens rafraîchis automatiquement avant expiration
```

## 📱 Intégration mobile

### 1. Démarrer le flux OAuth2

```typescript
import * as WebBrowser from 'expo-web-browser';

const connectOuraOAuth2 = async () => {
  // 1. Obtenir l'URL d'autorisation
  const response = await fetch('/api/oura/oauth/authorize', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const { auth_url, state } = await response.json();
  
  // 2. Ouvrir le navigateur
  const result = await WebBrowser.openAuthSessionAsync(
    auth_url,
    'pulse://oura/callback'  // Deep link de votre app
  );
  
  if (result.type === 'success') {
    // 3. Extraire le code depuis l'URL
    const url = new URL(result.url);
    const code = url.searchParams.get('code');
    
    if (code) {
      // 4. Compléter le flux
      await fetch('/api/oura/oauth/complete', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
      });
      
      Alert.alert('Succès', 'Compte Oura connecté !');
    }
  }
};
```

### 2. Configuration du deep link

**Fichier**: `app.json`

```json
{
  "expo": {
    "scheme": "pulse",
    "ios": {
      "bundleIdentifier": "com.pulse.app"
    },
    "android": {
      "package": "com.pulse.app"
    }
  }
}
```

## 🔐 Sécurité

### Tokens stockés

- ✅ `access_token` : Token d'accès (expire après ~24h)
- ✅ `refresh_token` : Token de rafraîchissement (longue durée)
- ✅ `expires_at` : Date d'expiration ISO 8601
- ✅ `auth_method` : Méthode d'authentification ("oauth2" ou "pat")

### Rafraîchissement automatique

Le système rafraîchit automatiquement les tokens:
- ⏰ 5 minutes avant l'expiration
- 🔄 Lors de chaque appel à `get_user_oura_token()`
- 💾 Nouveaux tokens stockés immédiatement

### Backward compatibility

- ✅ Les PAT existants continuent de fonctionner
- ✅ Détection automatique de la méthode (PAT vs OAuth2)
- ✅ Migration progressive possible

## 🧪 Tests

### Test manuel du flux OAuth2

```bash
# 1. Obtenir l'URL d'autorisation
curl -X GET "http://localhost:8000/api/oura/oauth/authorize" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 2. Ouvrir l'URL dans un navigateur et autoriser

# 3. Copier le code depuis l'URL de callback

# 4. Compléter le flux
curl -X POST "http://localhost:8000/api/oura/oauth/complete" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "authorization_code_here"}'
```

### Vérifier le token dans Supabase

```sql
SELECT 
  supabase_user_id,
  external_user_id,
  metadata->>'auth_method' as auth_method,
  metadata->>'expires_at' as expires_at,
  is_active
FROM external_identities
WHERE provider_system = 'oura';
```

## 📊 Comparaison PAT vs OAuth2

| Critère | Personal Access Token | OAuth2 |
|---------|----------------------|--------|
| **Configuration** | Simple | Complexe |
| **UX utilisateur** | Copier/coller manuel | Flux automatique |
| **Expiration** | Jamais (sauf révocation) | 24h (rafraîchi auto) |
| **Révocation** | Manuel sur Oura Cloud | Automatique |
| **Sécurité** | Bonne | Excellente |
| **Maintenance** | Aucune | Gestion refresh |

## 🚀 Migration des utilisateurs existants

### Option 1: Migration automatique (recommandé)

Les utilisateurs avec PAT continuent de fonctionner normalement. Lors de la prochaine connexion, proposer de migrer vers OAuth2.

### Option 2: Migration forcée

Envoyer une notification pour reconnecter via OAuth2:

```typescript
// Vérifier si l'utilisateur utilise un PAT
const status = await fetch('/api/oura/status', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await status.json();
const authMethod = data.auth_method;  // "pat" ou "oauth2"

if (authMethod === 'pat') {
  // Afficher un message pour migrer vers OAuth2
  Alert.alert(
    'Mise à jour disponible',
    'Reconnectez votre compte Oura pour une meilleure expérience',
    [
      { text: 'Plus tard', style: 'cancel' },
      { text: 'Reconnecter', onPress: () => connectOuraOAuth2() }
    ]
  );
}
```

## 🔧 Configuration Oura Developer Portal

### 1. Créer une application OAuth2

1. Aller sur [Oura Developer Portal](https://cloud.ouraring.com/oauth/applications)
2. Créer une nouvelle application
3. Configurer les redirect URIs:
   - `http://localhost:8000/api/oura/oauth/callback` (dev)
   - `https://api.pulse.com/api/oura/oauth/callback` (prod)
   - `pulse://oura/callback` (mobile deep link)

### 2. Scopes nécessaires

- `daily` : Données quotidiennes (readiness, sleep, activity)
- `personal` : Informations personnelles
- `email` : Email de l'utilisateur

## 📝 Notes importantes

### Expiration des tokens

- **Access token** : Expire après 24 heures
- **Refresh token** : Valide pendant 30 jours (renouvelé à chaque refresh)
- **Rafraîchissement** : Automatique 5 min avant expiration

### Erreurs courantes

#### "Invalid redirect_uri"
→ Vérifier que l'URL de callback est enregistrée dans Oura Developer Portal

#### "Invalid client credentials"
→ Vérifier `OURA_CLIENT_ID` et `OURA_CLIENT_SECRET` dans `.env`

#### "Token expired"
→ Le refresh token a expiré, l'utilisateur doit se reconnecter

## 🎯 Prochaines étapes

1. ✅ OAuth2 implémenté côté backend
2. ⏳ Implémenter l'UI mobile pour OAuth2
3. ⏳ Tester le flux complet
4. ⏳ Migrer les utilisateurs existants
5. ⏳ Monitoring des erreurs de refresh
6. ⏳ Déployer en production

## 📚 Ressources

- [Oura OAuth2 Documentation](https://cloud.ouraring.com/docs/authentication)
- [Expo WebBrowser](https://docs.expo.dev/versions/latest/sdk/webbrowser/)
- [Expo AuthSession](https://docs.expo.dev/versions/latest/sdk/auth-session/)

---

**Date de migration**: 4 février 2026  
**Statut**: ✅ BACKEND TERMINÉ - UI MOBILE À IMPLÉMENTER
