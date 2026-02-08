#!/usr/bin/env python3
"""
Script pour appliquer la migration FatSecret dans Supabase
Usage: python3 apply_fatsecret_migration.py
"""

import os
from dotenv import load_dotenv
from supabase_client import SupabaseClient

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL et SUPABASE_SERVICE_KEY requis dans .env")
    exit(1)

# Lire la migration SQL
with open("../database/migrations/018_fatsecret_integration.sql", "r") as f:
    migration_sql = f.read()

print("=" * 70)
print("APPLICATION DE LA MIGRATION FATSECRET")
print("=" * 70)
print()
print("⚠️  IMPORTANT:")
print("   Ce script ne peut pas exécuter du SQL directement via l'API Supabase.")
print("   Vous devez appliquer la migration manuellement.")
print()
print("=" * 70)
print("ÉTAPES À SUIVRE:")
print("=" * 70)
print()
print("1. Ouvrez https://supabase.com/dashboard")
print("2. Sélectionnez votre projet Pulse")
print("3. Allez dans 'SQL Editor'")
print("4. Copiez/collez le contenu de:")
print(f"   database/migrations/018_fatsecret_integration.sql")
print()
print("5. Cliquez sur 'Run' pour exécuter la migration")
print()
print("=" * 70)
print()

response = input("Avez-vous appliqué la migration ? (y/n): ").strip().lower()

if response == 'y':
    print()
    print("✅ Parfait ! Vous pouvez maintenant utiliser setup_fatsecret.py")
    print()
    print("Prochaine étape:")
    print("  python3 setup_fatsecret.py")
    print()
else:
    print()
    print("❌ Veuillez d'abord appliquer la migration SQL.")
    print()
    exit(1)
