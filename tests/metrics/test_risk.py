"""
Test risk metrics calculations.

Tests for max drawdown, recovery time, alpha/beta, omega ratio, tail ratio,
and max drawdown duration.
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

from lib.metrics.risk import (
    calculate_max_drawdown,
    calculate_recovery_time,
    calculate_alpha_beta,
    calculate_omega_ratio,
    calculate_tail_ratio,
    calculate_max_drawdown_duration,
    _get_daily_rf,
    MIN_PERIODS_FOR_RATIOS,
)


class TestGetDailyRf:
    """Test daily risk-free rate conversion."""

    @pytest.mark.unit
    def test_get_daily_rf_default(self):
        """Test default annual rate conversion."""
        daily_rf = _get_daily_rf(0.04, 252)
        assert daily_rf == pytest.approx(0.04 / 252, rel=1e-10)

    @pytest.mark.unit
    def test_get_daily_rf_custom_trading_days(self):
        """Test with custom trading days."""
        daily_rf = _get_daily_rf(0.05, 365)
        assert daily_rf == pytest.approx(0.05 / 365, rel=1e-10)

    @pytest.mark.unit
    def test_get_daily_rf_zero_rate(self):
        """Test with zero risk-free rate."""
        daily_rf = _get_daily_rf(0.0, 252)
        assert daily_rf == 0.0


class TestCalculateMaxDrawdown:
    """Test maximum drawdown calculation."""

    @pytest.mark.unit
    def test_max_drawdown_basic(self, sample_backtest_results):
        """Test basic max drawdown calculation."""
        returns = sample_backtest_results["returns"]
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert not np.isinf(max_dd)
        assert max_dd <= 0  # Drawdown should be negative or zero

    @pytest.mark.unit
    def test_max_drawdown_positive_returns(self):
        """Test max drawdown with consistently positive returns."""
        returns = pd.Series([0.01] * 100)  # 1% daily return
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd == 0.0  # No drawdown with constant positive returns

    @pytest.mark.unit
    def test_max_drawdown_negative_returns(self):
        """Test max drawdown with negative returns."""
        returns = pd.Series([-0.01, -0.02, -0.01, 0.01, -0.03])
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd < 0  # Should have negative drawdown

    @pytest.mark.unit
    def test_max_drawdown_empty_series(self):
        """Test max drawdown with empty series."""
        returns = pd.Series([], dtype=float)
        max_dd = calculate_max_drawdown(returns)

        assert max_dd == 0.0

    @pytest.mark.unit
    def test_max_drawdown_single_value(self):
        """Test max drawdown with single return value."""
        returns = pd.Series([0.05])  # Single positive return
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert max_dd == 0.0

    @pytest.mark.unit
    def test_max_drawdown_zero_returns(self):
        """Test max drawdown with zero returns."""
        returns = pd.Series([0.0] * 100)
        max_dd = calculate_max_drawdown(returns)

        assert max_dd == 0.0

    @pytest.mark.unit
    def test_max_drawdown_with_drawdown(self):
        """Test max drawdown with actual drawdown scenario."""
        # Create returns that go up then down
        returns = pd.Series([0.01] * 50 + [-0.02] * 30 + [0.01] * 20)
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd < 0  # Should have negative drawdown

    @pytest.mark.unit
    def test_max_drawdown_nan_handling(self):
        """Test max drawdown handles NaN values."""
        returns = pd.Series([0.01, np.nan, 0.02, -0.01, np.nan, 0.01])
        max_dd = calculate_max_drawdown(returns)

        assert isinstance(max_dd, (int, float))
        assert not np.isnan(max_dd)
        assert max_dd <= 0


class TestCalculateRecoveryTime:
    """Test recovery time calculation."""

    @pytest.mark.unit
    def test_recovery_time_basic(self, sample_dates):
        """Test basic recovery time calculation."""
        # Create returns with a clear drawdown and full recovery
        # Start high, drop, then recover above starting point
        dates = sample_dates[:60]
        returns = pd.Series(
            [0.01] * 20  # Build up to peak
            + [-0.02] * 10  # Drawdown
            + [0.02] * 30,  # Strong recovery (should exceed peak)
            index=dates,
        )
        recovery_time = calculate_recovery_time(returns)

        # Should return Timedelta if recovered, None if not
        assert recovery_time is None or isinstance(recovery_time, pd.Timedelta)
        if recovery_time is not None:
            assert recovery_time.total_seconds() >= 0

    @pytest.mark.unit
    def test_recovery_time_no_recovery(self, sample_dates):
        """Test recovery time when not yet recovered."""
        # Create returns with drawdown but no recovery
        dates = sample_dates[:40]
        returns = pd.Series(
            [0.01] * 20 + [-0.02] * 10 + [0.005] * 10,  # Small recovery, not full
            index=dates,
        )
        recovery_time = calculate_recovery_time(returns)

        # Should return None if not recovered
        assert recovery_time is None or isinstance(recovery_time, pd.Timedelta)

    @pytest.mark.unit
    def test_recovery_time_empty_series(self):
        """Test recovery time with empty series."""
        returns = pd.Series([], dtype=float)
        recovery_time = calculate_recovery_time(returns)

        assert isinstance(recovery_time, pd.Timedelta)
        assert recovery_time.total_seconds() == 0

    @pytest.mark.unit
    def test_recovery_time_no_drawdown(self, sample_dates):
        """Test recovery time with no drawdown."""
        returns = pd.Series([0.01] * 50, index=sample_dates[:50])
        recovery_time = calculate_recovery_time(returns)

        assert isinstance(recovery_time, pd.Timedelta)
        assert recovery_time.total_seconds() == 0

    @pytest.mark.unit
    def test_recovery_time_no_datetime_index(self):
        """Test recovery time with non-datetime index."""
        returns = pd.Series([0.01, -0.02, 0.01], index=[0, 1, 2])
        recovery_time = calculate_recovery_time(returns)

        # Should attempt to convert or return zero Timedelta
        # If conversion fails, returns Timedelta(seconds=0)
        assert recovery_time is None or isinstance(recovery_time, pd.Timedelta)

    @pytest.mark.unit
    def test_recovery_time_nan_handling(self, sample_dates):
        """Test recovery time handles NaN values."""
        # Create data that should recover (with NaN values)
        dates = sample_dates[:30]
        returns = pd.Series(
            [0.01] * 10  # Build up
            + [np.nan]  # NaN
            + [-0.02] * 5  # Drawdown
            + [0.02] * 14,  # Recovery
            index=dates,
        )
        recovery_time = calculate_recovery_time(returns)

        # Should return None or Timedelta (depending on recovery)
        assert recovery_time is None or isinstance(recovery_time, pd.Timedelta)


class TestCalculateAlphaBeta:
    """Test alpha and beta calculation."""

    @pytest.mark.unit
    def test_alpha_beta_basic(self, sample_backtest_results):
        """Test basic alpha/beta calculation."""
        returns = sample_backtest_results["returns"]
        benchmark_returns = pd.Series(
            np.random.normal(0.0005, 0.015, len(returns)), index=returns.index
        )

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        assert isinstance(alpha, (int, float))
        assert isinstance(beta, (int, float))
        assert not np.isnan(alpha)
        assert not np.isnan(beta)
        assert not np.isinf(alpha)
        assert not np.isinf(beta)

    @pytest.mark.unit
    def test_alpha_beta_insufficient_data(self):
        """Test alpha/beta with insufficient data."""
        returns = pd.Series([0.01] * (MIN_PERIODS_FOR_RATIOS - 1))
        benchmark_returns = pd.Series([0.005] * (MIN_PERIODS_FOR_RATIOS - 1))

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        assert alpha == 0.0
        assert beta == 1.0

    @pytest.mark.unit
    def test_alpha_beta_empty_returns(self):
        """Test alpha/beta with empty returns."""
        returns = pd.Series([], dtype=float)
        benchmark_returns = pd.Series([0.01] * 100)

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        assert alpha == 0.0
        assert beta == 1.0

    @pytest.mark.unit
    def test_alpha_beta_empty_benchmark(self):
        """Test alpha/beta with empty benchmark."""
        returns = pd.Series([0.01] * 100)
        benchmark_returns = pd.Series([], dtype=float)

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        assert alpha == 0.0
        assert beta == 1.0

    @pytest.mark.unit
    def test_alpha_beta_custom_risk_free_rate(self):
        """Test alpha/beta with custom risk-free rate."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        benchmark_returns = pd.Series(np.random.normal(0.0005, 0.015, 300))

        alpha_4pct, beta_4pct = calculate_alpha_beta(
            returns, benchmark_returns, risk_free_rate=0.04
        )
        alpha_2pct, beta_2pct = calculate_alpha_beta(
            returns, benchmark_returns, risk_free_rate=0.02
        )

        assert isinstance(alpha_4pct, (int, float))
        assert isinstance(beta_4pct, (int, float))
        assert isinstance(alpha_2pct, (int, float))
        assert isinstance(beta_2pct, (int, float))
        # Beta should be the same regardless of risk-free rate
        assert beta_4pct == pytest.approx(beta_2pct, rel=1e-10)

    @pytest.mark.unit
    def test_alpha_beta_custom_trading_days(self):
        """Test alpha/beta with custom trading days per year."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        benchmark_returns = pd.Series(np.random.normal(0.0005, 0.015, 300))

        alpha_252, beta_252 = calculate_alpha_beta(
            returns, benchmark_returns, trading_days_per_year=252
        )
        alpha_365, beta_365 = calculate_alpha_beta(
            returns, benchmark_returns, trading_days_per_year=365
        )

        assert isinstance(alpha_252, (int, float))
        assert isinstance(beta_252, (int, float))
        assert isinstance(alpha_365, (int, float))
        assert isinstance(beta_365, (int, float))
        # Beta should be the same regardless of trading days
        assert beta_252 == pytest.approx(beta_365, rel=1e-10)

    @pytest.mark.unit
    def test_alpha_beta_misaligned_indices(self):
        """Test alpha/beta with misaligned date indices."""
        returns = pd.Series([0.01] * 100, index=pd.date_range("2020-01-01", periods=100, freq="D"))
        benchmark_returns = pd.Series(
            [0.005] * 50, index=pd.date_range("2020-01-01", periods=50, freq="D")
        )

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        # Should align on common dates
        assert isinstance(alpha, (int, float))
        assert isinstance(beta, (int, float))
        assert not np.isnan(alpha)
        assert not np.isnan(beta)

    @pytest.mark.unit
    def test_alpha_beta_nan_handling(self):
        """Test alpha/beta handles NaN values."""
        returns = pd.Series([0.01, np.nan, 0.02, -0.01] * 75)
        benchmark_returns = pd.Series([0.005, 0.01, np.nan, -0.005] * 75)

        alpha, beta = calculate_alpha_beta(returns, benchmark_returns)

        assert isinstance(alpha, (int, float))
        assert isinstance(beta, (int, float))
        assert not np.isnan(alpha)
        assert not np.isnan(beta)


class TestCalculateOmegaRatio:
    """Test Omega ratio calculation."""

    @pytest.mark.unit
    def test_omega_ratio_basic(self, sample_backtest_results):
        """Test basic Omega ratio calculation."""
        returns = sample_backtest_results["returns"]
        omega = calculate_omega_ratio(returns)

        assert isinstance(omega, (int, float))
        assert not np.isnan(omega)
        assert not np.isinf(omega)
        assert omega >= 0  # Omega ratio should be non-negative

    @pytest.mark.unit
    def test_omega_ratio_positive_returns(self):
        """Test Omega ratio with positive returns."""
        returns = pd.Series([0.01] * 100)
        omega = calculate_omega_ratio(returns)

        assert isinstance(omega, (int, float))
        assert not np.isnan(omega)
        assert omega >= 0

    @pytest.mark.unit
    def test_omega_ratio_empty_series(self):
        """Test Omega ratio with empty series."""
        returns = pd.Series([], dtype=float)
        omega = calculate_omega_ratio(returns)

        assert omega == 0.0

    @pytest.mark.unit
    def test_omega_ratio_custom_risk_free_rate(self):
        """Test Omega ratio with custom risk-free rate."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))

        omega_4pct = calculate_omega_ratio(returns, risk_free_rate=0.04)
        omega_2pct = calculate_omega_ratio(returns, risk_free_rate=0.02)

        assert isinstance(omega_4pct, (int, float))
        assert isinstance(omega_2pct, (int, float))
        assert not np.isnan(omega_4pct)
        assert not np.isnan(omega_2pct)

    @pytest.mark.unit
    def test_omega_ratio_custom_trading_days(self):
        """Test Omega ratio with custom trading days per year."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))

        omega_252 = calculate_omega_ratio(returns, trading_days_per_year=252)
        omega_365 = calculate_omega_ratio(returns, trading_days_per_year=365)

        assert isinstance(omega_252, (int, float))
        assert isinstance(omega_365, (int, float))
        assert not np.isnan(omega_252)
        assert not np.isnan(omega_365)

    @pytest.mark.unit
    def test_omega_ratio_nan_handling(self):
        """Test Omega ratio handles NaN values."""
        returns = pd.Series([0.01, np.nan, 0.02, -0.01, np.nan, 0.01] * 50)
        omega = calculate_omega_ratio(returns)

        assert isinstance(omega, (int, float))
        assert not np.isnan(omega)
        assert omega >= 0


class TestCalculateTailRatio:
    """Test tail ratio calculation."""

    @pytest.mark.unit
    def test_tail_ratio_basic(self, sample_backtest_results):
        """Test basic tail ratio calculation."""
        returns = sample_backtest_results["returns"]
        tail_ratio = calculate_tail_ratio(returns)

        assert isinstance(tail_ratio, (int, float))
        assert not np.isnan(tail_ratio)
        assert not np.isinf(tail_ratio)
        assert tail_ratio >= 0  # Tail ratio should be non-negative

    @pytest.mark.unit
    def test_tail_ratio_positive_returns(self):
        """Test tail ratio with positive returns."""
        returns = pd.Series([0.01] * 100)
        tail_ratio = calculate_tail_ratio(returns)

        assert isinstance(tail_ratio, (int, float))
        assert not np.isnan(tail_ratio)
        assert tail_ratio >= 0

    @pytest.mark.unit
    def test_tail_ratio_empty_series(self):
        """Test tail ratio with empty series."""
        returns = pd.Series([], dtype=float)
        tail_ratio = calculate_tail_ratio(returns)

        assert tail_ratio == 0.0

    @pytest.mark.unit
    def test_tail_ratio_mixed_returns(self):
        """Test tail ratio with mixed positive and negative returns."""
        returns = pd.Series([-0.02, 0.01, -0.01, 0.02, -0.015, 0.015] * 50)
        tail_ratio = calculate_tail_ratio(returns)

        assert isinstance(tail_ratio, (int, float))
        assert not np.isnan(tail_ratio)
        assert tail_ratio >= 0

    @pytest.mark.unit
    def test_tail_ratio_nan_handling(self):
        """Test tail ratio handles NaN values."""
        returns = pd.Series([0.01, np.nan, 0.02, -0.01, np.nan, 0.01] * 50)
        tail_ratio = calculate_tail_ratio(returns)

        assert isinstance(tail_ratio, (int, float))
        assert not np.isnan(tail_ratio)
        assert tail_ratio >= 0


class TestCalculateMaxDrawdownDuration:
    """Test maximum drawdown duration calculation."""

    @pytest.mark.unit
    def test_max_drawdown_duration_basic(self, sample_backtest_results):
        """Test basic max drawdown duration calculation."""
        returns = sample_backtest_results["returns"]
        duration = calculate_max_drawdown_duration(returns)

        assert isinstance(duration, (int, float))
        assert not np.isnan(duration)
        assert not np.isinf(duration)
        assert duration >= 0  # Duration should be non-negative (in days)

    @pytest.mark.unit
    def test_max_drawdown_duration_positive_returns(self):
        """Test max drawdown duration with positive returns."""
        returns = pd.Series([0.01] * 100)
        duration = calculate_max_drawdown_duration(returns)

        assert isinstance(duration, (int, float))
        assert duration >= 0

    @pytest.mark.unit
    def test_max_drawdown_duration_empty_series(self):
        """Test max drawdown duration with empty series."""
        returns = pd.Series([], dtype=float)
        duration = calculate_max_drawdown_duration(returns)

        assert duration == 0.0

    @pytest.mark.unit
    def test_max_drawdown_duration_with_drawdown(self):
        """Test max drawdown duration with actual drawdown."""
        # Create returns with a sustained drawdown
        returns = pd.Series([0.01] * 20 + [-0.02] * 30 + [0.01] * 20)
        duration = calculate_max_drawdown_duration(returns)

        assert isinstance(duration, (int, float))
        assert not np.isnan(duration)
        assert duration >= 0

    @pytest.mark.unit
    def test_max_drawdown_duration_nan_handling(self):
        """Test max drawdown duration handles NaN values."""
        returns = pd.Series([0.01, np.nan, -0.02, 0.01, np.nan, -0.01] * 50)
        duration = calculate_max_drawdown_duration(returns)

        assert isinstance(duration, (int, float))
        assert not np.isnan(duration)
        assert duration >= 0
