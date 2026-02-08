#!/bin/bash

# Script de redémarrage rapide du serveur backend
# Usage: ./restart_server.sh

echo "🔄 Redémarrage du serveur Pulse Backend..."
echo ""

# Tuer le processus sur le port 9000
echo "🛑 Arrêt du serveur existant..."
lsof -ti:9000 | xargs kill -9 2>/dev/null

# Attendre que le port se libère
sleep 2

echo "✅ Serveur arrêté"
echo ""

# Redémarrer le serveur
echo "🚀 Démarrage du nouveau serveur..."
echo "   (avec bulles dynamiques v2.0 : couleurs + animations + icônes)"
echo ""

python3 api_server_ambient.py
