#!/usr/bin/env python3
"""
Script pour ajouter un Personal Access Token (PAT) Oura pour un utilisateur

Usage:
    python3 add_oura_pat_token.py \\
        --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \\
        --pat-token "VOTRE_TOKEN_OURA_ICI"
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def add_oura_pat_token(user_id: str, pat_token: str):
    """Ajoute ou met à jour le PAT Oura pour un utilisateur"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Variables d'environnement manquantes")
        print("   SUPABASE_URL et SUPABASE_SERVICE_KEY requis")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    print(f"\n{'='*60}")
    print(f"Ajout du Personal Access Token Oura")
    print(f"{'='*60}\n")
    print(f"User ID: {user_id}")
    print(f"PAT Token: {pat_token[:10]}...\n")
    
    try:
        # Vérifier si l'utilisateur existe
        user_check = client.table("profiles").select("id, full_name").eq("id", user_id).execute()
        
        if not user_check.data:
            print(f"❌ Utilisateur {user_id} non trouvé dans la table profiles")
            sys.exit(1)
        
        user_name = user_check.data[0].get('full_name', 'Sans nom')
        print(f"✓ Utilisateur trouvé: {user_name}")
        
        # Vérifier si une entrée Oura existe déjà
        existing = client.table("external_identities").select("*").eq("supabase_user_id", user_id).eq("provider_system", "oura").execute()
        
        # Générer un external_user_id basé sur le token
        external_user_id = f"oura_pat_{user_id[:8]}"
        
        metadata = {
            "access_token": pat_token,
            "auth_method": "pat",
            "token_type": "Personal Access Token",
            "configured_at": datetime.utcnow().isoformat(),
            "note": "Personal Access Token Oura - ne expire pas"
        }
        
        if existing.data:
            # Mettre à jour l'entrée existante
            print(f"✓ Entrée Oura existante trouvée, mise à jour...")
            
            # Fusionner avec les métadonnées existantes (garder les credentials OAuth2 si présentes)
            existing_metadata = existing.data[0].get('metadata', {})
            if 'oauth2_client_id' in existing_metadata:
                metadata['oauth2_client_id'] = existing_metadata['oauth2_client_id']
            if 'oauth2_client_secret' in existing_metadata:
                metadata['oauth2_client_secret'] = existing_metadata['oauth2_client_secret']
            
            result = client.table("external_identities").update({
                "metadata": metadata,
                "external_user_id": external_user_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", existing.data[0]['id']).execute()
            
            print(f"✅ Personal Access Token ajouté pour l'utilisateur {user_id}")
            
        else:
            # Créer une nouvelle entrée
            print(f"✓ Création d'une nouvelle entrée Oura...")
            
            result = client.table("external_identities").insert({
                "supabase_user_id": user_id,
                "provider_system": "oura",
                "external_user_id": external_user_id,
                "metadata": metadata,
                "is_active": True
            }).execute()
            
            print(f"✅ Nouvelle entrée Oura créée avec PAT pour l'utilisateur {user_id}")
        
        print(f"\n{'='*60}")
        print(f"✅ Configuration terminée avec succès")
        print(f"{'='*60}\n")
        print(f"📋 Prochaines étapes:")
        print(f"   Synchroniser les données:")
        print(f"   python3 run_oura_sync.py --user-id {user_id}")
        print()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ajouter un Personal Access Token Oura pour un utilisateur"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='UUID de l\'utilisateur Supabase'
    )
    parser.add_argument(
        '--pat-token',
        required=True,
        help='Personal Access Token Oura (depuis cloud.ouraring.com)'
    )
    
    args = parser.parse_args()
    
    add_oura_pat_token(
        user_id=args.user_id,
        pat_token=args.pat_token
    )


if __name__ == "__main__":
    main()
