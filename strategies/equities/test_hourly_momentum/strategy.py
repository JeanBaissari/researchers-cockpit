"""
Test Hourly Momentum Strategy
==============================================================================
A simple SMA crossover strategy to test multi-timeframe data ingestion.

This strategy:
1. Uses hourly data (1h timeframe)
2. Computes fast and slow SMAs
3. Generates buy/sell signals on crossovers

The primary purpose is to validate the multi-timeframe data system.
"""

from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order,
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


_project_root = _find_project_root()
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

    # Get asset symbol
    asset_symbol = params['strategy']['asset_symbol']
    context.asset = symbol(asset_symbol)

    # Strategy parameters
    context.fast_period = params['strategy'].get('fast_period', 5)
    context.slow_period = params['strategy'].get('slow_period', 20)

    # Initialize state
    context.in_position = False
    context.entry_price = 0.0
    context.warmup_complete = False
    context.bar_count = 0

    # Set benchmark
    set_benchmark(context.asset)

    # Configure costs
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )

    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )

    # Schedule trading function
    schedule_function(
        rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )

    # Schedule stop loss check
    if params.get('risk', {}).get('use_stop_loss', False):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )


def compute_signals(context, data):
    """
    Compute SMA crossover signals.

    Returns:
        signal: 1 for buy, -1 for sell, 0 for hold
        additional_data: dict of values to record
    """
    # Need enough data for slow SMA
    lookback = context.slow_period + 5

    # Get price history
    try:
        prices = data.history(context.asset, 'price', lookback, '1d')
    except Exception as e:
        return None, {'error': str(e)}

    if len(prices) < context.slow_period:
        return None, {'warmup': True}

    # Calculate SMAs
    fast_sma = prices.rolling(context.fast_period).mean().iloc[-1]
    slow_sma = prices.rolling(context.slow_period).mean().iloc[-1]

    # Previous SMAs for crossover detection
    fast_sma_prev = prices.rolling(context.fast_period).mean().iloc[-2]
    slow_sma_prev = prices.rolling(context.slow_period).mean().iloc[-2]

    current_price = prices.iloc[-1]

    # Crossover logic
    signal = 0
    if fast_sma_prev <= slow_sma_prev and fast_sma > slow_sma:
        signal = 1  # Golden cross - buy
    elif fast_sma_prev >= slow_sma_prev and fast_sma < slow_sma:
        signal = -1  # Death cross - sell

    additional_data = {
        'fast_sma': fast_sma,
        'slow_sma': slow_sma,
        'price': current_price,
    }

    return signal, additional_data


def rebalance(context, data):
    """Main rebalancing function called on schedule."""
    context.bar_count += 1

    signal, additional_data = compute_signals(context, data)

    if signal is None:
        return

    current_price = data.current(context.asset, 'price')

    # Record metrics
    record(
        signal=signal,
        **additional_data
    )

    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)

    # Execute trades
    max_position = context.params['position_sizing'].get('max_position_pct', 0.95)

    if signal == 1 and not context.in_position:
        order_target_percent(context.asset, max_position)
        context.in_position = True
        context.entry_price = current_price

    elif signal == -1 and context.in_position:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0


def check_stop_loss(context, data):
    """Check and execute stop loss orders."""
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
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    params = load_params()
    asset_symbol = params['strategy']['asset_symbol']

    print("\n" + "=" * 60)
    print(f"TEST HOURLY MOMENTUM RESULTS: {asset_symbol}")
    print("=" * 60)

    # Calculate metrics
    returns = perf['returns'].dropna()
    total_return = (1 + returns).prod() - 1
    final_value = perf['portfolio_value'].iloc[-1]

    try:
        import empyrical as ep
        sharpe = float(ep.sharpe_ratio(returns, risk_free=0.04, period='daily', annualization=252))
        max_dd = float(ep.max_drawdown(returns))
        if not np.isfinite(sharpe):
            sharpe = 0.0
    except ImportError:
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
    print(f"Total Bars Processed: {context.bar_count}")
    print("=" * 60)
