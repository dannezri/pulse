#!/usr/bin/env python3
"""
Test unitaire pour l'extraction des données biométriques
Vérifie que toutes les données nécessaires pour Gemini sont disponibles
"""

import os
import sys
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

# Ajouter le répertoire backend au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_client import SupabaseClient

# Charger les variables d'environnement
load_dotenv()

# ID utilisateur de test (Dan)
from user_config import get_test_user_uuid

TEST_USER_ID = get_test_user_uuid()
TEST_DATE = date.today()

def test_biometrics_extraction():
    """Test l'extraction des données biométriques"""
    print("=" * 80)
    print("🧪 TEST : Extraction des données biométriques")
    print("=" * 80)
    print(f"\n👤 User ID: {TEST_USER_ID}")
    print(f"📅 Date: {TEST_DATE}")
    print("\n" + "=" * 80)
    
    # Initialiser le client Supabase
    supabase = SupabaseClient()
    
    # 1. Tester la récupération depuis la table biometrics
    print("\n📊 1. TEST : Table biometrics")
    print("-" * 80)
    
    start_of_day = datetime.combine(TEST_DATE, datetime.min.time())
    end_of_day = datetime.combine(TEST_DATE, datetime.max.time())
    
    try:
        bio_result = supabase.client.table("biometrics") \
            .select("metric_type, value, recorded_at") \
            .eq("user_id", TEST_USER_ID) \
            .gte("recorded_at", start_of_day.isoformat()) \
            .lte("recorded_at", end_of_day.isoformat()) \
            .execute()
        
        if bio_result.data:
            print(f"✅ Trouvé {len(bio_result.data)} métriques biométriques")
            
            # Organiser par type
            metrics = {}
            for row in bio_result.data:
                metric_type = row.get("metric_type")
                value = row.get("value")
                metrics[metric_type] = value
                print(f"   - {metric_type}: {value}")
            
            # Vérifier les métriques critiques
            print("\n📋 Vérification des métriques critiques:")
            critical_metrics = {
                "HRV": metrics.get("hrv") or metrics.get("hrv_night"),
                "RHR": metrics.get("hr") or metrics.get("rhr") or metrics.get("rhr_night"),
                "Sleep Score": metrics.get("sleep_score"),
                "Readiness Score": metrics.get("readiness_score"),
                "Activity Score": metrics.get("activity_score"),
                "Steps": metrics.get("steps"),
            }
            
            for name, value in critical_metrics.items():
                status = "✅" if value is not None else "❌"
                print(f"   {status} {name}: {value if value is not None else 'MANQUANT'}")
            
            # Compter les données manquantes
            missing_count = sum(1 for v in critical_metrics.values() if v is None)
            total_count = len(critical_metrics)
            
            print(f"\n📊 Résumé: {total_count - missing_count}/{total_count} métriques disponibles")
            
            if missing_count > 0:
                print(f"⚠️  {missing_count} métrique(s) manquante(s)")
        else:
            print("❌ Aucune donnée biométrique trouvée pour cette date")
            print("   Vérifiez que la bague Oura a synchronisé les données")
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des biometrics: {e}")
    
    # 2. Tester la récupération des baselines
    print("\n" + "=" * 80)
    print("📊 2. TEST : Baselines utilisateur")
    print("-" * 80)
    
    try:
        baseline_result = supabase.client.table("user_baselines") \
            .select("baseline_type, baseline_data, confidence, calculated_at") \
            .eq("user_id", TEST_USER_ID) \
            .execute()
        
        if baseline_result.data:
            print(f"✅ Trouvé {len(baseline_result.data)} baseline(s)")
            
            baselines = {}
            for row in baseline_result.data:
                baseline_type = row.get("baseline_type")
                baseline_data = row.get("baseline_data", {})
                confidence = row.get("confidence", 0)
                calculated_at = row.get("calculated_at")
                
                value = baseline_data.get("value") if isinstance(baseline_data, dict) else None
                baselines[baseline_type] = value
                
                print(f"   - {baseline_type}: {value} (confiance: {confidence:.2f}, calculé: {calculated_at})")
            
            # Vérifier les baselines critiques
            print("\n📋 Vérification des baselines critiques:")
            critical_baselines = {
                "HRV Baseline": baselines.get("hrv"),
                "RHR Baseline": baselines.get("sleep"),  # Note: "sleep" contient souvent RHR baseline
            }
            
            for name, value in critical_baselines.items():
                status = "✅" if value is not None else "❌"
                print(f"   {status} {name}: {value if value is not None else 'MANQUANT'}")
        else:
            print("❌ Aucune baseline trouvée")
            print("   Les baselines doivent être calculées pour personnaliser l'analyse")
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des baselines: {e}")
    
    # 3. Tester la récupération des états latents
    print("\n" + "=" * 80)
    print("📊 3. TEST : États latents (daily_state)")
    print("-" * 80)
    
    try:
        state_result = supabase.client.table("daily_state") \
            .select("state_type, score, confidence") \
            .eq("user_id", TEST_USER_ID) \
            .eq("state_date", TEST_DATE.isoformat()) \
            .execute()
        
        if state_result.data:
            print(f"✅ Trouvé {len(state_result.data)} état(s) latent(s)")
            
            states = {}
            for row in state_result.data:
                state_type = row.get("state_type")
                score = row.get("score")
                confidence = row.get("confidence")
                
                states[state_type] = score
                score_pct = int(score * 100) if score is not None else 0
                conf_pct = int(confidence * 100) if confidence is not None else 0
                
                print(f"   - {state_type}: {score_pct}% (confiance: {conf_pct}%)")
            
            # Vérifier les états critiques
            print("\n📋 Vérification des états critiques:")
            critical_states = {
                "Récupération": states.get("recovery"),
                "Dette sommeil": states.get("sleep_debt"),
                "Surcharge": states.get("overtrain"),
                "Infection": states.get("infection_like"),
            }
            
            for name, value in critical_states.items():
                status = "✅" if value is not None else "❌"
                pct = int(value * 100) if value is not None else 0
                print(f"   {status} {name}: {pct}%" if value is not None else f"   {status} {name}: MANQUANT")
        else:
            print("❌ Aucun état latent trouvé pour cette date")
            print("   Les états latents doivent être calculés quotidiennement")
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des états latents: {e}")
    
    # 4. Tester la récupération de daily_energy
    print("\n" + "=" * 80)
    print("📊 4. TEST : Score d'énergie (daily_energy)")
    print("-" * 80)
    
    try:
        energy_result = supabase.client.table("daily_energy") \
            .select("*") \
            .eq("user_id", TEST_USER_ID) \
            .eq("energy_date", TEST_DATE.isoformat()) \
            .order("calculated_at", desc=True) \
            .limit(1) \
            .execute()
        
        if energy_result.data and len(energy_result.data) > 0:
            energy = energy_result.data[0]
            score = int(energy.get("energy_score", 0) * 100)
            confidence = int(energy.get("confidence", 0) * 100)
            label = energy.get("label")
            
            print(f"✅ Score d'énergie: {score}%")
            print(f"   - Label: {label}")
            print(f"   - Confiance: {confidence}%")
            print(f"   - Calculé à: {energy.get('calculated_at')}")
        else:
            print("❌ Aucun score d'énergie trouvé pour cette date")
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du score d'énergie: {e}")
    
    # 5. Tester la récupération du forecast
    print("\n" + "=" * 80)
    print("📊 5. TEST : Forecast intraday")
    print("-" * 80)
    
    try:
        forecast_result = supabase.client.table("intraday_energy_forecast") \
            .select("*") \
            .eq("user_id", TEST_USER_ID) \
            .eq("forecast_date", TEST_DATE.isoformat()) \
            .order("generated_at", desc=True) \
            .limit(1) \
            .execute()
        
        if forecast_result.data and len(forecast_result.data) > 0:
            forecast = forecast_result.data[0]
            influencers = forecast.get("influencers", [])
            points = forecast.get("points", [])
            
            print(f"✅ Forecast trouvé")
            print(f"   - Points: {len(points)}")
            print(f"   - Influenceurs: {len(influencers)}")
            
            if influencers:
                print(f"\n   Influenceurs détectés:")
                for inf in influencers[:5]:  # Montrer les 5 premiers
                    name = inf.get("name", "")
                    impact = inf.get("impact", "")
                    print(f"   - {name}: {impact}")
        else:
            print("❌ Aucun forecast trouvé pour cette date")
    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du forecast: {e}")
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DU TEST")
    print("=" * 80)
    print("\n✅ Le test est terminé. Vérifiez les résultats ci-dessus.")
    print("\n💡 Actions recommandées:")
    print("   1. Si des données manquent : synchroniser la bague Oura")
    print("   2. Si les baselines manquent : exécuter le calcul des baselines")
    print("   3. Si les états latents manquent : exécuter le calcul quotidien")
    print("   4. Redémarrer le backend avec ./restart_api_server.sh")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_biometrics_extraction()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
