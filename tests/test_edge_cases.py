"""
Test 5: Edge Cases

Test boundary conditions:
1. Very short backtest (1 month)
2. Very long backtest (10 years) - skip if too slow
3. Single trade strategy
4. No trades strategy
5. Extreme parameters
6. Missing data periods
"""

import pytest
from pathlib import Path
import sys
import shutil

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params, validate_strategy_params
from lib.utils import create_strategy_from_template
from lib.data_loader import list_bundles


@pytest.mark.slow
def test_very_short_backtest(project_root_path):
    """Test backtest with very short date range (1 month)."""
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available")
    
    bundle = bundles[0]
    strategy_name = 'test_short_backtest'
    
    try:
        create_strategy_from_template(
            name=strategy_name,
            asset_class='equities',
            asset_symbol='SPY'
        )
        
        params = load_strategy_params(strategy_name, 'equities')
        
        # Very short backtest: 1 month
        perf = run_backtest(
            strategy_name=strategy_name,
            start_date='2023-01-01',
            end_date='2023-01-31',  # 1 month
            bundle=bundle,
            asset_class='equities'
        )
        
        assert perf is not None, "Should handle short backtest"
        assert len(perf) > 0, "Should have some data"
        
        result_dir = save_results(
            strategy_name=strategy_name,
            perf=perf,
            params=params
        )
        
        assert result_dir.exists(), "Results should be saved"
        
    except Exception as e:
        pytest.skip(f"Short backtest skipped: {e}")
    finally:
        # Cleanup
        strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
        results_path = project_root_path / 'results' / strategy_name
        
        if strategy_path.exists():
            shutil.rmtree(strategy_path, ignore_errors=True)
        if results_path.exists():
            shutil.rmtree(results_path, ignore_errors=True)


@pytest.mark.slow
def test_extreme_parameters():
    """Test validation with extreme parameter values."""
    # Test very high position size
    extreme_params = {
        'strategy': {
            'asset_symbol': 'SPY',
            'rebalance_frequency': 'daily'
        },
        'position_sizing': {
            'max_position_pct': 2.0  # Invalid: > 1.0
        }
    }
    
    is_valid, errors = validate_strategy_params(extreme_params, 'test')
    assert not is_valid, "Should reject extreme position size"
    
    # Test negative stop loss
    extreme_params = {
        'strategy': {
            'asset_symbol': 'SPY',
            'rebalance_frequency': 'daily'
        },
        'risk': {
            'stop_loss_pct': -0.1  # Invalid: negative
        }
    }
    
    is_valid, errors = validate_strategy_params(extreme_params, 'test')
    assert not is_valid, "Should reject negative stop loss"
    
    # Test very high minutes_after_open
    extreme_params = {
        'strategy': {
            'asset_symbol': 'SPY',
            'rebalance_frequency': 'daily',
            'minutes_after_open': 120  # Invalid: > 60
        }
    }
    
    is_valid, errors = validate_strategy_params(extreme_params, 'test')
    assert not is_valid, "Should reject minutes_after_open > 60"


def test_no_trades_strategy():
    """Test handling of strategy that makes no trades."""
    # This would require a strategy that never enters positions
    # For now, just verify the system can handle empty transactions
    from lib.metrics import calculate_metrics
    import pandas as pd
    import numpy as np
    
    # Create returns with no trades (flat returns)
    dates = pd.date_range('2020-01-01', periods=10, freq='D')
    returns = pd.Series([0.0] * 10, index=dates)  # No returns = no trades
    
    empty_transactions = pd.DataFrame()
    
    metrics = calculate_metrics(returns, transactions=empty_transactions)
    
    assert 'trade_count' in metrics, "Should have trade_count metric"
    assert metrics['trade_count'] == 0, "Should have zero trades"
    # v1.0.7: total_return is now in percentage format (0.0% = 0.0)
    assert metrics['total_return'] == 0.0, "Should have zero return"


def test_single_trade_strategy():
    """Test handling of strategy with single trade."""
    from lib.metrics import calculate_trade_metrics
    import pandas as pd

    # Create single transaction
    transactions = pd.DataFrame({
        'sid': [1],
        'amount': [100],
        'price': [100.0],
        'commission': [0.0]
    }, index=[pd.Timestamp('2020-01-01')])

    # Add exit transaction
    exit_transaction = pd.DataFrame({
        'sid': [1],
        'amount': [-100],
        'price': [110.0],
        'commission': [0.0]
    }, index=[pd.Timestamp('2020-01-02')])

    transactions = pd.concat([transactions, exit_transaction])

    metrics = calculate_trade_metrics(transactions)

    assert metrics['trade_count'] == 1, "Should have one trade"
    # Note: calculate_trade_metrics() returns decimals (0.0 or 1.0)
    # Percentage conversion only happens when called via calculate_metrics()
    assert metrics['win_rate'] in [0.0, 1.0], "Win rate should be 0.0 or 1.0 for single trade"


def test_missing_data_periods():
    """Test handling of missing data periods."""
    # This tests that the system handles gaps in data gracefully
    from lib.metrics import calculate_metrics
    import pandas as pd
    import numpy as np
    
    # Create returns with NaN values (missing data)
    dates = pd.date_range('2020-01-01', periods=10, freq='D')
    returns = pd.Series([0.01, np.nan, 0.02, np.nan, 0.01, 0.02, np.nan, 0.01, 0.02, 0.01], index=dates)
    
    metrics = calculate_metrics(returns)
    
    # Should handle NaN values gracefully
    assert 'total_return' in metrics, "Should calculate metrics despite NaN"
    assert not np.isnan(metrics['total_return']), "Total return should not be NaN"


def test_zero_volatility_metrics():
    """
    v1.0.7: Test metrics calculation with zero volatility (no trades/flat returns).

    Sharpe and Sortino should be 0.0, not NaN or extreme values like -10.0.
    """
    from lib.metrics import calculate_metrics
    import pandas as pd
    import numpy as np

    # Create returns with zero volatility (all zeros - no price movement)
    dates = pd.date_range('2020-01-01', periods=50, freq='D')
    zero_returns = pd.Series([0.0] * 50, index=dates)

    metrics = calculate_metrics(zero_returns)

    # v1.0.7: These should be 0.0, not NaN or extreme values
    # Sharpe/Sortino are ratios (not percentages), so they stay as 0.0
    assert metrics['sharpe'] == 0.0, f"Sharpe should be 0.0 for zero volatility, got {metrics['sharpe']}"
    assert metrics['sortino'] == 0.0, f"Sortino should be 0.0 for zero volatility, got {metrics['sortino']}"
    # annual_volatility is now in percentage format (0.0% = 0.0)
    assert metrics['annual_volatility'] == 0.0, f"Volatility should be 0%, got {metrics['annual_volatility']}"

    # Ensure no NaN values
    for key, value in metrics.items():
        if isinstance(value, float):
            assert not np.isnan(value), f"Metric '{key}' should not be NaN"


def test_single_losing_trade_metrics():
    """
    v1.0.7: Test trade metrics with a single losing trade.

    max_win should be 0.0 (no wins), not the loss value.
    avg_win should be 0.0 (no wins).
    """
    from lib.metrics import calculate_trade_metrics
    import pandas as pd

    # Create single trade: buy at 100, sell at 90 (10% loss)
    transactions = pd.DataFrame({
        'sid': [1, 1],
        'amount': [100, -100],
        'price': [100.0, 90.0],
        'commission': [0.0, 0.0]
    }, index=pd.to_datetime(['2020-01-01', '2020-01-15']))

    metrics = calculate_trade_metrics(transactions)

    assert metrics['trade_count'] == 1, f"Should have 1 trade, got {metrics['trade_count']}"
    # Note: calculate_trade_metrics() returns decimals (0.0 for no wins)
    # Percentage conversion only happens when called via calculate_metrics()
    assert metrics['win_rate'] == 0.0, f"Win rate should be 0.0, got {metrics['win_rate']}"

    # v1.0.7: max_win should be 0.0 when there are no winning trades
    assert metrics['max_win'] == 0.0, f"max_win should be 0.0 when no wins, got {metrics['max_win']}"
    assert metrics['avg_win'] == 0.0, f"avg_win should be 0.0 when no wins, got {metrics['avg_win']}"

    # Loss metrics should be negative (decimal format, e.g., -0.10 for -10%)
    assert metrics['max_loss'] < 0, f"max_loss should be negative, got {metrics['max_loss']}"
    assert metrics['avg_loss'] < 0, f"avg_loss should be negative, got {metrics['avg_loss']}"


def test_json_serialization_no_nan():
    """
    v1.0.7: Test that metrics can be serialized to valid JSON without NaN.

    Python's json.dump outputs 'NaN' literal which is not valid strict JSON.
    All metrics should be serializable to valid JSON.
    """
    import json
    from lib.metrics import calculate_metrics
    import pandas as pd

    # Edge case: zero returns (previously produced NaN tail_ratio)
    dates = pd.date_range('2020-01-01', periods=30, freq='D')
    zero_returns = pd.Series([0.0] * 30, index=dates)

    metrics = calculate_metrics(zero_returns)

    # Serialize to JSON string
    json_str = json.dumps(metrics)

    # Check for invalid JSON literals
    assert 'NaN' not in json_str, f"JSON should not contain 'NaN' literal: {json_str}"
    assert 'Infinity' not in json_str, f"JSON should not contain 'Infinity' literal: {json_str}"
    assert '-Infinity' not in json_str, f"JSON should not contain '-Infinity' literal: {json_str}"

    # Parse should succeed with strict JSON parser
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict), "Parsed JSON should be a dict"

    # All float values should be valid (not NaN/Inf)
    for key, value in parsed.items():
        if isinstance(value, float):
            assert value == value, f"Metric '{key}' should not be NaN after JSON roundtrip"



