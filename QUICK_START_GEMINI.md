# 🚀 Quick Start - Gemini Thinking Mode

## ✅ Ce qui a été fait

La section **"Pourquoi ce score ?"** de la page énergie utilise maintenant **Gemini 2.0 Flash avec mode raisonnement** au lieu de GPT-4o.

---

## 📦 Installation (3 étapes)

### 1. Installer les dépendances

```bash
cd backend

# Désinstaller l'ancien package déprécié (si installé)
pip uninstall -y google-generativeai

# Installer le nouveau package
pip install -r requirements.txt
```

Cela installera `google-genai` (nouveau package, l'ancien `google-generativeai` est déprécié).

### 2. Configurer la clé API Gemini

**Option A : Variable d'environnement**
```bash
export GOOGLE_API_KEY="votre-clé-api-google"
```

**Option B : Fichier .env**
```bash
echo 'GOOGLE_API_KEY=votre-clé-api-google' >> backend/.env
```

**Option C : Dans start.sh**
```bash
# Ajouter cette ligne dans backend/start.sh
export GOOGLE_API_KEY="votre-clé-api-google"
```

**🔑 Où obtenir la clé ?**
1. Aller sur [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Créer une nouvelle clé API
3. Copier la clé

### 3. Tester l'installation

```bash
cd backend
python test_gemini_thinking.py
```

**Résultat attendu** :
```
🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!
✅ Gemini Thinking mode est prêt à être utilisé
```

---

## 🚀 Démarrage

### Backend

```bash
cd backend
python api_server.py
```

Le serveur démarre sur `http://0.0.0.0:9000`

### Mobile

```bash
cd mobile
npx expo start
```

---

## 🧪 Test Complet

### 1. Test Backend (API)

```bash
# Dans un terminal, démarrer le backend
cd backend
python api_server.py

# Dans un autre terminal, tester l'endpoint
curl -X GET "http://localhost:9000/api/energy/explain/YOUR_USER_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Test Mobile (UI)

1. Ouvrir l'app mobile
2. Aller sur l'onglet "Énergie" ⚡
3. Scroll vers la section "💡 Pourquoi ce score ?"
4. Vérifier que les explications sont affichées

---

## 📊 Vérification

### Logs Backend

Quand le backend démarre, vous devriez voir :

```
[INFO] ✅ Gemini client initialized for Energy Explain Service
[INFO] ✅ Energy Explain Service initialized with Gemini Thinking mode
```

Quand une explication est générée :

```
[INFO] 🧠 Calling Gemini 2.0 Flash Thinking for card generation...
[INFO] 💭 Gemini thinking process (first 300 chars): ...
[INFO] ✅ Generated 3 cards with Gemini thinking
```

### Réponse API

```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "date": "2026-02-03",
  "cards": [
    {
      "type": "nervous",
      "title": "Le câblage est saturé",
      "text": "Ton HRV est tombé à 25ms...",
      "analogy": "C'est comme charger ton téléphone avec un câble sectionné",
      "metrics": {
        "primary": {"label": "HRV actuel", "value": 25, "unit": "ms"}
      }
    }
  ]
}
```

---

## 🐛 Problèmes Courants

### ❌ "GOOGLE_API_KEY must be set"

**Solution** : Configurer la clé API (voir étape 2 ci-dessus)

### ❌ "Energy Explain Service not available"

**Cause** : Le client Gemini n'a pas pu s'initialiser

**Solution** :
```bash
# Vérifier que la clé est définie
echo $GOOGLE_API_KEY

# Vérifier que le package est installé
pip list | grep google-generativeai

# Relancer le backend
cd backend && python api_server.py
```

### ❌ "Invalid response from Gemini"

**Solution** : Le service a un fallback automatique qui génère des cartes par défaut. Vérifier les logs pour plus de détails.

---

## 📖 Documentation Complète

- **Guide de migration** : `GEMINI_THINKING_MIGRATION.md`
- **Architecture Why-Stack** : `WHY_ENERGY_STACK_MVP.md`
- **Tests** : `backend/test_gemini_thinking.py`

---

## 🎯 Différences avec GPT-4o

| Aspect | GPT-4o (avant) | Gemini Thinking (maintenant) |
|--------|----------------|------------------------------|
| **Mode** | Direct | Raisonnement explicite |
| **Qualité** | Bonne | Excellente (plus contextualisée) |
| **Latence** | ~2-3s | ~3-4s |
| **Coût** | $0.01/req | ~$0.005/req |
| **Logs** | Basiques | + processus de raisonnement |

---

## ✅ Checklist

- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] `GOOGLE_API_KEY` configurée
- [ ] Test réussi (`python test_gemini_thinking.py`)
- [ ] Backend démarre sans erreur
- [ ] Endpoint `/api/energy/explain` fonctionne
- [ ] Section "Pourquoi ce score ?" affichée dans l'app

---

## 🤝 Besoin d'Aide ?

1. Vérifier les logs backend
2. Lancer le script de test : `python backend/test_gemini_thinking.py`
3. Consulter `GEMINI_THINKING_MIGRATION.md` pour plus de détails

---

**Status** : ✅ Prêt à tester  
**Date** : 2026-02-03  
**Version** : Gemini Thinking v1.0

**Bon test ! 🧠✨**
