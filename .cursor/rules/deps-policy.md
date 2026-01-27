# Dépendances Mobile (Expo SDK 54) — Règles strictes

## Source of truth
- Seul `mobile/package.json` contient des dépendances.
- Le package.json racine ne doit contenir que des scripts proxy.

## Installation
- Toute dépendance Expo/RN: `cd mobile && npx expo install <pkg>`
- Interdit: `npm install <pkg>@latest` dans mobile

## Interdits (exemples)
- `react-native-health` (lib legacy, non Expo-managed)
- packages DOM/web-only dans mobile (ex: jsdom, DOMElement, window/document)
- outils CLI lancés avec un node différent de `mobile/.nvmrc` (ou équivalent)

## Obligatoire après changement deps
- `cd mobile && npx expo-doctor` doit être clean
- `cd mobile && npx expo install --fix` si nécessaire
