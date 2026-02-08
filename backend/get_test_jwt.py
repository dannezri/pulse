#!/usr/bin/env python3
"""
Script pour obtenir un JWT token de test
Usage: python3 get_test_jwt.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*70)
    print("GET TEST JWT TOKEN")
    print("="*70)
    
    # Lister les users disponibles
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    users = supabase.table("profiles").select("id, full_name").limit(10).execute()
    
    if not users.data:
        print("\n❌ Aucun utilisateur trouvé dans profiles")
        print("   Crée d'abord un utilisateur via Supabase Dashboard")
        return
    
    print(f"\n📋 Utilisateurs disponibles ({len(users.data)}):")
    for i, user in enumerate(users.data, 1):
        name = user.get("full_name") or "Sans nom"
        print(f"  {i}. {user['id'][:8]}... ({name})")
    
    # Utiliser le premier user par défaut
    test_user_id = users.data[0]["id"]
    
    # Vérifier si le user a un profil FatSecret
    profile = supabase.table("fatsecret_profiles").select("*").eq("user_id", test_user_id).execute()
    
    if profile.data:
        print(f"\n✅ User {test_user_id[:8]}... a un profil FatSecret actif")
    else:
        print(f"\n⚠️  User {test_user_id[:8]}... n'a pas encore de profil FatSecret")
        print("   → Sera créé automatiquement au premier appel")
    
    print("\n" + "="*70)
    print("🔑 Pour obtenir un vrai JWT:")
    print("="*70)
    print("\n1. Via Supabase Auth (Login):")
    print("   → Connecte-toi dans l'app mobile Pulse")
    print("   → Récupère le token depuis AsyncStorage ou Supabase client")
    print()
    print("2. Via Supabase Dashboard:")
    print("   → Authentication → Users → Sélectionne un user")
    print("   → Copy Access Token (JWT)")
    print()
    print("3. Ou utilise le script de test qui bypass JWT:")
    print("   → python3 test_food_diary_api.py")
    print()
    print(f"User ID de test suggéré: {test_user_id}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
