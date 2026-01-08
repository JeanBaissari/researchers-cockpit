"""
Test grid search optimization.

Tests for grid search optimizer.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize import grid_search


class TestGridSearchOptimizer:
    """Test grid search optimization."""
    
    @pytest.mark.unit
    def test_grid_search_function_exists(self):
        """Test that grid_search function exists."""
        assert grid_search is not None
        assert callable(grid_search)
    
    @pytest.mark.unit
    @pytest.mark.slow
    def test_grid_search_function_signature(self):
        """Test grid_search has correct signature."""
        import inspect
        
        # Get signature
        sig = inspect.signature(grid_search)
        params = list(sig.parameters.keys())
        
        # Should have parameters for optimization
        assert len(params) > 0
        assert 'strategy_name' in params
        assert 'param_grid' in params

