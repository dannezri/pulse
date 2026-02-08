#!/bin/bash
echo "============================================================"
echo "🔧 FIX AUTOMATIQUE - Connexion Backend ↔️ App"
echo "============================================================"
echo ""

# 1. Trouver l'IP locale
echo "1️⃣ Détection de votre IP locale..."
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n 1 | awk '{print $2}')

if [ -z "$LOCAL_IP" ]; then
  echo "❌ Impossible de détecter l'IP locale"
  echo "💡 Trouvez-la manuellement : ifconfig | grep 'inet '"
  exit 1
fi

echo "✅ IP locale détectée : $LOCAL_IP"
echo ""

# 2. Mettre à jour le fichier de config mobile
echo "2️⃣ Mise à jour de mobile/src/config/api.ts..."
CONFIG_FILE="/Users/dannezri/Desktop/Pulse/mobile/src/config/api.ts"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Fichier de config introuvable : $CONFIG_FILE"
  exit 1
fi

# Backup
cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"

# Remplacer l'IP (ligne 28)
sed -i '' "s|return 'http://.*:9000';|return 'http://$LOCAL_IP:9000';|g" "$CONFIG_FILE"

echo "✅ Config mise à jour avec IP : $LOCAL_IP"
echo ""

# 3. Vérifier si le backend est démarré
echo "3️⃣ Vérification du backend..."
if pgrep -f "api_server.py" > /dev/null; then
  echo "✅ Backend déjà démarré"
else
  echo "⚠️ Backend non démarré. Démarrage..."
  cd /Users/dannezri/Desktop/Pulse/backend
  chmod +x restart_backend_ml.sh
  ./restart_backend_ml.sh
  sleep 3
fi
echo ""

# 4. Test de connexion
echo "4️⃣ Test de connexion..."
echo "Test localhost:9000..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
  echo "✅ Backend accessible en local"
else
  echo "❌ Backend pas accessible en local"
  echo "💡 Vérifiez les logs : tail -f backend/backend_ml.log"
fi

echo ""
echo "Test $LOCAL_IP:9000..."
if curl -s http://$LOCAL_IP:9000/health > /dev/null 2>&1; then
  echo "✅ Backend accessible depuis le réseau"
else
  echo "⚠️ Backend pas accessible depuis le réseau"
  echo "💡 Vérifiez le firewall Mac (Préférences Système → Sécurité)"
fi
echo ""

# 5. Instructions finales
echo "============================================================"
echo "✅ CONFIGURATION TERMINÉE"
echo "============================================================"
echo ""
echo "📱 Prochaines étapes :"
echo ""
echo "1. Nettoyer les caches mobile :"
echo "   cd /Users/dannezri/Desktop/Pulse/mobile"
echo "   ./clear-all-caches.sh"
echo ""
echo "2. Redémarrer Metro :"
echo "   npx expo start --clear"
echo ""
echo "3. Relancer l'app sur votre iPhone (appuyez sur [i])"
echo ""
echo "🔍 URL configurée : http://$LOCAL_IP:9000"
echo ""
echo "Si l'erreur 61 persiste, vérifiez :"
echo "  - Mac et iPhone sur le même WiFi"
echo "  - Firewall Mac autorise Python"
echo "============================================================"
