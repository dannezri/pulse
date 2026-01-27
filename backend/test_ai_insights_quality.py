"""
Test 3 : Qualité des Insights IA
Teste la pertinence des conseils générés pour 3 personas types

Scénarios testés :
1. "Le Burnout imminent" : HRV très bas + Sommeil catastrophique + Rythme cardiaque au repos élevé
2. "L'Athlète en forme" : HRV haut + Sommeil parfait + Activité physique élevée
3. "Le sédentaire stressé" : Pas de pas (steps) + HR élevé pendant 2h (réunion stressante) + HRV moyen
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict
import json
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase_client import SupabaseClient
from data_normalizer import DataNormalizer
from insight_generator import InsightGenerator

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def create_auth_user(supabase_url: str, supabase_key: str, user_id: str) -> bool:
    """
    Crée un utilisateur dans auth.users via l'API Admin de Supabase
    
    Returns:
        True si succès, False sinon
    """
    from uuid import uuid4
    
    try:
        admin_url = f"{supabase_url}/auth/v1/admin/users"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        # Générer un email et mot de passe temporaires
        email = f"test-{user_id[:8]}@pulse-test.example.com"
        password = str(uuid4())  # Mot de passe aléatoire
        
        auth_user_data = {
            "id": user_id,
            "email": email,
            "password": password,
            "email_confirm": True
        }
        
        auth_response = requests.post(admin_url, json=auth_user_data, headers=headers)
        
        if auth_response.status_code in [200, 201]:
            return True
        elif auth_response.status_code == 409:
            # L'utilisateur existe déjà, c'est OK
            return True
        else:
            print(f"⚠️  Warning: Could not create auth user: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Warning: Could not create auth user: {e}")
        return False


def create_persona_profile(
    supabase: SupabaseClient,
    normalizer: DataNormalizer,
    persona_name: str,
    persona_data: Dict,
    supabase_url: str,
    supabase_key: str
) -> str:
    """
    Crée un profil utilisateur et un profil de santé pour une persona
    
    Returns:
        user_id: UUID de l'utilisateur créé
    """
    from uuid import uuid4
    
    # Créer un utilisateur de test
    user_id = str(uuid4())
    
    try:
        # Créer l'utilisateur dans auth.users d'abord
        print(f"   Création de l'utilisateur auth.users...")
        create_auth_user(supabase_url, supabase_key, user_id)
        
        # Créer le profil utilisateur
        supabase.client.table("profiles").insert({
            "id": user_id,
            "full_name": persona_name,
            "health_goal": persona_data.get("health_goal", "energy"),
            "baseline_hrv": persona_data.get("baseline_hrv"),
            "baseline_resting_hr": persona_data.get("baseline_hr")
        }).execute()
        
        # Créer des données biométriques historiques (pour les baselines)
        historical_data = persona_data.get("historical_data", [])
        for day_data in historical_data:
            date = datetime.now() - timedelta(days=day_data["days_ago"])
            
            # HRV
            if "hrv" in day_data:
                supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="hrv",
                    value=day_data["hrv"],
                    recorded_at=date,
                    raw_data={"source": "test_persona"},
                    source="test",
                    source_event_id=f"test_hrv_{persona_name}_{day_data['days_ago']}"
                )
            
            # HR
            if "hr" in day_data:
                supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="hr",
                    value=day_data["hr"],
                    recorded_at=date,
                    raw_data={"source": "test_persona"},
                    source="test",
                    source_event_id=f"test_hr_{persona_name}_{day_data['days_ago']}"
                )
            
            # Sommeil
            if "sleep_duration" in day_data:
                supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="sleep_duration",
                    value=day_data["sleep_duration"],
                    recorded_at=date,
                    raw_data={"source": "test_persona"},
                    source="test",
                    source_event_id=f"test_sleep_{persona_name}_{day_data['days_ago']}"
                )
        
        # Créer les données du jour (métriques actuelles)
        today_metrics = persona_data.get("today_metrics", {})
        today = datetime.now()
        
        # HRV du jour
        if "hrv" in today_metrics:
            supabase.insert_biometric(
                user_id=user_id,
                metric_type="hrv",
                value=today_metrics["hrv"],
                recorded_at=today,
                raw_data={"source": "test_persona"},
                source="test",
                source_event_id=f"test_hrv_today_{persona_name}"
            )
        
        # HR du jour (plusieurs mesures si nécessaire)
        if "hr" in today_metrics:
            hr_data = today_metrics["hr"]
            if isinstance(hr_data, list):
                # Plusieurs mesures (ex: réunion stressante de 2h)
                for i, hr_value in enumerate(hr_data):
                    measure_time = today - timedelta(hours=len(hr_data) - i)
                    supabase.insert_biometric(
                        user_id=user_id,
                        metric_type="hr",
                        value=hr_value,
                        recorded_at=measure_time,
                        raw_data={"source": "test_persona"},
                        source="test",
                        source_event_id=f"test_hr_today_{persona_name}_{i}"
                    )
            else:
                # Une seule mesure
                supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="hr",
                    value=hr_data,
                    recorded_at=today,
                    raw_data={"source": "test_persona"},
                    source="test",
                    source_event_id=f"test_hr_today_{persona_name}"
                )
        
        # Sommeil du jour
        if "sleep_duration" in today_metrics:
            supabase.insert_biometric(
                user_id=user_id,
                metric_type="sleep_duration",
                value=today_metrics["sleep_duration"],
                recorded_at=today - timedelta(hours=8),  # Sommeil de la nuit dernière
                raw_data={"source": "test_persona"},
                source="test",
                source_event_id=f"test_sleep_today_{persona_name}"
            )
        
        # Steps du jour
        if "steps" in today_metrics:
            supabase.insert_biometric(
                user_id=user_id,
                metric_type="steps",
                value=today_metrics["steps"],
                recorded_at=today,
                raw_data={"source": "test_persona"},
                source="test",
                source_event_id=f"test_steps_today_{persona_name}"
            )
        
        # Récupérer les données historiques pour calculer les baselines
        historical_biometrics = supabase.get_historical_biometrics(user_id, days=7)
        
        # Normaliser les données du jour
        today_data = supabase.get_today_biometrics(user_id)
        
        # Calculer les baselines
        # Note: calculate_baseline cherche "sleep_duration" dans les métriques historiques
        hrv_baseline, hrv_metadata = normalizer.calculate_baseline(historical_biometrics, "hrv", days=7)
        hr_baseline, hr_metadata = normalizer.calculate_baseline(historical_biometrics, "hr", days=7)
        # Le normalizer cherche "sleep" mais les données historiques ont "sleep_duration"
        # Il gère automatiquement les deux formats
        sleep_baseline, sleep_metadata = normalizer.calculate_baseline(historical_biometrics, "sleep", days=7)
        
        baseline_data = {
            "hrv_baseline": hrv_baseline,
            "hr_baseline": hr_baseline,
            "sleep_baseline": sleep_baseline,
            "hrv_baseline_metadata": hrv_metadata,
            "hr_baseline_metadata": hr_metadata,
            "sleep_baseline_metadata": sleep_metadata
        }
        
        # Normaliser les données du jour (format attendu par normalize_open_wearables_data)
        formatted_today_data = {
            "date": datetime.now().isoformat()
        }
        
        # HR
        if today_data.get("hr"):
            formatted_today_data["hr"] = [
                {"value": entry["value"], "timestamp": entry["recorded_at"]} 
                for entry in today_data["hr"]
            ]
        
        # HRV
        if today_data.get("hrv"):
            formatted_today_data["hrv"] = [
                {"value": entry["value"], "timestamp": entry["recorded_at"]} 
                for entry in today_data["hrv"]
            ]
        
        # Sommeil (convertir minutes en secondes)
        if today_data.get("sleep_duration"):
            sleep_minutes = today_data["sleep_duration"][0].get("value", 0)
            formatted_today_data["sleep"] = {
                "duration_seconds": sleep_minutes * 60,
                "score": 70  # Score par défaut
            }
        
        # Steps
        if today_data.get("steps"):
            formatted_today_data["steps"] = [
                {"value": entry["value"], "timestamp": entry["recorded_at"]} 
                for entry in today_data["steps"]
            ]
        
        normalized_data = normalizer.normalize_open_wearables_data(formatted_today_data)
        
        # Créer le profil de santé
        user_goal = supabase.get_user_goal(user_id)
        health_profile = normalizer.create_health_profile(
            normalized_data,
            baseline_data,
            user_goal
        )
        
        # Sauvegarder le profil de santé
        supabase.save_health_profile(user_id, health_profile)
        
        return user_id
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la persona {persona_name}: {e}")
        raise


def test_persona(persona_name: str, persona_data: Dict):
    """
    Teste une persona : crée le profil et génère un insight
    """
    print(f"\n{'='*80}")
    print(f"🧪 TEST : {persona_name}")
    print(f"{'='*80}\n")
    
    # Initialiser les clients
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    normalizer = DataNormalizer()
    insight_gen = InsightGenerator(api_key=OPENAI_API_KEY)
    
    try:
        # Créer le profil de la persona
        print(f"📝 Création du profil pour {persona_name}...")
        user_id = create_persona_profile(
            supabase, 
            normalizer, 
            persona_name, 
            persona_data,
            SUPABASE_URL,
            SUPABASE_SERVICE_KEY
        )
        print(f"✅ Profil créé (user_id: {user_id})")
        
        # Récupérer le profil de santé
        health_profile = supabase.get_latest_health_profile(user_id)
        if not health_profile:
            print(f"❌ Impossible de récupérer le profil de santé")
            return
        
        # Afficher le profil
        print(f"\n📊 Profil de santé :")
        print(json.dumps(health_profile, indent=2, ensure_ascii=False))
        
        # Générer l'insight
        print(f"\n🤖 Génération de l'insight IA...")
        insight = insight_gen.generate_insight(health_profile)
        
        # Afficher l'insight
        print(f"\n💡 INSIGHT GÉNÉRÉ :")
        print(f"   Catégorie : {insight['category']}")
        print(f"   Priorité : {'🔴 URGENT' if insight['priority'] == 2 else '🟢 Normal'}")
        print(f"   Conseil : {insight['instruction_text']}")
        
        # Sauvegarder l'insight
        supabase.client.table("insights").insert({
            "user_id": user_id,
            "instruction_text": insight["instruction_text"],
            "category": insight["category"],
            "priority": insight["priority"]
        }).execute()
        print(f"\n✅ Insight sauvegardé dans la base de données")
        
        return insight
        
    except Exception as e:
        print(f"❌ Erreur lors du test de {persona_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Test principal : teste les 3 personas
    """
    print("="*80)
    print("🧠 TEST 3 : QUALITÉ DES INSIGHTS IA")
    print("="*80)
    print("\nCe test vérifie la pertinence des conseils générés pour 3 scénarios de vie.")
    print("Chaque persona représente un profil de santé différent.\n")
    
    # Vérifier la configuration
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Erreur : SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être configurés")
        return
    
    if not OPENAI_API_KEY:
        print("❌ Erreur : OPENAI_API_KEY doit être configuré")
        return
    
    # Définir les 3 personas
    personas = {
        "Le Burnout imminent": {
            "health_goal": "recovery",
            "baseline_hrv": 65,
            "baseline_hr": 58,
            "historical_data": [
                {"days_ago": 7, "hrv": 65, "hr": 58, "sleep_duration": 450},
                {"days_ago": 6, "hrv": 63, "hr": 59, "sleep_duration": 440},
                {"days_ago": 5, "hrv": 64, "hr": 58, "sleep_duration": 460},
                {"days_ago": 4, "hrv": 62, "hr": 60, "sleep_duration": 430},
                {"days_ago": 3, "hrv": 61, "hr": 61, "sleep_duration": 420},
                {"days_ago": 2, "hrv": 58, "hr": 63, "sleep_duration": 380},
                {"days_ago": 1, "hrv": 55, "hr": 65, "sleep_duration": 360}
            ],
            "today_metrics": {
                "hrv": 42,  # HRV très bas (chute de 35% par rapport à baseline 65)
                "hr": 72,   # Rythme cardiaque au repos élevé (baseline 58)
                "sleep_duration": 300,  # Sommeil catastrophique (5h seulement, baseline 450)
                "steps": 2000  # Activité réduite
            }
        },
        "L'Athlète en forme": {
            "health_goal": "energy",
            "baseline_hrv": 75,
            "baseline_hr": 52,
            "historical_data": [
                {"days_ago": 7, "hrv": 75, "hr": 52, "sleep_duration": 480},
                {"days_ago": 6, "hrv": 76, "hr": 51, "sleep_duration": 490},
                {"days_ago": 5, "hrv": 74, "hr": 53, "sleep_duration": 475},
                {"days_ago": 4, "hrv": 77, "hr": 52, "sleep_duration": 485},
                {"days_ago": 3, "hrv": 75, "hr": 51, "sleep_duration": 480},
                {"days_ago": 2, "hrv": 76, "hr": 52, "sleep_duration": 490},
                {"days_ago": 1, "hrv": 78, "hr": 50, "sleep_duration": 495}
            ],
            "today_metrics": {
                "hrv": 80,  # HRV haut (au-dessus de la baseline)
                "hr": 50,   # Rythme cardiaque au repos excellent
                "sleep_duration": 510,  # Sommeil parfait (8h30)
                "steps": 15000  # Activité physique élevée
            }
        },
        "Le sédentaire stressé": {
            "health_goal": "focus",
            "baseline_hrv": 60,
            "baseline_hr": 65,
            "historical_data": [
                {"days_ago": 7, "hrv": 60, "hr": 65, "sleep_duration": 420},
                {"days_ago": 6, "hrv": 61, "hr": 64, "sleep_duration": 430},
                {"days_ago": 5, "hrv": 59, "hr": 66, "sleep_duration": 410},
                {"days_ago": 4, "hrv": 60, "hr": 65, "sleep_duration": 425},
                {"days_ago": 3, "hrv": 61, "hr": 64, "sleep_duration": 420},
                {"days_ago": 2, "hrv": 60, "hr": 65, "sleep_duration": 415},
                {"days_ago": 1, "hrv": 59, "hr": 66, "sleep_duration": 410}
            ],
            "today_metrics": {
                "hrv": 58,  # HRV moyen (légèrement en dessous)
                "hr": [85, 88, 90, 92, 88, 85],  # HR élevé pendant 2h (réunion stressante)
                "sleep_duration": 400,  # Sommeil moyen
                "steps": 500  # Pas de pas (sédentaire)
            }
        }
    }
    
    # Tester chaque persona
    results = {}
    for persona_name, persona_data in personas.items():
        insight = test_persona(persona_name, persona_data)
        results[persona_name] = insight
    
    # Résumé
    print(f"\n{'='*80}")
    print("📊 RÉSUMÉ DES TESTS")
    print(f"{'='*80}\n")
    
    for persona_name, insight in results.items():
        if insight:
            print(f"✅ {persona_name}")
            print(f"   Catégorie: {insight['category']} | Priorité: {insight['priority']}")
            print(f"   Conseil: {insight['instruction_text'][:100]}...")
        else:
            print(f"❌ {persona_name} : Échec")
        print()
    
    print("="*80)
    print("✅ Tests terminés !")
    print("="*80)


if __name__ == "__main__":
    main()
