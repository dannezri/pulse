# Pulse HealthKit Module

Module Expo Modules local pour l'intégration HealthKit iOS (lecture uniquement).

## Structure

- `index.ts` - API JavaScript exposée au code React Native
- `ios/PulseHealthkitModule.swift` - Implémentation Swift HealthKit
- `app.plugin.js` - Config plugin Expo pour automatiser la configuration iOS

## Fonctionnalités

- `isAvailable()` - Vérifie si HealthKit est disponible sur l'appareil
- `requestAuthorization()` - Demande les permissions HealthKit (lecture uniquement)
- `readSteps(fromISO, toISO)` - Lit les données de pas sur une période
- `readHeartRate(fromISO, toISO)` - Lit les données de fréquence cardiaque sur une période

## Configuration

Le module est automatiquement configuré via le plugin dans `app.json` :
- Ajoute les permissions HealthKit dans `Info.plist`
- Configure les entitlements HealthKit

## Utilisation

```typescript
import * as HealthKit from '@/src/modules/pulse-healthkit';

// Vérifier la disponibilité
const available = await HealthKit.isAvailable();

// Demander les permissions
const authorized = await HealthKit.requestAuthorization();

// Lire les données
const steps = await HealthKit.readSteps(fromISO, toISO);
const heartRates = await HealthKit.readHeartRate(fromISO, toISO);
```

## Prérequis

- iOS device réel (HealthKit n'est pas disponible sur simulateur)
- Permissions HealthKit accordées par l'utilisateur
- Build natif requis (`npx expo prebuild` + `npx expo run:ios --device`)
