#!/bin/bash
# Test rapide des endpoints API après les corrections

echo "============================================"
echo "TEST RAPIDE API - Pulse Energy Decay"
echo "============================================"

API_URL="http://localhost:9000"
USER_TOKEN="c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"

echo ""
echo "1️⃣  Test /api/energy/intraday (Pulse Energy Decay V2)"
echo "-------------------------------------------"
curl -s "${API_URL}/api/energy/intraday?model=pulse_energy_decay_v1&force_refresh=true" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  | jq '{type, current_energy, calculation_model, influencers: (.influencers | length)}'

echo ""
echo ""
echo "2️⃣  Test /api/oura/status"
echo "-------------------------------------------"
curl -s "${API_URL}/api/oura/status" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  | jq '.'

echo ""
echo ""
echo "3️⃣  Test /api/v1/generate-brief (devrait inclure intraday_forecast)"
echo "-------------------------------------------"
curl -s -X POST "${API_URL}/api/v1/generate-brief" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -d '{"user_id": "'${USER_TOKEN}'", "force_refresh": true}' \
  | jq '{status, pulseScore, cached, has_intraday: (.intraday_energy_forecast != null)}'

echo ""
echo ""
echo "============================================"
echo "✅ Tests terminés"
echo "============================================"
