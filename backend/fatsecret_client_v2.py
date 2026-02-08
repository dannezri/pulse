"""
Client FatSecret API (basé sur la documentation officielle)
Documentation: https://platform.fatsecret.com/docs/guides/authentication

Deux modes d'authentification :
1. OAuth 2.0 Client Credentials - Pour requêtes générales (foods.search, food.get)
2. OAuth 1.0a Profile-based - Pour requêtes utilisateur (food_entries, weights)
"""

import os
import time
import hashlib
import hmac
import base64
import urllib.parse
import requests
import logging
from typing import Dict, List, Optional, Any
import datetime as dt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FatSecretClient:
    """Client pour interagir avec l'API FatSecret"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        oauth_token: Optional[str] = None,
        oauth_secret: Optional[str] = None
    ):
        """
        Initialise le client FatSecret
        
        Args:
            client_id: Client ID (Consumer Key) FatSecret
            client_secret: Client Secret (Shared Secret) FatSecret
            oauth_token: Token OAuth du profil utilisateur (optionnel)
            oauth_secret: Secret OAuth du profil utilisateur (optionnel)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_token = oauth_token
        self.oauth_secret = oauth_secret
        
        # URLs de l'API
        self.api_url = "https://platform.fatsecret.com/rest/server.api"
        self.oauth2_token_url = "https://oauth.fatsecret.com/connect/token"
        
        self._access_token = None
        self._token_expires_at = 0
    
    # =====================================================
    # OAuth 2.0 - Pour requêtes générales (non-utilisateur)
    # =====================================================
    
    def get_oauth2_token(self) -> str:
        """
        Obtient un access token OAuth 2.0 (Client Credentials)
        Cache le token jusqu'à expiration
        
        Returns:
            Access token Bearer
        """
        # Vérifier si on a un token valide en cache
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        try:
            # Créer les credentials en Base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "basic"
            }
            
            response = requests.post(
                self.oauth2_token_url,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._token_expires_at = time.time() + token_data.get("expires_in", 86400) - 60  # -60s de marge
            
            logger.info("OAuth 2.0 token obtained successfully")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Error getting OAuth 2.0 token: {e}")
            raise
    
    # =====================================================
    # OAuth 1.0a - Signature pour requêtes utilisateur
    # =====================================================
    
    def _generate_oauth1_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str]
    ) -> str:
        """
        Génère une signature OAuth 1.0a HMAC-SHA1
        Documentation: https://platform.fatsecret.com/docs/guides/authentication/oauth1
        
        Args:
            method: HTTP method (GET ou POST)
            url: URL complète de la requête
            params: Paramètres de la requête (incluant les params OAuth)
        
        Returns:
            Signature base64 encodée
        """
        # 1. Trier les paramètres
        sorted_params = sorted(params.items())
        
        # 2. Créer la chaîne de paramètres (percent-encoded)
        param_string = "&".join([
            f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_params
        ])
        
        # 3. Créer la base string
        base_string = "&".join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # 4. Créer la signing key
        # key = consumer_secret&oauth_secret (show '&' even if oauth_secret is empty)
        signing_key = "&".join([
            urllib.parse.quote(self.client_secret, safe=''),
            urllib.parse.quote(self.oauth_secret or '', safe='')
        ])
        
        # 5. Calculer la signature HMAC-SHA1
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode(),
                base_string.encode(),
                hashlib.sha1
            ).digest()
        ).decode()
        
        return signature
    
    def _make_oauth1_request(
        self,
        params: Dict[str, str],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Fait une requête signée OAuth 1.0a
        
        Args:
            params: Paramètres de l'API (method, format, etc.)
            method: HTTP method (GET ou POST)
        
        Returns:
            Réponse JSON de l'API
        """
        # Paramètres OAuth requis
        oauth_params = {
            "oauth_consumer_key": self.client_id,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(int(time.time() * 1000000)),
            "oauth_version": "1.0"
        }
        
        # Ajouter oauth_token si on en a un (pour requêtes utilisateur)
        if self.oauth_token:
            oauth_params["oauth_token"] = self.oauth_token
        
        # Combiner tous les paramètres pour la signature
        all_params = {**params, **oauth_params}
        
        # Générer la signature
        signature = self._generate_oauth1_signature(method, self.api_url, all_params)
        oauth_params["oauth_signature"] = signature
        
        # Faire la requête
        if method.upper() == "GET":
            final_params = {**params, **oauth_params}
            response = requests.get(self.api_url, params=final_params, timeout=30)
        else:  # POST
            final_params = {**params, **oauth_params}
            response = requests.post(
                self.api_url,
                data=final_params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
        
        response.raise_for_status()
        return response.json()
    
    # =====================================================
    # Profile Management - Créer/Gérer des profils utilisateur
    # =====================================================
    
    def create_profile(self, user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Crée un profil FatSecret VIDE pour un utilisateur
        Utilisez cette méthode si vous voulez que l'utilisateur enregistre ses données via votre app
        
        Documentation: https://platform.fatsecret.com/api/Default.aspx?screen=rapiref2&method=profile.create
        
        Args:
            user_id: Identifiant unique de votre utilisateur (optionnel)
        
        Returns:
            Dict contenant auth_token et auth_secret
        """
        params = {
            "method": "profile.create",
            "format": "json"
        }
        
        if user_id:
            params["user_id"] = user_id
        
        result = self._make_oauth1_request(params)
        
        # Extraire les tokens du profil
        profile = result.get("profile", {})
        auth_token = profile.get("auth_token")
        auth_secret = profile.get("auth_secret")
        
        logger.info(f"Profile created: {auth_token[:20]}...")
        
        return {
            "auth_token": auth_token,
            "auth_secret": auth_secret
        }
    
    # =====================================================
    # OAuth Flow - Pour connecter un compte FatSecret existant
    # Utilise les endpoints /oauth/* traditionnels (pas server.api)
    # =====================================================
    
    def request_token(self, callback_url: str = "oob") -> Dict[str, str]:
        """
        Étape 1: Obtient un request token pour démarrer le flow OAuth
        Utilise l'endpoint /oauth/request_token (pas server.api)
        
        Args:
            callback_url: URL de callback ("oob" pour out-of-band)
        
        Returns:
            Dict contenant request_token et request_secret
        """
        url = "https://www.fatsecret.com/oauth/request_token"
        method = "POST"
        
        # Paramètres OAuth pour request_token
        oauth_params = {
            "oauth_consumer_key": self.client_id,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(int(time.time() * 1000000)),
            "oauth_version": "1.0",
            "oauth_callback": callback_url
        }
        
        # Générer la signature
        signature = self._generate_oauth1_signature(method, url, oauth_params)
        oauth_params["oauth_signature"] = signature
        
        # Faire la requête
        response = requests.post(
            url,
            data=oauth_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        response.raise_for_status()
        
        # Parser la réponse (format: oauth_token=xxx&oauth_token_secret=yyy)
        tokens = dict(param.split('=') for param in response.text.split('&'))
        request_token = tokens.get("oauth_token")
        request_secret = tokens.get("oauth_token_secret")
        
        logger.info(f"Request token obtained: {request_token[:20]}...")
        
        return {
            "request_token": request_token,
            "request_secret": request_secret
        }
    
    def get_authorize_url(self, request_token: str) -> str:
        """
        Étape 2: Génère l'URL d'autorisation pour l'utilisateur
        
        Args:
            request_token: Token obtenu via request_token()
        
        Returns:
            URL d'autorisation FatSecret
        """
        return f"https://www.fatsecret.com/oauth/authorize?oauth_token={request_token}"
    
    def get_access_token(self, request_token: str, request_secret: str, verifier: str) -> Dict[str, str]:
        """
        Étape 3: Échange le request token et verifier contre un access token
        Utilise l'endpoint /oauth/access_token (pas server.api)
        
        Args:
            request_token: Token de requête
            request_secret: Secret du token de requête
            verifier: Code de vérification obtenu après autorisation
        
        Returns:
            Dict contenant auth_token et auth_secret (liés au compte utilisateur)
        """
        url = "https://www.fatsecret.com/oauth/access_token"
        method = "POST"
        
        # Paramètres OAuth pour access_token
        oauth_params = {
            "oauth_consumer_key": self.client_id,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(int(time.time() * 1000000)),
            "oauth_version": "1.0",
            "oauth_token": request_token,
            "oauth_verifier": verifier
        }
        
        # Créer un client temporaire pour la signature (avec request_secret)
        temp_client = FatSecretClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            oauth_token=request_token,
            oauth_secret=request_secret
        )
        
        # Générer la signature
        signature = temp_client._generate_oauth1_signature(method, url, oauth_params)
        oauth_params["oauth_signature"] = signature
        
        # Faire la requête
        response = requests.post(
            url,
            data=oauth_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        response.raise_for_status()
        
        # Parser la réponse
        tokens = dict(param.split('=') for param in response.text.split('&'))
        auth_token = tokens.get("oauth_token")
        auth_secret = tokens.get("oauth_token_secret")
        
        logger.info(f"Access token obtained: {auth_token[:20]}...")
        
        # Mettre à jour les credentials de l'instance actuelle
        self.oauth_token = auth_token
        self.oauth_secret = auth_secret
        
        return {
            "auth_token": auth_token,
            "auth_secret": auth_secret
        }
    
    # =====================================================
    # API - Récupération des données alimentaires
    # =====================================================
    
    @staticmethod
    def date_to_int(date: dt.date) -> int:
        """
        Convertit une date en entier (nombre de jours depuis epoch)
        Format requis par FatSecret
        
        Args:
            date: Date à convertir
        
        Returns:
            Nombre de jours depuis le 1er janvier 1970
        """
        epoch = dt.date(1970, 1, 1)
        return (date - epoch).days
    
    def get_food_entries_for_date(self, date: dt.date) -> Dict[str, Any]:
        """
        Récupère les entrées alimentaires pour une date
        Requiert oauth_token et oauth_secret du profil
        
        Args:
            date: Date pour laquelle récupérer les entrées
        
        Returns:
            Réponse JSON de l'API
        """
        if not self.oauth_token or not self.oauth_secret:
            raise ValueError("oauth_token and oauth_secret required for user-specific requests")
        
        params = {
            "method": "food_entries.get",
            "date": str(self.date_to_int(date)),
            "format": "json"
        }
        
        logger.info(f"Fetching food entries for {date}")
        return self._make_oauth1_request(params)
    
    def get_food_entries_for_month(self, year: int, month: int) -> Dict[str, Any]:
        """
        Récupère les entrées alimentaires pour un mois complet
        
        Args:
            year: Année (ex: 2026)
            month: Mois (1-12)
        
        Returns:
            Réponse JSON de l'API
        """
        if not self.oauth_token or not self.oauth_secret:
            raise ValueError("oauth_token and oauth_secret required for user-specific requests")
        
        params = {
            "method": "food_entries.get_month",
            "date": f"{year}{month:02d}",  # Format: YYYYMM
            "format": "json"
        }
        
        logger.info(f"Fetching food entries for {year}-{month:02d}")
        return self._make_oauth1_request(params)
    
    def search_foods(self, query: str, page: int = 0) -> Dict[str, Any]:
        """
        Recherche des aliments (requête générale, pas besoin de profil)
        
        Args:
            query: Terme de recherche
            page: Numéro de page (défaut: 0)
        
        Returns:
            Résultats de la recherche
        """
        params = {
            "method": "foods.search",
            "search_expression": query,
            "page_number": str(page),
            "format": "json"
        }
        
        return self._make_oauth1_request(params, method="GET")
    
    def get_food(self, food_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un aliment spécifique
        
        Args:
            food_id: ID de l'aliment FatSecret
        
        Returns:
            Détails de l'aliment avec informations nutritionnelles
        """
        params = {
            "method": "food.get.v2",
            "food_id": str(food_id),
            "format": "json"
        }
        
        return self._make_oauth1_request(params, method="GET")
    
    def create_food_entry(
        self,
        food_id: int,
        serving_id: int,
        num_servings: float,
        meal: str,
        date: dt.date
    ) -> Dict[str, Any]:
        """
        Crée une entrée alimentaire pour l'utilisateur
        Requiert oauth_token et oauth_secret du profil
        
        Args:
            food_id: ID de l'aliment FatSecret
            serving_id: ID de la portion
            num_servings: Nombre de portions (ex: 1.5)
            meal: Type de repas (breakfast, lunch, dinner, snack, other)
            date: Date de l'entrée
        
        Returns:
            Réponse de l'API (confirmation)
        """
        if not self.oauth_token or not self.oauth_secret:
            raise ValueError("oauth_token and oauth_secret required for user-specific requests")
        
        params = {
            "method": "food_entry.create",
            "food_id": str(food_id),
            "serving_id": str(serving_id),
            "num_servings": str(num_servings),
            "meal": meal,
            "date": str(self.date_to_int(date)),
            "format": "json"
        }
        
        logger.info(f"Creating food entry: {food_id} for {date}, meal: {meal}")
        return self._make_oauth1_request(params)
    
    def delete_food_entry(self, food_entry_id: int) -> Dict[str, Any]:
        """
        Supprime une entrée alimentaire
        Requiert oauth_token et oauth_secret du profil
        
        Args:
            food_entry_id: ID de l'entrée à supprimer
        
        Returns:
            Réponse de l'API
        """
        if not self.oauth_token or not self.oauth_secret:
            raise ValueError("oauth_token and oauth_secret required for user-specific requests")
        
        params = {
            "method": "food_entry.delete",
            "food_entry_id": str(food_entry_id),
            "format": "json"
        }
        
        logger.info(f"Deleting food entry: {food_entry_id}")
        return self._make_oauth1_request(params)
    
    def parse_food_entries(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse les entrées alimentaires depuis la réponse API
        
        Args:
            payload: Réponse JSON de l'API
        
        Returns:
            Liste des entrées alimentaires
        """
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


def get_fatsecret_client(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    oauth_token: Optional[str] = None,
    oauth_secret: Optional[str] = None
) -> FatSecretClient:
    """
    Crée une instance du client FatSecret
    
    Args:
        client_id: Client ID FatSecret (optionnel, utilise env var)
        client_secret: Client Secret FatSecret (optionnel, utilise env var)
        oauth_token: Token du profil utilisateur (optionnel)
        oauth_secret: Secret du profil utilisateur (optionnel)
    
    Returns:
        FatSecretClient configuré
    """
    client_id = client_id or os.getenv("FATSECRET_CONSUMER_KEY")
    client_secret = client_secret or os.getenv("FATSECRET_CONSUMER_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("FATSECRET_CONSUMER_KEY and FATSECRET_CONSUMER_SECRET are required")
    
    return FatSecretClient(
        client_id=client_id,
        client_secret=client_secret,
        oauth_token=oauth_token,
        oauth_secret=oauth_secret
    )
