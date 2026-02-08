# ⚠️ Migration vers google-genai (Package Mis à Jour)

## 🚨 Alerte Importante

Le package `google-generativeai` est **DÉPRÉCIÉ** et ne reçoit plus de mises à jour.

Google recommande de migrer vers le nouveau package `google-genai`.

---

## ✅ Migration Effectuée

J'ai **automatiquement migré** le code vers le nouveau package.

### Changements

| Avant | Après |
|-------|-------|
| `google-generativeai>=0.3.0` | `google-genai>=0.2.0` |
| `import google.generativeai as genai` | `from google import genai` |
| `genai.configure(api_key=...)` | `genai.Client(api_key=...)` |
| `genai.GenerativeModel(...)` | `client.models.generate_content(...)` |

---

## 📦 Installation

### 1. Désinstaller l'ancien package

```bash
pip uninstall google-generativeai
```

### 2. Installer le nouveau package

```bash
cd backend
pip install -r requirements.txt
```

Cela installera `google-genai>=0.2.0` (le nouveau package).

---

## 🔑 Configuration (Inchangée)

La configuration reste la même :

```bash
export GOOGLE_API_KEY="votre-clé-api-google"
```

Ou dans `.env` :

```bash
echo 'GOOGLE_API_KEY=votre-clé' >> backend/.env
```

**Obtenir une clé** : https://makersuite.google.com/app/apikey

---

## 🧪 Test

```bash
cd backend
python3 test_gemini_thinking.py
```

**Résultat attendu** :
```
✅ Gemini client initialized with model: gemini-2.0-flash-thinking-exp-01-21
📦 Using new google-genai package (google-generativeai is deprecated)
```

---

## 📊 Différences d'API

### Avant (google-generativeai)

```python
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="gemini-2.0-flash-thinking-exp-01-21")
response = model.generate_content(prompt)
```

### Après (google-genai)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(temperature=0.8, ...)
response = client.models.generate_content(
    model="gemini-2.0-flash-thinking-exp-01-21",
    contents=prompt,
    config=config
)
```

---

## ✅ Fichiers Modifiés

| Fichier | Changement |
|---------|------------|
| `backend/requirements.txt` | `google-generativeai` → `google-genai` |
| `backend/gemini_client.py` | Migration complète vers nouvelle API |

---

## 🐛 Troubleshooting

### Erreur : "No module named 'google.generativeai'"

**Solution** : Réinstaller les dépendances

```bash
pip uninstall google-generativeai
pip install -r requirements.txt
```

### Warning : "google.generativeai is deprecated"

**Solution** : C'est normal si l'ancien package est encore installé. Désinstallez-le :

```bash
pip uninstall google-generativeai
```

### Erreur : "No module named 'google.genai'"

**Solution** : Installer le nouveau package

```bash
pip install google-genai
```

---

## 📖 Documentation Google

- **Nouveau package** : https://github.com/google-gemini/python-genai
- **Migration guide** : https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md
- **API Reference** : https://ai.google.dev/api/python/google/genai

---

## ✅ Checklist

- [x] Code migré vers `google-genai`
- [x] `requirements.txt` mis à jour
- [x] Imports mis à jour
- [x] API calls mis à jour
- [ ] Ancien package désinstallé (`pip uninstall google-generativeai`)
- [ ] Nouveau package installé (`pip install -r requirements.txt`)
- [ ] Tests réussis (`python3 test_gemini_thinking.py`)

---

**Status** : ✅ Migration Complète  
**Date** : 2026-02-03  
**Package** : google-genai >= 0.2.0

---

**Prochaine étape** : Réinstaller les dépendances et tester !

```bash
pip uninstall google-generativeai
pip install -r requirements.txt
python3 test_gemini_thinking.py
```
