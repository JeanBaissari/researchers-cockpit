"""
Performance metrics calculation for The Researcher's Cockpit.

Provides Sharpe ratio, Sortino ratio, Calmar ratio, and return calculations.
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


# Minimum periods for reliable ratio calculations
MIN_PERIODS_FOR_RATIOS = 20


def _get_daily_rf(annual_rf: float, trading_days: int = 252) -> float:
    """Convert annual risk-free rate to daily rate."""
    return annual_rf / trading_days


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252,
    annual_return: Optional[float] = None,
    annual_volatility: Optional[float] = None
) -> float:
    """
    Calculate Sharpe ratio with proper edge case handling.

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year
        annual_return: Pre-calculated annual return (optional)
        annual_volatility: Pre-calculated volatility (optional)

    Returns:
        Sharpe ratio as float
    """
    n_days = len(returns)

    # Insufficient data check
    if n_days < MIN_PERIODS_FOR_RATIOS:
        return 0.0

    # Calculate volatility if not provided
    if annual_volatility is None:
        daily_vol = float(returns.std())
        if np.isnan(daily_vol) or daily_vol < 0:
            daily_vol = 0.0
        annual_volatility = daily_vol * np.sqrt(trading_days_per_year)

    # Zero volatility edge case
    if annual_volatility < 1e-10:
        return 0.0

    # Calculate annual return if not provided
    if annual_return is None:
        total_return = float((1 + returns).prod() - 1)
        if total_return <= -1.0:
            annual_return = -1.0
        else:
            annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)

    # Try empyrical if available
    if EMPYRICAL_AVAILABLE:
        try:
            daily_rf = _get_daily_rf(risk_free_rate, trading_days_per_year)
            sharpe = float(ep.sharpe_ratio(
                returns,
                risk_free=daily_rf,
                period='daily',
                annualization=trading_days_per_year
            ))
            return sanitize_value(sharpe)
        except Exception:
            pass

    # Manual calculation
    excess_return = annual_return - risk_free_rate
    sharpe = sanitize_value(excess_return / annual_volatility)
    return sharpe


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252,
    annual_return: Optional[float] = None
) -> float:
    """
    Calculate Sortino ratio with proper downside deviation.

    Args:
        returns: Daily returns series
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year
        annual_return: Pre-calculated annual return (optional)

    Returns:
        Sortino ratio as float
    """
    n_days = len(returns)

    # Insufficient data check
    if n_days < MIN_PERIODS_FOR_RATIOS:
        return 0.0

    daily_rf = _get_daily_rf(risk_free_rate, trading_days_per_year)

    # Calculate annual return if not provided
    if annual_return is None:
        total_return = float((1 + returns).prod() - 1)
        if total_return <= -1.0:
            annual_return = -1.0
        else:
            annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)

    # ✅ FIX: Check zero volatility BEFORE calling empyrical (DRY + OCP + Fail-Fast)
    # Check if returns have zero volatility (all zeros or constant)
    returns_std = float(returns.std())
    if returns_std < 1e-10:
        return 0.0
    
    excess_returns = returns - daily_rf
    downside_returns = excess_returns[excess_returns < 0]

    # Zero downside deviation = no downside returns edge case
    if len(downside_returns) == 0:
        return 0.0

    # Calculate downside std for validation
    downside_std = float(np.sqrt(np.mean(downside_returns ** 2)))
    annualized_downside_std = downside_std * np.sqrt(trading_days_per_year)

    # Zero downside volatility check (DRY: single check, used by both paths)
    if annualized_downside_std < 1e-10:
        return 0.0

    # Try empyrical if available (now safe - we've validated edge cases)
    if EMPYRICAL_AVAILABLE:
        try:
            sortino = float(ep.sortino_ratio(
                returns,
                required_return=daily_rf,
                period='daily',
                annualization=trading_days_per_year
            ))
            # ✅ FIX: Validate empyrical output (defensive programming)
            sanitized = sanitize_value(sortino)
            # Additional check: empyrical might return inf/nan even after our checks
            if not np.isfinite(sanitized) or sanitized < -1e6 or sanitized > 1e6:
                # Fall back to manual calculation
                pass
            else:
                return sanitized
        except Exception:
            pass

    # Manual calculation (now only reached if empyrical unavailable or returns invalid value)
    excess_annual_return = annual_return - risk_free_rate
    sortino = sanitize_value(excess_annual_return / annualized_downside_std)
    return sortino


def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> float:
    """
    Calculate Calmar ratio (annual return / max drawdown).

    Args:
        annual_return: Annualized return
        max_drawdown: Maximum drawdown (negative value)

    Returns:
        Calmar ratio as float
    """
    if abs(max_drawdown) > 1e-10:
        return sanitize_value(annual_return / abs(max_drawdown))
    return 0.0


def calculate_annual_return(returns: pd.Series, trading_days_per_year: int = 252) -> float:
    """
    Calculate annualized return from daily returns.

    Args:
        returns: Daily returns series
        trading_days_per_year: Trading days per year

    Returns:
        Annualized return as float
    """
    if len(returns) == 0:
        return 0.0

    total_return = float((1 + returns).prod() - 1)
    n_days = len(returns)

    # Handle complete loss
    if total_return <= -1.0:
        return -1.0

    annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)
    return sanitize_value(annual_return)


def calculate_total_return(returns: pd.Series) -> float:
    """
    Calculate total return from daily returns.

    Args:
        returns: Daily returns series

    Returns:
        Total return as float
    """
    if len(returns) == 0:
        return 0.0

    total_return = float((1 + returns).prod() - 1)
    return sanitize_value(total_return)


def calculate_annual_volatility(returns: pd.Series, trading_days_per_year: int = 252) -> float:
    """
    Calculate annualized volatility from daily returns.

    Args:
        returns: Daily returns series
        trading_days_per_year: Trading days per year

    Returns:
        Annualized volatility as float
    """
    if len(returns) == 0:
        return 0.0

    daily_vol = float(returns.std())
    if np.isnan(daily_vol) or daily_vol < 0:
        daily_vol = 0.0

    volatility = daily_vol * np.sqrt(trading_days_per_year)
    return sanitize_value(volatility)
