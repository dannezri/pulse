#!/usr/bin/env python3
"""
Script cron BATCH pour calculer les baselines (RECOMMANDÉ pour production)

✅ PRODUCTION PATTERN - SCALABLE
Appelle l'endpoint batch unique qui boucle en interne

Usage:
    python cron_batch_baselines.py

Configuration:
    - CRON_SECRET: Secret partagé pour authentifier les appels cron
    - BACKEND_URL: URL du backend API (défaut: http://localhost:9000)

Avantages:
    - 1 seul HTTP call (vs N calls pour N users)
    - Le backend gère le batching et les erreurs
    - Timeout géré côté serveur
    - Logs centralisés

Recommandation:
    Utiliser ce script pour tout environnement avec >100 users
"""

import os
import sys
import requests
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Déclenche le calcul batch des baselines via l'API"""
    
    # Vérifier les variables d'environnement
    cron_secret = os.getenv("CRON_SECRET")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:9000")
    
    if not cron_secret:
        logger.error("Missing CRON_SECRET environment variable")
        sys.exit(1)
    
    logger.info("=== DÉBUT CALCUL BATCH BASELINES ===")
    
    try:
        response = requests.post(
            f"{backend_url}/api/baselines/recalculate-active",
            headers={"X-Cron-Secret": cron_secret},
            timeout=300  # 5 minutes timeout (le backend gère le batching)
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✓ Calcul batch terminé avec succès")
            logger.info(f"  Total users: {result.get('total_users', 0)}")
            logger.info(f"  Traités: {result.get('processed', 0)}")
            logger.info(f"  Échecs: {result.get('failed', 0)}")
            
            # Afficher les erreurs s'il y en a
            errors = result.get('errors', [])
            if errors:
                logger.warning(f"  {len(errors)} erreurs détectées:")
                for error in errors[:5]:  # Afficher max 5 erreurs
                    logger.warning(f"    User {error.get('user_id')}: {error.get('error')}")
                if len(errors) > 5:
                    logger.warning(f"    ... et {len(errors) - 5} autres erreurs")
            
            # Exit code selon le taux d'échec
            if result.get('failed', 0) > result.get('processed', 1) * 0.5:
                logger.error("Taux d'échec > 50%, exit code 1")
                sys.exit(1)
            else:
                sys.exit(0)
        
        else:
            logger.error(f"✗ Erreur HTTP {response.status_code}: {response.text}")
            sys.exit(1)
    
    except requests.exceptions.Timeout:
        logger.error("✗ Timeout (>5 minutes) - vérifier les logs du backend")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
