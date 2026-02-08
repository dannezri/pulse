# Tests Mobile : Setup

**Date:** 2026-01-30  
**Status:** ✅ Configuration ajoutée  

---

## 🎯 Configuration Ajoutée

### package.json

**Scripts ajoutés :**
```json
{
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage"
}
```

**DevDependencies ajoutées :**
- `jest`: ^29.7.0
- `jest-expo`: ^52.0.0
- `@testing-library/react-native`: ^12.4.3
- `@testing-library/jest-native`: ^5.4.3
- `react-test-renderer`: 19.1.0
- `@types/jest`: ^29.5.11

**Configuration Jest :**
- Preset: `jest-expo`
- Setup: `@testing-library/jest-native/extend-expect`
- Transform ignore patterns pour Expo/React Native

---

## 🚀 Installation

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Installer les nouvelles dépendances
npm install
```

---

## 🧪 Exécution Tests

### Tous les tests

```bash
npm test
```

### Tests spécifiques

```bash
# Test RiskWindowWithRecommendation uniquement
npm test RiskWindowWithRecommendation

# Ou
npm test -- RiskWindowWithRecommendation.test
```

### Watch mode (re-run automatique)

```bash
npm run test:watch
```

### Avec coverage

```bash
npm run test:coverage
```

---

## ✅ Résultat Attendu

```
PASS  src/components/__tests__/RiskWindowWithRecommendation.test.tsx
  RiskWindowWithRecommendation
    Affichage Classique
      ✓ affiche le risk window classique (45ms)
    Affichage Enrichi - Type Prepare
      ✓ affiche l'alerte creux d'énergie (31ms)
      ✓ expand/collapse les détails (89ms)
    ...

Test Suites: 1 passed, 1 total
Tests:       14 passed, 14 total
Snapshots:   2 passed, 2 total
```

---

## 🐛 Troubleshooting

### Erreur: Cannot find module 'expo'

**Solution :**
```bash
npm install
```

### Erreur: Transform error

**Solution :** Nettoyer le cache
```bash
npm run clean
npm install
npm test
```

### Erreur: Cannot resolve 'lucide-react-native'

**Solution :** Ajouter à `transformIgnorePatterns` (déjà fait)

---

## 📚 Docs

- Tests : `src/components/__tests__/RiskWindowWithRecommendation.test.tsx`
- Guide complet : `RISK_WINDOWS_TESTING_GUIDE.md`
