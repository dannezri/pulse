"""
Script pour créer un utilisateur avec identité Vital

Ce script permet de créer un utilisateur Pulse et lier son ID Vital
sans passer par Open Wearables.

Usage:
    python create_vital_user.py
"""

import os
import sys
import requests
from uuid import uuid4
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


def create_vital_user():
    """Crée un utilisateur avec identité Vital"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("CRÉATION D'UN UTILISATEUR VITAL DANS SUPABASE")
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
    
    # Vital User ID (obligatoire)
    vital_user_id = input(f"{Colors.YELLOW}Entrez l'ID utilisateur Vital (obligatoire): {Colors.RESET}").strip()
    if not vital_user_id:
        print_error("Vital User ID requis")
        return False
    
    # Vérifier si cet ID Vital existe déjà
    try:
        existing = client.table("external_identities").select("supabase_user_id").eq("provider_system", "vital").eq("external_user_id", vital_user_id).execute()
        if existing.data:
            print_error(f"Un utilisateur avec cet ID Vital existe déjà:")
            print(f"   Supabase User ID: {existing.data[0]['supabase_user_id']}")
            return False
    except Exception as e:
        print_error(f"Erreur lors de la vérification: {e}")
        return False
    
    # Informations utilisateur
    full_name = input(f"{Colors.YELLOW}Nom complet (optionnel): {Colors.RESET}").strip() or None
    
    health_goal = input(f"{Colors.YELLOW}Objectif santé (energy/sleep/weight/focus) [energy]: {Colors.RESET}").strip() or "energy"
    if health_goal not in ["energy", "sleep", "weight", "focus"]:
        print_info("Objectif invalide, utilisation de 'energy' par défaut")
        health_goal = "energy"
    
    # Générer un UUID pour l'utilisateur
    user_id = str(uuid4())
    
    # Créer l'utilisateur dans auth.users
    print_step("Création de l'utilisateur auth.users")
    try:
        admin_url = f"{supabase_url}/auth/v1/admin/users"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        email = f"vital-{user_id[:8]}@example.com"
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
        else:
            print_error(f"Impossible de créer l'utilisateur auth.users: {auth_response.status_code}")
            print_info("Tentative de création du profil quand même...")
    except Exception as e:
        print_error(f"Erreur lors de la création de l'utilisateur auth.users: {e}")
        print_info("Tentative de création du profil quand même...")
    
    # Afficher un résumé
    print_step("Résumé")
    print(f"UUID Supabase: {user_id}")
    print(f"Vital User ID: {vital_user_id}")
    print(f"Nom: {full_name or 'N/A'}")
    print(f"Objectif: {health_goal}")
    
    confirm = input(f"\n{Colors.YELLOW}Confirmer la création ? (O/n): {Colors.RESET}").strip().lower()
    if confirm == 'n':
        print_info("Annulé")
        return False
    
    # Créer le profil (sans open_wearables_user_id)
    print_step("Création du profil")
    
    try:
        profile_data = {
            "id": user_id,
            "health_goal": health_goal
        }
        
        if full_name:
            profile_data["full_name"] = full_name
        
        profile_response = client.table("profiles").insert(profile_data).execute()
        
        if profile_response.data:
            print_success("Profil créé avec succès")
        else:
            print_error("Erreur lors de la création du profil")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors de la création du profil: {e}")
        return False
    
    # Créer l'identité externe Vital
    print_step("Liaison de l'identité Vital")
    
    try:
        identity_data = {
            "id": str(uuid4()),
            "supabase_user_id": user_id,
            "provider_system": "vital",
            "external_user_id": vital_user_id,
            "is_active": True
        }
        
        identity_response = client.table("external_identities").insert(identity_data).execute()
        
        if identity_response.data:
            print_success(f"Identité Vital liée: {vital_user_id} -> {user_id}")
        else:
            print_error("Erreur lors de la liaison de l'identité Vital")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors de la liaison de l'identité Vital: {e}")
        return False
    
    # Succès final
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
    print("✅ UTILISATEUR VITAL CRÉÉ AVEC SUCCÈS")
    print(f"{'='*60}{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Informations:{Colors.RESET}")
    print(f"  UUID Supabase: {user_id}")
    print(f"  Vital User ID: {vital_user_id}")
    print(f"  Nom: {full_name or 'N/A'}")
    print(f"  Objectif: {health_goal}")
    
    print(f"\n{Colors.YELLOW}Vous pouvez maintenant envoyer des webhooks Vital avec user_id={vital_user_id}{Colors.RESET}")
    
    return True


if __name__ == "__main__":
    success = create_vital_user()
    sys.exit(0 if success else 1)
