#!/usr/bin/env python3
"""
Script pour extraire toutes les données de la page énergie pour l'utilisateur connecté
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from supabase_client import SupabaseClient
import requests

# Charger les variables d'environnement
load_dotenv()

API_URL = "http://localhost:9000"

# Initialiser le client Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables d'environnement SUPABASE_URL ou SUPABASE_SERVICE_KEY manquantes")
    sys.exit(1)

supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)

async def get_user_id():
    """Récupère l'ID de l'utilisateur connecté (le premier utilisateur actif)"""
    
    # Récupérer le premier utilisateur dans profiles
    response = supabase.client.table("profiles").select("id, full_name").limit(1).execute()
    
    if not response.data or len(response.data) == 0:
        print("❌ Aucun utilisateur trouvé dans la base de données")
        sys.exit(1)
    
    user_id = response.data[0]["id"]
    user_name = response.data[0].get("full_name", "N/A")
    print(f"✅ Utilisateur trouvé: {user_id} ({user_name})")
    return user_id

async def fetch_brief_data(user_id: str):
    """Récupère les données du brief via l'API"""
    print(f"\n📡 Appel API /api/v1/generate-brief...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/generate-brief",
            json={
                "user_id": user_id,
                "force_refresh": True
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur API: {response.status_code}")
            print(response.text)
            sys.exit(1)
        
        data = response.json()
        print(f"✅ Données récupérées (cached: {data.get('cached', False)})")
        return data
    
    except Exception as e:
        print(f"❌ Erreur lors de l'appel API: {e}")
        sys.exit(1)

async def fetch_biometrics_data(user_id: str):
    """Récupère les données biométriques de l'utilisateur"""
    print(f"\n📊 Récupération données biométriques...")
    
    # Récupérer les biométriques des 7 derniers jours
    biometrics = supabase.client.table("biometrics") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("recorded_at", desc=True) \
        .limit(200) \
        .execute()
    
    print(f"  ✅ Biométriques: {len(biometrics.data)} enregistrements")
    
    # Grouper par type de métrique
    by_type = {}
    for record in biometrics.data:
        metric_type = record.get("metric_type")
        if metric_type not in by_type:
            by_type[metric_type] = []
        by_type[metric_type].append(record)
    
    for metric_type, records in by_type.items():
        print(f"    - {metric_type}: {len(records)} valeurs")
    
    return {
        "all": biometrics.data,
        "by_type": by_type
    }

async def fetch_medications(user_id: str):
    """Récupère les médicaments de l'utilisateur"""
    print(f"\n💊 Récupération médicaments...")
    
    try:
        medications = supabase.client.table("user_medications") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("active", True) \
            .execute()
        
        print(f"  ✅ {len(medications.data)} médicaments actifs")
        return medications.data
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la récupération des médicaments: {e}")
        return []

async def fetch_conditions(user_id: str):
    """Récupère les conditions de santé de l'utilisateur"""
    print(f"\n🏥 Récupération conditions...")
    
    try:
        conditions = supabase.client.table("user_conditions") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("active", True) \
            .execute()
        
        print(f"  ✅ {len(conditions.data)} conditions actives")
        return conditions.data
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la récupération des conditions: {e}")
        return []

async def fetch_feedbacks(user_id: str):
    """Récupère les feedbacks de l'utilisateur"""
    print(f"\n💬 Récupération feedbacks...")
    
    try:
        feedbacks = supabase.client.table("user_feedback") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        
        print(f"  ✅ {len(feedbacks.data)} feedbacks")
        return feedbacks.data
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la récupération des feedbacks: {e}")
        return []

async def fetch_energy_profile(user_id: str):
    """Récupère le profil énergétique personnalisé"""
    print(f"\n🎯 Récupération profil énergétique...")
    
    try:
        profile = supabase.client.table("user_energy_profiles") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if profile.data:
            print(f"  ✅ Profil trouvé (version: {profile.data[0].get('version', 'N/A')})")
            return profile.data[0]
        else:
            print(f"  ⚠️  Aucun profil personnalisé")
            return None
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la récupération du profil: {e}")
        return None

async def main():
    print("=" * 60)
    print("🔍 EXTRACTION DONNÉES PAGE ÉNERGIE")
    print("=" * 60)
    
    # 1. Récupérer l'user_id
    user_id = await get_user_id()
    
    # 2. Récupérer toutes les données
    data = {
        "user_id": user_id,
        "extracted_at": datetime.now().isoformat(),
        "brief": await fetch_brief_data(user_id),
        "biometrics": await fetch_biometrics_data(user_id),
        "medications": await fetch_medications(user_id),
        "conditions": await fetch_conditions(user_id),
        "feedbacks": await fetch_feedbacks(user_id),
        "energy_profile": await fetch_energy_profile(user_id)
    }
    
    # 3. Sauvegarder dans un fichier
    output_file = f"/Users/dannezri/Desktop/Pulse/energy_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print(f"\n💾 Sauvegarde dans {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Export terminé!")
    print(f"\n📁 Fichier: {output_file}")
    
    # Afficher un résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES DONNÉES EXTRAITES")
    print("=" * 60)
    
    brief = data["brief"]
    if "intraday_energy_forecast" in brief and brief["intraday_energy_forecast"]:
        forecast = brief["intraday_energy_forecast"]
        print(f"✅ Énergie actuelle: {forecast.get('current_energy', 'N/A')}%")
        print(f"✅ Points courbe: {len(forecast.get('forecast_curve', []))}")
        print(f"✅ Influenceurs: {len(forecast.get('influencers', []))}")
        print(f"✅ Notes: {len(forecast.get('notes', []))}")
    
    print(f"✅ Pulse Score: {brief.get('pulseScore', 'N/A')}")
    print(f"✅ Cartes Brief: {len(brief.get('cards', []))}")
    print(f"✅ Biométriques: {len(data['biometrics']['all'])} enregistrements")
    print(f"✅ Médicaments: {len(data['medications'])}")
    print(f"✅ Conditions: {len(data['conditions'])}")
    print(f"✅ Feedbacks: {len(data['feedbacks'])}")
    print(f"✅ Profil personnalisé: {'Oui' if data['energy_profile'] else 'Non'}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
