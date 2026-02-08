# 🔧 Instructions de Réinstallation

## Problème
Le workspace npm a installé `expo-router` dans `/Users/dannezri/Desktop/Pulse/node_modules` au lieu de `mobile/node_modules`, causant des erreurs de résolution de modules.

## Solution

### Étape 1 : Arrêter Metro
```bash
lsof -ti:8081 | xargs kill -9 2>/dev/null
```

### Étape 2 : Aller dans le dossier mobile
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
```

### Étape 3 : Nettoyer tout
```bash
rm -rf node_modules .expo .metro node_modules/.cache package-lock.json
watchman watch-del-all 2>/dev/null
```

### Étape 4 : Configurer npm pour accepter les peer dependencies
```bash
echo "legacy-peer-deps=true" > .npmrc
```

### Étape 5 : Réinstaller les dépendances
```bash
npm install
```

**Note** : `--legacy-peer-deps` est nécessaire car `lucide-react-native@0.468.0` ne supporte pas encore React 19 officiellement, mais fonctionne en pratique.

### Étape 6 : Vérifier l'installation
```bash
# Vérifier que expo-router est dans mobile/node_modules
ls -la node_modules/expo-router/build/
```

**Tu devrais voir le dossier `build/` avec des fichiers `.js` dedans.**

### Étape 7 : Lancer Metro
```bash
npx expo start --clear
```

## ✅ Si tout fonctionne

Tu verras :
- Metro démarrer sans erreurs
- QR code affiché
- Pas d'erreur "Unable to resolve module"

## 🎯 Changements appliqués

1. **`/Users/dannezri/Desktop/Pulse/package.json`** : Ligne `"workspaces": ["mobile"]` supprimée
2. **`mobile/metro.config.js`** : Configuration monorepo retirée, alias `@` conservé
3. Dépendances seront maintenant installées dans `mobile/node_modules` uniquement

## 🐛 Si ça ne marche toujours pas

Vérifie que `expo-router` est bien installé :
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm list expo-router
```

Devrait afficher :
```
pulse-mobile@1.0.0 /Users/dannezri/Desktop/Pulse/mobile
└── expo-router@6.0.22
```

Si absent, installe-le :
```bash
npx expo install expo-router
```
