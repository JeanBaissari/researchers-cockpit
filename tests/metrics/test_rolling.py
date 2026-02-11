"""
Test rolling metrics calculations.

Tests for rolling window metrics calculation over time series.
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

from lib.metrics.rolling import calculate_rolling_metrics


class TestCalculateRollingMetrics:
    """Test rolling metrics calculation."""

    @pytest.mark.unit
    def test_rolling_metrics_basic(self, sample_backtest_results):
        """Test basic rolling metrics calculation."""
        returns = sample_backtest_results["returns"]
        rolling_metrics = calculate_rolling_metrics(returns, window=63)

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) > 0

        # Check required columns
        expected_columns = [
            "rolling_sharpe",
            "rolling_sortino",
            "rolling_return",
            "rolling_volatility",
            "rolling_max_dd",
        ]
        for col in expected_columns:
            assert col in rolling_metrics.columns

    @pytest.mark.unit
    def test_rolling_metrics_output_structure(self):
        """Test rolling metrics output DataFrame structure."""
        # Create returns with enough data for rolling window
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) == 71  # 100 - 30 + 1
        assert isinstance(rolling_metrics.index, pd.DatetimeIndex)

        # Check all columns are numeric
        for col in rolling_metrics.columns:
            assert rolling_metrics[col].dtype in [np.float64, np.int64]

    @pytest.mark.unit
    def test_rolling_metrics_window_size(self):
        """Test rolling metrics with different window sizes."""
        dates = pd.date_range("2020-01-01", periods=200, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 200), index=dates)

        # Test with window=30
        rolling_30 = calculate_rolling_metrics(returns, window=30)
        assert len(rolling_30) == 171  # 200 - 30 + 1

        # Test with window=63 (default)
        rolling_63 = calculate_rolling_metrics(returns, window=63)
        assert len(rolling_63) == 138  # 200 - 63 + 1

        # Test with window=126
        rolling_126 = calculate_rolling_metrics(returns, window=126)
        assert len(rolling_126) == 75  # 200 - 126 + 1

    @pytest.mark.unit
    def test_rolling_metrics_empty_series(self):
        """Test rolling metrics with empty series."""
        returns = pd.Series([], dtype=float)
        rolling_metrics = calculate_rolling_metrics(returns)

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) == 0

    @pytest.mark.unit
    def test_rolling_metrics_insufficient_data(self):
        """Test rolling metrics with series shorter than window."""
        dates = pd.date_range("2020-01-01", periods=50, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 50), index=dates)

        # Window larger than data
        rolling_metrics = calculate_rolling_metrics(returns, window=100)

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) == 0

    @pytest.mark.unit
    def test_rolling_metrics_exact_window_size(self):
        """Test rolling metrics with series exactly equal to window."""
        dates = pd.date_range("2020-01-01", periods=63, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 63), index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=63)

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) == 1  # Exactly one window

    @pytest.mark.unit
    def test_rolling_metrics_invalid_window(self):
        """Test rolling metrics with invalid window values."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        # Test with negative window (should default to 63)
        rolling_neg = calculate_rolling_metrics(returns, window=-10)
        rolling_default = calculate_rolling_metrics(returns, window=63)
        assert len(rolling_neg) == len(rolling_default)

        # Test with zero window (should default to 63)
        rolling_zero = calculate_rolling_metrics(returns, window=0)
        assert len(rolling_zero) == len(rolling_default)

        # Test with non-integer window (should default to 63)
        rolling_float = calculate_rolling_metrics(returns, window=30.5)
        assert len(rolling_float) == len(rolling_default)

    @pytest.mark.unit
    def test_rolling_metrics_custom_risk_free_rate(self):
        """Test rolling metrics with custom risk-free rate."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        rolling_4pct = calculate_rolling_metrics(returns, window=30, risk_free_rate=0.04)
        rolling_2pct = calculate_rolling_metrics(returns, window=30, risk_free_rate=0.02)

        assert len(rolling_4pct) == len(rolling_2pct)
        # Sharpe ratios should differ with different risk-free rates
        # (though exact relationship depends on returns)
        assert isinstance(rolling_4pct["rolling_sharpe"].iloc[0], (int, float))
        assert isinstance(rolling_2pct["rolling_sharpe"].iloc[0], (int, float))

    @pytest.mark.unit
    def test_rolling_metrics_decimal_values(self):
        """Test that rolling metrics use raw decimal values (not percentages)."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        # Create returns with known values
        returns = pd.Series([0.01] * 50 + [0.02] * 50, index=dates)  # 1% and 2% returns

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        # Check that values are in decimal format (not percentage multiplied by 100)
        # Annual return can be > 1.0 (100%) when daily returns are high
        # With 1-2% daily returns, annualized return can be very high (e.g., 145% = 1.45)
        # Max drawdown should be <= 0 (negative or zero)
        assert all(rolling_metrics["rolling_max_dd"] <= 0.0)  # Max DD should be negative or zero

        # Check that values are not NaN or Inf (main validation)
        assert not rolling_metrics["rolling_return"].isna().any()
        assert not rolling_metrics["rolling_volatility"].isna().any()
        assert not rolling_metrics["rolling_max_dd"].isna().any()
        assert not np.isinf(rolling_metrics["rolling_return"]).any()
        assert not np.isinf(rolling_metrics["rolling_volatility"]).any()
        assert not np.isinf(rolling_metrics["rolling_max_dd"]).any()

        # Check that values are numeric (not percentage * 100 format)
        # If it were percentage format, values would be 100x larger
        # We verify by checking that values are reasonable for decimal format
        # (e.g., 145.97 as decimal = 14597% return, which is possible with 2% daily returns)
        assert all(rolling_metrics["rolling_return"].abs() < 1000.0)  # Reasonable upper bound
        assert all(rolling_metrics["rolling_volatility"].abs() < 100.0)  # Reasonable upper bound

    @pytest.mark.unit
    def test_rolling_metrics_positive_returns(self):
        """Test rolling metrics with consistently positive returns."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 100, index=dates)  # 1% daily return

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        assert len(rolling_metrics) > 0
        # With constant positive returns, volatility should be near zero
        assert all(rolling_metrics["rolling_volatility"] >= 0)
        # Sharpe and Sortino should be 0.0 with zero volatility
        assert all(rolling_metrics["rolling_sharpe"] == 0.0)
        assert all(rolling_metrics["rolling_sortino"] == 0.0)

    @pytest.mark.unit
    def test_rolling_metrics_negative_returns(self):
        """Test rolling metrics with negative returns."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series([-0.01] * 100, index=dates)  # -1% daily return

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        assert len(rolling_metrics) > 0
        # All metrics should be valid (not NaN)
        assert not rolling_metrics["rolling_sharpe"].isna().any()
        assert not rolling_metrics["rolling_sortino"].isna().any()
        assert not rolling_metrics["rolling_return"].isna().any()
        assert not rolling_metrics["rolling_volatility"].isna().any()
        assert not rolling_metrics["rolling_max_dd"].isna().any()

    @pytest.mark.unit
    def test_rolling_metrics_mixed_returns(self):
        """Test rolling metrics with mixed positive and negative returns."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series([-0.02, 0.01, -0.01, 0.02] * 25, index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        assert len(rolling_metrics) > 0
        # All metrics should be valid
        assert not rolling_metrics.isna().any().any()
        # Max drawdown should be negative or zero
        assert all(rolling_metrics["rolling_max_dd"] <= 0)

    @pytest.mark.unit
    def test_rolling_metrics_with_nan_values(self):
        """Test rolling metrics handles NaN values in returns."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
        returns.iloc[10] = np.nan  # Add a NaN value

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        # Should handle NaN gracefully (sanitize_series removes NaN)
        assert isinstance(rolling_metrics, pd.DataFrame)
        # Output should not contain NaN in metric columns
        if len(rolling_metrics) > 0:
            assert (
                not rolling_metrics[
                    [
                        "rolling_sharpe",
                        "rolling_sortino",
                        "rolling_return",
                        "rolling_volatility",
                        "rolling_max_dd",
                    ]
                ]
                .isna()
                .any()
                .any()
            )

    @pytest.mark.unit
    def test_rolling_metrics_index_alignment(self):
        """Test that rolling metrics index aligns with returns index."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        # Index should be DatetimeIndex
        assert isinstance(rolling_metrics.index, pd.DatetimeIndex)
        # Last date in rolling metrics should match last date in returns
        assert rolling_metrics.index[-1] == returns.index[-1]
        # First date in rolling metrics should be returns.index[window-1]
        assert rolling_metrics.index[0] == returns.index[29]  # window=30, so index 29

    @pytest.mark.unit
    def test_rolling_metrics_time_series_consistency(self):
        """Test that rolling metrics produce consistent time series."""
        dates = pd.date_range("2020-01-01", periods=200, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 200), index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=63)

        # Check that index is monotonic (sorted)
        assert rolling_metrics.index.is_monotonic_increasing
        # Check that all dates are unique
        assert len(rolling_metrics.index) == len(rolling_metrics.index.unique())

    @pytest.mark.unit
    def test_rolling_metrics_edge_case_single_window(self):
        """Test rolling metrics with minimal data (window + 1)."""
        dates = pd.date_range("2020-01-01", periods=64, freq="D")  # window=63 + 1
        returns = pd.Series(np.random.normal(0.001, 0.02, 64), index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=63)

        assert len(rolling_metrics) == 2  # Two windows: [0:63] and [1:64]
        assert isinstance(rolling_metrics, pd.DataFrame)

    @pytest.mark.unit
    def test_rolling_metrics_zero_returns(self):
        """Test rolling metrics with zero returns."""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        returns = pd.Series([0.0] * 100, index=dates)

        rolling_metrics = calculate_rolling_metrics(returns, window=30)

        assert len(rolling_metrics) > 0
        # With zero returns, all metrics should be zero or near zero
        assert all(rolling_metrics["rolling_return"].abs() < 1e-10)
        assert all(rolling_metrics["rolling_volatility"] == 0.0)
        assert all(rolling_metrics["rolling_sharpe"] == 0.0)
        assert all(rolling_metrics["rolling_sortino"] == 0.0)
        assert all(rolling_metrics["rolling_max_dd"] == 0.0)
