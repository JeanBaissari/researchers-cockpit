"""
Tests for lib/strategy_validation integration with Zipline's Performance DataFrame.

Verifies that walk-forward and Monte Carlo correctly consume perf (or returns
derived from perf) as documented in docs/api/performance_dataframe_integration.md.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from lib.strategy_validation import monte_carlo
from lib.strategy_validation.walkforward import _run_period_backtest


@pytest.mark.unit
def test_run_period_backtest_uses_perf_returns_column_when_present():
    """Walk-forward extracts returns from perf['returns'] when present."""
    # Simulate perf as returned by run_backtest (minimal columns)
    dates = pd.date_range("2020-01-01", periods=20, freq="B", tz="UTC")
    returns_series = pd.Series([0.01] * 10 + [-0.005] * 10, index=dates)
    perf = pd.DataFrame({"returns": returns_series}, index=dates)

    with patch("lib.strategy_validation.walkforward.run_backtest", return_value=(perf, None)):
        out = _run_period_backtest(
            strategy_name="test",
            start_date="2020-01-01",
            end_date="2020-01-31",
            period_num=1,
        )

    assert "sharpe" in out
    assert "period" in out
    assert "start_date" in out
    assert "end_date" in out
    assert out["period"] == 1
    # Returns were used (non-empty metrics)
    assert isinstance(out.get("sharpe"), (int, float))


@pytest.mark.unit
def test_run_period_backtest_derives_returns_from_portfolio_value_when_returns_missing():
    """Walk-forward uses perf['portfolio_value'].pct_change() when 'returns' missing (e.g. metrics_set='none')."""
    dates = pd.date_range("2020-01-01", periods=20, freq="B", tz="UTC")
    pv = (1.0 + pd.Series([0.01] * 10 + [-0.005] * 10, index=dates)).cumprod() * 100000
    perf = pd.DataFrame({"portfolio_value": pv}, index=dates)
    assert "returns" not in perf.columns

    with patch("lib.strategy_validation.walkforward.run_backtest", return_value=(perf, None)):
        out = _run_period_backtest(
            strategy_name="test",
            start_date="2020-01-01",
            end_date="2020-01-31",
            period_num=1,
        )

    assert "sharpe" in out
    assert out["period"] == 1
    assert isinstance(out.get("sharpe"), (int, float))


@pytest.mark.unit
def test_run_period_backtest_handles_missing_returns_and_portfolio_value():
    """Walk-forward yields period metadata when perf has neither returns nor portfolio_value."""
    dates = pd.date_range("2020-01-01", periods=5, freq="B", tz="UTC")
    perf = pd.DataFrame({"period_label": ["2020-01-01"] * 5}, index=dates)

    with patch("lib.strategy_validation.walkforward.run_backtest", return_value=(perf, None)):
        out = _run_period_backtest(
            strategy_name="test",
            start_date="2020-01-01",
            end_date="2020-01-07",
            period_num=1,
        )

    assert out["period"] == 1
    assert out["start_date"] == "2020-01-01"
    assert out["end_date"] == "2020-01-07"
    # No returns → no metrics keys from calculate_metrics; period metadata still present


@pytest.mark.unit
def test_monte_carlo_accepts_returns_in_perf_format():
    """Monte Carlo accepts a returns series as would be extracted from perf (DatetimeIndex, dropna)."""
    dates = pd.date_range("2020-01-01", periods=30, freq="B", tz="UTC")
    returns = pd.Series(0.001, index=dates).dropna()

    out = monte_carlo(returns, n_simulations=10, initial_value=100000.0)

    assert "simulation_paths" in out
    assert "confidence_intervals" in out
    assert "final_value_stats" in out
    assert out["simulation_paths"].shape[0] == len(returns)
    assert out["n_simulations"] == 10
