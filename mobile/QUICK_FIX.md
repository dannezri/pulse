# 🚀 Fix Rapide - Food Diary MVP

## ❌ Problème
```
lucide-react-native ne supporte pas React 19
→ npm install échoue
→ node_modules vide
→ Metro ne peut pas démarrer
```

## ✅ Solution (Dans ton terminal actuel)

```bash
# Tu es déjà dans /Users/dannezri/Desktop/Pulse/mobile

# 1. Créer .npmrc
echo "legacy-peer-deps=true" > .npmrc

# 2. Installer
npm install

# 3. Vérifier
ls -la node_modules/expo-router/build/

# 4. Lancer
npx expo start --clear
```

## 🎯 Ou utilise le script automatique

```bash
chmod +x install-with-legacy-peers.sh
./install-with-legacy-peers.sh
```

## 📝 Explication

**`lucide-react-native@0.468.0`** déclare un peer dependency `react@^16.5.1 || ^17.0.0 || ^18.0.0`, mais :
- Le projet utilise `react@19.1.0` (Expo SDK 54)
- `lucide-react-native` fonctionne quand même avec React 19
- `--legacy-peer-deps` dit à npm d'ignorer ce warning

**Alternatives :**
1. ✅ **Utiliser `--legacy-peer-deps`** (solution rapide)
2. Attendre une mise à jour de `lucide-react-native` qui supporte React 19
3. Remplacer `lucide-react-native` par une autre lib d'icônes

Pour le MVP, option 1 est parfaite ! 🎉
