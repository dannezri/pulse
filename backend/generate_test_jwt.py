#!/usr/bin/env python3
"""
Génère un JWT token de test pour un utilisateur Supabase
Usage: python3 generate_test_jwt.py <user_email>
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def generate_jwt_for_user(email: str):
    """
    Génère un JWT token pour un utilisateur via Supabase Admin API
    """
    print("\n" + "="*70)
    print("GENERATE JWT TOKEN")
    print("="*70)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Trouver l'utilisateur dans auth.users
    try:
        # Récupérer l'user depuis la table profiles
        profile = supabase.table("profiles").select("id").limit(1).execute()
        
        if not profile.data:
            print(f"\n❌ Aucun utilisateur trouvé")
            return
        
        user_id = profile.data[0]["id"]
        
        print(f"\n✅ User trouvé: {user_id}")
        print(f"\nℹ️  Pour obtenir un JWT token, tu dois:")
        print("\n1. **Depuis l'app mobile** (méthode recommandée):")
        print("   ```typescript")
        print("   const { data: { session } } = await supabase.auth.getSession()")
        print("   const jwt = session?.access_token")
        print("   console.log('JWT:', jwt)")
        print("   ```")
        print("\n2. **Se connecter via l'API Supabase**:")
        print(f"   User ID: {user_id}")
        print("   Email: test@pulse.com (ou autre)")
        print("   Password: <ton_mot_de_passe>")
        print("\n3. **Pour les tests, utilise le script qui bypass JWT**:")
        print("   python3 test_food_diary_api.py")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "test@pulse.com"
    
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("❌ Variables d'environnement manquantes")
        print("   Vérifie .env : SUPABASE_URL, SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    generate_jwt_for_user(email)
