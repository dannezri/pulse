"""
Webhook Handler pour recevoir les données Open Wearables en temps réel
À déployer comme endpoint (ex: FastAPI, Flask, ou serverless function)
"""

from typing import Dict, Optional
import logging
import hashlib
import json
from datetime import datetime
from open_wearables_integration import OpenWearablesIntegration
from data_normalizer import DataNormalizer
from supabase_client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenWearablesWebhookHandler:
    """
    Gère les webhooks Open Wearables pour recevoir les données en temps réel
    """
    
    def __init__(
        self,
        open_wearables_client: OpenWearablesIntegration,
        normalizer: DataNormalizer,
        supabase_client: SupabaseClient
    ):
        self.open_wearables = open_wearables_client
        self.normalizer = normalizer
        self.supabase = supabase_client
    
    def handle_webhook(self, payload: Dict, signature: Optional[str] = None) -> Dict:
        """
        Traite un webhook Open Wearables avec support de l'idempotence
        Retourne un statut de succès/erreur
        
        Format attendu d'Open Wearables:
        {
            "user_id": "uuid",
            "event_id": "uuid",  # ID unique de l'événement (optionnel, pour idempotence)
            "data": {
                "hr": [...],  # Heart rate data points
                "hrv": [...], # HRV data points
                "sleep": {...}, # Sleep data
                "steps": [...]  # Steps data
            },
            "timestamp": "2024-01-15T10:00:00Z"
        }
        """
        # Vérifier la signature si fournie
        if signature and not self.open_wearables.verify_webhook_signature(str(payload), signature):
            logger.error("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}
        
        try:
            # Extraire les informations du webhook Open Wearables
            user_id = payload.get("user_id")
            data = payload.get("data", {})
            webhook_event_id = payload.get("event_id")  # ID unique du webhook (si fourni)
            
            if not user_id:
                return {"status": "error", "message": "Missing user_id"}
            
            # Récupérer le user_id Supabase depuis open_wearables_user_id
            supabase_user_id = self.supabase.get_user_by_open_wearables_id(user_id)
            if not supabase_user_id:
                logger.warning(f"User not found for Open Wearables ID: {user_id}")
                return {"status": "error", "message": "User not found"}
            
            # Traiter les données selon ce qui est disponible
            # Passer webhook_event_id pour l'idempotence
            if "sleep" in data:
                self._process_sleep_data(
                    data["sleep"], 
                    supabase_user_id, 
                    payload.get("timestamp"),
                    webhook_event_id
                )
            if "hr" in data:
                self._process_heartrate_data(
                    data["hr"], 
                    supabase_user_id, 
                    payload.get("timestamp"),
                    webhook_event_id
                )
            if "hrv" in data:
                self._process_hrv_data(
                    data["hrv"], 
                    supabase_user_id, 
                    payload.get("timestamp"),
                    webhook_event_id
                )
            if "steps" in data:
                self._process_activity_data(
                    data["steps"], 
                    supabase_user_id, 
                    payload.get("timestamp"),
                    webhook_event_id
                )
            
            # Après traitement, mettre à jour le profil de santé
            self._update_health_profile(supabase_user_id)
            
            return {"status": "success", "message": "Webhook processed"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    def _generate_source_event_id(
        self, 
        base_event_id: Optional[str], 
        metric_type: str, 
        entry_data: Dict
    ) -> str:
        """
        Génère un source_event_id unique pour chaque point de données.
        Utilise base_event_id si fourni, sinon génère un hash du payload.
        """
        if base_event_id:
            # Si on a un event_id de base, on le combine avec le type de métrique
            # pour créer un ID unique par point de données
            entry_hash = hashlib.md5(json.dumps(entry_data, sort_keys=True).encode()).hexdigest()[:8]
            return f"{base_event_id}_{metric_type}_{entry_hash}"
        else:
            # Fallback: hash du payload complet
            payload_str = json.dumps(entry_data, sort_keys=True)
            return hashlib.md5(payload_str.encode()).hexdigest()
    
    def _process_sleep_data(
        self, 
        sleep_data: Dict, 
        user_id: str, 
        timestamp: Optional[str] = None,
        base_event_id: Optional[str] = None
    ):
        """Traite les données de sommeil depuis Open Wearables avec idempotence"""
        # Format Open Wearables peut varier, on s'adapte
        if isinstance(sleep_data, dict):
            # Si c'est un objet avec durée en secondes
            duration_seconds = sleep_data.get("duration_seconds") or sleep_data.get("duration", 0)
            duration_minutes = int(duration_seconds / 60) if duration_seconds else 0
            
            # Timestamp
            recorded_at = datetime.now()
            if timestamp:
                try:
                    recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    pass
            elif "start_time" in sleep_data:
                try:
                    recorded_at = datetime.fromisoformat(sleep_data["start_time"].replace("Z", "+00:00"))
                except:
                    pass
            
            # Générer source_event_id pour l'idempotence
            source_event_id = self._generate_source_event_id(
                base_event_id, 
                "sleep_duration", 
                sleep_data
            )
            
            # Sauvegarder dans Supabase (idempotent)
            self.supabase.insert_biometric(
                user_id=user_id,
                metric_type="sleep_duration",
                value=duration_minutes,
                recorded_at=recorded_at,
                raw_data=sleep_data,
                source="open_wearables",
                source_event_id=source_event_id
            )
            
            # Sauvegarder le score de qualité si disponible
            score = sleep_data.get("score") or sleep_data.get("quality_score")
            if score:
                score_event_id = self._generate_source_event_id(
                    base_event_id,
                    "sleep_score",
                    {**sleep_data, "score": score}
                )
                self.supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="sleep_score",
                    value=float(score),
                    recorded_at=recorded_at,
                    raw_data=sleep_data,
                    source="open_wearables",
                    source_event_id=score_event_id
                )
        elif isinstance(sleep_data, list):
            # Si c'est une liste de points de données
            for entry in sleep_data:
                self._process_sleep_data(entry, user_id, timestamp, base_event_id)
    
    def _process_heartrate_data(
        self, 
        hr_data: any, 
        user_id: str, 
        timestamp: Optional[str] = None,
        base_event_id: Optional[str] = None
    ):
        """Traite les données de fréquence cardiaque depuis Open Wearables avec idempotence"""
        if isinstance(hr_data, list):
            # Liste de points de données
            for idx, entry in enumerate(hr_data):
                hr_value = entry.get("value") or entry.get("hr") or entry.get("heart_rate")
                if hr_value:
                    recorded_at = datetime.now()
                    if entry.get("timestamp"):
                        try:
                            recorded_at = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                        except:
                            pass
                    elif timestamp:
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            pass
                    
                    # Générer source_event_id unique pour chaque point
                    # Utiliser event_id de l'entrée si disponible, sinon base_event_id
                    entry_event_id = entry.get("event_id") or base_event_id
                    source_event_id = self._generate_source_event_id(
                        entry_event_id,
                        "hr",
                        {**entry, "index": idx}
                    )
                    
                    self.supabase.insert_biometric(
                        user_id=user_id,
                        metric_type="hr",
                        value=float(hr_value),
                        recorded_at=recorded_at,
                        raw_data=entry,
                        source="open_wearables",
                        source_event_id=source_event_id
                    )
        elif isinstance(hr_data, dict):
            # Objet unique
            hr_value = hr_data.get("value") or hr_data.get("hr") or hr_data.get("heart_rate")
            if hr_value:
                recorded_at = datetime.now()
                if hr_data.get("timestamp"):
                    try:
                        recorded_at = datetime.fromisoformat(hr_data["timestamp"].replace("Z", "+00:00"))
                    except:
                        pass
                elif timestamp:
                    try:
                        recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    except:
                        pass
                
                source_event_id = self._generate_source_event_id(
                    hr_data.get("event_id") or base_event_id,
                    "hr",
                    hr_data
                )
                
                self.supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="hr",
                    value=float(hr_value),
                    recorded_at=recorded_at,
                    raw_data=hr_data,
                    source="open_wearables",
                    source_event_id=source_event_id
                )
    
    def _process_hrv_data(
        self, 
        hrv_data: any, 
        user_id: str, 
        timestamp: Optional[str] = None,
        base_event_id: Optional[str] = None
    ):
        """Traite les données HRV depuis Open Wearables avec idempotence"""
        if isinstance(hrv_data, list):
            # Liste de points de données
            for idx, entry in enumerate(hrv_data):
                hrv_value = entry.get("value") or entry.get("hrv")
                if hrv_value:
                    recorded_at = datetime.now()
                    if entry.get("timestamp"):
                        try:
                            recorded_at = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                        except:
                            pass
                    elif timestamp:
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            pass
                    
                    entry_event_id = entry.get("event_id") or base_event_id
                    source_event_id = self._generate_source_event_id(
                        entry_event_id,
                        "hrv",
                        {**entry, "index": idx}
                    )
                    
                    self.supabase.insert_biometric(
                        user_id=user_id,
                        metric_type="hrv",
                        value=float(hrv_value),
                        recorded_at=recorded_at,
                        raw_data=entry,
                        source="open_wearables",
                        source_event_id=source_event_id
                    )
        elif isinstance(hrv_data, dict):
            # Objet unique
            hrv_value = hrv_data.get("value") or hrv_data.get("hrv")
            if hrv_value:
                recorded_at = datetime.now()
                if hrv_data.get("timestamp"):
                    try:
                        recorded_at = datetime.fromisoformat(hrv_data["timestamp"].replace("Z", "+00:00"))
                    except:
                        pass
                elif timestamp:
                    try:
                        recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    except:
                        pass
                
                source_event_id = self._generate_source_event_id(
                    hrv_data.get("event_id") or base_event_id,
                    "hrv",
                    hrv_data
                )
                
                self.supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="hrv",
                    value=float(hrv_value),
                    recorded_at=recorded_at,
                    raw_data=hrv_data,
                    source="open_wearables",
                    source_event_id=source_event_id
                )
    
    def _process_activity_data(
        self, 
        steps_data: any, 
        user_id: str, 
        timestamp: Optional[str] = None,
        base_event_id: Optional[str] = None
    ):
        """Traite les données d'activité depuis Open Wearables avec idempotence"""
        if isinstance(steps_data, list):
            # Liste de points de données
            for idx, entry in enumerate(steps_data):
                steps_value = entry.get("value") or entry.get("steps")
                if steps_value:
                    recorded_at = datetime.now()
                    if entry.get("timestamp"):
                        try:
                            recorded_at = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                        except:
                            pass
                    elif timestamp:
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            pass
                    
                    entry_event_id = entry.get("event_id") or base_event_id
                    source_event_id = self._generate_source_event_id(
                        entry_event_id,
                        "steps",
                        {**entry, "index": idx}
                    )
                    
                    self.supabase.insert_biometric(
                        user_id=user_id,
                        metric_type="steps",
                        value=float(steps_value),
                        recorded_at=recorded_at,
                        raw_data=entry,
                        source="open_wearables",
                        source_event_id=source_event_id
                    )
        elif isinstance(steps_data, (int, float)):
            # Valeur unique
            recorded_at = datetime.now()
            if timestamp:
                try:
                    recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    pass
            
            entry_data = {"steps": steps_data, "timestamp": timestamp}
            source_event_id = self._generate_source_event_id(
                base_event_id,
                "steps",
                entry_data
            )
            
            self.supabase.insert_biometric(
                user_id=user_id,
                metric_type="steps",
                value=float(steps_data),
                recorded_at=recorded_at,
                raw_data=entry_data,
                source="open_wearables",
                source_event_id=source_event_id
            )
    
    def _update_health_profile(self, user_id: str):
        """
        Met à jour le profil de santé normalisé après réception de nouvelles données
        """
        # Récupérer les données du jour
        today_data = self.supabase.get_today_biometrics(user_id)
        
        # Récupérer les données historiques pour calculer la baseline
        historical_data = self.supabase.get_historical_biometrics(user_id, days=7)
        
        # Transformer les données de la base vers le format attendu par le normaliseur
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
        
        # Transformer les données HRV
        if "hrv" in today_data and today_data["hrv"]:
            formatted_data["hrv"] = []
            for entry in today_data["hrv"]:
                if isinstance(entry, dict):
                    formatted_data["hrv"].append({
                        "value": entry.get("value"),
                        "timestamp": entry.get("recorded_at", datetime.now().isoformat())
                    })
        
        # Transformer les données de sommeil
        sleep_duration_entries = today_data.get("sleep_duration", [])
        sleep_score_entries = today_data.get("sleep_score", [])
        
        if sleep_duration_entries or sleep_score_entries:
            # Prendre la première entrée de sommeil pour les métadonnées
            first_sleep = sleep_duration_entries[0] if sleep_duration_entries else (sleep_score_entries[0] if sleep_score_entries else {})
            
            # Convertir les minutes en secondes pour duration_seconds
            duration_minutes = first_sleep.get("value", 0) if isinstance(first_sleep, dict) else 0
            duration_seconds = duration_minutes * 60
            
            # Récupérer le score
            score = None
            if sleep_score_entries and isinstance(sleep_score_entries[0], dict):
                score = sleep_score_entries[0].get("value")
            
            # Récupérer les métadonnées depuis raw_data si disponible
            raw_sleep_data = {}
            if isinstance(first_sleep, dict):
                raw_data = first_sleep.get("raw_data")
                if isinstance(raw_data, dict):
                    raw_sleep_data = raw_data
                elif raw_data is not None:
                    # raw_data n'est pas un dict, on l'ignore
                    raw_sleep_data = {}
            
            formatted_data["sleep"] = {
                "duration_seconds": duration_seconds,
                "duration": duration_seconds,
                "score": score or (raw_sleep_data.get("score") if isinstance(raw_sleep_data, dict) else None) or (raw_sleep_data.get("quality_score") if isinstance(raw_sleep_data, dict) else None),
                "quality_score": score or (raw_sleep_data.get("score") if isinstance(raw_sleep_data, dict) else None) or (raw_sleep_data.get("quality_score") if isinstance(raw_sleep_data, dict) else None),
                "deep_sleep_seconds": raw_sleep_data.get("deep_sleep_seconds", 0) if isinstance(raw_sleep_data, dict) else 0,
                "rem_sleep_seconds": raw_sleep_data.get("rem_sleep_seconds", 0) if isinstance(raw_sleep_data, dict) else 0,
                "light_sleep_seconds": raw_sleep_data.get("light_sleep_seconds", 0) if isinstance(raw_sleep_data, dict) else 0,
                "efficiency": raw_sleep_data.get("efficiency", 0) if isinstance(raw_sleep_data, dict) else 0,
                "start_time": (raw_sleep_data.get("start_time", "") if isinstance(raw_sleep_data, dict) else "") or (first_sleep.get("recorded_at", "") if isinstance(first_sleep, dict) else ""),
                "end_time": raw_sleep_data.get("end_time", "") if isinstance(raw_sleep_data, dict) else ""
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
        
        # Normaliser les données
        normalized_today = self.normalizer.normalize_open_wearables_data(formatted_data)
        
        # Calculer les baselines avec métadonnées (fallback automatique)
        hrv_baseline, hrv_metadata = self.normalizer.calculate_baseline(historical_data, "hrv", days=7)
        hr_baseline, hr_metadata = self.normalizer.calculate_baseline(historical_data, "hr", days=7)
        sleep_baseline, sleep_metadata = self.normalizer.calculate_baseline(historical_data, "sleep", days=7)
        
        baseline_data = {
            "hrv_baseline": hrv_baseline,
            "hr_baseline": hr_baseline,
            "sleep_baseline": sleep_baseline,
            # Métadonnées pour traçabilité
            "hrv_baseline_metadata": hrv_metadata,
            "hr_baseline_metadata": hr_metadata,
            "sleep_baseline_metadata": sleep_metadata
        }
        
        # Récupérer l'objectif utilisateur
        user_goal = self.supabase.get_user_goal(user_id)
        
        # Créer le profil de santé
        health_profile = self.normalizer.create_health_profile(
            normalized_today,
            baseline_data,
            user_goal
        )
        
        # Sauvegarder dans Supabase
        self.supabase.save_health_profile(user_id, health_profile)
