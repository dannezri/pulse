# 🚀 Commandes Essentielles - Gemini Thinking

## 📦 Installation (une seule fois)

```bash
# 1. Installer les dépendances
cd backend
pip uninstall -y google-generativeai  # Désinstaller l'ancien package déprécié
pip install -r requirements.txt

# 2. Configurer la clé API Gemini
export GOOGLE_API_KEY="votre-clé-api-google"

# Ou l'ajouter dans .env
echo 'GOOGLE_API_KEY=votre-clé' >> .env

# 3. Tester l'installation
python test_gemini_thinking.py
```

**Résultat attendu** :
```
🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!
```

---

## 🔑 Obtenir une Clé API

1. Aller sur https://makersuite.google.com/app/apikey
2. Cliquer sur "Create API Key"
3. Copier la clé
4. L'ajouter dans votre configuration (voir ci-dessus)

---

## 🚀 Démarrage

### Backend

```bash
cd backend

# Option 1 : Script avec Gemini
./start-with-gemini.sh

# Option 2 : Manuel
export GOOGLE_API_KEY="votre-clé"
python api_server.py
```

### Mobile

```bash
cd mobile
npx expo start
```

---

## 🧪 Tests

### Test Backend

```bash
# Test automatique
cd backend
python test_gemini_thinking.py

# Test API manuel
curl -X GET "http://localhost:9000/api/energy/explain/YOUR_USER_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test Mobile

1. Ouvrir l'app
2. Onglet "Énergie" ⚡
3. Scroll vers "💡 Pourquoi ce score ?"
4. ✅ Vérifier que les explications s'affichent

---

## 🐛 Dépannage Rapide

### Erreur : "GOOGLE_API_KEY must be set"

```bash
export GOOGLE_API_KEY="votre-clé"
```

### Erreur : "No module named 'google.generativeai'"

```bash
pip install -r requirements.txt
```

### Erreur : "Energy Explain Service not available"

```bash
# Vérifier la clé
echo $GOOGLE_API_KEY

# Relancer le backend
cd backend
python api_server.py
```

---

## 📖 Documentation

| Fichier | Description |
|---------|-------------|
| `QUICK_START_GEMINI.md` | ⭐ Guide rapide |
| `GEMINI_THINKING_MIGRATION.md` | Guide complet |
| `RESUME_MIGRATION_GEMINI.md` | Résumé exécutif |
| `backend/GEMINI_SETUP.md` | Setup backend |

---

## ✅ Checklist

- [ ] Dépendances installées
- [ ] GOOGLE_API_KEY configurée
- [ ] Test réussi
- [ ] Backend démarre
- [ ] App mobile fonctionne

---

**Quick Start** :
```bash
cd backend && pip install -r requirements.txt
export GOOGLE_API_KEY="votre-clé"
python test_gemini_thinking.py
./start-with-gemini.sh
```

**Status** : ✅ Prêt à tester  
**Date** : 2026-02-03
