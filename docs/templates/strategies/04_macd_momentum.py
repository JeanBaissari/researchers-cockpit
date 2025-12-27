# MACD Momentum Strategy Template
# ==============================================================================
# A momentum strategy using MACD with histogram divergence detection,
# signal line crossovers, and zero-line confirmation.
#
# STRATEGY LOGIC:
# - BUY on MACD line crossing above signal line (bullish crossover)
# - SELL on MACD line crossing below signal line (bearish crossover)
# - Optional: Confirm with zero-line position and histogram momentum
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
ASSET_SYMBOL = 'SPY'              # [PLACEHOLDER] Asset to trade

# MACD Parameters
MACD_FAST_PERIOD = 12             # [PLACEHOLDER] Fast EMA period (8-15)
MACD_SLOW_PERIOD = 26             # [PLACEHOLDER] Slow EMA period (20-30)
MACD_SIGNAL_PERIOD = 9            # [PLACEHOLDER] Signal line period (5-12)

# Signal Confirmation
REQUIRE_ZERO_LINE_CONFIRM = False # [PLACEHOLDER] Require MACD above/below zero
REQUIRE_HISTOGRAM_MOMENTUM = True # [PLACEHOLDER] Require histogram expansion
HISTOGRAM_BARS = 3                # [PLACEHOLDER] Bars of histogram growth (2-5)

# Trend Filter
USE_TREND_FILTER = True           # [PLACEHOLDER] Use trend filter
TREND_EMA_PERIOD = 50             # [PLACEHOLDER] Trend EMA period (50-200)
TREND_FILTER_MODE = 'price'       # [PLACEHOLDER] 'price' (price > EMA) or 'macd' (MACD > 0)

# Divergence Detection
USE_DIVERGENCE = False            # [PLACEHOLDER] Trade on divergence signals
DIVERGENCE_LOOKBACK = 20          # [PLACEHOLDER] Bars to check for divergence (10-30)

# Position Sizing
POSITION_SIZE = 0.95              # [PLACEHOLDER] Position allocation (0.5-1.0)
USE_SIGNAL_STRENGTH_SIZING = True # [PLACEHOLDER] Scale by histogram strength
MIN_POSITION_SIZE = 0.50          # [PLACEHOLDER] Minimum position (0.3-0.7)

# Risk Management
USE_STOP_LOSS = True              # [PLACEHOLDER] Enable stop loss
STOP_LOSS_PCT = 0.05              # [PLACEHOLDER] Fixed stop loss (0.03-0.08)
USE_TRAILING_STOP = True          # [PLACEHOLDER] Use trailing stop
TRAILING_STOP_PCT = 0.07          # [PLACEHOLDER] Trailing stop (0.05-0.12)
USE_PROFIT_TARGET = False         # [PLACEHOLDER] Enable profit target
PROFIT_TARGET_PCT = 0.15          # [PLACEHOLDER] Profit target (0.10-0.25)

# Exit Settings
EXIT_ON_SIGNAL_CROSS = True       # [PLACEHOLDER] Exit on opposite crossover
EXIT_ON_ZERO_CROSS = False        # [PLACEHOLDER] Exit when MACD crosses zero

# Execution Settings
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open (0-60)

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
MIN_TRADE_COST = 1.0              # [PLACEHOLDER] Minimum per trade
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
    context.entry_price = 0.0
    context.highest_price = 0.0
    context.lowest_price = float('inf')
    
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
    
    # Schedule risk management
    schedule_function(
        manage_risk,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=5)
    )


def compute_ema(prices, period):
    """Calculate Exponential Moving Average."""
    return prices.ewm(span=period, adjust=False).mean()


def compute_macd(prices):
    """Calculate MACD, Signal, and Histogram."""
    
    fast_ema = compute_ema(prices, MACD_FAST_PERIOD)
    slow_ema = compute_ema(prices, MACD_SLOW_PERIOD)
    
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, MACD_SIGNAL_PERIOD)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram,
        'fast_ema': fast_ema,
        'slow_ema': slow_ema
    }


def detect_crossover(series1, series2):
    """Detect if series1 crossed above series2."""
    current_above = series1.iloc[-1] > series2.iloc[-1]
    prev_above = series1.iloc[-2] > series2.iloc[-2]
    
    bullish_cross = current_above and not prev_above
    bearish_cross = not current_above and prev_above
    
    return bullish_cross, bearish_cross


def check_histogram_momentum(histogram, direction='bullish'):
    """Check if histogram is expanding in the expected direction."""
    
    if len(histogram) < HISTOGRAM_BARS + 1:
        return False
    
    recent = histogram.iloc[-(HISTOGRAM_BARS + 1):]
    
    if direction == 'bullish':
        # Histogram should be increasing
        for i in range(1, len(recent)):
            if recent.iloc[i] <= recent.iloc[i - 1]:
                return False
        return True
    else:
        # Histogram should be decreasing
        for i in range(1, len(recent)):
            if recent.iloc[i] >= recent.iloc[i - 1]:
                return False
        return True


def detect_divergence(prices, macd, lookback):
    """Detect bullish or bearish divergence."""
    
    if len(prices) < lookback or len(macd) < lookback:
        return None, None
    
    recent_prices = prices.iloc[-lookback:]
    recent_macd = macd.iloc[-lookback:]
    
    # Find local lows for bullish divergence
    price_low_idx = recent_prices.idxmin()
    macd_low_idx = recent_macd.idxmin()
    
    # Find local highs for bearish divergence
    price_high_idx = recent_prices.idxmax()
    macd_high_idx = recent_macd.idxmax()
    
    # Bullish divergence: price makes lower low, MACD makes higher low
    current_price = prices.iloc[-1]
    current_macd = macd.iloc[-1]
    
    bullish_div = False
    bearish_div = False
    
    # Simplified divergence check
    if current_price < recent_prices.quantile(0.25):
        if current_macd > recent_macd.quantile(0.25):
            bullish_div = True
    
    if current_price > recent_prices.quantile(0.75):
        if current_macd < recent_macd.quantile(0.75):
            bearish_div = True
    
    return bullish_div, bearish_div


def compute_position_size(histogram):
    """Calculate position size based on signal strength."""
    
    if not USE_SIGNAL_STRENGTH_SIZING:
        return POSITION_SIZE
    
    # Normalize histogram strength
    recent_hist = histogram.iloc[-20:]
    hist_range = recent_hist.max() - recent_hist.min()
    
    if hist_range > 0:
        current_strength = abs(histogram.iloc[-1]) / hist_range
        size = MIN_POSITION_SIZE + (POSITION_SIZE - MIN_POSITION_SIZE) * current_strength
        return min(size, POSITION_SIZE)
    
    return POSITION_SIZE


def execute_strategy(context, data):
    """Main strategy execution."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get price history
    lookback = max(MACD_SLOW_PERIOD + MACD_SIGNAL_PERIOD + 10, 
                   TREND_EMA_PERIOD + 5, 
                   DIVERGENCE_LOOKBACK + 5)
    
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    # Calculate MACD
    macd = compute_macd(prices)
    current_price = prices.iloc[-1]
    
    # Calculate trend filter
    trend_ema = compute_ema(prices, TREND_EMA_PERIOD)
    trend_bullish = True
    
    if USE_TREND_FILTER:
        if TREND_FILTER_MODE == 'price':
            trend_bullish = current_price > trend_ema.iloc[-1]
        elif TREND_FILTER_MODE == 'macd':
            trend_bullish = macd['macd'].iloc[-1] > 0
    
    # Detect crossovers
    bullish_cross, bearish_cross = detect_crossover(macd['macd'], macd['signal'])
    
    # Record metrics
    record(
        price=current_price,
        macd=macd['macd'].iloc[-1],
        signal=macd['signal'].iloc[-1],
        histogram=macd['histogram'].iloc[-1],
        trend_ema=trend_ema.iloc[-1]
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Entry Logic
    if not context.in_position:
        should_enter = bullish_cross
        
        # Additional confirmations
        if REQUIRE_ZERO_LINE_CONFIRM:
            should_enter = should_enter and (macd['macd'].iloc[-1] > 0)
        
        if REQUIRE_HISTOGRAM_MOMENTUM:
            should_enter = should_enter and check_histogram_momentum(
                macd['histogram'], 'bullish'
            )
        
        if USE_TREND_FILTER:
            should_enter = should_enter and trend_bullish
        
        # Divergence entry (if enabled)
        if USE_DIVERGENCE:
            bullish_div, _ = detect_divergence(prices, macd['macd'], DIVERGENCE_LOOKBACK)
            if bullish_div:
                should_enter = True
        
        if should_enter:
            position_size = compute_position_size(macd['histogram'])
            order_target_percent(context.asset, position_size)
            
            context.in_position = True
            context.entry_price = current_price
            context.highest_price = current_price
            
            record(entry_signal=1)
            return
    
    # Exit Logic
    if context.in_position:
        should_exit = False
        
        if EXIT_ON_SIGNAL_CROSS and bearish_cross:
            should_exit = True
        
        if EXIT_ON_ZERO_CROSS and macd['macd'].iloc[-1] < 0:
            if macd['macd'].iloc[-2] >= 0:  # Just crossed below
                should_exit = True
        
        # Bearish divergence exit
        if USE_DIVERGENCE:
            _, bearish_div = detect_divergence(prices, macd['macd'], DIVERGENCE_LOOKBACK)
            if bearish_div:
                should_exit = True
        
        if should_exit:
            order_target_percent(context.asset, 0)
            context.in_position = False
            context.entry_price = 0.0
            context.highest_price = 0.0
            record(exit_signal=1)
            return
    
    record(entry_signal=0, exit_signal=0)


def manage_risk(context, data):
    """Manage stop losses and profit targets."""
    
    if not context.in_position:
        return
    
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    
    # Update highest price for trailing stop
    context.highest_price = max(context.highest_price, current_price)
    
    # Calculate PnL
    pnl_pct = (current_price - context.entry_price) / context.entry_price
    
    should_exit = False
    
    # Fixed stop loss
    if USE_STOP_LOSS and not USE_TRAILING_STOP:
        if pnl_pct <= -STOP_LOSS_PCT:
            should_exit = True
            record(stop_triggered=1)
    
    # Trailing stop
    if USE_TRAILING_STOP:
        trail_stop_price = context.highest_price * (1 - TRAILING_STOP_PCT)
        if current_price <= trail_stop_price:
            should_exit = True
            record(stop_triggered=1)
    
    # Profit target
    if USE_PROFIT_TARGET:
        if pnl_pct >= PROFIT_TARGET_PCT:
            should_exit = True
            record(profit_target_hit=1)
    
    if should_exit:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
    else:
        record(stop_triggered=0, profit_target_hit=0)


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 60)
    print("MACD MOMENTUM STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {ASSET_SYMBOL}")
    print(f"MACD: ({MACD_FAST_PERIOD}, {MACD_SLOW_PERIOD}, {MACD_SIGNAL_PERIOD})")
    print(f"Trend Filter: {USE_TREND_FILTER} ({TREND_FILTER_MODE})")
    print(f"Total Return: {perf['returns'].sum():.2%}")
    print(f"Final Portfolio Value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    
    returns = perf['returns']
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
