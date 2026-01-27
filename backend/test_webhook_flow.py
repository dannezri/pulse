"""
Script de test complet pour simuler un webhook et vérifier le flux de bout en bout

Ce script permet de :
1. Simuler un webhook Open Wearables avec des données de test
2. Vérifier chaque étape du traitement
3. Vérifier que les données sont bien sauvegardées dans Supabase
4. Vérifier que le profil de santé est créé correctement

Usage:
    python test_webhook_flow.py
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
import json

# Charger les variables d'environnement
load_dotenv()

# Importer les modules du projet
from open_wearables_integration import OpenWearablesIntegration
from data_normalizer import DataNormalizer
from supabase_client import SupabaseClient
from webhook_handler import OpenWearablesWebhookHandler

# Configuration des couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num: int, description: str):
    """Affiche une étape du test"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ Étape {step_num}: {description} ═══{Colors.RESET}")

def print_success(message: str):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_info(message: str):
    """Affiche un message d'information"""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")

def print_data(data: Dict, title: str = "Données"):
    """Affiche des données JSON formatées"""
    print(f"\n{Colors.BOLD}{title}:{Colors.RESET}")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def create_test_webhook_payload(
    open_wearables_user_id: str,
    include_sleep: bool = True,
    include_hr: bool = True,
    include_hrv: bool = True,
    include_steps: bool = True
) -> Dict[str, Any]:
    """
    Crée un payload de webhook de test simulant les données Open Wearables
    
    Args:
        open_wearables_user_id: ID utilisateur Open Wearables
        include_sleep: Inclure des données de sommeil
        include_hr: Inclure des données de fréquence cardiaque
        include_hrv: Inclure des données HRV
        include_steps: Inclure des données de pas
    """
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    payload = {
        "user_id": open_wearables_user_id,
        "timestamp": now.isoformat(),
        "data": {}
    }
    
    # Données de sommeil (nuit précédente)
    if include_sleep:
        payload["data"]["sleep"] = {
            "duration_seconds": 28800,  # 8 heures
            "start_time": yesterday.replace(hour=23, minute=0, second=0).isoformat(),
            "end_time": now.replace(hour=7, minute=0, second=0).isoformat(),
            "score": 85,
            "quality_score": 85,
            "deep_sleep_seconds": 7200,  # 2 heures
            "rem_sleep_seconds": 5400,   # 1.5 heures
            "light_sleep_seconds": 16200, # 4.5 heures
            "efficiency": 0.92
        }
    
    # Données de fréquence cardiaque (plusieurs points dans la journée)
    if include_hr:
        payload["data"]["hr"] = [
            {
                "value": 65,
                "timestamp": now.replace(hour=7, minute=0, second=0).isoformat()
            },
            {
                "value": 72,
                "timestamp": now.replace(hour=12, minute=0, second=0).isoformat()
            },
            {
                "value": 68,
                "timestamp": now.replace(hour=18, minute=0, second=0).isoformat()
            }
        ]
    
    # Données HRV
    if include_hrv:
        payload["data"]["hrv"] = [
            {
                "value": 45,
                "timestamp": now.replace(hour=7, minute=0, second=0).isoformat()
            },
            {
                "value": 48,
                "timestamp": now.replace(hour=12, minute=0, second=0).isoformat()
            }
        ]
    
    # Données de pas
    if include_steps:
        payload["data"]["steps"] = [
            {
                "value": 2500,
                "timestamp": now.replace(hour=9, minute=0, second=0).isoformat()
            },
            {
                "value": 5000,
                "timestamp": now.replace(hour=14, minute=0, second=0).isoformat()
            },
            {
                "value": 8500,
                "timestamp": now.replace(hour=20, minute=0, second=0).isoformat()
            }
        ]
    
    return payload


def verify_biometrics_saved(supabase_client: SupabaseClient, user_id: str) -> bool:
    """
    Vérifie que les biométriques ont été sauvegardées dans Supabase
    """
    try:
        today_data = supabase_client.get_today_biometrics(user_id)
        
        if not today_data:
            print_error("Aucune donnée biométrique trouvée pour aujourd'hui")
            return False
        
        print_success(f"Données biométriques trouvées: {len(today_data)} types de métriques")
        
        # Vérifier les types de métriques attendus
        expected_metrics = ["sleep_duration", "sleep_score", "hr", "hrv", "steps"]
        found_metrics = list(today_data.keys())
        
        print_info(f"Métriques trouvées: {', '.join(found_metrics)}")
        
        for metric in expected_metrics:
            if metric in found_metrics:
                count = len(today_data[metric])
                print_success(f"  - {metric}: {count} enregistrement(s)")
            else:
                print_error(f"  - {metric}: manquant")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification des biométriques: {e}")
        return False


def verify_health_profile_created(supabase_client: SupabaseClient, user_id: str) -> bool:
    """
    Vérifie que le profil de santé a été créé
    """
    try:
        profile = supabase_client.get_latest_health_profile(user_id)
        
        if not profile:
            print_error("Aucun profil de santé trouvé")
            return False
        
        print_success("Profil de santé trouvé")
        print_data(profile, "Profil de santé")
        
        # Vérifier la structure du profil
        required_fields = ["timestamp", "user_goal", "current_metrics", "baselines", "anomalies", "context"]
        for field in required_fields:
            if field in profile:
                print_success(f"  - {field}: présent")
            else:
                print_error(f"  - {field}: manquant")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur lors de la vérification du profil de santé: {e}")
        return False


def test_webhook_flow():
    """
    Test complet du flux webhook
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("TEST COMPLET DU FLUX WEBHOOK")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Vérifier les variables d'environnement
    print_step(0, "Vérification de la configuration")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    open_wearables_base_url = os.getenv("OPEN_WEARABLES_BASE_URL", "http://localhost:8080")
    open_wearables_api_key = os.getenv("OPEN_WEARABLES_API_KEY")
    
    if not supabase_url or not supabase_key:
        print_error("Variables d'environnement manquantes (SUPABASE_URL, SUPABASE_SERVICE_KEY)")
        print_info("Assurez-vous d'avoir un fichier .env avec ces variables")
        return False
    
    print_success("Configuration chargée")
    print_info(f"  - Supabase URL: {supabase_url[:30]}...")
    print_info(f"  - Open Wearables URL: {open_wearables_base_url}")
    
    # Demander l'ID utilisateur Open Wearables
    print("\n" + "="*60)
    open_wearables_user_id = input(f"{Colors.YELLOW}Entrez l'ID utilisateur Open Wearables à tester: {Colors.RESET}").strip()
    
    if not open_wearables_user_id:
        print_error("ID utilisateur requis")
        return False
    
    # Initialiser les clients
    print_step(1, "Initialisation des clients")
    
    try:
        open_wearables_client = OpenWearablesIntegration(
            base_url=open_wearables_base_url,
            api_key=open_wearables_api_key
        )
        normalizer = DataNormalizer()
        supabase_client = SupabaseClient(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        webhook_handler = OpenWearablesWebhookHandler(
            open_wearables_client=open_wearables_client,
            normalizer=normalizer,
            supabase_client=supabase_client
        )
        print_success("Clients initialisés")
    except Exception as e:
        print_error(f"Erreur lors de l'initialisation: {e}")
        return False
    
    # Vérifier que l'utilisateur existe dans Supabase
    print_step(2, "Vérification de l'utilisateur")
    
    supabase_user_id = supabase_client.get_user_by_open_wearables_id(open_wearables_user_id)
    if not supabase_user_id:
        print_error(f"Utilisateur non trouvé pour Open Wearables ID: {open_wearables_user_id}")
        print_info("Assurez-vous que l'utilisateur existe dans la table 'profiles' avec open_wearables_user_id")
        return False
    
    print_success(f"Utilisateur trouvé: {supabase_user_id}")
    
    # Créer le payload de test
    print_step(3, "Création du payload de test")
    
    test_payload = create_test_webhook_payload(open_wearables_user_id)
    print_success("Payload de test créé")
    print_data(test_payload, "Payload du webhook")
    
    # Traiter le webhook
    print_step(4, "Traitement du webhook")
    
    try:
        result = webhook_handler.handle_webhook(test_payload)
        print_data(result, "Résultat du traitement")
        
        if result["status"] == "error":
            print_error(f"Erreur lors du traitement: {result.get('message')}")
            return False
        
        print_success("Webhook traité avec succès")
    except Exception as e:
        print_error(f"Exception lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Vérifier que les biométriques sont sauvegardées
    print_step(5, "Vérification des biométriques sauvegardées")
    
    if not verify_biometrics_saved(supabase_client, supabase_user_id):
        return False
    
    # Vérifier que le profil de santé est créé
    print_step(6, "Vérification du profil de santé")
    
    if not verify_health_profile_created(supabase_client, supabase_user_id):
        return False
    
    # Résumé final
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("✅ TEST RÉUSSI - Tous les composants fonctionnent correctement")
    print(f"{'='*60}{Colors.RESET}\n")
    
    return True


def test_individual_components():
    """
    Test des composants individuels pour le débogage
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("TEST DES COMPOSANTS INDIVIDUELS")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Test du normaliseur
    print_step(1, "Test du normaliseur de données")
    
    normalizer = DataNormalizer()
    test_data = {
        "date": datetime.now().isoformat(),
        "sleep": {
            "duration_seconds": 28800,
            "score": 85
        },
        "hr": [
            {"value": 65, "timestamp": datetime.now().isoformat()},
            {"value": 72, "timestamp": datetime.now().isoformat()}
        ],
        "hrv": [
            {"value": 45, "timestamp": datetime.now().isoformat()}
        ],
        "steps": [
            {"value": 5000, "timestamp": datetime.now().isoformat()}
        ]
    }
    
    normalized = normalizer.normalize_open_wearables_data(test_data)
    print_success("Données normalisées")
    print_data(normalized, "Données normalisées")
    
    # Test de création de profil de santé
    print_step(2, "Test de création de profil de santé")
    
    baseline_data = {
        "hrv_baseline": 50.0,
        "hr_baseline": 65.0,
        "sleep_baseline": 480.0  # 8 heures en minutes
    }
    
    health_profile = normalizer.create_health_profile(
        normalized,
        baseline_data,
        "energy"
    )
    print_success("Profil de santé créé")
    print_data(health_profile, "Profil de santé")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Tests des composants réussis{Colors.RESET}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test du flux webhook")
    parser.add_argument(
        "--components",
        action="store_true",
        help="Tester uniquement les composants individuels (sans Supabase)"
    )
    
    args = parser.parse_args()
    
    if args.components:
        test_individual_components()
    else:
        success = test_webhook_flow()
        sys.exit(0 if success else 1)
