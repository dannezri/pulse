"""
Client FatSecret API pour récupérer les données alimentaires
Documentation: https://platform.fatsecret.com/api/Default.aspx?screen=rapiauth

Utilise OAuth 1.0a (3-legged) pour l'authentification utilisateur
"""

import os
import datetime as dt
import logging
from typing import Dict, List, Optional, Any

import requests
from requests_oauthlib import OAuth1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FatSecretClient:
    """Client pour interagir avec l'API FatSecret"""
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        oauth_token: Optional[str] = None,
        oauth_token_secret: Optional[str] = None
    ):
        """
        Initialise le client FatSecret
        
        Args:
            consumer_key: Clé d'application FatSecret
            consumer_secret: Secret d'application FatSecret
            oauth_token: Token OAuth de l'utilisateur (pour requêtes authentifiées)
            oauth_token_secret: Secret OAuth de l'utilisateur
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        
        # URLs de l'API
        self.auth_base_url = "https://authentication.fatsecret.com/oauth"
        self.api_base_url = "https://platform.fatsecret.com/rest"
    
    def _get_auth(self, token: Optional[str] = None, token_secret: Optional[str] = None) -> OAuth1:
        """
        Crée l'objet OAuth1 pour les requêtes
        
        Args:
            token: Token OAuth à utiliser (défaut: self.oauth_token)
            token_secret: Secret OAuth à utiliser (défaut: self.oauth_token_secret)
        
        Returns:
            OAuth1: Objet d'authentification
        """
        return OAuth1(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=token or self.oauth_token,
            resource_owner_secret=token_secret or self.oauth_token_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header"  # OAuth header standard
        )
    
    # =====================================================
    # OAuth Flow - Obtention des tokens utilisateur
    # =====================================================
    
    def get_request_token(self, callback_url: str = "oob") -> Dict[str, str]:
        """
        Étape 1: Obtient un request token pour démarrer le flow OAuth
        
        Args:
            callback_url: URL de callback (utiliser "oob" pour out-of-band)
        
        Returns:
            Dict contenant oauth_token et oauth_token_secret
        """
        try:
            # Vérifier que les credentials sont présents
            if not self.consumer_key or not self.consumer_secret:
                raise ValueError("Consumer key and secret are required")
            
            logger.info(f"Requesting token with consumer_key: {self.consumer_key[:10]}...")
            
            auth = OAuth1(
                client_key=self.consumer_key,
                client_secret=self.consumer_secret,
                callback_uri=callback_url,
                signature_method="HMAC-SHA1",
                signature_type="auth_header"  # OAuth header standard
            )
            
            url = f"{self.auth_base_url}/request_token"
            logger.info(f"POST {url}")
            
            response = requests.post(url, auth=auth, timeout=30)
            
            # Logger la réponse complète pour debug
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}")
            
            response.raise_for_status()
            
            # Parse la réponse (format: oauth_token=xxx&oauth_token_secret=yyy)
            tokens = dict(param.split('=') for param in response.text.split('&'))
            
            logger.info("Request token obtained successfully")
            return tokens
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error getting request token: {e}")
            logger.error(f"Response body: {e.response.text if e.response else 'N/A'}")
            raise
        except Exception as e:
            logger.error(f"Error getting request token: {e}")
            raise
    
    def get_authorization_url(self, request_token: str) -> str:
        """
        Étape 2: Génère l'URL d'autorisation pour l'utilisateur
        
        Args:
            request_token: Token obtenu via get_request_token()
        
        Returns:
            URL d'autorisation
        """
        return f"{self.auth_base_url}/authorize?oauth_token={request_token}"
    
    def get_access_token(self, request_token: str, request_token_secret: str, verifier: str) -> Dict[str, str]:
        """
        Étape 3: Échange le request token contre un access token
        
        Args:
            request_token: Token de requête
            request_token_secret: Secret du token de requête
            verifier: Code de vérification obtenu après autorisation
        
        Returns:
            Dict contenant oauth_token et oauth_token_secret (access tokens finaux)
        """
        try:
            auth = OAuth1(
                client_key=self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=request_token,
                resource_owner_secret=request_token_secret,
                verifier=verifier,
                signature_method="HMAC-SHA1",
                signature_type="auth_header"  # OAuth header standard
            )
            
            url = f"{self.auth_base_url}/access_token"
            response = requests.post(url, auth=auth, timeout=30)
            response.raise_for_status()
            
            # Parse la réponse
            tokens = dict(param.split('=') for param in response.text.split('&'))
            
            # Mettre à jour les tokens de l'instance
            self.oauth_token = tokens.get("oauth_token")
            self.oauth_token_secret = tokens.get("oauth_token_secret")
            
            logger.info("Access token obtained successfully")
            return tokens
            
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    # =====================================================
    # API - Récupération des données alimentaires
    # =====================================================
    
    @staticmethod
    def date_to_days_since_epoch(date: dt.date) -> int:
        """
        Convertit une date en nombre de jours depuis le 1er janvier 1970
        (Format requis par l'API FatSecret)
        
        Args:
            date: Date à convertir
        
        Returns:
            Nombre de jours depuis l'epoch
        """
        epoch = dt.date(1970, 1, 1)
        return (date - epoch).days
    
    @staticmethod
    def days_since_epoch_to_date(days: int) -> dt.date:
        """
        Convertit un nombre de jours depuis l'epoch en date
        
        Args:
            days: Nombre de jours depuis l'epoch
        
        Returns:
            Date correspondante
        """
        epoch = dt.date(1970, 1, 1)
        return epoch + dt.timedelta(days=days)
    
    def get_food_entries_for_date(self, date: dt.date) -> Dict[str, Any]:
        """
        Récupère toutes les entrées alimentaires pour une date donnée
        
        Args:
            date: Date pour laquelle récupérer les entrées
        
        Returns:
            Réponse JSON de l'API contenant les entrées
        """
        try:
            if not self.oauth_token or not self.oauth_token_secret:
                raise ValueError("OAuth tokens required for user data access")
            
            auth = self._get_auth()
            url = f"{self.api_base_url}/food-entries/v1"
            
            params = {
                "date": self.date_to_days_since_epoch(date),
                "format": "json"
            }
            
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved food entries for {date}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting food entries for {date}: {e}")
            return {}
    
    def get_food_entries_for_month(self, year: int, month: int) -> Dict[str, Any]:
        """
        Récupère toutes les entrées alimentaires pour un mois donné
        (Plus efficace pour les synchronisations initiales)
        
        Args:
            year: Année (ex: 2026)
            month: Mois (1-12)
        
        Returns:
            Réponse JSON de l'API contenant les entrées
        """
        try:
            if not self.oauth_token or not self.oauth_token_secret:
                raise ValueError("OAuth tokens required for user data access")
            
            auth = self._get_auth()
            url = f"{self.api_base_url}/food-entries-month/v1"
            
            # Format YYYYMM
            date_param = f"{year}{month:02d}"
            
            params = {
                "date": date_param,
                "format": "json"
            }
            
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved food entries for {year}-{month:02d}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting food entries for {year}-{month}: {e}")
            return {}
    
    def parse_food_entries(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse la réponse de l'API et extrait les entrées alimentaires
        
        Args:
            payload: Réponse JSON de l'API
        
        Returns:
            Liste des entrées alimentaires
        """
        # Structure typique: {"food_entries": {"food_entry": [...]}}
        # ou {"food_entries": {"food_entry": {...}}} si une seule entrée
        
        if not payload or "food_entries" not in payload:
            return []
        
        food_entries = payload.get("food_entries", {})
        
        if not food_entries or "food_entry" not in food_entries:
            return []
        
        entries = food_entries["food_entry"]
        
        # Si une seule entrée, elle n'est pas dans une liste
        if isinstance(entries, dict):
            return [entries]
        elif isinstance(entries, list):
            return entries
        
        return []
    
    def get_food_item(self, food_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un aliment spécifique
        
        Args:
            food_id: ID de l'aliment FatSecret
        
        Returns:
            Détails de l'aliment
        """
        try:
            if not self.oauth_token or not self.oauth_token_secret:
                raise ValueError("OAuth tokens required")
            
            auth = self._get_auth()
            url = f"{self.api_base_url}/food/v4"
            
            params = {
                "food_id": food_id,
                "format": "json"
            }
            
            response = requests.get(url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting food item {food_id}: {e}")
            return None


def get_fatsecret_client(
    consumer_key: Optional[str] = None,
    consumer_secret: Optional[str] = None,
    oauth_token: Optional[str] = None,
    oauth_token_secret: Optional[str] = None
) -> FatSecretClient:
    """
    Crée une instance du client FatSecret avec les credentials fournis ou depuis les variables d'environnement
    
    Args:
        consumer_key: Clé consumer FatSecret (optionnel)
        consumer_secret: Secret consumer FatSecret (optionnel)
        oauth_token: Token OAuth utilisateur (optionnel)
        oauth_token_secret: Secret OAuth utilisateur (optionnel)
    
    Returns:
        FatSecretClient configuré
    """
    consumer_key = consumer_key or os.getenv("FATSECRET_CONSUMER_KEY")
    consumer_secret = consumer_secret or os.getenv("FATSECRET_CONSUMER_SECRET")
    
    if not consumer_key or not consumer_secret:
        raise ValueError("FATSECRET_CONSUMER_KEY and FATSECRET_CONSUMER_SECRET are required")
    
    return FatSecretClient(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        oauth_token=oauth_token,
        oauth_token_secret=oauth_token_secret
    )
