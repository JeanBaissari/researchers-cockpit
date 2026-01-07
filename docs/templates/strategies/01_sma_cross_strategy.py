# SMA Cross Strategy Template
# ==============================================================================
# A classic dual moving average crossover strategy with configurable parameters,
# position sizing, and risk management.
#
# STRATEGY LOGIC:
# - BUY when fast SMA crosses above slow SMA (golden cross)
# - SELL when fast SMA crosses below slow SMA (death cross)
# - Optional: Only trade when price is above/below a trend filter SMA
#
# CRITICAL RULES:
# - NO hardcoded parameters in this file - all params come from parameters.yaml
# - Every strategy MUST have a hypothesis.md file
# - Use lib/config.py to load parameters
# ==============================================================================

from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Optional Pipeline support
try:
    from zipline.pipeline import Pipeline, CustomFactor
    from zipline.pipeline.data import EquityPricing
    from zipline.pipeline.factors import SimpleMovingAverage, AverageDollarVolume
    from zipline.api import attach_pipeline, pipeline_output
    _PIPELINE_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older Zipline versions
        from zipline.pipeline import Pipeline, CustomFactor
        from zipline.pipeline.data import USEquityPricing as EquityPricing
        from zipline.pipeline.factors import SimpleMovingAverage, AverageDollarVolume
        from zipline.api import attach_pipeline, pipeline_output
        _PIPELINE_AVAILABLE = True
    except ImportError:
        _PIPELINE_AVAILABLE = False


# ==============================================================================
# PROJECT ROOT DISCOVERY
# ==============================================================================

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


# ==============================================================================
# PARAMETER LOADING
# ==============================================================================

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
        # Extract strategy name from path
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


# ==============================================================================
# WARMUP CALCULATION
# ==============================================================================

def _calculate_required_warmup(params: dict) -> int:
    """
    Calculate required warmup days based on strategy indicator periods.
    
    Finds the maximum of all indicator periods and adds a buffer to ensure
    sufficient data for indicator initialization and crossover detection.
    
    Args:
        params: Strategy parameters dictionary
    
    Returns:
        int: Required warmup days (max period + buffer)
    """
    strategy_config = params.get('strategy', {})
    
    # Collect all relevant period parameters
    # Generic detection: look for any key ending in '_period'
    periods = []
    
    for key, value in strategy_config.items():
        if key.endswith('_period') and isinstance(value, (int, float)) and value > 0:
            periods.append(int(value))
    
    # Volatility lookback for position sizing
    position_sizing = params.get('position_sizing', {})
    vol_lookback = position_sizing.get('volatility_lookback', 20)
    if position_sizing.get('method') == 'volatility_scaled':
        periods.append(vol_lookback)
    
    # Calculate max period and add buffer
    # Buffer of 10 days ensures we have enough data for crossover detection
    # and handles any edge cases with data availability
    max_period = max(periods) if periods else 30
    buffer = 10
    
    return max_period + buffer


# ==============================================================================
# PIPELINE SUPPORT (Optional)
# ==============================================================================

def make_pipeline(params=None):
    """
    Create a pipeline for universe selection and factor computation.
    
    This is a stub implementation. Override or extend for strategies
    that need pipeline-based universe selection or pre-computed factors.
    
    Args:
        params: Strategy parameters dictionary (optional)
    
    Returns:
        Pipeline: Configured pipeline instance, or None if pipeline not available
    """
    if not _PIPELINE_AVAILABLE:
        return None
    
    if params is None:
        params = load_params()
    
    strategy_params = params.get('strategy', {})
    fast_period = strategy_params.get('fast_sma_period', 10)
    slow_period = strategy_params.get('slow_sma_period', 30)
    
    # Example pipeline with SMA factors
    # Customize this for your strategy's needs
    return Pipeline(
        columns={
            'fast_sma': SimpleMovingAverage(
                inputs=[EquityPricing.close],
                window_length=fast_period
            ),
            'slow_sma': SimpleMovingAverage(
                inputs=[EquityPricing.close],
                window_length=slow_period
            ),
            'dollar_volume': AverageDollarVolume(window_length=20),
        },
        # No screen by default - single asset strategy
        # Add screen for universe selection in multi-asset strategies
    )


def before_trading_start(context, data):
    """
    Called before market open each day.
    
    Used to fetch pipeline output and prepare for trading.
    Override this function to add custom pre-trading logic.
    
    Note: This function is scheduled in initialize() to ensure it runs
    on all Zipline versions.
    
    Args:
        context: Zipline context object
        data: Zipline data object
    """
    # Fetch pipeline output if pipeline is attached
    if _PIPELINE_AVAILABLE and getattr(context, 'pipeline_attached', False):
        try:
            context.pipeline_output = pipeline_output('my_pipeline')
        except Exception:
            # Pipeline may not be attached or may have failed
            context.pipeline_output = None
    else:
        context.pipeline_output = None


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Set up the strategy."""
    
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
    
    # Get asset symbol from parameters with defensive access
    strategy_params = params.get('strategy', {})
    asset_symbol = strategy_params.get('asset_symbol')
    if asset_symbol is None:
        raise ValueError(
            "Missing 'asset_symbol' in strategy parameters. "
            "Please specify strategy.asset_symbol in parameters.yaml"
        )
    context.asset = symbol(asset_symbol)
    
    # Strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop
    context.day_count = 0  # Track days for warmup
    
    # Set benchmark
    set_benchmark(context.asset)
    
    # Optionally attach pipeline
    context.pipeline_attached = False
    if _PIPELINE_AVAILABLE and params.get('strategy', {}).get('use_pipeline', False):
        pipeline = make_pipeline(params)
        if pipeline is not None:
            attach_pipeline(pipeline, 'my_pipeline')
            context.pipeline_attached = True
    
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
    
    # Schedule before_trading_start to ensure it runs on all Zipline versions
    schedule_function(
        before_trading_start,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=0)
    )
    
    # Schedule rebalancing
    rebalance_frequency = strategy_params.get('rebalance_frequency', 'daily')
    minutes_after_open = strategy_params.get('minutes_after_open', 30)
    
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
    
    # Schedule stop loss check if enabled
    risk_params = params.get('risk', {})
    if risk_params.get('use_stop_loss', False) or risk_params.get('use_trailing_stop', False):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )


def compute_signals(context, data):
    """
    Compute trading signals.
    
    Returns:
        tuple: (signal, signal_data) where signal is -1/0/1 and signal_data
               is a dict containing additional signal information
    """
    
    # Get parameters from context
    strategy_params = context.params.get('strategy', {})
    fast_period = strategy_params.get('fast_sma_period', 10)
    slow_period = strategy_params.get('slow_sma_period', 30)
    trend_filter_period = strategy_params.get('trend_filter_period', 0)
    
    # Need enough history for slow SMA
    lookback = max(slow_period, trend_filter_period) + 5
    
    if not data.can_trade(context.asset):
        return None, {}
    
    # Get price history
    try:
        prices = data.history(context.asset, 'price', lookback, '1d')
    except Exception:
        return None, {}
    
    if len(prices) < lookback:
        return None, {}
    
    # Drop any NaN values
    prices = prices.dropna()
    if len(prices) < slow_period + 1:
        return None, {}
    
    # Calculate SMAs
    fast_sma = prices[-fast_period:].mean()
    slow_sma = prices[-slow_period:].mean()
    
    # Previous SMAs for crossover detection
    fast_sma_prev = prices[-(fast_period + 1):-1].mean()
    slow_sma_prev = prices[-(slow_period + 1):-1].mean()
    
    # Trend filter
    trend_bullish = True
    trend_sma = None
    if trend_filter_period > 0 and len(prices) >= trend_filter_period:
        trend_sma = prices[-trend_filter_period:].mean()
        trend_bullish = prices.iloc[-1] > trend_sma
    
    # Detect crossovers
    golden_cross = (fast_sma > slow_sma) and (fast_sma_prev <= slow_sma_prev)
    death_cross = (fast_sma < slow_sma) and (fast_sma_prev >= slow_sma_prev)
    
    # Generate signals
    signal = 0
    if golden_cross and trend_bullish:
        signal = 1  # Buy
    elif death_cross:
        signal = -1  # Sell
    
    # Return standardized format: (signal, data_dict)
    signal_data = {
        'fast_sma': fast_sma,
        'slow_sma': slow_sma,
        'trend_sma': trend_sma,
        'golden_cross': golden_cross,
        'death_cross': death_cross,
        'trend_bullish': trend_bullish,
    }
    
    return signal, signal_data


def compute_position_size(context, data):
    """Calculate position size based on method."""
    
    position_sizing = context.params.get('position_sizing', {})
    method = position_sizing.get('method', 'fixed')
    max_position = position_sizing.get('max_position_pct', 0.95)
    
    if method == 'fixed':
        return max_position
    
    elif method == 'volatility_scaled':
        vol_lookback = position_sizing.get('volatility_lookback', 20)
        vol_target = position_sizing.get('volatility_target', 0.15)
        
        try:
            prices = data.history(context.asset, 'price', vol_lookback + 1, '1d')
        except Exception:
            return max_position
            
        returns = prices.pct_change().dropna()
        
        if len(returns) < vol_lookback:
            return max_position
        
        # Annualized volatility
        current_vol = returns.std() * np.sqrt(252)
        
        if current_vol > 0:
            # Scale position to target volatility
            size = vol_target / current_vol
            return min(size, max_position)
        
        return max_position
    
    return max_position


def rebalance(context, data):
    """Main rebalancing logic."""
    
    # Increment day count
    context.day_count += 1
    
    # Skip during warmup period
    if context.day_count < context.required_warmup_days:
        return
    
    # Check if asset is tradeable before proceeding
    if not data.can_trade(context.asset):
        return
    
    signal, signal_data = compute_signals(context, data)
    
    if signal is None:
        return
    
    try:
        current_price = data.current(context.asset, 'price')
    except Exception:
        return
    
    # Record metrics
    record(
        fast_sma=signal_data.get('fast_sma'),
        slow_sma=signal_data.get('slow_sma'),
        signal=signal,
        price=current_price
    )
    
    # Cancel any open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Execute signals
    if signal == 1 and not context.in_position:
        # Enter long position
        position_size = compute_position_size(context, data)
        order_target_percent(context.asset, position_size)
        
        context.in_position = True
        context.entry_price = current_price
        context.highest_price = current_price
        
    elif signal == -1 and context.in_position:
        # Exit position
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0


def check_stop_loss(context, data):
    """Check and execute stop loss orders."""
    
    if not context.in_position:
        return
    
    if not data.can_trade(context.asset):
        return
    
    try:
        current_price = data.current(context.asset, 'price')
    except Exception:
        return
    
    # Update highest price for trailing stop
    context.highest_price = max(context.highest_price, current_price)
    
    risk_params = context.params.get('risk', {})
    use_trailing_stop = risk_params.get('use_trailing_stop', False)
    use_stop_loss = risk_params.get('use_stop_loss', False)
    
    should_stop = False
    
    if use_trailing_stop:
        # Trailing stop from highest price
        trailing_stop_pct = risk_params.get('trailing_stop_pct', 0.08)
        stop_price = context.highest_price * (1 - trailing_stop_pct)
        should_stop = current_price <= stop_price
    elif use_stop_loss:
        # Fixed stop from entry
        stop_loss_pct = risk_params.get('stop_loss_pct', 0.05)
        stop_price = context.entry_price * (1 - stop_loss_pct)
        should_stop = current_price <= stop_price
    
    if should_stop:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        record(stop_triggered=1)
    else:
        record(stop_triggered=0)


def handle_data(context, data):
    """Called every bar - used for recording only."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    # Use context.params if available, otherwise reload from YAML
    params = getattr(context, 'params', None) or load_params()
    strategy_params = params.get('strategy', {})
    asset_symbol = strategy_params.get('asset_symbol', 'UNKNOWN')
    fast_period = strategy_params.get('fast_sma_period', 10)
    slow_period = strategy_params.get('slow_sma_period', 30)
    
    print("\n" + "=" * 60)
    print("SMA CROSS STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {asset_symbol}")
    print(f"Fast SMA: {fast_period}, Slow SMA: {slow_period}")
    
    # Calculate basic metrics
    returns = perf['returns'].dropna()
    total_return = (1 + returns).prod() - 1
    final_value = perf['portfolio_value'].iloc[-1]
    
    # Use empyrical for consistent metrics calculation
    try:
        import empyrical as ep
        
        # Get risk-free rate from params, default to 4% annual
        risk_free_annual = params.get('backtest', {}).get('risk_free_rate', 0.04)
        risk_free_daily = risk_free_annual / 252
        
        sharpe = float(ep.sharpe_ratio(
            returns, 
            risk_free=risk_free_daily, 
            period='daily', 
            annualization=252
        ))
        max_dd = float(ep.max_drawdown(returns))
        
        # Validate Sharpe ratio (handle NaN/Inf)
        if not np.isfinite(sharpe):
            sharpe = 0.0
            
    except ImportError:
        # Fallback if empyrical not available
        if len(returns) > 0 and returns.std() > 0:
            sharpe = np.sqrt(252) * returns.mean() / returns.std()
        else:
            sharpe = 0.0
        cumulative = (1 + returns).cumprod()
        max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
