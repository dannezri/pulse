# 📸 Guide de Test du Scanner de Code-Barres

## ⚠️ IMPORTANT : La caméra ne fonctionne PAS sur simulateur !

Le scanner de code-barres nécessite un **appareil iOS réel** pour fonctionner. Les simulateurs iOS n'ont pas accès à la caméra de votre Mac.

## 🔧 Comment tester sur un appareil réel

### 1. Connectez votre iPhone via USB

### 2. Arrêtez le simulateur actuel
Fermez l'application dans le simulateur ou appuyez sur `Ctrl+C` dans le terminal actif.

### 3. Lancez sur votre appareil réel
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo run:ios --device
```

### 4. Testez le scanner
1. Ouvrez l'écran Médicaments
2. Appuyez sur le bouton "+"
3. Appuyez sur l'icône de scan à côté de la barre de recherche
4. Autorisez l'accès à la caméra quand demandé
5. Pointez vers un code-barres de médicament

## ❓ Que faire si ça ne fonctionne toujours pas ?

### Vérifier les permissions dans l'app
1. Ouvrez Réglages → Pulse
2. Vérifiez que "Appareil photo" est activé

### Si l'app plante encore
Vérifiez les logs dans le terminal pour voir l'erreur exacte.

## 📱 Statut actuel
- ✅ `expo-camera` installé (v17.0.10)
- ✅ Permissions configurées dans `app.json`
- ✅ Composant `BarcodeScannerModal` créé
- ✅ Intégration dans `MedicationAutocomplete`
- ❌ **Ne fonctionne PAS sur simulateur**
- ⏳ **À tester sur appareil réel**

## 🔍 Code-barres supportés
- **CIP13** : Code Identifiant de Présentation 13 chiffres (standard français)
- **GTIN** : Global Trade Item Number (standard international)
- Formats : EAN-13, UPC-A, etc.

## 📡 Backend
L'endpoint `/api/medications/scan` attend un code-barres et retourne :
```json
{
  "medication": {
    "name": "Nom du médicament",
    "dosage": "Dosage",
    "cis": "Code CIS"
  }
}
```
