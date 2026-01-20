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

REQUIREMENTS:
- This template requires v1.11.0 or later of The Researcher's Cockpit
- The lib/ package uses modular architecture (v1.11.0+)
- The lib/ package must be properly installed and available

MODULAR ARCHITECTURE (v1.11.0+):
- lib/bundles/ - Data bundle management (replaces lib/data_loader.py)
- lib/validation/ - Data validation (replaces lib/data_validation.py)
- lib/calendars/ - Trading calendars (replaces lib/extension.py)
- lib/config/ - Configuration loading with validation
- lib/strategies/ - Strategy management utilities
All imports use canonical paths from lib/_exports.py
==============================================================================
"""

# Standard library imports
import sys
import warnings
from pathlib import Path

# Third-party imports
import numpy as np
import pandas as pd
from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order,
)
from zipline.finance import commission, slippage

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

# Local imports
from lib.paths import get_project_root
from lib.config import load_strategy_params, get_warmup_days, validate_strategy_params
from lib.position_sizing import compute_position_size
from lib.risk_management import check_exit_conditions, get_exit_type_code
from lib.pipeline_utils import setup_pipeline

# =============================================================================
# IMPORT NOTES (v1.11.0 Modular Architecture)
# =============================================================================
# All imports use canonical paths from lib/_exports.py:
# - lib.paths: Project root and directory resolution
# - lib.config: Configuration loading and validation
# - lib.position_sizing: Position sizing algorithms
# - lib.risk_management: Risk management utilities
# - lib.pipeline_utils: Pipeline API setup helpers
#
# For data operations, use:
# - lib.bundles: Bundle ingestion and management (ingest_bundle, load_bundle)
# - lib.validation: Data validation (DataValidator, validate_bundle)
# - lib.calendars: Trading calendars (register_custom_calendars, CryptoCalendar)
# =============================================================================

_project_root = get_project_root()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def load_params():
    """
    Load parameters from parameters.yaml file using lib.config.
    
    Requires v1.11.0+ with lib.config.load_strategy_params() available.
    Uses modular architecture for configuration loading.
    
    Returns:
        dict: Strategy parameters
        
    Raises:
        FileNotFoundError: If parameters.yaml file is not found
        ValueError: If asset_class cannot be inferred from path
        
    See Also:
        lib.config.load_strategy_params - Main configuration loader
        lib.config.validate_strategy_params - Parameter validation
    """
    # Extract strategy name from path: strategies/{asset_class}/{name}/strategy.py
    strategy_path = Path(__file__).parent
    strategy_name = strategy_path.name
    
    # Try to infer asset_class from parent directory
    asset_class = strategy_path.parent.name
    
    # Validate asset_class
    if asset_class in ('strategies', '_template'):
        raise ValueError(
            f"Cannot infer asset_class from path {strategy_path}. "
            "Strategy must be in strategies/{{asset_class}}/{{name}}/"
        )
    
    try:
        return load_strategy_params(strategy_name, asset_class)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Failed to load parameters for strategy '{strategy_name}'. "
            f"Ensure parameters.yaml exists. Original error: {e}"
        ) from e
    # Let other exceptions propagate (ImportError, etc.)


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


def initialize(context):
    """
    Set up the strategy.

    This function is called once at the start of the backtest.
    Load parameters, set up assets, configure costs, and schedule functions.
    """
    # Load parameters from YAML
    params = load_params()
    
    # Extract strategy name for validation
    strategy_path = Path(__file__).parent
    strategy_name = strategy_path.name
    
    # Validate parameter structure
    is_valid, errors = validate_strategy_params(params, strategy_name)
    if not is_valid:
        error_msg = f"Invalid parameters.yaml for strategy '{strategy_name}':\n"
        error_msg += "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    # Store parameters in context for easy access
    context.params = params

    # Calculate and store required warmup days using lib function
    context.required_warmup_days = get_warmup_days(params)

    # Validate warmup configuration
    configured_warmup = params.get('backtest', {}).get('warmup_days')
    if configured_warmup is not None and configured_warmup < context.required_warmup_days:
        warnings.warn(
            f"Configured warmup_days ({configured_warmup}) is less than calculated "
            f"required warmup ({context.required_warmup_days}) based on indicator periods. "
            f"Consider increasing warmup_days in parameters.yaml to avoid insufficient data.",
            UserWarning,
            stacklevel=2
        )

    # Get data frequency from parameters, default to 'daily'
    context.data_frequency = _get_required_param(params, 'backtest', 'data_frequency', default='daily')

    # Get asset symbol from parameters (required)
    asset_symbol = _get_required_param(
        params, 'strategy', 'asset_symbol',
        error_msg="Missing required parameter 'strategy.asset_symbol' in parameters.yaml. "
                  "Example: asset_symbol: SPY (for equities), BTC-USD (for crypto), EURUSD=X (for forex)"
    )
    
    # Validate asset symbol is not a placeholder
    if asset_symbol in ['SPY', 'PLACEHOLDER', '']:
        warnings.warn(
            f"Asset symbol '{asset_symbol}' appears to be a placeholder. "
            "Please update strategy.asset_symbol in parameters.yaml with your actual trading symbol.",
            UserWarning,
            stacklevel=2
        )
    
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop tracking (initialized here)
    context.day_count = 0  # For explicit warmup tracking
    
    # Set benchmark
    set_benchmark(context.asset)

    # Set up pipeline using library function
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
    
    # Configure commission model
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
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
    rebalance_frequency = params.get('strategy', {}).get('rebalance_frequency', 'daily')
    
    # Validate rebalance frequency
    valid_frequencies = ['daily', 'weekly', 'monthly']
    if rebalance_frequency not in valid_frequencies:
        warnings.warn(
            f"Invalid rebalance_frequency '{rebalance_frequency}'. "
            f"Must be one of: {valid_frequencies}. Defaulting to 'daily'.",
            UserWarning,
            stacklevel=2
        )
        rebalance_frequency = 'daily'
    
    if rebalance_frequency == 'daily':
        schedule_function(
            rebalance,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=params.get('strategy', {}).get('minutes_after_open', 30))
        )
    elif rebalance_frequency == 'weekly':
        schedule_function(
            rebalance,
            date_rule=date_rules.week_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=params.get('strategy', {}).get('minutes_after_open', 30))
        )
    elif rebalance_frequency == 'monthly':
        schedule_function(
            rebalance,
            date_rule=date_rules.month_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=params.get('strategy', {}).get('minutes_after_open', 30))
        )
    
    # Schedule risk management checks if enabled
    risk_params = params.get('risk', {})
    if (risk_params.get('use_stop_loss', False) or 
        risk_params.get('use_trailing_stop', False) or 
        risk_params.get('use_take_profit', False)):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )

    # Schedule before_trading_start explicitly for cross-version compatibility
    # This ensures pipeline data is fetched before rebalance runs
    # Use minutes=1 for minute data (Zipline requires at least 1 minute offset)
    before_open_minutes = 1 if context.data_frequency == 'minute' else 0
    schedule_function(
        before_trading_start,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=before_open_minutes)
    )


def make_pipeline():
    """
    Create Pipeline with generic pricing data.
    
    This is an example pipeline. Customize based on your strategy needs.
    The window_length should be parameterized in your actual implementation.
    
    NOTE: Pipeline API is primarily designed for US equities. For crypto/forex,
    consider using direct price data access via data.history() instead.
    
    See Also:
        lib.pipeline_utils.setup_pipeline - Pipeline setup helper
        lib.pipeline_utils.validate_pipeline_config - Pipeline validation
    """
    if not _PIPELINE_AVAILABLE or _PRICING_CLASS is None:
        return None
    # Example: Use lookback_period from parameters (default to 30 if not specified)
    # In your actual strategy, parameterize this based on your needs
    window_length = 30  # Example value - parameterize this in your strategy
    sma = SimpleMovingAverage(inputs=[_PRICING_CLASS.close], window_length=window_length)
    return Pipeline(columns={'sma': sma}, screen=sma.isfinite())

def before_trading_start(context, data):
    """
    Called once per day before market open.

    Use this to fetch pipeline output and update context.
    """
    if context.use_pipeline and _PIPELINE_AVAILABLE:
        try:
            context.pipeline_data = pipeline_output('my_pipeline')
            # Example: Store the list of assets in our universe
            context.pipeline_universe = context.pipeline_data.index.tolist()
        except (KeyError, AttributeError, ValueError) as e:
            # Pipeline output may not be available yet or may have errors
            # Log and continue with empty pipeline data
            context.pipeline_data = None
            context.pipeline_universe = []

def compute_signals(context, data):
    """
    Compute trading signals based on your strategy logic.
    
    This is where you implement your trading hypothesis.
    
    COMMON PATTERNS:
    
    1. Momentum (Trend Following):
       - Price above/below moving average
       - Breakout above resistance
       - Rate of change indicators
       Example: Buy when price > SMA(50) and price crosses above SMA(20)
    
    2. Mean Reversion:
       - Price deviation from mean
       - RSI oversold/overbought
       - Bollinger Band extremes
       Example: Buy when RSI < 30, sell when RSI > 70
    
    3. Multi-Asset (Pipeline-based):
       - Use context.pipeline_data for factor-based selection
       - Rank assets by factor values
       - Select top/bottom N assets
       Example: Rank by momentum factor, select top 5 assets
    
    ASSET CLASS EXAMPLES:
    
    Equities: Use Pipeline API for multi-asset strategies
        - Access to fundamental data and factors
        - Screen large universes efficiently
        - Example: Select top 20 stocks by momentum factor
    
    Crypto: Direct price/indicator strategies (no Pipeline)
        - Use data.history() for price data
        - Calculate technical indicators directly
        - Example: BTC/USD momentum using SMA crossover
    
    Forex: Direct price/indicator strategies (no Pipeline)
        - Use data.history() for price data
        - Consider session-based patterns
        - Example: EUR/USD mean reversion using Bollinger Bands
    
    TROUBLESHOOTING:
    
    - If data.history() fails: Check that lookback period <= available data
    - If pipeline_data is None: Ensure use_pipeline: true and pipeline is attached
    - If signals are always 0: Verify indicator calculations and thresholds
    
    See docs/code_patterns/ for detailed examples and best practices.
    
    See Also:
        lib.bundles.ingest_bundle - For data ingestion before backtest
        lib.validation.validate_bundle - For bundle validation
        lib.calendars.get_calendar_for_asset_class - For calendar selection
    
    Args:
        context: Zipline context object with params attribute
        data: Zipline data object for price history and current prices
        
    Returns:
        tuple: (signal, additional_data)
            - signal: 1 for buy, -1 for sell, 0 for hold
            - additional_data: dict of values to record (e.g., {'sma': 100.5, 'rsi': 45.2})
    """
    # TODO: Implement your strategy logic here
    # 
    # EXAMPLE PATTERNS:
    #
    # Pattern 1: Pipeline-based strategy (if use_pipeline: true)
    #   if context.use_pipeline and context.pipeline_data is not None:
    #       if context.asset in context.pipeline_universe:
    #           factor_value = context.pipeline_data.loc[context.asset]['factor_name']
    #           current_price = data.current(context.asset, 'price')
    #           # Generate signal based on factor
    #
    # Pattern 2: Direct price/indicator strategy (if use_pipeline: false)
    #   current_price = data.current(context.asset, 'price')
    #   prices = data.history(context.asset, 'price', lookback_period, '1d')
    #   sma = prices.mean()
    #   # Generate signal based on price vs SMA
    #
    # Pattern 3: Multi-asset strategy
    #   for asset in context.pipeline_universe:
    #       # Evaluate each asset and select best
    #
    signal = 0
    additional_data = {}

    # Example: Simple price-based signal (works for all asset classes)
    if not data.can_trade(context.asset):
        return 0, additional_data
    
    current_price = data.current(context.asset, 'price')
    
    # Example: Simple momentum signal (replace with your logic)
    # This is a placeholder - implement your actual strategy here
    lookback = context.params.get('strategy', {}).get('lookback_period', 30)
    threshold_pct = context.params.get('strategy', {}).get('signal_threshold_pct', 0.02)
    
    try:
        prices = data.history(context.asset, 'price', lookback, '1d')
        if len(prices) >= lookback:
            sma = prices.mean()
            if current_price > sma * (1 + threshold_pct):
                signal = 1
            elif current_price < sma * (1 - threshold_pct):
                signal = -1
            additional_data['sma'] = sma
    except (KeyError, ValueError, AttributeError) as e:
        # If history fails (insufficient data, invalid asset, etc.), return neutral signal
        # Log error for debugging (using warnings since logging may not be configured)
        warnings.warn(
            f"Error computing signals for {context.asset}: {e}. "
            "Returning neutral signal.",
            UserWarning,
            stacklevel=2
        )

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

    signal, additional_data = compute_signals(context, data)

    if signal is None:
        return

    current_price = data.current(context.asset, 'price')

    # Record metrics
    record(
        signal=signal,
        price=current_price,
        **additional_data
    )

    # Cancel any open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)

    # Execute trades based on signal using dynamic position sizing
    if signal == 1 and not context.in_position:
        # Calculate position size based on configured method
        position_size = compute_position_size(context, data, context.params)
        order_target_percent(context.asset, position_size)
        context.in_position = True
        context.entry_price = current_price
        context.highest_price = current_price  # Initialize for trailing stop

    elif signal == -1 and context.in_position:
        # Exit position
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0  # Reset trailing stop tracking


def check_stop_loss(context, data):
    """
    Check and execute stop loss, trailing stop, and take profit orders.

    This function uses lib.risk_management to check exit conditions and
    executes the exit if any condition is met.

    Supports:
    - Fixed stop: exits when price drops below entry_price * (1 - stop_loss_pct)
    - Trailing stop: exits when price drops below highest_price * (1 - trailing_stop_pct)
    - Take profit: exits when price rises above entry_price * (1 + take_profit_pct)

    Called separately from rebalance to check stops more frequently.
    """
    # Use library function to check exit conditions
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    
    if exit_type:
        # Execute exit
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        
        # Record exit type using library helper
        exit_type_code = get_exit_type_code(exit_type)
        record(
            stop_triggered=1 if exit_type != 'take_profit' else 0,
            take_profit_triggered=1 if exit_type == 'take_profit' else 0,
            exit_type=exit_type_code
        )
    else:
        record(stop_triggered=0, take_profit_triggered=0)


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

    v1.11.0: When metrics_set='none', Zipline doesn't populate standard columns.
    This function now stores portfolio_value and returns in perf DataFrame
    for post-backtest metric calculation.

    Args:
        context: Zipline context object
        perf: Performance DataFrame (may be empty if metrics_set='none')
    """
    params = load_params()

    # Get strategy configuration
    strategy_config = params.get('strategy', {})
    asset_symbol = strategy_config.get('asset_symbol', 'UNKNOWN')
    asset_class = strategy_config.get('asset_class', 'equities')

    # Get risk-free rate and trading days from backtest config
    backtest_config = params.get('backtest', {})
    risk_free_rate = backtest_config.get('risk_free_rate', 0.04)

    # Trading days varies by asset class - use config or default by asset class
    trading_days_defaults = {'equities': 252, 'forex': 260, 'crypto': 365}
    trading_days = backtest_config.get(
        'trading_days_per_year',
        trading_days_defaults.get(asset_class, 252)
    )

    # Calculate daily risk-free rate
    daily_rf = risk_free_rate / trading_days

    print("\n" + "=" * 60)
    print(f"STRATEGY RESULTS: {asset_symbol}")
    print("=" * 60)

    # Calculate basic metrics
    # v1.11.0: Handle case where returns column is missing (when metrics_set='none')
    # Calculate returns from portfolio_value if needed
    if 'returns' in perf.columns:
        returns = perf['returns'].dropna()
    elif 'portfolio_value' in perf.columns:
        # Calculate returns from portfolio_value
        pv = perf['portfolio_value'].dropna()
        if len(pv) > 1:
            returns = pv.pct_change().dropna()
        else:
            returns = pd.Series(dtype=float)
    else:
        returns = pd.Series(dtype=float)
    
    total_return = (1 + returns).prod() - 1 if len(returns) > 0 else 0.0
    capital_base = context.portfolio.starting_cash if hasattr(context.portfolio, 'starting_cash') else context.portfolio.portfolio_value
    final_value = perf['portfolio_value'].iloc[-1] if 'portfolio_value' in perf.columns else capital_base

    # Use empyrical for consistent Sharpe/Sortino calculation (matches lib/metrics.py)
    # Note: lib/metrics.calculate_metrics() provides the same functionality
    # and is used by the backtest runner for standardized metric calculation
    try:
        import empyrical as ep
        sharpe = float(ep.sharpe_ratio(
            returns,
            risk_free=daily_rf,
            period='daily',
            annualization=trading_days
        ))
        sortino = float(ep.sortino_ratio(
            returns,
            required_return=daily_rf,
            period='daily',
            annualization=trading_days
        ))
        max_dd = float(ep.max_drawdown(returns))

        # Validate metrics (handle edge cases)
        if not np.isfinite(sharpe):
            sharpe = 0.0
        if not np.isfinite(sortino):
            sortino = 0.0
    except ImportError:
        # Fallback if empyrical not available
        if len(returns) > 0 and returns.std() > 0:
            excess_return = returns.mean() - daily_rf
            sharpe = np.sqrt(trading_days) * excess_return / returns.std()
        else:
            sharpe = 0.0
        sortino = 0.0  # Sortino requires empyrical for proper downside deviation
        cumulative = (1 + returns).cumprod()
        max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()

    # Print results
    print(f"Total Return: {total_return:.2%}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Sortino Ratio: {sortino:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("-" * 60)
    print(f"Config: risk_free_rate={risk_free_rate:.2%}, trading_days={trading_days}")
    print("=" * 60)

