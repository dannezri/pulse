#!/bin/bash
echo "============================================================"
echo "🚀 Démarrage Backend Pulse (Simple)"
echo "============================================================"
echo ""

cd /Users/dannezri/Desktop/Pulse/backend

# Tuer les processus existants
echo "🛑 Arrêt des anciens processus..."
pkill -f "api_server.py" 2>/dev/null
sleep 2

# Détecter python ou python3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Utilisation de python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Utilisation de python"
else
    echo "❌ Python non trouvé"
    echo "💡 Installez Python 3: brew install python3"
    exit 1
fi

# Vérifier les dépendances
echo ""
echo "📦 Vérification des dépendances..."
$PYTHON_CMD -c "import fastapi, supabase, anthropic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ Certaines dépendances manquent. Installation..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

# Démarrer le serveur
echo ""
echo "🚀 Démarrage du serveur API sur port 9000..."
nohup $PYTHON_CMD api_server.py > backend.log 2>&1 &
SERVER_PID=$!

sleep 3

# Vérifier que le serveur est démarré
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Serveur démarré avec succès (PID: $SERVER_PID)"
    echo ""
    echo "📋 Logs en temps réel: tail -f backend.log"
    echo "🛑 Arrêter: pkill -f api_server.py"
    echo ""
    
    # Test de santé
    sleep 2
    echo "🔍 Test de connexion..."
    if curl -s http://localhost:9000/health > /dev/null 2>&1; then
        echo "✅ Backend répond correctement !"
        echo "🌐 URL: http://localhost:9000"
    else
        echo "⚠️ Backend démarré mais ne répond pas encore"
        echo "💡 Attendez 5-10 secondes et testez: curl http://localhost:9000/health"
    fi
else
    echo "❌ Erreur : le serveur n'a pas démarré"
    echo ""
    echo "📋 Dernières lignes des logs:"
    tail -20 backend.log
    exit 1
fi

echo ""
echo "============================================================"
