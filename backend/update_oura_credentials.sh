#!/bin/bash
# Script pour mettre à jour les credentials OAuth2 Oura dans .env
# Usage: ./update_oura_credentials.sh

set -e

echo "============================================"
echo "Mise à jour des credentials OAuth2 Oura"
echo "============================================"
echo ""

# Chemin vers le fichier .env
ENV_FILE="/Users/dannezri/Desktop/Pulse/backend/.env"

# Vérifier si le fichier .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Fichier .env non trouvé: $ENV_FILE"
    echo "   Créez d'abord le fichier .env"
    exit 1
fi

echo "📝 Fichier .env trouvé: $ENV_FILE"
echo ""

# Nouveaux credentials OAuth2
CLIENT_ID="e7bb46a6-015d-4ffa-ad83-58ed64487655"
CLIENT_SECRET="ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU"
REDIRECT_URI="http://localhost:8000/api/oura/oauth/callback"

# Supprimer les anciennes lignes si elles existent
if grep -q "OURA_CLIENT_ID" "$ENV_FILE"; then
    echo "⚠️  Remplacement des credentials existants..."
    sed -i.bak '/OURA_CLIENT_ID/d' "$ENV_FILE"
    sed -i.bak '/OURA_CLIENT_SECRET/d' "$ENV_FILE"
    sed -i.bak '/OURA_REDIRECT_URI/d' "$ENV_FILE"
fi

# Ajouter les nouvelles credentials
echo "" >> "$ENV_FILE"
echo "# Oura OAuth2 Configuration (User: bee9a055-9b10-47d7-b91d-d7f6081a63f1)" >> "$ENV_FILE"
echo "OURA_CLIENT_ID=$CLIENT_ID" >> "$ENV_FILE"
echo "OURA_CLIENT_SECRET=$CLIENT_SECRET" >> "$ENV_FILE"
echo "OURA_REDIRECT_URI=$REDIRECT_URI" >> "$ENV_FILE"

echo ""
echo "✅ Credentials OAuth2 mises à jour avec succès!"
echo ""
echo "📋 Credentials configurées:"
echo "   - Client ID: $CLIENT_ID"
echo "   - Client Secret: ${CLIENT_SECRET:0:20}..."
echo "   - Redirect URI: $REDIRECT_URI"
echo ""
echo "🔄 Prochaines étapes:"
echo "   1. Redémarrer le backend pour charger les nouvelles credentials"
echo "   2. L'utilisateur bee9a055-9b10-47d7-b91d-d7f6081a63f1 pourra maintenant:"
echo "      - Se connecter à Oura via OAuth2 depuis l'app mobile"
echo "      - Ou utiliser le script: python setup_oura_oauth2.py"
echo ""
