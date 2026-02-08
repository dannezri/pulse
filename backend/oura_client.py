"""
Client Oura API pour récupérer les données de santé
Documentation: https://cloud.ouraring.com/v2/docs
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OuraClient:
    """Client pour interagir avec l'API Oura Ring v2"""
    
    def __init__(self, access_token: str):
        """
        Initialise le client Oura
        
        Args:
            access_token: Token d'accès personnel Oura
        """
        self.access_token = access_token
        self.base_url = "https://api.ouraring.com/v2/usercollection"
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_personal_info(self) -> Optional[Dict]:
        """
        Récupère les informations personnelles de l'utilisateur
        
        Returns:
            Dict avec age, weight, height, biological_sex, email
        """
        try:
            url = f"{self.base_url}/personal_info"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved personal info for user: {data.get('email', 'N/A')}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error getting personal info: {e}")
            return None
    
    def get_daily_sleep(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données de sommeil quotidiennes
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des sessions de sommeil
        """
        try:
            url = f"{self.base_url}/daily_sleep"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            sleep_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(sleep_data)} daily sleep records")
            return sleep_data
        
        except Exception as e:
            logger.error(f"Error getting daily sleep data: {e}")
            return []
    
    def get_sleep_sessions(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les sessions de sommeil détaillées (contient HRV, heart rate, etc.)
        
        Utilise l'endpoint /sleep directement avec start_date/end_date
        (L'approche /sleep/{id} ne fonctionne pas avec les IDs de /daily_sleep)
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des sessions de sommeil avec données détaillées (incluant HRV)
        """
        try:
            url = f"{self.base_url}/sleep"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            sleep_sessions = data.get("data", [])
            
            logger.info(f"Retrieved {len(sleep_sessions)} detailed sleep sessions from /sleep endpoint")
            return sleep_sessions
        
        except Exception as e:
            logger.error(f"Error getting detailed sleep sessions: {e}")
            return []
    
    def get_daily_activity(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données d'activité quotidiennes
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des données d'activité
        """
        try:
            url = f"{self.base_url}/daily_activity"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            activity_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(activity_data)} daily activity records")
            return activity_data
        
        except Exception as e:
            logger.error(f"Error getting daily activity data: {e}")
            return []
    
    def get_daily_readiness(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données de préparation quotidiennes (readiness)
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des données de readiness
        """
        try:
            url = f"{self.base_url}/daily_readiness"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            readiness_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(readiness_data)} daily readiness records")
            return readiness_data
        
        except Exception as e:
            logger.error(f"Error getting daily readiness data: {e}")
            return []
    
    def get_heart_rate(self, start_datetime: str, end_datetime: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données de fréquence cardiaque
        L'API Oura limite les requêtes de heart rate à 1 jour maximum
        
        Args:
            start_datetime: Date/heure de début (ISO 8601)
            end_datetime: Date/heure de fin (ISO 8601), optionnel
        
        Returns:
            Liste des mesures de fréquence cardiaque
        """
        try:
            # L'API Oura limite les requêtes heart rate à 1 jour
            # Si la période est plus longue, on récupère seulement le dernier jour
            if start_datetime and end_datetime:
                start = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))
                
                # Si la période est > 1 jour, limiter au dernier jour
                if (end - start).days > 1:
                    logger.warning(f"Heart rate API limited to 1 day, fetching only the last day")
                    start_datetime = (end - timedelta(days=1)).isoformat().replace("+00:00", "Z")
            
            url = f"{self.base_url}/heartrate"
            params = {"start_datetime": start_datetime}
            if end_datetime:
                params["end_datetime"] = end_datetime
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            hr_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(hr_data)} heart rate records")
            return hr_data
        
        except Exception as e:
            logger.error(f"Error getting heart rate data: {e}")
            return []
    
    def get_daily_spo2(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données de saturation en oxygène (SpO2)
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des mesures SpO2
        """
        try:
            url = f"{self.base_url}/daily_spo2"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            spo2_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(spo2_data)} daily SpO2 records")
            return spo2_data
        
        except Exception as e:
            logger.error(f"Error getting daily SpO2 data: {e}")
            return []
    
    def get_sessions(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les sessions (moments de relaxation, méditation, etc.)
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des sessions
        """
        try:
            url = f"{self.base_url}/session"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            sessions_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(sessions_data)} session records")
            return sessions_data
        
        except Exception as e:
            logger.error(f"Error getting sessions data: {e}")
            return []
    
    def get_workouts(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les entraînements
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des entraînements
        """
        try:
            url = f"{self.base_url}/workout"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            workouts_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(workouts_data)} workout records")
            return workouts_data
        
        except Exception as e:
            logger.error(f"Error getting workouts data: {e}")
            return []
    
    def get_sleep_time(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les données de temps de sommeil (granularité fine)
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des périodes de sommeil
        """
        try:
            url = f"{self.base_url}/sleep_time"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            sleep_time_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(sleep_time_data)} sleep time records")
            return sleep_time_data
        
        except Exception as e:
            logger.error(f"Error getting sleep time data: {e}")
            return []
    
    def get_rest_mode_period(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Récupère les périodes de mode repos
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel
        
        Returns:
            Liste des périodes de mode repos
        """
        try:
            url = f"{self.base_url}/rest_mode_period"
            params = {"start_date": start_date}
            if end_date:
                params["end_date"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            rest_mode_data = data.get("data", [])
            
            logger.info(f"Retrieved {len(rest_mode_data)} rest mode period records")
            return rest_mode_data
        
        except Exception as e:
            logger.error(f"Error getting rest mode period data: {e}")
            return []
    
    def get_all_data(self, start_date: str, end_date: Optional[str] = None, days_back: int = 30) -> Dict:
        """
        Récupère toutes les données disponibles pour une période
        
        Args:
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD), optionnel (défaut: aujourd'hui)
            days_back: Nombre de jours à récupérer si start_date n'est pas fourni
        
        Returns:
            Dict contenant toutes les données par type
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Pour les endpoints qui utilisent datetime au lieu de date
        start_datetime = f"{start_date}T00:00:00Z"
        end_datetime = f"{end_date}T23:59:59Z"
        
        logger.info(f"Fetching all Oura data from {start_date} to {end_date}")
        
        return {
            "personal_info": self.get_personal_info(),
            "daily_sleep": self.get_daily_sleep(start_date, end_date),
            "daily_activity": self.get_daily_activity(start_date, end_date),
            "daily_readiness": self.get_daily_readiness(start_date, end_date),
            "daily_spo2": self.get_daily_spo2(start_date, end_date),
            "heart_rate": self.get_heart_rate(start_datetime, end_datetime),
            "sessions": self.get_sessions(start_date, end_date),
            "workouts": self.get_workouts(start_date, end_date),
            "sleep_time": self.get_sleep_time(start_date, end_date),
            "rest_mode_period": self.get_rest_mode_period(start_date, end_date)
        }


def get_oura_client(access_token: Optional[str] = None) -> OuraClient:
    """
    Crée une instance du client Oura avec le token fourni ou depuis les variables d'environnement
    
    Args:
        access_token: Token d'accès Oura (optionnel, utilise OURA_ACCESS_TOKEN si non fourni)
    
    Returns:
        OuraClient configuré
    """
    if not access_token:
        access_token = os.getenv("OURA_ACCESS_TOKEN")
    
    if not access_token:
        raise ValueError("OURA_ACCESS_TOKEN is required")
    
    return OuraClient(access_token=access_token)
