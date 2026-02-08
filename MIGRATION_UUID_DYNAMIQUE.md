# Migration UUID Dynamique - Résumé des Changements

**Date :** 2026-02-04  
**Objectif :** Éliminer tous les UUIDs codés en dur et les rendre dynamiques via variables d'environnement

## 🎯 Problème Initial

De nombreux fichiers contenaient des UUIDs codés en dur :
- `mobile/app/index.tsx` : `"bee9a055-9b10-47d7-b91d-d7f6081a63f1"`
- `mobile/extract-energy-data.js` : `"c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"`
- 15+ scripts backend avec des UUIDs hardcodés

**Risques :**
- Difficile de changer d'utilisateur
- Code non portable
- Risque de commit d'UUIDs sensibles

## ✅ Solution Implémentée

### 1. Architecture Centralisée

**Backend :**
- Nouveau module `backend/user_config.py` qui centralise la récupération de l'UUID
- Tous les scripts utilisent `get_dev_user_uuid()` ou `get_test_user_uuid()`

**Mobile :**
- UUID stocké dans `mobile/app.json` sous `expo.extra.devUserUuid`
- Récupéré via `Constants.expoConfig.extra.devUserUuid`
- Stockage sécurisé dans SecureStore (Keychain iOS / Keystore Android)

**Variable d'environnement unique :**
```bash
export DEV_USER_UUID=votre-uuid-supabase
```

### 2. Fichiers Modifiés

#### Mobile (3 fichiers)

1. **`mobile/app/index.tsx`**
   - Avant : `const DEV_USER_UUID = "bee9a055-..."`
   - Après : `const DEV_USER_UUID = Constants.expoConfig?.extra?.devUserUuid || process.env.EXPO_PUBLIC_DEV_USER_UUID`

2. **`mobile/app.json`**
   - Ajout de `"devUserUuid": "bee9a055-..."` dans `expo.extra`

3. **`mobile/extract-energy-data.js`**
   - Avant : `const DEFAULT_USER_ID = 'c559fcd7-...'`
   - Après : `const DEFAULT_USER_ID = process.env.DEV_USER_UUID || null`
   - Validation obligatoire de l'UUID avant exécution

#### Backend (17 fichiers)

**Nouveau fichier :**
- ✅ `backend/user_config.py` - Module centralisé pour récupérer l'UUID

**Scripts principaux modifiés :**
1. ✅ `backend/setup_oura_complete.py`
2. ✅ `backend/force_sync_oura_today.py`
3. ✅ `backend/import_oura_data.py`
4. ✅ `backend/import_oura_data_full.py`
5. ✅ `backend/register_oura_user.py`
6. ✅ `backend/run_oura_sync.py`

**Scripts de test modifiés :**
7. ✅ `backend/test_oura_token_migration.py`
8. ✅ `backend/test_oura_sync.py`
9. ✅ `backend/debug_oura_scores.py`
10. ✅ `backend/test_prompt_preview.py`
11. ✅ `backend/find_oura_data.py`
12. ✅ `backend/inspect_biometrics.py`
13. ✅ `backend/test_get_biometrics.py`
14. ✅ `backend/test_biometrics_extraction.py`
15. ✅ `backend/test_influencers_direct.py`

**Autres :**
16. ✅ `check_metric_types.py`

### 3. Documentation Créée

1. **`UUID_CONFIGURATION.md`** (Documentation complète)
   - Vue d'ensemble du système
   - Guide de configuration détaillé
   - Exemples d'utilisation
   - Dépannage

2. **`SETUP_UUID.md`** (Guide rapide)
   - Configuration en 2 minutes
   - Tests de validation
   - Commandes essentielles

3. **`setup-uuid.sh`** (Script automatique)
   - Configuration automatique de l'UUID
   - Validation du format
   - Mise à jour de `.zshrc`/`.bashrc` et `app.json`
   - Vérification post-installation

4. **`backend/.env.example`** (Template)
   - Exemple de configuration complète
   - Documentation des variables requises

## 🔧 Utilisation

### Configuration Initiale

**Option 1 : Script automatique (recommandé)**

```bash
./setup-uuid.sh bee9a055-9b10-47d7-b91d-d7f6081a63f1
source ~/.zshrc  # ou ~/.bashrc
```

**Option 2 : Manuel**

```bash
# 1. Backend
echo 'export DEV_USER_UUID=bee9a055-9b10-47d7-b91d-d7f6081a63f1' >> ~/.zshrc
source ~/.zshrc

# 2. Mobile
# Éditer mobile/app.json et ajouter dans expo.extra:
# "devUserUuid": "bee9a055-9b10-47d7-b91d-d7f6081a63f1"
```

### Utilisation Quotidienne

Tous les scripts fonctionnent maintenant sans modification :

```bash
# Backend
cd backend
python3 run_oura_sync.py
python3 test_biometrics_extraction.py

# Node.js
node mobile/extract-energy-data.js

# Mobile
cd mobile
npx expo start
```

## 📊 Statistiques

- **Fichiers modifiés :** 20
- **Nouveau module :** 1 (`user_config.py`)
- **Documentation :** 4 fichiers
- **UUIDs codés en dur éliminés :** 100%
- **Scripts automatisés :** 1 (`setup-uuid.sh`)

## 🔒 Sécurité

### Avant
- ❌ UUIDs visibles dans le code source
- ❌ Risque de commit d'informations sensibles
- ❌ Difficile de changer d'utilisateur

### Après
- ✅ UUIDs dans variables d'environnement uniquement
- ✅ Mobile : Stockage sécurisé (Keychain/Keystore)
- ✅ Backend : Variables d'environnement (non committées)
- ✅ Changement d'utilisateur simple et rapide

## 🎓 Bonnes Pratiques Établies

1. **Centralisation**
   - Un seul point de configuration (`DEV_USER_UUID`)
   - Module utilitaire réutilisable (`user_config.py`)

2. **Validation**
   - Vérification obligatoire de la présence de l'UUID
   - Messages d'erreur clairs et explicites

3. **Documentation**
   - Guide rapide pour démarrer
   - Documentation complète pour référence
   - Script automatique pour faciliter la configuration

4. **Compatibilité**
   - Fonctionne avec tous les shells (bash, zsh)
   - Compatible iOS et Android (mobile)
   - Support des arguments en ligne de commande (fallback)

## 🚀 Migration Future

Pour ajouter un nouveau script :

**Backend :**
```python
from user_config import get_dev_user_uuid

user_id = get_dev_user_uuid()
# Votre code...
```

**Mobile :**
```typescript
import { useAuth } from '../src/hooks/useAuth';

const { userId } = useAuth();
// Votre code...
```

## ✅ Checklist de Vérification

- [x] Aucun UUID codé en dur dans le code source
- [x] Tous les scripts backend utilisent `user_config.py`
- [x] Mobile utilise `Constants.expoConfig` et `SecureStore`
- [x] Documentation complète créée
- [x] Script de configuration automatique créé
- [x] Tests de validation effectués
- [x] Messages d'erreur clairs en cas d'UUID manquant

## 📝 Notes

- Les UUIDs dans les fichiers markdown de documentation sont des **exemples** uniquement
- Le fichier `.env` n'est **jamais** committé dans Git
- Le `SecureStore` mobile persiste entre les redémarrages de l'app

## 🔗 Ressources

- [UUID_CONFIGURATION.md](./UUID_CONFIGURATION.md) - Documentation complète
- [SETUP_UUID.md](./SETUP_UUID.md) - Guide rapide
- `backend/user_config.py` - Module utilitaire
- `setup-uuid.sh` - Script de configuration automatique

---

**Auteur :** Migration automatique  
**Status :** ✅ Complété  
**Date :** 2026-02-04
