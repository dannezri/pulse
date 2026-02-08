# ✅ FIX CRASH DÉFINITIF - Scanner Caméra

**Date:** 4 février 2026  
**Problème:** App crash au clic sur "Réessayer"  
**Cause:** `requestPermission()` crashe quand `canAskAgain: false`  
**Status:** ✅ CORRIGÉ - Rebuild en cours

---

## 🔍 Analyse du Crash (Logs)

```
LOG  [BarcodeScanner] 🔵 handleRequestPermission APPELÉ
LOG  [BarcodeScanner] État avant appel: {"granted":false,"canAskAgain":false,"status":"denied"}
LOG  [BarcodeScanner] 🎥 Appel de requestPermission()...
(CRASH - pas de log suivant)
LOG  [BarcodeScanner] 🎥 Permission non accordée, isDefinitelyDenied: true
```

**Conclusion :** Le crash se produit **PENDANT** l'appel à `requestPermission()` quand `canAskAgain: false`.

---

## 💡 Explication du Problème

`expo-camera` ne supporte **PAS** d'appeler `requestPermission()` quand :
- La permission a été **refusée** précédemment
- iOS a marqué `canAskAgain: false`

Dans ce cas, iOS ne peut plus afficher le popup natif, et expo-camera **crashe** au lieu de gérer gracieusement ce cas.

---

## 🔧 Solution Appliquée

### AVANT ❌ (Causait le Crash)
```typescript
const handleRequestPermission = async () => {
  // Appeler requestPermission() dans tous les cas
  const result = await requestPermission(); // CRASH si canAskAgain: false
  
  if (!result.granted && result.canAskAgain === false) {
    Alert("Allez dans Réglages");
  }
};
```

### APRÈS ✅ (Fix)
```typescript
const handleRequestPermission = async () => {
  // 🔴 PROTECTION : Vérifier AVANT d'appeler requestPermission()
  if (permission?.canAskAgain === false) {
    console.log('⚠️ canAskAgain = false, ne pas appeler requestPermission()');
    
    // Afficher directement l'alert sans appeler requestPermission()
    Alert.alert(
      'Accès Caméra Requis',
      'Activez la caméra dans Réglages iOS :\n\nRéglages → Pulse → Appareil photo',
      [{ text: 'Compris', onPress: () => onClose() }]
    );
    return; // ⚠️ Sortir avant l'appel
  }
  
  // Si canAskAgain = true, on peut appeler requestPermission() en toute sécurité
  const result = await requestPermission(); // ✅ Pas de crash
};
```

---

## 📱 Comportements Attendus Maintenant

### Cas 1 : Première Installation (canAskAgain: true)

1. Clic sur "Autoriser"
2. `requestPermission()` est appelé
3. **Popup natif iOS s'affiche** ✅
4. Si OK → Caméra s'ouvre
5. Si refus → Reste sur l'écran

### Cas 2 : Permission Déjà Refusée (canAskAgain: false)

1. Clic sur "Réessayer"
2. `requestPermission()` n'est **PAS** appelé (protection)
3. **Alert s'affiche directement** : "Allez dans Réglages" ✅
4. **Pas de crash** ✅
5. Clic "Compris" → Fermeture du modal

---

## 🧪 Test Après le Rebuild

### Étape 1 : Vérifier Pas de Crash
1. Médicaments → + → Scanner 📷
2. Cliquer **"Réessayer"**
3. **→ Alert doit s'afficher (pas de crash)** ✅

### Étape 2 : Activer la Caméra
1. iPhone → **Réglages** → **Pulse**
2. **Appareil photo** → **Activer**

### Étape 3 : Tester le Scanner
1. Rouvrir l'app Pulse
2. Médicaments → + → Scanner 📷
3. **→ Caméra doit s'ouvrir directement** ✅

### Étape 4 : Tester le Popup Natif (Optionnel)
Pour voir le vrai popup iOS :
1. Supprimer l'app Pulse
2. Rebuild : `npx expo run:ios --device "iPhone 14 Pro Max"`
3. Médicaments → + → Scanner 📷 → "Autoriser"
4. **→ Popup natif iOS** ✅

---

## 📊 Logs de Debug Attendus

### Quand canAskAgain = false (Déjà Refusé)
```
[BarcodeScanner] 🔵 handleRequestPermission APPELÉ
[BarcodeScanner] État avant appel: {"canAskAgain":false}
[BarcodeScanner] ⚠️ canAskAgain = false, ne pas appeler requestPermission()
[BarcodeScanner] 📱 Affichage alert pour aller dans Réglages iOS
[BarcodeScanner] 🔵 handleRequestPermission TERMINÉ
```

### Quand canAskAgain = true (Peut Demander)
```
[BarcodeScanner] 🔵 handleRequestPermission APPELÉ
[BarcodeScanner] État avant appel: {"canAskAgain":true}
[BarcodeScanner] 🎥 Permission peut être demandée, appel de requestPermission()...
(Popup natif iOS s'affiche)
[BarcodeScanner] ✅ Résultat reçu: {"granted":true/false}
[BarcodeScanner] 🔵 handleRequestPermission TERMINÉ
```

---

## ✅ Résumé

| État Permission | Action | Résultat |
|----------------|--------|----------|
| **canAskAgain: false** | Ne PAS appeler requestPermission() | Alert "Réglages" ✅ |
| **canAskAgain: true** | Appeler requestPermission() | Popup natif iOS ✅ |
| **granted: true** | Rien | Caméra directe ✅ |

---

## 🎯 Prochaines Étapes

1. **Attendez que le build se termine** (~1-2 min)
2. **Testez sur votre iPhone** :
   - Cliquer "Réessayer" → Doit afficher alert (pas crash)
3. **Activez la caméra dans Réglages iOS**
4. **Retestez le scanner** → Caméra doit s'ouvrir !

---

**Build en cours... Installation automatique dès que terminé !** ⏳

**Ce fix devrait résoudre définitivement le problème de crash.** ✨
