#!/bin/bash
echo "============================================================"
echo "🧪 Test Backend Pulse"
echo "============================================================"
echo ""

echo "1️⃣ Test endpoint racine (localhost):"
curl -s http://localhost:9000/ | head -c 200
echo ""
echo ""

echo "2️⃣ Test endpoint racine (réseau - pour iPhone):"
curl -s http://192.168.0.23:9000/ | head -c 200
echo ""
echo ""

echo "============================================================"
echo "✅ Si vous voyez du JSON ci-dessus, le backend fonctionne !"
echo ""
echo "📱 Prochaine étape: Nettoyer les caches mobile"
echo "   cd /Users/dannezri/Desktop/Pulse/mobile"
echo "   ./clear-all-caches.sh"
echo "   npx expo start --clear"
echo "============================================================"
