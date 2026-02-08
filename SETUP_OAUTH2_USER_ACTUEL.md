# Configuration OAuth2 pour l'utilisateur actuel

## 📋 Informations

**User ID**: `c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd`

**Credentials OAuth2 Oura**:
- Client ID: `d0bf5c0a-f150-4112-adbd-408fecde8ad4`
- Client Secret: `ROMfYYnIXn3Vq1GckwsXkp-A2LSm4Rt85ADG-uZ4pxE`

## ⚙️ Configuration

### 1. Ajouter les credentials dans `.env`

Ajoutez ces lignes dans `/Users/dannezri/Desktop/Pulse/backend/.env`:

```bash
# Oura OAuth2 Configuration
OURA_CLIENT_ID=d0bf5c0a-f150-4112-adbd-408fecde8ad4
OURA_CLIENT_SECRET=ROMfYYnIXn3Vq1GckwsXkp-A2LSm4Rt85ADG-uZ4pxE
OURA_REDIRECT_URI=http://localhost:8000/api/oura/oauth/callback
```

### 2. Obtenir les tokens OAuth2

Vous avez deux options:

#### Option A: Via le flux OAuth2 complet (recommandé)

1. Démarrer le backend:
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python api_server.py
```

2. Obtenir l'URL d'autorisation:
```bash
# Remplacer $JWT_TOKEN par votre token JWT
curl -X GET "http://localhost:8000/api/oura/oauth/authorize" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

3. Ouvrir l'URL retournée dans un navigateur

4. Autoriser l'accès sur Oura Cloud

5. Copier le `code` depuis l'URL de callback

6. Compléter le flux:
```bash
curl -X POST "http://localhost:8000/api/oura/oauth/complete" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "VOTRE_CODE_ICI"}'
```

#### Option B: Configuration manuelle (si vous avez déjà les tokens)

Si vous avez déjà obtenu un `access_token` et un `refresh_token` depuis Oura:

```bash
cd /Users/dannezri/Desktop/Pulse/backend

python setup_oura_oauth2.py \
  --user-id c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd \
  --access-token "VOTRE_ACCESS_TOKEN" \
  --refresh-token "VOTRE_REFRESH_TOKEN" \
  --expires-in 86400
```

### 3. Vérifier la configuration

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python test_oura_token_migration.py
```

Ou vérifier dans Supabase:

```sql
SELECT 
  supabase_user_id,
  external_user_id,
  metadata->>'auth_method' as auth_method,
  metadata->>'expires_at' as expires_at,
  is_active
FROM external_identities
WHERE supabase_user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND provider_system = 'oura';
```

## 🧪 Tester OAuth2

### Test 1: Synchronisation avec OAuth2

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python test_oura_sync.py
```

Le script devrait:
- ✅ Récupérer le token OAuth2 depuis Supabase
- ✅ Synchroniser les données Oura
- ✅ Afficher les métriques (readiness, sleep, HRV, etc.)

### Test 2: Rafraîchissement automatique

Pour tester le rafraîchissement automatique, vous pouvez:

1. Modifier manuellement `expires_at` dans Supabase pour simuler l'expiration:

```sql
UPDATE external_identities
SET metadata = jsonb_set(
  metadata,
  '{expires_at}',
  to_jsonb(NOW() - INTERVAL '1 hour')
)
WHERE supabase_user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND provider_system = 'oura';
```

2. Relancer la synchronisation:

```bash
python test_oura_sync.py
```

Le système devrait automatiquement rafraîchir le token.

## 🔄 Migration depuis PAT

Si vous utilisez actuellement un Personal Access Token, voici comment migrer:

### Vérifier la méthode actuelle

```sql
SELECT 
  metadata->>'auth_method' as current_method
FROM external_identities
WHERE supabase_user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND provider_system = 'oura';
```

Si `current_method` est `null` ou `'pat'`, vous utilisez un PAT.

### Migrer vers OAuth2

1. Suivre les étapes de configuration ci-dessus (Option A ou B)

2. Le système détectera automatiquement que vous utilisez OAuth2

3. L'ancien PAT sera remplacé par les tokens OAuth2

## 📱 Utilisation dans l'app mobile

Une fois OAuth2 configuré, l'app mobile pourra:

1. **Vérifier le statut**:
```typescript
const response = await fetch('/api/oura/status', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();
console.log('Auth method:', data.auth_method); // "oauth2"
```

2. **Synchroniser les données**:
```typescript
const response = await fetch('/api/oura/sync', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

Les tokens seront automatiquement rafraîchis en arrière-plan.

## 🐛 Dépannage

### Erreur: "OURA_CLIENT_ID or OURA_CLIENT_SECRET not set"

→ Vérifier que les variables sont bien dans `.env` et redémarrer le backend

### Erreur: "Invalid client credentials"

→ Vérifier que le Client ID et Client Secret sont corrects

### Erreur: "Token expired"

→ Le refresh token a expiré, refaire le flux OAuth2 complet

### Erreur: "No Oura token found for user"

→ Vous n'avez pas encore configuré OAuth2, suivre les étapes ci-dessus

## ✅ Checklist

- [ ] Credentials ajoutés dans `.env`
- [ ] Backend redémarré
- [ ] Flux OAuth2 complété (Option A ou B)
- [ ] Vérification dans Supabase OK
- [ ] Test de synchronisation OK
- [ ] Test de rafraîchissement OK

## 📚 Documentation

- `OURA_OAUTH2_MIGRATION.md` - Documentation complète OAuth2
- `backend/OURA_API_ENDPOINTS.md` - Documentation des endpoints
- `backend/oura_oauth2_service.py` - Code du service OAuth2

---

**Date**: 4 février 2026  
**User**: c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
