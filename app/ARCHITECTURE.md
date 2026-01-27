# Architecture du dossier `app`

## Vue d'ensemble

L'application **Pulse** est une application React Native construite avec **Expo Router** (file-based routing) et **TypeScript**. Elle permet de collecter et visualiser des données de santé depuis HealthKit (iOS) et d'afficher des insights générés par le backend.

## Structure des dossiers

```
app/
├── android/              # Configuration native Android
├── ios/                  # Configuration native iOS
├── app/                  # Routes Expo Router (file-based routing)
│   ├── _layout.tsx       # Layout racine
│   ├── index.tsx         # Route d'accueil
│   ├── login.tsx         # Route de connexion
│   └── (tabs)/           # Groupe de routes avec navigation par onglets
│       ├── _layout.tsx   # Layout des onglets
│       ├── index.tsx     # Dashboard (onglet principal)
│       ├── profil.tsx    # Profil utilisateur
│       └── tendances.tsx # Tendances et graphiques
├── src/                  # Code source de l'application
│   ├── components/       # Composants React réutilisables
│   ├── hooks/            # Hooks React personnalisés
│   ├── lib/              # Utilitaires et clients (Supabase, storage)
│   ├── modules/          # Modules personnalisés
│   └── screens/          # Écrans (alternative aux routes)
├── pulse-healthkit/      # Module Expo natif pour HealthKit
├── assets/               # Images et ressources statiques
├── App.tsx               # Composant racine (legacy, non utilisé avec Expo Router)
├── app.json              # Configuration Expo
├── package.json          # Dépendances et scripts
├── tsconfig.json         # Configuration TypeScript
└── babel.config.js       # Configuration Babel
```

## Technologies principales

### Framework et routing
- **Expo SDK 54** : Framework React Native
- **Expo Router 6** : Routing basé sur le système de fichiers
- **React 19.1.0** : Bibliothèque UI
- **React Native 0.81.5** : Framework mobile

### Navigation
- **expo-router/unstable-native-tabs** : Navigation par onglets native
- **react-native-screens** : Gestion des écrans natifs
- **react-native-safe-area-context** : Gestion des zones sécurisées

### Backend et données
- **@supabase/supabase-js** : Client Supabase pour la base de données
- **expo-secure-store** : Stockage sécurisé des tokens

### UI et graphiques
- **react-native-gifted-charts** : Graphiques et visualisations
- **lucide-react-native** : Icônes
- **expo-linear-gradient** : Dégradés
- **expo-blur** : Effets de flou
- **react-native-svg** : Rendu SVG

### Modules natifs
- **pulse-healthkit** : Module Expo personnalisé pour accéder à HealthKit (iOS)

## Architecture détaillée

### 1. Routing (`app/`)

Le routing utilise **Expo Router** avec un système de fichiers :

- **`_layout.tsx`** : Layout racine qui utilise `<Slot />` pour rendre les routes enfants
- **`index.tsx`** : Route d'accueil (redirection ou landing)
- **`login.tsx`** : Page de connexion
- **`(tabs)/`** : Groupe de routes avec navigation par onglets
  - **`_layout.tsx`** : Configure 3 onglets (Dashboard, Tendances, Profil)
  - **`index.tsx`** : Dashboard principal
  - **`tendances.tsx`** : Visualisation des tendances
  - **`profil.tsx`** : Profil utilisateur

### 2. Composants (`src/components/`)

Composants React réutilisables :
- **`InsightCard.tsx`** : Carte d'affichage des insights générés par l'IA
- **`MetricCard.tsx`** : Carte d'affichage d'une métrique de santé (sommeil, HRV, fréquence cardiaque)

### 3. Hooks (`src/hooks/`)

Hooks React personnalisés pour la logique métier :

- **`useHealthData.ts`** : Hook principal pour gérer les données de santé
- **`useNativeHealth.ts`** : Point d'entrée unifié pour accéder aux données natives
- **`useNativeHealth.ios.ts`** : Implémentation iOS (HealthKit)
- **`useNativeHealth.android.ts`** : Implémentation Android (à implémenter)

### 4. Bibliothèques (`src/lib/`)

Utilitaires et clients externes :

- **`supabase.ts`** : Client Supabase configuré
- **`storage.ts`** : Utilitaires de stockage local (SecureStore)

### 5. Modules (`src/modules/`)

Modules personnalisés de l'application :

- **`pulse-healthkit/`** : Wrapper JavaScript pour le module natif
  - **`index.ts`** : API JavaScript exposée
  - **`app.plugin.js`** : Plugin Expo pour la configuration
  - **`ios/PulseHealthkitModule.swift`** : Module natif Swift

### 6. Module natif (`pulse-healthkit/`)

Module Expo natif pour accéder à HealthKit sur iOS :

**Structure :**
- **`ios/`** : Code natif Swift
  - **`PulseHealthkitModule.swift`** : Module principal
  - **`PulseHealthkitView.swift`** : Vue native (si nécessaire)
  - **`PulseHealthkit.podspec`** : Configuration CocoaPods
- **`android/`** : Code natif Kotlin (à implémenter)
- **`src/`** : Code TypeScript/JavaScript exposé
- **`expo-module.config.json`** : Configuration du module Expo

**API exposée :**
- `isAvailable()` : Vérifie la disponibilité de HealthKit
- `requestAuthorization()` : Demande les permissions
- `readSteps(fromISO, toISO)` : Lit les données de pas
- `readHeartRate(fromISO, toISO)` : Lit les données de fréquence cardiaque

### 7. Configuration native

#### iOS (`ios/`)
- **`app.entitlements`** : Permissions HealthKit
- **`Info.plist`** : Configuration de l'app iOS
- **`AppDelegate.swift`** : Point d'entrée de l'application
- **`Podfile`** : Dépendances CocoaPods

#### Android (`android/`)
- **`build.gradle`** : Configuration Gradle
- **`app/build.gradle`** : Configuration de l'application Android

### 8. Configuration

#### `app.json`
Configuration Expo incluant :
- Permissions HealthKit (iOS)
- Configuration des splash screens
- Plugin personnalisé `pulse-healthkit`

#### `tsconfig.json`
- Extends `expo/tsconfig.base`
- Alias `@/*` pour les imports absolus
- Mode strict activé

#### `babel.config.js`
- Preset `babel-preset-expo`
- Plugin `module-resolver` pour les alias `@`

## Flux de données

### 1. Collecte des données de santé

```
HealthKit (iOS) 
  → pulse-healthkit (module natif)
  → useNativeHealth (hook)
  → useHealthData (hook métier)
  → Composants UI
```

### 2. Synchronisation avec le backend

```
Composants
  → useHealthData
  → Supabase Client (src/lib/supabase.ts)
  → Backend Supabase
  → Webhooks → Backend Python
```

### 3. Affichage des insights

```
Backend Python (génération d'insights)
  → Supabase (stockage)
  → Composants (lecture via RPC)
  → InsightCard (affichage)
```

## Patterns architecturaux

### 1. File-based routing
Expo Router utilise la structure de fichiers pour définir les routes, simplifiant la navigation.

### 2. Platform-specific code
- Fichiers `.ios.ts` et `.android.ts` pour le code spécifique à la plateforme
- Module natif pour les fonctionnalités non disponibles en JavaScript

### 3. Hooks personnalisés
Abstraction de la logique métier dans des hooks réutilisables.

### 4. Composants réutilisables
Composants UI isolés et réutilisables dans `src/components/`.

## Points d'attention

1. **App.tsx legacy** : Le fichier `App.tsx` existe mais n'est pas utilisé avec Expo Router (point d'entrée via `index.ts`).

2. **Module natif** : Le module `pulse-healthkit` nécessite une compilation native et n'est disponible que sur iOS actuellement.

3. **Navigation tabs** : Utilise `unstable-native-tabs` (API instable), à surveiller pour les mises à jour.

4. **Dépendances Expo** : Toutes les dépendances doivent être compatibles avec Expo managed workflow (vérification via `expo-doctor`).

## Scripts disponibles

- `npm start` : Démarre le serveur de développement Expo
- `npm run android` : Lance sur Android
- `npm run ios` : Lance sur iOS
- `npm run web` : Lance la version web
- `npm run doctor` : Vérifie la configuration Expo
- `npm run deps:fix` : Corrige les dépendances incompatibles

## Évolutions possibles

1. **Android Health Connect** : Implémenter la collecte de données sur Android
2. **Offline-first** : Ajouter un système de cache local
3. **Notifications** : Notifications push pour les insights
4. **Widgets** : Widgets iOS/Android pour un accès rapide
5. **Tests** : Ajouter des tests unitaires et d'intégration
