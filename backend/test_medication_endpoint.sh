#!/bin/bash

# Script de test pour vérifier l'endpoint d'analyse de médicaments

echo "🧪 Test de l'endpoint d'analyse de médicaments"
echo "=============================================="
echo ""

# Vérifier que les variables sont définies
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL="http://localhost:9000"
    echo "⚠️  BACKEND_URL non défini, utilisation de: $BACKEND_URL"
fi

if [ -z "$USER_ID" ]; then
    echo "❌ Erreur: USER_ID non défini"
    echo ""
    echo "Usage:"
    echo "  export USER_ID='votre-user-id'"
    echo "  export JWT_TOKEN='votre-jwt-token'"
    echo "  ./test_medication_endpoint.sh"
    echo ""
    echo "Pour trouver un user_id:"
    echo "  psql \$DATABASE_URL -c \"SELECT id, full_name FROM profiles LIMIT 5;\""
    exit 1
fi

if [ -z "$JWT_TOKEN" ]; then
    echo "❌ Erreur: JWT_TOKEN non défini"
    echo ""
    echo "Usage:"
    echo "  export JWT_TOKEN='votre-jwt-token'"
    echo "  ./test_medication_endpoint.sh"
    echo ""
    echo "Pour générer un JWT token:"
    echo "  cd backend"
    echo "  python3 get_jwt_token.py"
    exit 1
fi

echo "📍 Backend URL: $BACKEND_URL"
echo "👤 User ID: $USER_ID"
echo "🔑 JWT Token: ${JWT_TOKEN:0:20}..."
echo ""

# Test de l'endpoint
echo "🚀 Appel de l'endpoint /api/medications/analyze/$USER_ID"
echo ""

response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    "$BACKEND_URL/api/medications/analyze/$USER_ID")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "📊 HTTP Status: $http_code"
echo ""

if [ "$http_code" = "200" ]; then
    echo "✅ Succès !"
    echo ""
    echo "Réponse JSON:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo ""
    
    # Extraire des infos utiles
    med_count=$(echo "$body" | jq -r '.analyse_traitements | length' 2>/dev/null)
    if [ "$med_count" != "null" ] && [ "$med_count" != "" ]; then
        echo "📋 Nombre de médicaments analysés: $med_count"
        
        if [ "$med_count" -gt 0 ]; then
            echo ""
            echo "Médicaments:"
            echo "$body" | jq -r '.analyse_traitements[] | "  - \(.nom)"' 2>/dev/null
        fi
        
        cost=$(echo "$body" | jq -r '._cost' 2>/dev/null)
        if [ "$cost" != "null" ] && [ "$cost" != "" ]; then
            echo ""
            echo "💰 Coût: \$$cost USD"
        fi
    fi
else
    echo "❌ Erreur HTTP $http_code"
    echo ""
    echo "Réponse:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
fi

echo ""
echo "=============================================="
