"""
Tests unitaires pour lib/stats.py (statistiques robustes)
"""

import pytest
import numpy as np
from backend.lib.stats import (
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
    IQR_TO_SIGMA
)


class TestComputeRobustStats:
    """Tests pour compute_robust_stats()"""
    
    def test_normal_distribution(self):
        """Test avec distribution normale"""
        values = [45, 50, 52, 58, 60, 65, 70, 72, 75, 80]
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.median == pytest.approx(62.5, rel=0.01)
        assert stats.iqr == pytest.approx(18.75, rel=0.01)
        assert stats.p25 == pytest.approx(52.5, rel=0.01)
        assert stats.p75 == pytest.approx(71.25, rel=0.01)
        assert stats.count == 10
        assert stats.confidence == 'low'  # < 30 points
    
    def test_with_outliers(self):
        """Test avec outliers (robustesse)"""
        # Distribution normale + 2 outliers extrêmes
        values = [50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 200, 300]
        stats = compute_robust_stats(values)
        
        # La médiane et IQR ne doivent PAS être affectés par les outliers
        assert stats is not None
        assert stats.median == pytest.approx(59, rel=0.1)
        assert stats.iqr < 20  # IQR reste raisonnable malgré outliers
    
    def test_high_confidence(self):
        """Test avec beaucoup de points (high confidence)"""
        # 70 points
        values = list(range(40, 110))
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.count == 70
        assert stats.confidence == 'high'  # >= 60 points
    
    def test_medium_confidence(self):
        """Test avec 30-59 points (medium confidence)"""
        values = list(range(50, 85))
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.count == 35
        assert stats.confidence == 'medium'
    
    def test_empty_list(self):
        """Test avec liste vide"""
        stats = compute_robust_stats([])
        assert stats is None
    
    def test_single_value(self):
        """Test avec une seule valeur"""
        stats = compute_robust_stats([60])
        assert stats is None  # Pas assez de points
    
    def test_all_same_values(self):
        """Test avec toutes les valeurs identiques"""
        values = [60] * 20
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.median == 60
        # IQR devrait être > 0 (minimum forcé)
        assert stats.iqr > 0
    
    def test_with_none_values(self):
        """Test avec valeurs None mélangées"""
        values = [50, None, 55, 60, None, 65, 70]
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.count == 5  # None filtrés
    
    def test_with_nan_values(self):
        """Test avec NaN"""
        values = [50, 55, np.nan, 60, 65, np.nan, 70]
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.count == 5  # NaN filtrés
    
    def test_with_inf_values(self):
        """Test avec infinity"""
        values = [50, 55, np.inf, 60, 65, -np.inf, 70]
        stats = compute_robust_stats(values)
        
        assert stats is not None
        assert stats.count == 5  # Inf filtrés
    
    def test_include_classical_stats(self):
        """Test avec statistiques classiques incluses"""
        values = [50, 55, 60, 65, 70]
        stats = compute_robust_stats(values, include_classical=True)
        
        assert stats.mean is not None
        assert stats.std is not None
        assert stats.mean == pytest.approx(60, rel=0.01)
    
    def test_exclude_classical_stats(self):
        """Test sans statistiques classiques"""
        values = [50, 55, 60, 65, 70]
        stats = compute_robust_stats(values, include_classical=False)
        
        assert stats.mean is None
        assert stats.std is None


class TestZScoreRobust:
    """Tests pour z_score_robust()"""
    
    def test_value_at_median(self):
        """Z-score à la médiane doit être ~0"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        z = z_score_robust(60, baseline)
        
        assert z == pytest.approx(0, abs=0.01)
    
    def test_value_above_median(self):
        """Z-score positif au-dessus de la médiane"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        z = z_score_robust(72, baseline)
        
        assert z > 0
        # Environ 1.35 sigma au-dessus
        assert z == pytest.approx(1.35, rel=0.1)
    
    def test_value_below_median(self):
        """Z-score négatif en dessous de la médiane"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        z = z_score_robust(48, baseline)
        
        assert z < 0
        # Environ -1.35 sigma en dessous
        assert z == pytest.approx(-1.35, rel=0.1)
    
    def test_iqr_to_sigma_conversion(self):
        """Vérifier la conversion IQR → sigma"""
        baseline = RobustStats(median=60, iqr=13.49, p25=53.26, p75=66.75, count=50)
        
        # Si IQR = 13.49, alors sigma ≈ 13.49 / 1.349 = 10
        # Une valeur à median + 10 devrait avoir Z ≈ 1
        z = z_score_robust(70, baseline)
        assert z == pytest.approx(1.0, rel=0.05)
    
    def test_zero_iqr(self):
        """Z-score avec IQR = 0 (edge case)"""
        baseline = RobustStats(median=60, iqr=0, p25=60, p75=60, count=50)
        z = z_score_robust(65, baseline)
        
        # Devrait retourner 0 (pas de variance)
        assert z == 0


class TestIsAnomaly:
    """Tests pour is_anomaly()"""
    
    def test_clear_anomaly_below(self):
        """Anomalie claire en dessous"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        # 2.5 sigma en dessous = anomalie
        assert is_anomaly(38, baseline) is True
    
    def test_clear_anomaly_above(self):
        """Anomalie claire au-dessus"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        # 2.5 sigma au-dessus = anomalie
        assert is_anomaly(82, baseline) is True
    
    def test_borderline_anomaly(self):
        """Valeur borderline (exactement 2 sigma)"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        # Exactement 2 sigma
        sigma = baseline.iqr / IQR_TO_SIGMA
        value_at_2sigma = baseline.median + (2 * sigma)
        
        # |Z| > 2.0 donc anomalie
        assert is_anomaly(value_at_2sigma + 0.1, baseline) is True
        # |Z| <= 2.0 donc pas anomalie
        assert is_anomaly(value_at_2sigma - 0.1, baseline) is False
    
    def test_normal_value(self):
        """Valeur normale (pas d'anomalie)"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        assert is_anomaly(60, baseline) is False
        assert is_anomaly(58, baseline) is False
        assert is_anomaly(62, baseline) is False
    
    def test_custom_threshold(self):
        """Anomalie avec seuil personnalisé"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        # Avec seuil 3 sigma
        value_at_2_5_sigma = 60 + (2.5 * baseline.iqr / IQR_TO_SIGMA)
        
        assert is_anomaly(value_at_2_5_sigma, baseline, threshold_sigma=2.0) is True
        assert is_anomaly(value_at_2_5_sigma, baseline, threshold_sigma=3.0) is False


class TestGetAnomalyDirection:
    """Tests pour get_anomaly_direction()"""
    
    def test_above_direction(self):
        """Direction 'above'"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        direction = get_anomaly_direction(80, baseline)
        
        assert direction == 'above'
    
    def test_below_direction(self):
        """Direction 'below'"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        direction = get_anomaly_direction(40, baseline)
        
        assert direction == 'below'
    
    def test_normal_direction(self):
        """Direction 'normal'"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        direction = get_anomaly_direction(60, baseline)
        
        assert direction == 'normal'


class TestHelperFunctions:
    """Tests pour fonctions helper"""
    
    def test_sigmoid_zero(self):
        """Sigmoid de 0 = 0.5"""
        assert sigmoid(0) == pytest.approx(0.5, abs=0.01)
    
    def test_sigmoid_positive(self):
        """Sigmoid positif > 0.5"""
        assert sigmoid(2) > 0.5
        assert sigmoid(2) == pytest.approx(0.88, rel=0.05)
    
    def test_sigmoid_negative(self):
        """Sigmoid négatif < 0.5"""
        assert sigmoid(-2) < 0.5
        assert sigmoid(-2) == pytest.approx(0.12, rel=0.05)
    
    def test_sigmoid_scale(self):
        """Sigmoid avec scale différent"""
        # Scale plus grand = courbe plus douce
        assert sigmoid(2, scale=2.0) < sigmoid(2, scale=1.0)
    
    def test_ema_first_value(self):
        """EMA avec première valeur (previous = None)"""
        assert ema(0.8, None, alpha=0.3) == 0.8
    
    def test_ema_smoothing(self):
        """EMA lissage normal"""
        result = ema(0.8, 0.6, alpha=0.3)
        
        # result = 0.3 * 0.8 + 0.7 * 0.6 = 0.24 + 0.42 = 0.66
        assert result == pytest.approx(0.66, abs=0.01)
    
    def test_normalize_to_range(self):
        """Normalisation dans plage [0, 1]"""
        assert normalize_to_range(50, 0, 100, 0, 1) == pytest.approx(0.5)
        assert normalize_to_range(0, 0, 100, 0, 1) == pytest.approx(0)
        assert normalize_to_range(100, 0, 100, 0, 1) == pytest.approx(1)
    
    def test_normalize_custom_range(self):
        """Normalisation dans plage custom"""
        result = normalize_to_range(50, 0, 100, 10, 20)
        
        # 50% de [0-100] → 50% de [10-20] = 15
        assert result == pytest.approx(15, abs=0.01)
    
    def test_percentile_rank_at_median(self):
        """Percentile rank à la médiane"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        rank = percentile_rank(60, baseline)
        
        assert rank == pytest.approx(50, rel=0.1)
    
    def test_percentile_rank_at_q3(self):
        """Percentile rank à Q3"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        rank = percentile_rank(66, baseline)
        
        assert rank == pytest.approx(75, rel=0.1)


class TestBatchOperations:
    """Tests pour opérations batch"""
    
    def test_compute_multiple_baselines(self):
        """Calcul de multiples baselines"""
        data = {
            'hrv': [50, 55, 60, 65, 70],
            'heart_rate': [60, 62, 65, 68, 70]
        }
        baselines = compute_multiple_baselines(data)
        
        assert 'hrv' in baselines
        assert 'heart_rate' in baselines
        assert baselines['hrv'].median == pytest.approx(60, rel=0.01)
        assert baselines['heart_rate'].median == pytest.approx(65, rel=0.01)
    
    def test_compute_multiple_with_invalid(self):
        """Calcul avec certaines métriques invalides"""
        data = {
            'valid': [50, 55, 60, 65, 70],
            'invalid': []  # Vide
        }
        baselines = compute_multiple_baselines(data)
        
        assert 'valid' in baselines
        assert 'invalid' not in baselines  # Ignorée
    
    def test_detect_anomalies(self):
        """Détection d'anomalies multiples"""
        current = {
            'hrv': 45,  # Anomalie basse
            'heart_rate': 85  # Anomalie haute
        }
        
        baselines = {
            'hrv': RobustStats(median=60, iqr=12, p25=54, p75=66, count=50),
            'heart_rate': RobustStats(median=65, iqr=8, p25=61, p75=69, count=50)
        }
        
        anomalies = detect_anomalies(current, baselines)
        
        assert len(anomalies) >= 1  # Au moins une anomalie
        assert all('z_score_robust' in a for a in anomalies)
        assert all('priority' in a for a in anomalies)
        
        # Vérifier tri par priorité
        priorities = [a['priority'] for a in anomalies]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_detect_anomalies_with_weights(self):
        """Détection avec poids personnalisés"""
        current = {'hrv': 45, 'steps': 3000}
        
        baselines = {
            'hrv': RobustStats(median=60, iqr=12, p25=54, p75=66, count=50),
            'steps': RobustStats(median=8000, iqr=2000, p25=7000, p75=9000, count=50)
        }
        
        weights = {
            'hrv': 5,  # Poids élevé
            'steps': 1  # Poids faible
        }
        
        anomalies = detect_anomalies(current, baselines, weights=weights)
        
        # HRV devrait avoir priorité plus élevée
        if len(anomalies) > 1:
            hrv_anomaly = next(a for a in anomalies if a['metric'] == 'hrv')
            steps_anomaly = next(a for a in anomalies if a['metric'] == 'steps')
            assert hrv_anomaly['priority'] > steps_anomaly['priority']


class TestValidation:
    """Tests pour validation"""
    
    def test_validate_valid_baseline(self):
        """Validation baseline valide"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=50)
        
        assert validate_baseline(baseline) is True
    
    def test_validate_invalid_order(self):
        """Validation baseline avec ordre invalide"""
        # p25 > median (invalide)
        baseline = RobustStats(median=60, iqr=12, p25=70, p75=66, count=50)
        
        assert validate_baseline(baseline) is False
    
    def test_validate_invalid_iqr(self):
        """Validation baseline avec IQR incohérent"""
        # IQR != p75 - p25
        baseline = RobustStats(median=60, iqr=20, p25=54, p75=66, count=50)
        
        assert validate_baseline(baseline) is False
    
    def test_validate_invalid_count(self):
        """Validation baseline avec count < 2"""
        baseline = RobustStats(median=60, iqr=12, p25=54, p75=66, count=1)
        
        assert validate_baseline(baseline) is False


class TestToDict:
    """Tests pour conversion en dict"""
    
    def test_to_dict_complete(self):
        """Conversion complète en dict"""
        baseline = RobustStats(
            median=60.123,
            iqr=12.456,
            p25=54.789,
            p75=66.987,
            mean=61.234,
            std=8.567,
            count=50,
            confidence='high'
        )
        
        d = baseline.to_dict()
        
        assert d['median'] == 60.12  # Arrondi 2 décimales
        assert d['iqr'] == 12.46
        assert d['p25'] == 54.79
        assert d['p75'] == 66.99
        assert d['mean'] == 61.23
        assert d['std'] == 8.57
        assert d['count'] == 50
        assert d['confidence'] == 'high'
    
    def test_to_dict_without_classical(self):
        """Conversion sans stats classiques"""
        baseline = RobustStats(
            median=60,
            iqr=12,
            p25=54,
            p75=66,
            count=50,
            confidence='medium'
        )
        
        d = baseline.to_dict()
        
        assert d['mean'] is None
        assert d['std'] is None


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
