# 🚀 Démarrage rapide OAuth2 Oura

## ⚡ En 3 étapes

### 1️⃣ Ajouter les credentials OAuth2

```bash
cd /Users/dannezri/Desktop/Pulse/backend
./add_oauth2_credentials.sh
```

Ce script ajoute automatiquement vos credentials OAuth2 dans le fichier `.env`.

### 2️⃣ Redémarrer le backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python api_server.py
```

### 3️⃣ Tester OAuth2

```bash
# Dans un autre terminal
cd /Users/dannezri/Desktop/Pulse/backend
python test_oura_sync.py
```

## ✅ C'est tout !

Le système OAuth2 est maintenant actif. Les tokens seront automatiquement rafraîchis.

## 📱 Pour l'app mobile

Consultez `mobile/INTEGRATION_OURA_MOBILE.md` pour implémenter l'UI OAuth2.

## 📚 Documentation complète

- `RESUME_OAUTH2_COMPLET.md` - Vue d'ensemble
- `OURA_OAUTH2_MIGRATION.md` - Documentation technique
- `SETUP_OAUTH2_USER_ACTUEL.md` - Guide détaillé

---

**Questions ?** Consultez la documentation ou les fichiers de code commentés.
