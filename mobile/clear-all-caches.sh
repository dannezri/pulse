#!/bin/bash
echo "🧹 Nettoyage complet des caches mobile..."

cd /Users/dannezri/Desktop/Pulse/mobile

# 1. Nettoyer les caches Metro/Expo
echo "📦 Nettoyage Metro & Expo..."
rm -rf .expo .expo-shared
rm -rf node_modules/.cache
watchman watch-del-all 2>/dev/null || true

# 2. Nettoyer le cache iOS
echo "🍎 Nettoyage iOS..."
rm -rf ios/build
rm -rf ~/Library/Developer/Xcode/DerivedData/Pulse-*

# 3. Nettoyer le cache npm
echo "📦 Nettoyage npm..."
npm cache clean --force

echo "✅ Caches nettoyés !"
echo ""
echo "🚀 Maintenant, lancez:"
echo "   npx expo start --clear"
