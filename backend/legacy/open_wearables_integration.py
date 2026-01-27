"""
Intégration Open Wearables pour récupérer les données des wearables
Supporte : Apple Health, Garmin, Oura, Fitbit, etc. via Open Wearables (auto-hébergé)
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenWearablesIntegration:
    """
    Client pour l'API Open Wearables (auto-hébergé)
    Documentation: https://github.com/open-wearables/open-wearables
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Récupère les informations d'un utilisateur Open Wearables"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users/{user_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user info: {e}")
            return None
    
    def get_sleep_data(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[Dict]:
        """
        Récupère les données de sommeil via l'API Open Wearables
        Retourne: durée, qualité, phases (REM, deep, light)
        """
        try:
            # Open Wearables utilise l'endpoint /api/v1/timeseries pour les données de séries temporelles
            # ou /api/v1/summaries pour les résumés
            response = requests.get(
                f"{self.base_url}/api/v1/timeseries",
                headers=self.headers,
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "series_type": "sleep"
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sleep data: {e}")
            return None
    
    def get_heart_rate_data(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict]:
        """
        Récupère les données de fréquence cardiaque (HR)
        Retourne: HR moyen, HR au repos, HR max
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/timeseries",
                headers=self.headers,
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "series_type": "heart_rate"
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching heart rate data: {e}")
            return None
    
    def get_hrv_data(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict]:
        """
        Récupère les données de Variabilité de la Fréquence Cardiaque (HRV/VFC)
        Retourne: HRV moyen, HRV max, tendances
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/timeseries",
                headers=self.headers,
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "series_type": "hrv"
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HRV data: {e}")
            return None
    
    def get_activity_data(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict]:
        """
        Récupère les données d'activité (pas, distance, calories)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/timeseries",
                headers=self.headers,
                params={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "series_type": "steps"
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching activity data: {e}")
            return None
    
    def get_all_data_for_date(
        self,
        user_id: str,
        target_date: datetime
    ) -> Dict:
        """
        Récupère toutes les données pour une date donnée
        Utilisé pour construire le profil quotidien
        """
        start_date = target_date.replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=1)
        
        return {
            "sleep": self.get_sleep_data(user_id, start_date, end_date),
            "heart_rate": self.get_heart_rate_data(user_id, start_date, end_date),
            "hrv": self.get_hrv_data(user_id, start_date, end_date),
            "activity": self.get_activity_data(user_id, start_date, end_date),
            "date": target_date.isoformat()
        }
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str
    ) -> bool:
        """
        Vérifie la signature du webhook Open Wearables
        Pour sécuriser les webhooks entrants
        Note: Open Wearables peut utiliser une clé API ou un secret partagé
        """
        if not self.api_key:
            # Si pas de clé API configurée, on accepte (pour le développement)
            logger.warning("No API key configured, skipping signature verification")
            return True
        
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.api_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
