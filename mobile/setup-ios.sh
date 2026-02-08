#!/bin/bash

set -e

echo "🍎 Setting up iOS project for Xcode..."
echo ""

cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies first..."
  echo "legacy-peer-deps=true" > .npmrc
  npm install
fi

echo "🔨 Generating native iOS project..."
npx expo prebuild --platform ios --clean

echo ""
echo "📲 Installing CocoaPods..."
cd ios
pod install
cd ..

echo ""
echo "✅ iOS project ready!"
echo ""
echo "🚀 To open in Xcode:"
echo "   open ios/app.xcworkspace"
echo ""
echo "Or run directly:"
echo "   npx expo run:ios"
