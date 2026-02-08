"""
Worker Celery pour normaliser les données webhook et mettre à jour les profils de santé
"""

from typing import Dict, Optional
import logging
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from job_queue import celery_app
from supabase_client import SupabaseClient
from legacy.data_normalizer import DataNormalizer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser les clients
supabase_client = SupabaseClient(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)

normalizer = DataNormalizer()


@celery_app.task(name="workers.normalization_worker.normalize_webhook_data", bind=True)
def normalize_webhook_data(
    self,
    webhook_event_id: str,
    user_id: str,
    open_wearables_user_id: str
) -> Dict:
    """
    Traite un webhook event : normalise les données et met à jour le profil de santé
    
    Args:
        webhook_event_id: ID de l'événement dans webhook_events
        user_id: UUID Supabase de l'utilisateur
        open_wearables_user_id: ID Open Wearables de l'utilisateur
    
    Returns:
        Dict avec le statut du traitement
    """
    try:
        # Marquer l'événement comme "processing"
        _update_webhook_status(webhook_event_id, "processing")
        
        # Récupérer le payload brut depuis la base
        webhook_event = _get_webhook_event(webhook_event_id)
        if not webhook_event:
            raise ValueError(f"Webhook event {webhook_event_id} not found")
        
        payload = webhook_event["payload"]
        data = payload.get("data", {})
        
        # Sauvegarder les données brutes dans biometrics (avec idempotence)
        _save_raw_biometrics(user_id, data, payload.get("event_id"))
        
        # Récupérer les données du jour pour normalisation
        today_data = supabase_client.get_today_biometrics(user_id)
        
        # Récupérer les données historiques pour calculer les baselines
        historical_data = supabase_client.get_historical_biometrics(user_id, days=7)
        
        # Normaliser les données
        formatted_data = _format_data_for_normalization(today_data, data)
        normalized_data = normalizer.normalize_open_wearables_data(formatted_data)
        
        # Calculer les baselines avec métadonnées (fallback automatique)
        hrv_baseline, hrv_metadata = normalizer.calculate_baseline(historical_data, "hrv", days=7)
        hr_baseline, hr_metadata = normalizer.calculate_baseline(historical_data, "hr", days=7)
        sleep_baseline, sleep_metadata = normalizer.calculate_baseline(historical_data, "sleep", days=7)
        
        baseline_data = {
            "hrv_baseline": hrv_baseline,
            "hr_baseline": hr_baseline,
            "sleep_baseline": sleep_baseline,
            # Métadonnées pour traçabilité
            "hrv_baseline_metadata": hrv_metadata,
            "hr_baseline_metadata": hr_metadata,
            "sleep_baseline_metadata": sleep_metadata
        }
        
        # Mettre à jour les baselines dans le profil si nécessaire
        if baseline_data["hrv_baseline"] or baseline_data["hr_baseline"]:
            supabase_client.update_baselines(
                user_id,
                int(baseline_data["hrv_baseline"]) if baseline_data["hrv_baseline"] else None,
                int(baseline_data["hr_baseline"]) if baseline_data["hr_baseline"] else None
            )
        
        # Récupérer l'objectif utilisateur
        user_goal = supabase_client.get_user_goal(user_id)
        
        # Créer le profil de santé
        health_profile = normalizer.create_health_profile(
            normalized_data,
            baseline_data,
            user_goal
        )
        
        # Sauvegarder le profil de santé (upsert quotidien)
        supabase_client.save_health_profile(user_id, health_profile)
        
        # Marquer l'événement comme "completed"
        _update_webhook_status(webhook_event_id, "completed")
        
        logger.info(f"Webhook {webhook_event_id} normalisé avec succès pour user {user_id}")
        
        return {
            "status": "success",
            "webhook_event_id": webhook_event_id,
            "user_id": user_id,
            "health_profile_updated": True
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation du webhook {webhook_event_id}: {e}", exc_info=True)
        
        # Marquer l'événement comme "failed"
        _update_webhook_status(webhook_event_id, "failed", str(e))
        
        # Relancer l'exception pour que Celery gère le retry
        raise


def _get_webhook_event(webhook_event_id: str) -> Optional[Dict]:
    """Récupère un événement webhook depuis la base"""
    try:
        response = supabase_client.client.table("webhook_events").select("*").eq("id", webhook_event_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching webhook event: {e}")
        return None


def _update_webhook_status(webhook_event_id: str, status: str, error_message: Optional[str] = None):
    """Met à jour le statut d'un événement webhook"""
    try:
        update_data = {
            "status": status,
            "processed_at": datetime.now().isoformat() if status in ["completed", "failed"] else None
        }
        if error_message:
            update_data["error_message"] = error_message
        
        supabase_client.client.table("webhook_events").update(update_data).eq("id", webhook_event_id).execute()
    except Exception as e:
        logger.error(f"Error updating webhook status: {e}")


def _save_raw_biometrics(user_id: str, data: Dict, base_event_id: Optional[str] = None):
    """Sauvegarde les données brutes dans biometrics avec idempotence"""
    import hashlib
    import json
    from datetime import datetime
    
    # Générer un ID de synchronisation si non fourni
    if base_event_id is None:
        base_event_id = f"webhook_{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]}"
    
    # Sauvegarder les données de sommeil
    if "sleep" in data and data["sleep"]:
        sleep_data = data["sleep"]
        if isinstance(sleep_data, dict):
            duration_seconds = sleep_data.get("duration_seconds") or sleep_data.get("duration", 0)
            duration_minutes = int(duration_seconds / 60) if duration_seconds else 0
            
            start_time = sleep_data.get("start_time")
            if start_time:
                try:
                    recorded_at = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except:
                    recorded_at = datetime.now()
            else:
                recorded_at = datetime.now()
            
            source_event_id = f"{base_event_id}_sleep_{hashlib.md5(json.dumps(sleep_data, sort_keys=True).encode()).hexdigest()[:8]}"
            
            supabase_client.insert_biometric(
                user_id=user_id,
                metric_type="sleep_duration",
                value=duration_minutes,
                recorded_at=recorded_at,
                raw_data=sleep_data,
                source="open_wearables",
                source_event_id=source_event_id
            )
    
    # Sauvegarder les données HR
    for hr_key in ["heart_rate", "hr"]:
        if hr_key in data and data[hr_key]:
            hr_data = data[hr_key]
            if isinstance(hr_data, list):
                for idx, hr_entry in enumerate(hr_data):
                    hr_value = hr_entry.get("value") or hr_entry.get("hr") or hr_entry.get("heart_rate")
                    if hr_value:
                        timestamp = hr_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{base_event_id}_hr_{idx}_{hashlib.md5(json.dumps(hr_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        supabase_client.insert_biometric(
                            user_id=user_id,
                            metric_type="hr",
                            value=float(hr_value),
                            recorded_at=recorded_at,
                            raw_data=hr_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )
    
    # Sauvegarder les données HRV
    if "hrv" in data and data["hrv"]:
        hrv_data = data["hrv"]
        if isinstance(hrv_data, list):
            for idx, hrv_entry in enumerate(hrv_data):
                hrv_value = hrv_entry.get("value") or hrv_entry.get("hrv")
                if hrv_value:
                    timestamp = hrv_entry.get("timestamp", datetime.now().isoformat())
                    try:
                        recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    except:
                        recorded_at = datetime.now()
                    
                    source_event_id = f"{base_event_id}_hrv_{idx}_{hashlib.md5(json.dumps(hrv_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                    
                    supabase_client.insert_biometric(
                        user_id=user_id,
                        metric_type="hrv",
                        value=float(hrv_value),
                        recorded_at=recorded_at,
                        raw_data=hrv_entry,
                        source="open_wearables",
                        source_event_id=source_event_id
                    )
    
    # Sauvegarder les données d'activité
    for activity_key in ["activity", "steps"]:
        if activity_key in data and data[activity_key]:
            activity_data = data[activity_key]
            if isinstance(activity_data, dict) and "steps" in activity_data:
                timestamp = activity_data.get("timestamp", datetime.now().isoformat())
                try:
                    recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    recorded_at = datetime.now()
                
                source_event_id = f"{base_event_id}_steps_{hashlib.md5(json.dumps(activity_data, sort_keys=True).encode()).hexdigest()[:8]}"
                
                supabase_client.insert_biometric(
                    user_id=user_id,
                    metric_type="steps",
                    value=float(activity_data["steps"]),
                    recorded_at=recorded_at,
                    raw_data=activity_data,
                    source="open_wearables",
                    source_event_id=source_event_id
                )
            elif isinstance(activity_data, list):
                for idx, step_entry in enumerate(activity_data):
                    steps_value = step_entry.get("value") or step_entry.get("steps")
                    if steps_value:
                        timestamp = step_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{base_event_id}_steps_{idx}_{hashlib.md5(json.dumps(step_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        supabase_client.insert_biometric(
                            user_id=user_id,
                            metric_type="steps",
                            value=float(steps_value),
                            recorded_at=recorded_at,
                            raw_data=step_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )


def _format_data_for_normalization(today_data: Dict, new_data: Dict) -> Dict:
    """Formate les données pour la normalisation"""
    from datetime import datetime
    
    formatted_data = {"date": datetime.now().isoformat()}
    
    # Transformer les données HR
    if "hr" in today_data and today_data["hr"]:
        formatted_data["hr"] = []
        for entry in today_data["hr"]:
            if isinstance(entry, dict):
                formatted_data["hr"].append({
                    "value": entry.get("value"),
                    "timestamp": entry.get("recorded_at", datetime.now().isoformat())
                })
    
    # Ajouter les nouvelles données HR si présentes
    for hr_key in ["heart_rate", "hr"]:
        if hr_key in new_data and new_data[hr_key]:
            hr_data = new_data[hr_key]
            if isinstance(hr_data, list):
                if "hr" not in formatted_data:
                    formatted_data["hr"] = []
                formatted_data["hr"].extend([
                    {
                        "value": entry.get("value") or entry.get("hr") or entry.get("heart_rate"),
                        "timestamp": entry.get("timestamp", datetime.now().isoformat())
                    }
                    for entry in hr_data
                    if entry.get("value") or entry.get("hr") or entry.get("heart_rate")
                ])
    
    # Transformer les données HRV
    if "hrv" in today_data and today_data["hrv"]:
        formatted_data["hrv"] = []
        for entry in today_data["hrv"]:
            if isinstance(entry, dict):
                formatted_data["hrv"].append({
                    "value": entry.get("value"),
                    "timestamp": entry.get("recorded_at", datetime.now().isoformat())
                })
    
    # Ajouter les nouvelles données HRV si présentes
    if "hrv" in new_data and new_data["hrv"]:
        hrv_data = new_data["hrv"]
        if isinstance(hrv_data, list):
            if "hrv" not in formatted_data:
                formatted_data["hrv"] = []
            formatted_data["hrv"].extend([
                {
                    "value": entry.get("value") or entry.get("hrv"),
                    "timestamp": entry.get("timestamp", datetime.now().isoformat())
                }
                for entry in hrv_data
                if entry.get("value") or entry.get("hrv")
            ])
    
    # Transformer les données de sommeil
    sleep_duration_entries = today_data.get("sleep_duration", [])
    sleep_score_entries = today_data.get("sleep_score", [])
    
    if sleep_duration_entries or sleep_score_entries or ("sleep" in new_data and new_data["sleep"]):
        first_sleep = sleep_duration_entries[0] if sleep_duration_entries else (sleep_score_entries[0] if sleep_score_entries else {})
        
        # Utiliser les nouvelles données de sommeil si disponibles
        sleep_data = new_data.get("sleep", {})
        if isinstance(sleep_data, dict):
            duration_seconds = sleep_data.get("duration_seconds") or sleep_data.get("duration", 0)
            if not duration_seconds and isinstance(first_sleep, dict):
                duration_minutes = first_sleep.get("value", 0)
                duration_seconds = duration_minutes * 60
        else:
            duration_minutes = first_sleep.get("value", 0) if isinstance(first_sleep, dict) else 0
            duration_seconds = duration_minutes * 60
        
        score = None
        if sleep_score_entries and isinstance(sleep_score_entries[0], dict):
            score = sleep_score_entries[0].get("value")
        elif isinstance(sleep_data, dict):
            score = sleep_data.get("score") or sleep_data.get("quality_score")
        
        raw_sleep_data = {}
        if isinstance(first_sleep, dict):
            raw_data = first_sleep.get("raw_data")
            if isinstance(raw_data, dict):
                raw_sleep_data = raw_data
        if isinstance(sleep_data, dict):
            raw_sleep_data = {**raw_sleep_data, **sleep_data}
        
        formatted_data["sleep"] = {
            "duration_seconds": duration_seconds,
            "duration": duration_seconds,
            "score": score or raw_sleep_data.get("score") or raw_sleep_data.get("quality_score"),
            "quality_score": score or raw_sleep_data.get("score") or raw_sleep_data.get("quality_score"),
            "deep_sleep_seconds": raw_sleep_data.get("deep_sleep_seconds", 0),
            "rem_sleep_seconds": raw_sleep_data.get("rem_sleep_seconds", 0),
            "light_sleep_seconds": raw_sleep_data.get("light_sleep_seconds", 0),
            "efficiency": raw_sleep_data.get("efficiency", 0),
            "start_time": raw_sleep_data.get("start_time", "") or (first_sleep.get("recorded_at", "") if isinstance(first_sleep, dict) else ""),
            "end_time": raw_sleep_data.get("end_time", "")
        }
    
    # Transformer les données de pas
    if "steps" in today_data and today_data["steps"]:
        formatted_data["steps"] = []
        for entry in today_data["steps"]:
            if isinstance(entry, dict):
                formatted_data["steps"].append({
                    "value": entry.get("value"),
                    "steps": entry.get("value"),
                    "timestamp": entry.get("recorded_at", datetime.now().isoformat())
                })
    
    # Ajouter les nouvelles données de pas si présentes
    for activity_key in ["activity", "steps"]:
        if activity_key in new_data and new_data[activity_key]:
            activity_data = new_data[activity_key]
            if isinstance(activity_data, dict) and "steps" in activity_data:
                if "steps" not in formatted_data:
                    formatted_data["steps"] = []
                formatted_data["steps"].append({
                    "value": activity_data["steps"],
                    "steps": activity_data["steps"],
                    "timestamp": activity_data.get("timestamp", datetime.now().isoformat())
                })
            elif isinstance(activity_data, list):
                if "steps" not in formatted_data:
                    formatted_data["steps"] = []
                formatted_data["steps"].extend([
                    {
                        "value": entry.get("value") or entry.get("steps"),
                        "steps": entry.get("value") or entry.get("steps"),
                        "timestamp": entry.get("timestamp", datetime.now().isoformat())
                    }
                    for entry in activity_data
                    if entry.get("value") or entry.get("steps")
                ])
    
    return formatted_data
