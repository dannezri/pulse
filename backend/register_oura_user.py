"""
Script pour enregistrer un utilisateur Oura dans la table external_identities
Usage: python register_oura_user.py
"""

import os
import sys
from supabase_client import SupabaseClient
from oura_client import get_oura_client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def register_oura_user(
    supabase_user_id: str,
    oura_token: str,
    supabase_url: str,
    supabase_key: str
):
    """
    Enregistre un utilisateur Oura dans external_identities
    
    Args:
        supabase_user_id: UUID Supabase de l'utilisateur
        oura_token: Token d'accès Oura
        supabase_url: URL Supabase
        supabase_key: Clé service_role Supabase
    """
    # Initialiser les clients
    supabase = SupabaseClient(supabase_url, supabase_key)
    oura_client = get_oura_client(oura_token)
    
    # Récupérer les informations personnelles de l'utilisateur Oura
    logger.info("Fetching Oura user personal info...")
    personal_info = oura_client.get_personal_info()
    
    if not personal_info:
        logger.error("Failed to fetch Oura user personal info")
        return False
    
    # Utiliser l'email comme identifiant externe (ou user_id si disponible)
    external_user_id = personal_info.get("email") or personal_info.get("id")
    
    if not external_user_id:
        logger.error("No valid external user ID found in Oura personal info")
        return False
    
    logger.info(f"Oura user identified: {external_user_id}")
    
    # Créer ou mettre à jour l'identité externe
    metadata = {
        "access_token": oura_token,  # ✅ Stocker le token Oura
        "email": personal_info.get("email"),
        "age": personal_info.get("age"),
        "weight": personal_info.get("weight"),
        "height": personal_info.get("height"),
        "biological_sex": personal_info.get("biological_sex"),
        "connected_at": personal_info.get("created_at")
    }
    
    logger.info(f"Creating/updating external identity for user {supabase_user_id}...")
    
    # Vérifier si l'identité existe déjà
    try:
        existing = supabase.client.table("external_identities").select("*").eq(
            "supabase_user_id", supabase_user_id
        ).eq("provider_system", "oura").execute()
        
        if existing.data:
            # Mise à jour
            logger.info("Identity already exists, updating...")
            result = supabase.client.table("external_identities").update({
                "external_user_id": external_user_id,
                "metadata": metadata,
                "is_active": True
            }).eq("supabase_user_id", supabase_user_id).eq("provider_system", "oura").execute()
        else:
            # Création
            result = supabase.client.table("external_identities").insert({
                "supabase_user_id": supabase_user_id,
                "provider_system": "oura",
                "external_user_id": external_user_id,
                "metadata": metadata,
                "is_active": True
            }).execute()
        
        logger.info("✅ Oura user successfully registered/updated in external_identities!")
        logger.info(f"   - Supabase User ID: {supabase_user_id}")
        logger.info(f"   - Provider: oura")
        logger.info(f"   - External ID: {external_user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register Oura user: {e}")
        return False


def main():
    """Fonction principale"""
    # Configuration
    OURA_TOKEN = "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"
    
    from user_config import get_dev_user_uuid
    USER_UUID = get_dev_user_uuid()
    
    # Charger les credentials Supabase depuis l'environnement
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        sys.exit(1)
    
    # Enregistrer l'utilisateur
    success = register_oura_user(
        supabase_user_id=USER_UUID,
        oura_token=OURA_TOKEN,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
