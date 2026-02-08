"""
Client ICD-11 pour rechercher des codes de pathologies via l'API WHO
Gère l'authentification OAuth2 et le cache des recherches
"""

import os
import logging
import requests
import hashlib
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from consumer_terms import (
    get_consumer_suggestions_for_query,
    filter_and_rank_results,
    score_icd11_result
)

logger = logging.getLogger(__name__)


class ICD11Client:
    """
    Client pour interagir avec l'API ICD-11 de l'OMS (WHO)
    
    Documentation API: https://icd.who.int/icdapi
    
    Fonctionnalités:
    - Authentification OAuth2 (client credentials)
    - Recherche de codes ICD-11 par mot-clé
    - Support multilingue (fr, en)
    - Cache intégré avec Supabase
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialise le client ICD-11
        
        Args:
            supabase_client: Instance de SupabaseClient pour le cache
        """
        self.client_id = os.getenv("ICD11_CLIENT_ID")
        self.client_secret = os.getenv("ICD11_CLIENT_SECRET")
        self.api_base_url = "https://icdaccessmanagement.who.int"
        self.icd_api_url = "https://id.who.int/icd"
        
        self.supabase_client = supabase_client
        
        # Cache du token OAuth2 en mémoire (durée: 1 heure typiquement)
        self._access_token = None
        self._token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning(
                "ICD11_CLIENT_ID ou ICD11_CLIENT_SECRET non configurés. "
                "L'intégration ICD-11 ne fonctionnera pas."
            )
    
    def _get_access_token(self) -> Optional[str]:
        """
        Obtient un token OAuth2 pour l'API ICD-11
        
        Returns:
            Token d'accès ou None si erreur
        """
        # Vérifier si le token en cache est encore valide
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Demander un nouveau token
        try:
            token_url = f"{self.api_base_url}/connect/token"
            
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "icdapi_access",
                "grant_type": "client_credentials"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(token_url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Par défaut 1 heure
                
                # Conserver le token en cache avec une marge de 5 minutes
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                logger.info(f"Token OAuth2 ICD-11 obtenu (expire dans {expires_in}s)")
                return self._access_token
            else:
                logger.error(f"Erreur OAuth2 ICD-11: {response.status_code} - {response.text[:200]}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'obtention du token ICD-11: {e}")
            return None
    
    def _get_cache_key(self, query: str, lang: str) -> str:
        """
        Génère une clé de cache pour une recherche
        
        Args:
            query: Terme de recherche
            lang: Code langue (fr, en)
        
        Returns:
            Clé de cache unique
        """
        normalized_query = query.lower().strip()
        return f"icd11:search:{lang}:{normalized_query}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """
        Récupère les résultats depuis le cache Supabase
        
        Args:
            cache_key: Clé de cache
        
        Returns:
            Résultats cachés ou None si non trouvé/expiré
        """
        if not self.supabase_client:
            return None
        
        try:
            response = self.supabase_client.client.table("terminology_cache").select("*").eq("cache_key", cache_key).execute()
            
            if response.data and len(response.data) > 0:
                cache_entry = response.data[0]
                
                # Vérifier si le cache est encore valide
                expires_at = datetime.fromisoformat(cache_entry["expires_at"].replace("Z", "+00:00"))
                if datetime.now(expires_at.tzinfo) < expires_at:
                    logger.info(f"Cache hit pour: {cache_key}")
                    return cache_entry["cache_data"].get("results", [])
                else:
                    logger.info(f"Cache expiré pour: {cache_key}")
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du cache: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, results: List[Dict], ttl_days: int = 7):
        """
        Sauvegarde les résultats dans le cache Supabase
        
        Args:
            cache_key: Clé de cache
            results: Résultats à cacher
            ttl_days: Durée de vie du cache en jours (défaut: 7)
        """
        if not self.supabase_client:
            return
        
        try:
            cache_data = {
                "results": results
            }
            
            expires_at = datetime.now() + timedelta(days=ttl_days)
            
            # Upsert (insert or update)
            self.supabase_client.client.table("terminology_cache").upsert({
                "cache_key": cache_key,
                "cache_data": cache_data,
                "expires_at": expires_at.isoformat()
            }, on_conflict="cache_key").execute()
            
            logger.info(f"Résultats mis en cache: {cache_key} (expire: {expires_at})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
    
    def search(
        self,
        query: str,
        lang: str = "fr",
        use_cache: bool = True,
        consumer_friendly: bool = True
    ) -> Dict:
        """
        Recherche des codes ICD-11 par mot-clé avec suggestions grand public
        
        Args:
            query: Terme de recherche (ex: "depression", "TDAH", "SOP")
            lang: Code langue (fr, en) - défaut: fr
            use_cache: Utiliser le cache (défaut: True)
            consumer_friendly: Retourner suggestions grand public (défaut: True)
        
        Returns:
            Si consumer_friendly=True:
            {
                "query": "depression",
                "suggestions": [  # Termes grand public (max 5)
                    {
                        "label": "Dépression",
                        "codes": ["6A70", "6A71"],
                        "category": "mental",
                        "kind": "consumer"
                    }
                ],
                "results": [  # Résultats ICD-11 filtrés/rankés (max 5)
                    {
                        "code": "6A70",
                        "display": "Épisode dépressif",
                        "category": "Troubles mentaux"
                    }
                ],
                "more_results": true  # Il y a plus de résultats disponibles
            }
            
            Si consumer_friendly=False:
            Liste simple comme avant
        """
        if not self.client_id or not self.client_secret:
            logger.error("ICD-11 non configuré")
            if consumer_friendly:
                return {"query": query, "suggestions": [], "results": [], "more_results": False}
            return []
        
        # Normaliser la requête
        query_normalized = query.strip()
        if not query_normalized:
            if consumer_friendly:
                return {"query": query, "suggestions": [], "results": [], "more_results": False}
            return []
        
        # Vérifier le cache
        cache_key = self._get_cache_key(query_normalized, lang)
        if use_cache:
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                # Si mode consumer_friendly, formater la réponse
                if consumer_friendly:
                    return self._format_consumer_response(query_normalized, cached_results, lang)
                return cached_results
        
        # Obtenir le token OAuth2
        token = self._get_access_token()
        if not token:
            logger.warning("Impossible d'obtenir le token OAuth2 ICD-11. Retour de résultats de secours.")
            # Mode dégradé : retourner des résultats de secours
            fallback_results = self._get_fallback_results(query_normalized, lang)
            if consumer_friendly:
                return self._format_consumer_response(query_normalized, fallback_results, lang)
            return fallback_results
        
        # Effectuer la recherche
        try:
            search_url = f"{self.icd_api_url}/release/11/2024-01/mms/search"
            # Note: L'API ICD-11 a des URLs différentes selon le mode d'accès
            # Pour la production, utiliser: https://id.who.int/icd/release/11/...
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Accept-Language": lang,
                "API-Version": "v2"
            }
            
            params = {
                "q": query,
                "useFlexisearch": "true",
                "flatResults": "true"
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Normaliser les résultats
            results = []
            for item in data.get("destinationEntities", []):
                # Extraire le code ICD-11 depuis l'URL
                code = self._extract_code_from_url(item.get("id", ""))
                
                # Récupérer le titre et la catégorie
                title = item.get("title", "")
                
                # Nettoyer le HTML du titre (remove <em>, <span>, etc.)
                title = self._clean_html(title)
                
                # Pour la catégorie, on peut utiliser le champ "theCode" ou "chapter"
                # Simplifié pour le MVP
                category = self._get_category_from_item(item)
                
                if code and title:
                    results.append({
                        "code": code,
                        "display": title,
                        "category": category
                    })
            
            # Limiter à 20 résultats pour le MVP
            results = results[:20]
            
            # Sauvegarder dans le cache (résultats bruts)
            if use_cache:
                self._save_to_cache(cache_key, results)
            
            logger.info(f"Recherche ICD-11 '{query_normalized}' ({lang}): {len(results)} résultats")
            
            # Formater la réponse si mode consumer
            if consumer_friendly:
                return self._format_consumer_response(query_normalized, results, lang)
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la recherche ICD-11: {e}")
            if consumer_friendly:
                return {"query": query_normalized, "suggestions": [], "results": [], "more_results": False}
            return []
    
    def _clean_html(self, text: str) -> str:
        """
        Nettoie les balises HTML d'un texte
        
        Args:
            text: Texte avec HTML (ex: "<em class='found'>Diabète</em>")
        
        Returns:
            Texte nettoyé (ex: "Diabète")
        """
        if not text:
            return ""
        
        # Supprimer toutes les balises HTML
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Décoder les entités HTML courantes
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        
        return clean_text.strip()
    
    def _extract_code_from_url(self, url: str) -> str:
        """
        Extrait le code ICD-11 depuis une URL
        
        Args:
            url: URL ICD (ex: "http://id.who.int/icd/entity/1234567890")
        
        Returns:
            Code court (ex: "6A70") ou l'ID complet si non trouvé
        """
        # Le code se trouve généralement à la fin de l'URL
        # Format: http://id.who.int/icd/entity/1234567890
        parts = url.split("/")
        if len(parts) > 0:
            return parts[-1]
        return url
    
    def _get_category_from_item(self, item: Dict) -> str:
        """
        Détermine la catégorie d'une condition depuis les métadonnées ICD-11
        
        Args:
            item: Item de résultat ICD-11
        
        Returns:
            Nom de catégorie (ex: "Troubles mentaux")
        """
        # Simplification pour le MVP
        # L'API ICD-11 fournit des métadonnées complexes
        # On pourrait utiliser le champ "chapter" ou extraire depuis la hiérarchie
        
        # Pour le MVP, on retourne une catégorie générique
        # À améliorer avec la hiérarchie complète ICD-11
        chapter = item.get("chapter", "")
        if chapter:
            return chapter
        
        return "Non classé"
    
    def _format_consumer_response(
        self,
        query: str,
        raw_results: List[Dict],
        lang: str
    ) -> Dict:
        """
        Formate la réponse avec suggestions consumer + résultats filtrés
        
        Args:
            query: Requête originale
            raw_results: Résultats ICD-11 bruts
            lang: Langue
        
        Returns:
            {suggestions, results, more_results}
        """
        # 1. Obtenir les suggestions consumer
        suggestions = get_consumer_suggestions_for_query(query, lang)
        
        # 2. Filtrer et ranker les résultats ICD-11
        filtered_results = filter_and_rank_results(raw_results, query, max_results=5)
        
        # 3. Déterminer s'il y a plus de résultats
        more_results = len(raw_results) > len(filtered_results)
        
        return {
            "query": query,
            "suggestions": suggestions,
            "results": filtered_results,
            "more_results": more_results
        }
    
    def _get_fallback_results(self, query: str, lang: str) -> List[Dict]:
        """
        Retourne des résultats de secours si l'API ICD-11 n'est pas disponible
        
        Args:
            query: Terme de recherche
            lang: Code langue
        
        Returns:
            Liste de résultats simulés pour le développement
        """
        logger.info(f"Mode dégradé: résultats de secours pour '{query}'")
        
        # Base de données de secours pour les termes courants (français)
        fallback_db = {
            "tdah": [
                {
                    "code": "6A05",
                    "display": "Trouble déficitaire de l'attention avec hyperactivité",
                    "category": "Troubles mentaux, comportementaux ou neurodéveloppementaux"
                }
            ],
            "depression": [
                {
                    "code": "6A70",
                    "display": "Épisode dépressif",
                    "category": "Troubles de l'humeur"
                },
                {
                    "code": "6A71",
                    "display": "Trouble dépressif récurrent",
                    "category": "Troubles de l'humeur"
                }
            ],
            "dépression": [
                {
                    "code": "6A70",
                    "display": "Épisode dépressif",
                    "category": "Troubles de l'humeur"
                }
            ],
            "diabete": [
                {
                    "code": "5A10",
                    "display": "Diabète sucré de type 1",
                    "category": "Troubles endocriniens"
                },
                {
                    "code": "5A11",
                    "display": "Diabète sucré de type 2",
                    "category": "Troubles endocriniens"
                }
            ],
            "diabète": [
                {
                    "code": "5A10",
                    "display": "Diabète sucré de type 1",
                    "category": "Troubles endocriniens"
                },
                {
                    "code": "5A11",
                    "display": "Diabète sucré de type 2",
                    "category": "Troubles endocriniens"
                }
            ],
            "sop": [
                {
                    "code": "GA34.3",
                    "display": "Syndrome des ovaires polykystiques",
                    "category": "Troubles du système génito-urinaire"
                }
            ],
            "anxiete": [
                {
                    "code": "6B00",
                    "display": "Trouble anxieux généralisé",
                    "category": "Troubles anxieux ou liés à la peur"
                }
            ],
            "anxiété": [
                {
                    "code": "6B00",
                    "display": "Trouble anxieux généralisé",
                    "category": "Troubles anxieux ou liés à la peur"
                }
            ],
        }
        
        query_lower = query.lower().strip()
        
        # Recherche exacte
        if query_lower in fallback_db:
            return fallback_db[query_lower]
        
        # Recherche partielle
        for key, results in fallback_db.items():
            if query_lower in key or key in query_lower:
                return results
        
        # Aucun résultat
        return []
    
    def get_entity_details(self, code: str, lang: str = "fr") -> Optional[Dict]:
        """
        Récupère les détails complets d'une entité ICD-11
        
        Args:
            code: Code ICD-11 (ex: "6A70")
            lang: Code langue (fr, en)
        
        Returns:
            Détails de l'entité ou None si non trouvé
        """
        token = self._get_access_token()
        if not token:
            return None
        
        try:
            entity_url = f"{self.icd_api_url}/release/11/2024-01/mms/{code}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Accept-Language": lang,
                "API-Version": "v2"
            }
            
            response = requests.get(entity_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération de l'entité ICD-11 {code}: {e}")
            return None


# Fonction helper pour créer une instance singleton
_icd11_client_instance = None


def get_icd11_client(supabase_client=None) -> ICD11Client:
    """
    Retourne une instance singleton du client ICD-11
    
    Args:
        supabase_client: Instance de SupabaseClient (optionnel)
    
    Returns:
        Instance de ICD11Client
    """
    global _icd11_client_instance
    if _icd11_client_instance is None:
        _icd11_client_instance = ICD11Client(supabase_client=supabase_client)
    return _icd11_client_instance
