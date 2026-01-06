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
    get_open_orders, cancel_order
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
from pathlib import Path
import sys


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


# Add project root to path for lib imports
# This allows strategies to import lib modules
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
    
    # Get asset symbol from parameters
    asset_symbol = params['strategy']['asset_symbol']
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    
    # Set benchmark
    set_benchmark(context.asset)
    
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
    if params.get('risk', {}).get('use_stop_loss', False):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )


def compute_signals(context, data):
    """
    Compute trading signals based on SMA crossover logic.
    
    SMA Crossover Strategy:
    - Buy (signal=1) when fast SMA crosses above slow SMA (golden cross)
    - Sell (signal=-1) when fast SMA crosses below slow SMA (death cross)
    - Hold (signal=0) otherwise
    
    Args:
        context: Zipline context object
        data: Zipline data object
        
    Returns:
        signal: 1 for buy, -1 for sell, 0 for hold
        additional_data: dict of values to record
    """
    if not data.can_trade(context.asset):
        return 0, {}
    
    # Get parameters
    fast_period = context.params['strategy'].get('fast_period', 10)
    slow_period = context.params['strategy'].get('slow_period', 30)
    
    # Need enough history for slow SMA
    lookback = slow_period + 5
    
    # Get price history
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return 0, {}
    
    # Calculate SMAs
    fast_sma = prices[-fast_period:].mean()
    slow_sma = prices[-slow_period:].mean()
    
    # Previous SMAs for crossover detection
    fast_sma_prev = prices[-(fast_period + 1):-1].mean()
    slow_sma_prev = prices[-(slow_period + 1):-1].mean()
    
    # Detect crossovers
    golden_cross = (fast_sma > slow_sma) and (fast_sma_prev <= slow_sma_prev)
    death_cross = (fast_sma < slow_sma) and (fast_sma_prev >= slow_sma_prev)
    
    # Generate signal
    signal = 0
    if golden_cross:
        signal = 1  # Buy
    elif death_cross:
        signal = -1  # Sell
    
    # Additional data to record
    additional_data = {
        'fast_sma': fast_sma,
        'slow_sma': slow_sma,
        'price': prices.iloc[-1],
    }
    
    return signal, additional_data


def rebalance(context, data):
    """
    Main rebalancing function called on schedule.
    
    This function:
    1. Computes signals
    2. Executes trades
    3. Records metrics
    """
    signal, additional_data = compute_signals(context, data)
    
    if signal is None:
        return
    
    current_price = data.current(context.asset, 'price')
    
    # Record metrics - ensure no duplicate keys
    record_data = {
        'signal': signal,
        'price': current_price,
        **additional_data  # additional_data may contain 'price', so it will override
    }
    # Remove 'price' from additional_data if present to avoid conflicts
    if 'price' in additional_data:
        record_data['price'] = current_price  # Use current_price, not additional_data['price']
    
    record(**record_data)
    
    # Cancel any open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Execute trades based on signal
    max_position = context.params['position_sizing'].get('max_position_pct', 0.95)
    
    if signal == 1 and not context.in_position:
        # Enter position
        order_target_percent(context.asset, max_position)
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
    try:
        import empyrical as ep
        # Equities use 252 trading days per year
        # empyrical expects DAILY risk-free rate: 0.04/252 ≈ 0.000159
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

