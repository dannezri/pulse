# Configuration UUID - Guide Rapide

## 🎯 Objectif

Configurer votre UUID utilisateur une seule fois pour que tous les scripts et l'application mobile l'utilisent automatiquement.

## ⚡ Configuration Rapide (2 minutes)

### 1. Récupérer votre UUID Supabase

Connectez-vous à votre dashboard Supabase et récupérez votre UUID utilisateur depuis la table `users` ou `profiles`.

**Exemple d'UUID :** `bee9a055-9b10-47d7-b91d-d7f6081a63f1`

### 2. Configuration Backend

Ajoutez cette ligne à votre fichier `~/.bashrc`, `~/.zshrc` ou `~/.bash_profile` :

```bash
export DEV_USER_UUID=bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

Puis rechargez votre configuration :

```bash
source ~/.zshrc  # ou ~/.bashrc selon votre shell
```

**Vérification :**

```bash
echo $DEV_USER_UUID
# Doit afficher votre UUID
```

### 3. Configuration Mobile

Éditez le fichier `mobile/app.json` :

```json
{
  "expo": {
    "extra": {
      "devUserUuid": "bee9a055-9b10-47d7-b91d-d7f6081a63f1"
    }
  }
}
```

**Redémarrez l'application mobile après modification.**

## ✅ Test

### Backend

```bash
cd backend
python3 -c "from user_config import get_dev_user_uuid; print(f'UUID: {get_dev_user_uuid()}')"
```

### Mobile

Lancez l'app et vérifiez les logs au démarrage :

```
✅ Utilisateur déjà connecté: bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

## 📝 Utilisation

Une fois configuré, tous les scripts fonctionnent automatiquement :

```bash
# Backend
python3 run_oura_sync.py
python3 test_biometrics_extraction.py
python3 force_sync_oura_today.py

# Node.js
node mobile/extract-energy-data.js
```

## 🔄 Changer d'utilisateur

Pour tester avec un autre utilisateur :

**Option 1 : Temporaire (une session)**

```bash
export DEV_USER_UUID=autre-uuid
python3 votre_script.py
```

**Option 2 : Permanent**

Modifier `~/.zshrc` et `mobile/app.json` avec le nouvel UUID.

## 📚 Documentation complète

Voir [UUID_CONFIGURATION.md](./UUID_CONFIGURATION.md) pour plus de détails.

## 🆘 Aide

**Erreur "DEV_USER_UUID doit être défini" ?**

→ Vérifiez que la variable est bien exportée : `echo $DEV_USER_UUID`

**Mobile : "UUID de développement non configuré" ?**

→ Vérifiez `mobile/app.json` et redémarrez l'app

**Script ne trouve pas user_config ?**

→ Assurez-vous d'être dans le dossier `backend/` : `cd backend`
