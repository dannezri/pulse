#!/bin/bash

# Script de monitoring pour le service Oura Sync
# Usage: ./monitor_oura_sync.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 MONITORING OURA SYNC SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Vérifier le statut du service
echo "🔍 Statut du service:"
if launchctl list com.pulse.oura-sync &>/dev/null; then
    echo "  ✅ Service chargé et actif"
    launchctl list com.pulse.oura-sync | grep -E "Label|LastExitStatus|PID"
else
    echo "  ❌ Service non chargé"
fi
echo ""

# Vérifier les fichiers de log
echo "📁 Fichiers de log:"
if [ -f /tmp/oura_sync.error.log ]; then
    SIZE=$(wc -c < /tmp/oura_sync.error.log | awk '{print $1}')
    LINES=$(wc -l < /tmp/oura_sync.error.log | awk '{print $1}')
    echo "  📝 oura_sync.error.log"
    echo "     Taille: $SIZE bytes"
    echo "     Lignes: $LINES"
else
    echo "  ⚠️  oura_sync.error.log n'existe pas encore"
fi

if [ -f /tmp/oura_sync.log ]; then
    SIZE=$(wc -c < /tmp/oura_sync.log | awk '{print $1}')
    LINES=$(wc -l < /tmp/oura_sync.log | awk '{print $1}')
    echo "  📝 oura_sync.log"
    echo "     Taille: $SIZE bytes"
    echo "     Lignes: $LINES"
fi
echo ""

# Statistiques d'exécution
echo "📈 Statistiques d'exécution:"
if [ -f /tmp/oura_sync.error.log ]; then
    STARTS=$(grep -c "Starting FULL Oura" /tmp/oura_sync.error.log 2>/dev/null || echo "0")
    INSERTS=$(grep -c "HTTP/2 201 Created" /tmp/oura_sync.error.log 2>/dev/null || echo "0")
    ERRORS=$(grep -c "ERROR:" /tmp/oura_sync.error.log 2>/dev/null || echo "0")
    
    echo "  🚀 Exécutions: $STARTS"
    echo "  💾 Insertions: $INSERTS"
    echo "  ❌ Erreurs: $ERRORS"
else
    echo "  ⚠️  Aucune donnée disponible"
fi
echo ""

# Dernière exécution
echo "🕐 Dernière exécution:"
if [ -f /tmp/oura_sync.error.log ]; then
    LAST_START=$(grep "Starting FULL Oura" /tmp/oura_sync.error.log | tail -1)
    if [ -n "$LAST_START" ]; then
        echo "  $LAST_START"
    else
        echo "  ⚠️  Aucune exécution détectée"
    fi
else
    echo "  ⚠️  Pas de log disponible"
fi
echo ""

# Dernières lignes du log
echo "📄 Dernières lignes du log (10 dernières):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f /tmp/oura_sync.error.log ]; then
    tail -10 /tmp/oura_sync.error.log | while IFS= read -r line; do
        # Colorier les lignes importantes
        if echo "$line" | grep -q "ERROR"; then
            echo "  🔴 $line"
        elif echo "$line" | grep -q "Starting"; then
            echo "  🟢 $line"
        elif echo "$line" | grep -q "201 Created"; then
            echo "  ✅ $line"
        else
            echo "  $line"
        fi
    done
else
    echo "  ⚠️  Pas de log disponible"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Commandes utiles
echo "💡 Commandes utiles:"
echo "  • Logs en temps réel:     tail -f /tmp/oura_sync.error.log"
echo "  • Forcer une synchro:     launchctl start com.pulse.oura-sync"
echo "  • Redémarrer le service:  launchctl unload ~/Library/LaunchAgents/com.pulse.oura-sync.plist && launchctl load ~/Library/LaunchAgents/com.pulse.oura-sync.plist"
echo "  • Voir la doc complète:   cat /Users/dannezri/Desktop/Pulse/backend/LAUNCHD_SERVICE.md"
echo ""
