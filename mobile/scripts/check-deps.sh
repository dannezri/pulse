#!/bin/bash
# Script de vérification des dépendances pour mobile/
# Vérifie Node version et expo-doctor

set -e

echo "🔍 Vérification des dépendances mobile/..."

# Vérifier Node version
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION="20.19.4"

echo "Node version: $NODE_VERSION"
echo "Required: >= $REQUIRED_VERSION"

# Comparer les versions (simple comparaison)
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Node version must be >= $REQUIRED_VERSION"
    exit 1
fi

echo "✅ Node version OK"

# Vérifier expo-doctor
cd "$(dirname "$0")/.." || exit 1

echo ""
echo "🔍 Exécution de expo-doctor..."
npx expo-doctor

if [ $? -eq 0 ]; then
    echo "✅ expo-doctor passed"
else
    echo "❌ expo-doctor failed"
    exit 1
fi

echo ""
echo "✅ Toutes les vérifications sont passées"
