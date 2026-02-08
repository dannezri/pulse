# Fix rapide : Erreur 401 Unauthorized Oura

## 🔴 **Problème**

```
ERROR: 401 Client Error: Unauthorized for url: https://api.ouraring.com/v2/...
❌ Aucun token Oura valide trouvé pour l'utilisateur
```

## 💡 **Cause**

L'utilisateur a les **credentials OAuth2** (client_id et client_secret) mais **pas d'access_token** valide pour accéder aux données Oura.

---

## ✅ **Solution 1 : Personal Access Token (PAT) - Le plus simple**

### Étape 1 : Obtenir un PAT depuis Oura Cloud

1. Allez sur [Oura Cloud](https://cloud.ouraring.com/)
2. Connectez-vous avec le compte Oura de l'utilisateur
3. Allez dans **Settings** → **Personal Access Tokens**
4. Créez un nouveau token avec tous les scopes
5. Copiez le token (format: `AAAABBBBCCCCDDDD...`)

### Étape 2 : Ajouter le PAT dans Pulse

```bash
cd /Users/dannezri/Desktop/Pulse/backend

python3 add_oura_pat_token.py \
  --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \
  --pat-token "VOTRE_TOKEN_PAT_ICI"
```

### Étape 3 : Synchroniser

```bash
python3 run_oura_sync.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

**✅ Avantages** :
- Simple et rapide
- Le token ne expire jamais
- Parfait pour les tests

**❌ Inconvénients** :
- Nécessite d'avoir accès au compte Oura Cloud de l'utilisateur
- Moins sécurisé qu'OAuth2

---

## ✅ **Solution 2 : Flux OAuth2 complet - Plus sécurisé**

### Prérequis

Les credentials OAuth2 sont déjà configurées :
- ✓ Client ID: `e7bb46a6-015d-4ffa-ad83-58ed64487655`
- ✓ Client Secret: `ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU`

### Option A : Via l'app mobile (recommandé)

1. Ouvrir l'app Pulse mobile
2. Aller dans **Paramètres** → **Connecter Oura**
3. Se connecter avec le compte Oura
4. Autoriser l'accès

### Option B : Via le backend (pour tests)

1. **Démarrer le backend** :
   ```bash
   cd /Users/dannezri/Desktop/Pulse/backend
   python3 api_server.py
   ```

2. **Obtenir l'URL d'autorisation** :
   ```bash
   # Obtenir d'abord un JWT token pour l'utilisateur
   python3 get_jwt_token.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
   
   # Utiliser le JWT pour obtenir l'URL OAuth2
   curl -X GET "http://localhost:8000/api/oura/oauth/authorize" \
     -H "Authorization: Bearer VOTRE_JWT_TOKEN"
   ```

3. **Ouvrir l'URL dans un navigateur** et autoriser l'accès

4. **Copier le code** depuis l'URL de callback (ex: `?code=XXXXXXX`)

5. **Compléter le flux** :
   ```bash
   curl -X POST "http://localhost:8000/api/oura/oauth/complete" \
     -H "Authorization: Bearer VOTRE_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"code": "CODE_COPIE_ICI"}'
   ```

6. **Synchroniser** :
   ```bash
   python3 run_oura_sync.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
   ```

**✅ Avantages** :
- Plus sécurisé
- Tokens rafraîchis automatiquement
- L'utilisateur garde le contrôle

**❌ Inconvénients** :
- Plus complexe à configurer
- Nécessite que le backend soit en ligne

---

## 🔍 **Vérifier l'état actuel**

Pour voir ce qui est actuellement stocké pour l'utilisateur :

```sql
SELECT 
  supabase_user_id,
  provider_system,
  metadata->>'auth_method' as auth_method,
  CASE 
    WHEN metadata->>'access_token' IS NOT NULL THEN 'OUI'
    ELSE 'NON'
  END as has_access_token,
  is_active
FROM external_identities
WHERE supabase_user_id = 'bee9a055-9b10-47d7-b91d-d7f6081a63f1'
  AND provider_system = 'oura';
```

---

## 📝 **Résumé rapide**

| Situation | Solution |
|-----------|----------|
| Je veux tester rapidement | **Solution 1 : PAT** |
| Production / utilisateur final | **Solution 2 : OAuth2** |
| Pas d'accès au compte Oura | **Solution 2 : OAuth2** (via app mobile) |
| Développement / debug | **Solution 1 : PAT** |

---

## 🎯 **Action recommandée pour Alyson**

```bash
# 1. Obtenir un PAT depuis https://cloud.ouraring.com/
# 2. Ajouter le PAT
cd /Users/dannezri/Desktop/Pulse/backend
python3 add_oura_pat_token.py \
  --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \
  --pat-token "VOTRE_TOKEN_PAT"

# 3. Synchroniser
python3 run_oura_sync.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

✅ **Cela devrait résoudre l'erreur 401 !**
