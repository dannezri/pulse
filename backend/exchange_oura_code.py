#!/usr/bin/env python3
"""
Script pour échanger un code OAuth2 Oura contre des tokens

Usage:
    python3 exchange_oura_code.py \
        --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1 \
        --code oaccBt7d63BhvCsR2lfhE5oxtekOYNqt
"""

import os
import sys
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def exchange_code(user_id: str, code: str):
    """Échange le code OAuth2 contre des tokens"""
    
    print(f"\n{'='*60}")
    print(f"Échange du code OAuth2 Oura")
    print(f"{'='*60}\n")
    
    # Charger les configs
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    client_id = os.getenv("OURA_CLIENT_ID")
    client_secret = os.getenv("OURA_CLIENT_SECRET")
    redirect_uri = os.getenv("OURA_REDIRECT_URI", "http://localhost:9000/api/oura/callback")
    
    if not all([supabase_url, supabase_key, client_id, client_secret]):
        print("❌ Variables d'environnement manquantes")
        sys.exit(1)
    
    print(f"User ID: {user_id}")
    print(f"Code: {code[:20]}...")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print()
    
    # Échanger le code contre des tokens
    token_url = "https://api.ouraring.com/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    print("🔄 Échange du code contre les tokens...")
    print(f"   Token URL: {token_url}")
    print(f"   Data envoyée:")
    for key, value in data.items():
        if key in ['client_secret', 'code']:
            print(f"     {key}: {value[:20]}...")
        else:
            print(f"     {key}: {value}")
    print()
    
    try:
        response = requests.post(token_url, data=data)
        
        # Debug de la réponse
        print(f"   Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response Headers: {dict(response.headers)}")
            print(f"   Response Body: {response.text}")
        
        response.raise_for_status()
        
        tokens = response.json()
        
        print(f"✅ Tokens obtenus avec succès!")
        print(f"   Access Token: {tokens['access_token'][:30]}...")
        print(f"   Refresh Token: {tokens.get('refresh_token', 'N/A')[:30] if tokens.get('refresh_token') else 'N/A'}...")
        print(f"   Expires In: {tokens.get('expires_in', 'N/A')} secondes")
        print()
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur lors de l'échange du code: {e}")
        print(f"   Status: {e.response.status_code}")
        print(f"   Réponse: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    
    # Sauvegarder les tokens dans Supabase
    print("💾 Sauvegarde des tokens dans Supabase...")
    
    client = create_client(supabase_url, supabase_key)
    
    # Calculer la date d'expiration
    expires_in = tokens.get('expires_in', 86400)
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    
    metadata = {
        "access_token": tokens['access_token'],
        "refresh_token": tokens.get('refresh_token'),
        "expires_at": expires_at,
        "token_type": tokens.get('token_type', 'Bearer'),
        "auth_method": "oauth2",
        "configured_at": datetime.utcnow().isoformat(),
        "oauth2_client_id": client_id,
        "oauth2_client_secret": client_secret
    }
    
    try:
        # Vérifier si une entrée existe déjà
        existing = client.table("external_identities").select("*").eq("supabase_user_id", user_id).eq("provider_system", "oura").execute()
        
        if existing.data:
            # Mettre à jour
            result = client.table("external_identities").update({
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", existing.data[0]['id']).execute()
            
            print(f"✅ Tokens mis à jour dans external_identities")
        else:
            # Créer une nouvelle entrée
            external_user_id = f"oura_oauth_{user_id[:8]}"
            
            result = client.table("external_identities").insert({
                "supabase_user_id": user_id,
                "provider_system": "oura",
                "external_user_id": external_user_id,
                "metadata": metadata,
                "is_active": True
            }).execute()
            
            print(f"✅ Nouvelle entrée créée dans external_identities")
        
        print(f"   User ID: {user_id}")
        print(f"   Access Token expire le: {expires_at}")
        print()
        
        print(f"{'='*60}")
        print(f"✅ CONFIGURATION OAUTH2 TERMINÉE AVEC SUCCÈS!")
        print(f"{'='*60}\n")
        print(f"Prochaines étapes:")
        print(f"  python3 run_oura_sync.py --user-id {user_id}")
        print()
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Échanger un code OAuth2 Oura contre des tokens"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='UUID de l\'utilisateur Supabase'
    )
    parser.add_argument(
        '--code',
        required=True,
        help='Code d\'autorisation OAuth2 depuis l\'URL de callback'
    )
    
    args = parser.parse_args()
    exchange_code(args.user_id, args.code)


if __name__ == "__main__":
    main()
