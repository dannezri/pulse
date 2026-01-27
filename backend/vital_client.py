"""
Client Vital API pour la gestion des utilisateurs et connexions
Documentation: https://docs.tryvital.io/
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VitalClient:
    """Client pour interagir avec l'API Vital"""
    
    def __init__(self, api_key: str, region: str = "us", environment: str = "sandbox"):
        """
        Initialise le client Vital
        
        Args:
            api_key: Clé API Vital
            region: Région (us ou eu)
            environment: Environment (sandbox ou production)
        """
        self.api_key = api_key
        self.region = region
        self.environment = environment
        
        # Base URL selon l'environnement et la région
        if environment == "sandbox":
            self.base_url = f"https://api.sandbox.tryvital.io"
        else:
            self.base_url = f"https://api.tryvital.io"
        
        self.headers = {
            "x-vital-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_user(self, client_user_id: str) -> Dict:
        """
        Crée un utilisateur Vital
        
        Args:
            client_user_id: ID unique de l'utilisateur côté client (Supabase UUID)
        
        Returns:
            Dict avec user_id, client_user_id, created_at
        """
        try:
            url = f"{self.base_url}/v2/user"
            payload = {
                "client_user_id": client_user_id
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Vital user created: {data.get('user_id')} for client_user_id: {client_user_id}")
            
            return {
                "user_id": data.get("user_id"),
                "client_user_id": data.get("client_user_id"),
                "created_at": data.get("created_at")
            }
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # Utilisateur existe déjà
                logger.warning(f"Vital user already exists for client_user_id: {client_user_id}")
                # Récupérer l'utilisateur existant
                return self.get_user_by_client_id(client_user_id)
            else:
                logger.error(f"Error creating Vital user: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error creating Vital user: {e}")
            raise
    
    def get_user_by_client_id(self, client_user_id: str) -> Optional[Dict]:
        """
        Récupère un utilisateur Vital par son client_user_id
        
        Args:
            client_user_id: ID unique de l'utilisateur côté client
        
        Returns:
            Dict avec user_id, client_user_id ou None si non trouvé
        """
        try:
            url = f"{self.base_url}/v2/user/resolve/{client_user_id}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return {
                "user_id": data.get("user_id"),
                "client_user_id": data.get("client_user_id")
            }
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Vital user not found for client_user_id: {client_user_id}")
                return None
            else:
                logger.error(f"Error getting Vital user: {e}")
                raise
        
        except Exception as e:
            logger.error(f"Error getting Vital user: {e}")
            raise
    
    def generate_link_token(self, user_id: str) -> Dict:
        """
        Génère un token Vital Link pour connecter des sources
        
        Args:
            user_id: ID utilisateur Vital
        
        Returns:
            Dict avec link_token, expires_at
        """
        try:
            url = f"{self.base_url}/v2/link/token"
            payload = {
                "user_id": user_id
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Link token generated for user_id: {user_id}")
            
            return {
                "link_token": data.get("link_token"),
                "expires_at": data.get("expires_at")
            }
        
        except Exception as e:
            logger.error(f"Error generating link token: {e}")
            raise
    
    def get_user_connections(self, user_id: str) -> List[Dict]:
        """
        Liste les sources connectées pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
        
        Returns:
            Liste de Dict avec provider name, status, created_at, etc.
        """
        try:
            url = f"{self.base_url}/v2/user/providers/{user_id}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            providers = data.get("providers", [])
            
            logger.info(f"Retrieved {len(providers)} connections for user_id: {user_id}")
            
            # Formatter les données
            connections = []
            for provider in providers:
                connections.append({
                    "name": provider.get("name"),
                    "slug": provider.get("slug"),
                    "status": provider.get("status"),
                    "created_at": provider.get("created_at"),
                    "last_sync_at": provider.get("last_sync_at")
                })
            
            return connections
        
        except Exception as e:
            logger.error(f"Error getting user connections: {e}")
            raise
    
    def deregister_provider(self, user_id: str, provider_slug: str) -> bool:
        """
        Déconnecte une source pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            provider_slug: Slug du provider (ex: "apple_health", "fitbit")
        
        Returns:
            True si succès
        """
        try:
            url = f"{self.base_url}/v2/user/{user_id}/{provider_slug}"
            
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"Provider {provider_slug} deregistered for user_id: {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deregistering provider: {e}")
            raise
    
    def get_available_providers(self) -> List[Dict]:
        """
        Liste tous les providers disponibles
        
        Returns:
            Liste de Dict avec name, slug, logo, etc.
        """
        try:
            url = f"{self.base_url}/v2/providers"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            providers = data.get("providers", [])
            
            logger.info(f"Retrieved {len(providers)} available providers")
            
            return providers
        
        except Exception as e:
            logger.error(f"Error getting available providers: {e}")
            raise
    
    def connect_demo_provider(self, user_id: str, provider_slug: str) -> Dict:
        """
        Connecte un provider en mode demo/sandbox (sans OAuth)
        
        Uniquement disponible en sandbox. Génère des données de test.
        
        Args:
            user_id: ID utilisateur Vital
            provider_slug: Slug du provider (ex: "apple_health", "fitbit")
        
        Returns:
            Dict avec les détails de la connexion
        """
        if self.environment != "sandbox":
            raise ValueError("Demo connections are only available in sandbox environment")
        
        try:
            url = f"{self.base_url}/v2/link/connect/demo"
            payload = {
                "user_id": user_id,
                "provider": provider_slug
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Demo provider {provider_slug} connected for user_id: {user_id}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error connecting demo provider: {e}")
            raise
    
    def get_sleep_data(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Récupère les données de sommeil pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
        
        Returns:
            Liste des sessions de sommeil
        """
        try:
            url = f"{self.base_url}/v2/summary/sleep/{user_id}"
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            sleep_data = data.get("sleep", [])
            
            logger.info(f"Retrieved {len(sleep_data)} sleep records for user {user_id}")
            return sleep_data
        
        except Exception as e:
            logger.error(f"Error getting sleep data: {e}")
            return []
    
    def get_activity_data(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Récupère les données d'activité pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
        
        Returns:
            Liste des données d'activité quotidiennes
        """
        try:
            url = f"{self.base_url}/v2/summary/activity/{user_id}"
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            activity_data = data.get("activity", [])
            
            logger.info(f"Retrieved {len(activity_data)} activity records for user {user_id}")
            return activity_data
        
        except Exception as e:
            logger.error(f"Error getting activity data: {e}")
            return []
    
    def get_body_data(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Récupère les données corporelles pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
        
        Returns:
            Liste des mesures corporelles
        """
        try:
            url = f"{self.base_url}/v2/summary/body/{user_id}"
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            body_data = data.get("body", [])
            
            logger.info(f"Retrieved {len(body_data)} body records for user {user_id}")
            return body_data
        
        except Exception as e:
            logger.error(f"Error getting body data: {e}")
            return []
    
    def get_workouts_data(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Récupère les données d'entraînement pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
        
        Returns:
            Liste des entraînements
        """
        try:
            url = f"{self.base_url}/v2/summary/workouts/{user_id}"
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            workouts_data = data.get("workouts", [])
            
            logger.info(f"Retrieved {len(workouts_data)} workout records for user {user_id}")
            return workouts_data
        
        except Exception as e:
            logger.error(f"Error getting workouts data: {e}")
            return []
    
    def get_vitals_data(self, user_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Récupère les données vitales (HRV, HR, SpO2, etc.) pour un utilisateur
        
        Args:
            user_id: ID utilisateur Vital
            start_date: Date de début (ISO 8601)
            end_date: Date de fin (ISO 8601)
        
        Returns:
            Liste des mesures vitales
        """
        try:
            url = f"{self.base_url}/v2/summary/vitals/{user_id}"
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            vitals_data = data.get("vitals", [])
            
            logger.info(f"Retrieved {len(vitals_data)} vitals records for user {user_id}")
            return vitals_data
        
        except Exception as e:
            logger.error(f"Error getting vitals data: {e}")
            return []


def get_vital_client() -> VitalClient:
    """
    Crée une instance du client Vital avec les variables d'environnement
    
    Returns:
        VitalClient configuré
    """
    api_key = os.getenv("VITAL_API_KEY")
    region = os.getenv("VITAL_REGION", "us")
    environment = os.getenv("VITAL_ENVIRONMENT", "sandbox")
    
    if not api_key:
        raise ValueError("VITAL_API_KEY environment variable is required")
    
    return VitalClient(api_key=api_key, region=region, environment=environment)
