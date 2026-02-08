#!/bin/bash

# ============================================
# Script de test API Giygas Medications
# ============================================
# Date: 4 Février 2026
# Usage: ./test-giygas-api.sh
# ============================================

BASE_URL="http://localhost:9000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "🧪 Tests API Giygas Medications"
echo "================================================"
echo ""

# ============================================
# TEST 1 : Recherche médicaments
# ============================================

echo -e "${YELLOW}TEST 1: Recherche 'doliprane'${NC}"
echo "GET $BASE_URL/api/medications/search?q=doliprane"
echo ""

RESPONSE=$(curl -s "$BASE_URL/api/medications/search?q=doliprane")
echo "$RESPONSE" | jq '.'

# Vérifier si la réponse contient des résultats
COUNT=$(echo "$RESPONSE" | jq -r '.count // 0')
if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ TEST 1 PASSED - $COUNT résultats trouvés${NC}"
else
    echo -e "${RED}❌ TEST 1 FAILED - Aucun résultat${NC}"
fi

echo ""
echo "------------------------------------------------"
echo ""

# ============================================
# TEST 2 : Détails d'un médicament par CIS
# ============================================

# Extraire le CIS du premier résultat
CIS=$(echo "$RESPONSE" | jq -r '.results[0].cis // "60001551"')

echo -e "${YELLOW}TEST 2: Détails médicament CIS ${CIS}${NC}"
echo "GET $BASE_URL/api/medications/$CIS"
echo ""

DETAILS=$(curl -s "$BASE_URL/api/medications/$CIS")
echo "$DETAILS" | jq '.'

# Vérifier présence composition
HAS_COMPOSITION=$(echo "$DETAILS" | jq -r '.composition // [] | length')
if [ "$HAS_COMPOSITION" -gt 0 ]; then
    echo -e "${GREEN}✅ TEST 2 PASSED - Composition présente ($HAS_COMPOSITION substances)${NC}"
else
    echo -e "${RED}❌ TEST 2 FAILED - Composition manquante${NC}"
fi

echo ""
echo "------------------------------------------------"
echo ""

# ============================================
# TEST 3 : Scan code-barres GS1 (GTIN → CIP13)
# ============================================

echo -e "${YELLOW}TEST 3: Scan code-barres GTIN${NC}"
echo "POST $BASE_URL/api/medications/scan"
echo "Body: {\"gtin\": \"03400927562396\"}"
echo ""

SCAN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/medications/scan" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "03400927562396"}')

echo "$SCAN_RESPONSE" | jq '.'

# Vérifier conversion GTIN → CIP13 et médicament trouvé
CIP13=$(echo "$SCAN_RESPONSE" | jq -r '.cip13 // ""')
MED_CIS=$(echo "$SCAN_RESPONSE" | jq -r '.medication.cis // ""')
if [ "$CIP13" == "3400927562396" ] && [ "$MED_CIS" == "60904643" ]; then
    echo -e "${GREEN}✅ TEST 3 PASSED - GTIN converti en CIP13: $CIP13, Médicament: $MED_CIS${NC}"
else
    echo -e "${RED}❌ TEST 3 FAILED - Conversion GTIN échouée (attendu CIP13: 3400927562396, reçu: $CIP13)${NC}"
fi

echo ""
echo "------------------------------------------------"
echo ""

# ============================================
# TEST 4 : Vérification DB (fonction gtin_to_cip13)
# ============================================

echo -e "${YELLOW}TEST 4: Fonction SQL gtin_to_cip13()${NC}"
echo "SQL: SELECT gtin_to_cip13('34009300015517');"
echo ""

# Note: Nécessite accès Supabase ou connexion PostgreSQL
# Exemple avec psql (à adapter selon votre config)

if command -v psql &> /dev/null; then
    DB_URL="${DATABASE_URL:-}"
    
    if [ -n "$DB_URL" ]; then
        SQL_RESULT=$(psql "$DB_URL" -t -c "SELECT gtin_to_cip13('34009300015517');")
        SQL_RESULT_CLEAN=$(echo "$SQL_RESULT" | xargs)
        
        if [ "$SQL_RESULT_CLEAN" == "3400930001551" ]; then
            echo -e "${GREEN}✅ TEST 4 PASSED - Fonction SQL OK: $SQL_RESULT_CLEAN${NC}"
        else
            echo -e "${RED}❌ TEST 4 FAILED - Résultat: $SQL_RESULT_CLEAN${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ TEST 4 SKIPPED - DATABASE_URL non défini${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ TEST 4 SKIPPED - psql non installé${NC}"
fi

echo ""
echo "------------------------------------------------"
echo ""

# ============================================
# TEST 5 : Cache (2ème recherche identique)
# ============================================

echo -e "${YELLOW}TEST 5: Cache (2ème recherche 'doliprane')${NC}"
echo "GET $BASE_URL/api/medications/search?q=doliprane (2ème fois)"
echo ""

START_TIME=$(date +%s%N)
CACHE_RESPONSE=$(curl -s "$BASE_URL/api/medications/search?q=doliprane")
END_TIME=$(date +%s%N)

DURATION=$(( ($END_TIME - $START_TIME) / 1000000 ))  # ms

echo "$CACHE_RESPONSE" | jq '.'
echo ""
echo "Temps de réponse: ${DURATION}ms"

if [ "$DURATION" -lt 500 ]; then
    echo -e "${GREEN}✅ TEST 5 PASSED - Cache fonctionne (réponse rapide: ${DURATION}ms)${NC}"
else
    echo -e "${YELLOW}⚠️ TEST 5 WARNING - Réponse lente (${DURATION}ms), cache peut-être non utilisé${NC}"
fi

echo ""
echo "================================================"
echo "🎯 Résumé des Tests"
echo "================================================"
echo ""
echo "Tests passés : Vérifiez les ✅ ci-dessus"
echo "Tests échoués : Vérifiez les ❌ ci-dessus"
echo ""
echo "📝 Notes:"
echo "- Si tous les tests passent : Migration réussie !"
echo "- Si TEST 4 est skipped : Normal si DATABASE_URL non défini"
echo "- Si TEST 3 échoue : Vérifier migration 034 appliquée"
echo "- Si TEST 1/2 échouent : Vérifier API Giygas accessible"
echo ""
echo "📚 Documentation complète : GIYGAS_MIGRATION_GUIDE.md"
echo ""
