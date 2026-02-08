#!/usr/bin/env python3
"""
Wrapper pour lancer la synchronisation Oura avec chargement automatique du .env
Ce script est conçu pour être appelé par launchd

Usage:
    python run_oura_sync.py
    python run_oura_sync.py --user-id UUID
    python run_oura_sync.py --user-id UUID --oura-client-id ID --oura-client-secret SECRET
"""

import os
import sys
import argparse
from pathlib import Path

# Changer vers le répertoire du script
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Charger les variables d'environnement depuis .env
env_file = script_dir / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Parser les arguments
parser = argparse.ArgumentParser(description="Synchroniser les données Oura pour un utilisateur")
parser.add_argument(
    '--user-id',
    type=str,
    help='UUID de l\'utilisateur Supabase (défaut: depuis DEV_USER_UUID env var)'
)
parser.add_argument(
    '--oura-client-id',
    type=str,
    help='OAuth2 Client ID Oura (optionnel, sinon utilise OURA_CLIENT_ID du .env)'
)
parser.add_argument(
    '--oura-client-secret',
    type=str,
    help='OAuth2 Client Secret Oura (optionnel, sinon utilise OURA_CLIENT_SECRET du .env)'
)

args = parser.parse_args()

# Récupérer l'UUID utilisateur (argument > env var)
user_id = args.user_id or os.getenv("DEV_USER_UUID")

if not user_id:
    print("❌ Erreur: UUID utilisateur requis")
    print()
    print("Fournissez l'UUID via:")
    print("  1. Argument: --user-id <uuid>")
    print("  2. Variable d'environnement: export DEV_USER_UUID=<uuid>")
    sys.exit(1)

# Surcharger les credentials Oura si fournis
if args.oura_client_id:
    os.environ['OURA_CLIENT_ID'] = args.oura_client_id
    print(f"✓ Utilisation du Client ID Oura fourni: {args.oura_client_id}")

if args.oura_client_secret:
    os.environ['OURA_CLIENT_SECRET'] = args.oura_client_secret
    print(f"✓ Utilisation du Client Secret Oura fourni: {args.oura_client_secret[:10]}...")

# Importer et exécuter le script principal
sys.path.insert(0, str(script_dir))

try:
    from import_oura_data_full import main
    main(user_id=user_id)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
