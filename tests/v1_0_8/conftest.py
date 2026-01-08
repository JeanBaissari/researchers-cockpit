"""
Shared fixtures for v1.0.8 test suite.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    data_dir = tmp_path / 'data'
    (data_dir / 'bundles').mkdir(parents=True, exist_ok=True)
    (data_dir / 'cache').mkdir(parents=True, exist_ok=True)
    (data_dir / 'processed' / '1d').mkdir(parents=True, exist_ok=True)
    (data_dir / 'processed' / '1h').mkdir(parents=True, exist_ok=True)
    (data_dir / 'exports').mkdir(parents=True, exist_ok=True)
    yield data_dir
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def temp_strategy_dir(tmp_path):
    """Create a temporary strategy directory."""
    strategy_dir = tmp_path / 'strategies' / 'test'
    strategy_dir.mkdir(parents=True, exist_ok=True)
    yield strategy_dir
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary results directory."""
    results_dir = tmp_path / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    yield results_dir
    shutil.rmtree(tmp_path, ignore_errors=True)


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def sample_dates():
    """Generate sample date range."""
    return pd.date_range(
        start='2020-01-01',
        end='2020-12-31',
        freq='D',
        tz='UTC'
    )


@pytest.fixture
def valid_ohlcv_data(sample_dates):
    """Create valid OHLCV DataFrame."""
    n = len(sample_dates)
    base_price = 100.0
    
    # Generate consistent OHLCV data
    opens = [base_price + i * 0.1 for i in range(n)]
    closes = [base_price + i * 0.12 for i in range(n)]
    highs = [max(o, c) + np.random.uniform(0.5, 2.0) for o, c in zip(opens, closes)]
    lows = [min(o, c) - np.random.uniform(0.5, 2.0) for o, c in zip(opens, closes)]
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000000 + i * 1000 for i in range(n)],
    }, index=sample_dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data(sample_dates):
    """Create invalid OHLCV DataFrame with inconsistent OHLC."""
    n = len(sample_dates)
    
    df = pd.DataFrame({
        'open': [100.0] * n,
        'high': [95.0] * n,  # Invalid: high < open
        'low': [105.0] * n,  # Invalid: low > open
        'close': [100.0] * n,
        'volume': [1000000] * n,
    }, index=sample_dates)
    
    return df


@pytest.fixture
def sample_csv_file(temp_data_dir, valid_ohlcv_data):
    """Create a sample CSV file with valid OHLCV data."""
    csv_path = temp_data_dir / 'processed' / '1d' / 'AAPL.csv'
    valid_ohlcv_data.to_csv(csv_path)
    return csv_path


# =============================================================================
# Strategy Fixtures
# =============================================================================

@pytest.fixture
def sample_strategy_params():
    """Return sample strategy parameters."""
    return {
        'name': 'test_strategy',
        'asset_class': 'equities',
        'symbols': ['SPY', 'QQQ'],
        'timeframe': '1d',
        'start_date': '2020-01-01',
        'end_date': '2020-12-31',
        'capital_base': 100000,
        'commission': 0.001,
    }


@pytest.fixture
def sample_strategy_file(temp_strategy_dir, sample_strategy_params):
    """Create a minimal sample strategy file."""
    strategy_file = temp_strategy_dir / 'strategy.py'
    strategy_content = '''
from zipline.api import order_target_percent, symbol, record

def initialize(context):
    """Initialize strategy."""
    context.symbol = symbol('SPY')
    context.set_commission(commission=0.001)

def handle_data(context, data):
    """Handle data each bar."""
    if data.can_trade(context.symbol):
        order_target_percent(context.symbol, 1.0)
        record(price=data.current(context.symbol, 'price'))
'''
    strategy_file.write_text(strategy_content)
    
    # Create params.yaml
    params_file = temp_strategy_dir / 'params.yaml'
    params_content = '''
name: test_strategy
asset_class: equities
symbols:
  - SPY
timeframe: 1d
start_date: '2020-01-01'
end_date: '2020-12-31'
capital_base: 100000
commission: 0.001
'''
    params_file.write_text(params_content)
    
    return strategy_file


# =============================================================================
# Results Fixtures
# =============================================================================

@pytest.fixture
def sample_backtest_results(sample_dates):
    """Create sample backtest results."""
    n = len(sample_dates)
    
    # Portfolio values
    portfolio_value = pd.Series(
        [100000 * (1 + 0.0001 * i) for i in range(n)],
        index=sample_dates
    )
    
    # Returns
    returns = portfolio_value.pct_change().fillna(0)
    
    # Positions
    positions = pd.DataFrame({
        'SPY': [100] * n,
    }, index=sample_dates)
    
    # Transactions
    transactions = pd.DataFrame({
        'sid': ['SPY'] * 10,
        'symbol': ['SPY'] * 10,
        'price': [100.0 + i for i in range(10)],
        'amount': [10, -5, 10, -5, 10, -5, 10, -5, 10, -5],
        'commission': [1.0] * 10,
    }, index=sample_dates[:10])
    
    results = {
        'portfolio_value': portfolio_value,
        'returns': returns,
        'positions': positions,
        'transactions': transactions,
        'sharpe_ratio': 1.5,
        'max_drawdown': -0.05,
        'total_return': 0.10,
        'annual_return': 0.10,
        'volatility': 0.15,
        'sortino_ratio': 2.0,
        'calmar_ratio': 2.0,
    }
    
    return results


@pytest.fixture
def sample_optimization_results():
    """Create sample optimization results."""
    return {
        'best_params': {
            'fast_period': 10,
            'slow_period': 30,
        },
        'best_score': 1.8,
        'all_results': [
            {'params': {'fast_period': 5, 'slow_period': 20}, 'score': 1.2},
            {'params': {'fast_period': 10, 'slow_period': 30}, 'score': 1.8},
            {'params': {'fast_period': 15, 'slow_period': 40}, 'score': 1.5},
        ],
        'optimization_time': 120.5,
    }


# =============================================================================
# Module Import Fixtures
# =============================================================================

@pytest.fixture
def modern_modules():
    """List of modern module paths that should exist."""
    return [
        'lib.bundles',
        'lib.validation',
        'lib.calendars',
        'lib.backtest',
        'lib.config',
        'lib.metrics',
        'lib.data',
        'lib.plots',
        'lib.report',
        'lib.optimize',
        'lib.validate',
        'lib.logging',
    ]


@pytest.fixture
def deprecated_modules():
    """List of deprecated module paths that should NOT exist."""
    return [
        'lib.data_loader',
        'lib.data_validation',
        'lib.data_integrity',
        'lib.logging_config',
        'lib.optimize',  # wrapper, not package
        'lib.validate',  # wrapper, not package
        'lib.extension',
    ]


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture
def cleanup_test_files(project_root_path):
    """Cleanup any test files created during testing."""
    yield
    
    # Cleanup test strategies
    test_strategies = project_root_path / 'strategies' / 'test'
    if test_strategies.exists():
        shutil.rmtree(test_strategies, ignore_errors=True)
    
    # Cleanup test results
    test_results = project_root_path / 'results' / 'test_strategy'
    if test_results.exists():
        shutil.rmtree(test_results, ignore_errors=True)

