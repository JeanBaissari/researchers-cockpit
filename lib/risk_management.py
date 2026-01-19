"""
Risk management utilities for trading strategies.

Provides functions to check exit conditions based on risk parameters:
- Fixed stop loss
- Trailing stop loss
- Take profit

This module follows the Single Responsibility Principle by focusing solely
on risk management logic, making it reusable across all strategies.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # Avoid circular imports - these are Zipline types
    from zipline.api import Context
    from zipline.data.data_portal import DataPortal

# Configure logging
logger = logging.getLogger(__name__)

# Floating point comparison tolerance for price comparisons
FLOAT_EPSILON = 1e-6


def check_exit_conditions(
    context: 'Context',
    data: 'DataPortal',
    risk_params: dict
) -> Optional[str]:
    """
    Check stop loss, trailing stop, and take profit conditions.

    Evaluates exit conditions in priority order:
    1. Take profit (highest priority - lock in gains)
    2. Trailing stop (takes precedence over fixed stop if both enabled)
    3. Fixed stop loss

    Args:
        context: Zipline context object with:
            - in_position: bool indicating if position is open
            - asset: Asset being traded
            - entry_price: float entry price
            - highest_price: float highest price since entry (for trailing stop)
        data: Zipline data object for current price
        risk_params: Risk management parameters dictionary

    Returns:
        Exit type as string: 'fixed', 'trailing', 'take_profit', or None if no exit

    Example:
        >>> exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
        >>> if exit_type:
        ...     order_target_percent(context.asset, 0)
        ...     context.in_position = False
    """
    # Early return if not in position
    if not getattr(context, 'in_position', False):
        return None

    # Early return if asset cannot be traded
    if not data.can_trade(context.asset):
        return None

    current_price = data.current(context.asset, 'price')
    entry_price = getattr(context, 'entry_price', 0.0)
    highest_price = getattr(context, 'highest_price', 0.0)

    # Update highest price for trailing stop tracking
    if highest_price > 0:
        context.highest_price = max(highest_price, current_price)
    else:
        # Initialize if not set (defensive programming)
        context.highest_price = current_price
        highest_price = current_price

    # Check take profit first (highest priority - lock in gains)
    if risk_params.get('use_take_profit', False):
        exit_type = _check_take_profit(current_price, entry_price, risk_params)
        if exit_type:
            return exit_type

    # Check trailing stop (takes precedence over fixed stop if both enabled)
    if risk_params.get('use_trailing_stop', False):
        exit_type = _check_trailing_stop(current_price, highest_price, risk_params)
        if exit_type:
            return exit_type

    # Check fixed stop if trailing not triggered
    if risk_params.get('use_stop_loss', False):
        exit_type = _check_fixed_stop(current_price, entry_price, risk_params)
        if exit_type:
            return exit_type

    return None


def _is_price_greater_or_equal(price1: float, price2: float, epsilon: float = FLOAT_EPSILON) -> bool:
    """
    Compare prices with floating point tolerance.
    
    Args:
        price1: First price
        price2: Second price
        epsilon: Tolerance for comparison
    
    Returns:
        True if price1 >= price2 (within tolerance)
    """
    return price1 >= (price2 - epsilon)


def _is_price_less_or_equal(price1: float, price2: float, epsilon: float = FLOAT_EPSILON) -> bool:
    """
    Compare prices with floating point tolerance (less than or equal).
    
    Args:
        price1: First price
        price2: Second price
        epsilon: Tolerance for comparison
    
    Returns:
        True if price1 <= price2 (within tolerance)
    """
    return price1 <= (price2 + epsilon)


def _validate_percentage_param(
    param_value: float,
    param_name: str,
    default: float,
    min_value: float = 0.0,
    max_value: float = 1.0
) -> float:
    """
    Validate and normalize percentage parameter.
    
    Args:
        param_value: Parameter value to validate
        param_name: Parameter name for logging
        default: Default value if invalid
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        Validated parameter value
    """
    if param_value <= min_value or param_value > max_value:
        logger.warning(
            f"Invalid {param_name}: {param_value}. Must be in ({min_value}, {max_value}]. "
            f"Using default: {default}"
        )
        return default
    return param_value


def _check_take_profit(
    current_price: float,
    entry_price: float,
    risk_params: dict
) -> Optional[str]:
    """
    Check if take profit condition is met.

    Args:
        current_price: Current asset price
        entry_price: Entry price of the position
        risk_params: Risk management parameters

    Returns:
        'take_profit' if condition met, None otherwise
    """
    if entry_price <= 0:
        return None

    # ✅ FIX: Use shared validation (DRY)
    take_profit_pct = _validate_percentage_param(
        risk_params.get('take_profit_pct', 0.10),
        'take_profit_pct',
        default=0.10,
        min_value=0.0,
        max_value=1.0  # 100% max
    )

    # Calculate profit target
    profit_price = entry_price * (1 + take_profit_pct)
    
    # ✅ FIX: Use floating point tolerant comparison (fixes precision issue)
    if _is_price_greater_or_equal(current_price, profit_price):
        logger.debug(
            f"Take profit triggered: current_price={current_price:.4f}, "
            f"profit_price={profit_price:.4f}, entry_price={entry_price:.4f}, "
            f"take_profit_pct={take_profit_pct:.4f}"
        )
        return 'take_profit'
    
    return None


def _check_trailing_stop(
    current_price: float,
    highest_price: float,
    risk_params: dict
) -> Optional[str]:
    """
    Check if trailing stop condition is met.

    Args:
        current_price: Current asset price
        highest_price: Highest price since entry
        risk_params: Risk management parameters

    Returns:
        'trailing' if condition met, None otherwise
    """
    if highest_price <= 0:
        return None

    # ✅ FIX: Use shared validation (DRY)
    trailing_stop_pct = _validate_percentage_param(
        risk_params.get('trailing_stop_pct', 0.08),
        'trailing_stop_pct',
        default=0.08,
        min_value=0.0,
        max_value=1.0
    )

    stop_price = highest_price * (1 - trailing_stop_pct)
    
    # ✅ FIX: Use floating point tolerant comparison
    if _is_price_less_or_equal(current_price, stop_price):
        logger.debug(
            f"Trailing stop triggered: current_price={current_price:.4f}, "
            f"stop_price={stop_price:.4f}, highest_price={highest_price:.4f}, "
            f"trailing_stop_pct={trailing_stop_pct:.4f}"
        )
        return 'trailing'
    
    return None


def _check_fixed_stop(
    current_price: float,
    entry_price: float,
    risk_params: dict
) -> Optional[str]:
    """
    Check if fixed stop loss condition is met.

    Args:
        current_price: Current asset price
        entry_price: Entry price of the position
        risk_params: Risk management parameters

    Returns:
        'fixed' if condition met, None otherwise
    """
    if entry_price <= 0:
        return None

    # ✅ FIX: Use shared validation (DRY)
    stop_loss_pct = _validate_percentage_param(
        risk_params.get('stop_loss_pct', 0.05),
        'stop_loss_pct',
        default=0.05,
        min_value=0.0,
        max_value=1.0
    )

    stop_price = entry_price * (1 - stop_loss_pct)
    
    # ✅ FIX: Use floating point tolerant comparison
    if _is_price_less_or_equal(current_price, stop_price):
        logger.debug(
            f"Fixed stop loss triggered: current_price={current_price:.4f}, "
            f"stop_price={stop_price:.4f}, entry_price={entry_price:.4f}, "
            f"stop_loss_pct={stop_loss_pct:.4f}"
        )
        return 'fixed'
    
    return None


def get_exit_type_code(exit_type: Optional[str]) -> int:
    """
    Convert exit type string to numeric code for recording.

    Args:
        exit_type: Exit type string ('fixed', 'trailing', 'take_profit', or None)

    Returns:
        Numeric code: 1=fixed, 2=trailing, 3=take_profit, 0=None
    """
    exit_type_map = {'fixed': 1, 'trailing': 2, 'take_profit': 3}
    return exit_type_map.get(exit_type, 0)

