# 🆔 Changement du Bundle Identifier

## 🎯 Objectif
Changer le Bundle Identifier pour que iOS considère l'app comme **nouvelle** et affiche le **popup natif de permission caméra** !

---

## ✅ Modifications Effectuées

### Fichier : `app.json`

**Ancien Bundle ID :**
```
com.dannezri.pulse
```

**Nouveau Bundle ID :**
```
com.dannezri.pulsecamera
```

---

## 🚀 Étapes Suivantes

### 1. Supprimer l'Ancienne App de l'iPhone
- Appui long sur l'icône **Pulse**
- **Supprimer l'app**
- Confirmez

### 2. Clean Build Complet
```bash
cd mobile
rm -rf ios/Pods ios/build Podfile.lock
npx pod-install
npx expo run:ios --device "iPhone 14 Pro Max"
```

### 3. Première Utilisation
Une fois l'app installée :
1. **Médicaments → + → Scanner 📷**
2. **Cliquez "Autoriser"**
3. **→ POPUP NATIF iOS s'affiche !** 🎉
4. **Cliquez "OK"**
5. **→ Caméra s'ouvre !** 📷

---

## 📝 Important

- Pour iOS, c'est une **nouvelle app** (nouveau Bundle ID)
- Toutes les permissions sont **réinitialisées**
- Le popup natif **va s'afficher** au premier clic
- Les données utilisateur **restent intactes** (même UUID, même Supabase)

---

## ✅ Résultat Attendu

**Après ce changement :**
- ✅ iOS ne se souvient plus du refus de permission précédent
- ✅ Le popup natif iOS s'affiche normalement
- ✅ La caméra fonctionne après autorisation
- ✅ L'option "Appareil photo" apparaît dans Réglages → Pulse

---

**Date :** 2026-02-04
**Changement :** `com.dannezri.pulse` → `com.dannezri.pulsecamera`
