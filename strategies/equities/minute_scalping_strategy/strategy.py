from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
import sys

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
        raise FileNotFoundError(
            f"parameters.yaml not found at {params_path}. "
            "Every strategy must have a parameters.yaml file."
        )
    
    with open(params_path) as f:
        return yaml.safe_load(f)

def initialize(context):
    params = load_params()
    context.params = params
    context.asset = symbol(params['strategy']['asset'])
    context.rsi_period = params['strategy']['rsi_period']
    context.rsi_oversold = params['strategy']['rsi_oversold']
    context.rsi_overbought = params['strategy']['rsi_overbought']
    context.data_frequency = params['backtest'].get('data_frequency', 'minute')

    set_benchmark(None) # No benchmark for scalping usually
    
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.001),
            min_trade_cost=commission_config.get('min_cost', 0.10)
        )
    )
    
    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.01),
            price_impact=slippage_config.get('price_impact', 0.05)
        )
    )

    context.has_position = False
    schedule_function(handle_data, date_rules.every_day(), time_rules.every_minute())

def handle_data(context, data):
    price_history = data.history(context.asset, 'price', context.rsi_period + 1, '1m')
    if len(price_history) < context.rsi_period + 1:
        return

    delta = price_history.diff()
    gain = delta.where(delta > 0, 0).rolling(window=context.rsi_period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=context.rsi_period).mean()

    # Avoid division by zero for rs
    if loss.iloc[-1] == 0:
        rsi = 100.0  # If no losses, RSI is 100
    else:
        rs = gain.iloc[-1] / loss.iloc[-1]
        rsi = 100 - (100 / (1 + rs))

    current_price = data.current(context.asset, 'price')

    record(price=current_price, rsi=rsi)

    if current_price and data.can_trade(context.asset):
        if rsi < context.rsi_oversold and not context.has_position:
            order_target_percent(context.asset, 0.99)
            context.has_position = True
        elif rsi > context.rsi_overbought and context.has_position:
            order_target_percent(context.asset, 0)
            context.has_position = False

def analyze(context, perf):
    params = load_params()
    asset_symbol = params['strategy']['asset']
    
    print("\n" + "=" * 60)
    print(f"STRATEGY RESULTS: {asset_symbol}")
    print("=" * 60)
    
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

