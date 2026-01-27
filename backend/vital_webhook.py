"""
Gestionnaire de webhook Vital API
Valide, mappe l'identité et insère les données dans biometrics avec idempotence
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging
import hmac
import hashlib
import os
from supabase_client import SupabaseClient, parse_iso_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VitalHRDataPoint(BaseModel):
    """Point de données HR depuis Vital"""
    value: float = Field(..., description="Valeur HR en bpm")
    timestamp: str = Field(..., description="Timestamp ISO 8601")


class VitalHRVDataPoint(BaseModel):
    """Point de données HRV depuis Vital"""
    value: float = Field(..., description="Valeur HRV en ms")
    timestamp: str = Field(..., description="Timestamp ISO 8601")


class VitalSleepData(BaseModel):
    """Données de sommeil depuis Vital"""
    duration_seconds: int = Field(..., description="Durée du sommeil en secondes")
    start_time: str = Field(..., description="Heure de début ISO 8601")
    end_time: Optional[str] = Field(None, description="Heure de fin ISO 8601")


class VitalWebhookPayload(BaseModel):
    """Payload webhook Vital API"""
    user_id: str = Field(..., description="ID utilisateur Vital (external_user_id)")
    event_id: Optional[str] = Field(None, description="ID unique de l'événement pour idempotence")
    data: Dict = Field(..., description="Données biométriques")
    
    @validator('data')
    def validate_data(cls, v):
        """Valide que data contient au moins un type de données"""
        if not any(key in v for key in ['hr', 'hrv', 'sleep']):
            raise ValueError("data must contain at least one of: hr, hrv, sleep")
        return v


class VitalWebhookHandler:
    """Gestionnaire de webhook Vital API"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.webhook_secret = os.getenv("VITAL_WEBHOOK_SECRET")
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Vérifie la signature HMAC du webhook Vital
        
        Args:
            payload: Payload brut du webhook (string JSON)
            signature: Signature depuis le header x-vital-webhook-signature
        
        Returns:
            True si la signature est valide
        """
        if not self.webhook_secret:
            logger.warning("VITAL_WEBHOOK_SECRET not configured, skipping signature verification")
            return True  # Pas de secret configuré, on accepte
        
        try:
            # Calculer le HMAC SHA-256
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparer de manière sécurisée (timing-safe)
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def process_webhook(self, payload: Dict) -> Dict:
        """
        Traite un webhook Vital :
        1. Valide le payload
        2. Mappe Vital user_id -> Supabase user_id via external_identities
        3. Insère dans biometrics avec idempotence
        
        Returns:
            Dict avec status et message
        """
        try:
            # 1. Valider le payload
            try:
                validated = VitalWebhookPayload(**payload)
            except Exception as e:
                logger.error(f"Invalid Vital webhook payload: {e}")
                return {
                    "status": "error",
                    "message": f"Invalid payload: {str(e)}"
                }
            
            # 2. Mapper l'identité Vital -> Supabase
            supabase_user_id = self.supabase.get_user_by_external_id(
                external_user_id=validated.user_id,
                provider_system="vital"
            )
            
            if not supabase_user_id:
                logger.warning(f"Vital user_id {validated.user_id} not found in external_identities")
                # Retourner 202 Accepted (webhook accepté mais utilisateur non trouvé)
                return {
                    "status": "accepted",
                    "message": f"User {validated.user_id} not found, webhook accepted but not processed"
                }
            
            # 3. Insérer les données avec idempotence
            inserted_count = 0
            
            # HR
            if "hr" in validated.data and isinstance(validated.data["hr"], list):
                for hr_entry in validated.data["hr"]:
                    try:
                        hr_point = VitalHRDataPoint(**hr_entry)
                        source_event_id = validated.event_id or f"vital_hr_{hr_point.timestamp}_{hr_point.value}"
                        
                        recorded_at = parse_iso_datetime(hr_point.timestamp)
                        self.supabase.insert_biometric(
                            user_id=supabase_user_id,
                            metric_type="hr",
                            value=hr_point.value,
                            recorded_at=recorded_at,
                            raw_data=hr_entry,
                            source="vital",
                            source_event_id=source_event_id
                        )
                        inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting HR data: {e}")
            
            # HRV
            if "hrv" in validated.data and isinstance(validated.data["hrv"], list):
                for hrv_entry in validated.data["hrv"]:
                    try:
                        hrv_point = VitalHRVDataPoint(**hrv_entry)
                        source_event_id = validated.event_id or f"vital_hrv_{hrv_point.timestamp}_{hrv_point.value}"
                        
                        recorded_at = parse_iso_datetime(hrv_point.timestamp)
                        self.supabase.insert_biometric(
                            user_id=supabase_user_id,
                            metric_type="hrv",
                            value=hrv_point.value,
                            recorded_at=recorded_at,
                            raw_data=hrv_entry,
                            source="vital",
                            source_event_id=source_event_id
                        )
                        inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting HRV data: {e}")
            
            # Sleep
            if "sleep" in validated.data and isinstance(validated.data["sleep"], dict):
                try:
                    sleep_data = VitalSleepData(**validated.data["sleep"])
                    duration_minutes = int(sleep_data.duration_seconds / 60)
                    source_event_id = validated.event_id or f"vital_sleep_{sleep_data.start_time}"
                    
                    recorded_at = parse_iso_datetime(sleep_data.start_time)
                    self.supabase.insert_biometric(
                        user_id=supabase_user_id,
                        metric_type="sleep_duration",
                        value=float(duration_minutes),
                        recorded_at=recorded_at,
                        raw_data=sleep_data.dict(),
                        source="vital",
                        source_event_id=source_event_id
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Error inserting sleep data: {e}")
            
            # Steps
            if "steps" in validated.data and isinstance(validated.data["steps"], list):
                for step_entry in validated.data["steps"]:
                    try:
                        value = step_entry.get("value")
                        timestamp = step_entry.get("timestamp")
                        if value is not None and timestamp:
                            source_event_id = validated.event_id or f"vital_steps_{timestamp}_{value}"
                            recorded_at = parse_iso_datetime(timestamp)
                            self.supabase.insert_biometric(
                                user_id=supabase_user_id,
                                metric_type="steps",
                                value=float(value),
                                recorded_at=recorded_at,
                                raw_data=step_entry,
                                source="vital",
                                source_event_id=source_event_id
                            )
                            inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting steps data: {e}")
            
            # Calories
            if "calories" in validated.data and isinstance(validated.data["calories"], list):
                for calorie_entry in validated.data["calories"]:
                    try:
                        value = calorie_entry.get("value")
                        timestamp = calorie_entry.get("timestamp")
                        if value is not None and timestamp:
                            source_event_id = validated.event_id or f"vital_calories_{timestamp}_{value}"
                            recorded_at = parse_iso_datetime(timestamp)
                            self.supabase.insert_biometric(
                                user_id=supabase_user_id,
                                metric_type="calories",
                                value=float(value),
                                recorded_at=recorded_at,
                                raw_data=calorie_entry,
                                source="vital",
                                source_event_id=source_event_id
                            )
                            inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting calories data: {e}")
            
            # Workouts
            if "workouts" in validated.data and isinstance(validated.data["workouts"], list):
                for workout_entry in validated.data["workouts"]:
                    try:
                        duration_minutes = workout_entry.get("duration_minutes")
                        timestamp = workout_entry.get("start_time")
                        workout_type = workout_entry.get("type", "unknown")
                        
                        if duration_minutes is not None and timestamp:
                            source_event_id = validated.event_id or f"vital_workout_{timestamp}"
                            recorded_at = parse_iso_datetime(timestamp)
                            self.supabase.insert_biometric(
                                user_id=supabase_user_id,
                                metric_type="workout_duration",
                                value=float(duration_minutes),
                                recorded_at=recorded_at,
                                raw_data=workout_entry,
                                source="vital",
                                source_event_id=source_event_id
                            )
                            inserted_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting workout data: {e}")
            
            logger.info(f"Vital webhook processed: {inserted_count} metrics inserted for user {supabase_user_id}")
            
            return {
                "status": "success",
                "message": f"{inserted_count} metrics inserted successfully",
                "user_id": supabase_user_id
            }
        
        except Exception as e:
            logger.error(f"Error processing Vital webhook: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
