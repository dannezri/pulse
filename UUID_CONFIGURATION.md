# Configuration des UUIDs Utilisateur - Pulse

## 📋 Vue d'ensemble

Tous les UUIDs utilisateur dans le projet Pulse sont maintenant **dynamiques** et configurables via des variables d'environnement. Il n'y a **plus d'UUIDs codés en dur** dans le code.

## 🎯 Principe de base

**L'UUID utilisateur doit être défini UNE SEULE FOIS dans les variables d'environnement**, et tous les scripts et l'application mobile le récupèrent dynamiquement.

## 🔧 Configuration

### 1. Mobile (Expo/React Native)

L'UUID est configuré dans `mobile/app.json` :

```json
{
  "expo": {
    "extra": {
      "devUserUuid": "votre-uuid-supabase"
    }
  }
}
```

**Ou** via variable d'environnement (prioritaire) :

```bash
export EXPO_PUBLIC_DEV_USER_UUID=votre-uuid-supabase
```

L'application mobile :
- Stocke l'UUID dans le **SecureStore** (iOS Keychain / Android Keystore)
- Le récupère via `storage.getUserId()`
- Tous les hooks utilisent `useAuth()` qui récupère l'UUID depuis le storage

**Fichiers concernés :**
- `mobile/app/index.tsx` - Point d'entrée, auto-login avec UUID
- `mobile/src/lib/storage.ts` - Gestion du SecureStore
- `mobile/src/hooks/useAuth.ts` - Hook pour récupérer l'UUID

### 2. Backend (Python)

Tous les scripts backend utilisent la variable d'environnement `DEV_USER_UUID`.

**Configuration :**

```bash
# Dans backend/.env ou dans votre shell
export DEV_USER_UUID=votre-uuid-supabase
```

**Module centralisé :**

Le fichier `backend/user_config.py` fournit des fonctions utilitaires :

```python
from user_config import get_dev_user_uuid, get_test_user_uuid

# Pour les scripts de production
user_id = get_dev_user_uuid()

# Pour les scripts de test (alias)
test_user_id = get_test_user_uuid()
```

**Fichiers modifiés :**
- ✅ `backend/user_config.py` - Module centralisé (NOUVEAU)
- ✅ `backend/setup_oura_complete.py`
- ✅ `backend/force_sync_oura_today.py`
- ✅ `backend/import_oura_data.py`
- ✅ `backend/import_oura_data_full.py`
- ✅ `backend/register_oura_user.py`
- ✅ `backend/run_oura_sync.py`
- ✅ `backend/test_oura_token_migration.py`
- ✅ `backend/test_oura_sync.py`
- ✅ `backend/debug_oura_scores.py`
- ✅ `backend/test_prompt_preview.py`
- ✅ `backend/find_oura_data.py`
- ✅ `backend/inspect_biometrics.py`
- ✅ `backend/test_get_biometrics.py`
- ✅ `backend/test_biometrics_extraction.py`
- ✅ `backend/test_influencers_direct.py`
- ✅ `check_metric_types.py`

### 3. Scripts Node.js

Le script `mobile/extract-energy-data.js` utilise également la variable d'environnement :

```bash
export DEV_USER_UUID=votre-uuid-supabase
node mobile/extract-energy-data.js
```

Ou passez l'UUID en argument :

```bash
node mobile/extract-energy-data.js votre-uuid-supabase
```

## 🚀 Utilisation

### Démarrage rapide

1. **Définir votre UUID une fois :**

```bash
# Dans votre .bashrc, .zshrc ou .env
export DEV_USER_UUID=bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

2. **Mobile :**

Mettre à jour `mobile/app.json` :

```json
{
  "expo": {
    "extra": {
      "devUserUuid": "bee9a055-9b10-47d7-b91d-d7f6081a63f1"
    }
  }
}
```

Puis lancer l'app :

```bash
cd mobile
npx expo start
```

3. **Backend :**

```bash
cd backend
export DEV_USER_UUID=bee9a055-9b10-47d7-b91d-d7f6081a63f1

# Tous les scripts fonctionnent maintenant
python3 run_oura_sync.py
python3 test_biometrics_extraction.py
python3 force_sync_oura_today.py
```

### Scripts avec arguments optionnels

Certains scripts acceptent l'UUID en argument (prioritaire sur la variable d'environnement) :

```bash
# run_oura_sync.py
python3 run_oura_sync.py --user-id <uuid>

# extract-energy-data.js
node extract-energy-data.js <uuid>
```

## 🔍 Vérification

Pour vérifier que tout fonctionne :

```bash
# Backend
cd backend
python3 -c "from user_config import get_dev_user_uuid; print(get_dev_user_uuid())"

# Mobile (dans l'app)
# Vérifier les logs au démarrage :
# ✅ Utilisateur déjà connecté: <uuid>
```

## ⚠️ Important

### Ce qui est INTERDIT

❌ **Ne JAMAIS coder en dur un UUID dans le code source**

```python
# ❌ MAUVAIS
USER_ID = "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

### Ce qui est AUTORISÉ

✅ **Toujours utiliser les variables d'environnement ou le storage**

```python
# ✅ BON
from user_config import get_dev_user_uuid
USER_ID = get_dev_user_uuid()
```

```typescript
// ✅ BON (Mobile)
const { userId } = useAuth();
```

## 📝 Changement d'utilisateur

Pour changer d'utilisateur :

1. **Mobile :** Modifier `mobile/app.json` et redémarrer l'app
2. **Backend :** Changer la variable `DEV_USER_UUID` dans votre environnement
3. **Scripts :** Passer le nouvel UUID en argument

## 🔐 Sécurité

- **Mobile :** Les UUIDs sont stockés dans le SecureStore (Keychain iOS / Keystore Android)
- **Backend :** Les UUIDs sont lus depuis les variables d'environnement (jamais committés dans Git)
- **Documentation :** Les exemples d'UUIDs dans les docs sont des exemples, pas des valeurs réelles

## 📚 Ressources

- Module backend : `backend/user_config.py`
- Storage mobile : `mobile/src/lib/storage.ts`
- Hook d'authentification : `mobile/src/hooks/useAuth.ts`
- Configuration Expo : `mobile/app.json`

## 🐛 Dépannage

### Erreur "DEV_USER_UUID doit être défini"

```bash
# Solution
export DEV_USER_UUID=votre-uuid-supabase
```

### Mobile : "UUID de développement non configuré"

Vérifier que `mobile/app.json` contient :

```json
{
  "expo": {
    "extra": {
      "devUserUuid": "votre-uuid"
    }
  }
}
```

### Backend : Import error "No module named 'user_config'"

Assurez-vous d'être dans le dossier `backend/` :

```bash
cd backend
python3 votre_script.py
```

## ✅ Checklist de migration

- [x] Mobile : UUID dynamique via `app.json` et `Constants.expoConfig`
- [x] Backend : Module `user_config.py` créé
- [x] Tous les scripts backend mis à jour
- [x] Scripts Node.js mis à jour
- [x] Documentation créée
- [x] Aucun UUID codé en dur dans le code source

---

**Date de mise à jour :** 2026-02-04  
**Version :** 1.0.0
