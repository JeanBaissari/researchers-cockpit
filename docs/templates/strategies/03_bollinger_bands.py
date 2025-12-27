# Bollinger Bands Strategy Template
# ==============================================================================
# A volatility-based strategy using Bollinger Bands with multiple trading modes:
# mean reversion or breakout, adaptive band width, and %B indicator.
#
# STRATEGY LOGIC:
# - MEAN REVERSION: Buy at lower band, sell at upper band
# - BREAKOUT: Buy on upper band breakout, sell on lower band breakdown
# - Uses %B indicator and bandwidth for signal confirmation
# ==============================================================================

from zipline.api import (
    symbol, symbols, order_target_percent, record,
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
ASSET_SYMBOL = 'IWM'              # [PLACEHOLDER] Asset to trade

# Bollinger Band Parameters
BB_PERIOD = 20                    # [PLACEHOLDER] Lookback period (10-30)
BB_STD_DEV = 2.0                  # [PLACEHOLDER] Standard deviations (1.5-3.0)
BB_STD_DEV_INNER = 1.0            # [PLACEHOLDER] Inner band for targets (0.5-1.5)

# Strategy Mode
STRATEGY_MODE = 'mean_reversion'  # [PLACEHOLDER] 'mean_reversion' or 'breakout'

# Mean Reversion Settings (when STRATEGY_MODE = 'mean_reversion')
MR_ENTRY_THRESHOLD = 0.0          # [PLACEHOLDER] %B threshold to enter (0.0-0.2)
MR_EXIT_THRESHOLD = 0.5           # [PLACEHOLDER] %B threshold to exit (0.4-0.6)
MR_UPPER_EXIT = 1.0               # [PLACEHOLDER] %B threshold for upper exit (0.8-1.0)

# Breakout Settings (when STRATEGY_MODE = 'breakout')
BO_CONFIRMATION_BARS = 2          # [PLACEHOLDER] Bars above/below band to confirm (1-3)
BO_VOLUME_MULTIPLIER = 1.5        # [PLACEHOLDER] Volume spike requirement (1.0-2.0)
BO_USE_VOLUME_CONFIRM = True      # [PLACEHOLDER] Require volume confirmation

# Bandwidth Filter
USE_BANDWIDTH_FILTER = True       # [PLACEHOLDER] Filter by bandwidth
MIN_BANDWIDTH = 0.05              # [PLACEHOLDER] Min bandwidth to trade (0.03-0.10)
MAX_BANDWIDTH = 0.30              # [PLACEHOLDER] Max bandwidth to trade (0.20-0.50)

# Position Sizing
POSITION_SIZE = 0.90              # [PLACEHOLDER] Position allocation (0.5-1.0)
USE_VOLATILITY_SIZING = True      # [PLACEHOLDER] Scale size by volatility
VOLATILITY_TARGET = 0.15          # [PLACEHOLDER] Target annual vol for sizing

# Risk Management
USE_STOP_LOSS = True              # [PLACEHOLDER] Enable stop loss
STOP_LOSS_ATR_MULT = 2.0          # [PLACEHOLDER] ATR multiplier for stop (1.5-3.0)
ATR_PERIOD = 14                   # [PLACEHOLDER] ATR calculation period

# Execution Settings
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open (0-60)

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
SLIPPAGE_VOLUME_LIMIT = 0.025     # [PLACEHOLDER] Max volume participation
SLIPPAGE_PRICE_IMPACT = 0.1       # [PLACEHOLDER] Price impact coefficient


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Set up the strategy."""
    
    context.asset = symbol(ASSET_SYMBOL)
    
    # Position tracking
    context.in_position = False
    context.position_side = 0        # 1 = long, -1 = short, 0 = flat
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.bars_above_upper = 0     # For breakout confirmation
    context.bars_below_lower = 0
    
    # Set benchmark
    set_benchmark(context.asset)
    
    # Set commission model
    set_commission(
        us_equities=commission.PerShare(
            cost=COMMISSION_PER_SHARE,
            min_trade_cost=1.0
        )
    )
    
    # Set slippage model
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=SLIPPAGE_VOLUME_LIMIT,
            price_impact=SLIPPAGE_PRICE_IMPACT
        )
    )
    
    # Schedule main logic
    schedule_function(
        execute_strategy,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=REBALANCE_TIME)
    )
    
    # Schedule stop check
    schedule_function(
        check_stops,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )


def compute_bollinger_bands(prices):
    """Calculate Bollinger Bands and related indicators."""
    
    sma = prices.rolling(window=BB_PERIOD).mean()
    std = prices.rolling(window=BB_PERIOD).std()
    
    upper_band = sma + (BB_STD_DEV * std)
    lower_band = sma - (BB_STD_DEV * std)
    
    # Inner bands for targets
    upper_inner = sma + (BB_STD_DEV_INNER * std)
    lower_inner = sma - (BB_STD_DEV_INNER * std)
    
    # %B indicator: (price - lower) / (upper - lower)
    band_width = upper_band - lower_band
    percent_b = (prices - lower_band) / band_width.replace(0, np.inf)
    
    # Bandwidth: (upper - lower) / middle
    bandwidth = band_width / sma
    
    return {
        'middle': sma,
        'upper': upper_band,
        'lower': lower_band,
        'upper_inner': upper_inner,
        'lower_inner': lower_inner,
        'percent_b': percent_b,
        'bandwidth': bandwidth
    }


def compute_atr(high, low, close, period):
    """Calculate Average True Range."""
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def compute_position_size(context, data, atr):
    """Calculate position size based on volatility."""
    
    if not USE_VOLATILITY_SIZING:
        return POSITION_SIZE
    
    prices = data.history(context.asset, 'price', 21, '1d')
    returns = prices.pct_change().dropna()
    
    current_vol = returns.std() * np.sqrt(252)
    
    if current_vol > 0:
        size = VOLATILITY_TARGET / current_vol
        return min(size, POSITION_SIZE)
    
    return POSITION_SIZE


def execute_strategy(context, data):
    """Main strategy execution."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get price history
    lookback = max(BB_PERIOD + 10, ATR_PERIOD + 5)
    
    prices = data.history(context.asset, 'price', lookback, '1d')
    high = data.history(context.asset, 'high', lookback, '1d')
    low = data.history(context.asset, 'low', lookback, '1d')
    volume = data.history(context.asset, 'volume', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    # Calculate indicators
    bb = compute_bollinger_bands(prices)
    atr = compute_atr(high, low, prices, ATR_PERIOD)
    
    current_price = prices.iloc[-1]
    current_bb = {k: v.iloc[-1] for k, v in bb.items()}
    current_atr = atr.iloc[-1]
    
    # Volume analysis
    avg_volume = volume[-20:].mean()
    current_volume = volume.iloc[-1]
    volume_spike = current_volume > (avg_volume * BO_VOLUME_MULTIPLIER)
    
    # Record metrics
    record(
        price=current_price,
        bb_upper=current_bb['upper'],
        bb_middle=current_bb['middle'],
        bb_lower=current_bb['lower'],
        percent_b=current_bb['percent_b'],
        bandwidth=current_bb['bandwidth']
    )
    
    # Bandwidth filter
    if USE_BANDWIDTH_FILTER:
        if current_bb['bandwidth'] < MIN_BANDWIDTH or current_bb['bandwidth'] > MAX_BANDWIDTH:
            return
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Execute based on strategy mode
    if STRATEGY_MODE == 'mean_reversion':
        execute_mean_reversion(context, data, current_price, current_bb, current_atr)
    elif STRATEGY_MODE == 'breakout':
        execute_breakout(context, data, current_price, current_bb, current_atr, volume_spike)


def execute_mean_reversion(context, data, price, bb, atr):
    """Mean reversion logic: buy low, sell high."""
    
    position_size = compute_position_size(context, data, atr)
    
    # Entry: price below lower band (%B < threshold)
    if not context.in_position:
        if bb['percent_b'] <= MR_ENTRY_THRESHOLD:
            order_target_percent(context.asset, position_size)
            context.in_position = True
            context.position_side = 1
            context.entry_price = price
            
            if USE_STOP_LOSS:
                context.stop_price = price - (atr * STOP_LOSS_ATR_MULT)
            
            record(entry_signal=1)
            return
    
    # Exit: price returns to middle or hits upper band
    if context.in_position and context.position_side == 1:
        should_exit = False
        
        # Exit at middle band
        if bb['percent_b'] >= MR_EXIT_THRESHOLD:
            should_exit = True
        
        # Exit at upper band (full reversion)
        if bb['percent_b'] >= MR_UPPER_EXIT:
            should_exit = True
        
        if should_exit:
            order_target_percent(context.asset, 0)
            context.in_position = False
            context.position_side = 0
            context.entry_price = 0.0
            context.stop_price = 0.0
            record(exit_signal=1)
            return
    
    record(entry_signal=0, exit_signal=0)


def execute_breakout(context, data, price, bb, atr, volume_spike):
    """Breakout logic: buy upper breakout, sell on breakdown."""
    
    position_size = compute_position_size(context, data, atr)
    
    # Track bars above/below bands
    if bb['percent_b'] > 1.0:
        context.bars_above_upper += 1
        context.bars_below_lower = 0
    elif bb['percent_b'] < 0.0:
        context.bars_below_lower += 1
        context.bars_above_upper = 0
    else:
        context.bars_above_upper = 0
        context.bars_below_lower = 0
    
    # Entry: breakout above upper band with confirmation
    if not context.in_position:
        breakout_confirmed = context.bars_above_upper >= BO_CONFIRMATION_BARS
        
        if BO_USE_VOLUME_CONFIRM:
            breakout_confirmed = breakout_confirmed and volume_spike
        
        if breakout_confirmed:
            order_target_percent(context.asset, position_size)
            context.in_position = True
            context.position_side = 1
            context.entry_price = price
            
            if USE_STOP_LOSS:
                context.stop_price = bb['middle']  # Stop at middle band
            
            record(entry_signal=1)
            return
    
    # Exit: price falls back into bands
    if context.in_position and context.position_side == 1:
        # Exit when price returns to middle band
        if bb['percent_b'] <= 0.5:
            order_target_percent(context.asset, 0)
            context.in_position = False
            context.position_side = 0
            context.entry_price = 0.0
            context.stop_price = 0.0
            record(exit_signal=1)
            return
    
    record(entry_signal=0, exit_signal=0)


def check_stops(context, data):
    """Check stop loss levels."""
    
    if not context.in_position or not USE_STOP_LOSS:
        return
    
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    
    if context.position_side == 1 and current_price <= context.stop_price:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.position_side = 0
        context.entry_price = 0.0
        context.stop_price = 0.0
        record(stop_triggered=1)
    else:
        record(stop_triggered=0)


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 60)
    print("BOLLINGER BANDS STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {ASSET_SYMBOL}")
    print(f"Mode: {STRATEGY_MODE}")
    print(f"BB Period: {BB_PERIOD}, Std Dev: {BB_STD_DEV}")
    print(f"Total Return: {perf['returns'].sum():.2%}")
    print(f"Final Portfolio Value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    
    returns = perf['returns']
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
