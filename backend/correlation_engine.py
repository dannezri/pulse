"""
Moteur de corrélation simple pour le MVP
Corrèle les données de contexte récentes (daily_context) avec les biométriques récentes (biometrics)
pour générer des insights personnalisés
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from supabase_client import SupabaseClient
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationEngine:
    """
    Moteur de corrélation simple pour générer des insights
    """
    
    def __init__(
        self,
        supabase_client: SupabaseClient,
        llm_client: LLMClient
    ):
        self.supabase = supabase_client
        self.llm = llm_client
    
    def generate_correlated_insight(
        self,
        user_id: str,
        recent_biometrics_count: int = 10,
        recent_context_count: int = 10
    ) -> Optional[Dict]:
        """
        Génère un insight en corrélant les données récentes
        
        Args:
            user_id: ID de l'utilisateur
            recent_biometrics_count: Nombre de biometrics récents à utiliser
            recent_context_count: Nombre de daily_context récents à utiliser
        
        Returns:
            Dict avec 'content', 'correlation_type', 'priority' ou None si erreur
        """
        try:
            # 1. Récupérer les biometrics récents
            logger.info(f"Fetching recent biometrics for user {user_id}")
            recent_biometrics = self._get_recent_biometrics(user_id, recent_biometrics_count)
            
            # 2. Récupérer les daily_context récents
            logger.info(f"Fetching recent daily_context for user {user_id}")
            recent_context = self._get_recent_daily_context(user_id, recent_context_count)
            
            # 3. Vérifier qu'on a assez de données
            if not recent_biometrics and not recent_context:
                logger.warning(f"No data available for user {user_id}")
                # Retourner un insight neutre si pas de données
                return {
                    "content": "Pas assez de données pour générer un insight. Synchronisez vos données de flux et de contexte.",
                    "correlation_type": "insufficient_data",
                    "priority": 1
                }
            
            # Si très peu de données, retourner insight neutre
            if len(recent_biometrics) < 3 and len(recent_context) < 3:
                logger.info(f"Insufficient data for user {user_id}: {len(recent_biometrics)} biometrics, {len(recent_context)} context")
                return {
                    "content": "Collectez plus de données pour obtenir des insights personnalisés.",
                    "correlation_type": "insufficient_data",
                    "priority": 1
                }
            
            # 4. Construire le prompt
            prompt = self._build_correlation_prompt(recent_biometrics, recent_context)
            
            # 5. Appeler le LLM
            logger.info(f"Calling LLM for user {user_id}")
            system_prompt = self._get_system_prompt()
            llm_response = self.llm.generate_insight(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # 6. Extraire les informations de corrélation
            correlation_type = self._detect_correlation_type(recent_biometrics, recent_context)
            priority = self._calculate_priority(recent_biometrics, recent_context)
            
            # 7. Retourner l'insight
            return {
                "content": llm_response["content"],
                "correlation_type": correlation_type,
                "priority": priority,
                "metadata": {
                    "biometrics_count": len(recent_biometrics),
                    "context_count": len(recent_context),
                    "model": llm_response.get("model"),
                    "usage": llm_response.get("usage")
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating correlated insight for user {user_id}: {e}")
            return None
    
    def _get_recent_biometrics(self, user_id: str, limit: int) -> List[Dict]:
        """Récupère les biometrics récents via RPC"""
        try:
            response = self.supabase.client.rpc(
                "get_recent_biometrics",
                {"p_user_id": user_id, "p_limit": limit}
            ).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recent biometrics: {e}")
            return []
    
    def _get_recent_daily_context(self, user_id: str, limit: int) -> List[Dict]:
        """Récupère les daily_context récents via RPC"""
        try:
            response = self.supabase.client.rpc(
                "get_recent_daily_context",
                {"p_user_id": user_id, "p_limit": limit}
            ).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recent daily_context: {e}")
            return []
    
    def _build_correlation_prompt(
        self,
        biometrics: List[Dict],
        context: List[Dict]
    ) -> str:
        """Construit le prompt pour le LLM"""
        prompt_parts = []
        
        prompt_parts.append("Analyse les données suivantes et génère un insight personnalisé en français (max 150 caractères).")
        prompt_parts.append("Format de réponse JSON: {\"insight\": \"texte de l'insight\"}")
        prompt_parts.append("")
        
        # Biometrics récents
        if biometrics:
            prompt_parts.append("=== DONNÉES BIOMÉTRIQUES RÉCENTES ===")
            for bio in biometrics[:5]:  # Limiter à 5 pour ne pas surcharger
                metric_type = bio.get("metric_type", "unknown")
                value = bio.get("value", "N/A")
                measured_at = bio.get("measured_at", "N/A")
                prompt_parts.append(f"- {metric_type}: {value} (mesuré à {measured_at})")
        else:
            prompt_parts.append("=== DONNÉES BIOMÉTRIQUES RÉCENTES ===")
            prompt_parts.append("Aucune donnée biométrique récente disponible.")
        
        prompt_parts.append("")
        
        # Context récent
        if context:
            prompt_parts.append("=== CONTEXTE RÉCENT (Nutrition, Médicaments, Symptômes) ===")
            for ctx in context[:5]:  # Limiter à 5
                category = ctx.get("category", "unknown")
                details = ctx.get("details", {})
                logged_at = ctx.get("logged_at", "N/A")
                prompt_parts.append(f"- {category}: {details} (enregistré à {logged_at})")
        else:
            prompt_parts.append("=== CONTEXTE RÉCENT ===")
            prompt_parts.append("Aucun contexte récent disponible.")
        
        prompt_parts.append("")
        prompt_parts.append("Génère un insight qui corrèle le contexte récent avec les biométriques récentes.")
        prompt_parts.append("Exemple: 'HRV basse après repas riche en glucides → Réduire les glucides le soir'")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Retourne le prompt système pour le LLM"""
        return """Tu es un assistant santé qui génère des insights personnalisés basés sur la corrélation entre le contexte quotidien (nutrition, médicaments, symptômes) et les données biométriques (HR, HRV, sommeil).

Règles:
- Réponds UNIQUEMENT en JSON avec le format: {"insight": "texte"}
- Le texte doit faire maximum 150 caractères
- Sois précis et actionnable
- Utilise un ton bienveillant et professionnel
- Corrèle le contexte récent avec les biométriques récentes
- Si pas assez de données, indique-le clairement"""
    
    def _detect_correlation_type(
        self,
        biometrics: List[Dict],
        context: List[Dict]
    ) -> Optional[str]:
        """Détecte le type de corrélation"""
        if not biometrics or not context:
            return None
        
        # Extraire les catégories de contexte
        context_categories = set(ctx.get("category") for ctx in context)
        
        # Extraire les types de métriques
        metric_types = set(bio.get("metric_type") for bio in biometrics)
        
        # Détecter les corrélations possibles
        if "nutrition" in context_categories and "hrv" in metric_types:
            return "nutrition_hrv"
        elif "nutrition" in context_categories and "hr" in metric_types:
            return "nutrition_hr"
        elif "medication" in context_categories and "sleep" in metric_types:
            return "medication_sleep"
        elif "symptoms" in context_categories and "hr" in metric_types:
            return "symptoms_hr"
        elif "symptoms" in context_categories and "hrv" in metric_types:
            return "symptoms_hrv"
        else:
            return "general"
    
    def _calculate_priority(
        self,
        biometrics: List[Dict],
        context: List[Dict]
    ) -> int:
        """Calcule la priorité de l'insight (1: Normal, 2: Urgent)"""
        # Priorité 2 si on a des anomalies détectées ou des symptômes
        if context:
            for ctx in context:
                if ctx.get("category") == "symptoms":
                    return 2
        
        # Priorité 1 par défaut
        return 1
