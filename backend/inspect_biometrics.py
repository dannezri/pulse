#!/usr/bin/env python3
"""
Script simple pour inspecter les données biométriques disponibles
"""

import os
from datetime import date, datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Config
from user_config import get_dev_user_uuid

USER_ID = get_dev_user_uuid()
TARGET_DATE = date.today()

# Connexion Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print("=" * 80)
print(f"🔍 INSPECTION DES DONNÉES BIOMÉTRIQUES")
print(f"👤 User: {USER_ID}")
print(f"📅 Date: {TARGET_DATE}")
print("=" * 80)

# 1. Lister tous les metric_type disponibles pour cette date
print("\n📊 1. METRIC TYPES disponibles pour cette date:")
print("-" * 80)

start_of_day = datetime.combine(TARGET_DATE, datetime.min.time())
end_of_day = datetime.combine(TARGET_DATE, datetime.max.time())

result = supabase.table("biometrics") \
    .select("metric_type, value, recorded_at") \
    .eq("user_id", USER_ID) \
    .gte("recorded_at", start_of_day.isoformat()) \
    .lte("recorded_at", end_of_day.isoformat()) \
    .execute()

if result.data:
    print(f"\n✅ Trouvé {len(result.data)} entrées")
    
    # Grouper par metric_type
    metrics = {}
    for row in result.data:
        mtype = row["metric_type"]
        if mtype not in metrics:
            metrics[mtype] = []
        metrics[mtype].append({
            "value": row["value"],
            "time": row["recorded_at"]
        })
    
    print("\n📋 Liste des metric_type:")
    for mtype in sorted(metrics.keys()):
        count = len(metrics[mtype])
        sample_value = metrics[mtype][0]["value"]
        print(f"   - {mtype:30s} : {count} entrée(s), ex: {sample_value}")
else:
    print("❌ Aucune donnée trouvée")

# 2. Vérifier les baselines
print("\n" + "=" * 80)
print("📊 2. BASELINES UTILISATEUR:")
print("-" * 80)

baseline_result = supabase.table("user_baselines") \
    .select("baseline_type, baseline_data, confidence") \
    .eq("user_id", USER_ID) \
    .execute()

if baseline_result.data:
    print(f"\n✅ Trouvé {len(baseline_result.data)} baseline(s)")
    for row in baseline_result.data:
        btype = row["baseline_type"]
        bdata = row["baseline_data"]
        conf = row.get("confidence", 0)
        value = bdata.get("value") if isinstance(bdata, dict) else None
        print(f"   - {btype:20s} : {value} (confiance: {conf:.2f})")
else:
    print("❌ Aucune baseline trouvée")

# 3. Suggestions
print("\n" + "=" * 80)
print("💡 SUGGESTIONS POUR MODIFIER _get_biometrics():")
print("-" * 80)

if result.data:
    print("\nAjustez les noms de metric_type dans explain_service.py :")
    print("\nDans la fonction _get_biometrics(), remplacez :")
    print('   .eq("metric_type", "hrv")')
    print("par un des types trouvés ci-dessus (ex: 'heart_rate_variability', 'oura_hrv', etc.)")
    
print("\n" + "=" * 80)
