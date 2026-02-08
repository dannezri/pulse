"""
Webhook Receiver : Endpoint rapide qui valide, enregistre brut et pousse un job
Découplé de la normalisation pour répondre rapidement
"""

from typing import Dict, Optional
import logging
from datetime import datetime
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import SupabaseClient
from legacy.open_wearables_integration import OpenWearablesIntegration
from job_queue import push_normalization_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebhookReceiver:
    """
    Reçoit les webhooks, valide la signature, enregistre brut et pousse un job
    Répond rapidement (200) sans attendre la normalisation
    """
    
    def __init__(
        self,
        open_wearables_client: OpenWearablesIntegration,
        supabase_client: SupabaseClient
    ):
        self.open_wearables = open_wearables_client
        self.supabase = supabase_client
    
    def receive_webhook(self, payload: Dict, signature: Optional[str] = None) -> Dict:
        """
        Reçoit un webhook, valide, enregistre brut et pousse un job
        
        Format attendu:
        {
            "user_id": "open_wearables_uuid",
            "event_id": "webhook-event-uuid",  # Optionnel
            "data": {
                "hr": [...],
                "hrv": [...],
                "sleep": {...},
                "steps": [...]
            },
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        Returns:
            Dict avec status et webhook_event_id
        """
        # 1. Valider la signature si fournie
        if signature and not self.open_wearables.verify_webhook_signature(str(payload), signature):
            logger.error("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}
        
        try:
            # 2. Extraire les informations
            open_wearables_user_id = payload.get("user_id")
            if not open_wearables_user_id:
                return {"status": "error", "message": "Missing user_id"}
            
            # 3. Récupérer le user_id Supabase
            supabase_user_id = self.supabase.get_user_by_open_wearables_id(open_wearables_user_id)
            if not supabase_user_id:
                logger.warning(f"User not found for Open Wearables ID: {open_wearables_user_id}")
                return {"status": "error", "message": "User not found"}
            
            # 4. Enregistrer le webhook brut dans webhook_events
            webhook_event_id = self._save_webhook_event(
                supabase_user_id=supabase_user_id,
                open_wearables_user_id=open_wearables_user_id,
                payload=payload,
                signature=signature
            )
            
            # 5. Pousser un job de normalisation dans la queue
            try:
                task_id = push_normalization_job(
                    webhook_event_id=webhook_event_id,
                    user_id=supabase_user_id,
                    open_wearables_user_id=open_wearables_user_id
                )
                logger.info(f"Job poussé: {task_id} pour webhook_event {webhook_event_id}")
            except Exception as e:
                logger.error(f"Erreur lors du push du job: {e}")
                # Marquer l'événement comme failed
                self._update_webhook_status(webhook_event_id, "failed", f"Failed to push job: {str(e)}")
                return {"status": "error", "message": f"Failed to queue job: {str(e)}"}
            
            # 6. Répondre rapidement (200 OK)
            return {
                "status": "accepted",
                "message": "Webhook received and queued for processing",
                "webhook_event_id": webhook_event_id,
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error receiving webhook: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def _save_webhook_event(
        self,
        supabase_user_id: str,
        open_wearables_user_id: str,
        payload: Dict,
        signature: Optional[str] = None
    ) -> str:
        """Enregistre le webhook brut dans webhook_events"""
        try:
            response = self.supabase.client.table("webhook_events").insert({
                "user_id": supabase_user_id,
                "open_wearables_user_id": open_wearables_user_id,
                "payload": payload,
                "signature": signature,
                "status": "pending"
            }).execute()
            
            if response.data:
                webhook_event_id = response.data[0]["id"]
                logger.info(f"Webhook event enregistré: {webhook_event_id}")
                return webhook_event_id
            else:
                raise ValueError("No data returned from webhook_events insert")
                
        except Exception as e:
            logger.error(f"Error saving webhook event: {e}")
            raise
    
    def _update_webhook_status(self, webhook_event_id: str, status: str, error_message: Optional[str] = None):
        """Met à jour le statut d'un événement webhook"""
        try:
            update_data = {
                "status": status,
                "processed_at": datetime.now().isoformat() if status in ["completed", "failed"] else None
            }
            if error_message:
                update_data["error_message"] = error_message
            
            self.supabase.client.table("webhook_events").update(update_data).eq("id", webhook_event_id).execute()
        except Exception as e:
            logger.error(f"Error updating webhook status: {e}")
