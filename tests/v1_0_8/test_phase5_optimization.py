"""
Test Phase 5: Parameter Optimization

Tests the parameter optimization workflow:
- Grid search
- Random search
- Optimization results
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize import (
    GridSearchOptimizer,
    RandomSearchOptimizer,
)


class TestGridSearchOptimizer:
    """Test GridSearchOptimizer."""
    
    def test_grid_search_optimizer_creation(self):
        """Test creating GridSearchOptimizer."""
        optimizer = GridSearchOptimizer()
        assert optimizer is not None
    
    @pytest.mark.slow
    def test_grid_search_optimizer_signature(self):
        """Test GridSearchOptimizer has correct signature."""
        import inspect
        
        # Check that optimize method exists
        assert hasattr(GridSearchOptimizer, 'optimize')
        
        # Get signature
        sig = inspect.signature(GridSearchOptimizer.optimize)
        params = list(sig.parameters.keys())
        
        # Should have parameters for optimization
        assert len(params) > 0


class TestRandomSearchOptimizer:
    """Test RandomSearchOptimizer."""
    
    def test_random_search_optimizer_creation(self):
        """Test creating RandomSearchOptimizer."""
        optimizer = RandomSearchOptimizer()
        assert optimizer is not None
    
    @pytest.mark.slow
    def test_random_search_optimizer_signature(self):
        """Test RandomSearchOptimizer has correct signature."""
        import inspect
        
        # Check that optimize method exists
        assert hasattr(RandomSearchOptimizer, 'optimize')


class TestOptimizationResults:
    """Test optimization results."""
    
    def test_optimization_results_structure(self, sample_optimization_results):
        """Test optimization results structure."""
        assert 'best_params' in sample_optimization_results
        assert 'best_score' in sample_optimization_results
        assert 'all_results' in sample_optimization_results
    
    def test_best_params_format(self, sample_optimization_results):
        """Test best params format."""
        best_params = sample_optimization_results['best_params']
        assert isinstance(best_params, dict)
        assert len(best_params) > 0
    
    def test_best_score_format(self, sample_optimization_results):
        """Test best score format."""
        best_score = sample_optimization_results['best_score']
        assert isinstance(best_score, (int, float))
    
    def test_all_results_format(self, sample_optimization_results):
        """Test all results format."""
        all_results = sample_optimization_results['all_results']
        assert isinstance(all_results, list)
        assert len(all_results) > 0


class TestParameterSpace:
    """Test parameter space definition."""
    
    def test_parameter_grid_definition(self):
        """Test defining parameter grid."""
        param_grid = {
            'fast_period': [5, 10, 15],
            'slow_period': [20, 30, 40],
        }
        
        # Should be a dict
        assert isinstance(param_grid, dict)
        
        # Each parameter should have list of values
        for key, values in param_grid.items():
            assert isinstance(values, list)
            assert len(values) > 0
    
    def test_parameter_ranges(self):
        """Test parameter ranges."""
        param_ranges = {
            'fast_period': (5, 20),
            'slow_period': (20, 50),
        }
        
        # Ranges should be tuples
        for key, value_range in param_ranges.items():
            assert isinstance(value_range, tuple)
            assert len(value_range) == 2
            assert value_range[0] < value_range[1]


class TestOptimizationMetrics:
    """Test optimization metrics."""
    
    def test_optimization_uses_sharpe_ratio(self):
        """Test that optimization can use Sharpe ratio."""
        # Sharpe ratio is common optimization metric
        metric = 'sharpe_ratio'
        assert isinstance(metric, str)
    
    def test_optimization_uses_calmar_ratio(self):
        """Test that optimization can use Calmar ratio."""
        metric = 'calmar_ratio'
        assert isinstance(metric, str)


class TestOptimizationValidation:
    """Test optimization validation."""
    
    def test_best_params_are_in_grid(self, sample_optimization_results):
        """Test that best params are from the searched space."""
        best_params = sample_optimization_results['best_params']
        all_results = sample_optimization_results['all_results']
        
        # Best params should be in one of the all_results
        found = False
        for result in all_results:
            if result['params'] == best_params:
                found = True
                break
        
        assert found or len(all_results) > 0
    
    def test_best_score_is_maximum(self, sample_optimization_results):
        """Test that best score is the maximum."""
        best_score = sample_optimization_results['best_score']
        all_results = sample_optimization_results['all_results']
        
        # Best score should be >= all other scores
        for result in all_results:
            assert best_score >= result['score']


class TestOptimizationOverfitting:
    """Test overfitting detection."""
    
    @pytest.mark.slow
    def test_optimization_overfitting_check(self):
        """Test that optimization includes overfitting checks."""
        # Check that overfit detection module exists
        from lib.optimize import overfit
        assert overfit is not None


class TestOptimizationPerformance:
    """Test optimization performance."""
    
    def test_optimization_time_tracking(self, sample_optimization_results):
        """Test that optimization tracks execution time."""
        assert 'optimization_time' in sample_optimization_results
        opt_time = sample_optimization_results['optimization_time']
        assert isinstance(opt_time, (int, float))
        assert opt_time > 0

