#!/bin/bash

# Script pour importer TOUTES les données Oura (version complète avec données brutes)
# Usage: ./run_oura_import_full.sh

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Exécuter le script Python
python3 import_oura_data_full.py
