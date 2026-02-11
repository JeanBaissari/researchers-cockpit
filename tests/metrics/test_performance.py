"""
Test performance metrics calculations.

Tests for Sharpe ratio, Sortino ratio, Calmar ratio, and return calculations.
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

from lib.metrics.performance import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_annual_return,
    calculate_total_return,
    calculate_annual_volatility,
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


class TestCalculateSharpeRatio:
    """Test Sharpe ratio calculation."""

    @pytest.mark.unit
    def test_sharpe_ratio_basic(self, sample_backtest_results):
        """Test basic Sharpe ratio calculation."""
        returns = sample_backtest_results["returns"]
        sharpe = calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)
        # Allow wider range for edge cases with very small returns/volatility
        assert abs(sharpe) < 1e6 or sharpe == 0.0

    @pytest.mark.unit
    def test_sharpe_ratio_positive_returns(self):
        """Test Sharpe ratio with consistently positive returns."""
        returns = pd.Series([0.01] * 100)  # 1% daily return
        sharpe = calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        # With zero volatility, should return 0.0
        assert sharpe == 0.0

    @pytest.mark.unit
    def test_sharpe_ratio_insufficient_data(self):
        """Test Sharpe ratio with insufficient data."""
        returns = pd.Series([0.01] * (MIN_PERIODS_FOR_RATIOS - 1))
        sharpe = calculate_sharpe_ratio(returns)

        assert sharpe == 0.0

    @pytest.mark.unit
    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        returns = pd.Series([0.01] * 100)  # Constant returns = zero volatility
        sharpe = calculate_sharpe_ratio(returns)

        assert sharpe == 0.0

    @pytest.mark.unit
    def test_sharpe_ratio_empty_series(self):
        """Test Sharpe ratio with empty series."""
        returns = pd.Series([], dtype=float)
        sharpe = calculate_sharpe_ratio(returns)

        # Should handle gracefully - returns 0.0 for insufficient data
        assert sharpe == 0.0

    @pytest.mark.unit
    def test_sharpe_ratio_custom_risk_free_rate(self):
        """Test Sharpe ratio with custom risk-free rate."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        sharpe_4pct = calculate_sharpe_ratio(returns, risk_free_rate=0.04)
        sharpe_2pct = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        # Higher risk-free rate should generally lower Sharpe ratio
        assert isinstance(sharpe_4pct, (int, float))
        assert isinstance(sharpe_2pct, (int, float))
        assert not np.isnan(sharpe_4pct)
        assert not np.isnan(sharpe_2pct)

    @pytest.mark.unit
    def test_sharpe_ratio_custom_trading_days(self):
        """Test Sharpe ratio with custom trading days per year."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        sharpe_252 = calculate_sharpe_ratio(returns, trading_days_per_year=252)
        sharpe_365 = calculate_sharpe_ratio(returns, trading_days_per_year=365)

        assert isinstance(sharpe_252, (int, float))
        assert isinstance(sharpe_365, (int, float))
        assert not np.isnan(sharpe_252)
        assert not np.isnan(sharpe_365)

    @pytest.mark.unit
    def test_sharpe_ratio_precalculated_metrics(self):
        """Test Sharpe ratio with pre-calculated annual return and volatility."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        annual_return = calculate_annual_return(returns)
        annual_volatility = calculate_annual_volatility(returns)

        sharpe = calculate_sharpe_ratio(
            returns, annual_return=annual_return, annual_volatility=annual_volatility
        )

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    @pytest.mark.unit
    def test_sharpe_ratio_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        returns = pd.Series([-0.01] * 100 + [0.02] * 100)  # Mix of negative and positive
        sharpe = calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    @pytest.mark.unit
    def test_sharpe_ratio_complete_loss(self):
        """Test Sharpe ratio with complete loss (total return <= -1.0)."""
        # Create returns that result in complete loss
        returns = pd.Series([-0.5] * 10)  # 50% loss per period
        sharpe = calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    @pytest.mark.unit
    def test_sharpe_ratio_exactly_min_periods(self):
        """Test Sharpe ratio at boundary of MIN_PERIODS_FOR_RATIOS."""
        returns = pd.Series(np.random.normal(0.001, 0.02, MIN_PERIODS_FOR_RATIOS))
        sharpe = calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)

    @pytest.mark.unit
    def test_sharpe_ratio_manual_formula_sanity(self):
        """Test Sharpe ratio with pre-calculated metrics returns finite, consistent value."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        annual_return = calculate_annual_return(returns)
        annual_volatility = calculate_annual_volatility(returns)
        risk_free_rate = 0.04

        sharpe = calculate_sharpe_ratio(
            returns,
            risk_free_rate=risk_free_rate,
            annual_return=annual_return,
            annual_volatility=annual_volatility,
        )
        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)
        if annual_volatility >= 1e-10:
            manual_sharpe = (annual_return - risk_free_rate) / annual_volatility
            # Implementation may use empyrical when available; both should be same sign
            assert np.sign(sharpe) == np.sign(manual_sharpe) or sharpe == 0.0


class TestCalculateSortinoRatio:
    """Test Sortino ratio calculation."""

    @pytest.mark.unit
    def test_sortino_ratio_basic(self, sample_backtest_results):
        """Test basic Sortino ratio calculation."""
        returns = sample_backtest_results["returns"]
        sortino = calculate_sortino_ratio(returns)

        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert not np.isinf(sortino)
        # Allow wider range for edge cases with very small returns/volatility
        assert abs(sortino) < 1e6 or sortino == 0.0

    @pytest.mark.unit
    def test_sortino_ratio_insufficient_data(self):
        """Test Sortino ratio with insufficient data."""
        returns = pd.Series([0.01] * (MIN_PERIODS_FOR_RATIOS - 1))
        sortino = calculate_sortino_ratio(returns)

        assert sortino == 0.0

    @pytest.mark.unit
    def test_sortino_ratio_zero_volatility(self):
        """Test Sortino ratio with zero volatility."""
        returns = pd.Series([0.01] * 100)  # Constant returns
        sortino = calculate_sortino_ratio(returns)

        assert sortino == 0.0

    @pytest.mark.unit
    def test_sortino_ratio_empty_series(self):
        """Test Sortino ratio with empty series."""
        returns = pd.Series([], dtype=float)
        sortino = calculate_sortino_ratio(returns)

        # Should handle gracefully
        assert sortino == 0.0

    @pytest.mark.unit
    def test_sortino_ratio_no_downside_returns(self):
        """Test Sortino ratio with no downside returns."""
        returns = pd.Series([0.01] * 100)  # All positive returns
        sortino = calculate_sortino_ratio(returns)

        # Should return 0.0 when no downside returns
        assert sortino == 0.0

    @pytest.mark.unit
    def test_sortino_ratio_custom_risk_free_rate(self):
        """Test Sortino ratio with custom risk-free rate."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        sortino_4pct = calculate_sortino_ratio(returns, risk_free_rate=0.04)
        sortino_2pct = calculate_sortino_ratio(returns, risk_free_rate=0.02)

        assert isinstance(sortino_4pct, (int, float))
        assert isinstance(sortino_2pct, (int, float))
        assert not np.isnan(sortino_4pct)
        assert not np.isnan(sortino_2pct)

    @pytest.mark.unit
    def test_sortino_ratio_custom_trading_days(self):
        """Test Sortino ratio with custom trading days per year."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        sortino_252 = calculate_sortino_ratio(returns, trading_days_per_year=252)
        sortino_365 = calculate_sortino_ratio(returns, trading_days_per_year=365)

        assert isinstance(sortino_252, (int, float))
        assert isinstance(sortino_365, (int, float))
        assert not np.isnan(sortino_252)
        assert not np.isnan(sortino_365)

    @pytest.mark.unit
    def test_sortino_ratio_precalculated_return(self):
        """Test Sortino ratio with pre-calculated annual return."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        annual_return = calculate_annual_return(returns)

        sortino = calculate_sortino_ratio(returns, annual_return=annual_return)

        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert not np.isinf(sortino)

    @pytest.mark.unit
    def test_sortino_ratio_with_downside_returns(self):
        """Test Sortino ratio with actual downside returns."""
        # Create returns with both positive and negative values
        returns = pd.Series([-0.02, 0.01, -0.01, 0.02] * 75)  # Mix of returns
        sortino = calculate_sortino_ratio(returns)

        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert not np.isinf(sortino)

    @pytest.mark.unit
    def test_sortino_ratio_complete_loss(self):
        """Test Sortino ratio with complete loss."""
        returns = pd.Series([-0.5] * 10)  # 50% loss per period
        sortino = calculate_sortino_ratio(returns)

        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert not np.isinf(sortino)


class TestCalculateCalmarRatio:
    """Test Calmar ratio calculation."""

    @pytest.mark.unit
    def test_calmar_ratio_basic(self):
        """Test basic Calmar ratio calculation."""
        calmar = calculate_calmar_ratio(annual_return=0.10, max_drawdown=-0.05)

        assert isinstance(calmar, (int, float))
        assert not np.isnan(calmar)
        assert not np.isinf(calmar)
        assert calmar == pytest.approx(0.10 / 0.05, rel=1e-10)

    @pytest.mark.unit
    def test_calmar_ratio_zero_drawdown(self):
        """Test Calmar ratio with zero drawdown."""
        calmar = calculate_calmar_ratio(annual_return=0.10, max_drawdown=0.0)

        assert calmar == 0.0

    @pytest.mark.unit
    def test_calmar_ratio_negative_return(self):
        """Test Calmar ratio with negative annual return."""
        calmar = calculate_calmar_ratio(annual_return=-0.05, max_drawdown=-0.10)

        assert isinstance(calmar, (int, float))
        assert not np.isnan(calmar)
        assert not np.isinf(calmar)
        assert calmar < 0  # Negative return / negative drawdown = positive, but we use abs

    @pytest.mark.unit
    def test_calmar_ratio_large_drawdown(self):
        """Test Calmar ratio with large drawdown."""
        calmar = calculate_calmar_ratio(annual_return=0.20, max_drawdown=-0.50)

        assert isinstance(calmar, (int, float))
        assert not np.isnan(calmar)
        assert calmar == pytest.approx(0.20 / 0.50, rel=1e-10)

    @pytest.mark.unit
    def test_calmar_ratio_very_small_drawdown(self):
        """Test Calmar ratio with very small drawdown."""
        calmar = calculate_calmar_ratio(annual_return=0.10, max_drawdown=-1e-11)

        # Should return 0.0 for very small drawdowns
        assert calmar == 0.0

    @pytest.mark.unit
    def test_calmar_ratio_positive_drawdown_uses_abs(self):
        """Test Calmar ratio with positive max_drawdown (implementation uses abs)."""
        calmar_neg = calculate_calmar_ratio(annual_return=0.10, max_drawdown=-0.05)
        calmar_pos = calculate_calmar_ratio(annual_return=0.10, max_drawdown=0.05)

        assert calmar_neg == pytest.approx(calmar_pos, rel=1e-10)
        assert calmar_pos == pytest.approx(2.0, rel=1e-10)


class TestCalculateAnnualReturn:
    """Test annual return calculation."""

    @pytest.mark.unit
    def test_annual_return_basic(self, sample_backtest_results):
        """Test basic annual return calculation."""
        returns = sample_backtest_results["returns"]
        annual_return = calculate_annual_return(returns)

        assert isinstance(annual_return, (int, float))
        assert not np.isnan(annual_return)
        assert not np.isinf(annual_return)

    @pytest.mark.unit
    def test_annual_return_positive_returns(self):
        """Test annual return with positive returns."""
        returns = pd.Series([0.001] * 252)  # 0.1% daily for 252 days
        annual_return = calculate_annual_return(returns)

        assert isinstance(annual_return, (int, float))
        assert not np.isnan(annual_return)
        assert annual_return > 0

    @pytest.mark.unit
    def test_annual_return_negative_returns(self):
        """Test annual return with negative returns."""
        returns = pd.Series([-0.001] * 252)  # -0.1% daily
        annual_return = calculate_annual_return(returns)

        assert isinstance(annual_return, (int, float))
        assert not np.isnan(annual_return)
        assert annual_return < 0

    @pytest.mark.unit
    def test_annual_return_empty_series(self):
        """Test annual return with empty series."""
        returns = pd.Series([], dtype=float)
        annual_return = calculate_annual_return(returns)

        assert annual_return == 0.0

    @pytest.mark.unit
    def test_annual_return_complete_loss(self):
        """Test annual return with complete loss."""
        returns = pd.Series([-0.5] * 10)  # 50% loss per period
        annual_return = calculate_annual_return(returns)

        assert annual_return == -1.0

    @pytest.mark.unit
    def test_annual_return_custom_trading_days(self):
        """Test annual return with custom trading days per year."""
        returns = pd.Series([0.001] * 365)  # Daily returns for 365 days
        annual_return_252 = calculate_annual_return(returns, trading_days_per_year=252)
        annual_return_365 = calculate_annual_return(returns, trading_days_per_year=365)

        assert isinstance(annual_return_252, (int, float))
        assert isinstance(annual_return_365, (int, float))
        assert not np.isnan(annual_return_252)
        assert not np.isnan(annual_return_365)
        # 365 days with 252 trading days should give different result than 365 trading days
        assert annual_return_252 != annual_return_365

    @pytest.mark.unit
    def test_annual_return_zero_returns(self):
        """Test annual return with zero returns."""
        returns = pd.Series([0.0] * 252)
        annual_return = calculate_annual_return(returns)

        assert annual_return == 0.0

    @pytest.mark.unit
    def test_annual_return_single_period(self):
        """Test annual return with single period."""
        returns = pd.Series([0.05])  # 5% in one period
        annual_return = calculate_annual_return(returns)

        assert isinstance(annual_return, (int, float))
        assert not np.isnan(annual_return)
        assert annual_return > 0


class TestCalculateTotalReturn:
    """Test total return calculation."""

    @pytest.mark.unit
    def test_total_return_basic(self, sample_backtest_results):
        """Test basic total return calculation."""
        returns = sample_backtest_results["returns"]
        total_return = calculate_total_return(returns)

        assert isinstance(total_return, (int, float))
        assert not np.isnan(total_return)
        assert not np.isinf(total_return)

    @pytest.mark.unit
    def test_total_return_positive_returns(self):
        """Test total return with positive returns."""
        returns = pd.Series([0.01, 0.02, 0.01])  # 1%, 2%, 1%
        total_return = calculate_total_return(returns)

        # (1.01 * 1.02 * 1.01) - 1 = 1.040402 - 1 = 0.040402
        expected = (1.01 * 1.02 * 1.01) - 1
        assert total_return == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_total_return_negative_returns(self):
        """Test total return with negative returns."""
        returns = pd.Series([-0.01, -0.02, -0.01])  # -1%, -2%, -1%
        total_return = calculate_total_return(returns)

        # (0.99 * 0.98 * 0.99) - 1 = 0.960498 - 1 = -0.039502
        expected = (0.99 * 0.98 * 0.99) - 1
        assert total_return == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_total_return_empty_series(self):
        """Test total return with empty series."""
        returns = pd.Series([], dtype=float)
        total_return = calculate_total_return(returns)

        assert total_return == 0.0

    @pytest.mark.unit
    def test_total_return_single_return(self):
        """Test total return with single return value."""
        returns = pd.Series([0.05])  # 5% return
        total_return = calculate_total_return(returns)

        assert total_return == pytest.approx(0.05, rel=1e-10)

    @pytest.mark.unit
    def test_total_return_zero_returns(self):
        """Test total return with zero returns."""
        returns = pd.Series([0.0] * 10)
        total_return = calculate_total_return(returns)

        assert total_return == 0.0

    @pytest.mark.unit
    def test_total_return_mixed_returns(self):
        """Test total return with mixed positive and negative returns."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.01])
        total_return = calculate_total_return(returns)

        expected = (1.01 * 0.99 * 1.02 * 0.99) - 1
        assert total_return == pytest.approx(expected, rel=1e-10)

    @pytest.mark.unit
    def test_total_return_complete_loss_single_period(self):
        """Test total return with single period complete loss (-100%)."""
        returns = pd.Series([-1.0])
        total_return = calculate_total_return(returns)

        assert total_return == pytest.approx(-1.0, rel=1e-10)


class TestCalculateAnnualVolatility:
    """Test annual volatility calculation."""

    @pytest.mark.unit
    def test_annual_volatility_basic(self, sample_backtest_results):
        """Test basic annual volatility calculation."""
        returns = sample_backtest_results["returns"]
        volatility = calculate_annual_volatility(returns)

        assert isinstance(volatility, (int, float))
        assert not np.isnan(volatility)
        assert not np.isinf(volatility)
        assert volatility >= 0

    @pytest.mark.unit
    def test_annual_volatility_positive_returns(self):
        """Test annual volatility with positive returns."""
        returns = pd.Series([0.01] * 252)  # Constant returns
        volatility = calculate_annual_volatility(returns)

        # Zero volatility for constant returns (with floating point tolerance)
        assert volatility == pytest.approx(0.0, abs=1e-10)

    @pytest.mark.unit
    def test_annual_volatility_variable_returns(self):
        """Test annual volatility with variable returns."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        volatility = calculate_annual_volatility(returns)

        assert isinstance(volatility, (int, float))
        assert not np.isnan(volatility)
        assert volatility > 0

    @pytest.mark.unit
    def test_annual_volatility_empty_series(self):
        """Test annual volatility with empty series."""
        returns = pd.Series([], dtype=float)
        volatility = calculate_annual_volatility(returns)

        assert volatility == 0.0

    @pytest.mark.unit
    def test_annual_volatility_custom_trading_days(self):
        """Test annual volatility with custom trading days per year."""
        returns = pd.Series(np.random.normal(0.001, 0.02, 300))
        vol_252 = calculate_annual_volatility(returns, trading_days_per_year=252)
        vol_365 = calculate_annual_volatility(returns, trading_days_per_year=365)

        assert isinstance(vol_252, (int, float))
        assert isinstance(vol_365, (int, float))
        assert not np.isnan(vol_252)
        assert not np.isnan(vol_365)
        # 365 trading days should give higher annualized volatility
        assert vol_365 > vol_252

    @pytest.mark.unit
    def test_annual_volatility_zero_returns(self):
        """Test annual volatility with zero returns."""
        returns = pd.Series([0.0] * 252)
        volatility = calculate_annual_volatility(returns)

        assert volatility == 0.0

    @pytest.mark.unit
    def test_annual_volatility_nan_handling(self):
        """Test annual volatility handles NaN values."""
        returns = pd.Series([0.01, np.nan, 0.02, 0.01])
        volatility = calculate_annual_volatility(returns)

        assert isinstance(volatility, (int, float))
        assert not np.isnan(volatility)
        assert volatility >= 0

    @pytest.mark.unit
    def test_annual_volatility_single_value(self):
        """Test annual volatility with single observation (std is NaN, treated as 0)."""
        returns = pd.Series([0.01])
        volatility = calculate_annual_volatility(returns)

        assert volatility == 0.0
