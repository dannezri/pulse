#!/bin/bash
# Script pour ajouter les credentials OAuth2 Oura dans .env
# Usage: ./add_oauth2_credentials.sh

set -e

echo "============================================"
echo "Configuration OAuth2 Oura"
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

# Credentials OAuth2
CLIENT_ID="d0bf5c0a-f150-4112-adbd-408fecde8ad4"
CLIENT_SECRET="ROMfYYnIXn3Vq1GckwsXkp-A2LSm4Rt85ADG-uZ4pxE"
REDIRECT_URI="http://localhost:8000/api/oura/oauth/callback"

# Vérifier si les credentials existent déjà
if grep -q "OURA_CLIENT_ID" "$ENV_FILE"; then
    echo "⚠️  Les credentials OAuth2 existent déjà dans .env"
    echo ""
    read -p "Voulez-vous les remplacer? (y/N) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Opération annulée"
        exit 0
    fi
    
    # Supprimer les anciennes lignes
    sed -i.bak '/OURA_CLIENT_ID/d' "$ENV_FILE"
    sed -i.bak '/OURA_CLIENT_SECRET/d' "$ENV_FILE"
    sed -i.bak '/OURA_REDIRECT_URI/d' "$ENV_FILE"
    
    echo "✅ Anciennes credentials supprimées"
fi

# Ajouter les nouvelles credentials
echo "" >> "$ENV_FILE"
echo "# Oura OAuth2 Configuration" >> "$ENV_FILE"
echo "OURA_CLIENT_ID=$CLIENT_ID" >> "$ENV_FILE"
echo "OURA_CLIENT_SECRET=$CLIENT_SECRET" >> "$ENV_FILE"
echo "OURA_REDIRECT_URI=$REDIRECT_URI" >> "$ENV_FILE"

echo ""
echo "✅ Credentials OAuth2 ajoutées avec succès!"
echo ""
echo "📋 Credentials configurées:"
echo "   - Client ID: $CLIENT_ID"
echo "   - Client Secret: ${CLIENT_SECRET:0:20}..."
echo "   - Redirect URI: $REDIRECT_URI"
echo ""
echo "🔄 Prochaines étapes:"
echo "   1. Redémarrer le backend"
echo "   2. Configurer OAuth2 pour votre utilisateur:"
echo "      python setup_oura_oauth2.py --help"
echo "   3. Ou utiliser le flux OAuth2 complet:"
echo "      curl http://localhost:8000/api/oura/oauth/authorize"
echo ""
echo "📚 Documentation:"
echo "   - SETUP_OAUTH2_USER_ACTUEL.md"
echo "   - OURA_OAUTH2_MIGRATION.md"
echo ""
echo "============================================"
