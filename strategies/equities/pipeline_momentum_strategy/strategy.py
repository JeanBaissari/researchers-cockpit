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
    attach_pipeline, pipeline_output
)
from zipline.pipeline import Pipeline
from zipline.pipeline.data import USEquityPricing
from zipline.pipeline.factors import SimpleMovingAverage, Returns
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for lib imports
# This allows strategies to import lib modules
_project_root = Path(__file__).parent.parent.parent
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
    
    # Get data frequency from parameters, default to 'daily'
    context.data_frequency = params.get('backtest', {}).get('data_frequency', 'daily')

    # Get asset symbol from parameters
    asset_symbol = params['strategy']['asset_symbol']
    context.asset = symbol(asset_symbol)
    
    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0
    
    # Set benchmark
    set_benchmark(context.asset)

    # Attach Pipeline
    attach_pipeline(make_pipeline(), 'my_pipeline')
    context.pipeline_data = None
    context.pipeline_universe = []
    
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


def make_pipeline():
    """
    Create Zipline Pipeline for factor computation and universe selection.
    
    Returns:
        Pipeline: Zipline Pipeline object
    """
    # Define pipeline factors
    # 10-day momentum factor
    momentum_10 = Returns(window_length=10)
    # 30-day momentum factor
    momentum_30 = Returns(window_length=30)

    return Pipeline(
        columns={
            'momentum_10': momentum_10,
            'momentum_30': momentum_30,
        },
        screen=momentum_10.isfinite() & momentum_30.isfinite(), # Only consider assets with valid momentum
    )

def before_trading_start(context, data):
    """
    Called once per day before market open.
    
    Use this to fetch pipeline output and update context.
    """
    context.pipeline_data = pipeline_output('my_pipeline')
    
    # Example: Store the list of assets in our universe
    context.pipeline_universe = context.pipeline_data.index.tolist()

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
    signal = 0
    additional_data = {}

    # Get parameters
    long_period = context.params['strategy']['long_period']
    short_period = context.params['strategy']['short_period']

    # Check if the asset is in our pipeline universe
    if context.asset in context.pipeline_universe:
        # Get momentum values from pipeline data
        momentum_10 = context.pipeline_data.loc[context.asset]['momentum_10']
        momentum_30 = context.pipeline_data.loc[context.asset]['momentum_30']

        # Simple momentum strategy: Buy if short-term momentum > long-term momentum
        # Sell if short-term momentum < long-term momentum
        if momentum_10 > momentum_30:
            signal = 1  # Buy
        elif momentum_10 < momentum_30:
            signal = -1 # Sell
        
        additional_data['momentum_10'] = momentum_10
        additional_data['momentum_30'] = momentum_30

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
    
    # Record metrics
    record(
        signal=signal,
        price=current_price,
        **additional_data
    )
    
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
    
    print("n" + "=" * 60)
    print(f"STRATEGY RESULTS: {asset_symbol}")
    print("=" * 60)
    
    # Calculate basic metrics
    returns = perf['returns']
    total_return = perf['returns'].sum()
    final_value = perf['portfolio_value'].iloc[-1]
    
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
    
    # TODO: Add more detailed analysis here
    # - Trade statistics
    # - Win rate
    # - Average trade duration
    # - Regime breakdown
    # etc.

