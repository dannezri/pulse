# Source of Truth pour les Dépendances

## Règle fondamentale

**`mobile/package.json` est le SEUL source of truth pour toutes les dépendances Expo/React Native.**

## Structure

```
Pulse/
├── package.json          # ⚠️ Scripts proxy UNIQUEMENT (pas de dépendances)
└── mobile/
    └── package.json      # ✅ Source of truth (toutes les dépendances)
```

## Règles strictes

### 1. Installation des dépendances

**TOUJOURS depuis `mobile/` :**
```bash
cd mobile
npx expo install <package>
```

**JAMAIS :**
- `npm install <package>@latest` sans vérifier la compatibilité Expo
- `npm install <package>` pour les packages Expo/React Native
- Modifier manuellement les versions dans `package.json`

### 2. Vérification avant installation

Avant d'installer un package :
1. Vérifier la compatibilité avec Expo SDK 54
2. Utiliser `npx expo install` qui sélectionne automatiquement la bonne version
3. Si le package nécessite du code natif, avertir et proposer une alternative

### 3. Après installation

**Toujours exécuter :**
```bash
cd mobile
npx expo-doctor
```

Corriger TOUS les warnings avant de continuer.

### 4. Le package.json racine

Le `package.json` à la racine :
- ✅ Contient UNIQUEMENT les scripts proxy
- ✅ Peut contenir `workspaces` si nécessaire
- ❌ NE contient PAS de dépendances Expo/React Native
- ❌ NE contient PAS de `dependencies` ou `devDependencies` liées au mobile

### 5. Scripts disponibles

Depuis la racine :
- `npm run start` → `cd mobile && expo start`
- `npm run doctor` → `cd mobile && npx expo-doctor`
- `npm run deps:fix` → `cd mobile && npx expo install --fix`

## Workflow

### Ajouter une dépendance

```bash
# 1. Aller dans mobile/
cd mobile

# 2. Installer avec expo install
npx expo install <package>

# 3. Vérifier
npx expo-doctor
```

### Mettre à jour les dépendances

```bash
cd mobile
npx expo install --fix
npx expo-doctor
```

## Objectif

Éviter les conflits de versions et garantir la compatibilité avec Expo SDK.
