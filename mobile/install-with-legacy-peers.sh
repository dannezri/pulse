#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "📝 Creating .npmrc with legacy-peer-deps..."
echo "legacy-peer-deps=true" > .npmrc

echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Installation complete!"
echo ""
echo "🔍 Verifying expo-router installation..."
if [ -d "node_modules/expo-router/build" ]; then
  echo "✅ expo-router/build/ found!"
  ls -la node_modules/expo-router/build/ | head -10
else
  echo "❌ expo-router/build/ NOT found!"
  exit 1
fi

echo ""
echo "🚀 Ready to start Metro:"
echo "   npx expo start --clear"
