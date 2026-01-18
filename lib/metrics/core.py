"""
Core metrics orchestration for The Researcher's Cockpit.

Provides the main calculate_metrics function that coordinates performance and risk metrics.
Refactored in v1.0.11 to split performance, risk, and orchestration into separate modules.

v1.0.4 Fixes Applied:
- Fixed Sharpe ratio calculation to handle edge cases (zero volatility, insufficient data)
- Fixed Sortino ratio calculation with proper downside deviation threshold
- Added NaN/Inf handling throughout all metric calculations
- Fixed recovery time calculation to handle edge cases properly
- Added input validation for all public functions
- Improved error handling with graceful degradation

v1.0.7 Fixes Applied:
- Fixed alpha() to use daily risk-free rate instead of annual
- Added profit factor cap (MAX_PROFIT_FACTOR = 999.0) for wins with no losses
- Fixed trade extraction to handle pyramiding with weighted average entry price
- Added convert_to_percentages parameter to calculate_metrics()
- Fixed calculate_rolling_metrics() to use raw decimal values
- Added as_percentages parameter to calculate_trade_metrics()

v1.0.11 Refactoring:
- Extracted performance metrics to performance.py
- Extracted risk metrics to risk.py
- Kept orchestration logic in core.py
"""

from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

# Import from refactored modules
from .performance import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_annual_return,
    calculate_total_return,
    calculate_annual_volatility,
    EMPYRICAL_AVAILABLE,
    _sanitize_value,
    _get_daily_rf,
)
from .risk import (
    calculate_max_drawdown,
    calculate_recovery_time,
    calculate_alpha_beta,
    calculate_omega_ratio,
    calculate_tail_ratio,
    calculate_max_drawdown_duration,
)


# Constants
MAX_PROFIT_FACTOR = 999.0


# Metrics that should be displayed as percentages
PERCENTAGE_METRICS = {
    'total_return',
    'annual_return',
    'annual_volatility',
    'max_drawdown',
    'win_rate',
    'avg_trade_return',
    'avg_win',
    'avg_loss',
    'max_win',
    'max_loss',
}


def _validate_returns(returns: pd.Series) -> pd.Series:
    """Validate and clean a returns series."""
    if returns is None:
        raise ValueError("Returns series cannot be None")

    if not isinstance(returns, pd.Series):
        raise ValueError(f"Returns must be a pandas Series, got {type(returns)}")

    # Drop NaN values and convert to float
    cleaned = returns.dropna().astype(float)

    # Replace infinite values with NaN and drop
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan).dropna()

    return cleaned


def _convert_to_percentages(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Convert decimal metrics to percentage format for human readability."""
    converted = metrics.copy()
    for key in PERCENTAGE_METRICS:
        if key in converted and isinstance(converted[key], (int, float)):
            converted[key] = converted[key] * 100
    return converted


def _empty_metrics() -> Dict[str, float]:
    """Return empty metrics dictionary with all values as valid floats."""
    return {
        'total_return': 0.0,
        'annual_return': 0.0,
        'annual_volatility': 0.0,
        'sharpe': 0.0,
        'sortino': 0.0,
        'max_drawdown': 0.0,
        'calmar': 0.0,
        'alpha': 0.0,
        'beta': 1.0,
        'omega': 0.0,
        'tail_ratio': 0.0,
        'max_drawdown_duration': 0.0,
        'recovery_time': 0.0,
        'trade_count': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'avg_trade_return': 0.0,
        'avg_win': 0.0,
        'avg_loss': 0.0,
        'max_win': 0.0,
        'max_loss': 0.0,
        'max_consecutive_losses': 0,
        'avg_trade_duration': 0.0,
        'trades_per_month': 0.0,
    }


def calculate_metrics(
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252,
    convert_to_percentages: bool = True
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics from returns.

    Orchestrates performance and risk metric calculations using specialized modules.

    Args:
        returns: Series of daily returns (timezone-naive index)
        transactions: Optional DataFrame of transactions for trade-level metrics
        benchmark_returns: Optional Series of benchmark daily returns for alpha/beta
        risk_free_rate: Annual risk-free rate (default: 0.04)
        trading_days_per_year: Trading days per year (default: 252)
        convert_to_percentages: If True, convert decimal metrics to percentages (default: True)

    Returns:
        Dictionary of calculated metrics (all values guaranteed to be valid floats)

    Raises:
        ValueError: If returns is not a valid pandas Series
    """
    # Import here to avoid circular imports
    from .trade import calculate_trade_metrics

    # Validate inputs
    returns = _validate_returns(returns)

    if len(returns) == 0:
        return _empty_metrics()

    # Validate risk_free_rate and trading_days_per_year
    if not isinstance(risk_free_rate, (int, float)) or np.isnan(risk_free_rate):
        risk_free_rate = 0.04
    if not isinstance(trading_days_per_year, int) or trading_days_per_year <= 0:
        trading_days_per_year = 252

    metrics = {}

    # Calculate return metrics
    metrics['total_return'] = calculate_total_return(returns)
    metrics['annual_return'] = calculate_annual_return(returns, trading_days_per_year)
    metrics['annual_volatility'] = calculate_annual_volatility(returns, trading_days_per_year)

    # Calculate ratio metrics
    metrics['sharpe'] = calculate_sharpe_ratio(
        returns,
        risk_free_rate,
        trading_days_per_year,
        metrics['annual_return'],
        metrics['annual_volatility']
    )

    metrics['sortino'] = calculate_sortino_ratio(
        returns,
        risk_free_rate,
        trading_days_per_year,
        metrics['annual_return']
    )

    # Calculate risk metrics
    metrics['max_drawdown'] = calculate_max_drawdown(returns)
    metrics['calmar'] = calculate_calmar_ratio(metrics['annual_return'], metrics['max_drawdown'])

    # Calculate alpha and beta if benchmark provided
    if benchmark_returns is not None and len(benchmark_returns) > 0:
        alpha, beta = calculate_alpha_beta(returns, benchmark_returns, risk_free_rate, trading_days_per_year)
        metrics['alpha'] = alpha
        metrics['beta'] = beta
    else:
        metrics['alpha'] = 0.0
        metrics['beta'] = 1.0

    # Additional risk metrics
    metrics['omega'] = calculate_omega_ratio(returns, risk_free_rate, trading_days_per_year)
    metrics['tail_ratio'] = calculate_tail_ratio(returns)
    metrics['max_drawdown_duration'] = calculate_max_drawdown_duration(returns)

    # Recovery time
    recovery_time = calculate_recovery_time(returns)
    if recovery_time is not None:
        metrics['recovery_time'] = recovery_time.total_seconds() / (60 * 60 * 24)
    else:
        metrics['recovery_time'] = 0.0

    # Trade-level metrics if transactions provided
    if transactions is not None:
        if len(transactions) > 0:
            try:
                trade_metrics = calculate_trade_metrics(transactions, as_percentages=False)
                metrics.update(trade_metrics)
            except Exception:
                # If trade metrics fail, add empty trade metrics
                metrics.update({
                    'trade_count': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'avg_trade_return': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'max_win': 0.0,
                    'max_loss': 0.0,
                    'max_consecutive_losses': 0,
                    'avg_trade_duration': 0.0,
                    'trades_per_month': 0.0,
                })
        else:
            # Empty transactions DataFrame
            metrics['trade_count'] = 0

    # Convert to percentages if requested
    if convert_to_percentages:
        return _convert_to_percentages(metrics)
    return metrics
