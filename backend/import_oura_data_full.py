"""
Script d'import COMPLET des données Oura (version améliorée)
Importe TOUTES les données brutes et granulaires disponibles

Usage: python import_oura_data_full.py
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


class OuraDataImporterFull:
    """Importeur COMPLET des données Oura (données brutes + scores)"""
    
    def __init__(self, oura_token: str, supabase_url: str, supabase_key: str):
        self.oura_client = get_oura_client(oura_token)
        self.supabase = SupabaseClient(supabase_url, supabase_key)
        self.stats = {
            "total_inserted": 0,
            "total_duplicates": 0,
            "total_errors": 0,
            "by_metric": {}
        }
    
    def normalize_sleep_data_full(self, sleep_records: List[Dict], user_id: str):
        """
        Normalise TOUTES les données de sommeil Oura (brutes + calculées)
        """
        logger.info(f"Processing {len(sleep_records)} sleep records (FULL mode)")
        
        for record in sleep_records:
            try:
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
                
                # Contributeurs individuels (NOUVEAU - données brutes)
                contributors = record.get("contributors", {})
                
                # Deep sleep contributor (score 0-100)
                if "deep_sleep" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_deep_score",
                        value=float(contributors["deep_sleep"]),
                        recorded_at=timestamp,
                        raw_data={"deep_sleep_score": contributors["deep_sleep"], "source": "oura"},
                        source_event_id=f"oura_sleep_deep_score_{record_id}"
                    )
                
                # Efficiency contributor
                if "efficiency" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_efficiency_score",
                        value=float(contributors["efficiency"]),
                        recorded_at=timestamp,
                        raw_data={"efficiency_score": contributors["efficiency"], "source": "oura"},
                        source_event_id=f"oura_sleep_efficiency_score_{record_id}"
                    )
                
                # Latency contributor (temps pour s'endormir)
                if "latency" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_latency_score",
                        value=float(contributors["latency"]),
                        recorded_at=timestamp,
                        raw_data={"latency_score": contributors["latency"], "source": "oura"},
                        source_event_id=f"oura_sleep_latency_score_{record_id}"
                    )
                
                # REM sleep contributor
                if "rem_sleep" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_rem_score",
                        value=float(contributors["rem_sleep"]),
                        recorded_at=timestamp,
                        raw_data={"rem_sleep_score": contributors["rem_sleep"], "source": "oura"},
                        source_event_id=f"oura_sleep_rem_score_{record_id}"
                    )
                
                # Restfulness contributor
                if "restfulness" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_restfulness_score",
                        value=float(contributors["restfulness"]),
                        recorded_at=timestamp,
                        raw_data={"restfulness_score": contributors["restfulness"], "source": "oura"},
                        source_event_id=f"oura_sleep_restfulness_score_{record_id}"
                    )
                
                # Timing contributor
                if "timing" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_timing_score",
                        value=float(contributors["timing"]),
                        recorded_at=timestamp,
                        raw_data={"timing_score": contributors["timing"], "source": "oura"},
                        source_event_id=f"oura_sleep_timing_score_{record_id}"
                    )
                
                # Total sleep contributor
                if "total_sleep" in contributors:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sleep_total_score",
                        value=float(contributors["total_sleep"]),
                        recorded_at=timestamp,
                        raw_data={"total_sleep_score": contributors["total_sleep"], "source": "oura"},
                        source_event_id=f"oura_sleep_total_score_{record_id}"
                    )
                
                # TIMESTAMPS DE SOMMEIL (bedtime_start, bedtime_end)
                # Ces données sont cruciales pour calculer l'heure de réveil réelle
                bedtime_start = record.get("bedtime_start")
                if bedtime_start:
                    bedtime_start_dt = datetime.fromisoformat(bedtime_start.replace("Z", "+00:00"))
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="bedtime_start",
                        value=bedtime_start_dt.hour + (bedtime_start_dt.minute / 60.0),  # Heure décimale (ex: 23.5 = 23h30)
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
                        value=bedtime_end_dt.hour + (bedtime_end_dt.minute / 60.0),  # Heure décimale (ex: 7.5 = 7h30)
                        recorded_at=bedtime_end_dt,
                        raw_data={"bedtime_end": bedtime_end, "source": "oura"},
                        source_event_id=f"oura_bedtime_end_{record_id}"
                    )
                    logger.info(f"Stored bedtime_end: {bedtime_end} (hour: {bedtime_end_dt.hour})")
                
            except Exception as e:
                logger.error(f"Error processing sleep record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_activity_data_full(self, activity_records: List[Dict], user_id: str):
        """
        Normalise TOUTES les données d'activité Oura (incluant MET minute par minute)
        """
        logger.info(f"Processing {len(activity_records)} activity records (FULL mode)")
        
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
                
                # Données de base
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
                
                # === NOUVEAU : Données granulaires d'activité ===
                
                # Temps d'activité par niveau (high, medium, low)
                high_activity_time = record.get("high_activity_time")
                if high_activity_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="high_activity_time_seconds",
                        value=float(high_activity_time),
                        recorded_at=timestamp,
                        raw_data={"high_activity_time": high_activity_time, "source": "oura"},
                        source_event_id=f"oura_high_activity_time_{record_id}"
                    )
                
                medium_activity_time = record.get("medium_activity_time")
                if medium_activity_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="medium_activity_time_seconds",
                        value=float(medium_activity_time),
                        recorded_at=timestamp,
                        raw_data={"medium_activity_time": medium_activity_time, "source": "oura"},
                        source_event_id=f"oura_medium_activity_time_{record_id}"
                    )
                
                low_activity_time = record.get("low_activity_time")
                if low_activity_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="low_activity_time_seconds",
                        value=float(low_activity_time),
                        recorded_at=timestamp,
                        raw_data={"low_activity_time": low_activity_time, "source": "oura"},
                        source_event_id=f"oura_low_activity_time_{record_id}"
                    )
                
                # MET minutes par niveau
                high_activity_met = record.get("high_activity_met_minutes")
                if high_activity_met is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="high_activity_met_minutes",
                        value=float(high_activity_met),
                        recorded_at=timestamp,
                        raw_data={"high_activity_met_minutes": high_activity_met, "source": "oura"},
                        source_event_id=f"oura_high_activity_met_{record_id}"
                    )
                
                medium_activity_met = record.get("medium_activity_met_minutes")
                if medium_activity_met is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="medium_activity_met_minutes",
                        value=float(medium_activity_met),
                        recorded_at=timestamp,
                        raw_data={"medium_activity_met_minutes": medium_activity_met, "source": "oura"},
                        source_event_id=f"oura_medium_activity_met_{record_id}"
                    )
                
                low_activity_met = record.get("low_activity_met_minutes")
                if low_activity_met is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="low_activity_met_minutes",
                        value=float(low_activity_met),
                        recorded_at=timestamp,
                        raw_data={"low_activity_met_minutes": low_activity_met, "source": "oura"},
                        source_event_id=f"oura_low_activity_met_{record_id}"
                    )
                
                # Non-wear time
                non_wear_time = record.get("non_wear_time")
                if non_wear_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="non_wear_time_seconds",
                        value=float(non_wear_time),
                        recorded_at=timestamp,
                        raw_data={"non_wear_time": non_wear_time, "source": "oura"},
                        source_event_id=f"oura_non_wear_time_{record_id}"
                    )
                
                # Resting time
                resting_time = record.get("resting_time")
                if resting_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="resting_time_seconds",
                        value=float(resting_time),
                        recorded_at=timestamp,
                        raw_data={"resting_time": resting_time, "source": "oura"},
                        source_event_id=f"oura_resting_time_{record_id}"
                    )
                
                # Sedentary time (déjà dans version de base mais avec nouveau nom)
                sedentary_time = record.get("sedentary_time")
                if sedentary_time is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="sedentary_time_seconds",
                        value=float(sedentary_time),
                        recorded_at=timestamp,
                        raw_data={"sedentary_time": sedentary_time, "source": "oura"},
                        source_event_id=f"oura_sedentary_time_{record_id}"
                    )
                
                # Average MET minutes
                avg_met = record.get("average_met_minutes")
                if avg_met is not None:
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="average_met_minutes",
                        value=float(avg_met),
                        recorded_at=timestamp,
                        raw_data={"average_met_minutes": avg_met, "source": "oura"},
                        source_event_id=f"oura_avg_met_{record_id}"
                    )
                
                # === NOUVEAU : MET minute par minute (données vraiment brutes !) ===
                met_data = record.get("met", {})
                if met_data and "items" in met_data:
                    # On stocke les données MET dans raw_data pour ne pas exploser le nombre de lignes
                    # Mais on crée une métrique avec la valeur moyenne
                    met_items = met_data["items"]
                    if met_items:
                        avg_met_value = sum(met_items) / len(met_items)
                        self._insert_metric(
                            user_id=user_id,
                            metric_type="met_timeseries_avg",
                            value=avg_met_value,
                            recorded_at=timestamp,
                            raw_data={
                                "met_items": met_items,
                                "interval": met_data.get("interval"),
                                "timestamp": met_data.get("timestamp"),
                                "source": "oura"
                            },
                            source_event_id=f"oura_met_timeseries_{record_id}"
                        )
                
                # === NOUVEAU : Classification 5-minutes (class_5_min) ===
                class_5_min = record.get("class_5_min")
                if class_5_min:
                    # Stocker la séquence complète dans raw_data
                    # Les valeurs sont: 0=non-wear, 1=rest, 2=inactive, 3=low, 4=medium, 5=high
                    self._insert_metric(
                        user_id=user_id,
                        metric_type="activity_class_5min",
                        value=0.0,  # Valeur symbolique, les vraies données sont dans raw_data
                        recorded_at=timestamp,
                        raw_data={
                            "class_5_min": class_5_min,
                            "description": "0=non-wear, 1=rest, 2=inactive, 3=low, 4=medium, 5=high",
                            "source": "oura"
                        },
                        source_event_id=f"oura_class_5min_{record_id}"
                    )
                
                # Contributeurs d'activité
                contributors = record.get("contributors", {})
                
                contributor_map = {
                    "meet_daily_targets": "activity_daily_targets_score",
                    "move_every_hour": "activity_move_hourly_score",
                    "recovery_time": "activity_recovery_time_score",
                    "stay_active": "activity_stay_active_score",
                    "training_frequency": "activity_training_freq_score",
                    "training_volume": "activity_training_vol_score"
                }
                
                for contributor_key, metric_type in contributor_map.items():
                    if contributor_key in contributors:
                        self._insert_metric(
                            user_id=user_id,
                            metric_type=metric_type,
                            value=float(contributors[contributor_key]),
                            recorded_at=timestamp,
                            raw_data={contributor_key: contributors[contributor_key], "source": "oura"},
                            source_event_id=f"oura_{contributor_key}_{record_id}"
                        )
                
            except Exception as e:
                logger.error(f"Error processing activity record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_readiness_data_full(self, readiness_records: List[Dict], user_id: str):
        """
        Normalise TOUTES les données de readiness Oura
        """
        logger.info(f"Processing {len(readiness_records)} readiness records (FULL mode)")
        
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
                
                # Contributeurs de readiness
                contributors = record.get("contributors", {})
                
                contributor_map = {
                    "activity_balance": "readiness_activity_balance_score",
                    "body_temperature": "readiness_body_temp_score",
                    "hrv_balance": "readiness_hrv_balance_score",
                    "previous_day_activity": "readiness_prev_day_activity_score",
                    "previous_night": "readiness_prev_night_score",
                    "recovery_index": "readiness_recovery_index_score",
                    "resting_heart_rate": "readiness_resting_hr_score",
                    "sleep_balance": "readiness_sleep_balance_score"
                }
                
                for contributor_key, metric_type in contributor_map.items():
                    if contributor_key in contributors:
                        self._insert_metric(
                            user_id=user_id,
                            metric_type=metric_type,
                            value=float(contributors[contributor_key]),
                            recorded_at=timestamp,
                            raw_data={contributor_key: contributors[contributor_key], "source": "oura"},
                            source_event_id=f"oura_{contributor_key}_{record_id}"
                        )
                
            except Exception as e:
                logger.error(f"Error processing readiness record {record.get('id')}: {e}")
                self.stats["total_errors"] += 1
    
    def normalize_heart_rate_data(self, hr_records: List[Dict], user_id: str):
        """Normalise les données de fréquence cardiaque"""
        logger.info(f"Processing {len(hr_records)} heart rate records")
        
        for record in hr_records:
            try:
                timestamp_str = record.get("timestamp")
                if not timestamp_str:
                    continue
                
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                bpm = record.get("bpm")
                
                if bpm is not None:
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
        """Normalise les données SpO2"""
        logger.info(f"Processing {len(spo2_records)} SpO2 records")
        
        for record in spo2_records:
            try:
                day = record.get("day")
                if not day:
                    continue
                
                timestamp = datetime.fromisoformat(day.replace("Z", "+00:00"))
                record_id = record.get("id")
                
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
    
    def _insert_metric(
        self,
        user_id: str,
        metric_type: str,
        value: float,
        recorded_at: datetime,
        raw_data: Dict,
        source_event_id: str
    ):
        """Insère une métrique dans Supabase"""
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
        """Importe TOUTES les données Oura disponibles (version complète)"""
        logger.info(f"Starting FULL Oura data import for user {user_id}")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Fetching data from {start_date} to {end_date}")
        
        # Récupérer toutes les données
        all_data = self.oura_client.get_all_data(start_date, end_date, days_back)
        
        # Traiter avec les méthodes complètes
        self.normalize_sleep_data_full(all_data.get("daily_sleep", []), user_id)
        self.normalize_activity_data_full(all_data.get("daily_activity", []), user_id)
        self.normalize_readiness_data_full(all_data.get("daily_readiness", []), user_id)
        self.normalize_heart_rate_data(all_data.get("heart_rate", []), user_id)
        self.normalize_spo2_data(all_data.get("daily_spo2", []), user_id)
        
        # Afficher les statistiques
        self._print_stats()
        
        logger.info("FULL Oura data import completed!")
    
    def _print_stats(self):
        """Affiche les statistiques d'importation"""
        logger.info("=" * 60)
        logger.info("FULL IMPORT STATISTICS")
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


def main(user_id: Optional[str] = None):
    """Fonction principale
    
    Args:
        user_id: UUID de l'utilisateur Supabase (optionnel, depuis DEV_USER_UUID env var)
    """
    import asyncio
    
    if user_id:
        USER_UUID = user_id
    else:
        from user_config import get_dev_user_uuid
        USER_UUID = get_dev_user_uuid()
    
    logger.info(f"🔄 Synchronisation Oura pour l'utilisateur: {USER_UUID}")
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        sys.exit(1)
    
    # Récupérer le token Oura depuis Supabase
    from oura_token_utils import get_user_oura_token
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    
    # Appel async de get_user_oura_token
    try:
        OURA_TOKEN = asyncio.run(get_user_oura_token(supabase, USER_UUID))
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du token: {e}")
        OURA_TOKEN = None
    
    if not OURA_TOKEN:
        logger.error(f"❌ Aucun token Oura valide trouvé pour l'utilisateur {USER_UUID}")
        logger.error("   Causes possibles:")
        logger.error("   1. L'utilisateur n'a pas encore connecté son compte Oura")
        logger.error("   2. Le token OAuth2 a expiré et n'a pas pu être rafraîchi")
        logger.error(f"   3. Pas de credentials Oura configurées")
        logger.error("")
        logger.error("   Solutions:")
        logger.error(f"   - Via OAuth2: python setup_oura_oauth2.py --user-id {USER_UUID}")
        logger.error(f"   - Via PAT: python register_oura_user.py")
        sys.exit(1)
    
    logger.info(f"✓ Token Oura récupéré pour l'utilisateur {USER_UUID}")
    
    # Créer l'importeur FULL
    importer = OuraDataImporterFull(
        oura_token=OURA_TOKEN,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    # Importer TOUTES les données (mode complet)
    importer.import_all_data(
        user_id=USER_UUID,
        days_back=90
    )


if __name__ == "__main__":
    main()
