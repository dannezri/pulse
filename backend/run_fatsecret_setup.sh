#!/bin/bash

# Script de setup interactif pour FatSecret
# Usage: ./run_fatsecret_setup.sh

set -e

echo "=================================="
echo "FatSecret Setup - Pulse"
echo "=================================="
echo ""

# Vérifier que nous sommes dans le bon dossier
if [ ! -f "setup_fatsecret.py" ]; then
    echo "❌ Erreur: setup_fatsecret.py introuvable"
    echo "   Veuillez exécuter ce script depuis le dossier backend/"
    exit 1
fi

# Vérifier que .env existe
if [ ! -f "../.env" ] && [ ! -f ".env" ]; then
    echo "⚠️  Avertissement: fichier .env introuvable"
    echo ""
fi

# Vérifier les variables d'environnement
echo "🔍 Vérification de la configuration..."

if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

missing_vars=()

if [ -z "$FATSECRET_CONSUMER_KEY" ]; then
    missing_vars+=("FATSECRET_CONSUMER_KEY")
fi

if [ -z "$FATSECRET_CONSUMER_SECRET" ]; then
    missing_vars+=("FATSECRET_CONSUMER_SECRET")
fi

if [ -z "$SUPABASE_URL" ]; then
    missing_vars+=("SUPABASE_URL")
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    missing_vars+=("SUPABASE_SERVICE_ROLE_KEY")
fi

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Variables d'environnement manquantes:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Veuillez ajouter ces variables dans votre fichier .env"
    exit 1
fi

echo "✅ Configuration OK"
echo ""

# Vérifier que requests-oauthlib est installé
echo "🔍 Vérification des dépendances Python..."

python3 -c "import requests_oauthlib" 2>/dev/null || {
    echo "❌ requests-oauthlib n'est pas installé"
    echo ""
    read -p "Installer maintenant ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install requests-oauthlib>=1.3.1
    else
        echo "Installation annulée"
        exit 1
    fi
}

echo "✅ Dépendances OK"
echo ""

# Lancer le script de setup
echo "🚀 Lancement du setup FatSecret..."
echo ""

python3 setup_fatsecret.py

echo ""
echo "=================================="
echo "Setup terminé !"
echo "=================================="
