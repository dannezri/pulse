"""
Gestionnaire de webhook Vital API - Format officiel
Gère les webhooks au format standard Vital (event_type, client_user_id, etc.)
Support de 52+ types de données timeseries
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import hmac
import hashlib
import os
from supabase_client import SupabaseClient
from vital_timeseries_types import get_metric_config, is_supported_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VitalWebhookPayloadV2(BaseModel):
    """Payload webhook Vital API (format officiel)"""
    event_type: str = Field(..., description="Type d'événement (ex: historical.data.water.created)")
    user_id: str = Field(..., description="ID utilisateur Vital")
    client_user_id: str = Field(..., description="ID utilisateur client (Supabase UUID)")
    team_id: str = Field(..., description="ID team Vital")
    data: Dict = Field(..., description="Données de l'événement")


class VitalWebhookHandlerV2:
    """Gestionnaire de webhook Vital API - Format officiel"""
    
    def __init__(self, supabase_client: SupabaseClient, vital_client=None):
        self.supabase = supabase_client
        self.vital_client = vital_client
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
            return True
        
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
        Traite un webhook Vital au format officiel
        
        Args:
            payload: Dict contenant event_type, user_id, client_user_id, data
        
        Returns:
            Dict avec status et message
        """
        try:
            # 1. Valider le payload
            try:
                validated = VitalWebhookPayloadV2(**payload)
            except Exception as e:
                logger.error(f"Invalid Vital webhook payload: {e}")
                return {
                    "status": "error",
                    "message": f"Invalid payload: {str(e)}"
                }
            
            # 2. Utiliser le client_user_id (Supabase UUID) directement
            supabase_user_id = validated.client_user_id
            
            # 3. Logger l'événement
            logger.info(f"Vital webhook received: {validated.event_type} for user {supabase_user_id}")
            logger.info(f"Event data: {validated.data}")
            
            # 4. Traiter selon le type d'événement
            event_type = validated.event_type
            
            if event_type.startswith("historical.data."):
                # Événements historiques (backfill de données)
                data_type = event_type.replace("historical.data.", "").replace(".created", "")
                logger.info(f"Historical data event for {data_type}")
                logger.info(f"Provider: {validated.data.get('provider')}")
                logger.info(f"Date range: {validated.data.get('start_date')} to {validated.data.get('end_date')}")
                
                # Récupérer et insérer les données
                if self.vital_client and validated.data.get("is_final"):
                    self._fetch_and_insert_data(
                        supabase_user_id=supabase_user_id,
                        vital_user_id=validated.user_id,
                        data_type=data_type,
                        start_date=validated.data.get("start_date"),
                        end_date=validated.data.get("end_date"),
                        provider=validated.data.get("provider")
                    )
                
            elif event_type.startswith("timeseries.data."):
                # Événements en temps réel (streaming)
                data_type = event_type.replace("timeseries.data.", "").replace(".created", "")
                logger.info(f"Timeseries data event for {data_type}")
                
                # Pour timeseries, les données sont dans validated.data directement
                # Format: { "data": [...], "provider": "...", ... }
                if validated.data.get("data"):
                    self._process_timeseries_data(
                        supabase_user_id=supabase_user_id,
                        data_type=data_type,
                        timeseries_data=validated.data.get("data"),
                        provider=validated.data.get("provider")
                    )
                
            elif event_type.startswith("daily.data."):
                # Événements quotidiens
                data_type = event_type.replace("daily.data.", "").replace(".created", "")
                logger.info(f"Daily data event for {data_type}")
            
            # Marquer comme traité avec succès
            return {
                "status": "success",
                "message": f"Webhook {event_type} processed",
                "event_type": event_type,
                "user_id": supabase_user_id
            }
        
        except Exception as e:
            logger.error(f"Error processing Vital webhook: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _fetch_and_insert_data(
        self,
        supabase_user_id: str,
        vital_user_id: str,
        data_type: str,
        start_date: str,
        end_date: str,
        provider: str
    ):
        """
        Récupère les données depuis l'API Vital et les insère dans Supabase
        
        Args:
            supabase_user_id: ID utilisateur Supabase
            vital_user_id: ID utilisateur Vital
            data_type: Type de données (sleep, activity, body, workouts, etc.)
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
            provider: Provider source (fitbit, oura, etc.)
        """
        try:
            logger.info(f"Fetching {data_type} data for user {vital_user_id} from {start_date} to {end_date}")
            
            # Mapper les types de données aux méthodes du client
            data_fetchers = {
                "sleep": self.vital_client.get_sleep_data,
                "activity": self.vital_client.get_activity_data,
                "body": self.vital_client.get_body_data,
                "workouts": self.vital_client.get_workouts_data,
                "vitals": self.vital_client.get_vitals_data,
            }
            
            fetcher = data_fetchers.get(data_type)
            if not fetcher:
                logger.info(f"No fetcher for data type {data_type}, skipping")
                return
            
            # Récupérer les données
            data_records = fetcher(vital_user_id, start_date, end_date)
            
            if not data_records:
                logger.info(f"No {data_type} data to insert")
                return
            
            # Insérer dans Supabase
            inserted_count = 0
            for record in data_records:
                if self._insert_biometric_data(supabase_user_id, data_type, record, provider):
                    inserted_count += 1
            
            logger.info(f"Inserted {inserted_count}/{len(data_records)} {data_type} records for user {supabase_user_id}")
        
        except Exception as e:
            logger.error(f"Error fetching and inserting {data_type} data: {e}")
    
    def _process_timeseries_data(
        self,
        supabase_user_id: str,
        data_type: str,
        timeseries_data: list,
        provider: str
    ):
        """
        Process timeseries data from Vital (real-time streaming data)
        
        Args:
            supabase_user_id: ID utilisateur Supabase
            data_type: Type de données (heart_rate, glucose, etc.)
            timeseries_data: Liste de points de données timeseries
            provider: Provider source
        """
        try:
            logger.info(f"Processing {len(timeseries_data)} timeseries {data_type} points")
            
            inserted_count = 0
            for point in timeseries_data:
                # Map timeseries data point to biometric format
                biometric_data = self._map_timeseries_to_biometric(data_type, point, provider)
                
                if not biometric_data:
                    continue
                
                # Add user_id
                biometric_data["user_id"] = supabase_user_id
                
                # Check for duplicate
                if self._is_duplicate(biometric_data):
                    continue
                
                # Insert
                try:
                    self.supabase.client.table("biometrics").insert(biometric_data).execute()
                    inserted_count += 1
                except Exception as insert_error:
                    if "duplicate key" in str(insert_error).lower():
                        continue
                    else:
                        raise
            
            logger.info(f"Inserted {inserted_count}/{len(timeseries_data)} timeseries {data_type} points")
        
        except Exception as e:
            logger.error(f"Error processing timeseries {data_type} data: {e}")
    
    def _map_timeseries_to_biometric(self, data_type: str, point: Dict, provider: str) -> Optional[Dict]:
        """
        Map a timeseries data point to biometric format (universel - 52+ types)
        
        Args:
            data_type: Type de données Vital (heart_rate, glucose, steps, etc.)
            point: Point de données timeseries
            provider: Provider source
        
        Returns:
            Dict au format biometrics ou None
        """
        try:
            # Récupérer la configuration du type depuis le mapping universel
            config = get_metric_config(data_type)
            
            if not config:
                logger.warning(f"Unsupported timeseries type: {data_type}")
                return None
            
            # Extraire la valeur selon le champ configuré
            value_field = config["value_field"]
            if value_field not in point or point[value_field] is None:
                return None
            
            value = point[value_field]
            
            # Conversion spéciale pour le texte (notes, diary)
            if config["unit"] == "text":
                # Pour les notes, on stocke 0 comme valeur et le texte dans metadata
                biometric_data = {
                    "source": f"vital_{provider}",
                    "source_event_id": point.get("id"),
                    "recorded_at": point.get("timestamp"),
                    "metric_type": config["metric_type"],
                    "value": 0,
                    "metadata": {
                        "unit": config["unit"],
                        "type": "timeseries",
                        "category": config["category"],
                        "text": str(value)
                    }
                }
            else:
                # Conversion de la valeur en float
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    logger.warning(f"Cannot convert value to float: {value}")
                    return None
                
                # Conversion d'unités si nécessaire
                if config["unit"] == "m" and value > 1000:
                    # Distance: convertir mètres en km si > 1000m
                    value = value / 1000
                    unit = "km"
                else:
                    unit = config["unit"]
                
                biometric_data = {
                    "source": f"vital_{provider}",
                    "source_event_id": point.get("id"),
                    "recorded_at": point.get("timestamp"),
                    "metric_type": config["metric_type"],
                    "value": value,
                    "metadata": {
                        "unit": unit,
                        "type": "timeseries",
                        "category": config["category"]
                    }
                }
            
            # Ajouter les champs extra (ex: diastolic pour blood_pressure)
            if "extra_fields" in config:
                for meta_key, field_key in config["extra_fields"].items():
                    if field_key in point and point[field_key] is not None:
                        biometric_data["metadata"][meta_key] = point[field_key]
            
            return biometric_data
        
        except Exception as e:
            logger.error(f"Error mapping timeseries {data_type} data: {e}")
            return None
    
    def _insert_biometric_data(
        self,
        user_id: str,
        data_type: str,
        record: Dict,
        provider: str
    ) -> bool:
        """
        Insère un enregistrement biométrique dans Supabase avec déduplication
        
        Args:
            user_id: ID utilisateur Supabase
            data_type: Type de données (sleep, activity, body, workouts)
            record: Enregistrement de données Vital
            provider: Provider source
        
        Returns:
            True si l'insertion a réussi
        """
        try:
            # Mapper les données Vital au format Supabase biometrics
            biometric_records = self._map_vital_to_biometric(data_type, record, provider)
            
            if not biometric_records:
                return False
            
            # Normaliser en liste
            if not isinstance(biometric_records, list):
                biometric_records = [biometric_records]
            
            # Insérer chaque métrique (peut y avoir plusieurs métriques par record activity)
            inserted_count = 0
            for biometric_data in biometric_records:
                if not biometric_data:
                    continue
                
                # Ajouter user_id
                biometric_data["user_id"] = user_id
                
                # Vérifier si existe déjà (déduplication)
                if self._is_duplicate(biometric_data):
                    logger.debug(f"Skipping duplicate: {biometric_data.get('metric_type')} at {biometric_data.get('recorded_at')}")
                    continue
                
                # Insérer dans Supabase (upsert pour éviter les erreurs de conflit)
                try:
                    self.supabase.client.table("biometrics").insert(biometric_data).execute()
                    inserted_count += 1
                except Exception as insert_error:
                    # Si erreur de conflit unique, ignorer silencieusement (déjà inséré)
                    if "duplicate key" in str(insert_error).lower():
                        logger.debug(f"Duplicate key skipped: {biometric_data.get('metric_type')}")
                    else:
                        raise
            
            return inserted_count > 0
        
        except Exception as e:
            logger.error(f"Error inserting biometric data: {e}")
            return False
    
    def _is_duplicate(self, biometric_data: Dict) -> bool:
        """
        Vérifie si un enregistrement existe déjà dans Supabase
        
        Déduplication basée sur:
        - user_id + metric_type + recorded_at + source_event_id (si présent)
        - OU user_id + metric_type + recorded_at + value (si pas de source_event_id)
        
        Args:
            biometric_data: Données biométriques à vérifier
        
        Returns:
            True si doublon trouvé
        """
        try:
            query = self.supabase.client.table("biometrics").select("id")
            
            # Filtres obligatoires
            query = query.eq("user_id", biometric_data["user_id"])
            query = query.eq("metric_type", biometric_data["metric_type"])
            query = query.eq("recorded_at", biometric_data["recorded_at"])
            
            # Si source_event_id existe, l'utiliser pour déduplication
            if biometric_data.get("source_event_id"):
                query = query.eq("source_event_id", biometric_data["source_event_id"])
            else:
                # Sinon, utiliser la valeur et la source
                query = query.eq("value", biometric_data["value"])
                if biometric_data.get("source"):
                    query = query.eq("source", biometric_data["source"])
            
            result = query.execute()
            
            return len(result.data) > 0
        
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False  # En cas d'erreur, continuer l'insertion
    
    def _map_vital_to_biometric(self, data_type: str, record: Dict, provider: str) -> Optional[Dict]:
        """
        Mappe un enregistrement Vital au format biometrics Supabase
        
        Args:
            data_type: Type de données (sleep, activity, body, workouts)
            record: Enregistrement Vital
            provider: Provider source
        
        Returns:
            Dict au format biometrics ou None
        """
        try:
            base_data = {
                "source": f"vital_{provider}",
                "source_event_id": record.get("id"),
                "recorded_at": record.get("calendar_date") or record.get("date"),
            }
            
            if data_type == "sleep":
                return {
                    **base_data,
                    "metric_type": "sleep_duration",
                    "value": record.get("duration_seconds", 0) / 3600.0,  # Convertir en heures
                    "metadata": {
                        "unit": "hours",
                        "sleep_score": record.get("score"),
                        "deep_sleep_duration": record.get("deep_sleep_duration_seconds"),
                        "rem_sleep_duration": record.get("rem_sleep_duration_seconds"),
                        "light_sleep_duration": record.get("light_sleep_duration_seconds"),
                    }
                }
            
            elif data_type == "activity":
                # Retourner toutes les métriques d'activité
                metrics = []
                
                # Steps (pas)
                if "steps" in record and record["steps"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "steps",
                        "value": float(record["steps"]),
                        "metadata": {"unit": "count"}
                    })
                
                # Calories totales
                if "calories_total" in record and record["calories_total"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "calories",
                        "value": float(record["calories_total"]),
                        "metadata": {"unit": "kcal", "type": "total"}
                    })
                
                # Calories actives
                if "calories_active" in record and record["calories_active"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "active_calories",
                        "value": float(record["calories_active"]),
                        "metadata": {"unit": "kcal", "type": "active"}
                    })
                
                # Distance
                if "distance_meters" in record and record["distance_meters"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "distance",
                        "value": float(record["distance_meters"]) / 1000.0,  # km
                        "metadata": {"unit": "km"}
                    })
                
                # Étages montés
                if "floors_climbed" in record and record["floors_climbed"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "floors_climbed",
                        "value": float(record["floors_climbed"]),
                        "metadata": {"unit": "count"}
                    })
                
                # Minutes actives
                if "active_duration_minutes" in record and record["active_duration_minutes"] is not None:
                    metrics.append({
                        **base_data,
                        "metric_type": "active_minutes",
                        "value": float(record["active_duration_minutes"]),
                        "metadata": {"unit": "minutes"}
                    })
                
                # Retourner toutes les métriques
                return metrics if metrics else None
            
            elif data_type == "body":
                if "weight" in record:
                    return {
                        **base_data,
                        "metric_type": "weight",
                        "value": record.get("weight", 0),
                        "metadata": {"unit": "kg"}
                    }
            
            elif data_type == "workouts":
                return {
                    **base_data,
                    "metric_type": "workout",
                    "value": record.get("moving_time", 0) / 60.0,  # minutes
                    "metadata": {
                        "unit": "minutes",
                        "sport": record.get("sport"),
                        "calories": record.get("calories"),
                        "distance_meters": record.get("distance_meters"),
                        "average_hr": record.get("average_hr"),
                        "max_hr": record.get("max_hr"),
                    }
                }
            
            elif data_type == "vitals":
                # Retourner toutes les métriques vitales
                metrics = []
                
                # HRV (Heart Rate Variability)
                if "hrv_rmssd_sdnn" in record and record["hrv_rmssd_sdnn"]:
                    hrv_data = record["hrv_rmssd_sdnn"]
                    if "avg_hrv_rmssd" in hrv_data and hrv_data["avg_hrv_rmssd"] is not None:
                        metrics.append({
                            **base_data,
                            "metric_type": "hrv",
                            "value": float(hrv_data["avg_hrv_rmssd"]),
                            "metadata": {
                                "unit": "ms",
                                "type": "rmssd",
                                "sdnn": hrv_data.get("avg_hrv_sdnn")
                            }
                        })
                
                # Resting Heart Rate
                if "heart_rate" in record and record["heart_rate"]:
                    hr_data = record["heart_rate"]
                    if "avg_bpm" in hr_data and hr_data["avg_bpm"] is not None:
                        metrics.append({
                            **base_data,
                            "metric_type": "heart_rate",
                            "value": float(hr_data["avg_bpm"]),
                            "metadata": {
                                "unit": "bpm",
                                "max_bpm": hr_data.get("max_bpm"),
                                "min_bpm": hr_data.get("min_bpm"),
                                "resting_bpm": hr_data.get("resting_bpm")
                            }
                        })
                
                # SpO2 (Oxygen Saturation)
                if "oxygen_saturation" in record and record["oxygen_saturation"]:
                    spo2_data = record["oxygen_saturation"]
                    if "avg_saturation" in spo2_data and spo2_data["avg_saturation"] is not None:
                        metrics.append({
                            **base_data,
                            "metric_type": "spo2",
                            "value": float(spo2_data["avg_saturation"]),
                            "metadata": {
                                "unit": "%",
                                "min_saturation": spo2_data.get("min_saturation")
                            }
                        })
                
                # Respiratory Rate
                if "respiratory_rate" in record and record["respiratory_rate"]:
                    resp_data = record["respiratory_rate"]
                    if "avg_breaths_per_minute" in resp_data and resp_data["avg_breaths_per_minute"] is not None:
                        metrics.append({
                            **base_data,
                            "metric_type": "respiratory_rate",
                            "value": float(resp_data["avg_breaths_per_minute"]),
                            "metadata": {
                                "unit": "bpm",
                                "type": "breaths_per_minute"
                            }
                        })
                
                return metrics if metrics else None
            
            return None
        
        except Exception as e:
            logger.error(f"Error mapping Vital data to biometric: {e}")
            return None
