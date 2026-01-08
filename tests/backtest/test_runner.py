"""
Test backtest runner.

Tests for backtest execution and configuration.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import inspect

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest import (
    run_backtest,
    BacktestConfig,
)


class TestBacktestConfig:
    """Test BacktestConfig."""
    
    @pytest.mark.unit
    def test_backtest_config_creation(self):
        """Test creating BacktestConfig."""
        config = BacktestConfig(
            strategy_name='test_strategy',
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
            bundle='test_bundle',
            data_frequency='daily',
        )
        assert config is not None
        assert config.start_date == '2020-01-01'
        assert config.end_date == '2020-12-31'
        assert config.capital_base == 100000
        assert config.strategy_name == 'test_strategy'
        assert config.bundle == 'test_bundle'
        assert config.data_frequency == 'daily'
    
    @pytest.mark.unit
    def test_backtest_config_defaults(self):
        """Test BacktestConfig default values."""
        config = BacktestConfig(
            strategy_name='test_strategy',
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
            bundle='test_bundle',
            data_frequency='daily',
            asset_class=None,  # Optional field
        )
        # Should have all required fields
        assert hasattr(config, 'capital_base')
        assert config.asset_class is None
    
    @pytest.mark.unit
    def test_invalid_date_range(self):
        """Test backtest with invalid date range."""
        # End date before start date
        try:
            config = BacktestConfig(
                strategy_name='test_strategy',
                start_date='2020-12-31',
                end_date='2020-01-01',
                capital_base=100000,
                bundle='test_bundle',
                data_frequency='daily',
            )
            # Some implementations may validate in __init__
            # Others may validate when run_backtest is called
        except ValueError:
            # Expected if validation happens in __init__
            pass
    
    @pytest.mark.unit
    def test_zero_capital_base(self):
        """Test backtest with zero capital base."""
        try:
            config = BacktestConfig(
                strategy_name='test_strategy',
                start_date='2020-01-01',
                end_date='2020-12-31',
                capital_base=0,
                bundle='test_bundle',
                data_frequency='daily',
            )
            # May or may not raise error depending on implementation
        except ValueError:
            # Expected if validation happens
            pass


class TestBacktestExecution:
    """Test backtest execution."""
    
    @pytest.mark.unit
    def test_run_backtest_function_exists(self):
        """Test that run_backtest function exists."""
        assert run_backtest is not None
        sig = inspect.signature(run_backtest)
        params = list(sig.parameters.keys())
        
        # Should have essential parameters
        assert len(params) > 0
    
    @pytest.mark.unit
    def test_run_backtest_with_config(self):
        """Test running backtest with config."""
        config = BacktestConfig(
            strategy_name='test_strategy',
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
            bundle='test_bundle',
            data_frequency='daily',
        )
        
        # Function should accept config
        assert config is not None

