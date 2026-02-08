#!/usr/bin/env python3
"""
Script pour localiser les données Oura dans Supabase
"""

import os
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

from user_config import get_dev_user_uuid

USER_ID = get_dev_user_uuid()
TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print("=" * 80)
print("🔍 RECHERCHE DES DONNÉES OURA")
print("=" * 80)

# 1. Chercher dans biometrics sur plusieurs jours
print("\n📊 1. Table BIOMETRICS (derniers 7 jours):")
print("-" * 80)

for days_ago in range(7):
    check_date = TODAY - timedelta(days=days_ago)
    start = datetime.combine(check_date, datetime.min.time())
    end = datetime.combine(check_date, datetime.max.time())
    
    result = supabase.table("biometrics") \
        .select("metric_type") \
        .eq("user_id", USER_ID) \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .execute()
    
    if result.data:
        metric_types = set(row["metric_type"] for row in result.data)
        print(f"📅 {check_date}: {len(result.data)} entrées - {', '.join(sorted(metric_types))}")
    else:
        print(f"📅 {check_date}: Aucune donnée")

# 2. Chercher des tables Oura spécifiques
print("\n" + "=" * 80)
print("📊 2. TABLES OURA POTENTIELLES:")
print("-" * 80)

oura_tables = [
    "oura_sleep",
    "oura_readiness", 
    "oura_activity",
    "sleep_data",
    "readiness_data",
    "activity_data",
    "daily_sleep",
    "daily_readiness",
    "daily_activity"
]

for table_name in oura_tables:
    try:
        result = supabase.table(table_name) \
            .select("*") \
            .eq("user_id", USER_ID) \
            .limit(1) \
            .execute()
        
        if result.data:
            print(f"✅ {table_name:25s} : Table existe avec données")
            # Afficher les colonnes disponibles
            if result.data:
                cols = list(result.data[0].keys())
                print(f"   Colonnes: {', '.join(cols[:10])}...")
        else:
            print(f"⚠️  {table_name:25s} : Table existe mais vide")
    except Exception as e:
        print(f"❌ {table_name:25s} : Table n'existe pas ou erreur")

# 3. Chercher les dernières données avec HRV dans biometrics
print("\n" + "=" * 80)
print("📊 3. DERNIÈRES DONNÉES HRV dans biometrics:")
print("-" * 80)

# Chercher sur les 30 derniers jours
start = datetime.combine(TODAY - timedelta(days=30), datetime.min.time())

for metric in ["hrv", "hrv_night", "heart_rate_variability", "oura_hrv"]:
    try:
        result = supabase.table("biometrics") \
            .select("recorded_at, value") \
            .eq("user_id", USER_ID) \
            .eq("metric_type", metric) \
            .gte("recorded_at", start.isoformat()) \
            .order("recorded_at", desc=True) \
            .limit(5) \
            .execute()
        
        if result.data:
            print(f"\n✅ Trouvé '{metric}':")
            for row in result.data:
                date_str = row["recorded_at"][:10]
                value = row["value"]
                print(f"   - {date_str}: {value}ms")
    except Exception as e:
        pass

# 4. Vérifier sleep_score
print("\n" + "=" * 80)
print("📊 4. DERNIÈRES DONNÉES SLEEP_SCORE dans biometrics:")
print("-" * 80)

for metric in ["sleep_score", "oura_sleep_score", "sleep", "sleep_quality"]:
    try:
        result = supabase.table("biometrics") \
            .select("recorded_at, value") \
            .eq("user_id", USER_ID) \
            .eq("metric_type", metric) \
            .gte("recorded_at", start.isoformat()) \
            .order("recorded_at", desc=True) \
            .limit(5) \
            .execute()
        
        if result.data:
            print(f"\n✅ Trouvé '{metric}':")
            for row in result.data:
                date_str = row["recorded_at"][:10]
                value = row["value"]
                print(f"   - {date_str}: {value}")
    except Exception as e:
        pass

print("\n" + "=" * 80)
print("💡 CONCLUSION:")
print("-" * 80)
print("\nSi aucune donnée HRV/Sleep n'est trouvée :")
print("1. Vérifiez que la bague Oura est bien synchronisée")
print("2. Les données Oura arrivent généralement le matin pour la nuit précédente")
print("3. Consultez l'app Oura pour voir si les données sont disponibles")
print("\n" + "=" * 80)
