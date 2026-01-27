"""
Script pour obtenir un token JWT Supabase pour tester les endpoints protégés
"""

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def get_jwt_token(user_id: str = None, email: str = None, password: str = None):
    """
    Obtient un token JWT Supabase de deux façons:
    1. Si user_id fourni: génère un token admin directement (nécessite SERVICE_KEY)
    2. Si email/password fournis: se connecte et récupère le token
    """
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL manquant dans .env")
        return
    
    # Option 1: Générer un token admin pour un user_id (pour tests)
    if user_id:
        if not supabase_service_key:
            print("❌ SUPABASE_SERVICE_KEY manquant dans .env")
            return
        
        print(f"🔑 Génération d'un token JWT pour user_id: {user_id}")
        print("\n⚠️  ATTENTION: Cette méthode utilise la SERVICE_KEY.")
        print("    En production, utilisez l'authentification normale (email/password)\n")
        
        # Créer un client avec service key
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Vérifier que l'utilisateur existe
        try:
            result = supabase.auth.admin.get_user_by_id(user_id)
            if result:
                print(f"✅ Utilisateur trouvé: {result.user.email if result.user.email else 'pas d email'}")
        except Exception as e:
            print(f"⚠️  Utilisateur non trouvé dans Supabase Auth: {e}")
            print("   Cet utilisateur existe peut-être dans la table users mais pas dans auth.users")
            print("   Le token généré pourrait ne pas fonctionner.\n")
        
        # Générer un token admin pour cet utilisateur
        # Note: Supabase Python SDK n'a pas de méthode directe pour générer un JWT custom
        # On utilise la méthode sign_in pour créer une session
        
        print("\n💡 Pour obtenir un JWT, vous devez:")
        print("   1. Créer un utilisateur dans Supabase Auth si nécessaire")
        print("   2. Utiliser l'option email/password ci-dessous\n")
        
        return
    
    # Option 2: Se connecter avec email/password
    if email and password:
        if not supabase_anon_key:
            print("❌ SUPABASE_ANON_KEY manquant dans .env")
            return
        
        print(f"🔐 Connexion avec email: {email}")
        
        # Créer un client avec anon key
        supabase = create_client(supabase_url, supabase_anon_key)
        
        try:
            # Se connecter
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.session:
                token = response.session.access_token
                user_id = response.user.id
                
                print(f"✅ Connexion réussie!")
                print(f"   User ID: {user_id}")
                print(f"\n📋 Token JWT (copier-coller pour curl):\n")
                print(f"{token}")
                print(f"\n\n🧪 Commande curl pour tester l'endpoint:\n")
                print(f'curl -X GET http://localhost:9000/api/insights/latest \\')
                print(f'  -H "Authorization: Bearer {token}"')
                print(f"\n\n💾 Pour exporter dans votre terminal:\n")
                print(f'export TOKEN="{token}"')
                print(f'curl -X GET http://localhost:9000/api/insights/latest -H "Authorization: Bearer $TOKEN"')
                
                return token
            else:
                print("❌ Échec de connexion: pas de session")
                return None
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return None
    
    # Aucune option fournie
    print("❌ Vous devez fournir soit:")
    print("   - user_id (pour info)")
    print("   - email ET password (pour obtenir un token)")


if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("🔐 Script d'obtention de token JWT Supabase")
    print("=" * 70)
    print()
    
    # Vérifier les arguments
    if len(sys.argv) == 2:
        # Un seul argument = user_id (mode info)
        get_jwt_token(user_id=sys.argv[1])
    elif len(sys.argv) == 3:
        # Deux arguments = email + password
        get_jwt_token(email=sys.argv[1], password=sys.argv[2])
    else:
        # Mode interactif
        print("Usage:")
        print(f"  python {sys.argv[0]} <email> <password>")
        print(f"  python {sys.argv[0]} <user_id>  # Info uniquement")
        print()
        
        # Essayer avec user_id par défaut de l'exemple
        default_user_id = "61cd2b1d-4f67-41b9-b4e7-4c151375c5bb"
        
        print(f"🔍 Test avec user_id par défaut: {default_user_id}")
        print()
        
        # Créer un compte de test si nécessaire
        print("📝 Pour créer un compte de test dans Supabase Auth:")
        print("   1. Via Dashboard Supabase > Authentication > Users > Add User")
        print("   2. Ou via Python:")
        print()
        print("from supabase import create_client")
        print("supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)")
        print("supabase.auth.admin.create_user({")
        print('    "email": "test@pulse.com",')
        print('    "password": "TestPassword123!",')
        print('    "email_confirm": True')
        print("})")
        print()
        print("Ensuite, exécutez ce script avec:")
        print(f"  python {sys.argv[0]} test@pulse.com TestPassword123!")
