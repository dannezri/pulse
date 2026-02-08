"""
Service de gestion des médicaments via API Giygas
Source unique de vérité pour les médicaments français
Remplace BDPM/open-medicaments.fr
"""

import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class GiygasMedicationService:
    """
    Service pour rechercher et enrichir les médicaments via API Giygas
    
    API: https://medicaments-api.giygas.dev
    
    Fonctionnalités:
    - Recherche de médicaments par nom ou CIS
    - Récupération détails complets (composition, génériques, présentations, conditions)
    - Support CIP13/CIP7 pour scan de boîtes (GS1 DataMatrix)
    - Cache local intégré
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialise le service médicaments Giygas
        
        Args:
            supabase_client: Instance de SupabaseClient pour le cache local
        """
        self.supabase_client = supabase_client
        self.api_base_url = "https://medicaments-api.giygas.dev"
        self.cache_ttl_days = 7  # Durée de vie du cache
    
    def search_medications(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche de médicaments par nom
        
        Args:
            query: Terme de recherche (min 2 caractères)
            limit: Nombre maximum de résultats (défaut: 10)
        
        Returns:
            Liste de médicaments:
            [
                {
                    "cis": "60001551",
                    "name": "DOLIPRANE 500 mg, comprimé",
                    "form": "comprimé",
                    "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
                    "active_substance": "PARACETAMOL",
                    "source": "giygas"
                }
            ]
        """
        if not query or len(query) < 2:
            return []
        
        # 1. Chercher dans le cache local (plus rapide si déjà en cache)
        local_results = self._search_local_cache(query, limit)
        if local_results and len(local_results) >= min(3, limit):
            # Si on a au moins 3 résultats en cache, les retourner
            logger.info(f"[Giygas] Cache hit: {len(local_results)} résultats pour '{query}'")
            return local_results
        
        # 2. Sinon interroger l'API Giygas
        try:
            url = f"{self.api_base_url}/medicament/{query}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"[Giygas] API erreur {response.status_code} pour '{query}'")
                return []
            
            data = response.json()
            
            # L'API Giygas peut retourner un objet unique ou une liste
            items = data if isinstance(data, list) else [data] if data else []
            
            # Normaliser le format
            results = []
            for item in items[:limit]:
                if not item or not item.get("cis"):
                    continue
                
                # Extraire composition (première substance active)
                composition = item.get("composition", [])
                active_substance = None
                if composition and len(composition) > 0:
                    active_substance = composition[0].get("denominationSubstance", "").upper()
                
                med_data = {
                    "cis": str(item.get("cis", "")),
                    "name": item.get("elementPharmaceutique", ""),
                    "form": item.get("formePharmaceutique", ""),
                    "laboratory": item.get("titulaire", None),
                    "active_substance": active_substance,
                    "source": "giygas"
                }
                
                # Ne garder que les médicaments avec CIS et nom
                if med_data["cis"] and med_data["name"]:
                    results.append(med_data)
                    
                    # Mettre en cache automatiquement
                    self._cache_medication(item, med_data)
            
            logger.info(f"[Giygas] Recherche '{query}': {len(results)} résultats")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Giygas] Erreur API: {e}")
            return []
        except Exception as e:
            logger.error(f"[Giygas] Erreur inattendue lors de la recherche: {e}")
            return []
    
    
    def get_by_cis(self, cis: str) -> Optional[Dict]:
        """
        Récupère un médicament par son code CIS
        
        Args:
            cis: Code CIS du médicament (ex: "60001551")
        
        Returns:
            Détails complets du médicament ou None
        """
        try:
            # Chercher d'abord dans le cache
            if self.supabase_client:
                cached = self._get_from_cache_by_cis(cis)
                if cached:
                    logger.info(f"[Giygas] Cache hit for CIS {cis}")
                    return cached
            
            # Sinon interroger l'API
            url = f"{self.api_base_url}/medicament/id/{cis}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"[Giygas] Médicament CIS {cis} non trouvé")
                return None
            
            data = response.json()
            
            if not data:
                return None
            
            # Normaliser et enrichir
            med_data = self._normalize_medication_full(data)
            
            # Mettre en cache
            if med_data:
                self._cache_medication(data, med_data)
            
            return med_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Giygas] Erreur API pour CIS {cis}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Giygas] Erreur inattendue pour CIS {cis}: {e}")
            return None
    
    def get_by_cip13(self, cip13: str) -> Optional[Dict]:
        """
        Récupère un médicament par son code CIP13 (utilisé pour scan de boîtes)
        
        Args:
            cip13: Code CIP13 (13 chiffres)
        
        Returns:
            Détails complets du médicament ou None
        """
        try:
            # Chercher dans le cache local d'abord
            if self.supabase_client:
                result = self.supabase_client.client.table("drug_presentations")\
                    .select("item_id, medications_catalog!inner(*)")\
                    .eq("cip13", cip13)\
                    .limit(1)\
                    .execute()
                
                if result.data and len(result.data) > 0:
                    med = result.data[0].get("medications_catalog")
                    if med:
                        logger.info(f"[Giygas] Cache hit for CIP13 {cip13}")
                        cis = med["external_id"]
                        return self.get_by_cis(cis)
            
            # L'API Giygas ne supporte pas la recherche directe par CIP13
            # Il faut d'abord récupérer le CIS associé (via autre source ou DB)
            logger.warning(f"[Giygas] CIP13 {cip13} non trouvé en cache, impossible de résoudre sans CIS")
            return None
            
        except Exception as e:
            logger.error(f"[Giygas] Erreur pour CIP13 {cip13}: {e}")
            return None
    
    def parse_gtin_to_cip13(self, gtin: str) -> Optional[str]:
        """
        Convertit un code GTIN (GS1 DataMatrix) en CIP13
        
        Args:
            gtin: Code GTIN (14 chiffres généralement)
        
        Returns:
            CIP13 (13 chiffres) ou None si conversion impossible
        """
        if not gtin:
            return None
        
        # Supprimer les espaces et les caractères non numériques
        gtin_clean = re.sub(r'\D', '', gtin)
        
        # GTIN-14 → CIP13 : retirer le 1er chiffre (indicateur), garder les 13 suivants
        # Format : [Indicateur: 1 chiffre][GTIN-13 / CIP13: 13 chiffres]
        if len(gtin_clean) == 14:
            cip13 = gtin_clean[1:14]
            logger.info(f"[Giygas] GTIN-14 {gtin} → CIP13 {cip13}")
            return cip13
        
        # GTIN-13 → CIP13 : déjà au bon format
        elif len(gtin_clean) == 13:
            logger.info(f"[Giygas] GTIN-13 {gtin} → CIP13 {gtin_clean}")
            return gtin_clean
        
        else:
            logger.warning(f"[Giygas] GTIN {gtin} format invalide (attendu: 13 ou 14 chiffres)")
            return None
    
    def resolve_cip13_via_public_api(self, cip13: str) -> Optional[str]:
        """
        Résout un CIP13 en nom de médicament via recherche Giygas par CIP13
        
        Stratégie:
        1. Extraire les 4 premiers chiffres du CIP13 (préfixe labo)
        2. Chercher dans Giygas avec ces chiffres
        3. Filtrer les résultats par CIP13 exact dans les présentations
        
        Args:
            cip13: Code CIP13 (13 chiffres)
        
        Returns:
            Nom du médicament ou None si non trouvé
        """
        try:
            # Le CIP13 commence toujours par 3400 pour les médicaments français
            # Les 3-4 chiffres suivants peuvent être un indicateur
            # Stratégie: chercher avec les derniers chiffres significatifs
            
            # Extraire les derniers 7 chiffres (CIP7)
            if len(cip13) == 13 and cip13.startswith('3400'):
                cip7 = cip13[4:11]  # Extraire les 7 chiffres après "3400"
                
                logger.info(f"[CIP Resolver] CIP13 {cip13} → CIP7 {cip7}")
                logger.info(f"[CIP Resolver] Recherche large dans Giygas avec CIP7...")
                
                # Rechercher dans Giygas avec le CIP7
                search_results = self.search_medications(cip7, limit=20)
                
                if search_results:
                    # Parcourir les résultats et récupérer les détails complets
                    for result in search_results:
                        cis = result.get("cis")
                        if cis:
                            # Récupérer les détails complets avec présentations
                            details = self.get_by_cis(cis)
                            if details and "presentations" in details:
                                # Chercher le CIP13 exact dans les présentations
                                for pres in details["presentations"]:
                                    if pres.get("cip13") == cip13:
                                        med_name = details.get("name")
                                        logger.info(f"[CIP Resolver] ✅ CIP13 {cip13} trouvé → {med_name}")
                                        return med_name
            
            logger.warning(f"[CIP Resolver] CIP13 {cip13} non résolu")
            return None
            
        except Exception as e:
            logger.error(f"[CIP Resolver] Erreur pour {cip13}: {e}")
            return None
    
    def _normalize_medication_full(self, api_data: Dict) -> Dict:
        """
        Normalise les données complètes de l'API Giygas
        
        Returns:
            {
                "cis": "60001551",
                "name": "DOLIPRANE 500 mg, comprimé",
                "form": "comprimé",
                "laboratory": "OPELLA HEALTHCARE",
                "active_substance": "PARACETAMOL",
                "composition": [...],
                "generics": [...],
                "presentations": [...],
                "conditions": {...}
            }
        """
        if not api_data:
            return None
        
        # Extraire composition
        composition = []
        composition_data = api_data.get("composition") or []
        for comp in composition_data:
            composition.append({
                "substance": comp.get("denominationSubstance", ""),
                "dosage": comp.get("dosage", ""),
                "reference": comp.get("referenceDosage", ""),
                "nature": comp.get("natureComposant", "")
            })
        
        # Extraire substance active principale
        active_substance = None
        if composition and len(composition) > 0:
            active_substance = composition[0]["substance"].upper()
        
        # Extraire génériques
        generics = []
        generiques_data = api_data.get("generiques") or []
        for gen in generiques_data:
            generics.append({
                "cis": str(gen.get("cis", "")),
                "name": gen.get("elementPharmaceutique", ""),
                "laboratory": gen.get("titulaire", "")
            })
        
        # Extraire présentations (CIP13/CIP7, prix, remboursement)
        presentations = []
        presentations_data = api_data.get("presentation") or []
        for pres in presentations_data:
            # Parser le taux de remboursement (ex: "65%" → 65)
            reimbursement_str = pres.get("tauxRemboursement", "")
            reimbursement_rate = None
            if reimbursement_str and isinstance(reimbursement_str, str):
                try:
                    reimbursement_rate = int(reimbursement_str.rstrip('%'))
                except (ValueError, AttributeError):
                    reimbursement_rate = None
            
            presentations.append({
                "cip13": str(pres.get("cip13", "")),
                "cip7": str(pres.get("cip7", "")),
                "label": pres.get("libelle", ""),
                "price": pres.get("prix", 0),
                "reimbursement_rate": reimbursement_rate,
                "status": pres.get("statusAdministratif", ""),
                "commercialisation": pres.get("etatComercialisation", "")
            })
        
        # Extraire conditions de prescription
        conditions = api_data.get("conditions", [])
        
        # Laboratoire = titulaire au niveau principal
        laboratory = api_data.get("titulaire", None)
        
        return {
            "cis": str(api_data.get("cis", "")),
            "name": api_data.get("elementPharmaceutique", ""),
            "form": api_data.get("formePharmaceutique", ""),
            "laboratory": laboratory,
            "active_substance": active_substance,
            "composition": composition,
            "generics": generics,
            "presentations": presentations,
            "conditions": conditions,
            "source": "giygas"
        }
    
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
                .select("id, external_id, name, form, laboratory, active_substance, source")\
                .eq("source", "giygas")\
                .ilike("name", f"%{query}%")\
                .limit(limit)\
                .execute()
            
            if not response.data:
                return []
            
            # Formater pour correspondre au format de l'API
            results = []
            for item in response.data:
                results.append({
                    "cis": item["external_id"],
                    "catalog_id": item["id"],
                    "name": item["name"],
                    "form": item["form"],
                    "laboratory": item["laboratory"],
                    "active_substance": item["active_substance"],
                    "source": item["source"]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"[Giygas] Erreur recherche cache local: {e}")
            return []
    
    def _get_from_cache_by_cis(self, cis: str) -> Optional[Dict]:
        """
        Récupère un médicament depuis le cache par CIS
        """
        if not self.supabase_client:
            return None
        
        try:
            result = self.supabase_client.client.table("medications_catalog")\
                .select("*, medication_details(*)")\
                .eq("source", "giygas")\
                .eq("external_id", cis)\
                .single()\
                .execute()
            
            if not result.data:
                return None
            
            med = result.data
            details = med.get("medication_details")
            
            # Reconstruire le format complet depuis le cache
            return {
                "cis": med["external_id"],
                "catalog_id": med["id"],
                "name": med["name"],
                "form": med["form"],
                "laboratory": med["laboratory"],
                "active_substance": med["active_substance"],
                "composition": details.get("composition", []) if details else [],
                "generics": details.get("generics", []) if details else [],
                "presentations": self._get_presentations_from_cache(med["id"]) if details else [],
                "conditions": details.get("conditions", {}) if details else {},
                "source": "giygas"
            }
            
        except Exception as e:
            logger.error(f"[Giygas] Erreur cache CIS {cis}: {e}")
            return None
    
    def _get_presentations_from_cache(self, medication_id: str) -> List[Dict]:
        """
        Récupère les présentations depuis la table drug_presentations
        """
        if not self.supabase_client:
            return []
        
        try:
            result = self.supabase_client.client.table("drug_presentations")\
                .select("*")\
                .eq("item_id", medication_id)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"[Giygas] Erreur récupération présentations: {e}")
            return []
    
    def _cache_medication(self, api_data: Dict, normalized_data: Dict) -> Optional[str]:
        """
        Enregistre un médicament dans le catalogue local
        
        Args:
            api_data: Données brutes de l'API
            normalized_data: Données normalisées
        
        Returns:
            UUID du médicament dans medications_catalog ou None
        """
        if not self.supabase_client or not normalized_data.get("cis"):
            return None
        
        try:
            # Upsert dans medications_catalog
            catalog_result = self.supabase_client.client.table("medications_catalog").upsert({
                "external_id": normalized_data["cis"],
                "source": "giygas",
                "name": normalized_data["name"],
                "active_substance": normalized_data.get("active_substance"),
                "atc_code": None,  # Giygas n'expose pas l'ATC directement
                "laboratory": normalized_data.get("laboratory"),
                "form": normalized_data.get("form"),
                "raw_data": api_data
            }, on_conflict="source,external_id").execute()
            
            if not catalog_result.data or len(catalog_result.data) == 0:
                return None
            
            medication_id = catalog_result.data[0]["id"]
            
            # Upsert medication_details (composition, génériques, conditions)
            if normalized_data:
                self.supabase_client.client.table("medication_details").upsert({
                    "medication_id": medication_id,
                    "composition": normalized_data.get("composition", []),
                    "generics": normalized_data.get("generics", []),
                    "conditions": normalized_data.get("conditions", {}),
                    "last_refreshed_at": datetime.now().isoformat()
                }, on_conflict="medication_id").execute()
                
                # Upsert présentations (CIP13/CIP7)
                for pres in normalized_data.get("presentations", []):
                    if pres.get("cip13"):
                        self.supabase_client.client.table("drug_presentations").upsert({
                            "item_id": medication_id,
                            "cip13": pres["cip13"],
                            "cip7": pres.get("cip7"),
                            "label": pres.get("label"),
                            "price": pres.get("price"),
                            "reimbursement_rate": pres.get("reimbursement_rate")
                        }, on_conflict="cip13").execute()
            
            logger.info(f"[Giygas] Médicament CIS {normalized_data['cis']} mis en cache")
            return medication_id
            
        except Exception as e:
            logger.error(f"[Giygas] Erreur cache médicament: {e}")
            return None


# Fonction helper pour créer une instance singleton
_giygas_service_instance = None


def get_giygas_medication_service(supabase_client=None) -> GiygasMedicationService:
    """
    Retourne une instance singleton du service Giygas
    
    Args:
        supabase_client: Instance de SupabaseClient (optionnel)
    
    Returns:
        Instance de GiygasMedicationService
    """
    global _giygas_service_instance
    if _giygas_service_instance is None:
        _giygas_service_instance = GiygasMedicationService(supabase_client=supabase_client)
    return _giygas_service_instance
