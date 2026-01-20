# RSI Mean Reversion Strategy Template
# ==============================================================================
# A mean reversion strategy using RSI with multiple entry/exit levels,
# position scaling, and adaptive parameters.
#
# STRATEGY LOGIC:
# - BUY when RSI drops below oversold threshold (mean reversion entry)
# - SELL when RSI rises above overbought threshold or hits target
# - Optional: Scale into positions at multiple RSI levels
# ==============================================================================

from zipline.api import (
    symbol, symbols, order_target_percent, order_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd


# ==============================================================================
# [PLACEHOLDERS] - CONFIGURE THESE PARAMETERS
# ==============================================================================

# Asset Configuration
ASSET_SYMBOL = 'QQQ'              # [PLACEHOLDER] Asset to trade

# RSI Parameters
RSI_PERIOD = 14                   # [PLACEHOLDER] RSI calculation period (7-21)
RSI_OVERSOLD = 30                 # [PLACEHOLDER] Oversold threshold (20-35)
RSI_OVERBOUGHT = 70               # [PLACEHOLDER] Overbought threshold (65-80)
RSI_EXTREME_OVERSOLD = 20         # [PLACEHOLDER] Extreme oversold for scaling (10-25)
RSI_EXIT_THRESHOLD = 50           # [PLACEHOLDER] RSI level to exit (45-55)

# Position Sizing
BASE_POSITION_SIZE = 0.50         # [PLACEHOLDER] Base position allocation (0.25-0.75)
MAX_POSITION_SIZE = 1.0           # [PLACEHOLDER] Maximum total allocation (0.5-1.0)
SCALE_IN_ENABLED = True           # [PLACEHOLDER] Enable position scaling
SCALE_IN_SIZE = 0.25              # [PLACEHOLDER] Additional size per scale (0.1-0.5)
MAX_SCALE_INS = 2                 # [PLACEHOLDER] Maximum number of scale-ins (1-3)

# Mean Reversion Settings
USE_PRICE_CONFIRMATION = True     # [PLACEHOLDER] Require price below SMA
CONFIRMATION_SMA_PERIOD = 20      # [PLACEHOLDER] SMA period for confirmation
MIN_HOLDING_DAYS = 1              # [PLACEHOLDER] Minimum days before exit (1-5)
MAX_HOLDING_DAYS = 20             # [PLACEHOLDER] Force exit after N days (10-30)

# Risk Management
USE_STOP_LOSS = True              # [PLACEHOLDER] Enable stop loss
STOP_LOSS_PCT = 0.07              # [PLACEHOLDER] Stop loss from entry (0.03-0.10)
USE_PROFIT_TARGET = True          # [PLACEHOLDER] Enable profit target
PROFIT_TARGET_PCT = 0.10          # [PLACEHOLDER] Profit target (0.05-0.15)

# Execution Settings
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open (0-60)

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
MIN_TRADE_COST = 1.0              # [PLACEHOLDER] Minimum per trade
SLIPPAGE_BPS = 5.0                # [PLACEHOLDER] Slippage in basis points


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Set up the strategy."""
    
    context.asset = symbol(ASSET_SYMBOL)
    
    # Position tracking
    context.position_level = 0        # 0 = no position, 1+ = position level
    context.entry_price = 0.0
    context.entry_date = None
    context.scale_in_count = 0
    context.days_held = 0
    
    # Set benchmark
    set_benchmark(context.asset)
    
    # Set commission model
    set_commission(
        us_equities=commission.PerShare(
            cost=COMMISSION_PER_SHARE,
            min_trade_cost=MIN_TRADE_COST
        )
    )
    
    # Set slippage model
    set_slippage(
        us_equities=slippage.FixedBasisPointsSlippage(
            basis_points=SLIPPAGE_BPS,
            volume_limit=0.1
        )
    )
    
    # Schedule main logic
    schedule_function(
        check_signals,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=REBALANCE_TIME)
    )
    
    # Schedule daily position check
    schedule_function(
        manage_position,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=REBALANCE_TIME + 5)
    )


def compute_rsi(prices, period):
    """Calculate RSI from price series."""
    
    deltas = prices.diff()
    
    gains = deltas.where(deltas > 0, 0.0)
    losses = (-deltas).where(deltas < 0, 0.0)
    
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def check_signals(context, data):
    """Check for entry and exit signals."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get price history
    lookback = max(RSI_PERIOD + 5, CONFIRMATION_SMA_PERIOD + 5)
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    # Calculate RSI
    rsi_series = compute_rsi(prices, RSI_PERIOD)
    current_rsi = rsi_series.iloc[-1]
    
    # Price confirmation
    current_price = prices.iloc[-1]
    sma = prices[-CONFIRMATION_SMA_PERIOD:].mean()
    price_below_sma = current_price < sma
    
    # Record metrics
    record(
        rsi=current_rsi,
        price=current_price,
        sma=sma,
        position_level=context.position_level
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Entry Logic
    if context.position_level == 0:
        # Initial entry on oversold
        should_enter = current_rsi < RSI_OVERSOLD
        
        if USE_PRICE_CONFIRMATION:
            should_enter = should_enter and price_below_sma
        
        if should_enter:
            order_target_percent(context.asset, BASE_POSITION_SIZE)
            context.position_level = 1
            context.entry_price = current_price
            context.entry_date = data.current_dt
            context.scale_in_count = 0
            context.days_held = 0
            record(entry_signal=1)
            return
    
    # Scale-in Logic
    elif context.position_level > 0 and SCALE_IN_ENABLED:
        if context.scale_in_count < MAX_SCALE_INS:
            # Scale in on extreme oversold
            if current_rsi < RSI_EXTREME_OVERSOLD:
                new_size = BASE_POSITION_SIZE + (SCALE_IN_SIZE * (context.scale_in_count + 1))
                new_size = min(new_size, MAX_POSITION_SIZE)
                
                order_target_percent(context.asset, new_size)
                context.scale_in_count += 1
                context.entry_price = (context.entry_price + current_price) / 2  # Average
                record(scale_in=1)
                return
    
    record(entry_signal=0, scale_in=0)


def manage_position(context, data):
    """Manage existing positions - exits, stops, targets."""
    
    if context.position_level == 0:
        return
    
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    context.days_held += 1
    
    # Get current RSI
    prices = data.history(context.asset, 'price', RSI_PERIOD + 5, '1d')
    rsi_series = compute_rsi(prices, RSI_PERIOD)
    current_rsi = rsi_series.iloc[-1]
    
    # Calculate PnL
    pnl_pct = (current_price - context.entry_price) / context.entry_price
    
    should_exit = False
    exit_reason = ""
    
    # Check minimum holding period
    if context.days_held < MIN_HOLDING_DAYS:
        # Only exit on stop loss during min hold
        if USE_STOP_LOSS and pnl_pct <= -STOP_LOSS_PCT:
            should_exit = True
            exit_reason = "stop_loss"
    else:
        # RSI exit - reversion complete
        if current_rsi >= RSI_EXIT_THRESHOLD:
            should_exit = True
            exit_reason = "rsi_exit"
        
        # Overbought exit
        if current_rsi >= RSI_OVERBOUGHT:
            should_exit = True
            exit_reason = "overbought"
        
        # Profit target
        if USE_PROFIT_TARGET and pnl_pct >= PROFIT_TARGET_PCT:
            should_exit = True
            exit_reason = "profit_target"
        
        # Stop loss
        if USE_STOP_LOSS and pnl_pct <= -STOP_LOSS_PCT:
            should_exit = True
            exit_reason = "stop_loss"
        
        # Max holding period
        if context.days_held >= MAX_HOLDING_DAYS:
            should_exit = True
            exit_reason = "max_holding"
    
    if should_exit:
        order_target_percent(context.asset, 0)
        context.position_level = 0
        context.entry_price = 0.0
        context.entry_date = None
        context.scale_in_count = 0
        context.days_held = 0
        
        record(exit_signal=1, exit_reason_rsi=(exit_reason == "rsi_exit"))
    else:
        record(exit_signal=0, exit_reason_rsi=0)


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 60)
    print("RSI MEAN REVERSION STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {ASSET_SYMBOL}")
    print(f"RSI Period: {RSI_PERIOD}")
    print(f"Oversold: {RSI_OVERSOLD}, Overbought: {RSI_OVERBOUGHT}")
    print(f"Total Return: {perf['returns'].sum():.2%}")
    print(f"Final Portfolio Value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    
    returns = perf['returns']
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    # Win rate estimation from recorded signals
    if 'exit_signal' in perf.columns:
        trades = perf['exit_signal'].sum()
        print(f"Approximate Trades: {int(trades)}")
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
