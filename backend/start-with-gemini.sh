#!/bin/bash

# Script de lancement pour l'API Pulse avec Gemini Thinking mode
# Remplacez les valeurs ci-dessous par vos vraies credentials

# Supabase
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGc..."

# OpenAI (encore utilisé par d'autres services)
export OPENAI_API_KEY="sk-..."

# Google Gemini (NOUVEAU - pour le Why-Stack)
export GOOGLE_API_KEY="your-google-api-key"
# Optionnel : spécifier un modèle différent
# export GEMINI_MODEL="gemini-2.0-flash-thinking-exp-01-21"

# Port (optionnel)
export PORT=9000

# Lancer le serveur
echo "🚀 Démarrage de Pulse API avec Gemini Thinking mode..."
echo "🧠 Gemini sera utilisé pour la section 'Pourquoi ce score ?'"
python3 api_server.py
