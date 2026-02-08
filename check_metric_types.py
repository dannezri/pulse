#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Récupérer les metric_types distincts pour cet utilisateur
import os
user_id = os.getenv("DEV_USER_UUID")

if not user_id:
    print("❌ DEV_USER_UUID doit être défini dans les variables d'environnement")
    print("   Exemple: export DEV_USER_UUID=votre-uuid")
    exit(1)

result = supabase.table("biometrics") \
    .select("metric_type, value, recorded_at") \
    .eq("user_id", user_id) \
    .order("recorded_at", desc=True) \
    .limit(100) \
    .execute()

# Grouper par metric_type
by_type = {}
for row in result.data:
    metric_type = row["metric_type"]
    if metric_type not in by_type:
        by_type[metric_type] = []
    by_type[metric_type].append(row)

print(f"📊 Metric types trouvés pour l'utilisateur {user_id}:\n")
for metric_type, rows in sorted(by_type.items()):
    latest = rows[0]
    print(f"  {metric_type:20} : {len(rows):3} entrées, dernière valeur: {latest['value']:6.1f} ({latest['recorded_at'][:10]})")

print("\n🔍 Détails HRV:")
if "hrv" in by_type:
    for row in by_type["hrv"][:5]:
        print(f"  - {row['recorded_at'][:19]} : {row['value']} ms")
else:
    print("  ❌ Aucune donnée HRV trouvée")

print("\n🔍 Détails RHR (tous les types contenant 'hr'):")
hr_types = [t for t in by_type.keys() if 'hr' in t.lower()]
for hr_type in sorted(hr_types):
    print(f"\n  Type: {hr_type}")
    for row in by_type[hr_type][:3]:
        print(f"    - {row['recorded_at'][:19]} : {row['value']} bpm")
