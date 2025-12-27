# Advanced Multi-Level Intraday Breakout Strategy
# ==============================================================================
# A sophisticated intraday strategy featuring:
# - Multiple support/resistance level detection
# - Statistical breakout validation
# - Volume profile analysis for order flow
# - Adaptive range calculation based on volatility regime
# - Multi-timeframe trend alignment
# - Smart position scaling on confirmed breakouts
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
from scipy import stats


# ==============================================================================
# [PLACEHOLDERS] - CONFIGURE THESE PARAMETERS
# ==============================================================================

# Asset Configuration
ASSET_SYMBOL = 'SPY'              # [PLACEHOLDER] Primary asset

# Multi-Level Detection
USE_MULTI_LEVEL = True            # [PLACEHOLDER] Multiple S/R levels
LEVEL_LOOKBACK_DAYS = 5           # [PLACEHOLDER] Days to find levels
MIN_TOUCHES = 2                   # [PLACEHOLDER] Min touches for valid level
LEVEL_TOLERANCE_PCT = 0.002       # [PLACEHOLDER] Tolerance for level touches
MAX_LEVELS = 5                    # [PLACEHOLDER] Max levels to track

# Opening Range Parameters
PRIMARY_RANGE_MINUTES = 30        # [PLACEHOLDER] Primary range period (15-60)
SECONDARY_RANGE_MINUTES = 15      # [PLACEHOLDER] Secondary range (5-30)
USE_ADAPTIVE_RANGE = True         # [PLACEHOLDER] Adjust range by volatility
MIN_RANGE_MINUTES = 10            # [PLACEHOLDER] Min range in high vol
MAX_RANGE_MINUTES = 60            # [PLACEHOLDER] Max range in low vol

# Statistical Breakout Validation
USE_STATISTICAL_VALIDATION = True # [PLACEHOLDER] Validate breakouts statistically
MIN_BREAKOUT_ZSCORE = 2.0         # [PLACEHOLDER] Min z-score for breakout
LOOKBACK_FOR_STATS = 20           # [PLACEHOLDER] Bars for statistics
REQUIRE_VOLUME_ANOMALY = True     # [PLACEHOLDER] Require unusual volume
VOLUME_ZSCORE_THRESHOLD = 1.5     # [PLACEHOLDER] Volume z-score threshold

# Volume Profile / Order Flow
USE_VOLUME_PROFILE = True         # [PLACEHOLDER] Analyze volume profile
VOLUME_PROFILE_BINS = 10          # [PLACEHOLDER] Price bins for profile
HIGH_VOLUME_NODE_THRESHOLD = 0.7  # [PLACEHOLDER] Percentile for HVN
TRADE_NEAR_HVN = True             # [PLACEHOLDER] Prefer trades near HVN

# Multi-Timeframe Alignment
USE_MTF_TREND = True              # [PLACEHOLDER] Align with higher TF
DAILY_TREND_EMA = 20              # [PLACEHOLDER] Daily EMA for trend
INTRADAY_TREND_EMA = 50           # [PLACEHOLDER] Intraday EMA (in bars)
REQUIRE_TREND_ALIGNMENT = True    # [PLACEHOLDER] Require trend alignment

# Breakout Confirmation
CONFIRMATION_BARS = 2             # [PLACEHOLDER] Bars above/below level
CONFIRMATION_CLOSE = True         # [PLACEHOLDER] Require close confirmation
MIN_BREAKOUT_DISTANCE_PCT = 0.002 # [PLACEHOLDER] Min distance from level
FAILED_BREAKOUT_THRESHOLD = 0.5   # [PLACEHOLDER] Retrace for failed BO

# Volatility Regime
VOL_REGIME_LOOKBACK = 20          # [PLACEHOLDER] Bars for vol regime
HIGH_VOL_PERCENTILE = 80          # [PLACEHOLDER] High vol threshold
LOW_VOL_PERCENTILE = 20           # [PLACEHOLDER] Low vol threshold
AVOID_EXTREME_VOL = True          # [PLACEHOLDER] Skip extreme volatility

# Position Sizing
BASE_POSITION = 0.70              # [PLACEHOLDER] Base position size
USE_RISK_BASED_SIZING = True      # [PLACEHOLDER] Size by risk
RISK_PER_TRADE = 0.015            # [PLACEHOLDER] Risk per trade (0.01-0.03)
MAX_POSITION = 1.0                # [PLACEHOLDER] Maximum position
MIN_POSITION = 0.20               # [PLACEHOLDER] Minimum position

# Scaling
USE_BREAKOUT_SCALING = True       # [PLACEHOLDER] Scale into breakouts
INITIAL_ENTRY_PCT = 0.5           # [PLACEHOLDER] Initial entry fraction
CONFIRMATION_ENTRY_PCT = 0.5      # [PLACEHOLDER] Confirmation add
MAX_SCALE_INS = 2                 # [PLACEHOLDER] Max scale-ins

# Risk Management
USE_ATR_STOPS = True              # [PLACEHOLDER] ATR-based stops
STOP_ATR_MULT = 1.5               # [PLACEHOLDER] ATR multiplier
INITIAL_STOP_AT_RANGE = True      # [PLACEHOLDER] Stop at range boundary
USE_BREAKEVEN_STOP = True         # [PLACEHOLDER] Move to breakeven
BREAKEVEN_TRIGGER_ATR = 1.0       # [PLACEHOLDER] ATR move for breakeven
USE_TRAILING_STOP = True          # [PLACEHOLDER] Trailing stop
TRAILING_STOP_ATR = 1.5           # [PLACEHOLDER] Trailing ATR mult
PROFIT_TARGET_ATR = 3.0           # [PLACEHOLDER] Profit target in ATRs

# Failed Breakout Handling
TRADE_FAILED_BREAKOUTS = False    # [PLACEHOLDER] Fade failed breakouts
FAILED_BO_REVERSAL_SIZE = 0.5     # [PLACEHOLDER] Size for reversal trade

# Time Management
EARLIEST_ENTRY_MINUTES = 35       # [PLACEHOLDER] Earliest entry
LATEST_ENTRY_MINUTES = 300        # [PLACEHOLDER] Latest entry (5 hours)
NO_NEW_TRADES_BEFORE_CLOSE = 30   # [PLACEHOLDER] No trades X min before close
FLATTEN_EOD = True                # [PLACEHOLDER] Flatten end of day
FLATTEN_MINUTES_BEFORE = 15       # [PLACEHOLDER] Minutes before close

# Execution
MAX_TRADES_PER_DAY = 3            # [PLACEHOLDER] Max daily trades

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission
SLIPPAGE_BPS = 3.0                # [PLACEHOLDER] Slippage


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Initialize strategy."""
    
    context.asset = symbol(ASSET_SYMBOL)
    
    # Daily state (reset each day)
    context.opening_range_high = None
    context.opening_range_low = None
    context.range_set = False
    context.detected_levels = []
    context.volume_profile = None
    context.trades_today = 0
    context.bars_since_open = 0
    
    # Position state
    context.in_position = False
    context.position_side = 0
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.highest_since_entry = 0.0
    context.lowest_since_entry = float('inf')
    context.scale_ins = 0
    context.breakeven_activated = False
    
    # Volatility state
    context.current_atr = 0.0
    context.vol_regime = 'normal'
    
    set_benchmark(context.asset)
    
    set_commission(us_equities=commission.PerShare(
        cost=COMMISSION_PER_SHARE, min_trade_cost=1.0
    ))
    
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(
        basis_points=SLIPPAGE_BPS, volume_limit=0.1
    ))
    
    # Daily reset
    schedule_function(daily_setup, date_rules.every_day(),
                     time_rules.market_open(minutes=1))
    
    # End of day
    if FLATTEN_EOD:
        schedule_function(flatten_positions, date_rules.every_day(),
                         time_rules.market_close(minutes=FLATTEN_MINUTES_BEFORE))


def daily_setup(context, data):
    """Reset daily variables and compute initial metrics."""
    
    context.opening_range_high = None
    context.opening_range_low = None
    context.range_set = False
    context.detected_levels = []
    context.volume_profile = None
    context.trades_today = 0
    context.bars_since_open = 0
    context.breakeven_activated = False
    
    if not data.can_trade(context.asset):
        return
    
    # Compute daily ATR from daily bars
    try:
        high_d = data.history(context.asset, 'high', 20, '1d')
        low_d = data.history(context.asset, 'low', 20, '1d')
        close_d = data.history(context.asset, 'close', 20, '1d')
        
        tr = pd.concat([high_d - low_d,
                        abs(high_d - close_d.shift(1)),
                        abs(low_d - close_d.shift(1))], axis=1).max(axis=1)
        context.current_atr = tr.rolling(14).mean().iloc[-1]
        
        # Volatility regime
        vol = tr.rolling(VOL_REGIME_LOOKBACK).std()
        vol_pct = vol.rank(pct=True).iloc[-1] * 100
        
        if vol_pct > HIGH_VOL_PERCENTILE:
            context.vol_regime = 'high'
        elif vol_pct < LOW_VOL_PERCENTILE:
            context.vol_regime = 'low'
        else:
            context.vol_regime = 'normal'
            
    except:
        context.current_atr = 0.01
        context.vol_regime = 'normal'
    
    # Detect support/resistance levels from recent days
    if USE_MULTI_LEVEL:
        try:
            detect_sr_levels(context, data)
        except:
            pass


def detect_sr_levels(context, data):
    """Detect support and resistance levels from recent price action."""
    
    high = data.history(context.asset, 'high', LEVEL_LOOKBACK_DAYS * 390, '1m')
    low = data.history(context.asset, 'low', LEVEL_LOOKBACK_DAYS * 390, '1m')
    close = data.history(context.asset, 'close', LEVEL_LOOKBACK_DAYS * 390, '1m')
    
    if len(high) < 100:
        return
    
    # Find swing highs and lows
    swing_highs = []
    swing_lows = []
    
    window = 10
    for i in range(window, len(high) - window):
        if high.iloc[i] == high.iloc[i-window:i+window+1].max():
            swing_highs.append(high.iloc[i])
        if low.iloc[i] == low.iloc[i-window:i+window+1].min():
            swing_lows.append(low.iloc[i])
    
    # Cluster nearby levels
    all_levels = swing_highs + swing_lows
    if len(all_levels) < 2:
        return
    
    levels = []
    tolerance = close.iloc[-1] * LEVEL_TOLERANCE_PCT
    
    for level in all_levels:
        # Count touches
        touches = sum(1 for l in all_levels if abs(l - level) < tolerance)
        if touches >= MIN_TOUCHES:
            # Check if already have nearby level
            is_new = True
            for existing in levels:
                if abs(existing['price'] - level) < tolerance:
                    is_new = False
                    break
            
            if is_new:
                levels.append({
                    'price': level,
                    'touches': touches,
                    'type': 'resistance' if level > close.iloc[-1] else 'support'
                })
    
    # Sort by touches and limit
    levels.sort(key=lambda x: x['touches'], reverse=True)
    context.detected_levels = levels[:MAX_LEVELS]


def compute_volume_profile(prices, volume, num_bins):
    """Compute volume profile (Volume at Price)."""
    
    price_min = prices.min()
    price_max = prices.max()
    
    if price_max == price_min:
        return None
    
    bin_size = (price_max - price_min) / num_bins
    bins = np.linspace(price_min, price_max, num_bins + 1)
    
    profile = []
    for i in range(num_bins):
        mask = (prices >= bins[i]) & (prices < bins[i+1])
        vol_in_bin = volume[mask].sum()
        mid_price = (bins[i] + bins[i+1]) / 2
        profile.append({
            'price': mid_price,
            'volume': vol_in_bin
        })
    
    return profile


def find_high_volume_nodes(profile, threshold_pct):
    """Find high volume nodes in profile."""
    if not profile:
        return []
    
    volumes = [p['volume'] for p in profile]
    threshold = np.percentile(volumes, threshold_pct * 100)
    
    hvn = [p for p in profile if p['volume'] >= threshold]
    return hvn


def validate_breakout_statistically(prices, volume, breakout_price, direction):
    """Statistically validate a breakout."""
    if not USE_STATISTICAL_VALIDATION:
        return True, 0, 0
    
    if len(prices) < LOOKBACK_FOR_STATS:
        return True, 0, 0
    
    recent_prices = prices.iloc[-LOOKBACK_FOR_STATS:]
    recent_volume = volume.iloc[-LOOKBACK_FOR_STATS:]
    
    # Price z-score
    price_mean = recent_prices.mean()
    price_std = recent_prices.std()
    
    if price_std > 0:
        price_zscore = (breakout_price - price_mean) / price_std
    else:
        price_zscore = 0
    
    # Volume z-score
    vol_mean = recent_volume.mean()
    vol_std = recent_volume.std()
    current_vol = volume.iloc[-1]
    
    if vol_std > 0:
        vol_zscore = (current_vol - vol_mean) / vol_std
    else:
        vol_zscore = 0
    
    # Validate
    price_valid = abs(price_zscore) >= MIN_BREAKOUT_ZSCORE
    
    if REQUIRE_VOLUME_ANOMALY:
        vol_valid = vol_zscore >= VOLUME_ZSCORE_THRESHOLD
    else:
        vol_valid = True
    
    return price_valid and vol_valid, price_zscore, vol_zscore


def get_adaptive_range_period(vol_regime):
    """Adjust range period based on volatility."""
    if not USE_ADAPTIVE_RANGE:
        return PRIMARY_RANGE_MINUTES
    
    if vol_regime == 'high':
        return MIN_RANGE_MINUTES
    elif vol_regime == 'low':
        return MAX_RANGE_MINUTES
    else:
        return PRIMARY_RANGE_MINUTES


def compute_risk_based_size(context, entry_price, stop_price):
    """Calculate position size based on risk."""
    if not USE_RISK_BASED_SIZING:
        return BASE_POSITION
    
    risk_per_share = abs(entry_price - stop_price)
    
    if risk_per_share <= 0:
        return BASE_POSITION
    
    portfolio_value = context.portfolio.portfolio_value
    risk_amount = portfolio_value * RISK_PER_TRADE
    
    shares = risk_amount / risk_per_share
    position_value = shares * entry_price
    position_pct = position_value / portfolio_value
    
    return np.clip(position_pct, MIN_POSITION, MAX_POSITION)


def handle_data(context, data):
    """Main intraday logic."""
    
    if not data.can_trade(context.asset):
        return
    
    context.bars_since_open += 1
    
    current_price = data.current(context.asset, 'price')
    current_high = data.current(context.asset, 'high')
    current_low = data.current(context.asset, 'low')
    current_volume = data.current(context.asset, 'volume')
    
    # Get intraday history
    try:
        prices = data.history(context.asset, 'price', 60, '1m')
        volume = data.history(context.asset, 'volume', 60, '1m')
        high = data.history(context.asset, 'high', 60, '1m')
        low = data.history(context.asset, 'low', 60, '1m')
    except:
        return
    
    # Adaptive range period
    range_period = get_adaptive_range_period(context.vol_regime)
    
    # Phase 1: Build opening range
    if not context.range_set:
        if context.opening_range_high is None:
            context.opening_range_high = current_high
            context.opening_range_low = current_low
        else:
            context.opening_range_high = max(context.opening_range_high, current_high)
            context.opening_range_low = min(context.opening_range_low, current_low)
        
        if context.bars_since_open >= range_period:
            context.range_set = True
            
            # Build volume profile
            if USE_VOLUME_PROFILE:
                context.volume_profile = compute_volume_profile(
                    prices, volume, VOLUME_PROFILE_BINS
                )
            
            record(
                range_high=context.opening_range_high,
                range_low=context.opening_range_low,
                range_set=1
            )
        return
    
    # Record state
    record(
        price=current_price,
        range_high=context.opening_range_high,
        range_low=context.opening_range_low,
        in_position=1 if context.in_position else 0
    )
    
    # Skip extreme volatility
    if AVOID_EXTREME_VOL and context.vol_regime == 'high':
        return
    
    # Phase 2: Manage existing position
    if context.in_position:
        manage_position(context, data, current_price)
        return
    
    # Phase 3: Look for entries
    if context.trades_today >= MAX_TRADES_PER_DAY:
        return
    
    if context.bars_since_open < EARLIEST_ENTRY_MINUTES:
        return
    
    if context.bars_since_open > LATEST_ENTRY_MINUTES:
        return
    
    # Check for breakouts
    check_breakout_entry(context, data, current_price, prices, volume)


def check_breakout_entry(context, data, price, prices, volume):
    """Check for and execute breakout entries."""
    
    range_high = context.opening_range_high
    range_low = context.opening_range_low
    range_size = range_high - range_low
    
    min_distance = price * MIN_BREAKOUT_DISTANCE_PCT
    
    # Multi-timeframe trend
    if USE_MTF_TREND:
        try:
            daily_prices = data.history(context.asset, 'close', DAILY_TREND_EMA + 5, '1d')
            daily_ema = daily_prices.ewm(span=DAILY_TREND_EMA, adjust=False).mean()
            daily_trend_bullish = daily_prices.iloc[-1] > daily_ema.iloc[-1]
        except:
            daily_trend_bullish = True
        
        intraday_ema = prices.ewm(span=min(INTRADAY_TREND_EMA, len(prices) - 1), 
                                  adjust=False).mean()
        intraday_trend_bullish = prices.iloc[-1] > intraday_ema.iloc[-1]
    else:
        daily_trend_bullish = True
        intraday_trend_bullish = True
    
    # Long breakout
    if price > range_high + min_distance:
        # Validate statistically
        is_valid, price_z, vol_z = validate_breakout_statistically(
            prices, volume, price, 1
        )
        
        if not is_valid:
            return
        
        # MTF alignment
        if REQUIRE_TREND_ALIGNMENT and USE_MTF_TREND:
            if not daily_trend_bullish or not intraday_trend_bullish:
                return
        
        # Check for level confluence
        near_level = False
        if USE_MULTI_LEVEL:
            for level in context.detected_levels:
                if level['type'] == 'resistance':
                    if abs(price - level['price']) < range_size * 0.5:
                        near_level = True
                        break
        
        # Volume profile check
        near_hvn = True
        if USE_VOLUME_PROFILE and context.volume_profile:
            hvn = find_high_volume_nodes(context.volume_profile, HIGH_VOLUME_NODE_THRESHOLD)
            near_hvn = any(abs(price - node['price']) < range_size * 0.3 for node in hvn)
            
            if TRADE_NEAR_HVN and not near_hvn:
                return
        
        execute_entry(context, data, price, 1, range_low)
        return
    
    # Short breakout (can be enabled)
    # if price < range_low - min_distance:
    #     ... similar logic


def execute_entry(context, data, price, direction, stop_reference):
    """Execute breakout entry."""
    
    atr = context.current_atr if context.current_atr > 0 else price * 0.01
    
    # Calculate stop
    if INITIAL_STOP_AT_RANGE:
        if direction == 1:
            stop = context.opening_range_low
        else:
            stop = context.opening_range_high
    else:
        stop = price - (atr * STOP_ATR_MULT * direction)
    
    context.stop_price = stop
    
    # Position sizing
    if USE_BREAKOUT_SCALING:
        position_size = compute_risk_based_size(context, price, stop) * INITIAL_ENTRY_PCT
    else:
        position_size = compute_risk_based_size(context, price, stop)
    
    # Target
    context.target_price = price + (atr * PROFIT_TARGET_ATR * direction)
    
    # Execute
    if direction == 1:
        order_target_percent(context.asset, position_size)
    else:
        order_target_percent(context.asset, -position_size)
    
    context.in_position = True
    context.position_side = direction
    context.entry_price = price
    context.highest_since_entry = price
    context.lowest_since_entry = price
    context.scale_ins = 0
    context.trades_today += 1
    context.breakeven_activated = False
    
    record(entry=direction)


def manage_position(context, data, price):
    """Manage existing position."""
    
    # Update tracking
    context.highest_since_entry = max(context.highest_since_entry, price)
    context.lowest_since_entry = min(context.lowest_since_entry, price)
    
    atr = context.current_atr if context.current_atr > 0 else price * 0.01
    
    should_exit = False
    should_scale = False
    
    if context.position_side == 1:  # Long
        # Stop loss
        if price <= context.stop_price:
            should_exit = True
        
        # Breakeven stop
        if USE_BREAKEVEN_STOP and not context.breakeven_activated:
            if price >= context.entry_price + (atr * BREAKEVEN_TRIGGER_ATR):
                context.stop_price = context.entry_price
                context.breakeven_activated = True
        
        # Trailing stop
        if USE_TRAILING_STOP:
            trail = context.highest_since_entry - (atr * TRAILING_STOP_ATR)
            if trail > context.stop_price:
                context.stop_price = trail
            
            if price <= context.stop_price:
                should_exit = True
        
        # Profit target
        if price >= context.target_price:
            should_exit = True
        
        # Scale in on confirmation
        if USE_BREAKOUT_SCALING and context.scale_ins < MAX_SCALE_INS:
            if price > context.entry_price * 1.005:  # 0.5% above entry
                should_scale = True
        
        # Failed breakout detection
        if TRADE_FAILED_BREAKOUTS:
            retrace = (context.highest_since_entry - price) / (context.highest_since_entry - context.entry_price)
            if retrace > FAILED_BREAKOUT_THRESHOLD:
                should_exit = True
    
    if should_scale and not should_exit:
        current_position = context.portfolio.positions.get(context.asset)
        if current_position:
            add_size = compute_risk_based_size(context, price, context.stop_price) * CONFIRMATION_ENTRY_PCT
            current_pct = (current_position.amount * price) / context.portfolio.portfolio_value
            new_pct = min(current_pct + add_size, MAX_POSITION)
            
            order_target_percent(context.asset, new_pct)
            context.scale_ins += 1
            record(scale_in=1)
    
    if should_exit:
        order_target_percent(context.asset, 0)
        reset_position_state(context)
        record(exit=1)


def flatten_positions(context, data):
    """Flatten all positions end of day."""
    
    if context.in_position:
        order_target_percent(context.asset, 0)
        reset_position_state(context)
        record(eod_flatten=1)


def reset_position_state(context):
    """Reset position tracking variables."""
    context.in_position = False
    context.position_side = 0
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.highest_since_entry = 0.0
    context.lowest_since_entry = float('inf')
    context.scale_ins = 0
    context.breakeven_activated = False


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 70)
    print("ADVANCED MULTI-LEVEL INTRADAY BREAKOUT RESULTS")
    print("=" * 70)
    
    returns = perf['returns']
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 70)
