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
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.day_count = 0  # For explicit warmup tracking
    
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
    rebalance_frequency = params['strategy'].get('rebalance_frequency', 'daily')
    
    if rebalance_frequency == 'daily':
        schedule_function(
            rebalance,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=params['strategy'].get('minutes_after_open', 30))
        )
    elif rebalance_frequency == 'weekly':
        schedule_function(
            rebalance,
            date_rule=date_rules.week_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=params['strategy'].get('minutes_after_open', 30))
        )
    elif rebalance_frequency == 'monthly':
        schedule_function(
            rebalance,
            date_rule=date_rules.month_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=params['strategy'].get('minutes_after_open', 30))
        )
    
    # Schedule risk management checks if enabled
    if params.get('risk', {}).get('use_stop_loss', False) or params.get('risk', {}).get('use_trailing_stop', False):
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
    # TODO: Implement your strategy logic here, utilizing pipeline data
    # Example structure:
    # 1. Get pipeline data for universe/factors
    # 2. Filter/select assets based on pipeline output
    # 3. Generate signal based on conditions
    # 4. Return signal and any metrics to record
    
    signal = 0
    additional_data = {}

    # Example: Use pipeline data for a simple signal
    if context.asset in context.pipeline_universe:
        sma_value = context.pipeline_data.loc[context.asset]['sma_30']
        current_price = data.current(context.asset, 'price')

        if current_price > sma_value:
            signal = 1  # Buy if current price is above SMA_30
        elif current_price < sma_value:
            signal = -1  # Sell if current price is below SMA_30
        
        additional_data['sma_30'] = sma_value

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

    elif signal == -1 and context.in_position:
        # Exit position
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0


def check_stop_loss(context, data):
    """
    Check and execute stop loss orders.
    
    Called separately from rebalance to check stops more frequently.
    """
    if not context.in_position:
        return
    
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    risk_params = context.params.get('risk', {})
    
    if risk_params.get('use_stop_loss', False):
        stop_loss_pct = risk_params.get('stop_loss_pct', 0.05)
        stop_price = context.entry_price * (1 - stop_loss_pct)
        
        if current_price <= stop_price:
            order_target_percent(context.asset, 0)
            context.in_position = False
            context.entry_price = 0.0
            record(stop_triggered=1)
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
    print(f"STRATEGY RESULTS: {asset_symbol}")
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
        sharpe = float(ep.sharpe_ratio(returns, risk_free=0.04/252, period='daily', annualization=252))
        max_dd = float(ep.max_drawdown(returns))
        # Validate Sharpe ratio
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

