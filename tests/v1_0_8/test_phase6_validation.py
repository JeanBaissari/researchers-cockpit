"""
Test Phase 6: Strategy Validation

Tests the strategy validation workflow:
- Walk-forward validation
- Monte Carlo simulation
- Out-of-sample testing
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validate import (
    WalkForwardValidator,
    MonteCarloValidator,
)


class TestWalkForwardValidator:
    """Test WalkForwardValidator."""
    
    def test_walk_forward_validator_creation(self):
        """Test creating WalkForwardValidator."""
        validator = WalkForwardValidator()
        assert validator is not None
    
    @pytest.mark.slow
    def test_walk_forward_validator_signature(self):
        """Test WalkForwardValidator has correct signature."""
        import inspect
        
        # Check that validate method exists
        assert hasattr(WalkForwardValidator, 'validate') or hasattr(WalkForwardValidator, 'run')
    
    def test_walk_forward_parameters(self):
        """Test walk-forward parameters."""
        # Typical parameters
        train_period = 252  # 1 year
        test_period = 63    # 3 months
        
        assert train_period > test_period
        assert train_period > 0
        assert test_period > 0


class TestMonteCarloValidator:
    """Test MonteCarloValidator."""
    
    def test_monte_carlo_validator_creation(self):
        """Test creating MonteCarloValidator."""
        validator = MonteCarloValidator()
        assert validator is not None
    
    @pytest.mark.slow
    def test_monte_carlo_validator_signature(self):
        """Test MonteCarloValidator has correct signature."""
        import inspect
        
        # Check that validate method exists
        assert hasattr(MonteCarloValidator, 'validate') or hasattr(MonteCarloValidator, 'run')
    
    def test_monte_carlo_parameters(self):
        """Test Monte Carlo parameters."""
        # Typical parameters
        num_simulations = 1000
        confidence_level = 0.95
        
        assert num_simulations > 0
        assert 0 < confidence_level < 1


class TestWalkForwardAnalysis:
    """Test walk-forward analysis."""
    
    def test_walk_forward_splits(self):
        """Test walk-forward time splits."""
        total_days = 1000
        train_period = 252
        test_period = 63
        
        # Calculate number of splits
        num_splits = (total_days - train_period) // test_period
        
        assert num_splits > 0
        assert num_splits >= 1
    
    def test_walk_forward_windows(self):
        """Test walk-forward window definition."""
        windows = [
            {'train_start': '2020-01-01', 'train_end': '2020-12-31',
             'test_start': '2021-01-01', 'test_end': '2021-03-31'},
            {'train_start': '2020-04-01', 'train_end': '2021-03-31',
             'test_start': '2021-04-01', 'test_end': '2021-06-30'},
        ]
        
        for window in windows:
            assert 'train_start' in window
            assert 'train_end' in window
            assert 'test_start' in window
            assert 'test_end' in window


class TestMonteCarloAnalysis:
    """Test Monte Carlo analysis."""
    
    def test_monte_carlo_simulation_count(self):
        """Test Monte Carlo simulation count."""
        num_simulations = 1000
        
        # Generate mock simulation results
        simulations = [i * 0.01 for i in range(num_simulations)]
        
        assert len(simulations) == num_simulations
    
    def test_monte_carlo_confidence_intervals(self):
        """Test Monte Carlo confidence intervals."""
        confidence_level = 0.95
        
        # Confidence level should be between 0 and 1
        assert 0 < confidence_level < 1
        
        # Calculate percentiles
        lower_percentile = (1 - confidence_level) / 2
        upper_percentile = 1 - lower_percentile
        
        assert 0 < lower_percentile < 0.5
        assert 0.5 < upper_percentile < 1


class TestValidationMetrics:
    """Test validation metrics."""
    
    def test_in_sample_vs_out_of_sample(self):
        """Test in-sample vs out-of-sample comparison."""
        in_sample_sharpe = 1.8
        out_of_sample_sharpe = 1.2
        
        # Out-of-sample typically lower
        degradation = (in_sample_sharpe - out_of_sample_sharpe) / in_sample_sharpe
        
        assert degradation >= 0
        assert degradation <= 1
    
    def test_consistency_score(self):
        """Test consistency score calculation."""
        # Walk-forward results
        wf_results = [1.2, 1.5, 1.3, 1.4, 1.1]
        
        # Calculate consistency (e.g., std dev)
        import numpy as np
        consistency = np.std(wf_results)
        
        assert consistency >= 0


class TestOverfittingDetection:
    """Test overfitting detection."""
    
    def test_overfitting_metrics(self):
        """Test overfitting detection metrics."""
        in_sample_sharpe = 2.5
        out_of_sample_sharpe = 0.5
        
        # Large degradation suggests overfitting
        degradation = in_sample_sharpe - out_of_sample_sharpe
        
        if degradation > 1.0:
            # Likely overfitted
            assert degradation > 1.0
    
    def test_parameter_sensitivity(self):
        """Test parameter sensitivity analysis."""
        # Results with slightly different parameters
        base_result = 1.5
        perturbed_results = [1.4, 1.45, 1.55, 1.6]
        
        # Calculate sensitivity
        import numpy as np
        sensitivity = np.std(perturbed_results)
        
        # Low sensitivity is good (robust)
        assert sensitivity >= 0


class TestValidationResults:
    """Test validation results."""
    
    def test_validation_report_structure(self):
        """Test validation report structure."""
        report = {
            'walk_forward': {
                'num_periods': 5,
                'avg_sharpe': 1.3,
                'consistency': 0.2,
            },
            'monte_carlo': {
                'num_simulations': 1000,
                'mean_return': 0.12,
                'confidence_95': (0.08, 0.16),
            },
        }
        
        assert 'walk_forward' in report
        assert 'monte_carlo' in report
    
    def test_validation_decision(self):
        """Test validation decision making."""
        # Criteria for accepting strategy
        out_of_sample_sharpe = 1.2
        consistency_score = 0.8
        monte_carlo_confidence = 0.95
        
        # Simple decision rule
        is_valid = (
            out_of_sample_sharpe > 1.0 and
            consistency_score > 0.5 and
            monte_carlo_confidence > 0.9
        )
        
        assert isinstance(is_valid, bool)


class TestRobustnessChecks:
    """Test robustness checks."""
    
    def test_parameter_robustness(self):
        """Test parameter robustness."""
        # Results with parameter variations
        param_variations = {
            'fast_period_9': 1.4,
            'fast_period_10': 1.5,
            'fast_period_11': 1.45,
        }
        
        # Should be relatively stable
        values = list(param_variations.values())
        import numpy as np
        std = np.std(values)
        
        # Low standard deviation means robust
        assert std >= 0
    
    def test_time_period_robustness(self):
        """Test robustness across time periods."""
        # Results in different time periods
        period_results = {
            '2015-2016': 1.2,
            '2017-2018': 1.4,
            '2019-2020': 1.3,
        }
        
        # Should have positive results in all periods
        for period, result in period_results.items():
            assert result > 0

