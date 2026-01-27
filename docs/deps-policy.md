# Dependency Policy (Expo + React Native)

## Source of Truth

**IMPORTANT : Un seul source of truth pour les versions**

- **`mobile/package.json`** est le **SEUL** source of truth pour toutes les dépendances Expo/React Native
- Le `package.json` à la racine ne doit contenir QUE les scripts de proxy vers `mobile/`
- **JAMAIS** de duplication de dépendances entre les deux fichiers

## Règles strictes

### 1. Installation des dépendances

**Pour les packages Expo/React Native :**
```bash
cd mobile
npx expo install <package>
```

**JAMAIS :**
```bash
npm install <package>@latest
npm install <package>
yarn add <package>
pnpm add <package>
```

### 2. Vérification avant installation

Avant d'installer un package :

1. **Vérifier la compatibilité Expo**
   - Consulter [Expo SDK Compatibility](https://docs.expo.dev/versions/latest/)
   - Vérifier que le package supporte Expo managed workflow
   - Si le package nécessite du code natif, pods, gradle, ou prebuild :
     - ⚠️ **Avertir clairement**
     - Proposer une alternative compatible Expo si possible

2. **Vérifier la version compatible avec le SDK**
   - Expo SDK 54 : `~54.0.32`
   - React Native : `0.81.5`
   - React : `19.1.0`
   - Utiliser `npx expo install` qui sélectionne automatiquement la bonne version

### 3. Après installation

**Toujours exécuter :**
```bash
cd mobile
npx expo-doctor
```

**Corriger TOUS les warnings et erreurs avant de continuer.**

### 4. Gestion des versions

**NE JAMAIS modifier manuellement les versions de :**
- `expo`
- `react`
- `react-native`
- `expo-router`
- Toute dépendance Expo (`expo-*`)

**Utiliser `npx expo install --fix` pour corriger les versions :**
```bash
cd mobile
npx expo install --fix
```

### 5. Structure des package.json

**`mobile/package.json`** (source of truth) :
- Contient TOUTES les dépendances
- Utilise les versions compatibles Expo SDK 54
- Les versions sont gérées par `npx expo install`

**`package.json`** (racine) :
- Contient UNIQUEMENT les scripts proxy
- NE contient PAS de dépendances (sauf si nécessaire pour les scripts racine)
- Les scripts pointent vers `mobile/`

### 6. Détection de conflits

Si un conflit est détecté :
1. **Arrêter immédiatement**
2. Expliquer l'incompatibilité
3. Proposer une alternative compatible Expo
4. Si aucune alternative n'existe, documenter la limitation

## Workflow recommandé

### Ajouter une nouvelle dépendance Expo

```bash
# 1. Vérifier la compatibilité (docs Expo)
# 2. Installer avec expo install
cd mobile
npx expo install <package>

# 3. Vérifier avec expo-doctor
npx expo-doctor

# 4. Si erreurs, corriger
npx expo install --fix
npx expo-doctor
```

### Ajouter une dépendance non-Expo (JavaScript pur)

```bash
cd mobile
npm install <package>

# Vérifier quand même avec expo-doctor
npx expo-doctor
```

### Mettre à jour les dépendances

```bash
cd mobile

# Corriger toutes les versions Expo
npx expo install --fix

# Vérifier
npx expo-doctor
```

## Scripts disponibles

Dans `package.json` racine :
- `npm run deps:fix` : Corrige les dépendances Expo dans `mobile/`
- `npm run doctor` : Vérifie la configuration Expo dans `mobile/`

## Objectif

Garantir la compatibilité avec Expo SDK et éviter les erreurs de runtime et de build.

## Références

- [Expo SDK Compatibility](https://docs.expo.dev/versions/latest/)
- [Expo Install Command](https://docs.expo.dev/more/expo-cli/#expo-install)
- [Expo Doctor](https://docs.expo.dev/more/expo-cli/#expo-doctor)
