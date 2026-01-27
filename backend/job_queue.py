"""
Système de queue de jobs pour le traitement asynchrone des webhooks
Utilise Celery avec Redis comme broker
"""

import os
from typing import Dict, Optional
from celery import Celery
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USERNAME = os.getenv("REDIS_USERNAME")

# Construire l'URL Redis
redis_auth = ""
if REDIS_USERNAME and REDIS_PASSWORD:
    redis_auth = f"{REDIS_USERNAME}:{REDIS_PASSWORD}@"
elif REDIS_PASSWORD:
    redis_auth = f":{REDIS_PASSWORD}@"
elif REDIS_USERNAME:
    redis_auth = f"{REDIS_USERNAME}@"

REDIS_URL = os.getenv("REDIS_URL", f"redis://{redis_auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Créer l'application Celery
celery_app = Celery(
    "pulse_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.normalization_worker"]
)

# Configuration Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="normalization",
    task_default_exchange="normalization",
    task_default_routing_key="normalization",
    result_expires=3600,  # 1 heure
    task_acks_late=True,  # Ack après traitement
    task_reject_on_worker_lost=True,  # Rejeter si worker crash
    task_time_limit=300,  # 5 minutes max par tâche
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Un job à la fois par worker
    worker_max_tasks_per_child=50,  # Redémarrer worker après 50 tâches
)

logger.info(f"Celery configuré avec Redis: {REDIS_URL.replace(redis_auth, '***@') if redis_auth else REDIS_URL}")


def push_normalization_job(webhook_event_id: str, user_id: str, open_wearables_user_id: str) -> str:
    """
    Pousse un job de normalisation dans la queue
    
    Args:
        webhook_event_id: ID de l'événement webhook dans la table webhook_events
        user_id: UUID Supabase de l'utilisateur
        open_wearables_user_id: ID Open Wearables de l'utilisateur
    
    Returns:
        ID de la tâche Celery
    """
    from workers.normalization_worker import normalize_webhook_data
    
    task = normalize_webhook_data.delay(webhook_event_id, user_id, open_wearables_user_id)
    logger.info(f"Job de normalisation poussé: {task.id} pour webhook_event {webhook_event_id}")
    return task.id
