#!/bin/bash
# Script pour mettre à jour le Redirect URI Oura dans .env

set -e

echo "============================================"
echo "Mise à jour du Redirect URI Oura"
echo "============================================"
echo ""

# Chemin vers le fichier .env
ENV_FILE="/Users/dannezri/Desktop/Pulse/backend/.env"

# Vérifier si le fichier .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Fichier .env non trouvé: $ENV_FILE"
    exit 1
fi

echo "📝 Fichier .env trouvé: $ENV_FILE"
echo ""

# Nouveau Redirect URI
REDIRECT_URI="http://localhost:9000/api/oura/callback"

# Supprimer l'ancienne ligne si elle existe
if grep -q "OURA_REDIRECT_URI" "$ENV_FILE"; then
    echo "⚠️  Remplacement du Redirect URI existant..."
    sed -i.bak '/OURA_REDIRECT_URI/d' "$ENV_FILE"
fi

# Ajouter le nouveau Redirect URI
echo "OURA_REDIRECT_URI=$REDIRECT_URI" >> "$ENV_FILE"

echo ""
echo "✅ Redirect URI mis à jour avec succès!"
echo ""
echo "📋 Configuration:"
echo "   Redirect URI: $REDIRECT_URI"
echo ""
echo "🔄 Prochaine étape:"
echo "   python3 oura_oauth2_flow.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1"
echo ""
