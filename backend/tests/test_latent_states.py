"""
Unit tests for latent states calculator module
Tests all 4 state calculators and utility functions
"""

import pytest
import math
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latent_states import (
    robust_zscore,
    sigmoid,
    ema,
    calculate_recovery_state,
    calculate_sleep_debt_state,
    calculate_overtrain_state,
    calculate_infection_state
)


# ============================================
# TEST UTILITIES
# ============================================

class TestUtilities:
    """Test utility functions"""
    
    def test_robust_zscore_normal(self):
        """Test robust z-score with normal values"""
        z = robust_zscore(x=60.0, baseline_median=50.0, baseline_iqr=13.49)
        assert abs(z - 1.0) < 0.01  # Should be approximately 1.0
    
    def test_robust_zscore_clamping(self):
        """Test z-score clamping to [-4, +4]"""
        z_high = robust_zscore(x=200.0, baseline_median=50.0, baseline_iqr=10.0)
        assert z_high == 4.0  # Clamped to max
        
        z_low = robust_zscore(x=-200.0, baseline_median=50.0, baseline_iqr=10.0)
        assert z_low == -4.0  # Clamped to min
    
    def test_robust_zscore_zero_iqr(self):
        """Test z-score with zero IQR (edge case)"""
        z = robust_zscore(x=50.0, baseline_median=50.0, baseline_iqr=0.0)
        assert z == 0.0  # Should return 0 to avoid division by zero
    
    def test_sigmoid_normal(self):
        """Test sigmoid with normal values"""
        assert abs(sigmoid(0.0) - 0.5) < 0.01  # sigmoid(0) = 0.5
        assert sigmoid(10.0) > 0.99  # Large positive → ~1
        assert sigmoid(-10.0) < 0.01  # Large negative → ~0
    
    def test_sigmoid_overflow(self):
        """Test sigmoid handles overflow"""
        result = sigmoid(-1000.0)  # Should not crash
        assert result < 0.01
        
        result = sigmoid(1000.0)
        assert result > 0.99
    
    def test_ema_smoothing(self):
        """Test exponential moving average"""
        current = 0.8
        previous = 0.5
        alpha = 0.2
        
        result = ema(current, previous, alpha)
        expected = 0.2 * 0.8 + 0.8 * 0.5  # 0.16 + 0.4 = 0.56
        assert abs(result - expected) < 0.001


# ============================================
# TEST RECOVERY STATE
# ============================================

class TestRecoveryState:
    """Test recovery state calculator"""
    
    def setup_method(self):
        """Setup common test data"""
        self.baselines = {
            'baseline_hrv_median': 50.0,
            'baseline_hrv_iqr': 15.0,
            'baseline_rhr_median': 60.0,
            'baseline_rhr_iqr': 5.0,
            'baseline_sleep_median': 7.5,
            'baseline_sleep_iqr': 1.0,
            'baseline_fragmentation_median': 20.0,
            'baseline_fragmentation_iqr': 10.0
        }
    
    def test_recovery_good(self):
        """Test recovery with good metrics"""
        result = calculate_recovery_state(
            hrv_night=60.0,  # Above baseline
            rhr_night=58.0,  # Below baseline (good)
            sleep_duration=8.0,  # Above baseline
            sleep_fragmentation=15.0,  # Below baseline (good)
            baselines=self.baselines
        )
        
        assert result['state'] == 'recovery'
        assert result['score'] > 0.6  # Should be good score
        assert result['interpretation'] in ['bonne', 'moyenne']
        assert result['confidence'] == 1.0  # All metrics available
        assert len(result['top_factors']) <= 2
    
    def test_recovery_poor(self):
        """Test recovery with poor metrics"""
        result = calculate_recovery_state(
            hrv_night=35.0,  # Well below baseline
            rhr_night=70.0,  # Well above baseline (bad)
            sleep_duration=5.5,  # Below baseline
            sleep_fragmentation=35.0,  # Above baseline (bad)
            baselines=self.baselines
        )
        
        assert result['state'] == 'recovery'
        assert result['score'] < 0.5  # Should be poor score
        assert result['interpretation'] == 'insuffisante'
        assert result['confidence'] == 1.0
    
    def test_recovery_missing_data(self):
        """Test recovery with missing metrics"""
        result = calculate_recovery_state(
            hrv_night=None,
            rhr_night=60.0,
            sleep_duration=None,
            sleep_fragmentation=20.0,
            baselines=self.baselines
        )
        
        assert result['state'] == 'recovery'
        assert result['confidence'] == 0.5  # Only 2/4 metrics
        assert 'metadata' in result
        assert result['metadata']['raw_inputs']['hrv_night'] is None
    
    def test_recovery_ema_smoothing(self):
        """Test EMA smoothing in recovery"""
        result1 = calculate_recovery_state(
            hrv_night=50.0,
            rhr_night=60.0,
            sleep_duration=7.5,
            sleep_fragmentation=20.0,
            baselines=self.baselines,
            previous_smoothed=None  # First day
        )
        
        # First day: smoothed = raw
        assert result1['smoothed_score'] == result1['score']
        
        # Second day with EMA
        result2 = calculate_recovery_state(
            hrv_night=60.0,  # Better metrics
            rhr_night=58.0,
            sleep_duration=8.0,
            sleep_fragmentation=15.0,
            baselines=self.baselines,
            previous_smoothed=result1['smoothed_score']
        )
        
        # Smoothed should be between previous and current
        assert result1['smoothed_score'] < result2['smoothed_score'] < result2['score']


# ============================================
# TEST SLEEP DEBT STATE
# ============================================

class TestSleepDebtState:
    """Test sleep debt state calculator"""
    
    def test_sleep_debt_no_debt(self):
        """Test with no sleep debt"""
        result = calculate_sleep_debt_state(
            sleep_history_7d=[8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0],
            baseline_sleep_need=8.0,
            previous_debt=0.0
        )
        
        assert result['state'] == 'sleep_debt'
        assert result['debt_hours'] == 0.0
        assert result['score'] > 0.9  # No debt = high score
        assert result['confidence'] == 1.0  # All 7 days available
    
    def test_sleep_debt_accumulation(self):
        """Test debt accumulation"""
        # Day 1: 2h deficit
        result1 = calculate_sleep_debt_state(
            sleep_history_7d=[6.0],
            baseline_sleep_need=8.0,
            previous_debt=0.0
        )
        
        assert result1['debt_hours'] == 2.0
        
        # Day 2: another 2h deficit
        result2 = calculate_sleep_debt_state(
            sleep_history_7d=[6.0, 6.0],
            baseline_sleep_need=8.0,
            previous_debt=result1['debt_hours']
        )
        
        # Debt should be: 2.0 * 0.85 (decay) + 2.0 (new deficit) = 3.7h
        assert result2['debt_hours'] > 3.5
        assert result2['debt_hours'] < 4.0
    
    def test_sleep_debt_recovery(self):
        """Test debt recovery with good sleep"""
        result = calculate_sleep_debt_state(
            sleep_history_7d=[9.0],  # Extra sleep
            baseline_sleep_need=8.0,
            previous_debt=3.0  # Starting with debt
        )
        
        # Debt should decrease: 3.0 * 0.85 = 2.55 (no new deficit)
        assert result['debt_hours'] < 3.0
        assert result['debt_hours'] > 2.0
    
    def test_sleep_debt_severe(self):
        """Test severe debt detection"""
        result = calculate_sleep_debt_state(
            sleep_history_7d=[5.0] * 7,  # 3h deficit every day
            baseline_sleep_need=8.0,
            previous_debt=10.0  # Already high debt
        )
        
        assert result['debt_hours'] > 5.0  # Severe debt
        assert result['score'] < 0.3  # Very low score


# ============================================
# TEST OVERTRAIN STATE
# ============================================

class TestOvertrainState:
    """Test overtrain state calculator"""
    
    def setup_method(self):
        """Setup common test data"""
        self.baselines = {
            'baseline_hrv_median': 50.0,
            'baseline_hrv_iqr': 15.0,
            'baseline_rhr_median': 60.0,
            'baseline_rhr_iqr': 5.0
        }
    
    def test_overtrain_normal_load(self):
        """Test with normal training load"""
        result = calculate_overtrain_state(
            activity_load_7d=[5.0] * 7,  # Consistent load
            activity_load_28d=[5.0] * 28,
            hrv_3d_avg=50.0,
            rhr_3d_avg=60.0,
            baselines=self.baselines
        )
        
        assert result['state'] == 'overtrain'
        # ACWR with epsilon: 5.0 / (5.0 + 0.1) = 0.98
        assert abs(result['acwr'] - 0.98) < 0.01
        assert result['interpretation'] == 'ok'
        assert result['score'] < 0.4  # Low risk
    
    def test_overtrain_high_acwr(self):
        """Test with high ACWR (overtraining risk)"""
        result = calculate_overtrain_state(
            activity_load_7d=[10.0] * 7,  # High recent load
            activity_load_28d=[5.0] * 28,  # Lower chronic load
            hrv_3d_avg=40.0,  # Suppressed HRV
            rhr_3d_avg=68.0,  # Elevated RHR
            baselines=self.baselines
        )
        
        # ACWR with epsilon: 10.0 / (5.0 + 0.1) = 1.96
        assert abs(result['acwr'] - 1.96) < 0.01
        assert result['interpretation'] in ['surcharge', 'surveiller']
        assert result['score'] > 0.5  # High risk
    
    def test_overtrain_edge_case_zero_chronic(self):
        """Test edge case with zero chronic load"""
        result = calculate_overtrain_state(
            activity_load_7d=[5.0] * 7,
            activity_load_28d=[0.0] * 28,
            hrv_3d_avg=50.0,
            rhr_3d_avg=60.0,
            baselines=self.baselines
        )
        
        # Should not crash (epsilon prevents division by zero)
        assert result['acwr'] > 0
        assert 'metadata' in result
    
    def test_overtrain_missing_physio(self):
        """Test with missing physiological data"""
        result = calculate_overtrain_state(
            activity_load_7d=[5.0] * 7,
            activity_load_28d=[5.0] * 28,
            hrv_3d_avg=None,
            rhr_3d_avg=None,
            baselines=self.baselines
        )
        
        assert result['state'] == 'overtrain'
        assert result['confidence'] < 1.0  # Reduced confidence
        assert len(result['top_factors']) >= 1  # At least ACWR factor


# ============================================
# TEST INFECTION STATE
# ============================================

class TestInfectionState:
    """Test infection-like state calculator"""
    
    def setup_method(self):
        """Setup common test data"""
        self.baselines = {
            'baseline_rhr_median': 60.0,
            'baseline_rhr_iqr': 5.0,
            'baseline_hrv_median': 50.0,
            'baseline_hrv_iqr': 15.0,
            'baseline_fragmentation_median': 20.0,
            'baseline_fragmentation_iqr': 10.0
        }
    
    def test_infection_strong_signature(self):
        """Test strong infection signature"""
        result = calculate_infection_state(
            rhr_night=75.0,  # Well above baseline (+15 bpm)
            hrv_night=30.0,  # Well below baseline (-20 ms)
            sleep_fragmentation=40.0,  # Well above baseline (+20)
            baselines=self.baselines,
            persistent_2_days=True,
            sleep_debt_hours=0.0,  # No confounding
            overtrain_score=0.0  # No confounding
        )
        
        assert result['state'] == 'infection_like'
        assert result['persistent'] is True
        assert result['signals_triggered'] >= 2  # Multiple signals
        assert result['score'] > 0.5  # High score
        assert len(result['metadata']['confounding_states']['penalties_applied']) == 0
    
    def test_infection_with_sleep_debt_penalty(self):
        """Test infection signature with sleep debt confounding"""
        result = calculate_infection_state(
            rhr_night=70.0,
            hrv_night=40.0,
            sleep_fragmentation=30.0,
            baselines=self.baselines,
            persistent_2_days=True,
            sleep_debt_hours=4.0,  # High debt (confounding)
            overtrain_score=0.0
        )
        
        assert 'sleep_debt' in result['metadata']['confounding_states']['penalties_applied']
        # Score should be penalized
        assert result['score'] < 0.7
    
    def test_infection_with_overtrain_penalty(self):
        """Test infection signature with overtrain confounding"""
        result = calculate_infection_state(
            rhr_night=70.0,
            hrv_night=40.0,
            sleep_fragmentation=30.0,
            baselines=self.baselines,
            persistent_2_days=True,
            sleep_debt_hours=0.0,
            overtrain_score=0.75  # High overtrain (confounding)
        )
        
        assert 'overtrain' in result['metadata']['confounding_states']['penalties_applied']
        assert result['score'] < 0.7
    
    def test_infection_both_penalties(self):
        """Test infection with both confounding factors"""
        result = calculate_infection_state(
            rhr_night=70.0,
            hrv_night=40.0,
            sleep_fragmentation=30.0,
            baselines=self.baselines,
            persistent_2_days=True,
            sleep_debt_hours=4.0,  # High debt
            overtrain_score=0.75  # High overtrain
        )
        
        penalties = result['metadata']['confounding_states']['penalties_applied']
        assert 'sleep_debt' in penalties
        assert 'overtrain' in penalties
        # Both penalties should compound: 0.8 * 0.85 = 0.68
        assert result['metadata']['guard_rails']['confounding_penalties']['final_multiplier'] < 0.7
    
    def test_infection_weak_signals(self):
        """Test infection with weak signals (< 2 strong signals)"""
        result = calculate_infection_state(
            rhr_night=62.0,  # Slightly above baseline
            hrv_night=48.0,  # Slightly below baseline
            sleep_fragmentation=22.0,  # Slightly above baseline
            baselines=self.baselines,
            persistent_2_days=False,
            sleep_debt_hours=0.0,
            overtrain_score=0.0
        )
        
        assert result['signals_triggered'] < 2
        assert result['score'] < 0.5  # Penalized for weak signals
    
    def test_infection_not_persistent(self):
        """Test infection signature without persistence"""
        result = calculate_infection_state(
            rhr_night=75.0,
            hrv_night=30.0,
            sleep_fragmentation=40.0,
            baselines=self.baselines,
            persistent_2_days=False,  # Only 1 day
            sleep_debt_hours=0.0,
            overtrain_score=0.0
        )
        
        assert result['persistent'] is False
        # Score should be penalized for non-persistence
        # Even with strong signals


# ============================================
# TEST CATEGORIZATION FUNCTIONS
# ============================================

class TestCategorization:
    """Test categorization helper functions"""
    
    def test_categorize_score(self):
        """Test score categorization"""
        from services.ai_service import AIAnalysisService
        
        assert AIAnalysisService._categorize_score(0.8) == "bonne"
        assert AIAnalysisService._categorize_score(0.6) == "moyenne"
        assert AIAnalysisService._categorize_score(0.3) == "faible"
    
    def test_categorize_confidence(self):
        """Test confidence categorization"""
        from services.ai_service import AIAnalysisService
        
        assert AIAnalysisService._categorize_confidence(0.8) == "élevée"
        assert AIAnalysisService._categorize_confidence(0.5) == "moyenne"
        assert AIAnalysisService._categorize_confidence(0.3) == "faible"
    
    def test_categorize_debt(self):
        """Test debt categorization"""
        from services.ai_service import AIAnalysisService
        
        assert AIAnalysisService._categorize_debt(6.0) == "dette sévère"
        assert AIAnalysisService._categorize_debt(4.0) == "dette modérée"
        assert AIAnalysisService._categorize_debt(2.0) == "dette légère"
        assert AIAnalysisService._categorize_debt(0.5) == "pas de dette"
    
    def test_format_top_factors(self):
        """Test top factors formatting"""
        from services.ai_service import AIAnalysisService
        
        factors = [
            {"factor": "hrv_below_baseline", "weight": 0.40},
            {"factor": "rhr_above_baseline", "weight": 0.25},
            {"factor": "sleep_duration_low", "weight": 0.20}
        ]
        
        result = AIAnalysisService._format_top_factors(factors, max_factors=2)
        assert "hrv below baseline" in result
        assert "rhr above baseline" in result
        assert "sleep duration low" not in result  # Only top 2
    
    def test_format_penalties(self):
        """Test penalties formatting"""
        from services.ai_service import AIAnalysisService
        
        assert AIAnalysisService._format_penalties([]) == "aucune"
        assert AIAnalysisService._format_penalties(['sleep_debt']) == "dette sommeil"
        assert AIAnalysisService._format_penalties(['sleep_debt', 'overtrain']) == "dette sommeil, surcharge"


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
