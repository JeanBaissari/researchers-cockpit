"""
Tests for Monte Carlo strategy validation.
"""

import numpy as np
import pandas as pd
import pytest

from lib.strategy_validation.montecarlo import monte_carlo


@pytest.mark.unit
def test_monte_carlo_returns_empty_results_for_empty_series():
    returns = pd.Series(dtype=float)
    out = monte_carlo(returns)

    assert isinstance(out, dict)
    assert out["simulation_paths"].empty
    assert out["confidence_intervals"] == {}
    assert out["final_value_stats"] == {}


@pytest.mark.unit
def test_monte_carlo_returns_empty_results_for_all_nan_series():
    idx = pd.date_range("2020-01-01", periods=5, freq="D", tz="UTC")
    returns = pd.Series([np.nan] * 5, index=idx)
    out = monte_carlo(returns)

    assert out["simulation_paths"].empty
    assert out["confidence_intervals"] == {}
    assert out["final_value_stats"] == {}


@pytest.mark.unit
def test_monte_carlo_zero_simulations_is_graceful():
    idx = pd.date_range("2020-01-01", periods=5, freq="D", tz="UTC")
    returns = pd.Series([0.01, -0.01, 0.0, 0.02, -0.02], index=idx)
    out = monte_carlo(returns, n_simulations=0)

    assert out["simulation_paths"].empty
    assert out["confidence_intervals"] == {}
    assert out["final_value_stats"] == {}
    assert out["n_simulations"] == 0


@pytest.mark.unit
def test_monte_carlo_constant_zero_returns_produces_constant_paths_and_stats():
    idx = pd.date_range("2020-01-01", periods=10, freq="D", tz="UTC")
    initial_value = 1234.0
    returns = pd.Series([0.0] * len(idx), index=idx)

    out = monte_carlo(
        returns,
        n_simulations=25,
        confidence_levels=[0.05, 0.5, 0.95],
        initial_value=initial_value,
    )

    paths = out["simulation_paths"]
    assert paths.shape == (len(idx), 25)
    assert list(paths.index) == list(idx)

    # All values should remain constant at initial_value
    assert float(paths.min().min()) == pytest.approx(initial_value)
    assert float(paths.max().max()) == pytest.approx(initial_value)

    assert out["confidence_intervals"]["p5"] == pytest.approx(initial_value)
    assert out["confidence_intervals"]["p50"] == pytest.approx(initial_value)
    assert out["confidence_intervals"]["p95"] == pytest.approx(initial_value)

    stats = out["final_value_stats"]
    assert stats["mean"] == pytest.approx(initial_value)
    assert stats["std"] == pytest.approx(0.0)
    assert stats["min"] == pytest.approx(initial_value)
    assert stats["max"] == pytest.approx(initial_value)


@pytest.mark.unit
def test_monte_carlo_is_deterministic_across_calls_due_to_fixed_seed():
    idx = pd.date_range("2020-01-01", periods=30, freq="D", tz="UTC")
    returns = pd.Series(np.linspace(-0.02, 0.03, len(idx)), index=idx)

    out1 = monte_carlo(returns, n_simulations=50, initial_value=1000.0)
    out2 = monte_carlo(returns, n_simulations=50, initial_value=1000.0)

    pd.testing.assert_frame_equal(out1["simulation_paths"], out2["simulation_paths"])
    assert out1["confidence_intervals"] == out2["confidence_intervals"]
    assert out1["final_value_stats"] == out2["final_value_stats"]
