#!/usr/bin/env python3
"""
Script de réconciliation pour syncs FatSecret
Réessaie les syncs en erreur ou pending
À lancer en cron quotidien : 0 3 * * * (ex: 3h du matin)
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from supabase import create_client
from services.food_log_service import FoodLogService
from fatsecret_client_v2 import FatSecretClient

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal"""
    logger.info("="*70)
    logger.info("Food Logs Reconciliation Starting")
    logger.info("="*70)
    
    # Vérifier variables d'environnement
    required_vars = [
        "SUPABASE_URL",
        "FATSECRET_CONSUMER_KEY",
        "FATSECRET_CONSUMER_SECRET"
    ]
    
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_key:
        required_vars.append("SUPABASE_SERVICE_KEY")
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing or not supabase_key:
        logger.error(f"Missing environment variables: {missing}")
        sys.exit(1)
    
    # Initialiser les services
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        supabase_key
    )
    
    fatsecret = FatSecretClient(
        client_id=os.getenv("FATSECRET_CONSUMER_KEY"),
        client_secret=os.getenv("FATSECRET_CONSUMER_SECRET")
    )
    
    food_log_service = FoodLogService(
        supabase=supabase,
        fatsecret=fatsecret
    )
    
    # Réconcilier (7 jours par défaut)
    days_back = int(os.getenv("RECONCILE_DAYS_BACK", "7"))
    user_id = os.getenv("RECONCILE_USER_ID", None)  # Optionnel : spécifier un user
    
    if user_id:
        logger.info(f"Reconciling for specific user: {user_id}")
    else:
        logger.info("Reconciling for all users")
    
    logger.info(f"Looking back {days_back} days")
    
    try:
        result = food_log_service.reconcile_pending_syncs(
            user_id=user_id,
            days_back=days_back
        )
        
        logger.info("="*70)
        logger.info("Reconciliation Complete!")
        logger.info(f"  Reconciled: {result['reconciled']}")
        logger.info(f"  Failed: {result['failed']}")
        logger.info(f"  Users affected: {len(result['users'])}")
        logger.info("="*70)
        
        # Exit code
        if result['failed'] > 0:
            logger.warning("Some syncs failed, check logs")
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Reconciliation error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
