#!/bin/bash
# Script d'installation des dépendances Gemini pour Pulse

echo "============================================================"
echo "🚀 Installation des dépendances Gemini"
echo "============================================================"
echo ""

# Aller dans le dossier backend
cd /Users/dannezri/Desktop/Pulse/backend

echo "📦 Installation de google-generativeai..."
pip3 install google-generativeai

echo ""
echo "============================================================"
echo "✅ Installation terminée !"
echo "============================================================"
echo ""
echo "🧪 Test du client Gemini..."
echo ""

export GOOGLE_API_KEY="AIzaSyAP9UbJfUJEsx-rBrVhWXcuA1sT6ctIj7c"
python3 test_gemini_thinking.py

echo ""
echo "============================================================"
echo "📖 Si le test réussit, vous pouvez démarrer le backend :"
echo "   python3 api_server.py"
echo "============================================================"
