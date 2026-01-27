# Architecture du dossier `mobile`

## Vue d'ensemble

L'application **Pulse** est une application React Native construite avec **Expo Router** (file-based routing) et **TypeScript**. Elle permet de collecter et visualiser des données de santé depuis HealthKit (iOS) et d'afficher des insights générés par le backend.

## Structure des dossiers

```
mobile/
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
│   ├── components/       # Composants UI réutilisables (présentation pure)
│   ├── hooks/            # Hooks React personnalisés (logique métier)
│   ├── lib/              # Utilitaires et clients (Supabase, storage)
│   ├── modules/          # Modules personnalisés (wrappers JS)
│   └── screens/          # ⚠️ OPTIONNEL - Voir section dédiée
├── pulse-healthkit/      # Module Expo natif pour HealthKit
│   ├── ios/              # Code natif Swift
│   ├── android/          # Code natif Kotlin
│   ├── app.plugin.js     # Plugin Expo
│   └── src/              # Code TypeScript du module
├── assets/               # Images et ressources statiques
├── scripts/              # Scripts utilitaires
│   └── check-deps.sh     # Validation des dépendances
├── app.json              # Configuration Expo
├── package.json          # Source of truth pour les dépendances
├── tsconfig.json         # Configuration TypeScript
└── babel.config.js       # Configuration Babel
```

## Technologies principales

### Framework et routing
- **Expo SDK 54** : Framework React Native
- **Expo Router 6** : Routing basé sur le système de fichiers
- **React 19.1.0** : Bibliothèque UI
- **React Native 0.81.5** : Framework mobile
- **Node.js >= 20.19.4** : Version minimale requise (définie dans `engines`)

### Navigation
- **expo-router/unstable-native-tabs** : Navigation par onglets native
- **react-native-screens** : Gestion des écrans natifs
- **react-native-safe-area-context** : Gestion des zones sécurisées

### Backend et données
- **@supabase/supabase-js** : Client Supabase pour la base de données
- **expo-secure-store** : Stockage sécurisé des tokens
- **@tanstack/react-query** : Gestion d'état et cache des données

### UI et graphiques
- **react-native-gifted-charts** : Graphiques et visualisations
- **lucide-react-native** : Icônes
- **expo-linear-gradient** : Dégradés
- **expo-blur** : Effets de flou
- **react-native-svg** : Rendu SVG
- **nativewind** : Tailwind CSS pour React Native

### Modules natifs
- **pulse-healthkit** : Module Expo personnalisé pour accéder à HealthKit (iOS)

## Architecture détaillée

### 1. Routing (`app/`) - Orchestration minimale

Le routing utilise **Expo Router** avec un système de fichiers dans le dossier `app/` :

- **`app/_layout.tsx`** : Layout racine qui utilise `<Slot />` pour rendre les routes enfants
- **`app/index.tsx`** : Route d'accueil (redirection ou landing)
- **`app/login.tsx`** : Page de connexion
- **`app/(tabs)/`** : Groupe de routes avec navigation par onglets
  - **`app/(tabs)/_layout.tsx`** : Configure 3 onglets (Dashboard, Tendances, Profil)
  - **`app/(tabs)/index.tsx`** : Dashboard principal
  - **`app/(tabs)/tendances.tsx`** : Visualisation des tendances
  - **`app/(tabs)/profil.tsx`** : Profil utilisateur

**Règle :** Les routes sont des points d'entrée minimaux qui :
- Utilisent les hooks pour la logique métier
- Composent les composants UI
- Gèrent la navigation et les états de chargement/erreur

### 2. Composants (`src/components/`) - UI Pure

Composants React réutilisables de **présentation pure** (UI uniquement) :

- **`InsightCard.tsx`** : Carte d'affichage des insights générés par l'IA
- **`MetricCard.tsx`** : Carte d'affichage d'une métrique de santé (sommeil, HRV, fréquence cardiaque)

**Règle stricte :**
- Les composants reçoivent des props et affichent uniquement
- Pas de logique métier directe (pas d'appels API, pas de calculs complexes)
- Peuvent utiliser des hooks pour la logique si nécessaire
- Focus sur la présentation et l'interaction utilisateur

### 3. Hooks (`src/hooks/`) - Logique Métier

Hooks React personnalisés pour la **logique métier** (business logic) :

- **`useHealthData.ts`** : Hook principal pour gérer les données de santé (API, transformations)
- **`useNativeHealth.ts`** : Point d'entrée unifié pour accéder aux données natives
- **`useNativeHealth.ios.ts`** : Implémentation iOS (HealthKit)
- **`useNativeHealth.android.ts`** : Implémentation Android (à implémenter)

**Règle stricte :**
- Toute la logique métier (API, calculs, validation, transformations) doit être dans les hooks
- Les hooks encapsulent les appels API, la gestion d'état métier, les transformations de données
- Les hooks peuvent utiliser d'autres hooks ou utilitaires (`src/lib/`)

### 4. Bibliothèques (`src/lib/`)

Utilitaires et clients externes :

- **`supabase.ts`** : Client Supabase configuré
- **`storage.ts`** : Utilitaires de stockage local (SecureStore)

### 5. Modules (`src/modules/`) - Wrappers JS

Modules personnalisés de l'application (wrappers JavaScript purs) :

- **`pulseHealthkit/`** : Wrapper JavaScript pur pour le module natif
  - **`index.ts`** : Wrapper JS qui utilise `requireNativeModule('PulseHealthkit')`
  - **Pas de code natif** (tout le code natif est dans `pulse-healthkit/`)

**Règle :** `src/modules/` contient uniquement du code JavaScript/TypeScript. Aucun code natif (Swift/Kotlin).

### 6. Module natif (`pulse-healthkit/`)

Module Expo natif pour accéder à HealthKit sur iOS :

**Structure :**
- **`ios/`** : Code natif Swift
  - **`PulseHealthkitModule.swift`** : Module principal avec logique HealthKit
  - **`PulseHealthkitView.swift`** : Vue native (si nécessaire)
  - **`PulseHealthkit.podspec`** : Configuration CocoaPods
- **`android/`** : Code natif Kotlin (à implémenter)
- **`src/`** : Code TypeScript/JavaScript exposé par le module
- **`app.plugin.js`** : Plugin Expo pour la configuration (permissions, entitlements)
- **`expo-module.config.json`** : Configuration du module Expo

**API exposée :**
- `isAvailable()` : Vérifie la disponibilité de HealthKit
- `requestAuthorization()` : Demande les permissions
- `readSteps(fromISO, toISO)` : Lit les données de pas
- `readHeartRate(fromISO, toISO)` : Lit les données de fréquence cardiaque

**Règle :** Tout le code natif (Swift/Kotlin) doit être dans `pulse-healthkit/`, jamais dans `src/modules/`.

### 7. Écrans (`src/screens/`) - OPTIONNEL

**⚠️ Règle importante :** `src/screens/` est **optionnel** avec Expo Router.

**Deux options possibles :**

**Option 1 : Tout dans `app/` (RECOMMANDÉ pour ce projet)**
- Les routes dans `app/` contiennent directement le code des écrans
- Pas de dossier `src/screens/`
- Plus simple, aligné avec Expo Router

**Option 2 : `src/screens/` comme composants réutilisables**
- `src/screens/` contient des **composants screen** réutilisables
- Les routes dans `app/` **importent** ces composants
- Utile si un écran est utilisé dans plusieurs routes

**Règle stricte :** Ne pas avoir du code d'écran à la fois dans `app/` ET `src/screens/`. Choisir une approche.

**Recommandation pour ce projet :** Supprimer `src/screens/` (non utilisé actuellement) et tout mettre dans `app/`.

### 8. Configuration native

#### iOS (`ios/`)
- **`app/app.entitlements`** : Permissions HealthKit
- **`app/Info.plist`** : Configuration de l'app iOS
- **`app/AppDelegate.swift`** : Point d'entrée de l'application
- **`Podfile`** : Dépendances CocoaPods

#### Android (`android/`)
- **`android/build.gradle`** : Configuration Gradle racine
- **`android/app/build.gradle`** : Configuration de l'application Android

### 9. Configuration

#### `app.json`
Configuration Expo incluant :
- Permissions HealthKit (iOS)
- Configuration des splash screens
- Plugin personnalisé `pulse-healthkit` (référence `./pulse-healthkit/app.plugin.js`)

#### `package.json` - Source of Truth

**IMPORTANT :** `mobile/package.json` est le **SEUL source of truth** pour toutes les dépendances.

- Contient toutes les dépendances Expo/React Native
- Versions gérées par `npx expo install` (compatibilité Expo SDK 54)
- `engines.node` : `>=20.19.4` (version minimale requise)
- Scripts disponibles :
  - `npm run doctor` : Vérifie la configuration Expo
  - `npm run deps:fix` : Corrige les versions Expo
  - `npm run deps:check` : Vérifie les dépendances

**Règle :** Toujours utiliser `npx expo install <package>` pour les dépendances Expo/React Native. Jamais `npm install <package>@latest` sans vérifier la compatibilité.

#### `tsconfig.json`
- Extends `expo/tsconfig.base`
- Alias `@/*` pour les imports absolus
- Mode strict activé

#### `babel.config.js`
- Preset `babel-preset-expo`
- Plugin `module-resolver` pour les alias `@`

## Séparation UI vs Métier

### Principe fondamental

**Séparation claire entre la logique métier (business logic) et l'interface utilisateur (UI).**

### Règles de séparation

1. **Hooks (`src/hooks/`) = Logique métier**
   - Appels API (Supabase, services externes)
   - Gestion d'état métier
   - Calculs et transformations de données
   - Validation métier
   - Gestion des erreurs métier

2. **Composants (`src/components/`) = UI pure**
   - Affichage uniquement (présentation)
   - Reçoivent des props
   - Pas de logique métier directe

3. **Routes (`app/`) = Orchestration minimale**
   - Point d'entrée minimal
   - Utilisent les hooks pour la logique métier
   - Composent les composants UI
   - Gèrent la navigation

### Exemple

```typescript
// ❌ MAUVAIS : Logique métier dans un composant
export default function HomeScreen() {
  const [data, setData] = useState(null);
  useEffect(() => {
    supabase.from('health_data').select().then(setData);
  }, []);
  return <View>{data && <Text>{data.value}</Text>}</View>;
}

// ✅ BON : Séparation claire
// src/hooks/useHealthData.ts
export function useHealthData(userId: string) {
  return useQuery({
    queryKey: ['healthData', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .rpc('get_latest_health_profile', { user_uuid: userId });
      if (error) throw error;
      return transformHealthData(data);
    },
  });
}

// app/(tabs)/index.tsx
export default function HomeScreen() {
  const { userId } = useAuth();
  const { data, isLoading, error } = useHealthData(userId);
  
  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorView error={error} />;
  
  return (
    <View>
      <MetricCard 
        title="HRV" 
        value={data?.hrv} 
        icon={<Activity />}
      />
    </View>
  );
}
```

## Flux de données

### 1. Collecte des données de santé

```
HealthKit (iOS) 
  → pulse-healthkit (module natif)
  → src/modules/pulseHealthkit (wrapper JS)
  → useNativeHealth (hook)
  → useHealthData (hook métier)
  → Composants UI
```

### 2. Synchronisation avec le backend

```
Composants
  → useHealthData (hook métier)
  → Supabase Client (src/lib/supabase.ts)
  → Backend Supabase
  → Webhooks → Backend Python
```

### 3. Affichage des insights

```
Backend Python (génération d'insights)
  → Supabase (stockage)
  → useHealthData (hook métier)
  → Composants UI (lecture via RPC)
  → InsightCard (affichage)
```

## Patterns architecturaux

### 1. Séparation UI vs Métier
Séparation claire entre logique métier (hooks) et présentation (composants).

### 2. File-based routing
Expo Router utilise la structure de fichiers pour définir les routes, simplifiant la navigation.

### 3. Platform-specific code
- Fichiers `.ios.ts` et `.android.ts` pour le code spécifique à la plateforme
- Module natif pour les fonctionnalités non disponibles en JavaScript

### 4. Hooks personnalisés
Abstraction de la logique métier dans des hooks réutilisables.

### 5. Composants réutilisables
Composants UI isolés et réutilisables dans `src/components/`.

### 6. Source of Truth unique
`mobile/package.json` est le seul source of truth pour les dépendances. Le `package.json` racine contient uniquement des scripts proxy.

## Gestion des dépendances

### Source of Truth

**`mobile/package.json` est le SEUL source of truth pour toutes les dépendances Expo/React Native.**

### Installation

**Pour les packages Expo/React Native :**
```bash
cd mobile
npx expo install <package>
```

**JAMAIS :**
```bash
npm install <package>@latest  # Sans vérifier la compatibilité Expo
npm install <package>          # Pour les packages Expo/React Native
```

### Validation

**Après chaque installation :**
```bash
cd mobile
npx expo-doctor
```

**Corriger TOUS les warnings avant de continuer.**

### Mise à jour

```bash
cd mobile
npx expo install --fix
npx expo-doctor
```

### Scripts disponibles

Depuis la racine du projet :
- `npm run doctor` → Vérifie la configuration Expo dans `mobile/`
- `npm run deps:fix` → Corrige les versions Expo dans `mobile/`

Depuis `mobile/` :
- `npm run doctor` → Vérifie la configuration Expo
- `npm run deps:fix` → Corrige les versions Expo
- `npm run deps:check` → Vérifie les dépendances

## Points d'attention

1. **App.tsx legacy** : Le fichier `App.tsx` existe mais n'est pas utilisé avec Expo Router (point d'entrée via `index.ts`).

2. **Module natif** : Le module `pulse-healthkit` nécessite une compilation native et n'est disponible que sur iOS actuellement.

3. **Navigation tabs** : Utilise `unstable-native-tabs` (API instable), à surveiller pour les mises à jour.

4. **Dépendances Expo** : Toutes les dépendances doivent être compatibles avec Expo managed workflow (vérification via `expo-doctor`).

5. **`src/screens/` non utilisé** : Le dossier `src/screens/` existe mais n'est pas utilisé. Les routes dans `app/` contiennent directement le code. Recommandation : supprimer `src/screens/` pour éviter la confusion.

6. **Séparation UI/Métier** : Vérifier que toute la logique métier est dans `src/hooks/` et que les composants dans `src/components/` sont des composants de présentation purs.

7. **Source of Truth** : Ne jamais modifier manuellement les versions dans `package.json`. Toujours utiliser `npx expo install` pour les dépendances Expo/React Native.

8. **Node.js version** : Vérifier que Node.js >= 20.19.4 est installé (défini dans `engines.node`).

## Scripts disponibles

### Depuis la racine du projet

- `npm run start` : Démarre le serveur de développement Expo dans `mobile/`
- `npm run android` : Lance sur Android
- `npm run ios` : Lance sur iOS
- `npm run web` : Lance la version web
- `npm run doctor` : Vérifie la configuration Expo dans `mobile/`
- `npm run deps:fix` : Corrige les dépendances Expo dans `mobile/`

### Depuis `mobile/`

- `npm start` : Démarre le serveur de développement Expo
- `npm run android` : Lance sur Android
- `npm run ios` : Lance sur iOS
- `npm run web` : Lance la version web
- `npm run doctor` : Vérifie la configuration Expo
- `npm run deps:fix` : Corrige les versions Expo
- `npm run deps:check` : Vérifie les dépendances

## Évolutions possibles

1. **Android Health Connect** : Implémenter la collecte de données sur Android
2. **Offline-first** : Ajouter un système de cache local
3. **Notifications** : Notifications push pour les insights
4. **Widgets** : Widgets iOS/Android pour un accès rapide
5. **Tests** : Ajouter des tests unitaires et d'intégration
6. **Supprimer `src/screens/`** : Nettoyer le dossier non utilisé

## Documentation complémentaire

- **`docs/architecture-ui-business.md`** : Documentation détaillée sur la séparation UI vs Métier
- **`docs/deps-policy.md`** : Politique complète des dépendances
- **`.cursor/rules/ui-vs-business.md`** : Règles pour Cursor
- **`.cursor/rules/screens-rule.md`** : Règle pour `src/screens/`
- **`.cursor/rules/deps-source-of-truth.md`** : Règle pour le source of truth