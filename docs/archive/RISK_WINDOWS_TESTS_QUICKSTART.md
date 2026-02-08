# Risk Windows Tests : Quick Start

**Status:** ✅ Tests prêts  
**Date:** 2026-01-30  

---

## 🚀 Exécution Rapide

### Backend Tests

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# 1. Sourcer les variables d'environnement
source .env  # ou export SUPABASE_URL=... SUPABASE_KEY=...

# 2. (Optionnel) Définir un user de test
export TEST_USER_ID="<uuid-user-avec-events>"

# 3. Exécuter les tests
cd tests
python3 test_risk_windows_agenda.py
```

**Sans TEST_USER_ID :** Les tests 1, 2 et 5 passeront (tests 3-4 skipped)  
**Avec TEST_USER_ID :** Tous les tests s'exécutent

---

### Mobile Tests

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# 1. Installer dependencies (si pas déjà fait)
npm install
npm install --save-dev @testing-library/react-native @testing-library/jest-native

# 2. Exécuter les tests
npm test RiskWindowWithRecommendation

# Ou tous les tests
npm test

# Avec coverage
npm test -- --coverage
```

---

## 📊 Résultats Attendus

### Backend (5 tests)

```
✅ PASS | Classification Événements
✅ PASS | Génération Recommandations
⏭️ SKIP | Enrichissement Risk Window (si pas de TEST_USER_ID)
⏭️ SKIP | Risk Windows Complet (si pas de TEST_USER_ID)
✅ PASS | Fail-Safe Erreur DB

Total: 3/3 passed (2 skipped)
```

### Mobile (14 tests)

```
✓ affiche le risk window classique
✓ affiche la recommandation Pulse
✓ expand/collapse les détails
✓ affiche les événements en conflit
...

Test Suites: 1 passed
Tests: 14 passed
Snapshots: 2 passed
```

---

## 🐛 Troubleshooting

### Erreur: "supabase_url is required"

**Solution :**
```bash
cd /Users/dannezri/Desktop/Pulse/backend
source .env
# Ou
export SUPABASE_URL="https://..."
export SUPABASE_KEY="eyJ..."
```

---

### Erreur: "@testing-library/react-native not found"

**Solution :**
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm install --save-dev @testing-library/react-native @testing-library/jest-native
```

---

### Tests Mobile Skip/Fail

**Vérifier configuration Jest dans `package.json` :**
```json
{
  "jest": {
    "preset": "react-native",
    "setupFilesAfterEnv": ["@testing-library/jest-native/extend-expect"]
  }
}
```

---

## ✅ Quick Check

### Backend OK si :
- ✅ Au moins 3/5 tests passent
- ✅ Classification fonctionne
- ✅ Recommandations correctes
- ✅ Fail-safe fonctionne

### Mobile OK si :
- ✅ 14/14 tests passent
- ✅ Snapshots générés
- ✅ Expand/collapse fonctionne

---

## 📚 Docs Complètes

- **`RISK_WINDOWS_TESTING_GUIDE.md`** → Guide complet (tests manuels, performance, debugging)
- **`RISK_WINDOWS_TESTS_QUICKSTART.md`** → Ce guide (quick start)

---

**Tests prêts ! Exécute-les pour valider l'implémentation.** 🧪
