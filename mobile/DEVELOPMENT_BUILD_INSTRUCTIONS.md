# Development Build Instructions

## ⚠️ IMPORTANT: expo-calendar Requires Development Build

`expo-calendar` nécessite du code natif et **NE FONCTIONNE PAS avec Expo Go**.

Vous devez créer un **Development Build** pour tester les fonctionnalités de calendrier.

## Prérequis

- Xcode installé (pour iOS)
- Android Studio installé (pour Android)
- Un device réel iOS ou Android (ou un simulateur/émulateur)
- Node.js >= 20.19.4

## Option 1: Build Local avec `npx expo run`

### Sur iOS (Device Réel ou Simulateur)

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# 1. Générer les fichiers natifs
npx expo prebuild

# 2. Lancer sur iOS
# Pour simulateur:
npx expo run:ios

# Pour device réel (connecté via USB):
npx expo run:ios --device
```

### Sur Android (Device Réel ou Émulateur)

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# 1. Générer les fichiers natifs (si pas déjà fait)
npx expo prebuild

# 2. Lancer sur Android
# Pour émulateur:
npx expo run:android

# Pour device réel (connecté via USB avec USB debugging activé):
npx expo run:android --device
```

## Option 2: EAS Build (Recommandé pour Production)

Si vous préférez utiliser Expo Application Services (EAS) pour créer le build:

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# 1. Installer EAS CLI si pas déjà fait
npm install -g eas-cli

# 2. Login EAS
eas login

# 3. Configurer le projet (si première fois)
eas build:configure

# 4. Créer un Development Build
# Pour iOS:
eas build --profile development --platform ios

# Pour Android:
eas build --profile development --platform android
```

Après le build, vous recevrez un QR code ou une URL pour installer l'app sur votre device.

## Ce qui a été fait

✅ Migration 013 appliquée (target_sleep_minutes ajouté à profiles)
✅ expo-calendar installé via `npx expo install expo-calendar`
✅ Permissions calendrier configurées dans app.json
✅ Tous les hooks métier créés:
  - useReadinessScore.ts
  - useCalendarEvents.ts
  - useAIPromptBuilder.ts
✅ Tous les composants UI créés:
  - ReadinessScoreCard.tsx
  - CalendarEventCard.tsx
✅ Dashboard mis à jour avec Readiness Score et Timeline Calendrier
✅ Page event-detail.tsx créée avec Badge de Probabilité de Succès
✅ Types TypeScript robustes pour JSONB (dailyContext.ts)

## Prochaines Étapes

1. **Créer le Development Build** (suivre les instructions ci-dessus)
2. **Tester le flow complet**:
   - Lancer l'app sur device réel/simulateur
   - Vérifier que le score de Readiness s'affiche correctement
   - Vérifier que les événements du calendrier apparaissent
   - Cliquer sur un événement pour voir le prompt IA
   - Copier le prompt et le tester dans ChatGPT
3. **Ajuster les baselines** dans Supabase si nécessaire (baseline_hrv, baseline_resting_hr, target_sleep_minutes)

## Notes Importantes

- **Expo Go ne fonctionnera pas** pour tester cette fonctionnalité
- Après `npx expo prebuild`, les dossiers `ios/` et `android/` seront générés/mis à jour
- Commitez ces changements dans Git si vous travaillez en équipe
- Les permissions calendrier seront demandées au runtime lors du premier accès

## Vérification expo-doctor

Avant de build, vérifiez la compatibilité:

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo-doctor
```

Si des warnings apparaissent, corrigez-les avant de continuer.

## Troubleshooting

### "Permission denied" lors du build iOS
- Assurez-vous que Xcode est à jour
- Nettoyez le cache: `rm -rf ios/build && rm -rf ~/Library/Developer/Xcode/DerivedData`

### "SDK not found" lors du build Android
- Vérifiez que Android Studio est installé
- Configurez ANDROID_HOME dans votre .bashrc ou .zshrc

### "expo-calendar not found"
- Relancez `npx expo prebuild` pour regénérer les fichiers natifs
- Vérifiez que le package est bien dans package.json
