#!/usr/bin/env python3
"""
Script de vérification de la configuration FatSecret
Usage: python3 check_fatsecret_config.py
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=" * 60)
print("VÉRIFICATION DE LA CONFIGURATION FATSECRET")
print("=" * 60)
print()

# Variables à vérifier
config = {
    "FATSECRET_CONSUMER_KEY": os.getenv("FATSECRET_CONSUMER_KEY"),
    "FATSECRET_CONSUMER_SECRET": os.getenv("FATSECRET_CONSUMER_SECRET"),
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY"),
}

all_ok = True

for var_name, var_value in config.items():
    if var_value:
        # Afficher les 10 premiers caractères seulement
        preview = var_value[:20] + "..." if len(var_value) > 20 else var_value
        print(f"✅ {var_name:30s} = {preview}")
    else:
        print(f"❌ {var_name:30s} = NON DÉFINIE")
        all_ok = False

print()
print("=" * 60)

if all_ok:
    print("✅ Configuration complète ! Vous pouvez lancer:")
    print("   python3 setup_fatsecret.py")
    print("=" * 60)
else:
    print("❌ Configuration incomplète. Veuillez ajouter les variables")
    print("   manquantes dans votre fichier .env")
    print()
    print("Exemple à ajouter dans backend/.env:")
    print()
    if not config["FATSECRET_CONSUMER_KEY"]:
        print("FATSECRET_CONSUMER_KEY=your_consumer_key_here")
    if not config["FATSECRET_CONSUMER_SECRET"]:
        print("FATSECRET_CONSUMER_SECRET=your_consumer_secret_here")
    if not config["SUPABASE_URL"]:
        print("SUPABASE_URL=https://your-project.supabase.co")
    if not config["SUPABASE_SERVICE_KEY"]:
        print("SUPABASE_SERVICE_KEY=your_service_role_key")
    print()
    print("Pour obtenir vos credentials FatSecret:")
    print("https://platform.fatsecret.com/api/")
    print("=" * 60)
