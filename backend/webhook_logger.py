"""
Logger pour les webhooks entrants
Enregistre tous les webhooks reçus dans Supabase pour debugging et monitoring
"""

from typing import Dict, Optional, Any
from datetime import datetime
import logging
import json
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class WebhookLogger:
    """Logger centralisé pour les webhooks"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
    
    def log_webhook(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        client_user_id: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None
    ) -> str:
        """
        Enregistre un webhook reçu
        
        Args:
            endpoint: Endpoint qui a reçu le webhook (ex: /api/webhooks/vital)
            payload: Payload JSON du webhook
            event_type: Type d'événement (ex: historical.data.water.created)
            user_id: Vital user_id (optionnel)
            client_user_id: Supabase UUID (optionnel)
            method: Méthode HTTP (default: POST)
            headers: Headers HTTP reçus (optionnel)
            start_time: Timestamp de début (pour calculer la durée)
        
        Returns:
            ID du log créé
        """
        try:
            log_entry = {
                "endpoint": endpoint,
                "method": method,
                "payload": payload,
                "event_type": event_type,
                "user_id": user_id,
                "client_user_id": client_user_id,
                "headers": headers if headers else None,
                "received_at": datetime.utcnow().isoformat(),
                "status_code": 200,  # Par défaut, sera mis à jour si erreur
                "response_message": "Received",
            }
            
            # Insérer dans Supabase
            result = self.supabase.client.table("webhook_logs").insert(log_entry).execute()
            
            log_id = result.data[0]["id"] if result.data else None
            logger.debug(f"Webhook logged: {log_id}")
            
            return log_id
        
        except Exception as e:
            logger.error(f"Error logging webhook: {e}")
            return None
    
    def update_webhook_log(
        self,
        log_id: str,
        status_code: int,
        response_message: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """
        Met à jour un log de webhook avec le résultat du traitement
        
        Args:
            log_id: ID du log à mettre à jour
            status_code: Code de statut HTTP (200, 400, 500, etc.)
            response_message: Message de réponse
            error: Message d'erreur si échec
            duration_ms: Durée de traitement en millisecondes
        """
        try:
            if not log_id:
                return
            
            update_data = {
                "status_code": status_code,
                "response_message": response_message,
                "error": error,
                "duration_ms": duration_ms,
                "processed_at": datetime.utcnow().isoformat(),
            }
            
            # Supprimer les valeurs None
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            self.supabase.client.table("webhook_logs").update(update_data).eq("id", log_id).execute()
            
            logger.debug(f"Webhook log updated: {log_id} - status {status_code}")
        
        except Exception as e:
            logger.error(f"Error updating webhook log: {e}")
    
    def log_webhook_complete(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        status_code: int,
        response_message: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        client_user_id: Optional[str] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Enregistre un webhook avec toutes les informations d'un seul coup
        Utile pour les webhooks déjà traités
        
        Args:
            endpoint: Endpoint qui a reçu le webhook
            payload: Payload JSON du webhook
            status_code: Code de statut HTTP
            response_message: Message de réponse
            error: Message d'erreur si échec
            duration_ms: Durée de traitement en millisecondes
            event_type: Type d'événement
            user_id: Vital user_id
            client_user_id: Supabase UUID
            method: Méthode HTTP
            headers: Headers HTTP reçus
        """
        try:
            log_entry = {
                "endpoint": endpoint,
                "method": method,
                "payload": payload,
                "event_type": event_type,
                "user_id": user_id,
                "client_user_id": client_user_id,
                "headers": headers if headers else None,
                "received_at": datetime.utcnow().isoformat(),
                "processed_at": datetime.utcnow().isoformat(),
                "status_code": status_code,
                "response_message": response_message,
                "error": error,
                "duration_ms": duration_ms,
            }
            
            # Supprimer les valeurs None
            log_entry = {k: v for k, v in log_entry.items() if v is not None}
            
            self.supabase.client.table("webhook_logs").insert(log_entry).execute()
            
            logger.debug(f"Webhook logged (complete): {endpoint} - status {status_code}")
        
        except Exception as e:
            logger.error(f"Error logging complete webhook: {e}")


def get_user_webhook_logs(supabase_client: SupabaseClient, user_id: str, limit: int = 50) -> list:
    """
    Récupère les logs de webhooks pour un utilisateur
    
    Args:
        supabase_client: Client Supabase
        user_id: UUID utilisateur
        limit: Nombre maximum de logs à récupérer
    
    Returns:
        Liste des logs de webhooks
    """
    try:
        result = supabase_client.client.rpc(
            "get_user_webhook_logs",
            {"p_user_id": user_id, "p_limit": limit}
        ).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.error(f"Error fetching user webhook logs: {e}")
        return []


def get_all_webhook_logs(supabase_client: SupabaseClient, limit: int = 100) -> list:
    """
    Récupère tous les logs de webhooks (admin)
    
    Args:
        supabase_client: Client Supabase
        limit: Nombre maximum de logs à récupérer
    
    Returns:
        Liste des logs de webhooks
    """
    try:
        result = supabase_client.client.rpc(
            "get_all_webhook_logs",
            {"p_limit": limit}
        ).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.error(f"Error fetching all webhook logs: {e}")
        return []
