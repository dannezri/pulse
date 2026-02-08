# 🔴 INSTRUCTIONS FINALES - Scanner Caméra

## 📊 État Actuel (d'après les logs)

```json
{
  "status": "denied",
  "canAskAgain": false,
  "granted": false
}
```

**Traduction :** iOS a enregistré que vous avez **déjà refusé** la permission caméra, et il **refuse d'afficher à nouveau le popup natif**.

---

## ❓ Question : Quel est le Problème Maintenant ?

### Option A : L'App Crash Encore ❌

Si l'app **plante/crash** quand vous cliquez :
- Sur l'icône Scanner 📷
- OU sur le bouton "Autoriser"

→ **Dites-moi et je regarderai les logs d'erreur**

### Option B : Pas de Popup Natif iOS ⚠️

Si l'app **NE crash PAS** mais :
- Vous voyez l'écran "Accès à la caméra"
- Vous cliquez "Autoriser"
- Rien ne se passe (pas de popup iOS)

→ **C'EST NORMAL !** iOS refuse d'afficher le popup car vous avez déjà refusé avant.

---

## ✅ SOLUTION OBLIGATOIRE : Réinitialiser la Permission

Pour que le popup natif iOS s'affiche, vous DEVEZ faire **l'une de ces 2 options** :

### 🎯 Option 1 : Supprimer et Réinstaller l'App (RECOMMANDÉ)

**Sur votre iPhone :**
1. Appui long sur l'icône **Pulse**
2. Sélectionnez **"Supprimer l'app"**
3. Confirmez **"Supprimer"**

**Puis dans le terminal :**
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo run:ios --device "iPhone 14 Pro Max"
```

**Attendez ~1-2 minutes** que l'app se réinstalle.

**Ensuite :**
- Médicaments → + → Scanner 📷
- Cliquer "Autoriser"
- **→ POPUP NATIF iOS VA S'AFFICHER !** ✅

---

### 🎯 Option 2 : Activer Manuellement dans Réglages iOS

**Sur votre iPhone :**
1. Ouvrez **Réglages**
2. Faites défiler jusqu'à **Pulse**
3. Appuyez sur **Appareil photo**
4. **Activez** l'accès

**Ensuite :**
- Rouvrez l'app Pulse
- Médicaments → + → Scanner 📷
- **→ Caméra s'ouvre directement !** ✅

---

## 🔍 Pourquoi iOS Ne Montre Pas le Popup ?

iOS garde en mémoire votre décision précédente. Quand vous avez cliqué "Ne pas autoriser" lors d'un test précédent, iOS a enregistré :

```
canAskAgain: false
```

Cela signifie : **"Ne plus demander à cet utilisateur"**

Pour réinitialiser ce choix, il n'y a que **2 solutions** :
1. Supprimer l'app (efface l'historique des permissions)
2. Changer manuellement dans Réglages iOS

**Il n'y a pas d'autre moyen** - c'est une limitation de sécurité d'iOS.

---

## 📝 Récapitulatif

| Situation | Solution |
|-----------|----------|
| **App crash** | Dites-moi et j'analyse les logs |
| **Popup iOS ne s'affiche pas** | Supprimez l'app puis réinstallez |
| **Ou** activer dans Réglages iOS | Réglages → Pulse → Appareil photo |

---

## 🎯 Action Immédiate

**Quelle option choisissez-vous ?**

1. Supprimer l'app → Je lance le rebuild
2. Activer dans Réglages → Testez maintenant

**Ou dites-moi si l'app crash encore**, et je continuerai le debug.
