# Configuration HealthKit iOS - Guide d'implémentation

## ✅ Fichiers créés/modifiés

### Nouveaux fichiers créés :
1. `src/modules/pulse-healthkit/index.ts` - API JavaScript du module
2. `src/modules/pulse-healthkit/ios/PulseHealthkitModule.swift` - Implémentation Swift HealthKit
3. `src/modules/pulse-healthkit/app.plugin.js` - Config plugin Expo
4. `src/modules/pulse-healthkit/package.json` - Métadonnées du module
5. `src/modules/pulse-healthkit/README.md` - Documentation du module

### Fichiers modifiés :
1. `app.json` - Ajout du plugin pulse-healthkit
2. `ios/app/app.entitlements` - Ajout de la capability HealthKit
3. `src/hooks/useNativeHealth.ios.ts` - Implémentation complète avec le module natif
4. `src/hooks/useNativeHealth.android.ts` - Stub propre pour Health Connect
5. `app/(tabs)/index.tsx` - Simplification du bouton (appelle uniquement `sync()`)

## 📋 Prérequis

- iPhone réel (HealthKit n'est **pas** disponible sur simulateur)
- Xcode installé
- Expo CLI installé
- Permissions HealthKit dans l'appareil (seront demandées au premier lancement)

## 🚀 Commandes de test sur iPhone réel

### 1. Nettoyer et reconstruire le projet iOS

```bash
cd /Users/dannezri/Desktop/Pulse/app
npx expo prebuild --clean
```

Cette commande va :
- Nettoyer les fichiers iOS générés précédemment
- Régénérer le projet Xcode avec les nouvelles configurations
- Intégrer le module Swift HealthKit
- Configurer les entitlements et Info.plist

### 2. Lancer l'app sur iPhone réel

```bash
npx expo run:ios --device
```

Cette commande va :
- Compiler le projet iOS
- Installer l'app sur l'iPhone connecté
- Lancer l'app

**Note** : Assurez-vous que votre iPhone est connecté et déverrouillé.

### 3. Vérification finale

```bash
npx expo-doctor
```

Doit afficher : **17/17 checks passed. No issues detected!**

## 🧪 Checklist de test

### Avant le premier lancement :
- [ ] iPhone connecté et déverrouillé
- [ ] `npx expo prebuild --clean` exécuté sans erreur
- [ ] `npx expo-doctor` affiche 17/17

### Pendant le test :
- [ ] L'app se lance sans crash
- [ ] Le bouton "Synchroniser" est visible
- [ ] Au premier clic, iOS demande les permissions HealthKit
- [ ] Après acceptation des permissions, la synchronisation fonctionne
- [ ] Les logs affichent le nombre d'échantillons lus
- [ ] Un message de succès s'affiche avec le nombre d'échantillons

### Vérification des données :
- [ ] Ouvrir la console pour voir les logs :
  ```
  [HealthKit Sync] Succès: X échantillons de pas, Y échantillons de fréquence cardiaque
  [HealthKit Sync] Total pas sur 7 jours: Z
  [HealthKit Sync] Fréquence cardiaque moyenne: W bpm
  ```

## 🔧 Dépannage

### Erreur : "PulseHealthkitModule is not available"
**Cause** : Le module Swift n'a pas été compilé ou n'est pas détecté.
**Solution** :
1. Vérifier que `npx expo prebuild --clean` a été exécuté
2. Vérifier que le fichier `ios/app/app.entitlements` contient la capability HealthKit
3. Rebuild complet : `npx expo run:ios --device --clean`

### Erreur : "HealthKit n'est pas disponible"
**Cause** : Test sur simulateur ou HealthKit non disponible.
**Solution** : Utiliser un iPhone réel (HealthKit n'est pas disponible sur simulateur).

### Erreur : "Autorisation refusée"
**Cause** : L'utilisateur a refusé les permissions.
**Solution** : Aller dans Réglages > Confidentialité > Santé > Pulse et activer les permissions.

### Erreur de compilation Swift
**Cause** : Le module Swift n'est pas correctement intégré.
**Solution** :
1. Vérifier que `expo-modules-core` est installé
2. Vérifier que le fichier Swift est dans `src/modules/pulse-healthkit/ios/`
3. Exécuter `npx expo prebuild --clean` à nouveau

## 📝 Notes importantes

1. **Simulateur** : HealthKit n'est **jamais** disponible sur simulateur. Le hook détecte automatiquement le simulateur et affiche un message approprié.

2. **Permissions** : Les permissions HealthKit sont demandées au premier appel de `sync()`. L'utilisateur peut les refuser, dans ce cas un message d'erreur s'affiche.

3. **Données** : Le module lit les données des **7 derniers jours** par défaut. Les données sont normalisées au format :
   - `StepsSample`: `{ start: string, end: string, count: number }`
   - `HeartRateSample`: `{ time: string, bpm: number }`

4. **Lecture seule** : Le module est configuré en **lecture uniquement**. Aucune donnée n'est écrite dans HealthKit.

5. **Android** : Le hook Android retourne un stub propre indiquant que Health Connect sera disponible prochainement.

## 🔄 Prochaines étapes (optionnel)

- Envoyer les données lues vers Supabase
- Ajouter d'autres types de données (HRV, sommeil, etc.)
- Implémenter Health Connect pour Android
