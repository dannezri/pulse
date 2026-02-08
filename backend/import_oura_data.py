"""
Script pour importer les données Oura dans Supabase
Usage: python import_oura_data.py
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from oura_client import get_oura_client
from supabase_client import SupabaseClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OuraDataImporter:
    """Importe les données Oura dans Supabase"""
    
    def __init__(self, oura_token: str, supabase_url: str, supabase_key: str):
        """
        Initialise l'importeur
        
        Args:
            oura_token: Token d'accès Oura
            supabase_url: URL du projet Supabase
            supabase_key: Clé service_role Supabase
        """
        self.oura_client = get_oura_client(oura_token)
        self.supabase = SupabaseClient(supabase_url, supabase_key)
        self.stats = {
            "total_inserted": 0,
            "total_duplicates": 0,
            "total_errors": 0,
            "by_metric": {}
        }
    
    def normalize_sleep_data(self, sleep_records: List[Dict], user_id: str):
        """
        Normalise et insère les données de sommeil Oura
        
        Args:
            sleep_records: Liste des enregistrements de sommeil
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(sleep_records)} sleep records")
        
        for record in sleep_records:
            try:
                # Timestamp principal (jour du sommeil)
                day = record.get("day")
                if not day:
                    continue
                
                timestamp = datetime.fromisoformat(day.replace("Z", "+00:00"))
                record_id = record.get("id")
                
                # Score de sommeil total
                score = record.get("score")
                if score is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_score",
                        value=float(score),
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_sleep_score_{record_id}"
                    )
                
                # Durée totale de sommeil (en secondes -> convertir en heures)
                total_sleep_duration = record.get("contributors", {}).get("total_sleep_duration")
                if total_sleep_duration is not None:
                    hours = total_sleep_duration / 3600.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_duration",
                        value=hours,
                        recorded_at=timestamp,
                        raw_data={"total_sleep_duration": total_sleep_duration, "source": "oura"},
                        source_event_id=f"oura_sleep_duration_{record_id}"
                    )
                
                # Efficacité du sommeil
                sleep_efficiency = record.get("contributors", {}).get("sleep_efficiency")
                if sleep_efficiency is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_efficiency",
                        value=float(sleep_efficiency),
                        recorded_at=timestamp,
                        raw_data={"sleep_efficiency": sleep_efficiency, "source": "oura"},
                        source_event_id=f"oura_sleep_efficiency_{record_id}"
                    )
                
                # Deep sleep (sommeil profond) en secondes -> minutes
                deep_sleep_duration = record.get("contributors", {}).get("deep_sleep_duration")
                if deep_sleep_duration is not None:
                    minutes = deep_sleep_duration / 60.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="deep_sleep_minutes",
                        value=minutes,
                        recorded_at=timestamp,
                        raw_data={"deep_sleep_duration": deep_sleep_duration, "source": "oura"},
                        source_event_id=f"oura_deep_sleep_{record_id}"
                    )
                
                # REM sleep en secondes -> minutes
                rem_sleep_duration = record.get("contributors", {}).get("rem_sleep_duration")
                if rem_sleep_duration is not None:
                    minutes = rem_sleep_duration / 60.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="rem_sleep_minutes",
                        value=minutes,
                        recorded_at=timestamp,
                        raw_data={"rem_sleep_duration": rem_sleep_duration, "source": "oura"},
                        source_event_id=f"oura_rem_sleep_{record_id}"
                    )
                
                # Resting heart rate (FC au repos)
                resting_hr = record.get("contributors", {}).get("resting_heart_rate")
                if resting_hr is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="resting_hr",
                        value=float(resting_hr),
                        recorded_at=timestamp,
                        raw_data={"resting_heart_rate": resting_hr, "source": "oura"},
                        source_event_id=f"oura_resting_hr_sleep_{record_id}"
                    )
                
                # HRV moyenne
                hrv_avg = record.get("contributors", {}).get("hrv_balance")
                if hrv_avg is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="hrv",
                        value=float(hrv_avg),
                        recorded_at=timestamp,
                        raw_data={"hrv_balance": hrv_avg, "source": "oura"},
                        source_event_id=f"oura_hrv_sleep_{record_id}"
                    )
                
                # TIMESTAMPS DE SOMMEIL (bedtime_start, bedtime_end)
                # Ces données sont cruciales pour calculer l'heure de réveil réelle
                bedtime_start = record.get("bedtime_start")
                if bedtime_start:
                    bedtime_start_dt = datetime.fromisoformat(bedtime_start.replace("Z", "+00:00"))
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="bedtime_start",
                        value=bedtime_start_dt.hour + (bedtime_start_dt.minute / 60.0),  # Heure décimale
                        recorded_at=bedtime_start_dt,
                        raw_data={"bedtime_start": bedtime_start, "source": "oura"},
                        source_event_id=f"oura_bedtime_start_{record_id}"
                    )
                    logger.info(f"Stored bedtime_start: {bedtime_start} (hour: {bedtime_start_dt.hour})")
                
                bedtime_end = record.get("bedtime_end")
                if bedtime_end:
                    bedtime_end_dt = datetime.fromisoformat(bedtime_end.replace("Z", "+00:00"))
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="bedtime_end",
                        value=bedtime_end_dt.hour + (bedtime_end_dt.minute / 60.0),  # Heure décimale
                        recorded_at=bedtime_end_dt,
                        raw_data={"bedtime_end": bedtime_end, "source": "oura"},
                        source_event_id=f"oura_bedtime_end_{record_id}"
                    )
                    logger.info(f"Stored bedtime_end: {bedtime_end} (hour: {bedtime_end_dt.hour})")
                
            except Exception as e:
                logger.error(f"Error processing sleep record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_activity_data(self, activity_records: List[Dict], user_id: str):
        """
        Normalise et insère les données d'activité Oura
        
        Args:
            activity_records: Liste des enregistrements d'activité
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(activity_records)} activity records")
        
        for record in activity_records:
            try:
                day = record.get("day")
                if not day:
                    continue
                
                timestamp = datetime.fromisoformat(day.replace("Z", "+00:00"))
                record_id = record.get("id")
                
                # Score d'activité
                score = record.get("score")
                if score is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="activity_score",
                        value=float(score),
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_activity_score_{record_id}"
                    )
                
                # Nombre de pas
                steps = record.get("steps")
                if steps is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="steps",
                        value=float(steps),
                        recorded_at=timestamp,
                        raw_data={"steps": steps, "source": "oura"},
                        source_event_id=f"oura_steps_{record_id}"
                    )
                
                # Calories actives
                active_calories = record.get("active_calories")
                if active_calories is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="active_calories",
                        value=float(active_calories),
                        recorded_at=timestamp,
                        raw_data={"active_calories": active_calories, "source": "oura"},
                        source_event_id=f"oura_active_calories_{record_id}"
                    )
                
                # Calories totales
                total_calories = record.get("total_calories")
                if total_calories is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="total_calories",
                        value=float(total_calories),
                        recorded_at=timestamp,
                        raw_data={"total_calories": total_calories, "source": "oura"},
                        source_event_id=f"oura_total_calories_{record_id}"
                    )
                
                # Équivalent MET (intensité d'activité)
                equivalent_walking_distance = record.get("equivalent_walking_distance")
                if equivalent_walking_distance is not None:
                    # Convertir mètres en km
                    km = equivalent_walking_distance / 1000.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="walking_distance_km",
                        value=km,
                        recorded_at=timestamp,
                        raw_data={"equivalent_walking_distance": equivalent_walking_distance, "source": "oura"},
                        source_event_id=f"oura_walking_distance_{record_id}"
                    )
                
                # Temps d'inactivité (en secondes -> heures)
                sedentary_time = record.get("sedentary_time")
                if sedentary_time is not None:
                    hours = sedentary_time / 3600.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sedentary_hours",
                        value=hours,
                        recorded_at=timestamp,
                        raw_data={"sedentary_time": sedentary_time, "source": "oura"},
                        source_event_id=f"oura_sedentary_time_{record_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing activity record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_readiness_data(self, readiness_records: List[Dict], user_id: str):
        """
        Normalise et insère les données de préparation (readiness) Oura
        
        Args:
            readiness_records: Liste des enregistrements de readiness
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(readiness_records)} readiness records")
        
        for record in readiness_records:
            try:
                day = record.get("day")
                if not day:
                    continue
                
                timestamp = datetime.fromisoformat(day.replace("Z", "+00:00"))
                record_id = record.get("id")
                
                # Score de préparation
                score = record.get("score")
                if score is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="readiness_score",
                        value=float(score),
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_readiness_score_{record_id}"
                    )
                
                # Température corporelle (déviation)
                temperature_deviation = record.get("contributors", {}).get("body_temperature")
                if temperature_deviation is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="body_temperature_deviation",
                        value=float(temperature_deviation),
                        recorded_at=timestamp,
                        raw_data={"body_temperature": temperature_deviation, "source": "oura"},
                        source_event_id=f"oura_body_temp_{record_id}"
                    )
                
                # Recovery index (indice de récupération)
                recovery_index = record.get("contributors", {}).get("recovery_index")
                if recovery_index is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="recovery_index",
                        value=float(recovery_index),
                        recorded_at=timestamp,
                        raw_data={"recovery_index": recovery_index, "source": "oura"},
                        source_event_id=f"oura_recovery_index_{record_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing readiness record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_heart_rate_data(self, hr_records: List[Dict], user_id: str):
        """
        Normalise et insère les données de fréquence cardiaque Oura
        
        Args:
            hr_records: Liste des enregistrements de FC
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(hr_records)} heart rate records")
        
        for record in hr_records:
            try:
                timestamp_str = record.get("timestamp")
                if not timestamp_str:
                    continue
                
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                
                # Fréquence cardiaque
                bpm = record.get("bpm")
                if bpm is not None:
                    # Utiliser timestamp comme partie de l'ID pour l'idempotence
                    ts_id = timestamp_str.replace(":", "").replace("-", "").replace(".", "")
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="hr",
                        value=float(bpm),
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_hr_{ts_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing heart rate record: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_spo2_data(self, spo2_records: List[Dict], user_id: str):
        """
        Normalise et insère les données SpO2 Oura
        
        Args:
            spo2_records: Liste des enregistrements SpO2
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(spo2_records)} SpO2 records")
        
        for record in spo2_records:
            try:
                day = record.get("day")
                if not day:
                    continue
                
                timestamp = datetime.fromisoformat(day.replace("Z", "+00:00"))
                record_id = record.get("id")
                
                # SpO2 moyenne
                spo2_percentage = record.get("spo2_percentage", {}).get("average")
                if spo2_percentage is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="spo2",
                        value=float(spo2_percentage),
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_spo2_{record_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing SpO2 record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_workout_data(self, workout_records: List[Dict], user_id: str):
        """
        Normalise et insère les données d'entraînement Oura
        
        Args:
            workout_records: Liste des entraînements
            user_id: UUID Supabase de l'utilisateur
        """
        logger.info(f"Processing {len(workout_records)} workout records")
        
        for record in workout_records:
            try:
                start_datetime = record.get("start_datetime")
                if not start_datetime:
                    continue
                
                timestamp = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
                record_id = record.get("id")
                
                # Durée d'entraînement (en secondes -> minutes)
                duration = record.get("duration")
                if duration is not None:
                    minutes = duration / 60.0
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="workout_duration_minutes",
                        value=minutes,
                        recorded_at=timestamp,
                        raw_data=record,
                        source_event_id=f"oura_workout_duration_{record_id}"
                    )
                
                # Calories brûlées
                calories = record.get("calories")
                if calories is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="workout_calories",
                        value=float(calories),
                        recorded_at=timestamp,
                        raw_data={"calories": calories, "activity": record.get("activity"), "source": "oura"},
                        source_event_id=f"oura_workout_calories_{record_id}"
                    )
                
                # Intensité (si disponible)
                intensity = record.get("intensity")
                if intensity:
                    # Mapper les valeurs textuelles vers des nombres (1-5)
                    intensity_map = {"easy": 1, "moderate": 3, "hard": 5}
                    intensity_value = intensity_map.get(intensity.lower(), 3)
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="workout_intensity",
                        value=float(intensity_value),
                        recorded_at=timestamp,
                        raw_data={"intensity": intensity, "source": "oura"},
                        source_event_id=f"oura_workout_intensity_{record_id}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing workout record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def _insert_metric(
        self,
        user_id: str,
        metric_type: str,
        value: float,
        recorded_at: datetime,
        raw_data: Dict,
        source_event_id: str
    ):
        """
        Insère une métrique dans Supabase avec gestion de l'idempotence
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            metric_type: Type de métrique
            value: Valeur de la métrique
            recorded_at: Timestamp de l'enregistrement
            raw_data: Données brutes
            source_event_id: ID unique de l'événement
        """
        result = self.supabase.insert_biometric(
            user_id=user_id,
            metric_type=metric_type,
            value=value,
            recorded_at=recorded_at,
            raw_data=raw_data,
            source="oura",
            source_event_id=source_event_id
        )
        
        status = result.get("status")
        if status == "inserted":
            self.stats["total_inserted"] += 1
            if metric_type not in self.stats["by_metric"]:
                self.stats["by_metric"][metric_type] = {"inserted": 0, "duplicates": 0}
            self.stats["by_metric"][metric_type]["inserted"] += 1
        elif status == "duplicate":
            self.stats["total_duplicates"] += 1
            if metric_type not in self.stats["by_metric"]:
                self.stats["by_metric"][metric_type] = {"inserted": 0, "duplicates": 0}
            self.stats["by_metric"][metric_type]["duplicates"] += 1
        else:
            self.stats["total_errors"] += 1
    
    def import_all_data(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_back: int = 90
    ):
        """
        Importe toutes les données Oura disponibles
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            start_date: Date de début (YYYY-MM-DD), optionnel
            end_date: Date de fin (YYYY-MM-DD), optionnel
            days_back: Nombre de jours à récupérer si start_date n'est pas fourni (défaut: 90)
        """
        logger.info(f"Starting Oura data import for user {user_id}")
        
        # Définir les dates par défaut
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching data from {start_date} to {end_date}")
        
        # Récupérer toutes les données
        all_data = self.oura_client.get_all_data(start_date, end_date, days_back)
        
        # Traiter chaque type de données
        self.normalize_sleep_data(all_data.get("daily_sleep", []), user_id)
        self.normalize_activity_data(all_data.get("daily_activity", []), user_id)
        self.normalize_readiness_data(all_data.get("daily_readiness", []), user_id)
        self.normalize_heart_rate_data(all_data.get("heart_rate", []), user_id)
        self.normalize_spo2_data(all_data.get("daily_spo2", []), user_id)
        self.normalize_workout_data(all_data.get("workouts", []), user_id)
        
        # Afficher les statistiques
        self._print_stats()
        
        logger.info("Oura data import completed!")
    
    def _print_stats(self):
        """Affiche les statistiques d'importation"""
        logger.info("=" * 60)
        logger.info("IMPORT STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total metrics inserted: {self.stats['total_inserted']}")
        logger.info(f"Total duplicates skipped: {self.stats['total_duplicates']}")
        logger.info(f"Total errors: {self.stats['total_errors']}")
        logger.info("")
        logger.info("By metric type:")
        for metric_type, counts in sorted(self.stats["by_metric"].items()):
            logger.info(f"  {metric_type}:")
            logger.info(f"    - Inserted: {counts['inserted']}")
            logger.info(f"    - Duplicates: {counts['duplicates']}")
        logger.info("=" * 60)


def main():
    """Fonction principale"""
    # Configuration depuis les arguments ou variables d'environnement
    from user_config import get_dev_user_uuid
    USER_UUID = get_dev_user_uuid()
    
    # Charger les credentials Supabase depuis l'environnement
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
        sys.exit(1)
    
    # Récupérer le token Oura depuis Supabase
    from oura_token_utils import get_user_oura_token
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    OURA_TOKEN = get_user_oura_token(supabase, USER_UUID)
    
    if not OURA_TOKEN:
        logger.error(f"❌ Aucun token Oura trouvé pour l'utilisateur {USER_UUID}")
        logger.error("   Exécutez d'abord: python register_oura_user.py")
        sys.exit(1)
    
    # Créer l'importeur
    importer = OuraDataImporter(
        oura_token=OURA_TOKEN,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    # Importer les données (90 derniers jours par défaut)
    importer.import_all_data(
        user_id=USER_UUID,
        days_back=90  # Récupérer les 3 derniers mois
    )


if __name__ == "__main__":
    main()
