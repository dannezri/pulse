"""
Script pour créer un utilisateur de test dans Supabase Auth
et le lier à un profil utilisateur existant
"""

from supabase import create_client
import os
from dotenv import load_dotenv
import sys

load_dotenv()

def create_test_auth_user(
    existing_user_id: str = None,
    email: str = "test@pulse.com",
    password: str = "TestPassword123!"
):
    """
    Crée un utilisateur dans Supabase Auth
    
    Args:
        existing_user_id: UUID d'un utilisateur existant dans la table users (optionnel)
        email: Email pour la connexion
        password: Mot de passe (min 6 caractères)
    """
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY manquant dans .env")
        return None
    
    print("=" * 70)
    print("👤 Création d'un utilisateur de test dans Supabase Auth")
    print("=" * 70)
    print()
    
    # Créer un client avec service key
    supabase = create_client(supabase_url, supabase_service_key)
    
    try:
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
        # Vérifier si l'utilisateur existe déjà
        try:
            list_result = supabase.auth.admin.list_users()
            existing = [u for u in list_result if u.email == email]
            if existing:
                print(f"\n⚠️  Un utilisateur avec cet email existe déjà!")
                print(f"   User ID: {existing[0].id}")
                print(f"   Email confirmé: {existing[0].email_confirmed_at is not None}")
                
                user_id = existing[0].id
                
                print(f"\n💡 Pour obtenir un token JWT, exécutez:")
                print(f"   python get_jwt_token.py {email} {password}")
                
                return user_id
        except Exception as e:
            print(f"⚠️  Impossible de lister les utilisateurs: {e}")
        
        print(f"\n🔨 Création de l'utilisateur...")
        
        # Créer l'utilisateur
        create_params = {
            "email": email,
            "password": password,
            "email_confirm": True  # Confirmer l'email automatiquement
        }
        
        # Si on veut utiliser un UUID spécifique (pour lier à un profil existant)
        if existing_user_id:
            create_params["user_id"] = existing_user_id
            print(f"   📌 Utilisation de l'UUID existant: {existing_user_id}")
        
        result = supabase.auth.admin.create_user(create_params)
        
        if result and result.user:
            user_id = result.user.id
            
            print(f"\n✅ Utilisateur créé avec succès!")
            print(f"   User ID: {user_id}")
            print(f"   Email: {result.user.email}")
            print(f"   Email confirmé: {result.user.email_confirmed_at is not None}")
            
            # Si un profil existant était fourni
            if existing_user_id:
                print(f"\n   ✅ Lié au profil utilisateur existant: {existing_user_id}")
            else:
                print(f"\n   ⚠️  Cet utilisateur n'a pas encore de profil dans la table 'users'")
                print(f"       Vous devrez peut-être en créer un avec:")
                print(f"       python add_user.py --name 'Test User' --uuid {user_id}")
            
            print(f"\n🧪 Pour obtenir un token JWT et tester l'endpoint:")
            print(f"   python get_jwt_token.py {email} {password}")
            
            print(f"\n📋 Ou directement avec curl:")
            print(f"   # D'abord, récupérer le token:")
            print(f"   TOKEN=$(python get_jwt_token.py {email} {password} | grep -A1 'Token JWT' | tail -1)")
            print(f"   # Puis tester l'endpoint:")
            print(f"   curl -X GET http://localhost:9000/api/insights/latest -H \"Authorization: Bearer $TOKEN\"")
            
            return user_id
        else:
            print(f"❌ Échec de création: pas de résultat")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        print(f"\n💡 Détails de l'erreur:")
        print(f"   {type(e).__name__}: {str(e)}")
        
        if "already exists" in str(e).lower():
            print(f"\n   Cet utilisateur existe peut-être déjà.")
            print(f"   Essayez d'obtenir le token avec:")
            print(f"   python get_jwt_token.py {email} {password}")
        
        return None


if __name__ == "__main__":
    print()
    
    # Paramètres par défaut
    email = "test@pulse.com"
    password = "TestPassword123!"
    existing_user_id = None
    
    # Parser les arguments
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    if len(sys.argv) > 2:
        password = sys.argv[2]
    
    if len(sys.argv) > 3:
        existing_user_id = sys.argv[3]
    
    # Si aucun argument, utiliser l'UUID de l'exemple
    if len(sys.argv) == 1:
        existing_user_id = "61cd2b1d-4f67-41b9-b4e7-4c151375c5bb"
        print(f"💡 Utilisation des paramètres par défaut:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   Lier au user_id existant: {existing_user_id}")
        print()
        print(f"   Pour personnaliser: python {sys.argv[0]} <email> <password> [user_id]")
        print()
        
        response = input("Continuer? (y/n): ")
        if response.lower() != 'y':
            print("❌ Annulé")
            sys.exit(0)
    
    # Créer l'utilisateur
    user_id = create_test_auth_user(
        existing_user_id=existing_user_id,
        email=email,
        password=password
    )
    
    if user_id:
        print("\n" + "=" * 70)
        print("✅ Processus terminé avec succès!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Le processus a échoué")
        print("=" * 70)
