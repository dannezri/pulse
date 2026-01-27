"""
Script pour démarrer le worker Celery
Usage: python start_worker.py
"""

import os
from dotenv import load_dotenv
from job_queue import celery_app

load_dotenv()

if __name__ == "__main__":
    # Démarrer le worker Celery
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # 2 workers en parallèle
        "--queue=normalization",  # Queue spécifique
        "--hostname=worker@%h"  # Nom du worker
    ])
