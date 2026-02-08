#!/usr/bin/env python3
"""
Script cron MVP pour calculer les baselines (ne scale pas)

⚠️ MVP PATTERN - NE SCALE PAS
À 1000 users = 1000 HTTP calls

Usage:
    python cron_calculate_baselines.py

Configuration:
    - SUPABASE_URL: URL du projet Supabase
    - SUPABASE_SERVICE_KEY: Clé de service Supabase
    - CRON_SECRET: Secret partagé pour authentifier les appels cron
    - BACKEND_URL: URL du backend API (défaut: http://localhost:9000)

Recommandation:
    Pour production (>100 users), utiliser cron_batch_baselines.py à la place
"""

import os
import sys
import requests
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from supabase_client import SupabaseClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Calcule les baselines pour tous les utilisateurs actifs"""
    
    # Vérifier les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    cron_secret = os.getenv("CRON_SECRET")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:9000")
    
    if not all([supabase_url, supabase_key, cron_secret]):
        logger.error("Missing required environment variables")
        logger.error("Required: SUPABASE_URL, SUPABASE_SERVICE_KEY, CRON_SECRET")
        sys.exit(1)
    
    # Initialiser le client Supabase
    supabase = SupabaseClient(supabase_url, supabase_key)
    
    logger.info("=== DÉBUT CALCUL BASELINES (MVP) ===")
    
    # Récupérer tous les users actifs
    try:
        response = supabase.client.table('profiles').select('id').execute()
        users = response.data if response.data else []
        logger.info(f"Trouvé {len(users)} utilisateurs")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        sys.exit(1)
    
    # ⚠️ Boucle qui ne scale pas (1 HTTP call par user)
    success_count = 0
    failed_count = 0
    
    for user in users:
        user_id = user['id']
        try:
            logger.info(f"Calcul baselines pour user {user_id}")
            
            response = requests.post(
                f"{backend_url}/api/baselines/calculate/{user_id}",
                headers={"X-Cron-Secret": cron_secret},
                timeout=60  # 60 secondes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ User {user_id}: {result.get('status')}")
                success_count += 1
            else:
                logger.error(f"✗ User {user_id}: HTTP {response.status_code} - {response.text}")
                failed_count += 1
        
        except requests.exceptions.Timeout:
            logger.error(f"✗ User {user_id}: Timeout")
            failed_count += 1
        except Exception as e:
            logger.error(f"✗ User {user_id}: {e}")
            failed_count += 1
    
    logger.info("=== FIN CALCUL BASELINES ===")
    logger.info(f"Succès: {success_count}/{len(users)}")
    logger.info(f"Échecs: {failed_count}/{len(users)}")
    
    # Exit code
    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
