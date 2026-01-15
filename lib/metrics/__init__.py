"""
Metrics package for The Researcher's Cockpit.

Provides comprehensive performance metrics using empyrical-reloaded library
and custom trade-level analysis.

Main exports:
- calculate_metrics: Calculate comprehensive performance metrics from returns
- calculate_trade_metrics: Calculate trade-level metrics from transactions
- calculate_rolling_metrics: Calculate rolling metrics over a specified window
- compare_strategies: Compare multiple strategies by loading their metrics

v1.0.4 Fixes Applied:
- Fixed Sharpe ratio calculation to handle edge cases
- Fixed Sortino ratio calculation with proper downside deviation threshold
- Added NaN/Inf handling throughout all metric calculations
- Fixed recovery time calculation to handle edge cases properly
- Added input validation for all public functions

v1.0.7 Fixes Applied:
- Fixed alpha() to use daily risk-free rate instead of annual
- Added profit factor cap for wins with no losses
- Fixed trade extraction to handle pyramiding with weighted average entry price
- Added convert_to_percentages parameter to calculate_metrics()
"""

# Core metrics calculation
from .core import (
    calculate_metrics,
    # Constants
    EMPYRICAL_AVAILABLE,
    MAX_PROFIT_FACTOR,
    PERCENTAGE_METRICS,
    # Helper functions (for internal use, but exposed for testing)
    _sanitize_value,
    _get_daily_rf,
    _validate_returns,
    _convert_to_percentages,
    _empty_metrics,
    _calculate_sortino_manual,
    _calculate_max_drawdown_manual,
    _calculate_recovery_time,
)

# Trade metrics
from .trade import (
    calculate_trade_metrics,
    _extract_trades,
    _calculate_max_consecutive_losses,
)

# Rolling metrics
from .rolling import (
    calculate_rolling_metrics,
)

# Strategy comparison
from .comparison import (
    compare_strategies,
)

__all__ = [
    # Main public API
    'calculate_metrics',
    'calculate_trade_metrics',
    'calculate_rolling_metrics',
    'compare_strategies',
    # Constants
    'EMPYRICAL_AVAILABLE',
    'MAX_PROFIT_FACTOR',
    'PERCENTAGE_METRICS',
    # Helper functions (exposed for advanced use)
    '_extract_trades',
    '_sanitize_value',
    '_get_daily_rf',
    '_validate_returns',
    '_convert_to_percentages',
    '_empty_metrics',
    '_calculate_sortino_manual',
    '_calculate_max_drawdown_manual',
    '_calculate_recovery_time',
    '_calculate_max_consecutive_losses',
]















