#!/usr/bin/env python3
"""
Test pour visualiser exactement ce que Gemini va recevoir dans le prompt
"""

import os
import sys
import asyncio
from datetime import date
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from explain_service import EnergyExplainService
from supabase_client import SupabaseClient
from gemini_client import GeminiClient

# Configuration
from user_config import get_dev_user_uuid

USER_ID = get_dev_user_uuid()

async def test_prompt_preview():
    """Teste et affiche le prompt qui sera envoyé à Gemini"""
    print("=" * 80)
    print("🔍 PRÉVISUALISATION DU PROMPT GEMINI")
    print("=" * 80)
    print(f"\n👤 User ID: {USER_ID}")
    
    # Initialiser le service
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        sys.exit(1)
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY must be set in environment")
        sys.exit(1)
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    gemini = GeminiClient(api_key=GOOGLE_API_KEY)
    service = EnergyExplainService(supabase, gemini)
    
    # Trouver la dernière date avec un score d'énergie
    print("\n🔍 Recherche de la dernière date avec score d'énergie...")
    print("-" * 80)
    
    try:
        last_energy_result = supabase.client.table("daily_energy") \
            .select("energy_date, energy_score") \
            .eq("user_id", USER_ID) \
            .order("energy_date", desc=True) \
            .limit(1) \
            .execute()
        
        if last_energy_result.data and len(last_energy_result.data) > 0:
            TARGET_DATE = date.fromisoformat(last_energy_result.data[0]["energy_date"])
            print(f"✅ Dernière date trouvée: {TARGET_DATE}")
        else:
            print("⚠️  Aucun score d'énergie trouvé, utilisation de hier")
            from datetime import timedelta
            TARGET_DATE = date.today() - timedelta(days=1)
    except Exception as e:
        print(f"⚠️  Erreur lors de la recherche: {e}")
        from datetime import timedelta
        TARGET_DATE = date.today() - timedelta(days=1)
    
    print(f"📅 Date de test: {TARGET_DATE}")
    print("\n" + "=" * 80)
    
    # Étape 1: Récupérer les biométriques
    print("\n📊 ÉTAPE 1: Récupération des biométriques")
    print("-" * 80)
    
    biometrics = await service._get_biometrics(USER_ID, TARGET_DATE)
    
    print("\n✅ Biométriques récupérées:")
    for key, value in biometrics.items():
        status = "✅" if value is not None else "❌"
        print(f"   {status} {key:25s} : {value if value is not None else 'None (MANQUANT)'}")
    
    # Compter les données disponibles
    available = sum(1 for v in biometrics.values() if v is not None)
    total = len(biometrics)
    print(f"\n📊 Résumé: {available}/{total} métriques disponibles")
    
    # Étape 2: Récupérer les états latents
    print("\n" + "=" * 80)
    print("📊 ÉTAPE 2: Récupération des états latents")
    print("-" * 80)
    
    try:
        latent_result = supabase.client.table("daily_state") \
            .select("state_type, score, confidence") \
            .eq("user_id", USER_ID) \
            .eq("state_date", TARGET_DATE.isoformat()) \
            .execute()
        
        latent_states = {}
        if latent_result.data:
            print(f"\n✅ Trouvé {len(latent_result.data)} état(s) latent(s):")
            for row in latent_result.data:
                state_type = row.get("state_type")
                score = row.get("score", 0)
                confidence = row.get("confidence", 0)
                latent_states[state_type] = {"score": score, "confidence": confidence}
                
                score_pct = int(score * 100)
                conf_pct = int(confidence * 100)
                print(f"   ✅ {state_type:20s} : {score_pct}% (confiance: {conf_pct}%)")
        else:
            print("❌ Aucun état latent trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        latent_states = {}
    
    # Étape 3: Récupérer le score d'énergie
    print("\n" + "=" * 80)
    print("📊 ÉTAPE 3: Récupération du score d'énergie")
    print("-" * 80)
    
    try:
        energy_result = supabase.client.table("daily_energy") \
            .select("*") \
            .eq("user_id", USER_ID) \
            .eq("energy_date", TARGET_DATE.isoformat()) \
            .order("calculated_at", desc=True) \
            .limit(1) \
            .execute()
        
        if energy_result.data and len(energy_result.data) > 0:
            energy_data = energy_result.data[0]
            score = int(energy_data.get("energy_score", 0) * 100)
            confidence = int(energy_data.get("confidence", 0) * 100)
            label = energy_data.get("label", "")
            
            print(f"\n✅ Score d'énergie: {score}%")
            print(f"   - Label: {label}")
            print(f"   - Confiance: {confidence}%")
        else:
            print("❌ Aucun score d'énergie trouvé")
            energy_data = {}
    except Exception as e:
        print(f"❌ Erreur: {e}")
        energy_data = {}
    
    # Étape 4: Récupérer le forecast (pour les influencers)
    print("\n" + "=" * 80)
    print("📊 ÉTAPE 4: Récupération du forecast (médicaments & conditions)")
    print("-" * 80)
    
    try:
        forecast_result = supabase.client.table("intraday_energy_forecast") \
            .select("*") \
            .eq("user_id", USER_ID) \
            .eq("forecast_date", TARGET_DATE.isoformat()) \
            .order("generated_at", desc=True) \
            .limit(1) \
            .execute()
        
        if forecast_result.data and len(forecast_result.data) > 0:
            forecast = forecast_result.data[0]
            influencers = forecast.get("influencers", [])
            
            print(f"\n✅ Trouvé {len(influencers)} influenceur(s):")
            
            medications = [inf for inf in influencers if "💊" in inf.get("name", "")]
            conditions = [inf for inf in influencers if inf.get("name", "").startswith("😔") or inf.get("name", "").startswith("🏥")]
            
            if medications:
                print(f"\n💊 Médicaments ({len(medications)}):")
                for med in medications:
                    print(f"   - {med.get('name')}: impact {med.get('impact')}")
            
            if conditions:
                print(f"\n🏥 Conditions ({len(conditions)}):")
                for cond in conditions:
                    print(f"   - {cond.get('name')}: impact {cond.get('impact')}")
        else:
            print("❌ Aucun forecast trouvé")
            forecast = {}
    except Exception as e:
        print(f"❌ Erreur: {e}")
        forecast = {}
    
    # Étape 5: Construire le prompt (simulation)
    print("\n" + "=" * 80)
    print("📝 ÉTAPE 5: APERÇU DU PROMPT QUI SERA ENVOYÉ À GEMINI")
    print("=" * 80)
    
    # Extraire les valeurs pour le prompt
    score = int(energy_data.get("energy_score", 0) * 100) if energy_data else 0
    confidence = int(energy_data.get("confidence", 0.6) * 100) if energy_data else 60
    
    recovery = int(latent_states.get("recovery", {}).get("score", 0) * 100) if latent_states else 0
    sleep_debt = int(latent_states.get("sleep_debt", {}).get("score", 1.0) * 100) if latent_states else 100
    overtrain = int(latent_states.get("overtrain", {}).get("score", 1.0) * 100) if latent_states else 100
    infection = int(latent_states.get("infection_like", {}).get("score", 0) * 100) if latent_states else 0
    
    hrv_night = biometrics.get("hrv_night")
    hrv_baseline = biometrics.get("hrv_baseline")
    rhr_night = biometrics.get("rhr_night")
    rhr_baseline = biometrics.get("rhr_baseline")
    sleep_score = biometrics.get("sleep_score")
    readiness_score = biometrics.get("readiness_score")
    activity_score = biometrics.get("activity_score")
    steps = biometrics.get("steps")
    
    print("\n📋 DONNÉES QUI SERONT DANS LE PROMPT:")
    print("-" * 80)
    print(f"\n🎯 SCORE D'ÉNERGIE:")
    print(f"   - Score final: {score}%")
    print(f"   - Confiance: {confidence}%")
    
    print(f"\n🧠 ÉTATS LATENTS:")
    print(f"   - Récupération: {recovery}%")
    print(f"   - Dette de sommeil: {sleep_debt}%")
    print(f"   - Surcharge: {overtrain}%")
    print(f"   - Infection: {infection}%")
    
    print(f"\n💓 MÉTRIQUES CARDIAQUES:")
    if hrv_night:
        warning = "⚠️ BAS" if hrv_baseline and hrv_night < hrv_baseline * 0.8 else "✅"
        print(f"   - HRV nuit: {hrv_night}ms (baseline: {hrv_baseline}ms) {warning}")
    else:
        print(f"   - HRV nuit: ❌ MANQUANT (baseline: {hrv_baseline}ms)")
    
    if rhr_night:
        warning = "⚠️ ÉLEVÉ" if rhr_baseline and rhr_night > rhr_baseline * 1.05 else "✅"
        print(f"   - RHR nuit: {rhr_night}bpm (baseline: {rhr_baseline}bpm) {warning}")
    else:
        print(f"   - RHR nuit: ❌ MANQUANT (baseline: {rhr_baseline}bpm)")
    
    print(f"\n😴 SCORES OURA:")
    print(f"   - Sleep Score: {sleep_score if sleep_score else '❌ MANQUANT'}")
    print(f"   - Readiness Score: {readiness_score if readiness_score else '❌ MANQUANT'}")
    print(f"   - Activity Score: {activity_score if activity_score else '❌ MANQUANT'}")
    print(f"   - Steps: {steps if steps else '❌ MANQUANT'}")
    
    if forecast and influencers:
        print(f"\n💊 MÉDICAMENTS & CONDITIONS:")
        for inf in influencers[:10]:  # Montrer les 10 premiers
            print(f"   - {inf.get('name')}: {inf.get('impact')}")
    
    # Évaluation finale
    print("\n" + "=" * 80)
    print("📊 ÉVALUATION FINALE")
    print("=" * 80)
    
    critical_data = {
        "Score d'énergie": score > 0,
        "États latents": len(latent_states) > 0,
        "HRV": hrv_night is not None,
        "RHR": rhr_night is not None,
        "Sleep Score": sleep_score is not None,
        "Readiness Score": readiness_score is not None,
        "Médicaments/Conditions": forecast and len(influencers) > 0,
    }
    
    available_count = sum(1 for v in critical_data.values() if v)
    total_count = len(critical_data)
    
    print(f"\n✅ Données critiques disponibles: {available_count}/{total_count}")
    
    for name, available in critical_data.items():
        status = "✅" if available else "❌"
        print(f"   {status} {name}")
    
    # Estimation de la confidence
    if available_count >= 6:
        expected_confidence = "70-85%"
        quality = "🎉 EXCELLENT"
    elif available_count >= 4:
        expected_confidence = "50-70%"
        quality = "✅ BON"
    elif available_count >= 2:
        expected_confidence = "30-50%"
        quality = "⚠️  MOYEN"
    else:
        expected_confidence = "< 30%"
        quality = "❌ FAIBLE"
    
    print(f"\n🎯 Confidence attendue: {expected_confidence}")
    print(f"📊 Qualité de l'analyse: {quality}")
    
    if available_count < 6:
        print(f"\n💡 Recommandations:")
        if not hrv_night:
            print("   - HRV manquant: Attendre la sync Oura (données de nuit arrivent le matin)")
        if not sleep_score:
            print("   - Sleep Score manquant: Vérifier dans l'app Oura si les données sont présentes")
        if not readiness_score:
            print("   - Readiness Score manquant: Vérifier dans l'app Oura")
    
    print("\n" + "=" * 80)
    print("✅ PRÉVISUALISATION TERMINÉE")
    print("=" * 80)
    print("\nSi les données critiques sont disponibles, tu peux redémarrer le backend:")
    print("   cd /Users/dannezri/Desktop/Pulse && ./restart_api_server.sh")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_prompt_preview())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
