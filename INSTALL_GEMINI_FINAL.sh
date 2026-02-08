#!/bin/bash
# Script d'installation final pour Gemini avec le nouveau package

echo "============================================================"
echo "🚀 Installation du NOUVEAU package google-genai"
echo "============================================================"
echo ""

cd /Users/dannezri/Desktop/Pulse/backend

echo "📦 Désinstallation de l'ancien package (déprécié)..."
pip3 uninstall -y google-generativeai

echo ""
echo "📦 Installation du nouveau package google-genai..."
pip3 install google-genai

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
