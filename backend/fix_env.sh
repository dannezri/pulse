#!/bin/bash
# Script pour mettre à jour automatiquement les credentials FatSecret dans .env

ENV_FILE="/Users/dannezri/Desktop/Pulse/backend/.env"

echo "🔧 Mise à jour des credentials FatSecret dans .env..."
echo ""

# Vérifier que le fichier existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Fichier .env introuvable : $ENV_FILE"
    exit 1
fi

# Backup du .env actuel
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup créé : ${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Nouvelles valeurs
NEW_KEY="23937fe67f5d4762bf1996ee584a7711"
NEW_SECRET="c136af15c45d41b3843b5d129fa3e323"

# Supprimer les anciennes lignes FatSecret (si elles existent)
sed -i '' '/^FATSECRET_CONSUMER_KEY=/d' "$ENV_FILE"
sed -i '' '/^FATSECRET_CONSUMER_SECRET=/d' "$ENV_FILE"

# Ajouter les nouvelles lignes à la fin
echo "" >> "$ENV_FILE"
echo "# FatSecret API Configuration" >> "$ENV_FILE"
echo "FATSECRET_CONSUMER_KEY=$NEW_KEY" >> "$ENV_FILE"
echo "FATSECRET_CONSUMER_SECRET=$NEW_SECRET" >> "$ENV_FILE"

echo "✅ Credentials FatSecret mis à jour dans .env"
echo ""
echo "🧪 Test de connexion..."
echo ""

# Tester la connexion
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_fatsecret_credentials.py

echo ""
echo "✅ Terminé !"
