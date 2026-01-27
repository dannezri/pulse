"""
Moteur de priorité pour calculer les baselines (μ, σ) et détecter les anomalies
Utilisé pour l'interface "Ambient Concierge"
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

from supabase_client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration des poids par métrique
METRIC_WEIGHTS = {
    # Poids 3 (Critique)
    "hrv": 3,
    "heart_rate": 3,
    "body_temperature": 3,
    "sleep_duration": 3,
    "sleep": 3,
    
    # Poids 2 (Important)
    "active_calories": 2,
    "stress": 2,
    "glucose": 2,
    "spo2": 2,
    
    # Poids 1 (Info)
    "steps": 1,
    "calories": 1,
    "water": 1,
    "distance": 1,
    "floors_climbed": 1,
    "weight": 1,
    "respiratory_rate": 1,
    "caffeine": 1,
}


class PriorityEngine:
    """
    Moteur de priorité pour calculer les baselines et détecter les anomalies
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
    
    def calculate_baselines(
        self,
        user_id: str,
        lookback_days: int = 14
    ) -> Dict[str, Dict]:
        """
        Calcule les baselines (μ, σ) pour chaque métrique sur les N derniers jours
        
        Args:
            user_id: ID de l'utilisateur
            lookback_days: Nombre de jours à analyser (défaut: 14)
        
        Returns:
            Dict avec structure:
            {
                "hrv": {"mean": 65.2, "std": 8.5, "weight": 3, "count": 42},
                "heart_rate": {"mean": 58.1, "std": 3.2, "weight": 3, "count": 120},
                ...
            }
        """
        try:
            # Calculer la date de début
            start_date = datetime.now() - timedelta(days=lookback_days)
            start_iso = start_date.isoformat()
            
            logger.info(f"Calculating baselines for user {user_id} from {start_iso}")
            
            # Récupérer toutes les biometrics des N derniers jours
            response = self.supabase.client.from_("biometrics").select("*").eq(
                "user_id", user_id
            ).gte("recorded_at", start_iso).execute()
            
            biometrics = response.data or []
            
            if not biometrics:
                logger.warning(f"No biometrics found for user {user_id}")
                return {}
            
            logger.info(f"Found {len(biometrics)} biometrics records")
            
            # Grouper par metric_type
            metrics_by_type: Dict[str, List[float]] = {}
            for bio in biometrics:
                metric_type = bio.get("metric_type")
                value = bio.get("value")
                
                if metric_type and value is not None:
                    if metric_type not in metrics_by_type:
                        metrics_by_type[metric_type] = []
                    metrics_by_type[metric_type].append(float(value))
            
            # Calculer μ et σ pour chaque métrique
            baselines = {}
            for metric_type, values in metrics_by_type.items():
                if len(values) >= 3:  # Besoin d'au moins 3 valeurs pour calculer σ
                    mean = statistics.mean(values)
                    std = statistics.stdev(values) if len(values) > 1 else 0
                    weight = METRIC_WEIGHTS.get(metric_type, 1)
                    
                    baselines[metric_type] = {
                        "mean": round(mean, 2),
                        "std": round(std, 2),
                        "weight": weight,
                        "count": len(values)
                    }
                    
                    logger.debug(
                        f"{metric_type}: μ={mean:.2f}, σ={std:.2f}, n={len(values)}"
                    )
            
            logger.info(f"Calculated baselines for {len(baselines)} metrics")
            return baselines
        
        except Exception as e:
            logger.error(f"Error calculating baselines for user {user_id}: {e}")
            return {}
    
    def detect_anomalies(
        self,
        user_id: str,
        current_metrics: Dict[str, float],
        baselines: Optional[Dict[str, Dict]] = None
    ) -> List[Dict]:
        """
        Détecte les anomalies en calculant les Z-Scores
        
        Args:
            user_id: ID de l'utilisateur
            current_metrics: Métriques actuelles {"hrv": 45.2, "heart_rate": 72, ...}
            baselines: Baselines pré-calculées (optionnel, sinon recalcule)
        
        Returns:
            Liste d'anomalies triées par priorité décroissante:
            [
                {
                    "metric": "hrv",
                    "value": 45.2,
                    "z_score": -2.35,
                    "weight": 3,
                    "priority": 7.05,
                    "direction": "below",
                    "baseline": {"mean": 65.2, "std": 8.5}
                },
                ...
            ]
        """
        try:
            # Récupérer les baselines si non fournies
            if baselines is None:
                baselines = self.calculate_baselines(user_id)
            
            if not baselines:
                logger.warning(f"No baselines available for user {user_id}")
                return []
            
            anomalies = []
            
            # Calculer le Z-Score pour chaque métrique
            for metric, value in current_metrics.items():
                if metric in baselines:
                    baseline = baselines[metric]
                    mean = baseline["mean"]
                    std = baseline["std"]
                    weight = baseline["weight"]
                    
                    # Éviter division par zéro
                    if std == 0:
                        continue
                    
                    # Calculer Z-Score
                    z_score = (value - mean) / std
                    
                    # Filtrer : garder uniquement |Z| > 2
                    if abs(z_score) > 2:
                        priority = abs(z_score) * weight
                        direction = "above" if z_score > 0 else "below"
                        
                        anomalies.append({
                            "metric": metric,
                            "value": round(value, 2),
                            "z_score": round(z_score, 2),
                            "weight": weight,
                            "priority": round(priority, 2),
                            "direction": direction,
                            "baseline": {
                                "mean": mean,
                                "std": std
                            }
                        })
                        
                        logger.info(
                            f"Anomaly detected: {metric}={value:.2f} "
                            f"(Z={z_score:.2f}, priority={priority:.2f})"
                        )
            
            # Trier par priorité décroissante
            anomalies.sort(key=lambda x: x["priority"], reverse=True)
            
            logger.info(f"Found {len(anomalies)} anomalies for user {user_id}")
            return anomalies
        
        except Exception as e:
            logger.error(f"Error detecting anomalies for user {user_id}: {e}")
            return []
    
    def get_top_anomalies(
        self,
        user_id: str,
        current_metrics: Dict[str, float],
        top_n: int = 3
    ) -> List[Dict]:
        """
        Retourne les top N anomalies
        
        Args:
            user_id: ID de l'utilisateur
            current_metrics: Métriques actuelles
            top_n: Nombre d'anomalies à retourner (défaut: 3)
        
        Returns:
            Liste des top N anomalies
        """
        anomalies = self.detect_anomalies(user_id, current_metrics)
        return anomalies[:top_n]
