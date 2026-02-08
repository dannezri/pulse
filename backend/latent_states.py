"""
Latent States Calculator Module
Calcule les 4 états latents physiologiques (MVP):
- Recovery (récupération)
- Sleep Debt (dette de sommeil)
- Overtrain (surcharge entraînement)
- Infection-like (signature infection)

Tous les calculs en Python (pas SQL) pour v1 - plus facile à débugger
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# BRIQUES COMMUNES (Utilities)
# ============================================

def robust_zscore(x: float, baseline_median: float, baseline_iqr: float) -> float:
    """
    Calculate robust z-score using median and IQR.
    
    Args:
        x: Current value
        baseline_median: User's baseline median
        baseline_iqr: User's baseline IQR (Interquartile Range)
    
    Returns:
        z-score clamped to [-4, +4] range
    """
    if baseline_iqr == 0:
        return 0.0
    
    # IQR ≈ 1.349σ pour distribution normale
    sigma_approx = baseline_iqr / 1.349
    z = (x - baseline_median) / sigma_approx
    
    # Clamp to [-4, +4] pour éviter valeurs extrêmes
    return max(-4.0, min(4.0, z))


def sigmoid(u: float) -> float:
    """
    Sigmoid activation function.
    
    Args:
        u: Input value
    
    Returns:
        Value between 0 and 1
    """
    try:
        return 1.0 / (1.0 + math.exp(-u))
    except OverflowError:
        # Si u très négatif, exp(-u) → inf, donc sigmoid → 0
        return 0.0 if u < 0 else 1.0


def ema(current: float, previous: float, alpha: float = 0.2) -> float:
    """
    Exponential moving average for temporal smoothing.
    
    Args:
        current: Current raw value
        previous: Previous EMA value
        alpha: Smoothing factor (0-1), higher = more reactive
    
    Returns:
        Smoothed value
    """
    return alpha * current + (1.0 - alpha) * previous


# ============================================
# STATE 1: RECOVERY (Récupération)
# ============================================

def calculate_recovery_state(
    hrv_night: Optional[float],
    rhr_night: Optional[float],
    sleep_duration: Optional[float],
    sleep_fragmentation: Optional[float],
    baselines: Dict,
    previous_smoothed: Optional[float] = None
) -> Dict:
    """
    Calculate recovery state (0-1 where 1 = well recovered).
    
    Formula:
    recovery_raw = 0.45*sigmoid(z_hrv/1.2) + 0.25*sigmoid(-z_rhr/1.2) 
                   + 0.20*sigmoid(z_sleep/1.2) + 0.10*sigmoid(-z_frag/1.2)
    
    Args:
        hrv_night: HRV nocturne (ms)
        rhr_night: Rythme cardiaque au repos nocturne (bpm)
        sleep_duration: Durée de sommeil (heures)
        sleep_fragmentation: Score de fragmentation (0-100, plus haut = pire)
        baselines: Dict avec baseline_hrv_median, baseline_hrv_iqr, etc.
        previous_smoothed: Score lissé du jour précédent pour EMA
    
    Returns:
        Dict avec state, score, smoothed_score, confidence, top_factors, etc.
    """
    logger.info("Calculating recovery state...")
    
    # Extraire les baselines
    hrv_baseline_median = baselines.get('baseline_hrv_median', 50.0)
    hrv_baseline_iqr = baselines.get('baseline_hrv_iqr', 15.0)
    rhr_baseline_median = baselines.get('baseline_rhr_median', 60.0)
    rhr_baseline_iqr = baselines.get('baseline_rhr_iqr', 5.0)
    sleep_baseline_median = baselines.get('baseline_sleep_median', 7.5)
    sleep_baseline_iqr = baselines.get('baseline_sleep_iqr', 1.0)
    frag_baseline_median = baselines.get('baseline_fragmentation_median', 20.0)
    frag_baseline_iqr = baselines.get('baseline_fragmentation_iqr', 10.0)
    
    # Calculer les z-scores
    z_hrv = robust_zscore(hrv_night, hrv_baseline_median, hrv_baseline_iqr) if hrv_night else 0.0
    z_rhr = robust_zscore(rhr_night, rhr_baseline_median, rhr_baseline_iqr) if rhr_night else 0.0
    z_sleep = robust_zscore(sleep_duration, sleep_baseline_median, sleep_baseline_iqr) if sleep_duration else 0.0
    z_frag = robust_zscore(sleep_fragmentation, frag_baseline_median, frag_baseline_iqr) if sleep_fragmentation else 0.0
    
    logger.info(f"Z-scores: HRV={z_hrv:.2f}, RHR={z_rhr:.2f}, Sleep={z_sleep:.2f}, Frag={z_frag:.2f}")
    
    # Calculer les composantes du score
    score_parts = []
    top_factors = []
    available_metrics = 0
    
    # HRV (40% du score)
    if hrv_night is not None:
        hrv_part = sigmoid(z_hrv / 1.2)
        score_parts.append(0.45 * hrv_part)
        available_metrics += 1
        top_factors.append({
            "factor": "hrv_below_baseline" if z_hrv < 0 else "hrv_above_baseline",
            "direction": "down" if z_hrv < 0 else "up",
            "weight": 0.45,
            "evidence": {
                "z": round(z_hrv, 2),
                "value": round(hrv_night, 1),
                "baseline": round(hrv_baseline_median, 1)
            }
        })
    
    # RHR (25% du score) - inversé car plus haut = pire
    if rhr_night is not None:
        rhr_part = sigmoid(-z_rhr / 1.2)
        score_parts.append(0.25 * rhr_part)
        available_metrics += 1
        top_factors.append({
            "factor": "rhr_above_baseline" if z_rhr > 0 else "rhr_below_baseline",
            "direction": "up" if z_rhr > 0 else "down",
            "weight": 0.25,
            "evidence": {
                "z": round(z_rhr, 2),
                "value": round(rhr_night, 1),
                "baseline": round(rhr_baseline_median, 1)
            }
        })
    
    # Sleep duration (20% du score)
    if sleep_duration is not None:
        sleep_part = sigmoid(z_sleep / 1.2)
        score_parts.append(0.20 * sleep_part)
        available_metrics += 1
        top_factors.append({
            "factor": "sleep_duration_low" if z_sleep < 0 else "sleep_duration_good",
            "direction": "down" if z_sleep < 0 else "up",
            "weight": 0.20,
            "evidence": {
                "z": round(z_sleep, 2),
                "value": round(sleep_duration, 1),
                "baseline": round(sleep_baseline_median, 1)
            }
        })
    
    # Fragmentation (10% du score) - inversé car plus haut = pire
    if sleep_fragmentation is not None:
        frag_part = sigmoid(-z_frag / 1.2)
        score_parts.append(0.10 * frag_part)
        available_metrics += 1
        top_factors.append({
            "factor": "sleep_fragmentation_high" if z_frag > 0 else "sleep_fragmentation_low",
            "direction": "up" if z_frag > 0 else "down",
            "weight": 0.10,
            "evidence": {
                "z": round(z_frag, 2),
                "value": round(sleep_fragmentation, 1),
                "baseline": round(frag_baseline_median, 1)
            }
        })
    
    # Score brut
    if score_parts:
        score_raw = sum(score_parts)
    else:
        score_raw = 0.5  # Neutral si aucune donnée
    
    # Score lissé (EMA)
    if previous_smoothed is not None:
        smoothed_score = ema(score_raw, previous_smoothed, alpha=0.2)
    else:
        smoothed_score = score_raw  # Bootstrap: premier jour
    
    # Confiance basée sur disponibilité des données
    confidence = min(1.0, available_metrics / 4.0)  # 4 métriques max
    
    # Interprétation
    if smoothed_score >= 0.75:
        interpretation = "bonne"
    elif smoothed_score >= 0.50:
        interpretation = "moyenne"
    else:
        interpretation = "insuffisante"
    
    # Trier les facteurs par poids (descending) et garder top 2
    top_factors.sort(key=lambda x: x['weight'], reverse=True)
    top_factors = top_factors[:2]
    
    logger.info(f"Recovery calculated: raw={score_raw:.3f}, smoothed={smoothed_score:.3f}, interpretation={interpretation}")
    
    return {
        'state': 'recovery',
        'score': round(score_raw, 3),
        'smoothed_score': round(smoothed_score, 3),
        'confidence': round(confidence, 3),
        'interpretation': interpretation,
        'top_factors': top_factors,
        'metadata': {
            'ema': {
                'alpha': 0.2,
                'prev_smoothed': round(previous_smoothed, 3) if previous_smoothed else None,
                'current_raw': round(score_raw, 3),
                'current_smoothed': round(smoothed_score, 3)
            },
            'raw_inputs': {
                'hrv_night': hrv_night,
                'rhr_night': rhr_night,
                'sleep_duration': sleep_duration,
                'sleep_fragmentation': sleep_fragmentation
            },
            'z_scores': {
                'z_hrv': round(z_hrv, 2),
                'z_rhr': round(z_rhr, 2),
                'z_sleep': round(z_sleep, 2),
                'z_frag': round(z_frag, 2)
            }
        }
    }


# ============================================
# STATE 2: SLEEP DEBT (Dette de sommeil)
# ============================================

def calculate_sleep_debt_state(
    sleep_history_7d: List[float],
    baseline_sleep_need: float,
    previous_debt: float = 0.0,
    previous_smoothed: Optional[float] = None
) -> Dict:
    """
    Calculate accumulated sleep debt over 7-14 days.
    
    Formula:
    debt_t = max(0, debt_(t-1) * 0.85 + (sleep_need - sleep_actual))
    score = exp(-debt_t / 3.5)  # 3.5h half-life
    
    Args:
        sleep_history_7d: Liste des durées de sommeil des 7 derniers jours (heures)
        baseline_sleep_need: Besoin de sommeil baseline de l'utilisateur (heures)
        previous_debt: Dette accumulée du jour précédent (heures)
        previous_smoothed: Score lissé du jour précédent pour EMA
    
    Returns:
        Dict avec state, score, smoothed_score, debt_hours, confidence, etc.
    """
    logger.info("Calculating sleep debt state...")
    
    # Calculer la dette accumulée
    # Decay factor 0.85 = perte de 15% par jour (récupération naturelle)
    current_debt = max(0.0, previous_debt * 0.85)
    
    # Ajouter le déficit d'aujourd'hui (si disponible)
    if sleep_history_7d and len(sleep_history_7d) > 0:
        today_sleep = sleep_history_7d[-1]  # Dernier élément = aujourd'hui
        deficit = baseline_sleep_need - today_sleep
        current_debt += max(0.0, deficit)  # Seulement si déficit positif
    
    logger.info(f"Sleep debt: previous={previous_debt:.1f}h, current={current_debt:.1f}h")
    
    # Score basé sur la dette (exp decay avec half-life de 3.5h)
    score_raw = math.exp(-current_debt / 3.5)
    
    # Score lissé (EMA)
    if previous_smoothed is not None:
        smoothed_score = ema(score_raw, previous_smoothed, alpha=0.2)
    else:
        smoothed_score = score_raw
    
    # Confiance basée sur historique disponible
    available_days = len([s for s in sleep_history_7d if s is not None])
    confidence = min(1.0, available_days / 7.0)
    
    # Top factors
    top_factors = [{
        "factor": "accumulated_debt",
        "direction": "up" if current_debt > 1.0 else "neutral",
        "weight": 1.0,
        "evidence": {
            "debt_hours": round(current_debt, 1),
            "nights": available_days,
            "baseline_need": round(baseline_sleep_need, 1)
        }
    }]
    
    logger.info(f"Sleep debt calculated: debt={current_debt:.1f}h, score={smoothed_score:.3f}")
    
    return {
        'state': 'sleep_debt',
        'score': round(score_raw, 3),
        'smoothed_score': round(smoothed_score, 3),
        'debt_hours': round(current_debt, 1),
        'confidence': round(confidence, 3),
        'top_factors': top_factors,
        'metadata': {
            'ema': {
                'alpha': 0.2,
                'prev_debt': round(previous_debt, 1),
                'current_debt': round(current_debt, 1),
                'prev_smoothed': round(previous_smoothed, 3) if previous_smoothed else None,
                'current_smoothed': round(smoothed_score, 3)
            },
            'decay_factor': 0.85,
            'sleep_history_7d': [round(s, 1) if s else None for s in sleep_history_7d],
            'baseline_sleep_need': round(baseline_sleep_need, 1)
        }
    }


# ============================================
# STATE 3: OVERTRAIN (Surcharge entraînement)
# ============================================

def calculate_overtrain_state(
    activity_load_7d: List[float],
    activity_load_28d: List[float],
    hrv_3d_avg: Optional[float],
    rhr_3d_avg: Optional[float],
    baselines: Dict,
    previous_smoothed: Optional[float] = None
) -> Dict:
    """
    Calculate overtraining risk using ACWR (Acute:Chronic Workload Ratio).
    
    Training load calculation (avec cap pour éviter outliers):
    load = min(10, steps/1000) pour MVP
    ou load = min(15, active_minutes/10) si disponible
    
    Formula:
    acwr = mean(load_7d) / (mean(load_28d) + epsilon)
    score = 0.55*sigmoid((acwr-1.2)/0.2) + 0.25*sigmoid(-z_hrv_3d) + 0.20*sigmoid(z_rhr_3d)
    
    Args:
        activity_load_7d: Charges d'activité des 7 derniers jours
        activity_load_28d: Charges d'activité des 28 derniers jours
        hrv_3d_avg: Moyenne HRV des 3 derniers jours
        rhr_3d_avg: Moyenne RHR des 3 derniers jours
        baselines: Dict avec baseline_hrv, baseline_rhr
        previous_smoothed: Score lissé du jour précédent
    
    Returns:
        Dict avec state, score, acwr, interpretation, etc.
    """
    logger.info("Calculating overtrain state...")
    
    # Calculer moyennes des loads
    mean_load_7d = sum(activity_load_7d) / len(activity_load_7d) if activity_load_7d else 0.0
    mean_load_28d = sum(activity_load_28d) / len(activity_load_28d) if activity_load_28d else 0.0
    
    # ACWR avec epsilon pour éviter division par zéro
    epsilon = 0.1
    acwr = mean_load_7d / (mean_load_28d + epsilon)
    
    logger.info(f"ACWR: {acwr:.2f} (7d={mean_load_7d:.1f}, 28d={mean_load_28d:.1f})")
    
    # Composante ACWR (55% du score)
    # acwr > 1.2 = surcharge, sigmoid centré sur 1.2
    acwr_part = 0.55 * sigmoid((acwr - 1.2) / 0.2)
    
    # Composantes physiologiques
    score_parts = [acwr_part]
    top_factors = [{
        "factor": "acwr_elevated" if acwr > 1.2 else "acwr_normal",
        "direction": "up" if acwr > 1.2 else "neutral",
        "weight": 0.55,
        "evidence": {
            "acwr": round(acwr, 2),
            "threshold": 1.2,
            "7d_avg": round(mean_load_7d, 1),
            "28d_avg": round(mean_load_28d, 1)
        }
    }]
    
    # HRV supprimé (25% du score)
    if hrv_3d_avg is not None:
        hrv_baseline_median = baselines.get('baseline_hrv_median', 50.0)
        hrv_baseline_iqr = baselines.get('baseline_hrv_iqr', 15.0)
        z_hrv_3d = robust_zscore(hrv_3d_avg, hrv_baseline_median, hrv_baseline_iqr)
        hrv_part = 0.25 * sigmoid(-z_hrv_3d / 1.0)  # Négatif car HRV bas = mauvais
        score_parts.append(hrv_part)
        top_factors.append({
            "factor": "hrv_suppressed_3d",
            "direction": "down" if z_hrv_3d < 0 else "up",
            "weight": 0.25,
            "evidence": {
                "z": round(z_hrv_3d, 2),
                "value": round(hrv_3d_avg, 1),
                "baseline": round(hrv_baseline_median, 1)
            }
        })
    
    # RHR élevé (20% du score)
    if rhr_3d_avg is not None:
        rhr_baseline_median = baselines.get('baseline_rhr_median', 60.0)
        rhr_baseline_iqr = baselines.get('baseline_rhr_iqr', 5.0)
        z_rhr_3d = robust_zscore(rhr_3d_avg, rhr_baseline_median, rhr_baseline_iqr)
        rhr_part = 0.20 * sigmoid(z_rhr_3d / 1.0)  # Positif car RHR haut = mauvais
        score_parts.append(rhr_part)
        top_factors.append({
            "factor": "rhr_elevated_3d",
            "direction": "up" if z_rhr_3d > 0 else "down",
            "weight": 0.20,
            "evidence": {
                "z": round(z_rhr_3d, 2),
                "value": round(rhr_3d_avg, 1),
                "baseline": round(rhr_baseline_median, 1)
            }
        })
    
    # Score brut
    score_raw = sum(score_parts)
    
    # Score lissé
    if previous_smoothed is not None:
        smoothed_score = ema(score_raw, previous_smoothed, alpha=0.2)
    else:
        smoothed_score = score_raw
    
    # Interprétation
    if smoothed_score >= 0.7:
        interpretation = "surcharge"
    elif smoothed_score >= 0.4:
        interpretation = "surveiller"
    else:
        interpretation = "ok"
    
    # Confiance
    available_metrics = 1  # ACWR toujours disponible
    if hrv_3d_avg is not None:
        available_metrics += 1
    if rhr_3d_avg is not None:
        available_metrics += 1
    confidence = min(1.0, available_metrics / 3.0)
    
    # Top 2 facteurs
    top_factors.sort(key=lambda x: x['weight'], reverse=True)
    top_factors = top_factors[:2]
    
    logger.info(f"Overtrain calculated: score={smoothed_score:.3f}, acwr={acwr:.2f}, interpretation={interpretation}")
    
    return {
        'state': 'overtrain',
        'score': round(score_raw, 3),
        'smoothed_score': round(smoothed_score, 3),
        'acwr': round(acwr, 2),
        'confidence': round(confidence, 3),
        'interpretation': interpretation,
        'top_factors': top_factors,
        'metadata': {
            'ema': {
                'alpha': 0.2,
                'prev_smoothed': round(previous_smoothed, 3) if previous_smoothed else None,
                'current_smoothed': round(smoothed_score, 3)
            },
            'load_windows': {
                '7d_loads': [round(l, 1) for l in activity_load_7d],
                '28d_loads': [round(l, 1) for l in activity_load_28d],
                '7d_avg': round(mean_load_7d, 1),
                '28d_avg': round(mean_load_28d, 1)
            },
            'load_calculation': {
                'method': 'steps_or_active_minutes_capped',
                'cap': '10 (steps) or 15 (active_minutes)'
            }
        }
    }


# ============================================
# STATE 4: INFECTION-LIKE (Signature infection)
# ============================================

def calculate_infection_state(
    rhr_night: Optional[float],
    hrv_night: Optional[float],
    sleep_fragmentation: Optional[float],
    baselines: Dict,
    persistent_2_days: bool = False,
    sleep_debt_hours: float = 0.0,
    overtrain_score: float = 0.0,
    previous_smoothed: Optional[float] = None
) -> Dict:
    """
    Detect infection-like physiological signature using proxies.
    
    Uses RHR↑ + HRV↓ + fragmentation↑ as proxies for temp + resp + inflammation.
    
    Formula:
    inf_raw = 0.40*sigmoid(z_rhr/1.0) + 0.40*sigmoid(-z_hrv/1.0) + 0.20*sigmoid(z_frag/1.0)
    
    Guard rails (évite faux positifs):
    1. Requires >= 2 signals over threshold
    2. Requires persistence >= 2 days
    3. Apply penalty if sleep debt > 3h: inf_raw *= 0.8
    4. Apply penalty if overtrain > 0.7: inf_raw *= 0.85
    
    Args:
        rhr_night: Rythme cardiaque repos nocturne
        hrv_night: HRV nocturne
        sleep_fragmentation: Score fragmentation
        baselines: Dict avec baselines
        persistent_2_days: True si pattern présent depuis 2+ jours
        sleep_debt_hours: Dette de sommeil actuelle (pour pénalité confounding)
        overtrain_score: Score surcharge actuel (pour pénalité confounding)
        previous_smoothed: Score lissé précédent
    
    Returns:
        Dict avec state, score, signals_triggered, persistent, etc.
    """
    logger.info("Calculating infection-like state...")
    
    # Extraire baselines
    rhr_baseline_median = baselines.get('baseline_rhr_median', 60.0)
    rhr_baseline_iqr = baselines.get('baseline_rhr_iqr', 5.0)
    hrv_baseline_median = baselines.get('baseline_hrv_median', 50.0)
    hrv_baseline_iqr = baselines.get('baseline_hrv_iqr', 15.0)
    frag_baseline_median = baselines.get('baseline_fragmentation_median', 20.0)
    frag_baseline_iqr = baselines.get('baseline_fragmentation_iqr', 10.0)
    
    # Calculer z-scores
    z_rhr = robust_zscore(rhr_night, rhr_baseline_median, rhr_baseline_iqr) if rhr_night else 0.0
    z_hrv = robust_zscore(hrv_night, hrv_baseline_median, hrv_baseline_iqr) if hrv_night else 0.0
    z_frag = robust_zscore(sleep_fragmentation, frag_baseline_median, frag_baseline_iqr) if sleep_fragmentation else 0.0
    
    logger.info(f"Infection z-scores: RHR={z_rhr:.2f}, HRV={z_hrv:.2f}, Frag={z_frag:.2f}")
    
    # Calculer composantes
    score_parts = []
    top_factors = []
    signals_over_threshold = 0
    threshold = 1.5  # z-score threshold pour "signal fort"
    
    # RHR spike (40%)
    if rhr_night is not None:
        rhr_part = 0.40 * sigmoid(z_rhr / 1.0)
        score_parts.append(rhr_part)
        if z_rhr > threshold:
            signals_over_threshold += 1
        top_factors.append({
            "factor": "rhr_spike",
            "direction": "up" if z_rhr > 0 else "neutral",
            "weight": 0.40,
            "evidence": {
                "z": round(z_rhr, 2),
                "value": round(rhr_night, 1),
                "baseline": round(rhr_baseline_median, 1)
            }
        })
    
    # HRV drop (40%)
    if hrv_night is not None:
        hrv_part = 0.40 * sigmoid(-z_hrv / 1.0)  # Négatif car HRV bas = mauvais
        score_parts.append(hrv_part)
        if z_hrv < -threshold:
            signals_over_threshold += 1
        top_factors.append({
            "factor": "hrv_drop",
            "direction": "down" if z_hrv < 0 else "neutral",
            "weight": 0.40,
            "evidence": {
                "z": round(z_hrv, 2),
                "value": round(hrv_night, 1),
                "baseline": round(hrv_baseline_median, 1)
            }
        })
    
    # Fragmentation (20%)
    if sleep_fragmentation is not None:
        frag_part = 0.20 * sigmoid(z_frag / 1.0)
        score_parts.append(frag_part)
        if z_frag > threshold:
            signals_over_threshold += 1
        top_factors.append({
            "factor": "sleep_fragmentation",
            "direction": "up" if z_frag > 0 else "neutral",
            "weight": 0.20,
            "evidence": {
                "z": round(z_frag, 2),
                "value": round(sleep_fragmentation, 1),
                "baseline": round(frag_baseline_median, 1)
            }
        })
    
    # Score brut
    score_raw = sum(score_parts) if score_parts else 0.0
    
    # GUARD RAILS: Pénalités pour confounding states
    penalties_applied = []
    original_score = score_raw
    
    # Pénalité dette de sommeil
    if sleep_debt_hours > 3.0:
        score_raw *= 0.8
        penalties_applied.append('sleep_debt')
        logger.info(f"Applied sleep debt penalty: {original_score:.3f} -> {score_raw:.3f}")
    
    # Pénalité surcharge
    if overtrain_score > 0.7:
        score_raw *= 0.85
        penalties_applied.append('overtrain')
        logger.info(f"Applied overtrain penalty: {score_raw:.3f} -> {score_raw:.3f}")
    
    # GUARD RAIL: Require >= 2 signals
    if signals_over_threshold < 2:
        score_raw *= 0.5
        logger.info(f"Applied low signals penalty: only {signals_over_threshold}/3 signals strong")
    
    # GUARD RAIL: Require persistence
    if not persistent_2_days:
        score_raw *= 0.7
        logger.info("Applied non-persistent penalty")
    
    # Score lissé (alpha plus élevé pour réactivité aux changements)
    if previous_smoothed is not None:
        smoothed_score = ema(score_raw, previous_smoothed, alpha=0.3)
    else:
        smoothed_score = score_raw
    
    # Confiance
    available_metrics = len([x for x in [rhr_night, hrv_night, sleep_fragmentation] if x is not None])
    confidence = min(1.0, available_metrics / 3.0)
    if penalties_applied:
        confidence *= 0.8  # Réduire confiance si pénalités (ambiguïté)
    
    # Top 2 facteurs
    top_factors.sort(key=lambda x: x['weight'], reverse=True)
    top_factors = top_factors[:2]
    
    logger.info(f"Infection calculated: score={smoothed_score:.3f}, signals={signals_over_threshold}/3, persistent={persistent_2_days}, penalties={penalties_applied}")
    
    return {
        'state': 'infection_like',
        'score': round(score_raw, 3),
        'smoothed_score': round(smoothed_score, 3),
        'confidence': round(confidence, 3),
        'signals_triggered': signals_over_threshold,
        'persistent': persistent_2_days,
        'top_factors': top_factors,
        'metadata': {
            'ema': {
                'alpha': 0.3,  # Plus réactif pour infection
                'prev_smoothed': round(previous_smoothed, 3) if previous_smoothed else None,
                'current_smoothed': round(smoothed_score, 3)
            },
            'persistence': {
                'days': 2 if persistent_2_days else 1,
                'threshold': 2
            },
            'guard_rails': {
                'min_signals': 2,
                'signals_over_threshold': signals_over_threshold,
                'confounding_penalties': {
                    'sleep_debt_penalty': 0.8,
                    'overtrain_penalty': 0.85,
                    'final_multiplier': round(score_raw / original_score, 2) if original_score > 0 else 1.0
                }
            },
            'confounding_states': {
                'sleep_debt_hours': round(sleep_debt_hours, 1),
                'overtrain_score': round(overtrain_score, 3),
                'penalties_applied': penalties_applied
            },
            'z_scores': {
                'z_rhr': round(z_rhr, 2),
                'z_hrv': round(z_hrv, 2),
                'z_frag': round(z_frag, 2)
            }
        }
    }
