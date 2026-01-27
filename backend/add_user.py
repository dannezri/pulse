"""
Script pour ajouter un utilisateur dans Supabase

Ce script permet de créer un utilisateur de test avec tous les champs nécessaires
pour tester le système.

Usage:
    python add_user.py
"""

import os
import sys
import requests
from uuid import uuid4, UUID
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Configuration des couleurs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")

def print_step(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══ {message} ═══{Colors.RESET}")


def create_user_interactive():
    """Crée un utilisateur de manière interactive"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("CRÉATION D'UN UTILISATEUR DANS SUPABASE")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Vérifier les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print_error("Variables d'environnement manquantes")
        print_info("Assurez-vous d'avoir SUPABASE_URL et SUPABASE_SERVICE_KEY dans votre .env")
        return False
    
    try:
        client = create_client(supabase_url, supabase_key)
        print_success("Connexion à Supabase réussie")
    except Exception as e:
        print_error(f"Erreur de connexion: {e}")
        return False
    
    # Demander les informations
    print_step("Informations utilisateur")
    
    # Option 1: Créer un nouvel utilisateur auth.users
    # Option 2: Utiliser un UUID existant (pour lier à auth.users)
    use_existing_uuid = input(f"{Colors.YELLOW}Utiliser un UUID existant (pour lier à auth.users) ? (o/N): {Colors.RESET}").strip().lower()
    
    if use_existing_uuid == 'o':
        user_id = input(f"{Colors.YELLOW}Entrez l'UUID de l'utilisateur (doit exister dans auth.users): {Colors.RESET}").strip()
        if not user_id:
            print_error("UUID requis")
            return False
        # Vérifier que c'est un UUID valide
        try:
            UUID(user_id)
        except ValueError:
            print_error(f"'{user_id}' n'est pas un UUID valide")
            return False
    else:
        # Créer un nouvel utilisateur dans auth.users d'abord
        print_info("Création d'un nouvel utilisateur dans auth.users...")
        user_id = str(uuid4())
        
        # Créer l'utilisateur dans auth.users via l'API Admin
        try:
            admin_url = f"{supabase_url}/auth/v1/admin/users"
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
            
            # Générer un email et mot de passe temporaires
            email = f"test-{user_id[:8]}@example.com"
            password = str(uuid4())  # Mot de passe aléatoire
            
            auth_user_data = {
                "id": user_id,
                "email": email,
                "password": password,
                "email_confirm": True
            }
            
            auth_response = requests.post(admin_url, json=auth_user_data, headers=headers)
            
            if auth_response.status_code in [200, 201]:
                print_success(f"Utilisateur auth.users créé: {user_id}")
                print_info(f"Email temporaire: {email}")
            elif auth_response.status_code == 409:
                # L'utilisateur existe déjà, c'est OK
                print_info(f"Utilisateur auth.users existe déjà: {user_id}")
            else:
                print_error(f"Impossible de créer l'utilisateur auth.users: {auth_response.status_code}")
                print_error(f"Réponse: {auth_response.text}")
                print_info("Tentative de création du profil quand même...")
        except Exception as e:
            print_error(f"Erreur lors de la création de l'utilisateur auth.users: {e}")
            print_info("Tentative de création du profil quand même...")
        
        print_info(f"UUID généré: {user_id}")
    
    # Open Wearables User ID (obligatoire)
    open_wearables_user_id = input(f"{Colors.YELLOW}Entrez l'ID Open Wearables (obligatoire): {Colors.RESET}").strip()
    if not open_wearables_user_id:
        print_error("Open Wearables User ID requis")
        return False
    
    # Vérifier si cet ID existe déjà
    try:
        existing = client.table("profiles").select("id, full_name").eq("open_wearables_user_id", open_wearables_user_id).execute()
        if existing.data:
            print_error(f"Un utilisateur avec cet Open Wearables ID existe déjà:")
            print(f"   ID: {existing.data[0]['id']}")
            print(f"   Nom: {existing.data[0].get('full_name', 'N/A')}")
            update = input(f"{Colors.YELLOW}Voulez-vous le mettre à jour ? (o/N): {Colors.RESET}").strip().lower()
            if update != 'o':
                return False
            user_id = existing.data[0]['id']  # Utiliser l'ID existant
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        return False
    
    # Informations optionnelles
    full_name = input(f"{Colors.YELLOW}Nom complet (optionnel): {Colors.RESET}").strip() or None
    
    health_goal = input(f"{Colors.YELLOW}Objectif santé (energy/sleep/weight/focus) [energy]: {Colors.RESET}").strip() or "energy"
    if health_goal not in ["energy", "sleep", "weight", "focus"]:
        print_info("Objectif invalide, utilisation de 'energy' par défaut")
        health_goal = "energy"
    
    # Baselines (optionnelles)
    baseline_hrv_input = input(f"{Colors.YELLOW}Baseline HRV (ms, optionnel): {Colors.RESET}").strip()
    baseline_hrv = int(baseline_hrv_input) if baseline_hrv_input.isdigit() else None
    
    baseline_hr_input = input(f"{Colors.YELLOW}Baseline Rythme cardiaque au repos (bpm, optionnel): {Colors.RESET}").strip()
    baseline_hr = int(baseline_hr_input) if baseline_hr_input.isdigit() else None
    
    # Préparer les données
    user_data = {
        "id": user_id,
        "open_wearables_user_id": open_wearables_user_id,
        "health_goal": health_goal
    }
    
    if full_name:
        user_data["full_name"] = full_name
    if baseline_hrv is not None:
        user_data["baseline_hrv"] = baseline_hrv
    if baseline_hr is not None:
        user_data["baseline_resting_hr"] = baseline_hr
    
    # Afficher un résumé
    print_step("Résumé")
    print(f"UUID: {user_id}")
    print(f"Open Wearables ID: {open_wearables_user_id}")
    print(f"Nom: {full_name or 'N/A'}")
    print(f"Objectif: {health_goal}")
    print(f"Baseline HRV: {baseline_hrv or 'N/A'}")
    print(f"Baseline HR: {baseline_hr or 'N/A'}")
    
    confirm = input(f"\n{Colors.YELLOW}Confirmer la création ? (O/n): {Colors.RESET}").strip().lower()
    if confirm == 'n':
        print_info("Annulé")
        return False
    
    # Créer ou mettre à jour l'utilisateur
    print_step("Création/Mise à jour de l'utilisateur")
    
    try:
        # Utiliser upsert pour créer ou mettre à jour
        response = client.table("profiles").upsert(user_data).execute()
        
        if response.data:
            print_success("Utilisateur créé/mis à jour avec succès !")
            print(f"\n{Colors.BOLD}Informations de l'utilisateur:{Colors.RESET}")
            user = response.data[0]
            print(f"  UUID: {user['id']}")
            print(f"  Open Wearables ID: {user.get('open_wearables_user_id')}")
            print(f"  Nom: {user.get('full_name', 'N/A')}")
            print(f"  Objectif: {user.get('health_goal', 'energy')}")
            print(f"  Baseline HRV: {user.get('baseline_hrv', 'N/A')}")
            print(f"  Baseline HR: {user.get('baseline_resting_hr', 'N/A')}")
            return True
        else:
            print_error("Aucune donnée retournée")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors de la création: {e}")
        error_str = str(e)
        
        # Analyser l'erreur
        if "duplicate key" in error_str.lower() or "unique constraint" in error_str.lower():
            print_info("L'utilisateur existe déjà. Essayez de le mettre à jour.")
        elif "foreign key" in error_str.lower() or "violates foreign key constraint" in error_str.lower():
            print_error("L'UUID doit exister dans auth.users")
            print_info("Solutions:")
            print_info("  1. Créez d'abord un utilisateur dans Supabase Auth (Dashboard → Authentication)")
            print_info("  2. Utilisez l'UUID d'un utilisateur existant")
            print_info("  3. Le script devrait créer automatiquement l'utilisateur auth.users")
        elif "invalid input syntax for type uuid" in error_str.lower():
            print_error("L'UUID fourni n'est pas au bon format")
            print_info("Un UUID doit être au format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        elif "column" in error_str.lower() and "does not exist" in error_str.lower():
            print_info("Un champ n'existe pas dans la table. Exécutez la migration SQL d'abord.")
        
        return False


def create_user_quick(open_wearables_user_id: str, user_id: str = None, full_name: str = None):
    """Crée un utilisateur rapidement (pour les scripts)"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Variables d'environnement manquantes")
    
    client = create_client(supabase_url, supabase_key)
    
    if not user_id:
        user_id = str(uuid4())
        # Créer l'utilisateur dans auth.users
        try:
            admin_url = f"{supabase_url}/auth/v1/admin/users"
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
            
            email = f"test-{user_id[:8]}@example.com"
            password = str(uuid4())
            
            auth_user_data = {
                "id": user_id,
                "email": email,
                "password": password,
                "email_confirm": True
            }
            
            auth_response = requests.post(admin_url, json=auth_user_data, headers=headers)
            if auth_response.status_code not in [200, 201, 409]:  # 409 = déjà existant
                print(f"Warning: Could not create auth user: {auth_response.status_code}")
        except Exception as e:
            print(f"Warning: Could not create auth user: {e}")
    
    user_data = {
        "id": user_id,
        "open_wearables_user_id": open_wearables_user_id,
        "health_goal": "energy"
    }
    
    if full_name:
        user_data["full_name"] = full_name
    
    response = client.table("profiles").upsert(user_data).execute()
    return response.data[0] if response.data else None


def list_users():
    """Liste tous les utilisateurs"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("LISTE DES UTILISATEURS")
    print(f"{'='*60}{Colors.RESET}\n")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print_error("Variables d'environnement manquantes")
        return
    
    try:
        client = create_client(supabase_url, supabase_key)
        
        response = client.table("profiles").select("id, full_name, open_wearables_user_id, health_goal, baseline_hrv, baseline_resting_hr, created_at").order("created_at", desc=True).execute()
        
        if not response.data:
            print_info("Aucun utilisateur trouvé")
            return
        
        print(f"Total: {len(response.data)} utilisateur(s)\n")
        
        for i, user in enumerate(response.data, 1):
            print(f"{Colors.BOLD}{i}. {user.get('full_name', 'Sans nom')}{Colors.RESET}")
            print(f"   UUID: {user['id']}")
            print(f"   Open Wearables ID: {user.get('open_wearables_user_id', 'N/A')}")
            print(f"   Objectif: {user.get('health_goal', 'energy')}")
            print(f"   Baseline HRV: {user.get('baseline_hrv', 'N/A')}")
            print(f"   Baseline HR: {user.get('baseline_resting_hr', 'N/A')}")
            print(f"   Créé le: {user.get('created_at', 'N/A')}")
            print()
            
    except Exception as e:
        print_error(f"Erreur: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gérer les utilisateurs Supabase")
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister tous les utilisateurs"
    )
    parser.add_argument(
        "--quick",
        nargs=2,
        metavar=("OPEN_WEARABLES_ID", "FULL_NAME"),
        help="Créer rapidement un utilisateur: --quick 'user-123' 'John Doe'"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.quick:
        open_wearables_id, full_name = args.quick
        try:
            user = create_user_quick(open_wearables_id, full_name=full_name)
            if user:
                print_success(f"Utilisateur créé: {user['id']}")
            else:
                print_error("Échec de la création")
        except Exception as e:
            print_error(f"Erreur: {e}")
    else:
        # Mode interactif
        success = create_user_interactive()
        sys.exit(0 if success else 1)
