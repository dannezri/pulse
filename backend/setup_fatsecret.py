"""
Script interactif pour créer un profil FatSecret pour un utilisateur
Usage: python setup_fatsecret.py

Ce script crée un profil FatSecret vide lié à l'utilisateur Pulse.
L'utilisateur pourra ensuite enregistrer ses repas via l'app Pulse.
"""

import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from supabase_client import SupabaseClient
from fatsecret_client import get_fatsecret_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_fatsecret_profile(
    user_id: str,
    supabase: SupabaseClient
) -> bool:
    """
    Crée un profil FatSecret pour un utilisateur Pulse
    
    Args:
        user_id: UUID de l'utilisateur Supabase
        supabase: Client Supabase
    
    Returns:
        True si le profil a été créé avec succès
    """
    try:
        # Initialiser le client FatSecret
        client = get_fatsecret_client()
        
        print("\n" + "=" * 70)
        print("CRÉATION DE PROFIL FATSECRET")
        print("=" * 70)
        print()
        print(f"Utilisateur: {user_id}")
        print()
        
        # Vérifier si un profil existe déjà
        existing = supabase.client.table("fatsecret_connections").select("*").eq(
            "user_id", user_id
        ).execute()
        
        if existing.data and len(existing.data) > 0:
            print("⚠️  Un profil FatSecret existe déjà pour cet utilisateur.")
            print()
            conn = existing.data[0]
            print(f"   Token: {conn['oauth_token'][:30]}...")
            print(f"   Connecté le: {conn['connected_at']}")
            print()
            
            response = input("Voulez-vous le recréer ? (y/n): ").strip().lower()
            if response != 'y':
                print("\nAnnulé.")
                return False
            print()
        
        # Créer le profil FatSecret
        print("[1/2] Création du profil FatSecret...")
        profile = client.create_profile(user_id=user_id)
        
        auth_token = profile["auth_token"]
        auth_secret = profile["auth_secret"]
        
        print(f"✓ Profil créé!")
        print(f"   Auth Token: {auth_token[:30]}...")
        print(f"   Auth Secret: {auth_secret[:30]}...")
        print()
        
        # Stocker dans Supabase
        print("[2/2] Sauvegarde dans Supabase...")
        
        connection_data = {
            "user_id": user_id,
            "oauth_token": auth_token,
            "oauth_token_secret": auth_secret,
            "is_active": True,
            "metadata": {
                "profile_type": "created",
                "source": "setup_script"
            }
        }
        
        if existing.data and len(existing.data) > 0:
            # Mise à jour
            supabase.client.table("fatsecret_connections").update({
                "oauth_token": auth_token,
                "oauth_token_secret": auth_secret,
                "is_active": True,
                "metadata": connection_data["metadata"]
            }).eq("user_id", user_id).execute()
        else:
            # Création
            supabase.client.table("fatsecret_connections").insert(
                connection_data
            ).execute()
        
        print("✓ Sauvegardé dans Supabase")
        print()
        print("=" * 70)
        print("✅ PROFIL FATSECRET CRÉÉ AVEC SUCCÈS !")
        print("=" * 70)
        print()
        print("L'utilisateur peut maintenant:")
        print("  • Enregistrer des repas via l'app Pulse")
        print("  • Consulter son journal alimentaire")
        print("  • Les données seront synchronisées automatiquement")
        print()
        print("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"Error during FatSecret profile setup: {e}")
        print(f"\n❌ Erreur: {e}")
        return False


def disconnect_fatsecret(user_id: str, supabase: SupabaseClient) -> bool:
    """
    Déconnecte un utilisateur FatSecret
    
    Args:
        user_id: UUID de l'utilisateur
        supabase: Client Supabase
    
    Returns:
        True si la déconnexion a réussi
    """
    try:
        result = supabase.client.table("fatsecret_connections").update({
            "is_active": False
        }).eq("user_id", user_id).execute()
        
        logger.info(f"FatSecret connection disabled for user {user_id}")
        print(f"\n✓ Profil FatSecret désactivé pour l'utilisateur {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error disconnecting FatSecret: {e}")
        return False


def list_connections(supabase: SupabaseClient) -> None:
    """
    Liste tous les profils FatSecret actifs
    
    Args:
        supabase: Client Supabase
    """
    try:
        result = supabase.client.table("fatsecret_connections").select(
            "user_id, connected_at, last_synced_date, is_active"
        ).execute()
        
        connections = result.data
        
        print("\n" + "=" * 70)
        print("PROFILS FATSECRET")
        print("=" * 70)
        
        if not connections:
            print("\nAucun profil trouvé.")
        else:
            print(f"\n{len(connections)} profil(s) trouvé(s):\n")
            for conn in connections:
                status = "✓ Actif" if conn["is_active"] else "✗ Inactif"
                print(f"  User ID: {conn['user_id']}")
                print(f"  Status: {status}")
                print(f"  Créé le: {conn['connected_at']}")
                print(f"  Dernière sync: {conn['last_synced_date'] or 'Jamais'}")
                print()
        
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Error listing connections: {e}")


def main():
    """Fonction principale"""
    # Charger les credentials depuis l'environnement
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    FATSECRET_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
    FATSECRET_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")
    
    missing = []
    if not FATSECRET_KEY:
        missing.append("FATSECRET_CONSUMER_KEY")
    if not FATSECRET_SECRET:
        missing.append("FATSECRET_CONSUMER_SECRET")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_KEY")
    
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        print(f"\n❌ Variables d'environnement manquantes: {', '.join(missing)}")
        sys.exit(1)
    
    # Initialiser Supabase
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    
    # Menu interactif
    print("\n" + "=" * 70)
    print("FATSECRET SETUP - Gestion des profils")
    print("=" * 70)
    print("\nOptions:")
    print("  1. Créer un profil pour un utilisateur")
    print("  2. Désactiver un profil")
    print("  3. Lister les profils existants")
    print("  4. Quitter")
    print("=" * 70)
    
    choice = input("\nVotre choix (1-4): ").strip()
    
    if choice == "1":
        # Créer un profil
        user_id = input("\nUUID de l'utilisateur Supabase: ").strip()
        if not user_id:
            print("❌ UUID requis")
            sys.exit(1)
        
        success = setup_fatsecret_profile(user_id, supabase)
        sys.exit(0 if success else 1)
    
    elif choice == "2":
        # Désactiver un profil
        user_id = input("\nUUID de l'utilisateur à désactiver: ").strip()
        if not user_id:
            print("❌ UUID requis")
            sys.exit(1)
        
        success = disconnect_fatsecret(user_id, supabase)
        sys.exit(0 if success else 1)
    
    elif choice == "3":
        # Lister les profils
        list_connections(supabase)
        sys.exit(0)
    
    elif choice == "4":
        print("\nAu revoir!")
        sys.exit(0)
    
    else:
        print("\n❌ Choix invalide")
        sys.exit(1)


if __name__ == "__main__":
    main()
