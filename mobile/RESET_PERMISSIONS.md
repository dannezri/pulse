# 🔄 Réinitialiser les Permissions de la Caméra

## ❌ Problème Identifié

Les logs montrent que la permission caméra a été **refusée définitivement** :
```
"canAskAgain": false
"granted": false
"status": "denied"
```

iOS a enregistré votre refus précédent, et l'app ne peut plus demander la permission.

## ✅ Solution : Réinitialiser l'App

### Option 1 : Désinstaller et Réinstaller (RECOMMANDÉ)

1. **Sur votre iPhone**, supprimez l'app Pulse :
   - Appuyez longuement sur l'icône Pulse
   - Sélectionnez "Supprimer l'app"
   - Confirmez "Supprimer"

2. **Relancez le build** depuis le terminal :
   ```bash
   cd /Users/dannezri/Desktop/Pulse/mobile
   npx expo run:ios --device "iPhone 14 Pro Max"
   ```

3. **Au premier lancement**, iOS demandera à nouveau la permission caméra

### Option 2 : Réglages iOS (Plus Rapide)

1. Ouvrez **Réglages** sur votre iPhone
2. Faites défiler et trouvez **Pulse**
3. Appuyez sur **Appareil photo**
4. Activez l'accès

Ensuite, retestez le scanner dans l'app.

## 🔧 Ce Qui a Été Corrigé

Le code a été mis à jour pour gérer ce cas :

✅ **AVANT** : L'app tentait de charger la caméra même si permission refusée → CRASH

✅ **MAINTENANT** : L'app détecte la permission refusée et affiche :
- Message clair "Permission Refusée"
- Instructions pour aller dans les Réglages
- Pas de crash !

## 🧪 Prochaine Étape

Une fois que vous aurez :
1. **Soit** désinstallé/réinstallé l'app
2. **Soit** activé la caméra dans Réglages

Retestez :
1. Médicaments → + → Scanner 📷
2. Cette fois, vous devriez voir :
   - Écran de demande de permission (si réinstallé)
   - OU directement la caméra (si activé dans Réglages)

## 📊 Commande de Rebuild

Si vous choisissez l'option 1 (réinstallation), voici la commande :

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo run:ios --device "iPhone 14 Pro Max"
```

Le rebuild prendra ~1-2 minutes.

---

**Le problème est maintenant identifié et corrigé ! Il suffit juste de réinitialiser la permission.** ✅
