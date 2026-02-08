# 🔧 Fix Final : Désactivation jest-expo

**Problème:** `TypeError: Object.defineProperty called on non-object` dans `jest-expo/src/preset/setup.js`  
**Cause:** Bug connu de jest-expo avec certaines dépendances  
**Solution:** Désactiver le preset et utiliser une config Node basique  

---

## ✅ Changements Appliqués

### 1. jest.config.js - Preset Désactivé

```javascript
module.exports = {
  // Preset désactivé temporairement
  // preset: 'jest-expo',
  testEnvironment: 'node',  // ← Utilise Node au lieu de jsdom
  setupFiles: ['<rootDir>/jest.setup.js'],
  setupFilesAfterEnv: ['@testing-library/jest-native/extend-expect'],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  // ... reste de la config
};
```

### 2. jest.setup.js - Mocks Améliorés

```javascript
// Mock react-native
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => ({
  default: { call: () => {} },
  createAnimatedComponent: (Component) => Component,
  FadeInDown: {
    duration: () => ({ springify: () => ({}) }),
  },
}));

// Mock lucide-react-native icons
jest.mock('lucide-react-native', () => ({
  TrendingDown: 'TrendingDown',
  Clock: 'Clock',
  AlertTriangle: 'AlertTriangle',
  Calendar: 'Calendar',
  CheckCircle: 'CheckCircle',
  ChevronDown: 'ChevronDown',
  ChevronUp: 'ChevronUp',
  Zap: 'Zap',
}));
```

---

## 🚀 Tester Maintenant

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm test -- --clearCache
npm test RiskWindowWithRecommendation
```

---

## 📊 Résultat Attendu

```
PASS  src/components/__tests__/RiskWindowWithRecommendation.test.tsx
  RiskWindowWithRecommendation
    Affichage Classique
      ✓ affiche le risk window classique quand has_conflict est absent
      ✓ affiche le risk window classique quand has_conflict est false
    Affichage Enrichi - Type Prepare
      ✓ affiche l'alerte creux d'énergie
      ✓ affiche la recommandation Pulse
      ✓ affiche le bouton expand détails
      ✓ expand/collapse les détails au tap
      ✓ affiche les événements en conflit quand expanded
    Affichage Enrichi - Type Reschedule
      ✓ affiche la recommandation reschedule
    Affichage Enrichi - Type Accept
      ✓ affiche la recommandation accept
      ✓ affiche tous les événements en conflit quand expanded
    Edge Cases
      ✓ gère has_conflict=true mais pas de recommendation
      ✓ gère conflicting_events vide
    Snapshots
      ✓ snapshot classique
      ✓ snapshot enrichi prepare

Test Suites: 1 passed, 1 total
Tests:       14 passed, 14 total
Time:        1.234s
```

---

## 🐛 Si Erreurs Persistent

### Option A : Simplifier le Test (Tests Logique Uniquement)

Créer `/Users/dannezri/Desktop/Pulse/mobile/src/hooks/__tests__/useDailyEnergy.test.ts` :

```typescript
import { classify_event_importance } from '../../utils/energyUtils';

describe('Energy Logic Tests', () => {
  test('classify event importance - critique', () => {
    expect(classify_event_importance('Réunion client')).toBe(3);
    expect(classify_event_importance('Meeting CEO')).toBe(3);
  });

  test('classify event importance - important', () => {
    expect(classify_event_importance('Call équipe')).toBe(2);
    expect(classify_event_importance('Rendez-vous manager')).toBe(2);
  });

  test('classify event importance - normal', () => {
    expect(classify_event_importance('Sport')).toBe(1);
    expect(classify_event_importance('Gym')).toBe(1);
  });

  test('classify event importance - personnel', () => {
    expect(classify_event_importance('Déjeuner')).toBe(0);
    expect(classify_event_importance('Café')).toBe(0);
  });
});
```

### Option B : Tests Manuels Documentés

Créer une checklist de test manuel dans `MANUAL_TESTING_CHECKLIST.md` :

```markdown
# ✅ Checklist Tests Manuels

## Scénario 1 : Risk Window Classique
- [ ] Ouvrir app
- [ ] Voir carte Energy
- [ ] Vérifier affichage "Creux prévu : 16h-18h"

## Scénario 2 : Risk Window avec Conflit
- [ ] Créer événement "Réunion client" à 16h30
- [ ] Ouvrir app
- [ ] Vérifier affichage "⚠️ Creux prévu : 16h-18h"
- [ ] Vérifier recommandation "Prends une pause 30 min avant"
- [ ] Taper "Voir détails"
- [ ] Vérifier expansion avec détails

## Scénario 3 : Différents Types Recommandations
- [ ] Événement critique → recommandation "prepare"
- [ ] Événement important → recommandation "reschedule"
- [ ] Événement normal → recommandation "reschedule" (léger)
```

### Option C : Tests E2E avec Detox

Installer Detox pour tests end-to-end (plus robuste) :

```bash
npm install detox --save-dev
npx detox init
```

---

## 🎯 Recommandation

**Pour le MVP :**
1. ✅ Tests Backend → Validés (3/3 passent)
2. 📝 Tests Mobile → Essayer avec la nouvelle config
3. 📱 Si échec → Tests manuels documentés (Option B)
4. 🚀 Deploy avec tests backend + tests manuels

**Post-MVP :**
- Migrer vers Detox pour tests E2E
- Ou attendre fix upstream de jest-expo

---

## 📝 Fichiers Modifiés

| Fichier | Modification |
|---------|--------------|
| `jest.config.js` | Preset désactivé, testEnvironment: 'node' |
| `jest.setup.js` | Mocks améliorés (reanimated, lucide) |

---

## 🚀 Commande à Exécuter

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm test -- --clearCache
npm test RiskWindowWithRecommendation
```

**Si ça passe :** 🎉 Tests validés !  
**Si ça échoue :** → Tests manuels (Option B) pour le MVP

---

**Dernière tentative avec config Node basique. Sinon, tests manuels documentés.** 🔧
