"""
Service OAuth2 pour Oura Ring
==============================

Gère le flux OAuth2 complet :
- Génération de l'URL d'autorisation
- Échange du code contre un access_token
- Refresh automatique des tokens expirés
- Stockage dans Supabase

Documentation Oura OAuth2: https://cloud.ouraring.com/docs/authentication
"""

import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class OuraOAuth2Service:
    """Service pour gérer l'authentification OAuth2 avec Oura"""
    
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.client_id = os.getenv("OURA_CLIENT_ID")
        self.client_secret = os.getenv("OURA_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OURA_REDIRECT_URI", "http://localhost:8000/api/oura/oauth/callback")
        
        # Oura OAuth2 URLs
        self.auth_url = "https://cloud.ouraring.com/oauth/authorize"
        self.token_url = "https://api.ouraring.com/oauth/token"
        
        if not self.client_id or not self.client_secret:
            logger.warning("OURA_CLIENT_ID or OURA_CLIENT_SECRET not set. OAuth2 will not work.")
    
    def generate_auth_url(self, state: Optional[str] = None) -> str:
        """
        Génère l'URL d'autorisation Oura
        
        Args:
            state: État optionnel pour la sécurité CSRF (recommandé)
            
        Returns:
            URL complète vers laquelle rediriger l'utilisateur
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "daily personal email",  # Scopes nécessaires
        }
        
        if state:
            params["state"] = state
        
        url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated OAuth2 auth URL with redirect_uri={self.redirect_uri}")
        
        return url
    
    async def exchange_code_for_tokens(self, code: str) -> Optional[Dict]:
        """
        Échange le code d'autorisation contre un access_token et refresh_token
        
        Args:
            code: Code d'autorisation reçu de Oura
            
        Returns:
            Dict contenant access_token, refresh_token, expires_in, token_type
        """
        try:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            logger.info(f"Exchanging authorization code for tokens...")
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            
            logger.info(f"Successfully obtained tokens (expires_in={tokens.get('expires_in')}s)")
            
            return tokens
        
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Rafraîchit l'access_token en utilisant le refresh_token
        
        Args:
            refresh_token: Refresh token Oura
            
        Returns:
            Dict contenant le nouveau access_token, refresh_token, expires_in
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            logger.info("Refreshing access token...")
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            
            logger.info("Successfully refreshed access token")
            
            return tokens
        
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None
    
    async def store_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        external_user_id: Optional[str] = None
    ) -> bool:
        """
        Stocke les tokens OAuth2 dans Supabase
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            access_token: Access token Oura
            refresh_token: Refresh token Oura
            expires_in: Durée de validité en secondes
            external_user_id: Email ou ID Oura (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Calculer la date d'expiration
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            # Récupérer les infos utilisateur depuis Oura si external_user_id non fourni
            if not external_user_id:
                from oura_client import OuraClient
                oura = OuraClient(access_token)
                personal_info = oura.get_personal_info()
                external_user_id = personal_info.get("email") if personal_info else f"oura_user_{user_id[:8]}"
            
            # Préparer les métadonnées OAuth2
            metadata = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
                "token_type": "Bearer",
                "auth_method": "oauth2",
            }
            
            # Vérifier si l'utilisateur existe déjà
            existing = self.supabase.client.from_('external_identities') \
                .select('id') \
                .eq('supabase_user_id', user_id) \
                .eq('provider_system', 'oura') \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                # Mettre à jour
                result = self.supabase.client.from_('external_identities') \
                    .update({
                        'external_user_id': external_user_id,
                        'metadata': metadata,
                        'is_active': True,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }) \
                    .eq('supabase_user_id', user_id) \
                    .eq('provider_system', 'oura') \
                    .execute()
                
                logger.info(f"✅ Updated OAuth2 tokens for user {user_id}")
            else:
                # Créer
                result = self.supabase.client.from_('external_identities') \
                    .insert({
                        'supabase_user_id': user_id,
                        'provider_system': 'oura',
                        'external_user_id': external_user_id,
                        'metadata': metadata,
                        'is_active': True
                    }) \
                    .execute()
                
                logger.info(f"✅ Stored OAuth2 tokens for user {user_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error storing tokens: {e}")
            return False
    
    async def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """
        Récupère un access_token valide (rafraîchit si expiré)
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            
        Returns:
            Access token valide ou None
        """
        try:
            # Récupérer les tokens depuis Supabase
            result = self.supabase.client.from_('external_identities') \
                .select('metadata') \
                .eq('supabase_user_id', user_id) \
                .eq('provider_system', 'oura') \
                .eq('is_active', True) \
                .single() \
                .execute()
            
            if not result.data:
                logger.warning(f"No Oura connection found for user {user_id}")
                return None
            
            metadata = result.data.get('metadata', {})
            access_token = metadata.get('access_token')
            refresh_token = metadata.get('refresh_token')
            expires_at_str = metadata.get('expires_at')
            auth_method = metadata.get('auth_method', 'pat')  # par défaut: Personal Access Token
            
            # Si c'est un PAT (pas OAuth2), retourner directement
            if auth_method != 'oauth2':
                logger.info("Using Personal Access Token (not OAuth2)")
                return access_token
            
            # Vérifier si le token est expiré
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.now(timezone.utc)
                
                # Si le token expire dans moins de 5 minutes, le rafraîchir
                if now >= expires_at - timedelta(minutes=5):
                    logger.info("Access token expired or expiring soon, refreshing...")
                    
                    if not refresh_token:
                        logger.error("No refresh token available")
                        return None
                    
                    # Rafraîchir le token
                    new_tokens = await self.refresh_access_token(refresh_token)
                    
                    if not new_tokens:
                        logger.error("Failed to refresh access token")
                        return None
                    
                    # Stocker les nouveaux tokens
                    await self.store_tokens(
                        user_id=user_id,
                        access_token=new_tokens['access_token'],
                        refresh_token=new_tokens.get('refresh_token', refresh_token),
                        expires_in=new_tokens['expires_in']
                    )
                    
                    return new_tokens['access_token']
            
            # Token encore valide
            return access_token
        
        except Exception as e:
            logger.error(f"Error getting valid access token: {e}")
            return None
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """
        Révoque les tokens OAuth2 (désactive la connexion)
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            
        Returns:
            True si succès, False sinon
        """
        try:
            result = self.supabase.client.from_('external_identities') \
                .update({'is_active': False}) \
                .eq('supabase_user_id', user_id) \
                .eq('provider_system', 'oura') \
                .execute()
            
            logger.info(f"✅ Revoked OAuth2 tokens for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error revoking tokens: {e}")
            return False


# ============================================
# Helper Functions
# ============================================

async def get_oura_oauth2_service(supabase: SupabaseClient) -> OuraOAuth2Service:
    """
    Crée une instance du service OAuth2
    
    Args:
        supabase: Client Supabase
        
    Returns:
        OuraOAuth2Service configuré
    """
    return OuraOAuth2Service(supabase)
