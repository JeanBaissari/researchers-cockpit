"""
Test core metrics calculations.

Tests for basic performance metrics.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.metrics import calculate_metrics


class TestCoreMetrics:
    """Test core metrics calculation."""
    
    @pytest.mark.unit
    def test_calculate_sharpe_ratio(self, sample_backtest_results):
        """Test calculating Sharpe ratio."""
        returns = sample_backtest_results['returns']
        metrics = calculate_metrics(returns)
        
        sharpe = metrics.get('sharpe_ratio', 0)
        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert -10 <= sharpe <= 10
    
    @pytest.mark.unit
    def test_calculate_max_drawdown(self, sample_backtest_results):
        """Test calculating max drawdown."""
        returns = sample_backtest_results['returns']
        metrics = calculate_metrics(returns)
        
        max_dd = metrics.get('max_drawdown', 0)
        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd <= 0
    
    @pytest.mark.unit
    def test_calculate_sortino_ratio(self, sample_backtest_results):
        """Test calculating Sortino ratio."""
        returns = sample_backtest_results['returns']
        metrics = calculate_metrics(returns)
        
        sortino = metrics.get('sortino_ratio', 0)
        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert -10 <= sortino <= 10

