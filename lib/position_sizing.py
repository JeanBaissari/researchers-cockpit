"""
Position sizing utilities for trading strategies.

Provides functions to calculate position sizes based on various methods:
- Fixed position sizing
- Volatility-scaled position sizing
- Kelly Criterion position sizing

This module follows the Single Responsibility Principle by focusing solely
on position sizing calculations, making it reusable across all strategies.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    # Avoid circular imports - these are Zipline types
    from zipline.api import Context
    from zipline.data.data_portal import DataPortal

# Configure logging
logger = logging.getLogger(__name__)


def compute_position_size(context: 'Context', data: 'DataPortal', params: dict) -> float:
    """
    Calculate position size based on the configured method.

    Supports three methods:
    - 'fixed': Returns max_position_pct directly
    - 'volatility_scaled': Scales position inversely with volatility to target vol
    - 'kelly': Uses Kelly Criterion with fractional sizing for capital preservation

    Args:
        context: Zipline context object with params attribute
        data: Zipline data object for price history
        params: Strategy parameters dictionary (can also use context.params)

    Returns:
        Position size as float (0.0 to max_position_pct)

    Raises:
        ValueError: If position sizing configuration is invalid

    Example:
        >>> position_size = compute_position_size(context, data, context.params)
        >>> order_target_percent(context.asset, position_size)
    """
    # Use params if provided, otherwise fall back to context.params
    if params is None:
        params = getattr(context, 'params', {})
    
    pos_config = params.get('position_sizing', {})
    method = pos_config.get('method', 'fixed')
    max_position = pos_config.get('max_position_pct', 0.95)
    min_position = pos_config.get('min_position_pct', 0.10)

    # Validate bounds
    if not (0.0 <= max_position <= 1.0):
        raise ValueError(
            f"max_position_pct must be between 0.0 and 1.0. Got: {max_position}"
        )
    if not (0.0 <= min_position <= 1.0):
        raise ValueError(
            f"min_position_pct must be between 0.0 and 1.0. Got: {min_position}"
        )
    if min_position > max_position:
        raise ValueError(
            f"min_position_pct ({min_position}) cannot be greater than "
            f"max_position_pct ({max_position})"
        )

    if method == 'fixed':
        return float(max_position)

    elif method == 'volatility_scaled':
        return _compute_volatility_scaled_size(
            context, data, params, pos_config, max_position, min_position
        )

    elif method == 'kelly':
        return _compute_kelly_size(
            pos_config, max_position, min_position
        )

    else:
        logger.warning(
            f"Unknown position sizing method '{method}'. "
            f"Falling back to 'fixed' method."
        )
        return float(max_position)


def _compute_volatility_scaled_size(
    context: 'Context',
    data: 'DataPortal',
    params: dict,
    pos_config: dict,
    max_position: float,
    min_position: float
) -> float:
    """
    Compute volatility-scaled position size.

    Scales position inversely with volatility to target a specific volatility level.
    Formula: position = volatility_target / current_volatility

    Args:
        context: Zipline context object
        data: Zipline data object
        params: Strategy parameters
        pos_config: Position sizing configuration
        max_position: Maximum position size
        min_position: Minimum position size

    Returns:
        Position size as float
    """
    vol_lookback = pos_config.get('volatility_lookback', 20)
    vol_target = pos_config.get('volatility_target', 0.15)

    # Validate volatility parameters
    if vol_lookback < 1:
        logger.warning(f"Invalid volatility_lookback: {vol_lookback}. Using default: 20")
        vol_lookback = 20
    if vol_target <= 0:
        logger.warning(f"Invalid volatility_target: {vol_target}. Using default: 0.15")
        vol_target = 0.15

    if not data.can_trade(context.asset):
        logger.debug(f"Asset {context.asset} cannot be traded. Using max_position.")
        return float(max_position)

    try:
        prices = data.history(context.asset, 'price', vol_lookback + 1, '1d')
        if len(prices) < vol_lookback + 1:
            logger.debug(
                f"Insufficient price history ({len(prices)} bars). "
                f"Need {vol_lookback + 1}. Using max_position."
            )
            return float(max_position)

        returns = prices.pct_change().dropna()
        if len(returns) < vol_lookback:
            logger.debug(
                f"Insufficient returns data ({len(returns)}). "
                f"Need {vol_lookback}. Using max_position."
            )
            return float(max_position)

        # Annualized volatility (trading days varies by asset class)
        asset_class = params.get('strategy', {}).get('asset_class', 'equities')
        trading_days = {'equities': 252, 'forex': 260, 'crypto': 365}.get(asset_class, 252)
        current_vol = returns.std() * np.sqrt(trading_days)

        if current_vol > 0:
            # Scale position to target volatility
            size = vol_target / current_vol
            clipped_size = float(np.clip(size, min_position, max_position))
            logger.debug(
                f"Volatility-scaled position: {clipped_size:.4f} "
                f"(current_vol={current_vol:.4f}, target_vol={vol_target:.4f})"
            )
            return clipped_size

        logger.debug(f"Zero volatility detected. Using max_position.")
        return float(max_position)

    except Exception as e:
        logger.warning(
            f"Error computing volatility-scaled size: {e}. "
            f"Falling back to max_position."
        )
        return float(max_position)


def _compute_kelly_size(
    pos_config: dict,
    max_position: float,
    min_position: float
) -> float:
    """
    Compute position size using Kelly Criterion.

    Kelly formula: f* = (bp - q) / b
    where: b = avg_win/avg_loss ratio, p = win rate, q = 1 - p

    NOTE: Full Kelly can be aggressive. Fractional Kelly (0.25-0.50) is recommended.

    Args:
        pos_config: Position sizing configuration
        max_position: Maximum position size
        min_position: Minimum position size

    Returns:
        Position size as float
    """
    kelly_config = pos_config.get('kelly', {})
    win_rate = kelly_config.get('win_rate_estimate', 0.55)
    win_loss_ratio = kelly_config.get('avg_win_loss_ratio', 1.5)
    kelly_fraction = kelly_config.get('kelly_fraction', 0.25)
    kelly_min = kelly_config.get('min_position_pct', min_position)

    # Validate Kelly parameters
    if not (0.0 < win_rate < 1.0):
        logger.warning(
            f"Invalid win_rate_estimate: {win_rate}. Must be between 0 and 1. "
            f"Using default: 0.55"
        )
        win_rate = 0.55
    if win_loss_ratio <= 0:
        logger.warning(
            f"Invalid avg_win_loss_ratio: {win_loss_ratio}. Must be positive. "
            f"Using default: 1.5"
        )
        win_loss_ratio = 1.5
    if not (0.0 < kelly_fraction <= 1.0):
        logger.warning(
            f"Invalid kelly_fraction: {kelly_fraction}. Must be between 0 and 1. "
            f"Using default: 0.25"
        )
        kelly_fraction = 0.25

    # Kelly formula
    b = win_loss_ratio
    p = win_rate
    q = 1 - p

    # Full Kelly (can be > 1 for high edge strategies)
    if b > 0:
        full_kelly = (b * p - q) / b
    else:
        logger.warning("avg_win_loss_ratio must be positive. Using min_position.")
        return float(kelly_min)

    # Apply fractional Kelly for safety (typically 0.25-0.50 of full Kelly)
    position_size = full_kelly * kelly_fraction

    # Clamp to bounds
    clipped_size = float(np.clip(position_size, kelly_min, max_position))
    logger.debug(
        f"Kelly position size: {clipped_size:.4f} "
        f"(full_kelly={full_kelly:.4f}, fraction={kelly_fraction:.4f})"
    )
    return clipped_size

