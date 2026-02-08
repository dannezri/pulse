#!/bin/bash
set -e

echo "Fixing dependencies..."

# Supprimer node_modules racine
rm -rf /Users/dannezri/Desktop/Pulse/node_modules
rm -f /Users/dannezri/Desktop/Pulse/package-lock.json

# Supprimer node_modules mobile
rm -rf /Users/dannezri/Desktop/Pulse/mobile/node_modules
rm -f /Users/dannezri/Desktop/Pulse/mobile/package-lock.json

# Réinstaller dans mobile avec npm (pas workspace)
cd /Users/dannezri/Desktop/Pulse/mobile
npm install

echo "Dependencies fixed! Now you can run: cd mobile && npx expo start"
