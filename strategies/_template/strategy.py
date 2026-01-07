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
# Uses centralized utility for robust path resolution
try:
    from lib.utils import get_project_root
    _project_root = get_project_root()
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from lib.config import load_strategy_params
    _has_lib_config = True
except ImportError:
    # Fallback: Try to find project root manually if lib not available
    markers = ['pyproject.toml', '.git', 'config/settings.yaml', 'CLAUDE.md']
    current = Path(__file__).resolve().parent
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                _project_root = current
                if str(_project_root) not in sys.path:
                    sys.path.insert(0, str(_project_root))
                break
        else:
            current = current.parent
            continue
        break
    else:
        raise RuntimeError("Could not find project root. Missing marker files.")
    
    # Try to import lib.config after adding to path
    try:
        from lib.config import load_strategy_params
        _has_lib_config = True
    except ImportError:
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


def _calculate_required_warmup(params: dict) -> int:
    """
    Dynamically calculate required warmup days from strategy parameters.

    Finds the maximum of all indicator period parameters to ensure
    sufficient data for indicator initialization.

    Args:
        params: Strategy parameters dictionary

    Returns:
        int: Required warmup days
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

    return max(period_values) if period_values else 30


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
            prices = data.history(context.asset, 'price', vol_lookback + 1, '1d')
            if len(prices) < vol_lookback + 1:
                return max_position

            returns = prices.pct_change().dropna()
            if len(returns) < vol_lookback:
                return max_position

            # Annualized volatility (252 trading days default)
            asset_class = params.get('strategy', {}).get('asset_class', 'equities')
            trading_days = {'equities': 252, 'forex': 260, 'crypto': 365}.get(asset_class, 252)
            current_vol = returns.std() * np.sqrt(trading_days)

            if current_vol > 0:
                # Scale position to target volatility
                size = vol_target / current_vol
                return float(np.clip(size, min_position, max_position))

            return max_position
        except Exception:
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
        import warnings
        warnings.warn(
            f"Asset symbol '{asset_symbol}' appears to be a placeholder. "
            "Please update strategy.asset_symbol in parameters.yaml with your actual trading symbol."
        )
    
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop tracking (initialized here)
    context.day_count = 0  # For explicit warmup tracking
    
    # Set benchmark
    set_benchmark(context.asset)

    # Attach Pipeline only if use_pipeline is enabled (and Pipeline is available)
    context.pipeline_data = None
    context.pipeline_universe = []
    context.use_pipeline = params.get('strategy', {}).get('use_pipeline', False)
    
    # Validate pipeline configuration
    asset_class = params.get('strategy', {}).get('asset_class', 'equities')
    if context.use_pipeline:
        if not _PIPELINE_AVAILABLE:
            import warnings
            warnings.warn(
                "Pipeline API not available in this Zipline version. "
                "Setting use_pipeline to False. Pipeline is primarily designed for US equities."
            )
            context.use_pipeline = False
        elif asset_class != 'equities':
            import warnings
            warnings.warn(
                f"Pipeline API is primarily designed for US equities, but asset_class is '{asset_class}'. "
                "Consider setting use_pipeline: false for crypto/forex strategies."
            )
    
    if context.use_pipeline and _PIPELINE_AVAILABLE:
        pipeline = make_pipeline()
        if pipeline is not None:
            attach_pipeline(pipeline, 'my_pipeline')
    
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
        import warnings
        warnings.warn(
            f"Invalid rebalance_frequency '{rebalance_frequency}'. "
            f"Must be one of: {valid_frequencies}. Defaulting to 'daily'."
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
    schedule_function(
        before_trading_start,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=0)
    )


def make_pipeline():
    """Create Pipeline with generic pricing data."""
    if not _PIPELINE_AVAILABLE or _PRICING_CLASS is None:
        return None
    sma_30 = SimpleMovingAverage(inputs=[_PRICING_CLASS.close], window_length=30)
    return Pipeline(columns={'sma_30': sma_30}, screen=sma_30.isfinite())

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
        except Exception:
            context.pipeline_data = None
            context.pipeline_universe = []

def compute_signals(context, data):
    """
    Compute trading signals based on your strategy logic.
    
    This is where you implement your trading hypothesis.
    
    Args:
        context: Zipline context object
        data: Zipline data object
        
    Returns:
        signal: 1 for buy, -1 for sell, 0 for hold
        additional_data: dict of values to record
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
    try:
        prices = data.history(context.asset, 'price', lookback, '1d')
        if len(prices) >= lookback:
            sma = prices.mean()
            if current_price > sma * 1.02:  # 2% above SMA
                signal = 1
            elif current_price < sma * 0.98:  # 2% below SMA
                signal = -1
            additional_data['sma'] = sma
    except Exception:
        # If history fails, return neutral signal
        pass

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
        position_size = compute_position_size(context, data)
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

    Supports:
    - Fixed stop: exits when price drops below entry_price * (1 - stop_loss_pct)
    - Trailing stop: exits when price drops below highest_price * (1 - trailing_stop_pct)
    - Take profit: exits when price rises above entry_price * (1 + take_profit_pct)

    Called separately from rebalance to check stops more frequently.
    """
    if not context.in_position:
        return

    if not data.can_trade(context.asset):
        return

    current_price = data.current(context.asset, 'price')
    risk_params = context.params.get('risk', {})

    # Update highest price for trailing stop tracking
    if context.highest_price > 0:
        context.highest_price = max(context.highest_price, current_price)
    else:
        # Initialize if not set (shouldn't happen, but defensive)
        context.highest_price = current_price

    should_exit = False
    exit_type = None

    # Check take profit first (highest priority - lock in gains)
    if risk_params.get('use_take_profit', False):
        take_profit_pct = risk_params.get('take_profit_pct', 0.10)
        if context.entry_price > 0:
            profit_price = context.entry_price * (1 + take_profit_pct)
            if current_price >= profit_price:
                should_exit = True
                exit_type = 'take_profit'

    # Check trailing stop (takes precedence over fixed stop if both enabled)
    if not should_exit and risk_params.get('use_trailing_stop', False):
        trailing_stop_pct = risk_params.get('trailing_stop_pct', 0.08)
        if context.highest_price > 0:
            stop_price = context.highest_price * (1 - trailing_stop_pct)
            if current_price <= stop_price:
                should_exit = True
                exit_type = 'trailing'

    # Check fixed stop if trailing not triggered
    if not should_exit and risk_params.get('use_stop_loss', False):
        stop_loss_pct = risk_params.get('stop_loss_pct', 0.05)
        if context.entry_price > 0:
            stop_price = context.entry_price * (1 - stop_loss_pct)
            if current_price <= stop_price:
                should_exit = True
                exit_type = 'fixed'

    if should_exit:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        # Record exit type as numeric hash for charting
        exit_type_map = {'fixed': 1, 'trailing': 2, 'take_profit': 3}
        record(
            stop_triggered=1 if exit_type != 'take_profit' else 0,
            take_profit_triggered=1 if exit_type == 'take_profit' else 0,
            exit_type=exit_type_map.get(exit_type, 0)
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

    Args:
        context: Zipline context object
        perf: Performance DataFrame with returns, positions, etc.
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
    returns = perf['returns'].dropna()
    total_return = (1 + returns).prod() - 1
    final_value = perf['portfolio_value'].iloc[-1]

    # Use empyrical for consistent Sharpe/Sortino calculation (matches lib/metrics.py)
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

