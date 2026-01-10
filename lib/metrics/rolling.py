"""
Rolling metrics calculation for The Researcher's Cockpit.

Provides time-series rolling metrics for performance analysis.

v1.0.4 Fixes Applied:
- Added input validation
- Added error handling for edge cases

v1.0.7 Fixes Applied:
- Uses raw decimal values (convert_to_percentages=False) for time-series analysis
"""

# Third-party imports
import pandas as pd

# Local imports
from .core import (
    calculate_metrics,
    _validate_returns,
)


def calculate_rolling_metrics(
    returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.04
) -> pd.DataFrame:
    """
    Calculate rolling metrics over a specified window.
    
    v1.0.4 Fixes:
    - Added input validation
    - Added error handling for edge cases
    
    v1.0.7 Fixes:
    - Uses raw decimal values (convert_to_percentages=False) for time-series analysis
    
    Args:
        returns: Series of daily returns
        window: Rolling window size in days (default: 63 = ~3 months)
        risk_free_rate: Annual risk-free rate
        
    Returns:
        DataFrame with rolling metrics columns
    """
    # v1.0.4: Input validation
    try:
        returns = _validate_returns(returns)
    except ValueError:
        return pd.DataFrame()
    
    if len(returns) < window:
        return pd.DataFrame()
    
    # v1.0.4: Validate window
    if not isinstance(window, int) or window <= 0:
        window = 63
    
    rolling_data = []
    
    for i in range(window, len(returns) + 1):
        try:
            window_returns = returns.iloc[i-window:i]
            
            if len(window_returns) == 0:
                continue
            
            # v1.0.7: Use raw decimal values for rolling metrics (no percentage conversion)
            window_metrics = calculate_metrics(
                window_returns, 
                risk_free_rate=risk_free_rate,
                convert_to_percentages=False  # v1.0.7: Keep as decimals for time-series
            )
            
            rolling_data.append({
                'date': returns.index[i-1],
                'rolling_sharpe': window_metrics.get('sharpe', 0.0),
                'rolling_sortino': window_metrics.get('sortino', 0.0),
                'rolling_return': window_metrics.get('annual_return', 0.0),
                'rolling_volatility': window_metrics.get('annual_volatility', 0.0),
                'rolling_max_dd': window_metrics.get('max_drawdown', 0.0),
            })
        except Exception:
            # v1.0.4: Skip windows that fail
            continue
    
    if len(rolling_data) == 0:
        return pd.DataFrame()
    
    return pd.DataFrame(rolling_data).set_index('date')





