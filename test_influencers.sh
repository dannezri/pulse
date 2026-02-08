#!/bin/bash

# Test des influencers pour l'utilisateur c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd

echo "🧪 Test de l'endpoint /api/energy/intraday avec force_refresh..."
echo ""

# Utiliser un token valide (service role key)
curl -s "http://localhost:9000/api/energy/intraday?force_refresh=true&model=heuristic" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNTU5ZmNkNy1mNmE2LTRhNGQtODAzNi1jOWM5ZDhiOGM3YmQiLCJleHAiOjk5OTk5OTk5OTl9.fake" \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    influencers = data.get('influencers', [])
    print(f'✅ Nombre d\\'influencers: {len(influencers)}')
    print('')
    if influencers:
        print('📊 Détail des influencers:')
        for inf in influencers:
            print(f'  - {inf.get(\"name\")}: {inf.get(\"impact\")} ({inf.get(\"type\")})')
    else:
        print('❌ Aucun influencer trouvé!')
    print('')
    print('🔍 Clés disponibles:', list(data.keys()))
except Exception as e:
    print(f'❌ Erreur: {e}')
    sys.exit(1)
"

echo ""
echo "✅ Test terminé"
