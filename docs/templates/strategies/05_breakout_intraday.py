# Breakout Intraday Strategy Template
# ==============================================================================
# An intraday breakout strategy that identifies and trades range breakouts
# using opening range, previous day's high/low, and volume confirmation.
#
# STRATEGY LOGIC:
# - Identify opening range during first N minutes
# - BUY when price breaks above opening range high with volume
# - SELL when price breaks below opening range low
# - Close all positions before market close
# ==============================================================================

from zipline.api import (
    symbol, symbols, order_target_percent, order_target, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order, get_datetime
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd


# ==============================================================================
# [PLACEHOLDERS] - CONFIGURE THESE PARAMETERS
# ==============================================================================

# Asset Configuration
ASSET_SYMBOL = 'SPY'              # [PLACEHOLDER] Asset to trade

# Opening Range Parameters
OPENING_RANGE_MINUTES = 30        # [PLACEHOLDER] Minutes to form opening range (15-60)
BREAKOUT_BUFFER_PCT = 0.001       # [PLACEHOLDER] Buffer above/below range (0.0005-0.003)

# Breakout Confirmation
REQUIRE_VOLUME_CONFIRM = True     # [PLACEHOLDER] Require volume confirmation
VOLUME_MULTIPLIER = 1.5           # [PLACEHOLDER] Volume vs average (1.2-2.0)
VOLUME_LOOKBACK_BARS = 20         # [PLACEHOLDER] Bars for average volume (10-30)
REQUIRE_CLOSE_CONFIRM = True      # [PLACEHOLDER] Wait for bar close above/below
MIN_BREAKOUT_SIZE_PCT = 0.002     # [PLACEHOLDER] Minimum breakout move (0.001-0.005)

# Previous Day Levels
USE_PREV_DAY_LEVELS = True        # [PLACEHOLDER] Include prev day high/low
PREV_DAY_WEIGHT = 0.5             # [PLACEHOLDER] Weight for prev day levels (0.0-1.0)

# Entry Timing
EARLIEST_ENTRY_MINUTES = 35       # [PLACEHOLDER] Earliest entry after open (30-60)
LATEST_ENTRY_MINUTES = 300        # [PLACEHOLDER] Latest entry (5 hours = 300 min)
MAX_ENTRIES_PER_DAY = 2           # [PLACEHOLDER] Maximum trades per day (1-3)

# Position Sizing
POSITION_SIZE = 0.90              # [PLACEHOLDER] Position allocation (0.5-1.0)
USE_ATR_SIZING = True             # [PLACEHOLDER] Size based on ATR
ATR_PERIOD = 14                   # [PLACEHOLDER] ATR period (10-20)
RISK_PER_TRADE_PCT = 0.02         # [PLACEHOLDER] Risk per trade (0.01-0.03)

# Risk Management
USE_STOP_LOSS = True              # [PLACEHOLDER] Enable stop loss
STOP_LOSS_ATR_MULT = 1.5          # [PLACEHOLDER] ATR multiplier for stop (1.0-2.5)
STOP_LOSS_RANGE_PCT = 0.5         # [PLACEHOLDER] Stop at % of range (0.3-0.7)
USE_PROFIT_TARGET = True          # [PLACEHOLDER] Enable profit target
PROFIT_TARGET_ATR_MULT = 2.0      # [PLACEHOLDER] ATR multiplier for target (1.5-3.0)
USE_TRAILING_STOP = True          # [PLACEHOLDER] Enable trailing stop
TRAILING_STOP_ATR_MULT = 1.0      # [PLACEHOLDER] ATR for trailing (0.5-1.5)

# End of Day Settings
CLOSE_BEFORE_EOD_MINUTES = 15     # [PLACEHOLDER] Close positions N mins before close
FLATTEN_EOD = True                # [PLACEHOLDER] Close all positions EOD

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
    
    # Daily reset variables
    context.opening_range_high = None
    context.opening_range_low = None
    context.prev_day_high = None
    context.prev_day_low = None
    context.opening_range_set = False
    context.trades_today = 0
    context.bars_since_open = 0
    
    # Position tracking
    context.in_position = False
    context.position_side = 0        # 1 = long, -1 = short
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.highest_since_entry = 0.0
    context.current_atr = 0.0
    
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
    
    # Schedule daily reset
    schedule_function(
        daily_reset,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )
    
    # Schedule end of day close
    if FLATTEN_EOD:
        schedule_function(
            close_all_positions,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_close(minutes=CLOSE_BEFORE_EOD_MINUTES)
        )


def daily_reset(context, data):
    """Reset daily variables at market open."""
    
    context.opening_range_high = None
    context.opening_range_low = None
    context.opening_range_set = False
    context.trades_today = 0
    context.bars_since_open = 0
    
    # Get previous day's high/low
    if USE_PREV_DAY_LEVELS and data.can_trade(context.asset):
        try:
            hist_high = data.history(context.asset, 'high', 2, '1d')
            hist_low = data.history(context.asset, 'low', 2, '1d')
            
            if len(hist_high) >= 2:
                context.prev_day_high = hist_high.iloc[-2]
                context.prev_day_low = hist_low.iloc[-2]
        except:
            pass
    
    # Calculate ATR for sizing
    try:
        high = data.history(context.asset, 'high', ATR_PERIOD + 5, '1d')
        low = data.history(context.asset, 'low', ATR_PERIOD + 5, '1d')
        close = data.history(context.asset, 'close', ATR_PERIOD + 5, '1d')
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        context.current_atr = true_range.rolling(ATR_PERIOD).mean().iloc[-1]
    except:
        context.current_atr = 0.0


def handle_data(context, data):
    """Called every bar - main intraday logic."""
    
    if not data.can_trade(context.asset):
        return
    
    context.bars_since_open += 1
    
    current_price = data.current(context.asset, 'price')
    current_high = data.current(context.asset, 'high')
    current_low = data.current(context.asset, 'low')
    current_volume = data.current(context.asset, 'volume')
    
    # Phase 1: Build opening range
    if not context.opening_range_set:
        update_opening_range(context, current_high, current_low)
        return
    
    # Record levels
    record(
        price=current_price,
        or_high=context.opening_range_high,
        or_low=context.opening_range_low,
        in_position=1 if context.in_position else 0
    )
    
    # Phase 2: Manage existing position
    if context.in_position:
        manage_position(context, data, current_price)
        return
    
    # Phase 3: Look for breakout entries
    if context.trades_today < MAX_ENTRIES_PER_DAY:
        if context.bars_since_open >= EARLIEST_ENTRY_MINUTES:
            if context.bars_since_open <= LATEST_ENTRY_MINUTES:
                check_breakout_entry(context, data, current_price, current_volume)


def update_opening_range(context, high, low):
    """Update opening range during formation period."""
    
    if context.opening_range_high is None:
        context.opening_range_high = high
        context.opening_range_low = low
    else:
        context.opening_range_high = max(context.opening_range_high, high)
        context.opening_range_low = min(context.opening_range_low, low)
    
    # Check if opening range period complete
    if context.bars_since_open >= OPENING_RANGE_MINUTES:
        context.opening_range_set = True
        
        # Blend with previous day levels if enabled
        if USE_PREV_DAY_LEVELS and context.prev_day_high is not None:
            w = PREV_DAY_WEIGHT
            context.opening_range_high = (
                (1 - w) * context.opening_range_high + 
                w * context.prev_day_high
            )
            context.opening_range_low = (
                (1 - w) * context.opening_range_low + 
                w * context.prev_day_low
            )
        
        record(
            or_high=context.opening_range_high,
            or_low=context.opening_range_low,
            range_set=1
        )


def check_breakout_entry(context, data, price, volume):
    """Check for and execute breakout entries."""
    
    # Calculate breakout levels with buffer
    range_size = context.opening_range_high - context.opening_range_low
    buffer = range_size * BREAKOUT_BUFFER_PCT
    
    upper_breakout = context.opening_range_high + buffer
    lower_breakout = context.opening_range_low - buffer
    
    # Volume confirmation
    volume_confirmed = True
    if REQUIRE_VOLUME_CONFIRM:
        try:
            avg_volume = data.history(
                context.asset, 'volume', VOLUME_LOOKBACK_BARS, '1m'
            ).mean()
            volume_confirmed = volume > (avg_volume * VOLUME_MULTIPLIER)
        except:
            volume_confirmed = True
    
    # Minimum breakout size
    breakout_size_ok = True
    if MIN_BREAKOUT_SIZE_PCT > 0:
        if price > upper_breakout:
            breakout_pct = (price - context.opening_range_high) / context.opening_range_high
            breakout_size_ok = breakout_pct >= MIN_BREAKOUT_SIZE_PCT
        elif price < lower_breakout:
            breakout_pct = (context.opening_range_low - price) / context.opening_range_low
            breakout_size_ok = breakout_pct >= MIN_BREAKOUT_SIZE_PCT
    
    # Long breakout
    if price > upper_breakout and volume_confirmed and breakout_size_ok:
        execute_entry(context, data, price, 1)  # Long
        return
    
    # Short breakout (if allowed)
    # Uncomment for short entries:
    # if price < lower_breakout and volume_confirmed and breakout_size_ok:
    #     execute_entry(context, data, price, -1)  # Short


def execute_entry(context, data, price, direction):
    """Execute a breakout entry."""
    
    # Calculate position size
    position_size = calculate_position_size(context, price, direction)
    
    # Calculate stops and targets
    atr = context.current_atr if context.current_atr > 0 else price * 0.01
    range_size = context.opening_range_high - context.opening_range_low
    
    if direction == 1:  # Long
        # Stop below opening range or ATR-based
        stop_range = context.opening_range_low + (range_size * STOP_LOSS_RANGE_PCT)
        stop_atr = price - (atr * STOP_LOSS_ATR_MULT)
        context.stop_price = max(stop_range, stop_atr)
        
        # Target based on ATR
        context.target_price = price + (atr * PROFIT_TARGET_ATR_MULT)
    else:  # Short
        stop_range = context.opening_range_high - (range_size * STOP_LOSS_RANGE_PCT)
        stop_atr = price + (atr * STOP_LOSS_ATR_MULT)
        context.stop_price = min(stop_range, stop_atr)
        
        context.target_price = price - (atr * PROFIT_TARGET_ATR_MULT)
    
    # Execute order
    order_target_percent(context.asset, position_size * direction)
    
    context.in_position = True
    context.position_side = direction
    context.entry_price = price
    context.highest_since_entry = price
    context.trades_today += 1
    
    record(entry_signal=direction)


def calculate_position_size(context, price, direction):
    """Calculate position size based on risk parameters."""
    
    if not USE_ATR_SIZING or context.current_atr == 0:
        return POSITION_SIZE
    
    # Risk-based sizing: risk amount / distance to stop
    atr = context.current_atr
    stop_distance = atr * STOP_LOSS_ATR_MULT
    
    # Position size = (Portfolio * Risk%) / (Price * Stop%)
    risk_per_share = stop_distance
    
    if risk_per_share > 0:
        shares_for_risk = (RISK_PER_TRADE_PCT * price) / risk_per_share
        size = min(shares_for_risk / 100, POSITION_SIZE)  # Normalize
        return max(size, 0.1)  # Minimum 10%
    
    return POSITION_SIZE


def manage_position(context, data, price):
    """Manage existing position - stops, targets, trailing."""
    
    # Update highest price for trailing stop
    if context.position_side == 1:
        context.highest_since_entry = max(context.highest_since_entry, price)
    else:
        context.highest_since_entry = min(context.highest_since_entry, price)
    
    should_exit = False
    exit_reason = ""
    
    atr = context.current_atr if context.current_atr > 0 else price * 0.01
    
    if context.position_side == 1:  # Long position
        # Stop loss
        if USE_STOP_LOSS and price <= context.stop_price:
            should_exit = True
            exit_reason = "stop_loss"
        
        # Trailing stop
        if USE_TRAILING_STOP and not should_exit:
            trail_stop = context.highest_since_entry - (atr * TRAILING_STOP_ATR_MULT)
            if price <= trail_stop and trail_stop > context.stop_price:
                should_exit = True
                exit_reason = "trailing_stop"
        
        # Profit target
        if USE_PROFIT_TARGET and price >= context.target_price:
            should_exit = True
            exit_reason = "profit_target"
        
        # Break back into range (failed breakout)
        if price < context.opening_range_high:
            should_exit = True
            exit_reason = "failed_breakout"
    
    else:  # Short position
        if USE_STOP_LOSS and price >= context.stop_price:
            should_exit = True
            exit_reason = "stop_loss"
        
        if USE_TRAILING_STOP and not should_exit:
            trail_stop = context.highest_since_entry + (atr * TRAILING_STOP_ATR_MULT)
            if price >= trail_stop and trail_stop < context.stop_price:
                should_exit = True
                exit_reason = "trailing_stop"
        
        if USE_PROFIT_TARGET and price <= context.target_price:
            should_exit = True
            exit_reason = "profit_target"
        
        if price > context.opening_range_low:
            should_exit = True
            exit_reason = "failed_breakout"
    
    if should_exit:
        order_target_percent(context.asset, 0)
        reset_position_state(context)
        record(exit_signal=1, exit_type=hash(exit_reason) % 10)


def close_all_positions(context, data):
    """Close all positions before end of day."""
    
    if context.in_position:
        order_target_percent(context.asset, 0)
        reset_position_state(context)
        record(eod_close=1)


def reset_position_state(context):
    """Reset position tracking variables."""
    context.in_position = False
    context.position_side = 0
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.highest_since_entry = 0.0


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 60)
    print("BREAKOUT INTRADAY STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {ASSET_SYMBOL}")
    print(f"Opening Range: {OPENING_RANGE_MINUTES} minutes")
    print(f"Total Return: {perf['returns'].sum():.2%}")
    print(f"Final Portfolio Value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    
    returns = perf['returns']
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
