#!/usr/bin/env python3
"""
Script pour ajouter/mettre à jour les credentials OAuth2 Oura pour un utilisateur spécifique

Usage:
    python add_user_oura_credentials.py \\
        --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \\
        --client-id e7bb46a6-015d-4ffa-ad83-58ed64487655 \\
        --client-secret ZKWxVx0JVELxsQP2xKo-CsOITdhDNELSK9cGGHPCjhU
"""

import os
import sys
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def add_oura_credentials(user_id: str, client_id: str, client_secret: str):
    """Ajoute ou met à jour les credentials OAuth2 Oura pour un utilisateur"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Variables d'environnement manquantes")
        print("   SUPABASE_URL et SUPABASE_SERVICE_KEY requis")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    print(f"\n{'='*60}")
    print(f"Configuration OAuth2 Oura pour l'utilisateur")
    print(f"{'='*60}\n")
    print(f"User ID: {user_id}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret[:10]}...\n")
    
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
        
        metadata = {
            "oauth2_client_id": client_id,
            "oauth2_client_secret": client_secret,
            "configured_at": datetime.utcnow().isoformat(),
            "note": "Credentials OAuth2 spécifiques à cet utilisateur"
        }
        
        if existing.data:
            # Mettre à jour l'entrée existante
            print(f"✓ Entrée Oura existante trouvée, mise à jour...")
            
            # Fusionner avec les métadonnées existantes
            existing_metadata = existing.data[0].get('metadata', {})
            if existing_metadata:
                # Conserver les tokens existants si présents
                if 'access_token' in existing_metadata:
                    metadata['access_token'] = existing_metadata['access_token']
                if 'refresh_token' in existing_metadata:
                    metadata['refresh_token'] = existing_metadata['refresh_token']
                if 'expires_at' in existing_metadata:
                    metadata['expires_at'] = existing_metadata['expires_at']
                if 'auth_method' in existing_metadata:
                    metadata['auth_method'] = existing_metadata['auth_method']
            
            result = client.table("external_identities").update({
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", existing.data[0]['id']).execute()
            
            print(f"✅ Credentials OAuth2 mis à jour pour l'utilisateur {user_id}")
            
        else:
            # Créer une nouvelle entrée
            print(f"✓ Création d'une nouvelle entrée Oura...")
            
            # Générer un external_user_id temporaire (sera remplacé lors du flux OAuth2)
            external_user_id = f"oura_user_{user_id[:8]}"
            
            result = client.table("external_identities").insert({
                "supabase_user_id": user_id,
                "provider_system": "oura",
                "external_user_id": external_user_id,
                "metadata": metadata,
                "is_active": True
            }).execute()
            
            print(f"✅ Nouvelle entrée Oura créée pour l'utilisateur {user_id}")
        
        print(f"\n{'='*60}")
        print(f"✅ Configuration terminée avec succès")
        print(f"{'='*60}\n")
        print(f"📋 Prochaines étapes:")
        print(f"   1. L'utilisateur doit maintenant compléter le flux OAuth2")
        print(f"   2. Synchroniser les données:")
        print(f"      python run_oura_sync.py --user-id {user_id}")
        print()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ajouter les credentials OAuth2 Oura pour un utilisateur"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='UUID de l\'utilisateur Supabase'
    )
    parser.add_argument(
        '--client-id',
        required=True,
        help='OAuth2 Client ID Oura'
    )
    parser.add_argument(
        '--client-secret',
        required=True,
        help='OAuth2 Client Secret Oura'
    )
    
    args = parser.parse_args()
    
    add_oura_credentials(
        user_id=args.user_id,
        client_id=args.client_id,
        client_secret=args.client_secret
    )


if __name__ == "__main__":
    main()
