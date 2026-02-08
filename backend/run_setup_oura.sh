#!/bin/bash

# Script de configuration complète Oura
# Usage: ./run_setup_oura.sh

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Exécuter le script Python
python3 setup_oura_complete.py
