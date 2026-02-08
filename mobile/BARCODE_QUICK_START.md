# 🚀 Quick Start - Scanner de Code-Barres

**Date:** 2026-02-04

---

## ✅ Fonctionnalité Ajoutée

Un **bouton scanner** 📷 est maintenant disponible à côté de la barre de recherche dans le formulaire d'ajout de médicament.

---

## 📱 Comment l'Utiliser

### 1. Ouvrir le formulaire de médicament

```
App → Médicaments → Bouton "+" → Étape 1
```

### 2. Cliquer sur le bouton scanner

Le bouton **violet** à droite de la barre de recherche avec l'icône 📷

### 3. Autoriser la caméra

Si c'est la première fois, l'app demandera la permission d'accéder à la caméra.

### 4. Scanner le code-barres

Placez le **code-barres de la boîte** dans le cadre violet.

### 5. Auto-remplissage

Le médicament est automatiquement trouvé et rempli dans le formulaire ! 🎉

---

## ⚠️ Important : Rebuild Requis

L'ajout de `expo-camera` nécessite un **rebuild natif**.

### iOS

```bash
cd mobile
npx expo run:ios
```

### Android

```bash
cd mobile
npx expo run:android
```

### Expo Go

❌ **Non supporté** - Vous devez utiliser un build de développement.

---

## 🧪 Test Manuel

### Tester avec un vrai médicament

1. Prenez une boîte de **Doliprane** (ou autre médicament français)
2. Trouvez le code-barres au dos (code-barres EAN-13)
3. Scannez-le avec le bouton 📷
4. Vérifiez que le médicament est trouvé et rempli

### Codes-barres de test

Si vous n'avez pas de boîte sous la main, voici quelques CIP13 à tester manuellement :

- **Doliprane 500mg:** `3400930001551`
- **Doliprane 1000mg:** `3400930007280`

---

## 🎨 Design

### Bouton Scanner

- **Couleur:** Violet #5E5CE6
- **Taille:** 52x52px
- **Position:** À droite de la barre de recherche
- **Icône:** `ScanBarcode` de lucide-react-native

### Modal de Scan

- **Plein écran** avec fond noir
- **Cadre violet** de 280x200px au centre
- **Instructions:** "Placez le code-barres dans le cadre"
- **Feedback:** "Recherche en cours..." pendant le traitement

---

## 🔧 Fichiers Modifiés

### Créés
- ✅ `mobile/src/components/BarcodeScannerModal.tsx`

### Modifiés
- ✅ `mobile/src/components/MedicationAutocomplete.tsx`
- ✅ `mobile/src/services/GiygasMedicationAPI.ts`
- ✅ `mobile/app.json`

### Documentation
- ✅ `mobile/BARCODE_SCANNER_FEATURE_2026-02-04.md` (documentation complète)
- ✅ `mobile/BARCODE_QUICK_START.md` (ce fichier)

---

## ✅ Checklist

- [x] expo-camera installé via `npx expo install`
- [x] Composant BarcodeScannerModal créé
- [x] Bouton scanner ajouté à MedicationAutocomplete
- [x] API service corrigé (gtin au lieu de barcode)
- [x] Permissions caméra configurées dans app.json
- [x] 0 erreurs de linting
- [ ] **Rebuild natif à effectuer** (iOS/Android)
- [ ] Test sur device réel avec une vraie boîte de médicament

---

## 🐛 En Cas de Problème

### Caméra noire
```bash
# iOS: Vérifier les permissions dans Réglages > Pulse
# Android: Vérifier les permissions dans Paramètres > Apps > Pulse
```

### "Permission denied"
- L'utilisateur a refusé la permission
- Aller dans les paramètres du téléphone pour l'autoriser

### "Médicament introuvable"
- Le code-barres n'est pas dans la base Giygas
- Solution : Saisir le nom manuellement

### Rebuild échoue
```bash
# Nettoyer et réinstaller
cd mobile
rm -rf node_modules ios/Pods
npm install
npx pod-install
npx expo run:ios
```

---

## 📞 Support

Pour plus d'informations, consultez :
- `BARCODE_SCANNER_FEATURE_2026-02-04.md` (documentation technique complète)
- Logs dans l'app : `[GiygasMedicationAPI] Scan barcode: ...`
- Logs backend : `[Scan] GTIN ... → CIP13 ...`

---

**Prêt à scanner ! 📷🎉**
