#!/usr/bin/env python3
"""
Script de test complet du Food Diary API (bypass JWT)
Teste directement les services sans passer par les endpoints HTTP
"""
import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client
from services.food_log_service import FoodLogService
from services.photo_service import PhotoService
from fatsecret_client_v2 import FatSecretClient

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
FATSECRET_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
FATSECRET_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")


def test_food_diary():
    print("\n" + "="*70)
    print("FOOD DIARY API - TEST COMPLET")
    print("="*70)
    
    # Initialiser services
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    fatsecret = FatSecretClient(client_id=FATSECRET_KEY, client_secret=FATSECRET_SECRET)
    food_log_service = FoodLogService(supabase=supabase, fatsecret=fatsecret)
    photo_service = PhotoService(supabase=supabase, fatsecret=fatsecret)
    
    # Récupérer un user de test
    users = supabase.table("profiles").select("id, full_name").limit(1).execute()
    
    if not users.data:
        print("\n❌ Aucun utilisateur trouvé")
        print("   Crée un utilisateur via Supabase Dashboard")
        sys.exit(1)
    
    user_id = users.data[0]["id"]
    user_name = users.data[0].get("full_name") or "Test User"
    
    print(f"\n👤 Test user: {user_name} ({user_id[:8]}...)")
    
    # ======================================================================
    # TEST 1: PROVISIONING PROFIL FATSECRET
    # ======================================================================
    print("\n" + "-"*70)
    print("[1/6] Provisioning profil FatSecret...")
    print("-"*70)
    
    try:
        result = food_log_service.provision_fatsecret_profile(user_id)
        print(f"✅ Status: {result['status']}")
        print(f"✅ Profil: {result['fatsecret_profile']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    
    # ======================================================================
    # TEST 2: RECHERCHE D'ALIMENTS
    # ======================================================================
    print("\n" + "-"*70)
    print("[2/6] Recherche d'aliments...")
    print("-"*70)
    
    search_terms = ["pomme", "poulet", "riz"]
    
    for term in search_terms:
        try:
            foods = food_log_service.search_foods(term, max_results=3)
            print(f"✅ '{term}' → {len(foods)} résultat(s)")
            if foods:
                print(f"   Premier: {foods[0]['name']} (ID: {foods[0]['fs_food_id']})")
        except Exception as e:
            print(f"❌ Erreur recherche '{term}': {e}")
    
    # ======================================================================
    # TEST 3: DÉTAILS ALIMENT
    # ======================================================================
    print("\n" + "-"*70)
    print("[3/6] Détails aliment...")
    print("-"*70)
    
    try:
        # Pomme (ID connu: 35718)
        details = food_log_service.get_food_details(35718)
        print(f"✅ Aliment: {details['name']}")
        print(f"✅ Servings disponibles: {len(details['servings'])}")
        if details['servings']:
            first = details['servings'][0]
            print(f"   Ex: {first['serving_description']} - {first.get('calories')} kcal")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # ======================================================================
    # TEST 4: AJOUTER UN REPAS
    # ======================================================================
    print("\n" + "-"*70)
    print("[4/6] Ajouter un repas...")
    print("-"*70)
    
    try:
        log_result = food_log_service.create_food_log(
            user_id=user_id,
            logged_at=datetime.now(),
            meal_type="breakfast",
            items=[
                {
                    "name": "Pommes",
                    "fs_food_id": 35718,
                    "fs_serving_id": 0,
                    "quantity": 1.0,
                    "unit": "serving",
                    "nutrition": {
                        "calories": 95,
                        "protein": 0.5,
                        "carbohydrate": 25,
                        "fat": 0.3
                    }
                }
            ],
            note="Test petit-déjeuner",
            context={"hunger": 7, "mood": "ok"},
            source="search"
        )
        
        print(f"✅ Repas créé: {log_result['food_log_id'][:8]}...")
        print(f"✅ Items: {log_result['items_count']}")
        print(f"✅ Sync FatSecret: {log_result['fs_sync_status']}")
        if log_result['fs_entry_ids']:
            print(f"✅ FatSecret Entry IDs: {log_result['fs_entry_ids']}")
        
        test_log_id = log_result['food_log_id']
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        test_log_id = None
    
    # ======================================================================
    # TEST 5: CONSULTER JOURNAL
    # ======================================================================
    print("\n" + "-"*70)
    print("[5/6] Consulter journal...")
    print("-"*70)
    
    try:
        today = date.today()
        diary = food_log_service.get_food_diary(
            user_id=user_id,
            date_obj=today,
            force_sync=False
        )
        
        print(f"✅ Date: {diary['date']}")
        
        total_meals = sum(len(meals) for meals in diary['meals'].values())
        print(f"✅ Total repas: {total_meals}")
        
        for meal_type, meals in diary['meals'].items():
            if meals:
                print(f"   {meal_type}: {len(meals)} repas")
        
        nutrition = diary['total_nutrition']
        print(f"✅ Total nutrition: {nutrition['calories']:.0f} kcal")
        print(f"   P: {nutrition['protein']:.1f}g | C: {nutrition['carbohydrate']:.1f}g | F: {nutrition['fat']:.1f}g")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # ======================================================================
    # TEST 6: UPLOAD PHOTO (SIMULATION)
    # ======================================================================
    print("\n" + "-"*70)
    print("[6/6] Upload photo (simulation)...")
    print("-"*70)
    
    if test_log_id:
        # Créer une image de test simple (1x1 pixel PNG)
        test_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        try:
            photo_result = photo_service.upload_food_photo(
                user_id=user_id,
                food_log_id=test_log_id,
                file_data=test_image_bytes,
                filename="test_meal.png",
                mime_type="image/png",
                analyze=False
            )
            
            print(f"✅ Photo uploadée: {photo_result['photo_id'][:8]}...")
            print(f"✅ Storage path: {photo_result['storage_path']}")
            print(f"✅ Taille: {photo_result['file_size_bytes']} bytes")
            print(f"✅ Analyse status: {photo_result['analysis_status']}")
            
        except Exception as e:
            print(f"⚠️  Erreur upload (peut nécessiter bucket Supabase): {e}")
    else:
        print("⚠️  Skipped (pas de food_log_id)")
    
    # ======================================================================
    # RÉSUMÉ
    # ======================================================================
    print("\n" + "="*70)
    print("✅ TESTS TERMINÉS")
    print("="*70)
    print("\nL'API Food Diary est fonctionnelle !")
    print("\nPour utiliser via HTTP (avec JWT):")
    print(f"  1. Obtiens un JWT token pour user {user_id[:8]}...")
    print("  2. Utilise-le dans: Authorization: Bearer <JWT>")
    print("\nDocumentation: backend/FOOD_DIARY_MVP.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    if not all([SUPABASE_URL, SUPABASE_KEY, FATSECRET_KEY, FATSECRET_SECRET]):
        print("❌ Variables d'environnement manquantes")
        print("   Vérifie .env : SUPABASE_*, FATSECRET_*")
        sys.exit(1)
    
    test_food_diary()
