#!/bin/bash
echo "🔄 Redémarrage forcé du backend API..."
echo ""

# Tuer tous les processus Python API
echo "1️⃣ Arrêt des processus existants..."
pkill -f "python.*api_server.py" 2>/dev/null
sleep 2

# Vérifier qu'ils sont bien arrêtés
if pgrep -f "python.*api_server.py" > /dev/null; then
    echo "⚠️ Processus encore actifs, force kill..."
    pkill -9 -f "python.*api_server.py"
    sleep 1
fi

echo "✅ Processus arrêtés"
echo ""

# Redémarrer
echo "2️⃣ Démarrage du nouveau serveur..."
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server.py &

sleep 3

# Vérifier que le serveur est démarré
if pgrep -f "python.*api_server.py" > /dev/null; then
    echo "✅ Serveur démarré avec succès!"
    echo ""
    echo "📡 Test de l'API dans 5 secondes..."
    sleep 5
    
    curl -s -X GET \
      "http://192.168.0.23:9000/api/medications/analyze/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
      -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
      | python3 -c "import json, sys; d=json.load(sys.stdin); print(f'✅ API OK - {d.get(\"_medications_count\", 0)} médicaments')" 2>/dev/null || echo "❌ API non accessible"
else
    echo "❌ Échec du démarrage"
fi
