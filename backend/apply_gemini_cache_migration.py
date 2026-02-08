#!/usr/bin/env python3
"""
Script pour appliquer la migration de la table de cache Gemini
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("🗄️  CRÉATION DE LA TABLE DE CACHE GEMINI")
print("=" * 80)

# Lire le fichier de migration
migration_file = "../database/migrations/20260204_create_gemini_cache.sql"

try:
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    print(f"\n📄 Lecture de la migration: {migration_file}")
    print(f"📏 Taille: {len(sql)} caractères")
    
    print("\n⚙️  Application de la migration...")
    
    # Exécuter le SQL (Supabase Python n'a pas de méthode directe pour SQL brut)
    # Il faut utiliser l'API REST ou le dashboard Supabase
    print("\n" + "=" * 80)
    print("⚠️  IMPORTANT")
    print("=" * 80)
    print("\nPour appliquer cette migration, vous devez :")
    print("\n1. Aller sur le dashboard Supabase:")
    print(f"   {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/editor")
    print("\n2. Aller dans l'onglet 'SQL Editor'")
    print("\n3. Créer une nouvelle query et coller le contenu de:")
    print(f"   {os.path.abspath(migration_file)}")
    print("\n4. Exécuter la query")
    print("\n" + "=" * 80)
    
    # Alternative : Utiliser la commande supabase CLI si installée
    print("\n💡 OU utiliser Supabase CLI:")
    print("\n  supabase db push --db-url <votre-database-url>")
    print("\n" + "=" * 80)
    
    print("\n✅ Migration prête à être appliquée")
    print("\nAprès application, la table 'gemini_explanations_cache' sera créée.")
    
except FileNotFoundError:
    print(f"\n❌ Fichier de migration non trouvé: {migration_file}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    sys.exit(1)
