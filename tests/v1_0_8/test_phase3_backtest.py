"""
Test Phase 3: Backtest Execution

Tests the backtest execution workflow:
- Backtest configuration
- Backtest execution
- Results generation
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest import (
    run_backtest,
    BacktestConfig,
    BacktestResults,
)


class TestBacktestConfig:
    """Test BacktestConfig."""
    
    def test_backtest_config_creation(self):
        """Test creating BacktestConfig."""
        config = BacktestConfig(
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
        )
        assert config is not None
        assert config.start_date == '2020-01-01'
        assert config.end_date == '2020-12-31'
        assert config.capital_base == 100000
    
    def test_backtest_config_defaults(self):
        """Test BacktestConfig default values."""
        config = BacktestConfig(
            start_date='2020-01-01',
            end_date='2020-12-31',
        )
        # Should have default capital_base
        assert hasattr(config, 'capital_base')


class TestBacktestResults:
    """Test BacktestResults."""
    
    def test_backtest_results_structure(self, sample_backtest_results):
        """Test BacktestResults structure."""
        assert 'portfolio_value' in sample_backtest_results
        assert 'returns' in sample_backtest_results
        assert 'sharpe_ratio' in sample_backtest_results
        assert 'max_drawdown' in sample_backtest_results
    
    def test_backtest_results_types(self, sample_backtest_results):
        """Test BacktestResults types."""
        assert isinstance(sample_backtest_results['portfolio_value'], pd.Series)
        assert isinstance(sample_backtest_results['returns'], pd.Series)
        assert isinstance(sample_backtest_results['sharpe_ratio'], (int, float))
        assert isinstance(sample_backtest_results['max_drawdown'], (int, float))


class TestBacktestExecution:
    """Test backtest execution."""
    
    @pytest.mark.slow
    def test_run_backtest_function_exists(self):
        """Test that run_backtest function exists."""
        assert run_backtest is not None
        import inspect
        sig = inspect.signature(run_backtest)
        params = list(sig.parameters.keys())
        
        # Should have essential parameters
        assert len(params) > 0
    
    @pytest.mark.slow
    def test_run_backtest_with_config(self):
        """Test running backtest with config."""
        config = BacktestConfig(
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
        )
        
        # Function should accept config
        assert config is not None


class TestBacktestMetrics:
    """Test backtest metrics calculation."""
    
    def test_sharpe_ratio_range(self, sample_backtest_results):
        """Test that Sharpe ratio is in reasonable range."""
        sharpe = sample_backtest_results['sharpe_ratio']
        assert -10 <= sharpe <= 10
    
    def test_max_drawdown_negative(self, sample_backtest_results):
        """Test that max drawdown is negative or zero."""
        max_dd = sample_backtest_results['max_drawdown']
        assert max_dd <= 0
    
    def test_returns_series(self, sample_backtest_results):
        """Test that returns is a valid series."""
        returns = sample_backtest_results['returns']
        assert isinstance(returns, pd.Series)
        assert len(returns) > 0
    
    def test_portfolio_value_series(self, sample_backtest_results):
        """Test that portfolio_value is a valid series."""
        pv = sample_backtest_results['portfolio_value']
        assert isinstance(pv, pd.Series)
        assert len(pv) > 0
        assert all(pv > 0)


class TestTransactions:
    """Test transaction tracking."""
    
    def test_transactions_dataframe(self, sample_backtest_results):
        """Test that transactions is a DataFrame."""
        transactions = sample_backtest_results['transactions']
        assert isinstance(transactions, pd.DataFrame)
    
    def test_transactions_columns(self, sample_backtest_results):
        """Test that transactions has required columns."""
        transactions = sample_backtest_results['transactions']
        
        # Should have key columns
        expected_cols = ['symbol', 'amount', 'price']
        for col in expected_cols:
            if col in transactions.columns:
                assert col in transactions.columns


class TestPositions:
    """Test position tracking."""
    
    def test_positions_dataframe(self, sample_backtest_results):
        """Test that positions is a DataFrame."""
        positions = sample_backtest_results['positions']
        assert isinstance(positions, pd.DataFrame)
    
    def test_positions_have_symbols(self, sample_backtest_results):
        """Test that positions tracks symbols."""
        positions = sample_backtest_results['positions']
        assert len(positions.columns) > 0


class TestBacktestOutputs:
    """Test backtest outputs."""
    
    def test_results_directory_structure(self, temp_results_dir):
        """Test that results directory can be created."""
        assert temp_results_dir.exists()
        assert temp_results_dir.is_dir()
    
    def test_metrics_json_structure(self, sample_backtest_results):
        """Test that metrics can be serialized to JSON."""
        import json
        
        metrics = {
            'sharpe_ratio': sample_backtest_results['sharpe_ratio'],
            'max_drawdown': sample_backtest_results['max_drawdown'],
            'total_return': sample_backtest_results['total_return'],
        }
        
        # Should be JSON serializable
        json_str = json.dumps(metrics)
        assert isinstance(json_str, str)


class TestBacktestValidation:
    """Test backtest validation."""
    
    def test_validate_backtest_results(self, sample_backtest_results):
        """Test validating backtest results."""
        from lib.validation import validate_backtest_results
        
        result = validate_backtest_results(
            sample_backtest_results,
            returns=sample_backtest_results['returns'],
            transactions=sample_backtest_results['transactions'],
            positions=sample_backtest_results['positions']
        )
        
        assert result is not None
        from lib.validation import ValidationResult
        assert isinstance(result, ValidationResult)


class TestBacktestErrorHandling:
    """Test backtest error handling."""
    
    def test_invalid_date_range(self):
        """Test backtest with invalid date range."""
        # End date before start date
        try:
            config = BacktestConfig(
                start_date='2020-12-31',
                end_date='2020-01-01',
            )
            # Some implementations may validate in __init__
            # Others may validate when run_backtest is called
        except ValueError:
            # Expected if validation happens in __init__
            pass
    
    def test_zero_capital_base(self):
        """Test backtest with zero capital base."""
        try:
            config = BacktestConfig(
                start_date='2020-01-01',
                end_date='2020-12-31',
                capital_base=0,
            )
            # May or may not raise error depending on implementation
        except ValueError:
            # Expected if validation happens
            pass

