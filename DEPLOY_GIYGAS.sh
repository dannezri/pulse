#!/bin/bash

# ============================================
# Script de déploiement API Giygas
# ============================================
# Date: 4 Février 2026
# Usage: ./DEPLOY_GIYGAS.sh
# ============================================

set -e  # Arrêter en cas d'erreur

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "🚀 Déploiement API Giygas Medications"
echo "================================================"
echo ""

# ============================================
# ÉTAPE 1 : Vérifications préalables
# ============================================

echo -e "${BLUE}ÉTAPE 1/5 : Vérifications préalables${NC}"
echo ""

# Vérifier que les fichiers existent
echo "Vérification des fichiers..."

if [ ! -f "backend/giygas_medication_service.py" ]; then
    echo -e "${RED}❌ Fichier manquant: backend/giygas_medication_service.py${NC}"
    exit 1
fi

if [ ! -f "database/migrations/034_giygas_medications_refactor.sql" ]; then
    echo -e "${RED}❌ Fichier manquant: database/migrations/034_giygas_medications_refactor.sql${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tous les fichiers présents${NC}"
echo ""

# Vérifier variables d'environnement
echo "Vérification des variables d'environnement..."

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${YELLOW}⚠️ Variables Supabase non définies${NC}"
    echo "Assurez-vous que SUPABASE_URL et SUPABASE_SERVICE_KEY sont configurés"
    echo ""
fi

echo -e "${GREEN}✅ Vérifications terminées${NC}"
echo ""

# ============================================
# ÉTAPE 2 : Migration base de données
# ============================================

echo -e "${BLUE}ÉTAPE 2/5 : Migration base de données${NC}"
echo ""

echo "📋 Migration à appliquer: database/migrations/034_giygas_medications_refactor.sql"
echo ""
echo "Cette migration va :"
echo "  - Créer la table drug_presentations (CIP13/CIP7, prix)"
echo "  - Étendre medication_details (composition, conditions)"
echo "  - Créer la fonction gtin_to_cip13()"
echo "  - Créer la vue medications_full"
echo ""

read -p "Appliquer la migration maintenant ? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Application de la migration..."
    
    # Option 1 : Via psql (si DATABASE_URL défini)
    if [ -n "$DATABASE_URL" ]; then
        psql "$DATABASE_URL" -f database/migrations/034_giygas_medications_refactor.sql
        echo -e "${GREEN}✅ Migration appliquée via psql${NC}"
    else
        echo -e "${YELLOW}⚠️ DATABASE_URL non défini${NC}"
        echo ""
        echo "Appliquez manuellement la migration via Supabase Dashboard :"
        echo "1. Ouvrir https://app.supabase.com"
        echo "2. SQL Editor → New Query"
        echo "3. Copier-coller le contenu de database/migrations/034_giygas_medications_refactor.sql"
        echo "4. Run"
        echo ""
        read -p "Migration appliquée manuellement ? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Déploiement annulé${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️ Migration ignorée${NC}"
    echo "Pensez à l'appliquer avant de continuer"
fi

echo ""

# ============================================
# ÉTAPE 3 : Vérification migration
# ============================================

echo -e "${BLUE}ÉTAPE 3/5 : Vérification migration${NC}"
echo ""

if [ -n "$DATABASE_URL" ]; then
    echo "Vérification de la table drug_presentations..."
    
    TABLE_EXISTS=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'drug_presentations');" | xargs)
    
    if [ "$TABLE_EXISTS" == "t" ]; then
        echo -e "${GREEN}✅ Table drug_presentations créée${NC}"
    else
        echo -e "${RED}❌ Table drug_presentations non trouvée${NC}"
        exit 1
    fi
    
    echo "Vérification de la fonction gtin_to_cip13()..."
    
    FUNCTION_RESULT=$(psql "$DATABASE_URL" -t -c "SELECT gtin_to_cip13('34009300015517');" | xargs)
    
    if [ "$FUNCTION_RESULT" == "3400930001551" ]; then
        echo -e "${GREEN}✅ Fonction gtin_to_cip13() fonctionne${NC}"
    else
        echo -e "${RED}❌ Fonction gtin_to_cip13() erreur (résultat: $FUNCTION_RESULT)${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Vérification DB ignorée (DATABASE_URL non défini)${NC}"
    echo "Vérifiez manuellement que :"
    echo "  - Table drug_presentations existe"
    echo "  - Fonction gtin_to_cip13() fonctionne"
fi

echo ""

# ============================================
# ÉTAPE 4 : Redémarrage backend
# ============================================

echo -e "${BLUE}ÉTAPE 4/5 : Redémarrage backend${NC}"
echo ""

echo "Arrêt du backend actuel..."

# Chercher processus Python api_server
BACKEND_PID=$(pgrep -f "python.*api_server" || true)

if [ -n "$BACKEND_PID" ]; then
    echo "Arrêt du processus $BACKEND_PID..."
    kill $BACKEND_PID
    sleep 2
    echo -e "${GREEN}✅ Backend arrêté${NC}"
else
    echo -e "${YELLOW}⚠️ Aucun backend en cours d'exécution${NC}"
fi

echo ""
echo "Démarrage du nouveau backend..."

cd backend

# Vérifier si venv existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Démarrer en background
nohup python api_server.py > ../backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend démarré (PID: $BACKEND_PID)"
echo "Logs: backend.log"

# Attendre que le backend soit prêt
echo "Attente du démarrage (5 secondes)..."
sleep 5

# Vérifier que le backend répond
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend démarré avec succès${NC}"
else
    echo -e "${YELLOW}⚠️ Backend démarré mais endpoint /health non accessible${NC}"
    echo "Vérifiez les logs: tail -f backend.log"
fi

cd ..

echo ""

# ============================================
# ÉTAPE 5 : Tests de validation
# ============================================

echo -e "${BLUE}ÉTAPE 5/5 : Tests de validation${NC}"
echo ""

echo "Exécution des tests..."
echo ""

if [ -f "test-giygas-api.sh" ]; then
    chmod +x test-giygas-api.sh
    ./test-giygas-api.sh
else
    echo -e "${YELLOW}⚠️ Script test-giygas-api.sh non trouvé${NC}"
    echo "Tests manuels :"
    echo ""
    echo "1. Test recherche :"
    echo "   curl http://localhost:9000/api/medications/search?q=doliprane"
    echo ""
    echo "2. Test détails :"
    echo "   curl http://localhost:9000/api/medications/60001551"
    echo ""
    echo "3. Test scan :"
    echo "   curl -X POST http://localhost:9000/api/medications/scan -H 'Content-Type: application/json' -d '{\"gtin\": \"34009300015517\"}'"
fi

echo ""

# ============================================
# RÉSUMÉ
# ============================================

echo ""
echo "================================================"
echo "✅ Déploiement terminé"
echo "================================================"
echo ""
echo "📝 Résumé des changements :"
echo "  - API Giygas intégrée (giygas_medication_service.py)"
echo "  - Table drug_presentations créée (CIP13/CIP7, prix)"
echo "  - Fonction gtin_to_cip13() disponible"
echo "  - Endpoints /api/medications/* mis à jour"
echo "  - Nouveau endpoint /api/medications/scan (GS1 DataMatrix)"
echo ""
echo "📚 Documentation :"
echo "  - Guide complet : GIYGAS_MIGRATION_GUIDE.md"
echo "  - Résumé : REFACTORING_SUMMARY.md"
echo ""
echo "🧪 Tests :"
echo "  - Script : ./test-giygas-api.sh"
echo "  - Tests unitaires : pytest backend/tests/test_giygas_medication_service.py"
echo ""
echo "📊 Prochaines étapes :"
echo "  1. Tester recherche avec plusieurs médicaments"
echo "  2. Tester scan code-barres avec GTIN réels"
echo "  3. Adapter frontend mobile (composition, présentations)"
echo "  4. (Optionnel) Migrer données BDPM → Giygas : python backend/migrate_bdpm_to_giygas.py --dry-run"
echo ""
echo "🎯 Ancien service BDPM :"
echo "  - Fichier : backend/medication_service.py"
echo "  - Statut : Obsolète (marqué comme LEGACY)"
echo "  - Action : Peut être supprimé après validation complète"
echo ""
echo "================================================"
echo ""
