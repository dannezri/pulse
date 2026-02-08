#!/bin/bash
echo "============================================================"
echo "🔄 Redémarrage du Backend avec ML Optimizer"
echo "============================================================"

cd /Users/dannezri/Desktop/Pulse/backend

# Tuer le processus API existant
echo "🛑 Arrêt du serveur existant..."
pkill -f "api_server.py"
sleep 2

# Redémarrer le serveur
echo "🚀 Démarrage du nouveau serveur avec MLOptimizer..."
nohup python3 api_server.py > backend_ml.log 2>&1 &

sleep 3

# Vérifier que le serveur est démarré
if pgrep -f "api_server.py" > /dev/null; then
    echo "✅ Serveur démarré avec succès !"
    echo "📋 Logs: tail -f backend_ml.log"
    echo ""
    echo "🧠 Le système ML est maintenant actif."
    echo "📡 Endpoint: POST http://localhost:9000/api/v1/feedback"
else
    echo "❌ Erreur : le serveur n'a pas démarré"
    echo "📋 Vérifier les logs: cat backend_ml.log"
    exit 1
fi

echo "============================================================"
