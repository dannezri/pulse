#!/usr/bin/env python3
"""
Force la synchronisation des données Oura pour les 7 derniers jours
Usage: python3 force_sync_oura_today.py
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer le module d'import complet
from import_oura_data_full import OuraDataImporterFull
from supabase_client import SupabaseClient
from oura_token_utils import get_user_oura_token

# Configuration
from user_config import get_dev_user_uuid
USER_UUID = get_dev_user_uuid()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
    sys.exit(1)

# Récupérer le token Oura depuis Supabase
supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
OURA_TOKEN = get_user_oura_token(supabase, USER_UUID)

if not OURA_TOKEN:
    print(f"❌ Aucun token Oura trouvé pour l'utilisateur {USER_UUID}")
    print("   Exécutez d'abord: python register_oura_user.py")
    sys.exit(1)

print("=" * 80)
print("🔄 SYNCHRONISATION FORCÉE DES DONNÉES OURA")
print("=" * 80)
print(f"\n👤 User: {USER_UUID}")
print(f"📅 Période: 7 derniers jours")
print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n" + "=" * 80)

# Créer l'importeur
print("\n📡 Connexion à l'API Oura...")
importer = OuraDataImporterFull(
    oura_token=OURA_TOKEN,
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY
)

# Importer les 7 derniers jours (pour capturer les données récentes)
print("\n🔄 Import des données en cours...")
print("   (Cela peut prendre 30-60 secondes)\n")

importer.import_all_data(
    user_id=USER_UUID,
    days_back=7  # 7 derniers jours seulement
)

print("\n" + "=" * 80)
print("✅ SYNCHRONISATION TERMINÉE")
print("=" * 80)
print("\n💡 Prochaines étapes:")
print("   1. Vérifier que les données sont dans Supabase:")
print("      python3 inspect_biometrics.py")
print("\n   2. Redémarrer le backend:")
print("      cd /Users/dannezri/Desktop/Pulse && ./restart_api_server.sh")
print("\n   3. Tester dans l'app mobile")
print("\n" + "=" * 80)
