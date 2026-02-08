"""
⚠️ OBSOLÈTE - Remplacé par giygas_medication_service.py ⚠️

Ce service est conservé temporairement pour référence et migration progressive.
Il utilise l'ancienne API BDPM/open-medicaments.fr.

NOUVEAU SERVICE (à utiliser) : giygas_medication_service.py
- Source : API Giygas (medicaments-api.giygas.dev)
- Fonctionnalités : Composition, génériques, présentations (CIP13, prix), scan boîtes

Date dépréciation : 4 Février 2026
À supprimer après : Migration complète validée

---

Service de gestion des médicaments (LEGACY)
Intègre BDPM/ANSM pour notice/génériques/alternatives
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.warning("⚠️ medication_service.py est obsolète. Utilisez giygas_medication_service.py")


class MedicationService:
    """
    Service pour rechercher et enrichir les médicaments
    Source: BDPM (Base de données publique des médicaments) - API publique française
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialise le service médicaments
        
        Args:
            supabase_client: Instance de SupabaseClient pour le cache local
        """
        self.supabase_client = supabase_client
        self.bdpm_api_url = "https://open-medicaments.fr/api/v1"
        self.cache_ttl_days = 7  # Durée de vie du cache
    
    def search_medications(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche de médicaments via API BDPM
        
        Args:
            query: Terme de recherche (min 2 caractères)
            limit: Nombre maximum de résultats (défaut: 10)
        
        Returns:
            Liste de médicaments:
            [
                {
                    "id": "CIS-...",
                    "name": "Doliprane 500mg",
                    "form": "Comprimé",
                    "laboratory": "Sanofi",
                    "active_substance": "Paracétamol",
                    "atc_code": "N02BE01",
                    "source": "bdpm"
                }
            ]
        """
        if not query or len(query) < 2:
            return []
        
        # 1. Chercher d'abord dans le cache local (plus rapide)
        local_results = self._search_local_cache(query, limit)
        if local_results:
            logger.info(f"Cache hit: {len(local_results)} résultats pour '{query}'")
            return local_results
        
        # 2. Sinon interroger l'API BDPM
        try:
            url = f"{self.bdpm_api_url}/medicaments"
            params = {"query": query, "limit": limit}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"API BDPM erreur {response.status_code} pour '{query}'")
                return []
            
            data = response.json()
            
            # Normaliser le format
            results = []
            for item in (data if isinstance(data, list) else []):
                med_data = {
                    "id": item.get("cis") or item.get("id"),
                    "name": item.get("denomination") or item.get("name"),
                    "form": item.get("forme") or item.get("form"),
                    "laboratory": item.get("titulaire") or item.get("laboratory"),
                    "active_substance": item.get("substance_active") or item.get("active_substance"),
                    "atc_code": item.get("code_atc") or item.get("atc_code"),
                    "source": "bdpm"
                }
                
                # Ne garder que les médicaments avec au moins un ID et un nom
                if med_data["id"] and med_data["name"]:
                    results.append(med_data)
                    
                    # Mettre en cache automatiquement
                    self._cache_medication(med_data)
            
            logger.info(f"Recherche BDPM '{query}': {len(results)} résultats")
            return results[:limit]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API BDPM: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche: {e}")
            return []
    
    def _search_local_cache(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche dans le cache local (medications_catalog)
        
        Returns:
            Liste de médicaments depuis le cache
        """
        if not self.supabase_client:
            return []
        
        try:
            # Recherche insensible à la casse avec ILIKE
            response = self.supabase_client.client.table("medications_catalog")\
                .select("id, external_id, name, form, laboratory, active_substance, atc_code, source")\
                .ilike("name", f"%{query}%")\
                .limit(limit)\
                .execute()
            
            if not response.data:
                return []
            
            # Formater pour correspondre au format de l'API
            results = []
            for item in response.data:
                results.append({
                    "id": item["external_id"],  # ID externe pour compatibilité
                    "catalog_id": item["id"],  # ID interne du catalogue
                    "name": item["name"],
                    "form": item["form"],
                    "laboratory": item["laboratory"],
                    "active_substance": item["active_substance"],
                    "atc_code": item["atc_code"],
                    "source": item["source"]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche cache local: {e}")
            return []
    
    def _cache_medication(self, medication_data: Dict) -> Optional[str]:
        """
        Enregistre un médicament dans le catalogue local
        
        Args:
            medication_data: Données du médicament à cacher
        
        Returns:
            UUID du médicament dans medications_catalog ou None
        """
        if not self.supabase_client or not medication_data.get("id"):
            return None
        
        try:
            # Upsert dans medications_catalog
            result = self.supabase_client.client.table("medications_catalog").upsert({
                "external_id": medication_data["id"],
                "source": medication_data.get("source", "bdpm"),
                "name": medication_data["name"],
                "active_substance": medication_data.get("active_substance"),
                "atc_code": medication_data.get("atc_code"),
                "laboratory": medication_data.get("laboratory"),
                "form": medication_data.get("form"),
                "raw_data": medication_data
            }, on_conflict="source,external_id").execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur cache médicament: {e}")
            return None
    
    def get_medication_details(self, external_id: str, source: str = "bdpm") -> Optional[Dict]:
        """
        Récupère les détails complets d'un médicament (notice, génériques, alternatives)
        
        Args:
            external_id: ID externe du médicament (ex: code CIS)
            source: Source du médicament (défaut: bdpm)
        
        Returns:
            {
                "notice_url": "https://...",
                "notice_text": "...",
                "generics": [{"id": "...", "name": "...", "laboratory": "..."}],
                "alternatives": [{"id": "...", "name": "...", "reason": "..."}]
            }
        """
        if source != "bdpm":
            logger.warning(f"Source '{source}' non supportée pour le moment")
            return None
        
        try:
            url = f"{self.bdpm_api_url}/medicaments/{external_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"API BDPM erreur {response.status_code} pour {external_id}")
                return self._get_fallback_details(external_id)
            
            data = response.json()
            
            # Extraire notice
            notice_url = data.get("notice_url") or data.get("rdp_url")
            notice_text = data.get("notice_text")  # Si disponible
            
            # Extraire génériques
            generics = []
            if data.get("generiques"):
                for gen in data.get("generiques", []):
                    generics.append({
                        "id": gen.get("cis"),
                        "name": gen.get("denomination"),
                        "laboratory": gen.get("titulaire")
                    })
            
            # Extraire alternatives (médicaments avec même substance active)
            alternatives = []
            active_substance = data.get("substance_active")
            if active_substance and self.supabase_client:
                try:
                    alt_results = self.supabase_client.client.table("medications_catalog")\
                        .select("id, external_id, name, laboratory")\
                        .eq("active_substance", active_substance)\
                        .neq("external_id", external_id)\
                        .limit(5)\
                        .execute()
                    
                    if alt_results.data:
                        alternatives = [
                            {
                                "id": item["external_id"],
                                "catalog_id": item["id"],
                                "name": item["name"],
                                "laboratory": item["laboratory"],
                                "reason": "Même substance active"
                            }
                            for item in alt_results.data
                        ]
                except Exception as e:
                    logger.warning(f"Erreur recherche alternatives: {e}")
            
            return {
                "notice_url": notice_url,
                "notice_text": notice_text,
                "generics": generics,
                "alternatives": alternatives
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API BDPM pour détails {external_id}: {e}")
            return self._get_fallback_details(external_id)
        except Exception as e:
            logger.error(f"Erreur inattendue détails {external_id}: {e}")
            return None
    
    def _get_fallback_details(self, external_id: str) -> Dict:
        """
        Retourne des détails par défaut si l'API échoue
        
        Returns:
            Détails minimaux (vides)
        """
        return {
            "notice_url": None,
            "notice_text": None,
            "generics": [],
            "alternatives": []
        }
    
    def get_or_create_catalog_entry(self, external_id: str, source: str = "bdpm") -> Optional[str]:
        """
        Récupère ou crée une entrée dans le catalogue
        
        Args:
            external_id: ID externe du médicament
            source: Source du médicament
        
        Returns:
            UUID du médicament dans medications_catalog
        """
        if not self.supabase_client:
            return None
        
        try:
            # Chercher si existe déjà
            result = self.supabase_client.client.table("medications_catalog")\
                .select("id")\
                .eq("external_id", external_id)\
                .eq("source", source)\
                .single()\
                .execute()
            
            if result.data:
                return result.data["id"]
            
            # Sinon, récupérer depuis l'API et créer
            search_results = self.search_medications(external_id, limit=1)
            if search_results and len(search_results) > 0:
                med = search_results[0]
                return self._cache_medication(med)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur get_or_create_catalog_entry: {e}")
            return None
    
    def cache_medication_details(self, medication_id: str, details: Dict) -> bool:
        """
        Sauvegarde les détails d'un médicament dans le cache
        
        Args:
            medication_id: UUID du médicament dans medications_catalog
            details: Dictionnaire des détails (notice, generics, alternatives)
        
        Returns:
            True si succès, False sinon
        """
        if not self.supabase_client:
            return False
        
        try:
            self.supabase_client.client.table("medication_details").upsert({
                "medication_id": medication_id,
                "notice_url": details.get("notice_url"),
                "notice_text": details.get("notice_text"),
                "generics": details.get("generics", []),
                "alternatives": details.get("alternatives", []),
                "last_refreshed_at": datetime.now().isoformat()
            }, on_conflict="medication_id").execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde détails: {e}")
            return False


# Fonction helper pour créer une instance singleton
_medication_service_instance = None


def get_medication_service(supabase_client=None) -> MedicationService:
    """
    Retourne une instance singleton du service médicaments
    
    Args:
        supabase_client: Instance de SupabaseClient (optionnel)
    
    Returns:
        Instance de MedicationService
    """
    global _medication_service_instance
    if _medication_service_instance is None:
        _medication_service_instance = MedicationService(supabase_client=supabase_client)
    return _medication_service_instance
