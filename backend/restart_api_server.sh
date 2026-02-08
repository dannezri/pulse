#!/bin/bash
# Script pour redémarrer proprement le serveur API

PORT=9000

echo "🔍 Vérification du port $PORT..."

# Trouver le PID du processus utilisant le port
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "⚠️  Port $PORT déjà utilisé par le processus $PID"
    echo "🛑 Arrêt du processus..."
    kill -9 $PID
    sleep 1
    echo "✅ Processus terminé"
else
    echo "✅ Port $PORT disponible"
fi

echo ""
echo "🚀 Démarrage du serveur API..."
echo ""

cd "$(dirname "$0")"
python3 api_server.py
