#!/usr/bin/env python3
"""
Cron Job - Synchronisation Quotidienne Oura
============================================
À exécuter tous les jours à 08:00 UTC (09:00 Paris) via cron.

Récupère les données Oura de tous les utilisateurs actifs et met à jour
health_profiles.current_metrics pour alimenter le modèle Pulse Energy Decay.

Usage:
    python3 cron_oura_daily_sync.py

Crontab:
    0 8 * * * cd /path/to/backend && python3 cron_oura_daily_sync.py >> /var/log/oura_sync.log 2>&1
"""

import asyncio
import os
import sys
import logging
from datetime import date, datetime
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# Ajouter le backend au path
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import SupabaseClient
from oura_sync_service import sync_all_oura_users

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Point d'entrée principal du cron"""
    
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("CRON: Oura Daily Sync - START")
    logger.info("=" * 60)
    
    try:
        # Initialiser Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")
            sys.exit(1)
        
        supabase = SupabaseClient(supabase_url, supabase_key)
        
        # Synchroniser tous les utilisateurs pour aujourd'hui
        target_date = date.today()
        logger.info(f"Target date: {target_date}")
        
        result = await sync_all_oura_users(supabase, target_date)
        
        # Afficher les résultats
        logger.info("-" * 60)
        logger.info("SYNC RESULTS:")
        logger.info(f"  Total users: {result['total_users']}")
        logger.info(f"  Success: {result['success_count']}")
        logger.info(f"  Errors: {result['error_count']}")
        
        if result.get('errors'):
            logger.warning("Errors details:")
            for error in result['errors']:
                logger.warning(f"  - User {error['user_id']}: {error['error']}")
        
        # Durée d'exécution
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)
        logger.info("CRON: Oura Daily Sync - COMPLETED")
        logger.info("=" * 60)
        
        # Code de sortie
        if result['error_count'] > 0:
            sys.exit(1)  # Échec partiel
        else:
            sys.exit(0)  # Succès
    
    except Exception as e:
        logger.error(f"CRON FAILED: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
