"""
Tests for strategy validation metrics.
"""

import math

import pandas as pd
import pytest

from lib.strategy_validation.metrics import (
    calculate_overfit_probability,
    calculate_walk_forward_efficiency,
)


@pytest.mark.unit
def test_calculate_overfit_probability_returns_0_5_when_is_sharpe_is_effectively_zero():
    out = calculate_overfit_probability(
        in_sample_sharpe=0.0,
        out_sample_sharpe=10.0,
        n_trials=999,
    )
    assert out == pytest.approx(0.5)


@pytest.mark.unit
@pytest.mark.parametrize(
    "efficiency,expected",
    [
        (0.29, 0.8),
        (0.30, 0.6),
        (0.49, 0.6),
        (0.50, 0.4),
        (0.69, 0.4),
        (0.70, 0.2),
        (1.20, 0.2),
        (-0.10, 0.8),  # negative efficiency should be treated as very poor
    ],
)
def test_calculate_overfit_probability_thresholds(efficiency, expected):
    # Choose IS=1 so that OOS equals efficiency exactly.
    out = calculate_overfit_probability(
        in_sample_sharpe=1.0,
        out_sample_sharpe=efficiency,
        n_trials=10,
    )
    assert out == pytest.approx(expected)


@pytest.mark.unit
def test_calculate_walk_forward_efficiency_empty_inputs_are_graceful():
    empty = pd.DataFrame(columns=["sharpe"])
    out = calculate_walk_forward_efficiency(empty, empty)

    assert out == {
        "efficiency": 0.0,
        "consistency": 0.0,
        "avg_is_sharpe": 0.0,
        "avg_oos_sharpe": 0.0,
        "std_oos_sharpe": 0.0,
    }


@pytest.mark.unit
def test_calculate_walk_forward_efficiency_computes_efficiency_consistency_and_stats():
    in_sample = pd.DataFrame({"sharpe": [1.0, 2.0, 3.0]})
    out_sample = pd.DataFrame({"sharpe": [0.5, -0.25, 1.25, 0.0]})

    out = calculate_walk_forward_efficiency(in_sample, out_sample)

    assert out["avg_is_sharpe"] == pytest.approx(2.0)
    assert out["avg_oos_sharpe"] == pytest.approx(0.375)
    assert out["efficiency"] == pytest.approx(0.375 / 2.0)
    assert out["consistency"] == pytest.approx(2 / 4)  # >0 only: 0.5 and 1.25
    assert out["n_periods"] == 4
    assert out["std_oos_sharpe"] == pytest.approx(out_sample["sharpe"].std())


@pytest.mark.unit
def test_calculate_walk_forward_efficiency_returns_zero_efficiency_when_avg_is_sharpe_is_effectively_zero():
    # Avg IS Sharpe is ~0 (below threshold), so efficiency should be 0.
    in_sample = pd.DataFrame({"sharpe": [1e-12, -1e-12]})
    out_sample = pd.DataFrame({"sharpe": [1.0, 1.0]})

    out = calculate_walk_forward_efficiency(in_sample, out_sample)
    assert out["avg_is_sharpe"] == pytest.approx(0.0)
    assert out["efficiency"] == pytest.approx(0.0)


@pytest.mark.unit
def test_calculate_walk_forward_efficiency_std_is_nan_for_single_oos_period():
    in_sample = pd.DataFrame({"sharpe": [1.0, 1.0]})
    out_sample = pd.DataFrame({"sharpe": [0.5]})

    out = calculate_walk_forward_efficiency(in_sample, out_sample)
    assert out["n_periods"] == 1
    assert math.isnan(out["std_oos_sharpe"])
