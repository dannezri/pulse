"""
Bibliothèque partagée pour statistiques et calculs
"""

from .stats import (
    compute_robust_stats,
    z_score_robust,
    is_anomaly,
    get_anomaly_direction,
    sigmoid,
    ema,
    normalize_to_range,
    percentile_rank,
    compute_multiple_baselines,
    detect_anomalies,
    validate_baseline,
    RobustStats,
    IQR_TO_SIGMA,
    CONFIDENCE_THRESHOLDS
)

__all__ = [
    'compute_robust_stats',
    'z_score_robust',
    'is_anomaly',
    'get_anomaly_direction',
    'sigmoid',
    'ema',
    'normalize_to_range',
    'percentile_rank',
    'compute_multiple_baselines',
    'detect_anomalies',
    'validate_baseline',
    'RobustStats',
    'IQR_TO_SIGMA',
    'CONFIDENCE_THRESHOLDS'
]
