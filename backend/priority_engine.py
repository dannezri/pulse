"""
Moteur de priorité pour calculer les baselines robustes (median/IQR) et détecter les anomalies
Utilisé pour l'interface "Ambient Concierge"

MISE À JOUR v2: Utilise statistiques robustes (median/IQR) au lieu de mean/std
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from supabase_client import SupabaseClient
from lib.stats import (
    compute_robust_stats,
    detect_anomalies,
    RobustStats
)

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
        Calcule les baselines robustes (median/IQR) pour chaque métrique sur les N derniers jours
        
        MISE À JOUR: Utilise statistiques robustes au lieu de mean/std
        
        Args:
            user_id: ID de l'utilisateur
            lookback_days: Nombre de jours à analyser (défaut: 14)
        
        Returns:
            Dict avec structure:
            {
                "hrv": {"median": 65.2, "iqr": 12.5, "p25": 59, "p75": 71, "weight": 3, "count": 42, "confidence": "high"},
                "heart_rate": {"median": 58.1, "iqr": 5.2, "p25": 55, "p75": 60, "weight": 3, "count": 120, "confidence": "high"},
                ...
            }
        """
        try:
            # Calculer la date de début
            start_date = datetime.now() - timedelta(days=lookback_days)
            start_iso = start_date.isoformat()
            
            logger.info(f"Calculating ROBUST baselines for user {user_id} from {start_iso}")
            
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
            
            # Calculer statistiques robustes pour chaque métrique
            baselines = {}
            for metric_type, values in metrics_by_type.items():
                if len(values) >= 2:  # compute_robust_stats nécessite au moins 2 valeurs
                    # Utiliser la fonction centralisée
                    stats = compute_robust_stats(values, include_classical=True)
                    
                    if stats:
                        weight = METRIC_WEIGHTS.get(metric_type, 1)
                        
                        baselines[metric_type] = {
                            "median": stats.median,
                            "iqr": stats.iqr,
                            "p25": stats.p25,
                            "p75": stats.p75,
                            "mean": stats.mean,  # Inclus pour compatibilité/graphiques
                            "std": stats.std,    # Inclus pour compatibilité/graphiques
                            "weight": weight,
                            "count": stats.count,
                            "confidence": stats.confidence
                        }
                        
                        logger.debug(
                            f"{metric_type}: median={stats.median:.2f}, "
                            f"IQR={stats.iqr:.2f}, n={stats.count}, "
                            f"confidence={stats.confidence}"
                        )
            
            logger.info(f"Calculated ROBUST baselines for {len(baselines)} metrics")
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
        Détecte les anomalies en calculant les Z-Scores ROBUSTES
        
        MISE À JOUR: Utilise Z-Score robuste (median/IQR) au lieu de (mean/std)
        
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
                    "z_score_robust": -2.35,
                    "weight": 3,
                    "priority": 7.05,
                    "direction": "below",
                    "baseline": {"median": 65.2, "iqr": 12.5, "p25": 59, "p75": 71}
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
            
            # Convertir baselines dict → RobustStats objects
            baselines_objects = {}
            weights_map = {}
            
            for metric, baseline_dict in baselines.items():
                baselines_objects[metric] = RobustStats(
                    median=baseline_dict['median'],
                    iqr=baseline_dict['iqr'],
                    p25=baseline_dict['p25'],
                    p75=baseline_dict['p75'],
                    mean=baseline_dict.get('mean'),
                    std=baseline_dict.get('std'),
                    count=baseline_dict['count'],
                    confidence=baseline_dict['confidence']
                )
                weights_map[metric] = baseline_dict['weight']
            
            # Utiliser la fonction centralisée detect_anomalies
            anomalies_list = detect_anomalies(
                current_metrics=current_metrics,
                baselines=baselines_objects,
                weights=weights_map,
                threshold_sigma=2.0
            )
            
            # Log
            for anomaly in anomalies_list:
                logger.info(
                    f"Anomaly detected: {anomaly['metric']}={anomaly['value']} "
                    f"(Z_robust={anomaly['z_score_robust']:.2f}, priority={anomaly['priority']:.2f})"
                )
            
            logger.info(f"Found {len(anomalies_list)} anomalies for user {user_id}")
            return anomalies_list
        
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
