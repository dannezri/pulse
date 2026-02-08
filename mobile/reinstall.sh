#!/bin/bash

set -e

echo "🧹 Cleaning up..."

# Stop Metro if running
PORT=8081
PID=$(lsof -t -i:$PORT 2>/dev/null || true)
if [ -n "$PID" ]; then
  echo "⏹️  Stopping Metro Bundler (PID: $PID)"
  kill -9 $PID
  sleep 2
fi

# Clean caches and lock files
echo "🗑️  Removing caches..."
rm -rf node_modules
rm -rf .expo
rm -rf .metro
rm -rf node_modules/.cache
rm -f package-lock.json
rm -f yarn.lock

# Clean Watchman (if available)
if command -v watchman &> /dev/null; then
  echo "🔍 Cleaning Watchman..."
  watchman watch-del-all 2>/dev/null || true
fi

# Reinstall dependencies
echo "📦 Installing dependencies..."
npm install

echo "✅ Done! You can now run: npx expo start"
