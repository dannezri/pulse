#!/bin/bash

# Script pour enregistrer un utilisateur Oura
# Usage: ./run_register_oura.sh

# Charger les variables d'environnement
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Exécuter le script Python
python3 register_oura_user.py
