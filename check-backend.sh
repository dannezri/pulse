#!/bin/bash
echo "============================================================"
echo "🔍 Diagnostic Backend"
echo "============================================================"
echo ""

# 1. Vérifier si le backend est démarré
echo "1️⃣ Processus backend :"
ps aux | grep "api_server.py" | grep -v grep || echo "❌ Backend non démarré"
echo ""

# 2. Vérifier le port 9000
echo "2️⃣ Port 9000 (attendu) :"
lsof -i :9000 || echo "❌ Rien n'écoute sur le port 9000"
echo ""

# 3. Vérifier le port 8097 (dans les logs)
echo "3️⃣ Port 8097 (dans les erreurs) :"
lsof -i :8097 || echo "✅ Rien n'écoute sur le port 8097"
echo ""

# 4. Test de connexion
echo "4️⃣ Test de connexion :"
echo "Test localhost:9000..."
curl -s http://localhost:9000/health 2>&1 || echo "❌ Pas de réponse"
echo ""

# 5. IP locale
echo "5️⃣ Votre IP locale :"
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
echo ""

echo "============================================================"
echo "💡 Actions recommandées :"
echo "============================================================"
echo ""
echo "Si le backend n'est pas démarré :"
echo "  cd /Users/dannezri/Desktop/Pulse/backend"
echo "  ./restart_backend_ml.sh"
echo ""
echo "Si l'IP a changé, mettez à jour :"
echo "  mobile/src/config/api.ts (ligne 28)"
echo "============================================================"
