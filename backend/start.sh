#!/bin/bash

# Script de lancement pour l'API Ambient Concierge
# Remplacez les valeurs ci-dessous par vos vraies credentials

# Supabase
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGc..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Port (optionnel)
export PORT=9000

# Lancer le serveur
echo "🚀 Démarrage de Pulse - Ambient Concierge API..."
python3 api_server_ambient.py
