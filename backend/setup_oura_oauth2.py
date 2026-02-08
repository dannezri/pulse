#!/usr/bin/env python3
"""
Script pour configurer un utilisateur Oura avec OAuth2
======================================================

Ce script permet de stocker directement les credentials OAuth2 pour un utilisateur
(utile pour les tests ou la migration d'utilisateurs existants).

Usage:
    python setup_oura_oauth2.py --user-id <uuid> --access-token <token> --refresh-token <token>
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

from supabase_client import SupabaseClient
from oura_oauth2_service import OuraOAuth2Service

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis")
    sys.exit(1)


async def setup_oauth2_user(
    user_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int = 86400  # 24 heures par défaut
):
    """
    Configure un utilisateur avec des tokens OAuth2
    
    Args:
        user_id: UUID Supabase de l'utilisateur
        access_token: Access token Oura
        refresh_token: Refresh token Oura
        expires_in: Durée de validité en secondes (défaut: 24h)
    """
    print("=" * 70)
    print("🔐 CONFIGURATION OURA OAUTH2")
    print("=" * 70)
    print(f"\nUser ID: {user_id}")
    print(f"Access Token: {access_token[:20]}...")
    print(f"Refresh Token: {refresh_token[:20]}...")
    print(f"Expires in: {expires_in}s ({expires_in/3600:.1f}h)")
    print()
    
    # Initialiser le service OAuth2
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    oauth_service = OuraOAuth2Service(supabase)
    
    # Récupérer les infos utilisateur depuis Oura
    print("📡 Récupération des informations utilisateur depuis Oura...")
    
    from oura_client import OuraClient
    oura = OuraClient(access_token)
    personal_info = oura.get_personal_info()
    
    if not personal_info:
        print("❌ Impossible de récupérer les informations utilisateur")
        print("   Vérifiez que l'access_token est valide")
        return False
    
    external_user_id = personal_info.get("email", f"oura_user_{user_id[:8]}")
    print(f"✅ Utilisateur Oura: {external_user_id}")
    print()
    
    # Stocker les tokens
    print("💾 Stockage des tokens OAuth2 dans Supabase...")
    
    success = await oauth_service.store_tokens(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        external_user_id=external_user_id
    )
    
    if not success:
        print("❌ Échec du stockage des tokens")
        return False
    
    print("✅ Tokens OAuth2 stockés avec succès")
    print()
    
    # Vérifier le stockage
    print("🔍 Vérification du stockage...")
    
    result = supabase.client.from_('external_identities') \
        .select('external_user_id, metadata, is_active') \
        .eq('supabase_user_id', user_id) \
        .eq('provider_system', 'oura') \
        .single() \
        .execute()
    
    if result.data:
        metadata = result.data.get('metadata', {})
        print(f"✅ Utilisateur: {result.data['external_user_id']}")
        print(f"✅ Active: {result.data['is_active']}")
        print(f"✅ Auth method: {metadata.get('auth_method', 'N/A')}")
        print(f"✅ Expires at: {metadata.get('expires_at', 'N/A')}")
        print()
        
        # Tester le rafraîchissement automatique
        print("🧪 Test du rafraîchissement automatique...")
        from oura_token_utils import get_user_oura_token
        
        token = await get_user_oura_token(supabase, user_id)
        
        if token:
            print(f"✅ Token récupéré: {token[:20]}...")
            print()
        else:
            print("❌ Échec de la récupération du token")
            return False
    else:
        print("❌ Impossible de vérifier le stockage")
        return False
    
    print("=" * 70)
    print("🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 70)
    print()
    print("✅ L'utilisateur peut maintenant utiliser Oura avec OAuth2")
    print("✅ Les tokens seront rafraîchis automatiquement")
    print()
    
    return True


async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Configure un utilisateur Oura avec OAuth2"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help="UUID Supabase de l'utilisateur"
    )
    parser.add_argument(
        '--access-token',
        required=True,
        help="Access token Oura OAuth2"
    )
    parser.add_argument(
        '--refresh-token',
        required=True,
        help="Refresh token Oura OAuth2"
    )
    parser.add_argument(
        '--expires-in',
        type=int,
        default=86400,
        help="Durée de validité en secondes (défaut: 86400 = 24h)"
    )
    
    args = parser.parse_args()
    
    success = await setup_oauth2_user(
        user_id=args.user_id,
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        expires_in=args.expires_in
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
