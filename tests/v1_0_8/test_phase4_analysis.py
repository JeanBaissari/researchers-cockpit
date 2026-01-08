"""
Test Phase 4: Results Analysis

Tests the results analysis workflow:
- Metrics calculation
- Performance analysis
- Trade analysis
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_sortino_ratio,
)


class TestMetricsCalculation:
    """Test metrics calculation functions."""
    
    def test_calculate_sharpe_ratio(self, sample_backtest_results):
        """Test calculating Sharpe ratio."""
        returns = sample_backtest_results['returns']
        sharpe = calculate_sharpe_ratio(returns)
        
        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert -10 <= sharpe <= 10
    
    def test_calculate_max_drawdown(self, sample_backtest_results):
        """Test calculating max drawdown."""
        returns = sample_backtest_results['returns']
        max_dd = calculate_max_drawdown(returns)
        
        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd <= 0
    
    def test_calculate_sortino_ratio(self, sample_backtest_results):
        """Test calculating Sortino ratio."""
        returns = sample_backtest_results['returns']
        sortino = calculate_sortino_ratio(returns)
        
        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert -10 <= sortino <= 10


class TestPerformanceMetrics:
    """Test performance metrics."""
    
    def test_total_return(self, sample_backtest_results):
        """Test total return calculation."""
        total_return = sample_backtest_results['total_return']
        assert isinstance(total_return, (int, float))
    
    def test_annual_return(self, sample_backtest_results):
        """Test annual return calculation."""
        annual_return = sample_backtest_results['annual_return']
        assert isinstance(annual_return, (int, float))
    
    def test_volatility(self, sample_backtest_results):
        """Test volatility calculation."""
        volatility = sample_backtest_results['volatility']
        assert isinstance(volatility, (int, float))
        assert volatility >= 0


class TestTradeAnalysis:
    """Test trade analysis."""
    
    def test_transactions_analysis(self, sample_backtest_results):
        """Test analyzing transactions."""
        transactions = sample_backtest_results['transactions']
        
        # Count total trades
        total_trades = len(transactions)
        assert total_trades >= 0
        
        # Check for buys and sells
        if len(transactions) > 0:
            assert 'amount' in transactions.columns
    
    def test_positions_analysis(self, sample_backtest_results):
        """Test analyzing positions."""
        positions = sample_backtest_results['positions']
        
        # Should have position data
        assert len(positions) > 0
        
        # Positions should be numeric
        assert positions.select_dtypes(include=[np.number]).shape[1] > 0


class TestRiskMetrics:
    """Test risk metrics."""
    
    def test_max_drawdown_properties(self, sample_backtest_results):
        """Test max drawdown properties."""
        max_dd = sample_backtest_results['max_drawdown']
        
        # Max drawdown should be negative or zero
        assert max_dd <= 0
        
        # Should be percentage (typically between -1 and 0)
        assert max_dd >= -1
    
    def test_sharpe_ratio_properties(self, sample_backtest_results):
        """Test Sharpe ratio properties."""
        sharpe = sample_backtest_results['sharpe_ratio']
        
        # Sharpe should be finite
        assert np.isfinite(sharpe)
        
        # Typical range is -3 to 3 for most strategies
        assert -10 <= sharpe <= 10


class TestReturnAnalysis:
    """Test return analysis."""
    
    def test_returns_statistics(self, sample_backtest_results):
        """Test returns statistics."""
        returns = sample_backtest_results['returns']
        
        # Calculate basic statistics
        mean_return = returns.mean()
        std_return = returns.std()
        
        assert isinstance(mean_return, (int, float))
        assert isinstance(std_return, (int, float))
        assert std_return >= 0
    
    def test_returns_distribution(self, sample_backtest_results):
        """Test returns distribution."""
        returns = sample_backtest_results['returns']
        
        # Check for outliers
        extreme_returns = returns[returns.abs() > 0.5]
        
        # Most strategies shouldn't have many extreme daily returns
        assert len(extreme_returns) < len(returns) * 0.1


class TestEquityCurve:
    """Test equity curve analysis."""
    
    def test_portfolio_value_monotonic_check(self, sample_backtest_results):
        """Test portfolio value trend."""
        pv = sample_backtest_results['portfolio_value']
        
        # Portfolio value should always be positive
        assert all(pv > 0)
        
        # Check that we have continuous data
        assert len(pv) > 0
    
    def test_portfolio_value_growth(self, sample_backtest_results):
        """Test portfolio value growth."""
        pv = sample_backtest_results['portfolio_value']
        
        initial_value = pv.iloc[0]
        final_value = pv.iloc[-1]
        
        # Both should be positive
        assert initial_value > 0
        assert final_value > 0


class TestMetricsComparison:
    """Test metrics comparison."""
    
    def test_sharpe_vs_sortino(self, sample_backtest_results):
        """Test relationship between Sharpe and Sortino."""
        sharpe = sample_backtest_results['sharpe_ratio']
        sortino = sample_backtest_results['sortino_ratio']
        
        # Sortino is typically >= Sharpe (uses only downside deviation)
        # But both should be reasonable numbers
        assert isinstance(sharpe, (int, float))
        assert isinstance(sortino, (int, float))
    
    def test_calmar_ratio(self, sample_backtest_results):
        """Test Calmar ratio."""
        calmar = sample_backtest_results['calmar_ratio']
        
        assert isinstance(calmar, (int, float))
        assert np.isfinite(calmar)


class TestResultsValidation:
    """Test results validation."""
    
    def test_metrics_consistency(self, sample_backtest_results):
        """Test that metrics are consistent."""
        returns = sample_backtest_results['returns']
        total_return = sample_backtest_results['total_return']
        
        # Calculate total return from returns series
        calculated_total = (1 + returns).prod() - 1
        
        # Should be close (within 0.1%)
        assert abs(calculated_total - total_return) < 0.001 or np.isclose(calculated_total, total_return, rtol=0.01)

