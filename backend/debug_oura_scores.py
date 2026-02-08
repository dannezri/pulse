#!/usr/bin/env python3
"""
Debug: Inspecte exactement quand les scores Oura sont enregistrés
"""

import os
import sys
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

from user_config import get_dev_user_uuid

USER_ID = get_dev_user_uuid()
TARGET_DATE = date(2026, 2, 3)  # Date où on sait qu'il y a un score d'énergie

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print("=" * 80)
print("🔍 DEBUG : Scores Oura - Quand sont-ils enregistrés ?")
print("=" * 80)
print(f"\n👤 User: {USER_ID}")
print(f"📅 Date cible: {TARGET_DATE}")
print("\n" + "=" * 80)

# Chercher sleep_score sur une large période
print("\n📊 1. SLEEP_SCORE - Sur 10 derniers jours:")
print("-" * 80)

start = datetime.combine(TARGET_DATE - timedelta(days=10), datetime.min.time())
end = datetime.combine(TARGET_DATE + timedelta(days=2), datetime.max.time())

try:
    result = supabase.table("biometrics") \
        .select("value, recorded_at, created_at") \
        .eq("user_id", USER_ID) \
        .eq("metric_type", "sleep_score") \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        print(f"\n✅ Trouvé {len(result.data)} sleep_score:")
        for row in result.data:
            value = row["value"]
            recorded_at = row["recorded_at"][:10]  # Date seulement
            created_at = row.get("created_at", "")[:10] if row.get("created_at") else "N/A"
            print(f"   - Valeur: {value:3d} | recorded_at: {recorded_at} | created_at: {created_at}")
        
        # Analyser la relation date target vs recorded_at
        print(f"\n💡 Analyse pour {TARGET_DATE}:")
        for row in result.data:
            recorded_date = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00")).date()
            value = row["value"]
            
            if recorded_date == TARGET_DATE:
                print(f"   ✅ Sleep Score {value} enregistré le MÊME JOUR ({recorded_date})")
            elif recorded_date == TARGET_DATE - timedelta(days=1):
                print(f"   ⚠️  Sleep Score {value} enregistré J-1 ({recorded_date})")
            elif recorded_date == TARGET_DATE + timedelta(days=1):
                print(f"   ⚠️  Sleep Score {value} enregistré J+1 ({recorded_date})")
            else:
                print(f"   📅 Sleep Score {value} enregistré le {recorded_date}")
    else:
        print("❌ Aucun sleep_score trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Chercher readiness_score
print("\n" + "=" * 80)
print("📊 2. READINESS_SCORE - Sur 10 derniers jours:")
print("-" * 80)

try:
    result = supabase.table("biometrics") \
        .select("value, recorded_at, created_at") \
        .eq("user_id", USER_ID) \
        .eq("metric_type", "readiness_score") \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        print(f"\n✅ Trouvé {len(result.data)} readiness_score:")
        for row in result.data:
            value = row["value"]
            recorded_at = row["recorded_at"][:10]
            created_at = row.get("created_at", "")[:10] if row.get("created_at") else "N/A"
            print(f"   - Valeur: {value:3d} | recorded_at: {recorded_at} | created_at: {created_at}")
        
        print(f"\n💡 Analyse pour {TARGET_DATE}:")
        for row in result.data:
            recorded_date = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00")).date()
            value = row["value"]
            
            if recorded_date == TARGET_DATE:
                print(f"   ✅ Readiness Score {value} enregistré le MÊME JOUR ({recorded_date})")
            elif recorded_date == TARGET_DATE - timedelta(days=1):
                print(f"   ⚠️  Readiness Score {value} enregistré J-1 ({recorded_date})")
            elif recorded_date == TARGET_DATE + timedelta(days=1):
                print(f"   ⚠️  Readiness Score {value} enregistré J+1 ({recorded_date})")
    else:
        print("❌ Aucun readiness_score trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Chercher activity_score
print("\n" + "=" * 80)
print("📊 3. ACTIVITY_SCORE - Sur 10 derniers jours:")
print("-" * 80)

try:
    result = supabase.table("biometrics") \
        .select("value, recorded_at, created_at") \
        .eq("user_id", USER_ID) \
        .eq("metric_type", "activity_score") \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        print(f"\n✅ Trouvé {len(result.data)} activity_score:")
        for row in result.data:
            value = row["value"]
            recorded_at = row["recorded_at"][:10]
            created_at = row.get("created_at", "")[:10] if row.get("created_at") else "N/A"
            print(f"   - Valeur: {value:3d} | recorded_at: {recorded_at} | created_at: {created_at}")
    else:
        print("❌ Aucun activity_score trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Chercher steps
print("\n" + "=" * 80)
print("📊 4. STEPS - Sur 10 derniers jours:")
print("-" * 80)

try:
    result = supabase.table("biometrics") \
        .select("value, recorded_at, created_at") \
        .eq("user_id", USER_ID) \
        .eq("metric_type", "steps") \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        print(f"\n✅ Trouvé {len(result.data)} steps:")
        for row in result.data[:5]:  # Montrer les 5 premiers
            value = row["value"]
            recorded_at = row["recorded_at"][:10]
            created_at = row.get("created_at", "")[:10] if row.get("created_at") else "N/A"
            print(f"   - Valeur: {value:6.0f} | recorded_at: {recorded_at} | created_at: {created_at}")
    else:
        print("❌ Aucun steps trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Chercher HRV
print("\n" + "=" * 80)
print("📊 5. HRV - Sur 10 derniers jours:")
print("-" * 80)

try:
    result = supabase.table("biometrics") \
        .select("value, recorded_at, created_at") \
        .eq("user_id", USER_ID) \
        .eq("metric_type", "hrv") \
        .gte("recorded_at", start.isoformat()) \
        .lte("recorded_at", end.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        print(f"\n✅ Trouvé {len(result.data)} hrv:")
        for row in result.data:
            value = row["value"]
            recorded_at = row["recorded_at"][:10]
            created_at = row.get("created_at", "")[:10] if row.get("created_at") else "N/A"
            print(f"   - Valeur: {value:5.1f}ms | recorded_at: {recorded_at} | created_at: {created_at}")
        
        print(f"\n💡 Analyse pour {TARGET_DATE}:")
        for row in result.data:
            recorded_date = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00")).date()
            value = row["value"]
            
            if recorded_date == TARGET_DATE:
                print(f"   ✅ HRV {value}ms enregistré le MÊME JOUR ({recorded_date})")
            elif recorded_date == TARGET_DATE - timedelta(days=1):
                print(f"   ⚠️  HRV {value}ms enregistré J-1 ({recorded_date})")
            elif recorded_date == TARGET_DATE + timedelta(days=1):
                print(f"   ⚠️  HRV {value}ms enregistré J+1 ({recorded_date})")
    else:
        print("❌ Aucun HRV trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Test de la requête actuelle de _get_biometrics
print("\n" + "=" * 80)
print("📊 6. TEST : Requête actuelle de _get_biometrics()")
print("-" * 80)

search_start = TARGET_DATE - timedelta(days=2)
search_end = TARGET_DATE

print(f"\n🔍 Recherche de {search_start} à {search_end}")

start_of_period = datetime.combine(search_start, datetime.min.time())
end_of_day = datetime.combine(search_end, datetime.max.time())

try:
    result = supabase.table("biometrics") \
        .select("metric_type, value, recorded_at") \
        .eq("user_id", USER_ID) \
        .gte("recorded_at", start_of_period.isoformat()) \
        .lte("recorded_at", end_of_day.isoformat()) \
        .order("recorded_at", desc=True) \
        .execute()
    
    if result.data:
        # Compter par metric_type
        metric_counts = {}
        for row in result.data:
            mtype = row["metric_type"]
            metric_counts[mtype] = metric_counts.get(mtype, 0) + 1
        
        print(f"\n✅ Trouvé {len(result.data)} entrées totales")
        print(f"\n📋 Metric types trouvés:")
        for mtype, count in sorted(metric_counts.items()):
            if mtype in ["sleep_score", "readiness_score", "activity_score", "steps", "hrv"]:
                status = "🎯"
            else:
                status = "  "
            print(f"   {status} {mtype:30s} : {count:4d} entrée(s)")
    else:
        print("❌ Aucune donnée trouvée")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 80)
print("💡 CONCLUSION")
print("=" * 80)
print("\nSi les scores Oura ne sont PAS dans la requête de _get_biometrics(),")
print("cela signifie qu'ils sont enregistrés avec un 'recorded_at' HORS de la")
print("période de recherche (J-2 à J).")
print("\nSolution possible:")
print("  1. Élargir la fenêtre de recherche (J-7 à J)")
print("  2. Ou utiliser created_at au lieu de recorded_at")
print("\n" + "=" * 80)
