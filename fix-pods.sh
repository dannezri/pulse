#!/bin/bash
set -e

echo "Fixing iOS Pods..."

cd /Users/dannezri/Desktop/Pulse/mobile

# Supprimer Pods et Podfile.lock
rm -rf ios/Pods ios/Podfile.lock

# Réinstaller les Pods
cd ios
pod install

echo "✅ Pods fixed! You can now run: npx expo run:ios --device"
