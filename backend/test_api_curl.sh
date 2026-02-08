#!/bin/bash
echo "🧪 Test de l'API Medication Analysis avec effets horaires"
echo "=========================================================="
echo ""
echo "📡 Appel API..."
curl -s -X GET \
  "http://192.168.0.23:9000/api/medications/analyze/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  -H "Content-Type: application/json" \
  | python3 -c "
import json
import sys

data = json.load(sys.stdin)

print('✅ Réponse reçue\n')
print(f'📊 Médicaments analysés: {data.get(\"_medications_count\", 0)}')
print(f'💰 Coût: \${data.get(\"_cost\", 0):.4f} USD')
print(f'📅 Généré à: {data.get(\"_generated_at\", \"N/A\")}\n')

analyses = data.get('analyse_traitements', [])
for i, med in enumerate(analyses, 1):
    print(f'🔹 Médicament {i}: {med.get(\"nom\", \"Inconnu\")}')
    
    effets_horaires = med.get('effets_horaires', [])
    if effets_horaires:
        print(f'   ✅ effets_horaires: {len(effets_horaires)} heures')
        if len(effets_horaires) > 0:
            first = effets_horaires[0]
            print(f'   📍 Exemple ({first[\"heure\"]}): concentration={first[\"concentration\"]}%, efficacite={first[\"efficacite\"]}%')
    else:
        print(f'   ❌ effets_horaires: MANQUANT')
    print()
"
