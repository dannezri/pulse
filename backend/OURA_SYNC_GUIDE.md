# Guide de synchronisation Oura par utilisateur

## 📋 Vue d'ensemble

Les scripts ont été modifiés pour permettre de :
- Passer l'ID utilisateur Supabase en paramètre
- Passer les credentials OAuth2 Oura (client_id et client_secret) en paramètre
- Stocker ces credentials par utilisateur dans Supabase

## 🚀 Scripts disponibles

### 1. `add_user_oura_credentials.py`
**Objectif** : Ajouter/mettre à jour les credentials OAuth2 Oura pour un utilisateur spécifique dans Supabase.

**Usage** :
```bash
cd /Users/dannezri/Desktop/Pulse/backend

python3 add_user_oura_credentials.py \
  --user-id UUID_UTILISATEUR \
  --client-id CLIENT_ID_OURA \
  --client-secret CLIENT_SECRET_OURA
```

**Exemple** :
```bash
python3 add_user_oura_credentials.py \
  --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \
  --client-id e7bb46a6-015d-4ffa-ad83-58ed64487655 \
  --client-secret ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU
```

**Ce que ça fait** :
- Vérifie que l'utilisateur existe dans `profiles`
- Crée ou met à jour une entrée dans `external_identities` pour Oura
- Stocke les credentials OAuth2 dans `metadata`
- Préserve les tokens existants (access_token, refresh_token) s'ils existent

---

### 2. `run_oura_sync.py`
**Objectif** : Synchroniser les données Oura pour un utilisateur spécifique.

**Usage** :
```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Option 1: Utiliser les credentials du .env (par défaut)
python3 run_oura_sync.py --user-id UUID_UTILISATEUR

# Option 2: Fournir les credentials Oura en paramètre
python3 run_oura_sync.py \
  --user-id UUID_UTILISATEUR \
  --oura-client-id CLIENT_ID \
  --oura-client-secret CLIENT_SECRET
```

**Exemples** :

```bash
# Sync pour l'utilisateur par défaut (c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd)
python3 run_oura_sync.py

# Sync pour un utilisateur spécifique
python3 run_oura_sync.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1

# Sync avec credentials Oura personnalisées
python3 run_oura_sync.py \
  --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \
  --oura-client-id e7bb46a6-015d-4ffa-ad83-58ed64487655 \
  --oura-client-secret ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU
```

**Ce que ça fait** :
- Charge les variables d'environnement depuis `.env`
- Surcharge `OURA_CLIENT_ID` et `OURA_CLIENT_SECRET` si fournis en paramètre
- Appelle `import_oura_data_full.py` avec l'user_id
- Récupère le token Oura depuis `external_identities.metadata`
- Synchronise toutes les données Oura (sommeil, activité, readiness, etc.)

---

## 📊 Structure des données dans Supabase

### Table `external_identities`

Les credentials OAuth2 Oura sont stockés dans la table `external_identities` :

```json
{
  "supabase_user_id": "bee9a055-9b10-47d7-b91d-d7f6081a63f1",
  "provider_system": "oura",
  "external_user_id": "oura_user_bee9a055",
  "metadata": {
    "oauth2_client_id": "e7bb46a6-015d-4ffa-ad83-58ed64487655",
    "oauth2_client_secret": "ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU",
    "configured_at": "2026-02-04T12:00:00Z",
    "note": "Credentials OAuth2 spécifiques à cet utilisateur",
    
    // Tokens OAuth2 (ajoutés après le flux OAuth2)
    "access_token": "eyJhbGci...",
    "refresh_token": "def502...",
    "expires_at": "2026-02-05T12:00:00Z",
    "auth_method": "oauth2"
  },
  "is_active": true
}
```

---

## 🔄 Workflow complet

### Pour un nouvel utilisateur avec ses propres credentials Oura

1. **Ajouter les credentials Oura dans Supabase** :
   ```bash
   python3 add_user_oura_credentials.py \
     --user-id UUID_UTILISATEUR \
     --client-id CLIENT_ID_OURA \
     --client-secret CLIENT_SECRET_OURA
   ```

2. **L'utilisateur doit compléter le flux OAuth2** :
   - Via l'app mobile : Paramètres → Connecter Oura
   - Ou via API : GET `/api/oura/oauth/authorize`

3. **Synchroniser les données** :
   ```bash
   python3 run_oura_sync.py --user-id UUID_UTILISATEUR
   ```

### Pour utiliser les credentials globales (dans `.env`)

1. **Les credentials sont déjà dans `.env`** :
   ```bash
   OURA_CLIENT_ID=e7bb46a6-015d-4ffa-ad83-58ed64487655
   OURA_CLIENT_SECRET=ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU
   ```

2. **Synchroniser directement** :
   ```bash
   python3 run_oura_sync.py --user-id UUID_UTILISATEUR
   ```

---

## 📝 Notes importantes

### Différence entre Client Credentials et Access Tokens

- **Client ID + Client Secret** : Credentials de l'**application Oura** (configurés dans Oura Cloud Dashboard)
  - Permettent d'initier le flux OAuth2
  - Peuvent être partagées entre tous les utilisateurs (mode .env)
  - Ou être spécifiques à chaque utilisateur (mode Supabase)

- **Access Token + Refresh Token** : Tokens OAuth2 de l'**utilisateur**
  - Obtenus après le flux OAuth2
  - Uniques par utilisateur
  - Permettent d'accéder aux données Oura de l'utilisateur
  - Stockés dans `external_identities.metadata`

### Ordre de priorité des credentials

Quand vous lancez `run_oura_sync.py` :

1. **Paramètres en ligne de commande** (`--oura-client-id`, `--oura-client-secret`)
2. **Variables d'environnement** (`.env` : `OURA_CLIENT_ID`, `OURA_CLIENT_SECRET`)
3. **Erreur** si aucune credential n'est trouvée

---

## 🎯 Cas d'usage

### Cas 1 : Une seule application Oura pour tous les utilisateurs
Utilisez les credentials dans `.env` (déjà configurées) :
```bash
python3 run_oura_sync.py --user-id UUID_UTILISATEUR
```

### Cas 2 : Chaque utilisateur a sa propre application Oura
Ajoutez les credentials par utilisateur :
```bash
python3 add_user_oura_credentials.py \
  --user-id UUID_UTILISATEUR \
  --client-id CLIENT_ID_SPECIFIQUE \
  --client-secret CLIENT_SECRET_SPECIFIQUE

python3 run_oura_sync.py --user-id UUID_UTILISATEUR
```

### Cas 3 : Test ponctuel avec des credentials temporaires
Passez les credentials en paramètre sans les stocker :
```bash
python3 run_oura_sync.py \
  --user-id UUID_UTILISATEUR \
  --oura-client-id CLIENT_ID_TEST \
  --oura-client-secret CLIENT_SECRET_TEST
```

---

## ✅ Résumé

| Action | Commande |
|--------|----------|
| Ajouter credentials Oura pour un utilisateur | `python3 add_user_oura_credentials.py --user-id UUID --client-id ID --client-secret SECRET` |
| Sync avec credentials du .env | `python3 run_oura_sync.py --user-id UUID` |
| Sync avec credentials en paramètre | `python3 run_oura_sync.py --user-id UUID --oura-client-id ID --oura-client-secret SECRET` |
| Lister les utilisateurs | `python3 add_user.py --list` |

---

## 📞 Support

En cas de problème :
1. Vérifiez que l'utilisateur existe : `python3 add_user.py --list`
2. Vérifiez les credentials dans Supabase : table `external_identities` où `provider_system = 'oura'`
3. Vérifiez les logs de synchronisation
4. Vérifiez que le token OAuth2 est valide (pas expiré)
