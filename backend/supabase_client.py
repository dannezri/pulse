"""
Client Supabase pour interagir avec la base de données
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from supabase import create_client, Client
import os
import logging
import hashlib
import json

# Utiliser dateutil pour un parsing robuste des dates ISO
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Avertir si dateutil n'est pas disponible
if not DATEUTIL_AVAILABLE:
    logger.warning("python-dateutil not available. Install with: pip install python-dateutil")


def parse_iso_datetime(date_string: str) -> datetime:
    """
    Parse une date ISO de manière robuste (gère les microsecondes variables)
    
    Args:
        date_string: Chaîne de date ISO (ex: "2026-01-23T21:37:06.50345+00:00")
    
    Returns:
        datetime object
    """
    if DATEUTIL_AVAILABLE:
        # Utiliser dateutil.parser pour un parsing robuste
        return date_parser.isoparse(date_string)
    else:
        # Fallback : essayer fromisoformat avec nettoyage
        # Remplacer "Z" par "+00:00" et normaliser les microsecondes
        normalized = date_string.replace("Z", "+00:00")
        # Si pas de timezone, ajouter +00:00
        if "+" not in normalized and "-" not in normalized[-6:]:
            normalized = normalized + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            # Si ça échoue encore, essayer sans microsecondes
            if "." in normalized:
                parts = normalized.split(".")
                if len(parts) == 2:
                    # Garder seulement la partie avant les microsecondes
                    base = parts[0]
                    # Extraire la timezone
                    tz_part = parts[1].split("+")[-1] if "+" in parts[1] else parts[1].split("-")[-1]
                    if "+" in parts[1]:
                        normalized = base + "+" + tz_part
                    elif "-" in parts[1] and len(parts[1].split("-")) > 1:
                        normalized = base + "-" + tz_part
                    else:
                        normalized = base + "+00:00"
            return datetime.fromisoformat(normalized)


class SupabaseClient:
    """
    Client pour interagir avec Supabase
    Gère toutes les opérations CRUD sur les tables
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
    
    def get_user_by_external_id(
        self, 
        external_user_id: str, 
        provider_system: str = "open_wearables"
    ) -> Optional[str]:
        """
        Récupère l'UUID Supabase d'un utilisateur via son ID externe (provider)
        
        Args:
            external_user_id: ID utilisateur dans le système externe
            provider_system: Système externe ('open_wearables', 'apple_health', etc.)
        
        Returns:
            UUID Supabase de l'utilisateur ou None si non trouvé
        """
        try:
            response = self.client.table("external_identities").select("supabase_user_id").eq(
                "provider_system", provider_system
            ).eq("external_user_id", external_user_id).eq("is_active", True).execute()
            
            if response.data:
                return response.data[0]["supabase_user_id"]
            return None
        except Exception as e:
            logger.error(f"Error fetching user by external ID ({provider_system}): {e}")
            return None
    
    def get_user_by_open_wearables_id(self, open_wearables_user_id: str) -> Optional[str]:
        """
        Récupère l'UUID Supabase d'un utilisateur via son Open Wearables ID
        (Méthode de compatibilité - utilise get_user_by_external_id en interne)
        """
        return self.get_user_by_external_id(open_wearables_user_id, "open_wearables")
    
    def create_or_update_external_identity(
        self,
        supabase_user_id: str,
        provider_system: str,
        external_user_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Crée ou met à jour une identité externe
        
        Args:
            supabase_user_id: UUID Supabase de l'utilisateur
            provider_system: Système externe ('open_wearables', 'apple_health', etc.)
            external_user_id: ID utilisateur dans le système externe
            metadata: Métadonnées additionnelles (tokens, permissions, etc.)
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Upsert (insert ou update)
            self.client.table("external_identities").upsert({
                "supabase_user_id": supabase_user_id,
                "provider_system": provider_system,
                "external_user_id": external_user_id,
                "metadata": metadata or {},
                "is_active": True
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error creating/updating external identity: {e}")
            return False
    
    def get_external_identities(self, supabase_user_id: str) -> List[Dict]:
        """
        Récupère toutes les identités externes d'un utilisateur
        
        Args:
            supabase_user_id: UUID Supabase de l'utilisateur
        
        Returns:
            Liste des identités externes
        """
        try:
            response = self.client.table("external_identities").select("*").eq(
                "supabase_user_id", supabase_user_id
            ).eq("is_active", True).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching external identities: {e}")
            return []
    
    def deactivate_external_identity(
        self,
        supabase_user_id: str,
        provider_system: str,
        external_user_id: Optional[str] = None
    ) -> bool:
        """
        Désactive une identité externe (au lieu de la supprimer)
        
        Args:
            supabase_user_id: UUID Supabase de l'utilisateur
            provider_system: Système externe
            external_user_id: ID externe (optionnel, désactive toutes les identités du provider si non fourni)
        
        Returns:
            True si succès, False sinon
        """
        try:
            query = self.client.table("external_identities").update({
                "is_active": False
            }).eq("supabase_user_id", supabase_user_id).eq("provider_system", provider_system)
            
            if external_user_id:
                query = query.eq("external_user_id", external_user_id)
            
            query.execute()
            return True
        except Exception as e:
            logger.error(f"Error deactivating external identity: {e}")
            return False
    
    def insert_biometric(
        self,
        user_id: str,
        metric_type: str,
        value: float,
        recorded_at: datetime,
        raw_data: Dict,
        source: str = "open_wearables",
        source_event_id: Optional[str] = None
    ):
        """
        Insère une mesure biométrique dans la table biometrics avec support de l'idempotence.
        
        Si source_event_id est fourni, la contrainte unique (user_id, source, source_event_id)
        empêchera les doublons. Si source_event_id n'est pas fourni, génère un hash du payload
        comme fallback.
        """
        try:
            # Générer source_event_id si non fourni (fallback: hash du payload)
            if source_event_id is None:
                # Créer un hash du payload pour l'idempotence
                payload_str = json.dumps({
                    "user_id": user_id,
                    "metric_type": metric_type,
                    "value": value,
                    "recorded_at": recorded_at.isoformat(),
                    "raw_data": raw_data
                }, sort_keys=True)
                source_event_id = hashlib.md5(payload_str.encode()).hexdigest()
            
            # Vérifier si l'événement existe déjà (idempotence)
            if source_event_id:
                existing = self.client.table("biometrics").select("id").eq(
                    "user_id", user_id
                ).eq("source", source).eq("source_event_id", source_event_id).execute()
                
                if existing.data:
                    logger.debug(f"Event déjà traité (idempotence): {source_event_id}")
                    return {"status": "duplicate", "existing_id": existing.data[0]["id"]}
            
            # Insérer la mesure
            result = self.client.table("biometrics").insert({
                "user_id": user_id,
                "metric_type": metric_type,
                "value": value,
                "recorded_at": recorded_at.isoformat(),
                "raw_data": raw_data,
                "source": source,
                "source_event_id": source_event_id
            }).execute()
            
            return {"status": "inserted", "data": result.data[0] if result.data else None}
            
        except Exception as e:
            # Si c'est une erreur de contrainte unique, c'est un doublon (idempotence)
            error_str = str(e).lower()
            if "unique" in error_str or "duplicate" in error_str:
                logger.debug(f"Event déjà traité (contrainte unique): {source_event_id}")
                return {"status": "duplicate"}
            logger.error(f"Error inserting biometric: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_today_biometrics(self, user_id: str) -> Dict:
        """Récupère toutes les biométriques du jour pour un utilisateur"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            response = self.client.table("biometrics").select("*").eq("user_id", user_id).gte("recorded_at", today_start.isoformat()).lt("recorded_at", today_end.isoformat()).execute()
            
            # Organiser par type de métrique
            organized = {}
            for entry in response.data:
                metric_type = entry["metric_type"]
                if metric_type not in organized:
                    organized[metric_type] = []
                organized[metric_type].append(entry)
            
            return organized
        except Exception as e:
            logger.error(f"Error fetching today's biometrics: {e}")
            return {}
    
    def get_historical_biometrics(self, user_id: str, days: int = 7) -> List[Dict]:
        """Récupère les biométriques historiques pour calculer les baselines"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            response = self.client.table("biometrics").select("*").eq("user_id", user_id).gte("recorded_at", start_date.isoformat()).order("recorded_at", desc=False).execute()
            
            # Organiser par date
            by_date = defaultdict(lambda: {"date": "", "metrics": {}})
            
            for entry in response.data:
                # Parser la date de manière robuste (gère les microsecondes variables)
                date_string = entry["recorded_at"]
                recorded_at = parse_iso_datetime(date_string)
                date_key = recorded_at.date().isoformat()
                
                if not by_date[date_key]["date"]:
                    by_date[date_key]["date"] = date_key
                
                metric_type = entry["metric_type"]
                if metric_type not in by_date[date_key]["metrics"]:
                    by_date[date_key]["metrics"][metric_type] = []
                
                by_date[date_key]["metrics"][metric_type].append(entry["value"])
            
            # Convertir en liste et calculer les moyennes par jour
            result = []
            for date_key, data in by_date.items():
                daily_metrics = {}
                
                # Calculer les moyennes pour chaque métrique
                for metric_type, values in data["metrics"].items():
                    if values:
                        daily_metrics[metric_type] = sum(values) / len(values)
                
                result.append({
                    "date": data["date"],
                    "metrics": daily_metrics
                })
            
            return result
        except Exception as e:
            logger.error(f"Error fetching historical biometrics: {e}")
            return []
    
    def get_user_goal(self, user_id: str) -> str:
        """Récupère l'objectif santé de l'utilisateur"""
        try:
            response = self.client.table("profiles").select("health_goal").eq("id", user_id).execute()
            if response.data:
                return response.data[0].get("health_goal", "energy")
            return "energy"
        except Exception as e:
            logger.error(f"Error fetching user goal: {e}")
            return "energy"
    
    def save_health_profile(
        self, 
        user_id: str, 
        profile_data: Dict,
        profile_version: Optional[int] = None,
        normalizer_version: Optional[str] = None,
        schema_version: Optional[str] = None
    ):
        """
        Sauvegarde le profil de santé normalisé avec versioning
        
        Les versions peuvent être extraites du profile_data["_version"] si présentes,
        ou passées explicitement en paramètres.
        """
        try:
            today = datetime.now().date().isoformat()
            
            # Extraire les versions depuis profile_data si présentes
            version_info = profile_data.get("_version", {})
            if not profile_version:
                profile_version = version_info.get("profile_version", 1)
            if not normalizer_version:
                normalizer_version = version_info.get("normalizer_version")
            if not schema_version:
                schema_version = version_info.get("schema_version")
            
            # Upsert (insert ou update si existe déjà)
            self.client.table("health_profiles").upsert({
                "user_id": user_id,
                "profile_data": profile_data,
                "date": today,
                "profile_version": profile_version,
                "normalizer_version": normalizer_version,
                "schema_version": schema_version
            }).execute()
        except Exception as e:
            logger.error(f"Error saving health profile: {e}")
    
    def get_latest_health_profile(self, user_id: str) -> Optional[Dict]:
        """Récupère le dernier profil de santé pour un utilisateur"""
        try:
            response = self.client.table("health_profiles").select("*").eq("user_id", user_id).order("date", desc=True).limit(1).execute()
            if response.data:
                return response.data[0]["profile_data"]
            return None
        except Exception as e:
            logger.error(f"Error fetching latest health profile: {e}")
            return None
    
    def update_baselines(self, user_id: str, baseline_hrv: Optional[int], baseline_hr: Optional[int]):
        """Met à jour les baselines dans le profil utilisateur"""
        try:
            update_data = {}
            if baseline_hrv is not None:
                update_data["baseline_hrv"] = baseline_hrv
            if baseline_hr is not None:
                update_data["baseline_resting_hr"] = baseline_hr
            
            if update_data:
                self.client.table("profiles").update(update_data).eq("id", user_id).execute()
        except Exception as e:
            logger.error(f"Error updating baselines: {e}")
