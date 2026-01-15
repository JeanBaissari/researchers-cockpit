"""
Strategy Template for The Researcher's Cockpit
==============================================================================
This is the canonical starting point for all new strategies.

To create a new strategy:
1. Copy this entire _template/ directory to strategies/{asset_class}/{strategy_name}/
2. Edit hypothesis.md with your trading rationale
3. Configure parameters.yaml with your parameter values
4. Implement your strategy logic below

CRITICAL RULES:
- NO hardcoded parameters in this file - all params come from parameters.yaml
- Every strategy MUST have a hypothesis.md file
- Use lib/config.py to load parameters
- Follow naming conventions from .agent/conventions.md
==============================================================================
"""

from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order,
)
from zipline.finance import commission, slippage
from datetime import time, datetime, timedelta
import pytz
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Optional Pipeline imports with two-level fallback for version compatibility
_PIPELINE_AVAILABLE = False
_PRICING_CLASS = None
try:
    from zipline.api import attach_pipeline, pipeline_output
    from zipline.pipeline import Pipeline
    from zipline.pipeline.factors import SimpleMovingAverage
    # Two-level fallback: prefer EquityPricing (Zipline-Reloaded 3.x), fall back to USEquityPricing
    try:
        from zipline.pipeline.data import EquityPricing
        _PRICING_CLASS = EquityPricing
    except ImportError:
        from zipline.pipeline.data import USEquityPricing
        _PRICING_CLASS = USEquityPricing
    _PIPELINE_AVAILABLE = True
except ImportError:
    pass
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for lib imports
# This allows strategies to import lib modules
# Uses marker-based root discovery for robust path resolution
def _find_project_root() -> Path:
    """Find project root by searching for marker files."""
    markers = ['pyproject.toml', '.git', 'config/settings.yaml', 'CLAUDE.md']
    current = Path(__file__).resolve().parent
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    raise RuntimeError("Could not find project root. Missing marker files.")

_project_root = _find_project_root()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from lib.config import load_strategy_params
    _has_lib_config = True
except ImportError:
    # Fallback to direct YAML loading if lib not available
    import yaml
    _has_lib_config = False


def load_params():
    """
    Load parameters from parameters.yaml file.
    
    Uses lib.config.load_strategy_params() if available, otherwise falls back
    to direct YAML loading.
    
    Returns:
        dict: Strategy parameters
    """
    if _has_lib_config:
        # Use lib.config for centralized config loading
        # Extract strategy name from path: strategies/{asset_class}/{name}/strategy.py
        strategy_path = Path(__file__).parent
        strategy_name = strategy_path.name
        # Try to infer asset_class from parent directory
        asset_class = strategy_path.parent.name
        if asset_class == 'strategies':
            asset_class = None  # Couldn't infer, will search all
        
        try:
            return load_strategy_params(strategy_name, asset_class)
        except Exception:
            # Fallback to direct loading if lib.config fails
            pass
    
    # Fallback: Direct YAML loading
    import yaml
    params_path = Path(__file__).parent / 'parameters.yaml'
    if not params_path.exists():
        raise FileNotFoundError(
            f"parameters.yaml not found at {params_path}. "
            "Every strategy must have a parameters.yaml file."
        )
    
    with open(params_path) as f:
        return yaml.safe_load(f)


def _get_previous_trading_day(current_time: datetime) -> datetime:
    """
    Determine the previous trading day, accounting for weekends.
    Forex markets are 24/5.
    """
    previous_day = current_time.date() - timedelta(days=1)
    # If it's Sunday (0) or Saturday (6), go back to Friday (4)
    while previous_day.weekday() > 4:  # 5 = Saturday, 6 = Sunday
        previous_day -= timedelta(days=1)
    return datetime.combine(previous_day, time(0, 0), tzinfo=pytz.utc)

def _get_safe_historical_data(data, start_date: datetime, end_date: datetime, asset, bar_count: int) -> pd.DataFrame:
    """
    Safely retrieve historical data, handling potential data gaps or insufficient data.
    """
    try:
        hist_data = data.history(asset, ['open', 'high', 'low', 'close', 'volume'], bar_count, '1m')
        # Ensure that the data returned is only up to the end_date to prevent look-ahead bias
        hist_data = hist_data[hist_data.index < end_date]
        return hist_data
    except Exception as e:
        logger.error(f"Error fetching historical data for {asset.symbol}: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def _calculate_previous_day_levels(context, data) -> Tuple[Optional[float], Optional[float]]:
    """
    CRITICAL: Ensures NO look-ahead bias - only uses data available BEFORE current_time.
    """
    current_time = data.current_dt
    asset = context.asset
    
    # We need to look back at least 2 trading days to calculate previous day levels reliably
    # The `bar_count` below is an estimate, assuming '1m' frequency and a 24-hour trading day
    # A safer approach is to request enough bars and then filter by date
    # Let's request enough bars for 2 full days to be safe (24 hours * 60 minutes = 1440 minutes/day)
    # Adding a buffer, say 3000 minutes.
    bar_count_estimate = 3000 

    # Fetch data up to current_time, then filter for previous trading day
    hist_data = _get_safe_historical_data(data, current_time - timedelta(days=2), current_time, asset, bar_count_estimate)
    
    if hist_data.empty:
        return None, None
        
    previous_trading_day_end = _get_previous_trading_day(current_time)
    
    # Filter data for the actual previous trading day
    prev_day_data = hist_data[hist_data.index < previous_trading_day_end]
    
    if prev_day_data.empty:
        return None, None

    prev_day_high = prev_day_data['high'].max()
    prev_day_low = prev_day_data['low'].min()
    
    return prev_day_high, prev_day_low

def _calculate_required_warmup(params: dict) -> int:
    """
    Dynamically calculate required warmup days from strategy parameters.

    Finds the maximum of all indicator period parameters to ensure
    sufficient data for indicator initialization.
    """
    strategy_config = params.get('strategy', {})
    period_values = []

    # Collect all *_period parameters
    for key, value in strategy_config.items():
        if key.endswith('_period') and isinstance(value, (int, float)) and value > 0:
            period_values.append(int(value))

    # Also check common non-suffixed period params
    for key in ['lookback', 'window', 'span']:
        if key in strategy_config:
            value = strategy_config[key]
            if isinstance(value, (int, float)) and value > 0:
                period_values.append(int(value))

    # Add ATR period if range detection is enabled
    strategy_config = params.get('strategy', {})
    if strategy_config.get('enable_range_detection', False):
        atr_period = strategy_config.get('atr_period', 14)
        if isinstance(atr_period, (int, float)) and atr_period > 0:
            period_values.append(int(atr_period))
    
    # Add volatility lookback for position sizing if enabled
    pos_config = params.get('position_sizing', {})
    if pos_config.get('method', 'fixed') == 'volatility_scaled':
        vol_lookback = pos_config.get('volatility_lookback', 20)
        if isinstance(vol_lookback, (int, float)) and vol_lookback > 0:
            period_values.append(int(vol_lookback))

    # We need at least 2 days of minute data for previous day high/low calculations
    return max(period_values) + 2 if period_values else 30

def _get_current_session(dt: datetime) -> str:
    """
    Determine the current trading session based on UTC time.
    """
    hour = dt.hour
    minute = dt.minute

    # Session definitions (UTC times for forex, as per documentation)
    ASIAN_SESSION_START = time(0, 0)
    ASIAN_SESSION_END = time(9, 0)
    LONDON_SESSION_START = time(7, 0)
    LONDON_SESSION_END = time(16, 0)
    NY_SESSION_START = time(13, 0)
    NY_SESSION_END = time(22, 0)

    current_time_obj = time(hour, minute)

    if LONDON_SESSION_START <= current_time_obj < LONDON_SESSION_END:
        if NY_SESSION_START <= current_time_obj < LONDON_SESSION_END: # Overlap is within London session for definition
            return 'overlap'
        return 'london'
    elif NY_SESSION_START <= current_time_obj < NY_SESSION_END:
        return 'new_york'
    elif ASIAN_SESSION_START <= current_time_obj < ASIAN_SESSION_END:
        return 'asian'
    else:
        return 'none'

def _should_trade_current_session(params: dict, current_session: str) -> bool:
    """
    PHASE 11 ENHANCEMENT: Session filtering based on parameters.
    """
    session_settings = params.get('strategy', {}).get('session_settings', {})
    london_only_mode = params['strategy'].get('london_only_mode', False)

    if london_only_mode:
        if current_session not in ['london', 'overlap']:
            logger.debug(f"LONDON-ONLY MODE: Skipping {current_session} session")
            return False

    if current_session == 'none':
        return False

    return True

def _calculate_atr(data, asset, atr_period: int) -> Optional[float]:
    """
    Calculate Average True Range (ATR).
    """
    if not data.can_trade(asset):
        return None

    # Need atr_period + 1 bars for initial TR calculation and then SMA
    # Fetching 'close', 'high', 'low' for ATR calculation
    hist_data = data.history(asset, ['high', 'low', 'close'], atr_period + 1, '1d')

    if len(hist_data) < atr_period + 1:
        return None

    highs = hist_data['high']
    lows = hist_data['low']
    closes = hist_data['close']

    # Calculate True Range (TR)
    tr_values = []
    for i in range(1, len(hist_data)):
        tr = max(
            highs.iloc[i] - lows.iloc[i],
            abs(highs.iloc[i] - closes.iloc[i-1]),
            abs(lows.iloc[i] - closes.iloc[i-1])
        )
        tr_values.append(tr)

    if not tr_values:
        return None

    # ATR is the simple moving average of True Ranges
    atr = pd.Series(tr_values).mean() # Using .mean() for SMA over tr_values
    return float(atr)

def _detect_range_bound_market(context, data, prev_high: float, prev_low: float) -> bool:
    """
    PHASE 11 CRITICAL ENHANCEMENT: Detect consolidation to avoid whipsaw trades.
    """
    params = context.params
    strategy_params = params.get('strategy', {})
    enable_range_detection = strategy_params.get('enable_range_detection', False)

    if not enable_range_detection:
        return False

    atr_period = strategy_params.get('atr_period', 14)
    range_detection_threshold = strategy_params.get('range_detection_threshold', 1.5)

    atr_value = _calculate_atr(data, context.asset, atr_period)
    if atr_value is None or atr_value == 0:
        return False  # Fail-safe: allow trading if cannot detect ATR

    prev_day_range = prev_high - prev_low
    if atr_value > 0: # Avoid division by zero
        range_ratio = prev_day_range / atr_value
    else:
        return False # If ATR is zero, cannot calculate ratio, assume not range bound

    if range_ratio < range_detection_threshold:
        logger.warning(f"RANGE-BOUND MARKET: ratio {range_ratio:.2f} < {range_detection_threshold:.2f}")
        return True  # DO NOT TRADE

    return False  # Trending market - OK to trade

def _check_daily_trade_limit(context) -> bool:
    """
    Check if the daily trade limit has been reached.
    """
    max_daily_trades = context.params['strategy'].get('MAX_DAILY_TRADES', 2)
    if context.daily_trade_count >= max_daily_trades:
        logger.info(f"Daily trade limit of {max_daily_trades} reached.")
        return False
    return True

def _check_breakout_signals(context, data, current_price: float, prev_high: float, prev_low: float, current_session: str) -> Optional[dict]:
    """
    Generate breakout signals (SIGNAL-ONLY - no position sizing).
    """
    params = context.params
    confidence_threshold = params.get('risk', {}).get('confidence_threshold', 0.0)

    SESSION_CONFIDENCE = {
        'london': 0.95,
        'overlap': 0.85,
        'new_york': 0.75,
        'asian': 0.65,
        'none': 0.0
    }

    signal_confidence = SESSION_CONFIDENCE.get(current_session, 0.0)

    if signal_confidence < confidence_threshold:
        logger.debug(f"Signal confidence {signal_confidence:.2f} below threshold {confidence_threshold:.2f}.")
        return None

    signal = 0
    entry_reason = ""

    if current_price > prev_high and not context.in_position:
        signal = 1  # Long signal
        entry_reason = 'breakout_high'
    elif current_price < prev_low and not context.in_position:
        signal = -1  # Short signal
        entry_reason = 'breakout_low'

    if signal != 0:
        return {
            'signal': signal,
            'confidence': signal_confidence,
            'timestamp': data.current_dt,
            'metadata': {
                'entry_reason': entry_reason,
                'session': current_session,
                'prev_high': prev_high,
                'prev_low': prev_low
            }
        }
    return None

def _check_exit_signals(context, data, current_price: float) -> Optional[dict]:
    """
    Check for trailing stop or end-of-day exit signals.
    """
    params = context.params
    risk_params = params.get('risk', {})
    strategy_params = params.get('strategy', {})

    # End-of-day exit
    eod_exit_hour = strategy_params.get('eod_exit_hour', 23)
    if data.current_dt.hour >= eod_exit_hour and context.in_position:
        logger.info(f"End-of-day exit triggered at {data.current_dt.isoformat()}.")
        return {'signal': 0, 'exit_reason': 'eod_exit'}

    # Trailing Stop Exit
    if risk_params.get('use_trailing_stop', False) and context.in_position:
        trailing_stop_pct = risk_params.get('trailing_stop_pct', 0.08)
        trail_activation_pips = strategy_params.get('TRAIL_ACTIVATION_PIPS', 10)
        trail_distance_pips = strategy_params.get('TRAIL_DISTANCE_PIPS', 10)

        # Convert pips to price difference dynamically based on asset type.
        # JPY pairs use 2 decimal places (0.01), other forex pairs use 4 decimal places (0.0001)
        pip_value = 0.01 if 'JPY' in context.asset.symbol else 0.0001

        profit_pips = (current_price - context.entry_price) / pip_value * (1 if context.position_direction == 1 else -1)

        if context.trailing_stop_active:
            if context.position_direction == 1: # Long position
                stop_level = context.highest_price * (1 - trailing_stop_pct)
                if current_price <= stop_level:
                    logger.info(f"Trailing stop (long) triggered at {current_price:.4f}. Stop level: {stop_level:.4f}")
                    return {'signal': 0, 'exit_reason': 'trailing_stop'}
                context.highest_price = max(context.highest_price, current_price) # Update highest price
            else: # Short position
                stop_level = context.highest_price * (1 + trailing_stop_pct)
                if current_price >= stop_level:
                    logger.info(f"Trailing stop (short) triggered at {current_price:.4f}. Stop level: {stop_level:.4f}")
                    return {'signal': 0, 'exit_reason': 'trailing_stop'}
                context.highest_price = min(context.highest_price, current_price) # Update lowest price for short
        elif profit_pips >= trail_activation_pips: # Activate trailing stop
            context.trailing_stop_active = True
            context.highest_price = current_price # Set initial highest price upon activation
            logger.info(f"Trailing stop activated. Current price: {current_price:.4f}, Profit: {profit_pips:.2f} pips")

    return None


def _get_required_param(params: dict, *keys, default=None, error_msg: str = None):
    """
    Safely retrieve a nested parameter with clear error messaging.

    Args:
        params: Parameters dictionary
        *keys: Nested keys to traverse (e.g., 'strategy', 'asset_symbol')
        default: Default value if not found (None raises error for required params)
        error_msg: Custom error message

    Returns:
        Parameter value

    Raises:
        ValueError: If required parameter is missing (when default is None)

    Example:
        asset = _get_required_param(params, 'strategy', 'asset_symbol')
        warmup = _get_required_param(params, 'backtest', 'warmup_days', default=30)
    """
    value = params
    path = []
    for key in keys:
        path.append(str(key))
        if not isinstance(value, dict):
            value = None
            break
        value = value.get(key)
        if value is None:
            break

    if value is None:
        if default is not None:
            return default
        path_str = '.'.join(path)
        msg = error_msg or (
            f"Missing required parameter '{path_str}' in parameters.yaml. "
            f"Please add this parameter to your strategy configuration."
        )
        raise ValueError(msg)

    return value


def compute_position_size(context, data) -> float:
    """
    Calculate position size based on the configured method.

    Supports three methods:
    - 'fixed': Returns max_position_pct directly
    - 'volatility_scaled': Scales position inversely with volatility to target vol
    - 'kelly': Uses Kelly Criterion with fractional sizing for capital preservation

    Args:
        context: Zipline context object with params
        data: Zipline data object for price history

    Returns:
        Position size as float (0.0 to max_position_pct)
    """
    params = context.params
    pos_config = params.get('position_sizing', {})
    method = pos_config.get('method', 'fixed')
    max_position = pos_config.get('max_position_pct', 0.95)
    min_position = pos_config.get('min_position_pct', 0.10)

    if method == 'fixed':
        return max_position

    elif method == 'volatility_scaled':
        vol_lookback = pos_config.get('volatility_lookback', 20)
        vol_target = pos_config.get('volatility_target', 0.15)

        if not data.can_trade(context.asset):
            return max_position

        try:
            # Fetch minute data for volatility calculation, as it's an intraday strategy
            # Request enough bars for the lookback period (24 hours * 60 minutes/day)
            bar_count = vol_lookback * 1440 # Roughly equivalent to days in minutes
            prices = data.history(context.asset, 'price', bar_count + 1, '1m')
            
            if len(prices) < bar_count + 1:
                logger.warning(f"Insufficient minute data for volatility calculation for {context.asset.symbol}. Returning max position.")
                return max_position

            returns = prices.pct_change().dropna()
            if len(returns) < bar_count:
                logger.warning(f"Insufficient returns data for volatility calculation for {context.asset.symbol}. Returning max position.")
                return max_position

            # Annualized volatility
            # Use trading_days_per_year from parameters for correct annualization
            trading_days = params.get('backtest', {}).get('trading_days_per_year', 260)
            # Calculate daily volatility from minute returns, then annualize
            # Assuming 1440 minutes in a trading day (24*60)
            daily_returns = returns.resample('1D').apply(lambda x: (1 + x).prod() - 1).dropna()
            if len(daily_returns) > 0 and daily_returns.std() > 0:
                current_vol = daily_returns.std() * np.sqrt(trading_days)
            else:
                current_vol = 0.0

            if current_vol > 0:
                size = vol_target / current_vol
                return float(np.clip(size, min_position, max_position))

            return max_position
        except Exception as e:
            logger.error(f"Error in volatility-scaled position sizing for {context.asset.symbol}: {e}. Returning max position.")
            return max_position

    elif method == 'kelly':
        # Kelly Criterion: f* = (bp - q) / b
        # where b = avg_win/avg_loss ratio, p = win rate, q = 1 - p
        kelly_config = pos_config.get('kelly', {})
        win_rate = kelly_config.get('win_rate_estimate', 0.55)
        win_loss_ratio = kelly_config.get('avg_win_loss_ratio', 1.5)
        kelly_fraction = kelly_config.get('kelly_fraction', 0.25)
        kelly_min = kelly_config.get('min_position_pct', min_position)

        # Kelly formula
        b = win_loss_ratio
        p = win_rate
        q = 1 - p

        # Full Kelly (can be > 1 for high edge strategies)
        full_kelly = (b * p - q) / b if b > 0 else 0

        # Apply fractional Kelly for safety (typically 0.25-0.50 of full Kelly)
        position_size = full_kelly * kelly_fraction

        # Clamp to bounds
        return float(np.clip(position_size, kelly_min, max_position))

    # Fallback for unknown method
    return max_position


def initialize(context):
    """
    Set up the strategy.

    This function is called once at the start of the backtest.
    Load parameters, set up assets, configure costs, and schedule functions.
    """
    # Load parameters from YAML
    params = load_params()

    # Store parameters in context for easy access
    context.params = params

    # Calculate and store required warmup days
    context.required_warmup_days = _calculate_required_warmup(params)

    # Validate warmup configuration
    configured_warmup = params.get('backtest', {}).get('warmup_days')
    if configured_warmup is not None and configured_warmup < context.required_warmup_days:
        import warnings
        warnings.warn(
            f"Configured warmup_days ({configured_warmup}) is less than calculated "
            f"required warmup ({context.required_warmup_days}) based on indicator periods. "
            f"Consider increasing warmup_days in parameters.yaml to avoid insufficient data."
        )

    # Get data frequency from parameters, default to 'minute' for forex
    context.data_frequency = _get_required_param(params, 'backtest', 'data_frequency', default='minute')

    # Get asset symbol from parameters (required)
    asset_symbol = _get_required_param(
        params, 'strategy', 'asset_symbol',
        error_msg="Missing required parameter 'strategy.asset_symbol' in parameters.yaml. "
                  "Example: asset_symbol: SPY (for equities), BTC-USD (for crypto), EURUSD=X (for forex)"
    )
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop tracking
    context.day_count = 0  # For explicit warmup tracking
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop tracking
    context.day_count = 0  # For explicit warmup tracking
    context.daily_trade_count = 0 # For daily trade limit
    context.current_date = None # To track date changes for daily limits
    context.position_direction = 0 # 1 for long, -1 for short
    context.trailing_stop_active = False
    
    # Set benchmark
    set_benchmark(context.asset)

    # Attach Pipeline only if use_pipeline is enabled (and Pipeline is available)
    context.pipeline_data = None
    context.pipeline_universe = []
    context.use_pipeline = params['strategy'].get('use_pipeline', False)
    if context.use_pipeline and _PIPELINE_AVAILABLE:
        pipeline = make_pipeline()
        if pipeline is not None:
            attach_pipeline(pipeline, 'my_pipeline')
    
    # Configure commission model
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        # For forex, commissions are typically per share (unit) or a fixed amount per trade
        # Adjusting for forex based on parameters.yaml
        us_equities=commission.PerShare( # Using PerShare for flexibility
            cost=commission_config.get('per_share', 0.00002), # Default 0.2 pips
            min_trade_cost=commission_config.get('min_cost', 0.0) # Default 0.0 for forex
        )
    )
    
    # Configure slippage model
    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )
    
    # Schedule main trading function
    rebalance_frequency = params['strategy'].get('rebalance_frequency', 'daily')
    minutes_after_open = params['strategy'].get('minutes_after_open', 0) # Default to 0 for intraday
    
    if rebalance_frequency == 'daily':
        schedule_function(
            rebalance,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=minutes_after_open)
        )
    elif rebalance_frequency == 'weekly':
        schedule_function(
            rebalance,
            date_rule=date_rules.week_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=minutes_after_open)
        )
    elif rebalance_frequency == 'monthly':
        schedule_function(
            rebalance,
            date_rule=date_rules.month_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=minutes_after_open)
        )
    
    # Schedule risk management checks if enabled
    if params.get('risk', {}).get('use_stop_loss', False) or params.get('risk', {}).get('use_trailing_stop', False):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1) # Check frequently
        )

    # Schedule before_trading_start explicitly for cross-version compatibility
    # This ensures pipeline data is fetched before rebalance runs
    schedule_function(
        before_trading_start,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )


def make_pipeline():
    """
    Create Pipeline with generic pricing data.
    
    This strategy doesn't use Pipeline (use_pipeline: false), but this function
    is provided for completeness in case pipeline support is needed in the future.
    """
    if not _PIPELINE_AVAILABLE or _PRICING_CLASS is None:
        return None
    # Return a minimal pipeline - not used by this strategy
    return None


def before_trading_start(context, data):
    """
    Called once per day before market open.
    Use this to reset daily counters or fetch any pre-trading data.
    """
    current_date = data.current_dt.date()
    if context.current_date is None or context.current_date != current_date:
        context.daily_trade_count = 0
        context.current_date = current_date
        logger.info(f"New trading day: {current_date}. Daily trade count reset.")
    
    # For this strategy, no pipeline is used, so we just pass.
    pass

def compute_signals(context, data) -> Tuple[Optional[int], dict]:
    """
    Compute trading signals for the Breakout Intraday strategy.
        
    Returns:
        signal: 1 for long, -1 for short, 0 for exit/hold
        additional_data: dict of values to record
    """
    if not data.can_trade(context.asset):
        return None, {}

    current_price = data.current(context.asset, 'price')
    if pd.isna(current_price):
        return None, {}

    prev_high, prev_low = _calculate_previous_day_levels(context, data)

    if prev_high is None or prev_low is None:
        return None, {}

    current_session = _get_current_session(data.current_dt)

    # Phase 11 Filters
    if not _should_trade_current_session(context.params, current_session):
        return 0, {'filter_reason': 'session_filter'}

    if not _check_daily_trade_limit(context):
        return 0, {'filter_reason': 'daily_trade_limit'}

    if _detect_range_bound_market(context, data, prev_high, prev_low):
        return 0, {'filter_reason': 'range_detection'}

    signal = None
    additional_data = {}

    # Check for exit signals first if in position
    if context.in_position:
        exit_signal_data = _check_exit_signals(context, data, current_price)
        if exit_signal_data:
            context.in_position = False
            context.entry_price = 0.0
            context.highest_price = 0.0
            context.position_direction = 0
            context.trailing_stop_active = False
            additional_data['exit_reason'] = exit_signal_data['exit_reason']
            signal = 0 # Exit signal
            logger.info(f"Exit signal: {exit_signal_data['exit_reason']} at {current_price:.4f}")
            return signal, additional_data

    # Check for entry signals if not in position (and no exit was triggered)
    if not context.in_position:
        entry_signal_data = _check_breakout_signals(context, data, current_price, prev_high, prev_low, current_session)
        if entry_signal_data:
            signal = entry_signal_data['signal']
            context.daily_trade_count += 1
            additional_data.update(entry_signal_data['metadata'])
            additional_data['confidence'] = entry_signal_data['confidence']
            logger.info(f"Entry signal: {entry_signal_data['metadata']['entry_reason']} ({signal}) at {current_price:.4f} in {current_session} session.")

    return signal, additional_data


def rebalance(context, data):
    """
    Main rebalancing function called on schedule.

    This function:
    1. Checks warmup period
    2. Computes signals
    3. Executes trades
    4. Records metrics
    """
    # Increment day counter for warmup tracking
    context.day_count += 1

    # Skip warmup period - ensures sufficient data for indicators
    warmup_days = context.params.get('backtest', {}).get('warmup_days')
    if warmup_days is None:
        warmup_days = context.required_warmup_days

    if context.day_count <= warmup_days:
        return

    signal_tuple = compute_signals(context, data)
    if signal_tuple is None or signal_tuple[0] is None:
        # No signal or an error occurred in compute_signals, simply return.
        return

    signal, additional_data = signal_tuple

    current_price = data.current(context.asset, 'price')
    if pd.isna(current_price):
        return

    # Record metrics
    record_data = {
        'signal': signal,
        'price': current_price,
        **additional_data
    }
    record(**record_data)

    # Cancel any open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)

    # Execute trades based on signal using dynamic position sizing
    if signal == 1 and not context.in_position: # Long entry
        position_size = compute_position_size(context, data)
        if position_size > 0:
            order_target_percent(context.asset, position_size)
            context.in_position = True
            context.entry_price = current_price
            context.highest_price = current_price  # Initialize for trailing stop
            context.position_direction = 1
            context.trailing_stop_active = False
            logger.info(f"Entered LONG position in {context.asset.symbol} at {current_price:.4f} with size {position_size:.2f}%")

    elif signal == -1 and not context.in_position: # Short entry
        position_size = compute_position_size(context, data)
        if position_size > 0:
            order_target_percent(context.asset, -position_size) # Negative for short position
            context.in_position = True
            context.entry_price = current_price
            context.highest_price = current_price  # Initialize for trailing stop (will track lowest for short)
            context.position_direction = -1
            context.trailing_stop_active = False
            logger.info(f"Entered SHORT position in {context.asset.symbol} at {current_price:.4f} with size {position_size:.2f}%")

    elif signal == 0 and context.in_position: # Exit position
        # An exit signal (0) could come from compute_signals (e.g., EOD exit, trailing stop)
        # Or it could be a manual exit by strategy logic
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        context.position_direction = 0
        context.trailing_stop_active = False
        logger.info(f"Exited position in {context.asset.symbol} at {current_price:.4f}")


def check_stop_loss(context, data):
    """
    Check and execute stop loss orders.

    Supports both fixed and trailing stop losses:
    - Fixed stop: exits when price drops below entry_price * (1 - stop_loss_pct)
    - Trailing stop: exits when price drops below highest_price * (1 - trailing_stop_pct)

    Called separately from rebalance to check stops more frequently.
    """
    if not context.in_position:
        return

    if not data.can_trade(context.asset):
        return

    current_price = data.current(context.asset, 'price')
    risk_params = context.params.get('risk', {})

    # Update highest/lowest price for trailing stop tracking
    if context.position_direction == 1: # Long position
        if context.highest_price > 0: # Only update if already tracking
            context.highest_price = max(context.highest_price, current_price)
        else:
            context.highest_price = current_price # Initialize if not yet set
    elif context.position_direction == -1: # Short position, track lowest price
        if context.highest_price < float('inf') and context.highest_price > 0: # Only update if already tracking
            context.highest_price = min(context.highest_price, current_price)
        else:
            context.highest_price = current_price # Initialize (using highest_price to store lowest for short)

    should_stop = False
    stop_type = None

    if context.position_direction == 1: # Long position
        # Check trailing stop first (takes precedence if both enabled)
        if risk_params.get('use_trailing_stop', False) and context.trailing_stop_active:
            trailing_stop_pct = risk_params.get('trailing_stop_pct', 0.08)
            stop_price = context.highest_price * (1 - trailing_stop_pct)
            if current_price <= stop_price:
                should_stop = True
                stop_type = 'trailing'
                logger.info(f"Long Trailing stop triggered for {context.asset.symbol} at {current_price:.4f}. Stop level: {stop_price:.4f}")

        # Check fixed stop if trailing not triggered or not active
        if not should_stop and risk_params.get('use_stop_loss', False):
            stop_loss_pct = risk_params.get('stop_loss_pct', 0.05)
            if context.entry_price > 0:
                stop_price = context.entry_price * (1 - stop_loss_pct)
                if current_price <= stop_price:
                    should_stop = True
                    stop_type = 'fixed'
                    logger.info(f"Long Fixed stop loss triggered for {context.asset.symbol} at {current_price:.4f}. Stop level: {stop_price:.4f}")

    elif context.position_direction == -1: # Short position
        # Check trailing stop for short position
        if risk_params.get('use_trailing_stop', False) and context.trailing_stop_active:
            trailing_stop_pct = risk_params.get('trailing_stop_pct', 0.08)
            # For short, stop is above price, so add percentage to lowest (highest_price holds lowest for shorts)
            stop_price = context.highest_price * (1 + trailing_stop_pct)
            if current_price >= stop_price:
                should_stop = True
                stop_type = 'trailing'
                logger.info(f"Short Trailing stop triggered for {context.asset.symbol} at {current_price:.4f}. Stop level: {stop_price:.4f}")

        # Check fixed stop for short position
        if not should_stop and risk_params.get('use_stop_loss', False):
            stop_loss_pct = risk_params.get('stop_loss_pct', 0.05)
            if context.entry_price > 0:
                stop_price = context.entry_price * (1 + stop_loss_pct) # For short, stop is above entry
                if current_price >= stop_price:
                    should_stop = True
                    stop_type = 'fixed'
                    logger.info(f"Short Fixed stop loss triggered for {context.asset.symbol} at {current_price:.4f}. Stop level: {stop_price:.4f}")

    if should_stop:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        context.position_direction = 0
        context.trailing_stop_active = False
        record(stop_triggered=1, stop_type=1 if stop_type == 'fixed' else 2, current_price_at_stop=current_price)
    else:
        record(stop_triggered=0)


def handle_data(context, data):
    """
    Called every bar.
    
    Use this for intra-bar logic or recording. For most strategies,
    schedule_function in initialize() is preferred.
    """
    pass


def analyze(context, perf):
    """
    Post-backtest analysis.

    This function is called after the backtest completes.
    Use it to print summary statistics or perform final calculations.

    Args:
        context: Zipline context object
        perf: Performance DataFrame with returns, positions, etc.
    """
    params = load_params()
    asset_symbol = params['strategy']['asset_symbol']

    print("\n" + "=" * 60)
    print(f"BREAKOUT INTRADAY STRATEGY RESULTS: {asset_symbol}")
    print("=" * 60)

    # Calculate basic metrics
    returns = perf['returns'].dropna()
    total_return = (1 + returns).prod() - 1
    final_value = perf['portfolio_value'].iloc[-1]

    # Use empyrical for consistent Sharpe calculation (matches lib/metrics.py)
    # NOTE: Adjust annualization factor based on asset class:
    #   - Equities: 252
    #   - Forex: 260
    #   - Crypto: 365
    try:
        import empyrical as ep
        # Get risk-free rate and trading days per year from parameters
        risk_free_annual = params.get('backtest', {}).get('risk_free_rate', 0.04)
        trading_days_per_year = params.get('backtest', {}).get('trading_days_per_year', 260) # Default to 260 for forex
        risk_free_daily = risk_free_annual / trading_days_per_year
        
        sharpe = float(ep.sharpe_ratio(returns, risk_free=risk_free_daily, period='daily', annualization=trading_days_per_year))
        max_dd = float(ep.max_drawdown(returns))
        # Validate Sharpe ratio
        if not np.isfinite(sharpe):
            sharpe = 0.0
    except ImportError:
        # Fallback if empyrical not available
        if len(returns) > 0 and returns.std() > 0:
            # Fallback to 260 trading days for forex if empyrical is not available
            trading_days_per_year_fallback = params.get('backtest', {}).get('trading_days_per_year', 260)
            sharpe = np.sqrt(trading_days_per_year_fallback) * returns.mean() / returns.std()
        else:
            sharpe = 0.0
        cumulative = (1 + returns).cumprod()
        max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()

    print(f"Total Return: {total_return:.2%}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)

