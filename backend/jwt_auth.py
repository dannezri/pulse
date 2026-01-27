"""
Authentification JWT Supabase pour les endpoints protégés
"""

from fastapi import HTTPException, Header
from typing import Optional
import jwt
import os
import logging
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_jwt_token(
    authorization: Optional[str] = Header(None),
    supabase_url: Optional[str] = None,
    supabase_anon_key: Optional[str] = None
) -> str:
    """
    Vérifie un token JWT Supabase et retourne le user_id
    
    TEMPORAIRE: Accepte aussi un UUID simple pour compatibilité avec le MVP actuel
    TODO: Migrer vers une vraie authentification JWT
    
    Args:
        authorization: Header Authorization (format: "Bearer <token>")
        supabase_url: URL Supabase (depuis env si non fourni)
        supabase_anon_key: Clé anon Supabase (depuis env si non fourni)
    
    Returns:
        user_id (UUID) extrait du token
    
    Raises:
        HTTPException si token invalide ou manquant
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extraire le token du header "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected: Bearer <token>")
    
    token = parts[1]
    
    # TEMPORAIRE: Vérifier si c'est un UUID simple (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    # Pour le MVP, on accepte directement un UUID comme "token"
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if uuid_pattern.match(token):
        logger.info(f"Using simple UUID auth (temporary): {token[:8]}...")
        return token
    
    try:
        # Option 1: Vérifier via Supabase client (recommandé)
        supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        supabase_anon_key = supabase_anon_key or os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_anon_key:
            # Créer un client avec le token comme header
            # Note: Supabase Python client ne supporte pas directement get_user(token)
            # On utilise jwt.decode pour extraire le user_id (vérification basique)
            # Pour une vérification complète, utiliser Supabase REST API ou vérifier manuellement
            
            try:
                # Décoder le JWT sans vérification (juste pour extraire user_id)
                # En production, vérifier la signature avec la clé secrète JWT
                decoded = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded.get("sub")
                
                if not user_id:
                    raise HTTPException(status_code=401, detail="No user_id in token")
                
                return user_id
            except jwt.DecodeError:
                raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Option 2: Vérifier manuellement (fallback si pas de Supabase client)
        # Note: Nécessite la clé secrète JWT (non recommandé en production)
        # Pour l'instant, on utilise l'option 1 uniquement
        
        raise HTTPException(status_code=401, detail="Supabase configuration missing")
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Error verifying JWT: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


# Alias pour compatibilité
verify_jwt_or_uuid_token = verify_jwt_token
