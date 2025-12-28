"""
Simple Crypto Strategy - SMA Crossover
==============================================================================
A simple moving average crossover strategy for cryptocurrency trading.

This strategy:
- Uses fast/slow SMA crossover for entry/exit signals
- Operates on 24/7 CRYPTO calendar
- Uses Yahoo Finance BTC-USD data
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

# Add project root to path for lib imports
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from lib.config import load_strategy_params
    _has_lib_config = True
except ImportError:
    import yaml
    _has_lib_config = False


def load_params():
    """Load parameters from parameters.yaml file."""
    if _has_lib_config:
        strategy_path = Path(__file__).parent
        strategy_name = strategy_path.name
        asset_class = strategy_path.parent.name
        if asset_class == 'strategies':
            asset_class = None
        try:
            return load_strategy_params(strategy_name, asset_class)
        except Exception:
            pass

    import yaml
    params_path = Path(__file__).parent / 'parameters.yaml'
    if not params_path.exists():
        raise FileNotFoundError(f"parameters.yaml not found at {params_path}")
    with open(params_path) as f:
        return yaml.safe_load(f)


def initialize(context):
    """Set up the strategy."""
    params = load_params()
    context.params = params

    # Get asset symbol from parameters
    asset_symbol = params['strategy']['asset_symbol']
    context.asset = symbol(asset_symbol)

    # Initialize strategy state
    context.in_position = False
    context.entry_price = 0.0

    # Note: Crypto uses different commission/slippage models
    # For MVP, using simplified flat rate
    set_commission(
        us_equities=commission.PerShare(cost=0.0, min_trade_cost=0.0)
    )
    set_slippage(
        us_equities=slippage.FixedSlippage(spread=0.0)
    )

    # Schedule daily rebalancing
    schedule_function(
        rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )


def compute_signals(context, data):
    """Compute trading signals based on SMA crossover."""
    if not data.can_trade(context.asset):
        return 0, {}

    fast_period = context.params['strategy'].get('short_period', 50)
    slow_period = context.params['strategy'].get('long_period', 200)
    lookback = slow_period + 5

    prices = data.history(context.asset, 'price', lookback, '1d')

    if len(prices) < lookback:
        return 0, {}

    fast_sma = prices[-fast_period:].mean()
    slow_sma = prices[-slow_period:].mean()

    fast_sma_prev = prices[-(fast_period + 1):-1].mean()
    slow_sma_prev = prices[-(slow_period + 1):-1].mean()

    golden_cross = (fast_sma > slow_sma) and (fast_sma_prev <= slow_sma_prev)
    death_cross = (fast_sma < slow_sma) and (fast_sma_prev >= slow_sma_prev)

    signal = 0
    if golden_cross:
        signal = 1
    elif death_cross:
        signal = -1

    additional_data = {
        'fast_sma': fast_sma,
        'slow_sma': slow_sma,
        'price': prices.iloc[-1],
    }

    return signal, additional_data


def rebalance(context, data):
    """Main rebalancing function."""
    signal, additional_data = compute_signals(context, data)

    if signal is None:
        return

    current_price = data.current(context.asset, 'price')

    record(
        signal=signal,
        price=current_price,
        **{k: v for k, v in additional_data.items() if k != 'price'}
    )

    for order in get_open_orders(context.asset):
        cancel_order(order)

    max_position = 0.95

    if signal == 1 and not context.in_position:
        order_target_percent(context.asset, max_position)
        context.in_position = True
        context.entry_price = current_price
    elif signal == -1 and context.in_position:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    params = load_params()
    asset_symbol = params['strategy']['asset_symbol']

    print("\n" + "=" * 60)
    print(f"STRATEGY RESULTS: {asset_symbol}")
    print("=" * 60)

    returns = perf['returns']
    total_return = returns.sum()
    final_value = perf['portfolio_value'].iloc[-1]

    if len(returns) > 0 and returns.std() > 0:
        sharpe = np.sqrt(365) * returns.mean() / returns.std()  # 365 for crypto
    else:
        sharpe = 0.0

    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()

    print(f"Total Return: {total_return:.2%}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
