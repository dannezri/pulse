# Project Technical Stack

## Source of Truth

**`mobile/package.json` est le SEUL source of truth pour toutes les dépendances.**

Le `package.json` racine contient UNIQUEMENT les scripts proxy.

## Workflow

- Expo managed workflow
- No bare / no custom native code

## Core versions (DO NOT CHANGE WITHOUT PROCEDURE)

Ces versions sont définies dans `mobile/package.json` et gérées par `npx expo install` :

- Expo SDK: ~54.0.0 (géré par Expo)
- React Native: 0.81.5
- React: 19.1.0
- Expo Router: ~6.0.22

## Package manager

- npm (package-lock.json dans `mobile/` est le source of truth)

## Règles strictes

### Installation

**TOUJOURS depuis `mobile/` :**
```bash
cd mobile
npx expo install <package>
```

**JAMAIS :**
- `npm install <package>@latest` sans vérifier la compatibilité Expo
- `npm install <package>` pour les packages Expo/React Native
- Modifier manuellement les versions dans `package.json`

### Validation

**Après chaque installation :**
```bash
cd mobile
npx expo-doctor
```

**Corriger TOUS les warnings avant de continuer.**

### Mise à jour des versions

```bash
cd mobile
npx expo install --fix
npx expo-doctor
```

## Scripts disponibles (depuis la racine)

- `npm run start` → Lance Expo dans `mobile/`
- `npm run doctor` → Vérifie la configuration Expo
- `npm run deps:fix` → Corrige les versions Expo

## Documentation

Voir aussi :
- `docs/deps-policy.md` - Politique complète des dépendances
- `.cursor/rules/deps-source-of-truth.md` - Règles pour Cursor
