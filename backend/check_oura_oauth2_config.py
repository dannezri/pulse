#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier la configuration OAuth2 Oura

Usage:
    python3 check_oura_oauth2_config.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def check_config(user_id: str):
    """Vérifie la configuration OAuth2 Oura"""
    
    print(f"\n{'='*70}")
    print(f"  DIAGNOSTIC CONFIGURATION OAUTH2 OURA")
    print(f"{'='*70}\n")
    
    # 1. Vérifier les variables d'environnement
    print("1️⃣  Variables d'environnement (.env)")
    print("-" * 60)
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    oura_client_id = os.getenv("OURA_CLIENT_ID")
    oura_client_secret = os.getenv("OURA_CLIENT_SECRET")
    oura_redirect_uri = os.getenv("OURA_REDIRECT_URI")
    
    if supabase_url:
        print(f"   ✅ SUPABASE_URL: {supabase_url}")
    else:
        print(f"   ❌ SUPABASE_URL: MANQUANT")
    
    if supabase_key:
        print(f"   ✅ SUPABASE_SERVICE_KEY: {supabase_key[:20]}...")
    else:
        print(f"   ❌ SUPABASE_SERVICE_KEY: MANQUANT")
    
    if oura_client_id:
        print(f"   ✅ OURA_CLIENT_ID: {oura_client_id}")
    else:
        print(f"   ⚠️  OURA_CLIENT_ID: MANQUANT (utilisera les credentials de l'utilisateur)")
    
    if oura_client_secret:
        print(f"   ✅ OURA_CLIENT_SECRET: {oura_client_secret[:10]}...")
    else:
        print(f"   ⚠️  OURA_CLIENT_SECRET: MANQUANT (utilisera les credentials de l'utilisateur)")
    
    if oura_redirect_uri:
        print(f"   ✅ OURA_REDIRECT_URI: {oura_redirect_uri}")
    else:
        print(f"   ⚠️  OURA_REDIRECT_URI: MANQUANT (utilisera http://localhost:8000/api/oura/oauth/callback)")
    
    print()
    
    # 2. Vérifier l'utilisateur dans Supabase
    if not supabase_url or not supabase_key:
        print("❌ Impossible de se connecter à Supabase")
        return
    
    client = create_client(supabase_url, supabase_key)
    
    print("2️⃣  Utilisateur Supabase")
    print("-" * 60)
    
    try:
        user_result = client.table("profiles").select("id, full_name").eq("id", user_id).execute()
        
        if user_result.data:
            user = user_result.data[0]
            print(f"   ✅ Utilisateur trouvé: {user.get('full_name', 'Sans nom')}")
            print(f"      ID: {user['id']}")
        else:
            print(f"   ❌ Utilisateur {user_id} non trouvé")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    print()
    
    # 3. Vérifier les credentials Oura de l'utilisateur
    print("3️⃣  Credentials OAuth2 Oura")
    print("-" * 60)
    
    try:
        oura_result = client.table("external_identities").select("*").eq("supabase_user_id", user_id).eq("provider_system", "oura").execute()
        
        if oura_result.data:
            oura_identity = oura_result.data[0]
            metadata = oura_identity.get('metadata', {})
            
            print(f"   ✅ Entrée Oura trouvée")
            print(f"      External User ID: {oura_identity.get('external_user_id')}")
            print(f"      Active: {oura_identity.get('is_active')}")
            print()
            
            # Credentials OAuth2
            user_client_id = metadata.get('oauth2_client_id')
            user_client_secret = metadata.get('oauth2_client_secret')
            
            if user_client_id:
                print(f"   ✅ OAuth2 Client ID (utilisateur): {user_client_id}")
            else:
                print(f"   ⚠️  OAuth2 Client ID (utilisateur): MANQUANT")
            
            if user_client_secret:
                print(f"   ✅ OAuth2 Client Secret (utilisateur): {user_client_secret[:10]}...")
            else:
                print(f"   ⚠️  OAuth2 Client Secret (utilisateur): MANQUANT")
            
            print()
            
            # Tokens OAuth2
            access_token = metadata.get('access_token')
            refresh_token = metadata.get('refresh_token')
            expires_at = metadata.get('expires_at')
            auth_method = metadata.get('auth_method')
            
            if access_token:
                print(f"   ✅ Access Token: {access_token[:20]}...")
            else:
                print(f"   ❌ Access Token: MANQUANT")
            
            if refresh_token:
                print(f"   ✅ Refresh Token: {refresh_token[:20]}...")
            else:
                print(f"   ⚠️  Refresh Token: MANQUANT")
            
            if expires_at:
                print(f"   ℹ️  Expire le: {expires_at}")
            
            if auth_method:
                print(f"   ℹ️  Méthode d'auth: {auth_method}")
            else:
                print(f"   ⚠️  Méthode d'auth: NON SPÉCIFIÉE")
        else:
            print(f"   ❌ Aucune entrée Oura trouvée pour cet utilisateur")
            print(f"   💡 Exécutez:")
            print(f"      python3 add_user_oura_credentials.py --user-id {user_id} --client-id ... --client-secret ...")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print()
    
    # 4. Configuration recommandée
    print("4️⃣  Configuration OAuth2 finale")
    print("-" * 60)
    
    # Déterminer les credentials à utiliser
    final_client_id = None
    final_client_secret = None
    
    if oura_result.data:
        metadata = oura_result.data[0].get('metadata', {})
        final_client_id = metadata.get('oauth2_client_id') or oura_client_id
        final_client_secret = metadata.get('oauth2_client_secret') or oura_client_secret
    else:
        final_client_id = oura_client_id
        final_client_secret = oura_client_secret
    
    if final_client_id and final_client_secret:
        print(f"   Client ID à utiliser: {final_client_id}")
        print(f"   Client Secret à utiliser: {final_client_secret[:10]}...")
        print(f"   Redirect URI: http://localhost:8000/api/oura/oauth/callback")
        print()
        print(f"   ⚠️  IMPORTANT:")
        print(f"   Ces credentials DOIVENT être configurées dans votre application Oura Cloud:")
        print(f"   1. Allez sur https://cloud.ouraring.com/oauth/applications")
        print(f"   2. Sélectionnez votre application (Client ID: {final_client_id})")
        print(f"   3. Vérifiez que le Redirect URI est EXACTEMENT:")
        print(f"      http://localhost:8000/api/oura/oauth/callback")
        print(f"   4. Vérifiez que tous les scopes sont autorisés")
    else:
        print(f"   ❌ Credentials OAuth2 manquantes")
        print(f"   💡 Solutions:")
        print(f"      1. Ajouter dans .env: OURA_CLIENT_ID et OURA_CLIENT_SECRET")
        print(f"      2. Ou exécuter: python3 add_user_oura_credentials.py --user-id {user_id} ...")
    
    print()
    
    # 5. Diagnostic de l'erreur 400
    print("5️⃣  Diagnostic de l'erreur 400 Invalid Request")
    print("-" * 60)
    print(f"   L'erreur 400 peut être causée par:")
    print()
    print(f"   ❌ Redirect URI non configuré dans l'application Oura")
    print(f"      → Vérifiez sur https://cloud.ouraring.com/oauth/applications")
    print(f"      → Le Redirect URI doit être EXACTEMENT: http://localhost:8000/api/oura/oauth/callback")
    print()
    print(f"   ❌ Client ID invalide ou application désactivée")
    print(f"      → Vérifiez que l'application existe et est active")
    print()
    print(f"   ❌ Scopes non autorisés pour l'application")
    print(f"      → Assurez-vous que tous les scopes sont activés dans l'app")
    print()
    
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic de configuration OAuth2 Oura"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='UUID de l\'utilisateur Supabase'
    )
    
    args = parser.parse_args()
    check_config(args.user_id)


if __name__ == "__main__":
    main()
