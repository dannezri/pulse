# FatSecret - Flow d'intégration correct (basé sur la documentation officielle)

## 📚 Deux cas d'usage distincts

### Cas 1: Créer un nouveau profil FatSecret (vide)
**Méthode:** `profile.create`  
**Usage:** Si vous voulez que l'utilisateur enregistre ses données via VOTRE app

```python
profile = client.create_profile(user_id="your_user_123")
# → Retourne auth_token + auth_secret
# → L'utilisateur peut maintenant enregistrer des repas via votre app
```

### Cas 2: Connecter un compte FatSecret existant (avec données)
**Méthode:** OAuth 3-legged authorization flow  
**Usage:** Si l'utilisateur a déjà un compte FatSecret avec des données

**C'est ce qu'on veut pour récupérer les repas !**

## 🔄 Flow OAuth correct (pour récupérer les données existantes)

### Étape 1: Request Token
```python
params = {
    "method": "profile.request_token",
    "format": "json"
}
response = client._make_oauth1_request(params)
# → Retourne request_token + request_secret
```

### Étape 2: Authorize (user opens URL)
```
URL: https://www.fatsecret.com/oauth/authorize?oauth_token=<request_token>
```
L'utilisateur se connecte et autorise → reçoit un verifier code

### Étape 3: Get Access Token
```python
params = {
    "method": "profile.get_auth",
    "oauth_token": request_token,
    "oauth_verifier": verifier_code,
    "format": "json"
}
response = client._make_oauth1_request(params)
# → Retourne auth_token + auth_secret (liés au compte utilisateur)
```

### Étape 4: Utiliser les credentials
```python
client = FatSecretClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    oauth_token=auth_token,  # Du step 3
    oauth_secret=auth_secret  # Du step 3
)

# Maintenant on peut récupérer les vraies données
entries = client.get_food_entries_for_date(today)
```

## 🎯 Implémentation pour Pulse

Pour notre MVP, on a besoin du **flow OAuth 3-legged** complet :

1. **Backend:** Implémenter `profile.request_token` 
2. **App Mobile:** Ouvrir l'URL d'autorisation
3. **Backend:** Échanger le verifier contre auth_token/auth_secret
4. **Backend:** Stocker auth_token + auth_secret dans Supabase
5. **Backend:** Utiliser ces credentials pour sync les food entries

## 📝 Note importante

La documentation FatSecret indique deux endpoints différents pour `profile.get_auth` :

1. **Après autorisation** (avec verifier) :
   - Utilise le request_token + verifier
   - Retourne les credentials du compte autorisé

2. **Pour récupérer** (avec user_id) :
   - Utilise le user_id
   - Retourne les credentials d'un profil existant

Notre cas = Méthode 1 (après autorisation)

