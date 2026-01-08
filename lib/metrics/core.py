"""
Core metrics calculation for The Researcher's Cockpit.

Provides the main calculate_metrics function and supporting utilities using
empyrical-reloaded library for financial metrics.

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
"""

# Standard library imports
from typing import Optional, Dict, Any

# Third-party imports
import numpy as np
import pandas as pd

try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False


# v1.0.7: Maximum profit factor when there are profits but no losses
MAX_PROFIT_FACTOR = 999.0


# v1.0.7: Metrics that should be displayed as percentages (multiply by 100)
# This makes metrics.json more human-readable (80.0 instead of 0.8 for win_rate)
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


def _sanitize_value(value: float, default: float = 0.0) -> float:
    """
    Sanitize a numeric value by replacing NaN/Inf with a default.
    
    v1.0.4: Added to ensure all returned metrics are valid floats.
    
    Args:
        value: The value to sanitize
        default: The default value to use if value is NaN or Inf
        
    Returns:
        Sanitized float value
    """
    if value is None or np.isnan(value) or np.isinf(value):
        return default
    return float(value)


def _get_daily_rf(annual_rf: float, trading_days: int = 252) -> float:
    """
    Convert annual risk-free rate to daily rate.
    
    v1.0.7: Helper to standardize risk-free rate conversion.
    All public functions expect ANNUAL rates; this converts to daily for empyrical.
    
    Args:
        annual_rf: Annual risk-free rate (e.g., 0.04 for 4%)
        trading_days: Trading days per year (default: 252)
        
    Returns:
        Daily risk-free rate
    """
    return annual_rf / trading_days


def _convert_to_percentages(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert decimal metrics to percentage format for human readability.

    v1.0.7: Converts metrics like win_rate from 0.8 to 80.0 for clarity.

    Args:
        metrics: Dictionary of metrics with decimal values

    Returns:
        Dictionary with percentage metrics multiplied by 100
    """
    converted = metrics.copy()
    for key in PERCENTAGE_METRICS:
        if key in converted and isinstance(converted[key], (int, float)):
            converted[key] = converted[key] * 100
    return converted


def _validate_returns(returns: pd.Series) -> pd.Series:
    """
    Validate and clean a returns series.
    
    v1.0.4: Added comprehensive input validation.
    
    Args:
        returns: Series of returns to validate
        
    Returns:
        Cleaned returns series with NaN values removed
        
    Raises:
        ValueError: If returns is not a valid pandas Series
    """
    if returns is None:
        raise ValueError("Returns series cannot be None")
    
    if not isinstance(returns, pd.Series):
        raise ValueError(f"Returns must be a pandas Series, got {type(returns)}")
    
    # Drop NaN values and convert to float
    cleaned = returns.dropna().astype(float)
    
    # v1.0.4: Replace any infinite values with NaN and then drop
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan).dropna()
    
    return cleaned


def _calculate_sortino_manual(
    returns: pd.Series,
    daily_risk_free_rate: float,
    annual_return: float,
    risk_free_rate: float,
    trading_days_per_year: int
) -> float:
    """
    Calculate Sortino ratio manually with proper downside deviation.
    
    v1.0.4: Extracted and fixed Sortino calculation.
    
    The downside deviation should use returns below the target (risk-free rate),
    not just negative returns.
    
    Args:
        returns: Daily returns series
        daily_risk_free_rate: Daily risk-free rate
        annual_return: Annualized return
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year
        
    Returns:
        Sortino ratio as float
    """
    # v1.0.4: Calculate downside deviation using returns below target
    # Target is the daily risk-free rate
    excess_returns = returns - daily_risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        # v1.0.4: No downside returns means all returns beat the target
        # Return 0 as we can't calculate a meaningful ratio
        return 0.0
    
    # v1.0.4: Downside deviation is the std of returns below target
    # Using squared deviations from zero (since we already subtracted target)
    downside_std = float(np.sqrt(np.mean(downside_returns ** 2)))
    annualized_downside_std = downside_std * np.sqrt(trading_days_per_year)
    
    if annualized_downside_std < 1e-10:
        return 0.0
    
    excess_annual_return = annual_return - risk_free_rate
    sortino = _sanitize_value(excess_annual_return / annualized_downside_std)
    
    return sortino


def _calculate_max_drawdown_manual(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown manually.
    
    v1.0.4: Extracted for reuse and added error handling.
    
    Args:
        returns: Daily returns series
        
    Returns:
        Maximum drawdown as a negative float (or 0 if no drawdown)
    """
    if len(returns) == 0:
        return 0.0
    
    try:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
        return _sanitize_value(max_dd)
    except Exception:
        return 0.0


def _calculate_recovery_time(returns: pd.Series) -> Optional[pd.Timedelta]:
    """
    Calculate the recovery time from the start of the maximum drawdown to new equity high.

    v1.0.4 Fixes:
    - Added input validation
    - Fixed edge case handling for empty returns
    - Fixed edge case when drawdown starts at first data point
    - Added proper handling for when recovery hasn't occurred

    Args:
        returns: Series of daily returns.

    Returns:
        pd.Timedelta: The recovery time, or None if not yet recovered.
    """
    # v1.0.4: Input validation
    if returns is None or len(returns) == 0:
        return pd.Timedelta(seconds=0)

    try:
        # v1.0.4: Validate returns has a proper datetime index
        if not isinstance(returns.index, pd.DatetimeIndex):
            # Try to convert index to datetime
            try:
                returns.index = pd.to_datetime(returns.index)
            except Exception:
                return pd.Timedelta(seconds=0)
        
        # Calculate cumulative returns
        cumulative_returns = (1 + returns).cumprod()
        
        # v1.0.4: Check for valid cumulative returns
        if cumulative_returns.isna().all() or len(cumulative_returns) == 0:
            return pd.Timedelta(seconds=0)
        
        # Calculate the running maximum
        running_max = cumulative_returns.cummax()
        
        # Calculate drawdowns
        # v1.0.4: Handle division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdown = (cumulative_returns - running_max) / running_max
            drawdown = drawdown.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Find the maximum drawdown (most negative value in the drawdown series)
        max_dd_value = drawdown.min()
        
        # v1.0.4: If no drawdown, no recovery needed
        if max_dd_value >= 0 or np.isnan(max_dd_value):
            return pd.Timedelta(seconds=0)

        # Find the index of the start and end of the max drawdown
        # The end of the max drawdown is the lowest trough itself
        end_of_max_dd_idx = drawdown.idxmin()
        
        # The start of the max drawdown is the last peak before the lowest trough
        cumulative_before_trough = cumulative_returns[:end_of_max_dd_idx]
        
        # v1.0.4: Handle edge case where trough is at the beginning
        if len(cumulative_before_trough) == 0:
            return pd.Timedelta(seconds=0)
        
        start_of_max_dd_idx = cumulative_before_trough.idxmax()

        # Find the next time the equity curve makes a new high after the max drawdown trough
        recovery_candidates = cumulative_returns[cumulative_returns.index > end_of_max_dd_idx]
        
        if len(recovery_candidates) == 0:
            return None  # Has not recovered yet
        
        # Find the first index where the cumulative returns recover to or exceed the peak before the drawdown
        peak_value = cumulative_returns[start_of_max_dd_idx]
        
        # v1.0.4: Handle NaN peak value
        if np.isnan(peak_value):
            return pd.Timedelta(seconds=0)
        
        recovered_mask = recovery_candidates >= peak_value
        
        if not recovered_mask.any():
            return None  # Has not recovered yet
        
        recovered_date = recovery_candidates[recovered_mask].index[0]
        
        return recovered_date - start_of_max_dd_idx
        
    except Exception:
        # v1.0.4: Return 0 on any unexpected error
        return pd.Timedelta(seconds=0)


def _empty_metrics() -> Dict[str, float]:
    """
    Return empty metrics dictionary.
    
    v1.0.4: All values are guaranteed to be valid (no NaN/Inf).
    """
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
    
    Uses empyrical-reloaded library for financial metrics when available, falls back
    to manual calculations otherwise.
    
    v1.0.4 Fixes:
    - Added input validation for all parameters
    - Fixed Sharpe ratio edge cases (zero volatility, insufficient data)
    - Fixed Sortino ratio with proper downside deviation calculation
    - Added NaN/Inf sanitization for all output values
    - Improved error handling with graceful degradation
    
    v1.0.7 Fixes:
    - Added convert_to_percentages parameter for API consistency
    - Fixed alpha() to use daily risk-free rate
    
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
    
    # v1.0.4: Validate inputs
    returns = _validate_returns(returns)
    
    if len(returns) == 0:
        return _empty_metrics()
    
    # v1.0.4: Validate risk_free_rate and trading_days_per_year
    if not isinstance(risk_free_rate, (int, float)) or np.isnan(risk_free_rate):
        risk_free_rate = 0.04
    if not isinstance(trading_days_per_year, int) or trading_days_per_year <= 0:
        trading_days_per_year = 252
    
    metrics = {}
    
    # v1.0.7: Use helper for daily risk-free rate conversion
    daily_risk_free_rate = _get_daily_rf(risk_free_rate, trading_days_per_year)
    
    # Basic return metrics
    total_return = float((1 + returns).prod() - 1)
    metrics['total_return'] = _sanitize_value(total_return)
    
    # Annualized return
    n_days = len(returns)
    if n_days > 0:
        # v1.0.4: Handle edge case where total_return is -100% (would cause negative base for power)
        if total_return <= -1.0:
            annual_return = -1.0  # Complete loss
        else:
            annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)
        metrics['annual_return'] = _sanitize_value(annual_return)
    else:
        metrics['annual_return'] = 0.0
    
    annual_return = metrics['annual_return']  # Use sanitized value for subsequent calculations
    
    # Volatility (annualized)
    # v1.0.4: Handle edge case where std is zero or NaN
    daily_volatility = float(returns.std())
    if np.isnan(daily_volatility) or daily_volatility < 0:
        daily_volatility = 0.0
    volatility = daily_volatility * np.sqrt(trading_days_per_year)
    metrics['annual_volatility'] = _sanitize_value(volatility)
    
    # v1.0.4: Fixed Sharpe ratio calculation with proper edge case handling
    # Sharpe ratio requires sufficient data and non-zero volatility
    MIN_PERIODS_FOR_SHARPE = 20  # v1.0.4: Minimum periods for reliable Sharpe calculation
    
    if n_days < MIN_PERIODS_FOR_SHARPE:
        # v1.0.4: Not enough data for reliable Sharpe ratio
        sharpe = 0.0
    elif volatility < 1e-10:
        # v1.0.4: Zero volatility edge case - if returns positive, infinite Sharpe (cap at 0)
        # We return 0 because zero volatility with positive returns is unrealistic
        sharpe = 0.0
    elif EMPYRICAL_AVAILABLE:
        try:
            # v1.0.7: empyrical expects DAILY risk-free rate
            sharpe = float(ep.sharpe_ratio(
                returns,
                risk_free=daily_risk_free_rate,
                period='daily',
                annualization=trading_days_per_year
            ))
            sharpe = _sanitize_value(sharpe)
        except Exception:
            # v1.0.4: Fallback to manual calculation on empyrical error
            excess_return = annual_return - risk_free_rate
            sharpe = _sanitize_value(excess_return / volatility)
    else:
        # Manual calculation: (annualized_return - risk_free_rate) / annualized_volatility
        excess_return = annual_return - risk_free_rate
        sharpe = _sanitize_value(excess_return / volatility)
    metrics['sharpe'] = sharpe
    
    # v1.0.4: Fixed Sortino ratio calculation with proper downside deviation
    # The threshold for downside deviation should be the target return (often 0 or risk-free rate)
    if n_days < MIN_PERIODS_FOR_SHARPE:
        # v1.0.4: Not enough data for reliable Sortino ratio
        sortino = 0.0
    elif volatility < 1e-10:
        # v1.0.7: Zero volatility edge case - can't calculate meaningful Sortino
        sortino = 0.0
    elif EMPYRICAL_AVAILABLE:
        try:
            # empyrical expects DAILY required return, use daily_risk_free_rate
            sortino = float(ep.sortino_ratio(
                returns,
                required_return=daily_risk_free_rate,
                period='daily',
                annualization=trading_days_per_year
            ))
            sortino = _sanitize_value(sortino)
        except Exception:
            # v1.0.4: Fallback to manual calculation
            sortino = _calculate_sortino_manual(
                returns, daily_risk_free_rate, annual_return, 
                risk_free_rate, trading_days_per_year
            )
    else:
        # v1.0.4: Manual Sortino calculation with corrected downside deviation
        sortino = _calculate_sortino_manual(
            returns, daily_risk_free_rate, annual_return, 
            risk_free_rate, trading_days_per_year
        )
    metrics['sortino'] = sortino
    
    # Maximum drawdown
    if EMPYRICAL_AVAILABLE:
        try:
            max_dd = float(ep.max_drawdown(returns))
            max_dd = _sanitize_value(max_dd)
        except Exception:
            max_dd = _calculate_max_drawdown_manual(returns)
    else:
        max_dd = _calculate_max_drawdown_manual(returns)
    metrics['max_drawdown'] = max_dd
    
    # Calmar ratio (annual return / max drawdown)
    # v1.0.4: Handle edge case where max_dd is zero or very small
    if abs(max_dd) > 1e-10:
        calmar = _sanitize_value(annual_return / abs(max_dd))
    else:
        calmar = 0.0
    metrics['calmar'] = calmar
    
    # Additional metrics from empyrical-reloaded if available
    if EMPYRICAL_AVAILABLE:
        # Alpha and Beta require benchmark returns
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            try:
                # v1.0.4: Validate benchmark returns
                benchmark_returns = _validate_returns(benchmark_returns)
                
                # Align returns and benchmark
                aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
                aligned_returns = aligned_returns.dropna()
                aligned_benchmark = aligned_benchmark.dropna()
                
                if len(aligned_returns) >= MIN_PERIODS_FOR_SHARPE and len(aligned_benchmark) >= MIN_PERIODS_FOR_SHARPE:
                    # v1.0.7: Fixed - alpha() expects DAILY risk-free rate, not annual
                    alpha = float(ep.alpha(
                        aligned_returns, 
                        aligned_benchmark, 
                        risk_free=daily_risk_free_rate,  # v1.0.7: Use daily rate
                        period='daily', 
                        annualization=trading_days_per_year
                    ))
                    beta = float(ep.beta(aligned_returns, aligned_benchmark))
                    metrics['alpha'] = _sanitize_value(alpha)
                    metrics['beta'] = _sanitize_value(beta, default=1.0)
                else:
                    metrics['alpha'] = 0.0
                    metrics['beta'] = 1.0
            except Exception:
                metrics['alpha'] = 0.0
                metrics['beta'] = 1.0
        else:
            # Without benchmark, alpha is 0 and beta is undefined (set to 1)
            metrics['alpha'] = 0.0
            metrics['beta'] = 1.0
        
        # Omega ratio
        try:
            omega = float(ep.omega_ratio(
                returns,
                risk_free=daily_risk_free_rate,  # v1.0.7: Use daily rate for consistency
                required_return=0.0, 
                annualization=trading_days_per_year
            ))
            metrics['omega'] = _sanitize_value(omega)
        except Exception:
            metrics['omega'] = 0.0
        
        # Tail ratio
        try:
            tail_ratio = float(ep.tail_ratio(returns))
            metrics['tail_ratio'] = _sanitize_value(tail_ratio)
        except Exception:
            metrics['tail_ratio'] = 0.0
        
        # Maximum drawdown duration
        try:
            max_dd_duration = ep.max_drawdown_duration(returns)
            if max_dd_duration is not None:
                # v1.0.4: Handle case where duration is a timedelta
                if isinstance(max_dd_duration, pd.Timedelta):
                    metrics['max_drawdown_duration'] = _sanitize_value(
                        max_dd_duration.total_seconds() / (60 * 60 * 24)
                    )
                else:
                    metrics['max_drawdown_duration'] = _sanitize_value(float(max_dd_duration))
            else:
                metrics['max_drawdown_duration'] = 0.0
        except Exception:
            metrics['max_drawdown_duration'] = 0.0

        # Recovery time
        try:
            recovery_time = _calculate_recovery_time(returns)
            if recovery_time is not None:
                metrics['recovery_time'] = _sanitize_value(
                    recovery_time.total_seconds() / (60 * 60 * 24)
                )
            else:
                metrics['recovery_time'] = 0.0
        except Exception:
            metrics['recovery_time'] = 0.0
    else:
        metrics['alpha'] = 0.0
        metrics['beta'] = 1.0
        metrics['omega'] = 0.0
        metrics['tail_ratio'] = 0.0
        metrics['max_drawdown_duration'] = 0.0
        metrics['recovery_time'] = 0.0
    
    # Trade-level metrics if transactions provided
    if transactions is not None:
        if len(transactions) > 0:
            try:
                # v1.0.7: Don't convert to percentages here - we'll do it at the end
                trade_metrics = calculate_trade_metrics(transactions, as_percentages=False)
                metrics.update(trade_metrics)
            except Exception:
                # v1.0.4: If trade metrics fail, add empty trade metrics
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
            # v1.0.6: Empty transactions DataFrame - still include trade_count: 0
            metrics['trade_count'] = 0

    # v1.0.7: Only convert to percentages if requested (default: True for backward compatibility)
    if convert_to_percentages:
        return _convert_to_percentages(metrics)
    return metrics

