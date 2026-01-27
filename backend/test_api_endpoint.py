"""
Script pour tester l'API HTTP directement (simule un appel webhook externe)

Ce script permet de tester l'endpoint /api/webhooks/wearables
comme si Open Wearables envoyait réellement un webhook.

Usage:
    # Démarrer l'API d'abord: python api_server.py
    # Puis dans un autre terminal: python test_api_endpoint.py
"""

import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000")
OPEN_WEARABLES_USER_ID = os.getenv("OPEN_WEARABLES_USER_ID", "")


def create_test_payload(open_wearables_user_id: str) -> dict:
    """Crée un payload de test"""
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    return {
        "user_id": open_wearables_user_id,
        "timestamp": now.isoformat(),
        "data": {
            "sleep": {
                "duration_seconds": 28800,  # 8 heures
                "start_time": yesterday.replace(hour=23, minute=0, second=0).isoformat(),
                "end_time": now.replace(hour=7, minute=0, second=0).isoformat(),
                "score": 85,
                "quality_score": 85,
                "deep_sleep_seconds": 7200,
                "rem_sleep_seconds": 5400,
                "light_sleep_seconds": 16200,
                "efficiency": 0.92
            },
            "hr": [
                {
                    "value": 65,
                    "timestamp": now.replace(hour=7, minute=0, second=0).isoformat()
                },
                {
                    "value": 72,
                    "timestamp": now.replace(hour=12, minute=0, second=0).isoformat()
                }
            ],
            "hrv": [
                {
                    "value": 45,
                    "timestamp": now.replace(hour=7, minute=0, second=0).isoformat()
                }
            ],
            "steps": [
                {
                    "value": 5000,
                    "timestamp": now.replace(hour=14, minute=0, second=0).isoformat()
                }
            ]
        }
    }


def test_webhook_endpoint():
    """Teste l'endpoint webhook"""
    print("🧪 Test de l'endpoint webhook\n")
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ API accessible: {response.json()}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {API_BASE_URL}")
        print("   Assurez-vous que l'API est démarrée: python api_server.py")
        return False
    
    # Demander l'ID utilisateur si non fourni
    open_wearables_user_id = OPEN_WEARABLES_USER_ID
    if not open_wearables_user_id:
        open_wearables_user_id = input("Entrez l'ID utilisateur Open Wearables: ").strip()
    
    if not open_wearables_user_id:
        print("❌ ID utilisateur requis")
        return False
    
    # Créer le payload
    payload = create_test_payload(open_wearables_user_id)
    
    print(f"\n📤 Envoi du webhook à {API_BASE_URL}/api/webhooks/wearables")
    print(f"   User ID: {open_wearables_user_id}")
    print(f"\n📦 Payload:")
    print(json.dumps(payload, indent=2, default=str))
    
    # Envoyer le webhook
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/webhooks/wearables",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Réponse (Status: {response.status_code}):")
        
        if response.status_code == 200:
            print("✅ Webhook traité avec succès")
            print(json.dumps(response.json(), indent=2, default=str))
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_sync_endpoint():
    """Teste l'endpoint de synchronisation"""
    print("\n🧪 Test de l'endpoint de synchronisation\n")
    
    open_wearables_user_id = OPEN_WEARABLES_USER_ID
    if not open_wearables_user_id:
        open_wearables_user_id = input("Entrez l'ID utilisateur Open Wearables: ").strip()
    
    if not open_wearables_user_id:
        print("❌ ID utilisateur requis")
        return False
    
    print(f"📤 Synchronisation des données pour {open_wearables_user_id}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/sync/{open_wearables_user_id}")
        
        print(f"\n📥 Réponse (Status: {response.status_code}):")
        print(json.dumps(response.json(), indent=2, default=str))
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_health_profile_endpoint():
    """Teste l'endpoint de récupération du profil de santé"""
    print("\n🧪 Test de l'endpoint de profil de santé\n")
    
    user_id = input("Entrez l'UUID Supabase de l'utilisateur: ").strip()
    
    if not user_id:
        print("❌ ID utilisateur requis")
        return False
    
    print(f"📤 Récupération du profil de santé pour {user_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health-profile/{user_id}")
        
        print(f"\n📥 Réponse (Status: {response.status_code}):")
        
        if response.status_code == 200:
            print("✅ Profil de santé récupéré")
            print(json.dumps(response.json(), indent=2, default=str))
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "webhook":
            test_webhook_endpoint()
        elif test_type == "sync":
            test_sync_endpoint()
        elif test_type == "profile":
            test_health_profile_endpoint()
        else:
            print("Usage: python test_api_endpoint.py [webhook|sync|profile]")
    else:
        # Tester tous les endpoints
        print("="*60)
        print("TEST COMPLET DES ENDPOINTS API")
        print("="*60)
        
        test_webhook_endpoint()
        # test_sync_endpoint()  # Décommenter si nécessaire
        # test_health_profile_endpoint()  # Décommenter si nécessaire
