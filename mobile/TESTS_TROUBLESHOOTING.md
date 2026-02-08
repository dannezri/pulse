# 🔧 Tests Mobile : Dépannage

## ✅ Corrections Appliquées

### 1. Configuration Jest Externalisée
- **Créé** : `jest.config.js` (configuration séparée)
- **Créé** : `jest.setup.js` (mocks minimalistes)
- **Modifié** : `package.json` (supprimé config inline)

### 2. Conflit Haste Résolu
```javascript
// jest.config.js
modulePathIgnorePatterns: [
  '<rootDir>/pulse-healthkit/',
  '<rootDir>/src/modules/pulseHealthkit/',
]
```

### 3. Mock Reanimated
```javascript
// jest.setup.js
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});
```

---

## 🚀 Tester Maintenant

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm test RiskWindowWithRecommendation
```

**Résultat attendu :** 14 tests passent

---

## ❌ Si Erreur "Object.defineProperty called on non-object"

### Cause
`jest-expo/preset/setup.js` essaie de configurer des propriétés inexistantes.

### Solution 1: Nettoyer le cache Jest

```bash
# Dans un terminal
cd /Users/dannezri/Desktop/Pulse/mobile
npm test -- --clearCache
npm test RiskWindowWithRecommendation
```

### Solution 2: Nettoyer watchman

```bash
watchman watch-del '/Users/dannezri/Desktop/Pulse'
watchman watch-project '/Users/dannezri/Desktop/Pulse'
```

### Solution 3: Désactiver temporairement le preset jest-expo

Si les erreurs persistent, éditer `jest.config.js` :

```javascript
module.exports = {
  // preset: 'jest-expo', // DÉSACTIVÉ temporairement
  testEnvironment: 'node',
  setupFiles: ['<rootDir>/jest.setup.js'],
  setupFilesAfterEnv: ['@testing-library/jest-native/extend-expect'],
  // ... reste de la config
};
```

---

## 🐛 Erreurs Fréquentes

### 1. "Cannot find module 'lucide-react-native'"

**Cause :** Dépendance manquante ou mal configurée.

**Solution :**
```bash
npm install lucide-react-native
```

### 2. "jest-haste-map: Haste module naming collision"

**Cause :** Deux `package.json` avec le même nom.

**Solution :** Déjà corrigé dans `jest.config.js` via `modulePathIgnorePatterns`.

### 3. "Invariant Violation: View config getter callback for component"

**Cause :** Composants natifs non mockés.

**Solution :** Ajouter dans `jest.setup.js` :
```javascript
jest.mock('react-native/Libraries/Components/View/ViewNativeComponent', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: ({ children }) => children,
  };
});
```

### 4. Tests passent mais avec warnings

**Cause :** Certains mocks incomplets.

**Solution :** Acceptable en MVP, à améliorer progressivement.

---

## 🔍 Debugging Avancé

### Mode Verbose

```bash
npm test RiskWindowWithRecommendation -- --verbose
```

### Voir les logs complets

```bash
npm test RiskWindowWithRecommendation 2>&1 | tee test-output.log
```

### Exécuter un seul test

```bash
npm test RiskWindowWithRecommendation -- -t "affiche le risk window classique"
```

---

## 📝 Configuration Finale

### jest.config.js
```javascript
module.exports = {
  preset: 'jest-expo',
  setupFiles: ['<rootDir>/jest.setup.js'],
  setupFilesAfterEnv: ['@testing-library/jest-native/extend-expect'],
  testMatch: ['**/__tests__/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[jt]s?(x)'],
  testPathIgnorePatterns: ['/node_modules/', '/pulse-healthkit/'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|lucide-react-native))',
  ],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.test.{ts,tsx}', '!src/**/__tests__/**'],
  modulePathIgnorePatterns: ['<rootDir>/pulse-healthkit/', '<rootDir>/src/modules/pulseHealthkit/'],
  haste: {
    defaultPlatform: 'ios',
    platforms: ['ios', 'android'],
  },
};
```

### jest.setup.js
```javascript
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});
```

### package.json
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

---

## 🎯 Commande Finale

```bash
# Nettoyer + Tester
cd /Users/dannezri/Desktop/Pulse/mobile
npm test -- --clearCache
npm test RiskWindowWithRecommendation
```

---

## ✅ Si Tests Passent

**Screenshot attendu :**
```
PASS  src/components/__tests__/RiskWindowWithRecommendation.test.tsx
  RiskWindowWithRecommendation
    Affichage Classique
      ✓ affiche le risk window classique (45ms)
    Affichage Enrichi
      ✓ affiche la recommandation (28ms)
      ...

Test Suites: 1 passed, 1 total
Tests:       14 passed, 14 total
Snapshots:   2 passed, 2 total
Time:        2.456s
```

**Prochaine étape :** Test manuel sur device 📱

---

## 🆘 Si Problèmes Persistent

**Option 1 : Skip Jest, utiliser tests E2E**
- Utiliser Detox/Maestro pour tests E2E
- Tests unitaires en MVP sont "nice to have"

**Option 2 : Tests manuels documentés**
- Créer checklist de scénarios
- Screenshots before/after
- Valider manuellement

**Option 3 : Simplifier le test**
- Tester uniquement la logique (pas le render)
- Créer `useDailyEnergy.test.ts` (hooks uniquement)

---

**Corrections appliquées ! À tester : `npm test -- --clearCache && npm test RiskWindowWithRecommendation`** 🚀
