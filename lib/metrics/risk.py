"""
Risk metrics calculation for The Researcher's Cockpit.

Provides max drawdown, volatility, VaR, CVaR, alpha, beta, and related risk metrics.
Extracted from core.py as part of v1.0.11 refactoring.
"""

from typing import Optional

import numpy as np
import pandas as pd

from ..data.sanitization import sanitize_value

try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False


# Minimum periods for reliable calculations
MIN_PERIODS_FOR_RATIOS = 20


def _get_daily_rf(annual_rf: float, trading_days: int = 252) -> float:
    """Convert annual risk-free rate to daily rate."""
    return annual_rf / trading_days


def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown.

    Args:
        returns: Daily returns series

    Returns:
        Maximum drawdown as negative float (or 0 if no drawdown)
    """
    if len(returns) == 0:
        return 0.0

    if EMPYRICAL_AVAILABLE:
        try:
            max_dd = float(ep.max_drawdown(returns))
            return sanitize_value(max_dd)
        except Exception:
            pass

    # Manual calculation
    try:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
        return sanitize_value(max_dd)
    except Exception:
        return 0.0


def calculate_recovery_time(returns: pd.Series) -> Optional[pd.Timedelta]:
    """
    Calculate recovery time from max drawdown to new equity high.

    Args:
        returns: Series of daily returns with datetime index

    Returns:
        pd.Timedelta or None if not yet recovered
    """
    if returns is None or len(returns) == 0:
        return pd.Timedelta(seconds=0)

    try:
        # Validate datetime index
        if not isinstance(returns.index, pd.DatetimeIndex):
            try:
                returns.index = pd.to_datetime(returns.index)
            except Exception:
                return pd.Timedelta(seconds=0)

        # Calculate cumulative returns
        cumulative_returns = (1 + returns).cumprod()

        if cumulative_returns.isna().all() or len(cumulative_returns) == 0:
            return pd.Timedelta(seconds=0)

        # Calculate running maximum
        running_max = cumulative_returns.cummax()

        # Calculate drawdowns
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdown = (cumulative_returns - running_max) / running_max
            drawdown = drawdown.replace([np.inf, -np.inf], 0).fillna(0)

        # Find maximum drawdown
        max_dd_value = drawdown.min()

        if max_dd_value >= 0 or np.isnan(max_dd_value):
            return pd.Timedelta(seconds=0)

        # Find end of max drawdown (lowest trough)
        end_of_max_dd_idx = drawdown.idxmin()

        # Find start (last peak before trough)
        cumulative_before_trough = cumulative_returns[:end_of_max_dd_idx]

        if len(cumulative_before_trough) == 0:
            return pd.Timedelta(seconds=0)

        start_of_max_dd_idx = cumulative_before_trough.idxmax()

        # Find recovery point
        recovery_candidates = cumulative_returns[cumulative_returns.index > end_of_max_dd_idx]

        if len(recovery_candidates) == 0:
            return None  # Has not recovered yet

        peak_value = cumulative_returns[start_of_max_dd_idx]

        if np.isnan(peak_value):
            return pd.Timedelta(seconds=0)

        recovered_mask = recovery_candidates >= peak_value

        if not recovered_mask.any():
            return None  # Has not recovered yet

        recovered_date = recovery_candidates[recovered_mask].index[0]

        return recovered_date - start_of_max_dd_idx

    except Exception:
        return pd.Timedelta(seconds=0)


def calculate_alpha_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> tuple[float, float]:
    """
    Calculate alpha and beta against a benchmark.

    Args:
        returns: Strategy returns series
        benchmark_returns: Benchmark returns series
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year

    Returns:
        Tuple of (alpha, beta)
    """
    if not EMPYRICAL_AVAILABLE:
        return 0.0, 1.0

    if benchmark_returns is None or len(benchmark_returns) == 0:
        return 0.0, 1.0

    try:
        # Validate returns
        if returns is None or len(returns) == 0:
            return 0.0, 1.0

        # Align returns and benchmark
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
        aligned_returns = aligned_returns.dropna()
        aligned_benchmark = aligned_benchmark.dropna()

        if len(aligned_returns) < MIN_PERIODS_FOR_RATIOS or len(aligned_benchmark) < MIN_PERIODS_FOR_RATIOS:
            return 0.0, 1.0

        # Calculate alpha and beta
        daily_rf = _get_daily_rf(risk_free_rate, trading_days_per_year)

        alpha = float(ep.alpha(
            aligned_returns,
            aligned_benchmark,
            risk_free=daily_rf,
            period='daily',
            annualization=trading_days_per_year
        ))

        beta = float(ep.beta(aligned_returns, aligned_benchmark))

        return sanitize_value(alpha), sanitize_value(beta, default=1.0)

    except Exception:
        return 0.0, 1.0


def calculate_omega_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> float:
    """
    Calculate Omega ratio.

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year

    Returns:
        Omega ratio as float
    """
    if not EMPYRICAL_AVAILABLE:
        return 0.0

    try:
        daily_rf = _get_daily_rf(risk_free_rate, trading_days_per_year)
        omega = float(ep.omega_ratio(
            returns,
            risk_free=daily_rf,
            required_return=0.0,
            annualization=trading_days_per_year
        ))
        return sanitize_value(omega)
    except Exception:
        return 0.0


def calculate_tail_ratio(returns: pd.Series) -> float:
    """
    Calculate tail ratio (95th percentile / 5th percentile).

    Args:
        returns: Daily returns series

    Returns:
        Tail ratio as float
    """
    if not EMPYRICAL_AVAILABLE:
        return 0.0

    try:
        tail_ratio = float(ep.tail_ratio(returns))
        return sanitize_value(tail_ratio)
    except Exception:
        return 0.0


def calculate_max_drawdown_duration(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown duration in days.

    Args:
        returns: Daily returns series

    Returns:
        Maximum drawdown duration in days
    """
    if not EMPYRICAL_AVAILABLE:
        return 0.0

    try:
        max_dd_duration = ep.max_drawdown_duration(returns)
        if max_dd_duration is not None:
            if isinstance(max_dd_duration, pd.Timedelta):
                return sanitize_value(max_dd_duration.total_seconds() / (60 * 60 * 24))
            else:
                return sanitize_value(float(max_dd_duration))
        return 0.0
    except Exception:
        return 0.0
