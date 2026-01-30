"""
Bibliothèque centralisée pour statistiques robustes

Utilisée par:
- baseline_calculator.py (calcul des baselines)
- anomaly_detector.py (détection d'anomalies)
- latent_states.py (calcul des états latents)

Toutes les statistiques utilisent les méthodes robustes (median/IQR)
pour résister aux outliers.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# ============================================
# CONSTANTS
# ============================================

# Pour convertir IQR en équivalent sigma (distribution normale)
# IQR ≈ 1.349 * σ pour une distribution normale
IQR_TO_SIGMA = 1.349

# Seuils de confiance basés sur sample_count
CONFIDENCE_THRESHOLDS = {
    'high': 60,    # >= 60 points
    'medium': 30,  # 30-59 points
    'low': 10      # 10-29 points
}


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class RobustStats:
    """
    Statistiques robustes d'un échantillon
    """
    # Statistiques robustes (principal)
    median: float
    iqr: float
    p25: float
    p75: float
    
    # Statistiques classiques (optionnel)
    mean: Optional[float] = None
    std: Optional[float] = None
    
    # Métadonnées
    count: int = 0
    confidence: str = 'low'
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return {
            'median': round(self.median, 2),
            'iqr': round(self.iqr, 2),
            'p25': round(self.p25, 2),
            'p75': round(self.p75, 2),
            'mean': round(self.mean, 2) if self.mean else None,
            'std': round(self.std, 2) if self.std else None,
            'count': self.count,
            'confidence': self.confidence
        }


# ============================================
# CORE FUNCTIONS
# ============================================

def compute_robust_stats(
    values: List[float],
    include_classical: bool = True
) -> Optional[RobustStats]:
    """
    Calcule statistiques robustes (median/IQR) d'un échantillon
    
    Args:
        values: Liste de valeurs numériques
        include_classical: Inclure mean/std (optionnel)
    
    Returns:
        RobustStats ou None si échantillon trop petit
    
    Example:
        >>> stats = compute_robust_stats([45, 50, 52, 58, 60, 65, 70, 72, 75, 80])
        >>> print(stats.median)  # 62.5
        >>> print(stats.iqr)     # 18.75
    """
    if not values or len(values) < 2:
        logger.warning(f"Not enough values: {len(values) if values else 0}")
        return None
    
    # Filtrer valeurs invalides
    clean_values = [v for v in values if v is not None and np.isfinite(v)]
    
    if len(clean_values) < 2:
        logger.warning(f"Not enough valid values after filtering: {len(clean_values)}")
        return None
    
    arr = np.array(clean_values)
    
    # Statistiques robustes
    median = float(np.median(arr))
    p25 = float(np.percentile(arr, 25))
    p75 = float(np.percentile(arr, 75))
    iqr = p75 - p25
    
    # Éviter IQR = 0 (tous les points identiques)
    if iqr == 0:
        # Utiliser un IQR minimum basé sur la médiane
        iqr = max(median * 0.01, 0.1)  # 1% de la médiane ou 0.1 minimum
        logger.warning(f"IQR was 0, using minimum: {iqr}")
    
    # Statistiques classiques (optionnel)
    mean = None
    std = None
    if include_classical:
        mean = float(np.mean(arr))
        std = float(np.std(arr))
    
    # Confiance basée sur le nombre de points
    count = len(clean_values)
    if count >= CONFIDENCE_THRESHOLDS['high']:
        confidence = 'high'
    elif count >= CONFIDENCE_THRESHOLDS['medium']:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return RobustStats(
        median=median,
        iqr=iqr,
        p25=p25,
        p75=p75,
        mean=mean,
        std=std,
        count=count,
        confidence=confidence
    )


def z_score_robust(
    value: float,
    baseline: RobustStats
) -> float:
    """
    Calcule Z-Score robuste
    
    Z_robust = (x - median) / (IQR / 1.349)
    
    Le diviseur 1.349 convertit IQR en équivalent sigma pour
    rendre Z_robust comparable au Z classique.
    
    Args:
        value: Valeur à évaluer
        baseline: Baseline robuste
    
    Returns:
        Z-score robuste (float)
    
    Example:
        >>> baseline = RobustStats(median=65, iqr=12, p25=59, p75=71, count=50)
        >>> z = z_score_robust(45, baseline)
        >>> print(z)  # -2.25 (2.25 sigma en dessous de la médiane)
    """
    if baseline.iqr == 0:
        logger.warning("IQR is 0, cannot calculate z-score")
        return 0.0
    
    # Sigma équivalent
    sigma_equivalent = baseline.iqr / IQR_TO_SIGMA
    
    # Z-score robuste
    z = (value - baseline.median) / sigma_equivalent
    
    return z


def is_anomaly(
    value: float,
    baseline: RobustStats,
    threshold_sigma: float = 2.0
) -> bool:
    """
    Détermine si une valeur est une anomalie
    
    Args:
        value: Valeur à évaluer
        baseline: Baseline robuste
        threshold_sigma: Seuil en sigma (défaut: 2.0)
    
    Returns:
        True si anomalie détectée
    
    Example:
        >>> baseline = RobustStats(median=65, iqr=12, p25=59, p75=71, count=50)
        >>> is_anomaly(45, baseline)  # True (trop bas)
        >>> is_anomaly(63, baseline)  # False (normal)
    """
    z = z_score_robust(value, baseline)
    return abs(z) > threshold_sigma


def get_anomaly_direction(
    value: float,
    baseline: RobustStats
) -> str:
    """
    Détermine la direction d'une anomalie
    
    Returns:
        'above' | 'below' | 'normal'
    """
    z = z_score_robust(value, baseline)
    
    if z > 2.0:
        return 'above'
    elif z < -2.0:
        return 'below'
    else:
        return 'normal'


# ============================================
# HELPER FUNCTIONS
# ============================================

def sigmoid(z: float, scale: float = 1.0) -> float:
    """
    Sigmoid transformation pour normaliser Z-scores
    
    Utilisé par les états latents pour convertir Z-scores
    en scores 0-1.
    
    Args:
        z: Z-score
        scale: Facteur d'échelle (défaut: 1.0)
    
    Returns:
        Valeur entre 0 et 1
    
    Example:
        >>> sigmoid(0)     # 0.5
        >>> sigmoid(2)     # 0.88
        >>> sigmoid(-2)    # 0.12
    """
    return 1.0 / (1.0 + np.exp(-z / scale))


def ema(
    current: float,
    previous: Optional[float],
    alpha: float = 0.3
) -> float:
    """
    Exponential Moving Average
    
    Utilisé pour lisser les scores des états latents.
    
    Args:
        current: Valeur actuelle
        previous: Valeur précédente (None si première)
        alpha: Facteur de lissage (0-1, défaut: 0.3)
    
    Returns:
        Valeur lissée
    
    Example:
        >>> ema(0.8, 0.6, alpha=0.3)  # 0.66
        >>> ema(0.8, None, alpha=0.3)  # 0.8 (première valeur)
    """
    if previous is None:
        return current
    
    return alpha * current + (1 - alpha) * previous


def normalize_to_range(
    value: float,
    min_val: float,
    max_val: float,
    target_min: float = 0.0,
    target_max: float = 1.0
) -> float:
    """
    Normalise une valeur dans une plage cible
    
    Args:
        value: Valeur à normaliser
        min_val: Minimum de la plage source
        max_val: Maximum de la plage source
        target_min: Minimum de la plage cible
        target_max: Maximum de la plage cible
    
    Returns:
        Valeur normalisée
    
    Example:
        >>> normalize_to_range(50, 0, 100, 0, 1)  # 0.5
        >>> normalize_to_range(75, 0, 100, 0, 1)  # 0.75
    """
    if max_val == min_val:
        return target_min
    
    normalized = (value - min_val) / (max_val - min_val)
    scaled = normalized * (target_max - target_min) + target_min
    
    # Clamp dans la plage cible
    return max(target_min, min(target_max, scaled))


def percentile_rank(
    value: float,
    baseline: RobustStats
) -> float:
    """
    Calcule le percentile d'une valeur par rapport à une baseline
    
    Utilise une approximation gaussienne basée sur le Z-score robuste.
    
    Args:
        value: Valeur à évaluer
        baseline: Baseline robuste
    
    Returns:
        Percentile (0-100)
    
    Example:
        >>> baseline = RobustStats(median=65, iqr=12, p25=59, p75=71, count=50)
        >>> percentile_rank(65, baseline)  # ~50 (médiane)
        >>> percentile_rank(71, baseline)  # ~75 (Q3)
    """
    # Cas spéciaux
    if value <= baseline.p25:
        return 25.0 * (value / baseline.p25) if baseline.p25 > 0 else 0.0
    elif value >= baseline.p75:
        return 75.0 + 25.0 * ((value - baseline.p75) / (baseline.p75 * 0.5))
    elif value <= baseline.median:
        # Entre P25 et médiane
        return 25.0 + 25.0 * ((value - baseline.p25) / (baseline.median - baseline.p25))
    else:
        # Entre médiane et P75
        return 50.0 + 25.0 * ((value - baseline.median) / (baseline.p75 - baseline.median))


# ============================================
# BATCH OPERATIONS
# ============================================

def compute_multiple_baselines(
    data: Dict[str, List[float]],
    include_classical: bool = True
) -> Dict[str, RobustStats]:
    """
    Calcule les baselines pour plusieurs métriques en une seule fois
    
    Args:
        data: Dict {metric_name: [values]}
        include_classical: Inclure mean/std
    
    Returns:
        Dict {metric_name: RobustStats}
    
    Example:
        >>> data = {
        ...     'hrv': [45, 50, 55, 60, 65, 70],
        ...     'heart_rate': [60, 62, 65, 68, 70, 72]
        ... }
        >>> baselines = compute_multiple_baselines(data)
        >>> print(baselines['hrv'].median)
    """
    baselines = {}
    
    for metric_name, values in data.items():
        try:
            stats = compute_robust_stats(values, include_classical)
            if stats:
                baselines[metric_name] = stats
            else:
                logger.warning(f"Failed to compute baseline for {metric_name}")
        except Exception as e:
            logger.error(f"Error computing baseline for {metric_name}: {e}")
    
    return baselines


def detect_anomalies(
    current_metrics: Dict[str, float],
    baselines: Dict[str, RobustStats],
    weights: Optional[Dict[str, float]] = None,
    threshold_sigma: float = 2.0
) -> List[Dict]:
    """
    Détecte les anomalies pour plusieurs métriques
    
    Args:
        current_metrics: Dict {metric: value}
        baselines: Dict {metric: RobustStats}
        weights: Dict {metric: weight} (optionnel)
        threshold_sigma: Seuil de détection
    
    Returns:
        Liste d'anomalies triées par priorité
    
    Example:
        >>> current = {'hrv': 45, 'heart_rate': 85}
        >>> baselines = {...}
        >>> anomalies = detect_anomalies(current, baselines)
        >>> for a in anomalies:
        ...     print(f"{a['metric']}: {a['z_score']:.2f}σ")
    """
    anomalies = []
    
    # Poids par défaut
    default_weights = {
        'hrv': 3,
        'heart_rate': 2,
        'sleep_duration': 2,
        'body_temperature': 2,
        'spo2': 2,
        'stress': 1,
        'glucose': 1,
        'steps': 1
    }
    weights = weights or default_weights
    
    for metric, value in current_metrics.items():
        if metric not in baselines:
            continue
        
        baseline = baselines[metric]
        z = z_score_robust(value, baseline)
        
        # Filtrer: |Z| > threshold
        if abs(z) > threshold_sigma:
            weight = weights.get(metric, 1)
            priority = abs(z) * weight
            direction = 'above' if z > 0 else 'below'
            
            anomalies.append({
                'metric': metric,
                'value': round(value, 2),
                'z_score_robust': round(z, 2),
                'weight': weight,
                'priority': round(priority, 2),
                'direction': direction,
                'baseline': baseline.to_dict()
            })
    
    # Trier par priorité décroissante
    anomalies.sort(key=lambda x: x['priority'], reverse=True)
    
    return anomalies


# ============================================
# VALIDATION
# ============================================

def validate_baseline(baseline: RobustStats) -> bool:
    """
    Valide qu'une baseline est cohérente
    
    Vérifie:
    - median, IQR, p25, p75 sont positifs (ou nuls pour certaines métriques)
    - p25 <= median <= p75
    - IQR = p75 - p25
    """
    try:
        # Vérifier ordre des percentiles
        if not (baseline.p25 <= baseline.median <= baseline.p75):
            logger.error(f"Invalid percentile order: p25={baseline.p25}, median={baseline.median}, p75={baseline.p75}")
            return False
        
        # Vérifier IQR
        expected_iqr = baseline.p75 - baseline.p25
        if abs(baseline.iqr - expected_iqr) > 0.01:
            logger.error(f"Invalid IQR: expected {expected_iqr}, got {baseline.iqr}")
            return False
        
        # Vérifier count
        if baseline.count < 2:
            logger.error(f"Invalid count: {baseline.count}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating baseline: {e}")
        return False


# ============================================
# LOGGING HELPERS
# ============================================

def log_baseline_stats(metric_name: str, stats: RobustStats):
    """Log détaillé des statistiques d'une baseline"""
    logger.info(
        f"Baseline {metric_name}: "
        f"median={stats.median:.2f}, "
        f"IQR={stats.iqr:.2f} "
        f"[{stats.p25:.2f} - {stats.p75:.2f}], "
        f"n={stats.count}, "
        f"confidence={stats.confidence}"
    )


def log_anomaly(anomaly: Dict):
    """Log détaillé d'une anomalie"""
    logger.info(
        f"Anomaly detected: "
        f"{anomaly['metric']}={anomaly['value']} "
        f"(Z={anomaly['z_score_robust']:.2f}σ, "
        f"priority={anomaly['priority']:.2f}, "
        f"direction={anomaly['direction']})"
    )


# ============================================
# MAIN (pour tests)
# ============================================

if __name__ == "__main__":
    # Configuration logging
    logging.basicConfig(level=logging.INFO)
    
    # Test basique
    print("=== Test RobustStats ===")
    values = [45, 50, 52, 58, 60, 65, 70, 72, 75, 80]
    stats = compute_robust_stats(values)
    
    if stats:
        print(f"Median: {stats.median}")
        print(f"IQR: {stats.iqr}")
        print(f"P25-P75: [{stats.p25}, {stats.p75}]")
        print(f"Count: {stats.count}")
        print(f"Confidence: {stats.confidence}")
        
        # Test Z-score
        print("\n=== Test Z-Score ===")
        test_values = [45, 62, 80]
        for val in test_values:
            z = z_score_robust(val, stats)
            direction = get_anomaly_direction(val, stats)
            print(f"Value {val}: Z={z:.2f}σ, direction={direction}")
        
        # Test anomalies
        print("\n=== Test Anomaly Detection ===")
        current_metrics = {'hrv': 45, 'heart_rate': 85}
        baselines_dict = {'hrv': stats, 'heart_rate': stats}
        anomalies = detect_anomalies(current_metrics, baselines_dict)
        for a in anomalies:
            log_anomaly(a)
    
    print("\n=== Tests completed ===")
