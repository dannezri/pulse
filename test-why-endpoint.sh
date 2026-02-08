#!/bin/bash

# Test de l'endpoint Why-Stack
USER_ID="c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
API_URL="http://localhost:8001"

echo "🧪 Test de l'endpoint /api/energy/explain/${USER_ID}"
echo "================================================"
echo ""

# Faire une requête GET
curl -X GET \
  "${API_URL}/api/energy/explain/${USER_ID}" \
  -H "Authorization: Bearer ${USER_ID}" \
  -H "Content-Type: application/json" \
  -v

echo ""
echo "================================================"
