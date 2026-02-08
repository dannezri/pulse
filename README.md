# Pulse - Monorepo

Application mobile de suivi de santé personnalisé avec insights en temps réel.

## 🏗️ Structure du Projet

```
Pulse/
├── mobile/          # Application mobile principale (Expo SDK 54, React Native 0.81.5)
├── backend/         # API Backend (FastAPI, Python)
├── database/        # Schémas et migrations SQL (Supabase/PostgreSQL)
└── docs/            # Documentation technique et architecture
```

## 🚀 Démarrage Rapide

### Prérequis
- Node.js >= 20.19.4
- Python 3.11+
- iOS: Xcode 15+ et simulateur iOS
- Android: Android Studio + SDK

### ⚙️ Configuration Initiale (IMPORTANT)

**Avant de lancer l'application, configurez votre UUID utilisateur :**

```bash
# Option 1 : Script automatique (recommandé)
./setup-uuid.sh votre-uuid-supabase

# Option 2 : Manuel
export DEV_USER_UUID=votre-uuid-supabase
# Puis éditer mobile/app.json (voir SETUP_UUID.md)
```

📚 **Guide complet :** [SETUP_UUID.md](./SETUP_UUID.md)

### Installation et Lancement

#### Mobile (Expo)
```bash
npm run start       # Démarrer le serveur de développement Expo
npm run ios         # Lancer sur iOS
npm run android     # Lancer sur Android
npm run doctor      # Vérifier la configuration Expo
```

#### Backend (FastAPI)
```bash
cd backend
./start_backend.sh  # Démarrer l'API sur http://localhost:9000
```

## 📚 Documentation Principale

### 🚀 Démarrage
- **[SETUP_UUID.md](./SETUP_UUID.md)** - ⭐ Configuration UUID (À FAIRE EN PREMIER)
- **[START_HERE.md](./START_HERE.md)** - Point d'entrée pour les nouveaux développeurs

### 📖 Architecture & Configuration
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture globale du système
- **[UUID_CONFIGURATION.md](./UUID_CONFIGURATION.md)** - Gestion des UUIDs utilisateur
- **[mobile/ARCHITECTURE.md](./mobile/ARCHITECTURE.md)** - Architecture mobile détaillée

### 🚢 Déploiement & Roadmap
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Guide de déploiement production
- **[MVP.md](./MVP.md)** - Fonctionnalités MVP et roadmap

### 📁 Autres
- **[docs/](./docs/)** - Documentation technique complète et archives
- **[MIGRATION_UUID_DYNAMIQUE.md](./MIGRATION_UUID_DYNAMIQUE.md)** - Historique migration UUID

## 🎯 Focus de Développement

**Workspace principal : `/mobile/`**

- Expo SDK 54 (managed workflow)
- React Native 0.81.5
- React 19.1.0
- TypeScript strict
- Architecture : `app/` (orchestration) + `src/` (composants/hooks/modules)

### Règles de Dépendances (IMPORTANT)

⚠️ **Pour toute dépendance Expo/React Native, TOUJOURS utiliser :**
```bash
cd mobile && npx expo install <package>
```

❌ **JAMAIS** `npm install`, `yarn add` ou `pnpm add` pour des packages natifs.

## 📱 Fonctionnalités Principales

- Synchronisation HealthKit (iOS) / Health Connect (Android)
- Score d'énergie en temps réel avec prédictions intraday
- Suivi nutrition avec intégration FatSecret
- Gestion des conditions de santé (ICD-11)
- Insights personnalisés et recommandations
- Mode sombre zen optimisé

## 🔗 Services Externes

- **Supabase** : Base de données PostgreSQL + Auth + Storage
- **FatSecret API** : Données nutritionnelles
- **Oura API** : Synchronisation wearables (optionnel)

## 🧪 Tests

```bash
# Mobile
cd mobile
npm test              # Jest unit tests
npm run test:watch    # Mode watch
npm run test:coverage # Coverage report

# Backend
cd backend
pytest                # Run all tests
```

## 📦 Gestion des Packages

```bash
npm run deps:fix      # Corriger les versions Expo
npm run deps:check    # Vérifier les incompatibilités
```

## 🤝 Contribution

1. Créer une branche feature depuis `main`
2. Respecter l'architecture définie dans `/mobile/ARCHITECTURE.md`
3. Tester avec `npm run doctor` avant commit
4. Documenter les changements majeurs

## 📄 License

Propriétaire - Tous droits réservés
