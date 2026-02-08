"""
Service principal : Orchestre l'intégration Open Wearables et la normalisation
Peut être utilisé comme script standalone ou importé dans une API
"""

import os
import sys
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legacy.open_wearables_integration import OpenWearablesIntegration
from legacy.data_normalizer import DataNormalizer
from supabase_client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Pipeline principal qui orchestre :
    1. Récupération des données Open Wearables
    2. Normalisation
    3. Calcul des baselines
    4. Création du profil de santé
    5. Sauvegarde dans Supabase
    """
    
    def __init__(
        self,
        open_wearables_base_url: str,
        supabase_url: str,
        supabase_key: str,
        open_wearables_api_key: Optional[str] = None
    ):
        self.open_wearables = OpenWearablesIntegration(open_wearables_base_url, open_wearables_api_key)
        self.normalizer = DataNormalizer()
        self.supabase = SupabaseClient(supabase_url, supabase_key)
    
    def sync_user_data(
        self,
        open_wearables_user_id: str,
        target_date: Optional[datetime] = None
    ) -> Dict:
        """
        Synchronise les données d'un utilisateur pour une date donnée
        (ou aujourd'hui si non spécifiée)
        """
        if target_date is None:
            target_date = datetime.now()
        
        # 1. Récupérer le user_id Supabase
        supabase_user_id = self.supabase.get_user_by_open_wearables_id(open_wearables_user_id)
        if not supabase_user_id:
            logger.error(f"User not found for Open Wearables ID: {open_wearables_user_id}")
            return {"status": "error", "message": "User not found"}
        
        # 2. Récupérer toutes les données Open Wearables pour la date
        logger.info(f"Fetching Open Wearables data for {open_wearables_user_id} on {target_date.date()}")
        raw_data = self.open_wearables.get_all_data_for_date(open_wearables_user_id, target_date)
        
        # 3. Normaliser les données
        logger.info("Normalizing data...")
        normalized_data = self.normalizer.normalize_open_wearables_data(raw_data)
        
        # 4. Sauvegarder les données brutes dans Supabase (avec idempotence)
        # Générer un ID unique pour cette synchronisation
        sync_id = f"sync_{open_wearables_user_id}_{target_date.date().isoformat()}_{hashlib.md5(json.dumps(raw_data, sort_keys=True).encode()).hexdigest()[:8]}"
        self._save_raw_biometrics(supabase_user_id, raw_data, sync_id)
        
        # 5. Récupérer les données historiques pour calculer les baselines
        logger.info("Calculating baselines...")
        historical_data = self.supabase.get_historical_biometrics(supabase_user_id, days=7)
        
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
        
        # 6. Mettre à jour les baselines dans le profil si nécessaire
        if baseline_data["hrv_baseline"] or baseline_data["hr_baseline"]:
            self.supabase.update_baselines(
                supabase_user_id,
                int(baseline_data["hrv_baseline"]) if baseline_data["hrv_baseline"] else None,
                int(baseline_data["hr_baseline"]) if baseline_data["hr_baseline"] else None
            )
        
        # 7. Créer le profil de santé
        logger.info("Creating health profile...")
        user_goal = self.supabase.get_user_goal(supabase_user_id)
        health_profile = self.normalizer.create_health_profile(
            normalized_data,
            baseline_data,
            user_goal
        )
        
        # 8. Sauvegarder le profil de santé
        self.supabase.save_health_profile(supabase_user_id, health_profile)
        
        logger.info(f"Successfully synced data for user {supabase_user_id}")
        
        return {
            "status": "success",
            "user_id": supabase_user_id,
            "health_profile": health_profile
        }
    
    def _save_raw_biometrics(self, user_id: str, raw_data: Dict, sync_id: Optional[str] = None):
        """
        Sauvegarde les données brutes dans Supabase avec support de l'idempotence.
        sync_id: ID unique de la synchronisation (pour éviter les doublons en cas de rejeu)
        """
        
        # Générer un ID de synchronisation si non fourni
        if sync_id is None:
            sync_id = f"sync_{datetime.now().isoformat()}_{hashlib.md5(json.dumps(raw_data, sort_keys=True).encode()).hexdigest()[:8]}"
        
        # Sauvegarder les données de sommeil
        if "sleep" in raw_data and raw_data["sleep"]:
            sleep_data = raw_data["sleep"]
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
                
                # Générer source_event_id pour l'idempotence
                source_event_id = f"{sync_id}_sleep_{hashlib.md5(json.dumps(sleep_data, sort_keys=True).encode()).hexdigest()[:8]}"
                
                self.supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="sleep_duration",
                    value=duration_minutes,
                    recorded_at=recorded_at,
                    raw_data=sleep_data,
                    source="open_wearables",
                    source_event_id=source_event_id
                )
        
        # Sauvegarder les données HR
        if "heart_rate" in raw_data and raw_data["heart_rate"]:
            hr_data = raw_data["heart_rate"]
            if isinstance(hr_data, list):
                for idx, hr_entry in enumerate(hr_data):
                    hr_value = hr_entry.get("value") or hr_entry.get("hr") or hr_entry.get("heart_rate")
                    if hr_value:
                        timestamp = hr_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{sync_id}_hr_{idx}_{hashlib.md5(json.dumps(hr_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        self.supabase.insert_biometric(
                            user_id=user_id,
                            metric_type="hr",
                            value=float(hr_value),
                            recorded_at=recorded_at,
                            raw_data=hr_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )
        elif "hr" in raw_data and raw_data["hr"]:
            hr_data = raw_data["hr"]
            if isinstance(hr_data, list):
                for idx, hr_entry in enumerate(hr_data):
                    hr_value = hr_entry.get("value") or hr_entry.get("hr")
                    if hr_value:
                        timestamp = hr_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{sync_id}_hr_{idx}_{hashlib.md5(json.dumps(hr_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        self.supabase.insert_biometric(
                            user_id=user_id,
                            metric_type="hr",
                            value=float(hr_value),
                            recorded_at=recorded_at,
                            raw_data=hr_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )
        
        # Sauvegarder les données HRV
        if "hrv" in raw_data and raw_data["hrv"]:
            hrv_data = raw_data["hrv"]
            if isinstance(hrv_data, list):
                for idx, hrv_entry in enumerate(hrv_data):
                    hrv_value = hrv_entry.get("value") or hrv_entry.get("hrv")
                    if hrv_value:
                        timestamp = hrv_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{sync_id}_hrv_{idx}_{hashlib.md5(json.dumps(hrv_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        self.supabase.insert_biometric(
                            user_id=user_id,
                            metric_type="hrv",
                            value=float(hrv_value),
                            recorded_at=recorded_at,
                            raw_data=hrv_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )
        
        # Sauvegarder les données d'activité
        if "activity" in raw_data and raw_data["activity"]:
            activity_data = raw_data["activity"]
            if isinstance(activity_data, dict) and "steps" in activity_data:
                timestamp = activity_data.get("timestamp", datetime.now().isoformat())
                try:
                    recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    recorded_at = datetime.now()
                
                source_event_id = f"{sync_id}_steps_{hashlib.md5(json.dumps(activity_data, sort_keys=True).encode()).hexdigest()[:8]}"
                
                self.supabase.insert_biometric(
                    user_id=user_id,
                    metric_type="steps",
                    value=float(activity_data["steps"]),
                    recorded_at=recorded_at,
                    raw_data=activity_data,
                    source="open_wearables",
                    source_event_id=source_event_id
                )
        elif "steps" in raw_data and raw_data["steps"]:
            steps_data = raw_data["steps"]
            if isinstance(steps_data, list):
                for idx, step_entry in enumerate(steps_data):
                    steps_value = step_entry.get("value") or step_entry.get("steps")
                    if steps_value:
                        timestamp = step_entry.get("timestamp", datetime.now().isoformat())
                        try:
                            recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except:
                            recorded_at = datetime.now()
                        
                        source_event_id = f"{sync_id}_steps_{idx}_{hashlib.md5(json.dumps(step_entry, sort_keys=True).encode()).hexdigest()[:8]}"
                        
                        self.supabase.insert_biometric(
                            user_id=user_id,
                            metric_type="steps",
                            value=float(steps_value),
                            recorded_at=recorded_at,
                            raw_data=step_entry,
                            source="open_wearables",
                            source_event_id=source_event_id
                        )


def main():
    """Point d'entrée pour exécuter le pipeline manuellement"""
    # Charger les variables d'environnement
    open_wearables_base_url = os.getenv("OPEN_WEARABLES_BASE_URL", "http://localhost:8080")
    open_wearables_api_key = os.getenv("OPEN_WEARABLES_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        logger.error("Missing required environment variables (SUPABASE_URL, SUPABASE_SERVICE_KEY)")
        return
    
    # Créer le pipeline
    pipeline = DataPipeline(
        open_wearables_base_url=open_wearables_base_url,
        open_wearables_api_key=open_wearables_api_key,
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
    
    # Exemple : synchroniser les données pour un utilisateur
    open_wearables_user_id = os.getenv("OPEN_WEARABLES_USER_ID")
    if open_wearables_user_id:
        result = pipeline.sync_user_data(open_wearables_user_id)
        logger.info(f"Sync result: {result}")
    else:
        logger.warning("OPEN_WEARABLES_USER_ID not set, skipping sync")


if __name__ == "__main__":
    main()
