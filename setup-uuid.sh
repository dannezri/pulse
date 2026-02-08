#!/bin/bash
# Script de configuration UUID pour Pulse
# Usage: ./setup-uuid.sh <votre-uuid-supabase>

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔧 Configuration UUID Utilisateur - Pulse    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier l'argument
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erreur: UUID manquant${NC}"
    echo ""
    echo "Usage:"
    echo "  ./setup-uuid.sh <votre-uuid-supabase>"
    echo ""
    echo "Exemple:"
    echo "  ./setup-uuid.sh bee9a055-9b10-47d7-b91d-d7f6081a63f1"
    exit 1
fi

UUID="$1"

# Valider le format UUID
if ! [[ "$UUID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo -e "${RED}❌ Erreur: Format UUID invalide${NC}"
    echo ""
    echo "Format attendu: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    echo "Exemple valide: bee9a055-9b10-47d7-b91d-d7f6081a63f1"
    exit 1
fi

echo -e "${GREEN}✅ UUID valide: ${UUID}${NC}"
echo ""

# 1. Configuration Backend (shell)
echo -e "${YELLOW}📝 Configuration Backend...${NC}"

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
else
    echo -e "${RED}❌ Aucun fichier de configuration shell trouvé${NC}"
    echo "   Créez manuellement: export DEV_USER_UUID=$UUID"
    exit 1
fi

# Vérifier si la variable existe déjà
if grep -q "DEV_USER_UUID" "$SHELL_RC"; then
    echo -e "${YELLOW}⚠️  DEV_USER_UUID existe déjà dans $SHELL_RC${NC}"
    read -p "   Voulez-vous le remplacer ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Supprimer l'ancienne ligne
        sed -i.bak '/DEV_USER_UUID/d' "$SHELL_RC"
        echo "export DEV_USER_UUID=$UUID" >> "$SHELL_RC"
        echo -e "${GREEN}✅ UUID mis à jour dans $SHELL_RC${NC}"
    else
        echo -e "${YELLOW}⏭️  Ignoré${NC}"
    fi
else
    echo "export DEV_USER_UUID=$UUID" >> "$SHELL_RC"
    echo -e "${GREEN}✅ UUID ajouté à $SHELL_RC${NC}"
fi

# Exporter pour la session courante
export DEV_USER_UUID="$UUID"
echo -e "${GREEN}✅ UUID exporté pour cette session${NC}"
echo ""

# 2. Configuration Mobile (app.json)
echo -e "${YELLOW}📱 Configuration Mobile...${NC}"

APP_JSON="mobile/app.json"

if [ ! -f "$APP_JSON" ]; then
    echo -e "${RED}❌ Fichier $APP_JSON introuvable${NC}"
    exit 1
fi

# Backup du fichier
cp "$APP_JSON" "$APP_JSON.bak"

# Utiliser Python pour modifier le JSON proprement
python3 << EOF
import json

with open('$APP_JSON', 'r') as f:
    data = json.load(f)

if 'extra' not in data['expo']:
    data['expo']['extra'] = {}

data['expo']['extra']['devUserUuid'] = '$UUID'

with open('$APP_JSON', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ UUID configuré dans mobile/app.json")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ mobile/app.json mis à jour${NC}"
    echo -e "${YELLOW}⚠️  Backup sauvegardé: mobile/app.json.bak${NC}"
else
    echo -e "${RED}❌ Erreur lors de la mise à jour de mobile/app.json${NC}"
    mv "$APP_JSON.bak" "$APP_JSON"
    exit 1
fi

echo ""

# 3. Vérification
echo -e "${YELLOW}🔍 Vérification...${NC}"

# Backend
if python3 -c "import sys; sys.path.insert(0, 'backend'); from user_config import get_dev_user_uuid; assert get_dev_user_uuid() == '$UUID'" 2>/dev/null; then
    echo -e "${GREEN}✅ Backend: UUID correctement configuré${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: Rechargez votre shell (source $SHELL_RC)${NC}"
fi

# Mobile
if grep -q "\"devUserUuid\": \"$UUID\"" "$APP_JSON"; then
    echo -e "${GREEN}✅ Mobile: UUID correctement configuré${NC}"
else
    echo -e "${RED}❌ Mobile: Erreur de configuration${NC}"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ✅ Configuration terminée !                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 Prochaines étapes:${NC}"
echo ""
echo "1. Rechargez votre shell:"
echo -e "   ${GREEN}source $SHELL_RC${NC}"
echo ""
echo "2. Redémarrez l'application mobile:"
echo -e "   ${GREEN}cd mobile && npx expo start${NC}"
echo ""
echo "3. Testez la configuration:"
echo -e "   ${GREEN}echo \$DEV_USER_UUID${NC}"
echo ""
echo -e "${BLUE}📚 Documentation complète: UUID_CONFIGURATION.md${NC}"
