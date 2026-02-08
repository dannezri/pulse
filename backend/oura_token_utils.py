"""
Utilitaires pour récupérer les tokens Oura depuis Supabase
Supporte à la fois Personal Access Tokens (PAT) et OAuth2
"""

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


async def get_user_oura_token(supabase: SupabaseClient, user_id: str) -> Optional[str]:
    """
    Récupère un token Oura valide d'un utilisateur depuis external_identities
    
    Supporte:
    - Personal Access Token (PAT) - retourné directement
    - OAuth2 - rafraîchit automatiquement si expiré
    
    Args:
        supabase: Client Supabase
        user_id: UUID Supabase de l'utilisateur
        
    Returns:
        Token Oura valide ou None si non trouvé
    """
    try:
        result = supabase.client.from_('external_identities') \
            .select('metadata') \
            .eq('supabase_user_id', user_id) \
            .eq('provider_system', 'oura') \
            .eq('is_active', True) \
            .single() \
            .execute()
        
        if not result.data:
            logger.warning(f"⚠️  Aucune identité Oura active trouvée pour {user_id}")
            return None
        
        metadata = result.data.get('metadata', {})
        access_token = metadata.get('access_token')
        auth_method = metadata.get('auth_method', 'pat')  # 'pat' ou 'oauth2'
        
        if not access_token:
            logger.warning(f"⚠️  Aucun access_token trouvé dans metadata pour {user_id}")
            return None
        
        # Si c'est un PAT, retourner directement
        if auth_method == 'pat':
            logger.info(f"✅ Token Oura (PAT) récupéré pour l'utilisateur {user_id}")
            return access_token
        
        # Si c'est OAuth2, vérifier l'expiration et rafraîchir si nécessaire
        if auth_method == 'oauth2':
            expires_at_str = metadata.get('expires_at')
            refresh_token = metadata.get('refresh_token')
            
            if not expires_at_str:
                logger.warning(f"⚠️  OAuth2 token sans date d'expiration pour {user_id}")
                return access_token
            
            # Parser la date d'expiration et s'assurer qu'elle a une timezone
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            
            # Si expires_at est naive (pas de timezone), ajouter UTC
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            
            # Si le token expire dans moins de 5 minutes, le rafraîchir
            if now >= expires_at - timedelta(minutes=5):
                logger.info(f"🔄 Token OAuth2 expiré ou expirant bientôt, rafraîchissement...")
                
                if not refresh_token:
                    logger.error(f"❌ Pas de refresh_token disponible pour {user_id}")
                    return None
                
                # Rafraîchir le token
                from oura_oauth2_service import OuraOAuth2Service
                oauth_service = OuraOAuth2Service(supabase)
                
                new_tokens = await oauth_service.refresh_access_token(refresh_token)
                
                if not new_tokens:
                    logger.error(f"❌ Échec du rafraîchissement du token pour {user_id}")
                    return None
                
                # Stocker les nouveaux tokens
                await oauth_service.store_tokens(
                    user_id=user_id,
                    access_token=new_tokens['access_token'],
                    refresh_token=new_tokens.get('refresh_token', refresh_token),
                    expires_in=new_tokens['expires_in']
                )
                
                logger.info(f"✅ Token OAuth2 rafraîchi pour {user_id}")
                return new_tokens['access_token']
            
            logger.info(f"✅ Token Oura (OAuth2) récupéré pour l'utilisateur {user_id}")
            return access_token
        
        # Méthode inconnue
        logger.warning(f"⚠️  Méthode d'authentification inconnue: {auth_method}")
        return access_token
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du token Oura: {e}")
        return None


def update_user_oura_token(supabase: SupabaseClient, user_id: str, oura_token: str) -> bool:
    """
    Met à jour le token Oura d'un utilisateur dans external_identities
    
    Args:
        supabase: Client Supabase
        user_id: UUID Supabase de l'utilisateur
        oura_token: Nouveau token Oura
        
    Returns:
        True si succès, False sinon
    """
    try:
        # Récupérer l'entrée existante
        result = supabase.client.from_('external_identities') \
            .select('metadata') \
            .eq('supabase_user_id', user_id) \
            .eq('provider_system', 'oura') \
            .single() \
            .execute()
        
        if result.data:
            # Mettre à jour le token dans metadata
            metadata = result.data.get('metadata', {})
            metadata['access_token'] = oura_token
            
            update_result = supabase.client.from_('external_identities') \
                .update({'metadata': metadata}) \
                .eq('supabase_user_id', user_id) \
                .eq('provider_system', 'oura') \
                .execute()
            
            logger.info(f"✅ Token Oura mis à jour pour {user_id}")
            return True
        else:
            logger.error(f"❌ Aucune identité Oura trouvée pour {user_id}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du token: {e}")
        return False
