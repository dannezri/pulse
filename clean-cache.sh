#!/bin/bash
echo "🧹 Nettoyage complet des caches..."

cd /Users/dannezri/Desktop/Pulse/mobile

# Arrêter tous les processus Metro
echo "Arrêt des processus Metro..."
pkill -f "expo start" || true
pkill -f "metro" || true

# Nettoyer les caches
echo "Nettoyage des caches..."
rm -rf .expo
rm -rf $TMPDIR/metro-*
rm -rf $TMPDIR/haste-*
rm -rf $TMPDIR/react-*
watchman watch-del-all 2>/dev/null || true

# Nettoyer le cache npm
npm cache clean --force

echo "✅ Caches nettoyés !"
echo ""
echo "Maintenant, lancez depuis le dossier mobile:"
echo "  cd /Users/dannezri/Desktop/Pulse/mobile"
echo "  npx expo start --clear"
