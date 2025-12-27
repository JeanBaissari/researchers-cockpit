# Advanced MACD Momentum with Impulse System
# ==============================================================================
# A sophisticated momentum strategy featuring:
# - Elder's Impulse System combining MACD with EMA
# - Multi-timeframe MACD confirmation
# - Histogram divergence with price patterns
# - Momentum ranking for signal strength
# - Adaptive parameters based on volatility regime
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
ASSET_SYMBOL = 'QQQ'              # [PLACEHOLDER] Primary asset

# Primary MACD Parameters
MACD_FAST = 12                    # [PLACEHOLDER] Fast EMA (8-15)
MACD_SLOW = 26                    # [PLACEHOLDER] Slow EMA (20-35)
MACD_SIGNAL = 9                   # [PLACEHOLDER] Signal EMA (5-12)

# Multi-Timeframe MACD
USE_MTF_CONFIRMATION = True       # [PLACEHOLDER] Use multiple timeframes
MTF_FAST_MULT = 0.5               # [PLACEHOLDER] Fast TF multiplier
MTF_SLOW_MULT = 2.0               # [PLACEHOLDER] Slow TF multiplier
MIN_TF_AGREEMENT = 2              # [PLACEHOLDER] Min timeframes agreeing (1-3)

# Adaptive MACD Parameters
USE_ADAPTIVE_MACD = True          # [PLACEHOLDER] Adjust MACD by volatility
VOL_LOOKBACK = 20                 # [PLACEHOLDER] Volatility lookback
HIGH_VOL_FAST_MULT = 0.75         # [PLACEHOLDER] Fast period multiplier in high vol
LOW_VOL_FAST_MULT = 1.25          # [PLACEHOLDER] Fast period multiplier in low vol

# Elder's Impulse System
USE_IMPULSE_SYSTEM = True         # [PLACEHOLDER] Elder's Impulse System
IMPULSE_EMA_PERIOD = 13           # [PLACEHOLDER] EMA for impulse (10-20)
IMPULSE_REQUIRE_GREEN = True      # [PLACEHOLDER] Only trade on green bars

# Histogram Analysis
USE_HISTOGRAM_PATTERNS = True     # [PLACEHOLDER] Trade histogram patterns
HISTOGRAM_DIVERGENCE_LOOKBACK = 20  # [PLACEHOLDER] Divergence lookback
HISTOGRAM_MOMENTUM_BARS = 5       # [PLACEHOLDER] Bars for momentum analysis
HISTOGRAM_ACCELERATION = True     # [PLACEHOLDER] Trade on histogram acceleration

# Signal Strength / Momentum Ranking
USE_MOMENTUM_RANKING = True       # [PLACEHOLDER] Rank signal strength
MOMENTUM_COMPONENTS = ['histogram', 'slope', 'divergence']  # [PLACEHOLDER] Components
STRONG_SIGNAL_THRESHOLD = 0.7     # [PLACEHOLDER] Threshold for strong signal (0.5-0.9)
WEAK_SIGNAL_THRESHOLD = 0.3       # [PLACEHOLDER] Threshold for weak signal (0.2-0.5)

# Trend Confirmation
USE_TREND_FILTER = True           # [PLACEHOLDER] Trend filter
TREND_EMA = 50                    # [PLACEHOLDER] Trend EMA period
ADX_PERIOD = 14                   # [PLACEHOLDER] ADX period
MIN_ADX = 20                      # [PLACEHOLDER] Minimum ADX for trending

# Zero Line Analysis
ZERO_LINE_PROXIMITY = 0.001       # [PLACEHOLDER] Near zero threshold
ZERO_CROSS_CONFIRM_BARS = 2       # [PLACEHOLDER] Bars to confirm zero cross

# Position Sizing
BASE_POSITION = 0.80              # [PLACEHOLDER] Base position size
SIGNAL_STRENGTH_SIZING = True     # [PLACEHOLDER] Size by signal strength
MAX_POSITION = 1.0                # [PLACEHOLDER] Maximum position
MIN_POSITION = 0.30               # [PLACEHOLDER] Minimum position
VOLATILITY_SCALING = True         # [PLACEHOLDER] Scale by volatility
TARGET_VOLATILITY = 0.15          # [PLACEHOLDER] Target annual vol

# Risk Management
USE_MACD_BASED_STOPS = True       # [PLACEHOLDER] MACD-based exits
STOP_ON_SIGNAL_CROSS = True       # [PLACEHOLDER] Exit on bearish cross
STOP_ON_HISTOGRAM_FLIP = True     # [PLACEHOLDER] Exit on histogram sign change
ATR_STOP_MULT = 2.5               # [PLACEHOLDER] ATR stop multiplier
TRAILING_STOP_ATR = 2.0           # [PLACEHOLDER] Trailing stop ATR mult
PROFIT_TARGET_ATR = 4.0           # [PLACEHOLDER] Profit target ATR mult

# Impulse Exit Rules
IMPULSE_EXIT_ON_RED = True        # [PLACEHOLDER] Exit on red impulse bar
IMPULSE_EXIT_ON_BLUE = False      # [PLACEHOLDER] Exit on blue (neutral) bar

# Divergence Trading
TRADE_DIVERGENCE = True           # [PLACEHOLDER] Trade on divergence
BULLISH_DIV_ENTRY = True          # [PLACEHOLDER] Enter on bullish divergence
BEARISH_DIV_EXIT = True           # [PLACEHOLDER] Exit on bearish divergence

# Execution
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission
SLIPPAGE_BPS = 5.0                # [PLACEHOLDER] Slippage bps


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Initialize strategy."""
    
    context.asset = symbol(ASSET_SYMBOL)
    
    # Position state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.signal_strength = 0.0
    context.bars_since_zero_cross = 0
    
    set_benchmark(context.asset)
    
    set_commission(us_equities=commission.PerShare(
        cost=COMMISSION_PER_SHARE, min_trade_cost=1.0
    ))
    
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(
        basis_points=SLIPPAGE_BPS, volume_limit=0.1
    ))
    
    schedule_function(execute_strategy, date_rules.every_day(),
                     time_rules.market_open(minutes=REBALANCE_TIME))


def compute_ema(prices, period):
    """Exponential moving average."""
    return prices.ewm(span=period, adjust=False).mean()


def compute_macd(prices, fast, slow, signal):
    """Calculate MACD components."""
    fast_ema = compute_ema(prices, int(fast))
    slow_ema = compute_ema(prices, int(slow))
    
    macd_line = fast_ema - slow_ema
    signal_line = compute_ema(macd_line, int(signal))
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram,
        'fast_ema': fast_ema,
        'slow_ema': slow_ema
    }


def compute_multi_timeframe_macd(prices, base_fast, base_slow, base_signal):
    """Compute MACD on multiple effective timeframes."""
    timeframes = {}
    
    # Fast timeframe (shorter periods)
    tf_fast = compute_macd(prices, 
                          base_fast * MTF_FAST_MULT,
                          base_slow * MTF_FAST_MULT,
                          base_signal * MTF_FAST_MULT)
    timeframes['fast'] = tf_fast
    
    # Base timeframe
    tf_base = compute_macd(prices, base_fast, base_slow, base_signal)
    timeframes['base'] = tf_base
    
    # Slow timeframe (longer periods)
    tf_slow = compute_macd(prices,
                          base_fast * MTF_SLOW_MULT,
                          base_slow * MTF_SLOW_MULT,
                          base_signal * MTF_SLOW_MULT)
    timeframes['slow'] = tf_slow
    
    return timeframes


def compute_impulse_system(prices, high, low, macd_histogram, ema_period):
    """Elder's Impulse System: combines EMA slope + MACD histogram."""
    ema = compute_ema(prices, ema_period)
    ema_slope = ema.diff()
    hist_slope = macd_histogram.diff()
    
    # Green: EMA rising AND histogram rising
    # Red: EMA falling AND histogram falling  
    # Blue: Mixed signals
    
    impulse = pd.Series(index=prices.index, dtype='object')
    
    for i in range(1, len(prices)):
        if ema_slope.iloc[i] > 0 and hist_slope.iloc[i] > 0:
            impulse.iloc[i] = 'green'
        elif ema_slope.iloc[i] < 0 and hist_slope.iloc[i] < 0:
            impulse.iloc[i] = 'red'
        else:
            impulse.iloc[i] = 'blue'
    
    return impulse, ema_slope, hist_slope


def detect_histogram_patterns(histogram, prices, lookback):
    """Detect histogram patterns and divergences."""
    patterns = {
        'bullish_divergence': False,
        'bearish_divergence': False,
        'histogram_rising': False,
        'histogram_falling': False,
        'positive_momentum': False,
        'negative_momentum': False,
        'acceleration': 0.0
    }
    
    if len(histogram) < lookback:
        return patterns
    
    recent_hist = histogram.iloc[-lookback:]
    recent_prices = prices.iloc[-lookback:]
    
    # Histogram momentum
    patterns['histogram_rising'] = histogram.iloc[-1] > histogram.iloc[-2]
    patterns['histogram_falling'] = histogram.iloc[-1] < histogram.iloc[-2]
    
    # Acceleration (second derivative)
    hist_change = histogram.diff()
    patterns['acceleration'] = hist_change.iloc[-1] - hist_change.iloc[-2]
    
    # Positive/negative momentum over bars
    hist_sum = histogram.iloc[-HISTOGRAM_MOMENTUM_BARS:].sum()
    patterns['positive_momentum'] = hist_sum > 0
    patterns['negative_momentum'] = hist_sum < 0
    
    # Divergence detection
    # Find histogram lows
    hist_lows = []
    price_lows = []
    
    for i in range(2, len(recent_hist) - 2):
        if (recent_hist.iloc[i] < recent_hist.iloc[i-1] and 
            recent_hist.iloc[i] < recent_hist.iloc[i+1] and
            recent_hist.iloc[i] < 0):
            hist_lows.append((i, recent_hist.iloc[i]))
            price_lows.append((i, recent_prices.iloc[i]))
    
    if len(hist_lows) >= 2:
        # Bullish divergence: price lower low, histogram higher low
        if price_lows[-1][1] < price_lows[-2][1] and hist_lows[-1][1] > hist_lows[-2][1]:
            patterns['bullish_divergence'] = True
    
    # Find histogram highs for bearish divergence
    hist_highs = []
    price_highs = []
    
    for i in range(2, len(recent_hist) - 2):
        if (recent_hist.iloc[i] > recent_hist.iloc[i-1] and 
            recent_hist.iloc[i] > recent_hist.iloc[i+1] and
            recent_hist.iloc[i] > 0):
            hist_highs.append((i, recent_hist.iloc[i]))
            price_highs.append((i, recent_prices.iloc[i]))
    
    if len(hist_highs) >= 2:
        # Bearish divergence: price higher high, histogram lower high
        if price_highs[-1][1] > price_highs[-2][1] and hist_highs[-1][1] < hist_highs[-2][1]:
            patterns['bearish_divergence'] = True
    
    return patterns


def compute_signal_strength(mtf_signals, patterns, impulse, adx):
    """Compute composite signal strength score."""
    scores = []
    
    # Multi-timeframe agreement
    bullish_count = sum(1 for tf in mtf_signals.values() 
                        if tf['histogram'].iloc[-1] > 0)
    tf_score = bullish_count / len(mtf_signals)
    scores.append(tf_score)
    
    # Histogram momentum
    if patterns['positive_momentum'] and patterns['histogram_rising']:
        scores.append(1.0)
    elif patterns['positive_momentum']:
        scores.append(0.6)
    else:
        scores.append(0.2)
    
    # Histogram acceleration
    if patterns['acceleration'] > 0:
        scores.append(min(1.0, 0.5 + patterns['acceleration'] * 10))
    else:
        scores.append(max(0.0, 0.5 + patterns['acceleration'] * 10))
    
    # Impulse system
    if impulse.iloc[-1] == 'green':
        scores.append(1.0)
    elif impulse.iloc[-1] == 'blue':
        scores.append(0.5)
    else:
        scores.append(0.0)
    
    # ADX trend strength
    adx_score = min(1.0, adx / 50)  # Normalize ADX
    scores.append(adx_score)
    
    # Divergence bonus
    if patterns['bullish_divergence']:
        scores.append(1.0)
    else:
        scores.append(0.5)
    
    return np.mean(scores)


def get_adaptive_parameters(volatility, vol_percentile):
    """Adjust MACD parameters based on volatility."""
    if not USE_ADAPTIVE_MACD:
        return MACD_FAST, MACD_SLOW, MACD_SIGNAL
    
    if vol_percentile > 0.8:  # High volatility
        fast = MACD_FAST * HIGH_VOL_FAST_MULT
        slow = MACD_SLOW * HIGH_VOL_FAST_MULT
        signal = MACD_SIGNAL * HIGH_VOL_FAST_MULT
    elif vol_percentile < 0.2:  # Low volatility
        fast = MACD_FAST * LOW_VOL_FAST_MULT
        slow = MACD_SLOW * LOW_VOL_FAST_MULT
        signal = MACD_SIGNAL * LOW_VOL_FAST_MULT
    else:
        fast, slow, signal = MACD_FAST, MACD_SLOW, MACD_SIGNAL
    
    return max(5, fast), max(15, slow), max(3, signal)


def compute_position_size(signal_strength, volatility, target_vol):
    """Calculate position size based on signal strength and volatility."""
    size = BASE_POSITION
    
    # Signal strength sizing
    if SIGNAL_STRENGTH_SIZING:
        if signal_strength >= STRONG_SIGNAL_THRESHOLD:
            size = size * 1.2
        elif signal_strength <= WEAK_SIGNAL_THRESHOLD:
            size = size * 0.6
        else:
            size = size * (0.6 + (signal_strength - WEAK_SIGNAL_THRESHOLD) * 1.5)
    
    # Volatility scaling
    if VOLATILITY_SCALING and volatility > 0:
        vol_scalar = target_vol / volatility
        size = size * vol_scalar
    
    return np.clip(size, MIN_POSITION, MAX_POSITION)


def compute_atr(high, low, close, period):
    """Average True Range."""
    tr = pd.concat([high - low,
                    abs(high - close.shift(1)),
                    abs(low - close.shift(1))], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(high, low, close, period):
    """Average Directional Index."""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    tr = pd.concat([high - low,
                    abs(high - close.shift(1)),
                    abs(low - close.shift(1))], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)
    adx = dx.rolling(period).mean()
    
    return adx, plus_di, minus_di


def execute_strategy(context, data):
    """Main strategy execution."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get data
    lookback = max(MACD_SLOW * MTF_SLOW_MULT + 50, TREND_EMA + 20)
    lookback = int(lookback)
    
    prices = data.history(context.asset, 'price', lookback, '1d')
    high = data.history(context.asset, 'high', lookback, '1d')
    low = data.history(context.asset, 'low', lookback, '1d')
    close = data.history(context.asset, 'close', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    current_price = prices.iloc[-1]
    returns = prices.pct_change().dropna()
    
    # Volatility
    volatility = returns.rolling(VOL_LOOKBACK).std() * np.sqrt(252)
    current_vol = volatility.iloc[-1]
    vol_percentile = volatility.rank(pct=True).iloc[-1]
    
    # Adaptive MACD parameters
    fast, slow, signal = get_adaptive_parameters(current_vol, vol_percentile)
    
    # Multi-timeframe MACD
    mtf = compute_multi_timeframe_macd(prices, fast, slow, signal)
    base_macd = mtf['base']
    
    # Impulse system
    impulse, ema_slope, hist_slope = compute_impulse_system(
        prices, high, low, base_macd['histogram'], IMPULSE_EMA_PERIOD
    )
    current_impulse = impulse.iloc[-1]
    
    # Histogram patterns
    patterns = detect_histogram_patterns(
        base_macd['histogram'], prices, HISTOGRAM_DIVERGENCE_LOOKBACK
    )
    
    # ADX
    adx, plus_di, minus_di = compute_adx(high, low, close, ADX_PERIOD)
    current_adx = adx.iloc[-1]
    
    # ATR
    atr = compute_atr(high, low, close, 14)
    current_atr = atr.iloc[-1]
    
    # Signal strength
    signal_strength = compute_signal_strength(mtf, patterns, impulse, current_adx)
    context.signal_strength = signal_strength
    
    # Trend filter
    trend_ema = compute_ema(prices, TREND_EMA)
    trend_bullish = current_price > trend_ema.iloc[-1]
    
    # MTF agreement
    bullish_tf_count = sum(1 for tf_name, tf in mtf.items() 
                          if tf['histogram'].iloc[-1] > 0)
    
    # Zero line tracking
    if abs(base_macd['macd'].iloc[-1]) < ZERO_LINE_PROXIMITY * current_price:
        context.bars_since_zero_cross = 0
    else:
        context.bars_since_zero_cross += 1
    
    # Record metrics
    record(
        price=current_price,
        macd=base_macd['macd'].iloc[-1],
        signal=base_macd['signal'].iloc[-1],
        histogram=base_macd['histogram'].iloc[-1],
        impulse=1 if current_impulse == 'green' else (-1 if current_impulse == 'red' else 0),
        signal_strength=signal_strength,
        adx=current_adx
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Entry Logic
    if not context.in_position:
        should_enter = False
        
        # Primary entry: histogram cross with confirmation
        macd_bullish = base_macd['macd'].iloc[-1] > base_macd['signal'].iloc[-1]
        prev_macd_bullish = base_macd['macd'].iloc[-2] > base_macd['signal'].iloc[-2]
        
        bullish_cross = macd_bullish and not prev_macd_bullish
        
        if bullish_cross:
            should_enter = True
        
        # Histogram pattern entry
        if USE_HISTOGRAM_PATTERNS:
            if HISTOGRAM_ACCELERATION and patterns['acceleration'] > 0:
                if patterns['positive_momentum']:
                    should_enter = True
        
        # Divergence entry
        if TRADE_DIVERGENCE and BULLISH_DIV_ENTRY:
            if patterns['bullish_divergence']:
                should_enter = True
        
        # Apply filters
        if should_enter:
            # MTF confirmation
            if USE_MTF_CONFIRMATION and bullish_tf_count < MIN_TF_AGREEMENT:
                should_enter = False
            
            # Impulse filter
            if USE_IMPULSE_SYSTEM and IMPULSE_REQUIRE_GREEN:
                if current_impulse != 'green':
                    should_enter = False
            
            # Trend filter
            if USE_TREND_FILTER and not trend_bullish:
                should_enter = False
            
            # ADX filter
            if current_adx < MIN_ADX:
                should_enter = False
            
            # Signal strength filter
            if signal_strength < WEAK_SIGNAL_THRESHOLD:
                should_enter = False
        
        if should_enter:
            position_size = compute_position_size(signal_strength, current_vol, TARGET_VOLATILITY)
            order_target_percent(context.asset, position_size)
            
            context.in_position = True
            context.entry_price = current_price
            context.highest_price = current_price
            context.stop_price = current_price - (current_atr * ATR_STOP_MULT)
            context.target_price = current_price + (current_atr * PROFIT_TARGET_ATR)
            
            record(entry=1)
            return
    
    # Exit Logic
    if context.in_position:
        context.highest_price = max(context.highest_price, current_price)
        
        should_exit = False
        
        # Signal line cross
        if STOP_ON_SIGNAL_CROSS:
            macd_bearish = base_macd['macd'].iloc[-1] < base_macd['signal'].iloc[-1]
            prev_macd_bearish = base_macd['macd'].iloc[-2] < base_macd['signal'].iloc[-2]
            
            if macd_bearish and not prev_macd_bearish:
                should_exit = True
        
        # Histogram flip
        if STOP_ON_HISTOGRAM_FLIP:
            if base_macd['histogram'].iloc[-1] < 0 and base_macd['histogram'].iloc[-2] >= 0:
                should_exit = True
        
        # Impulse exit
        if USE_IMPULSE_SYSTEM:
            if IMPULSE_EXIT_ON_RED and current_impulse == 'red':
                should_exit = True
            if IMPULSE_EXIT_ON_BLUE and current_impulse == 'blue':
                should_exit = True
        
        # Bearish divergence exit
        if TRADE_DIVERGENCE and BEARISH_DIV_EXIT:
            if patterns['bearish_divergence']:
                should_exit = True
        
        # Stop loss
        if current_price <= context.stop_price:
            should_exit = True
        
        # Trailing stop
        trail_stop = context.highest_price - (current_atr * TRAILING_STOP_ATR)
        if trail_stop > context.stop_price and current_price < trail_stop:
            should_exit = True
        
        # Profit target
        if current_price >= context.target_price:
            should_exit = True
        
        if should_exit:
            order_target_percent(context.asset, 0)
            
            context.in_position = False
            context.entry_price = 0.0
            context.highest_price = 0.0
            context.stop_price = 0.0
            context.target_price = 0.0
            
            record(exit=1)
            return
    
    record(entry=0, exit=0)


def handle_data(context, data):
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 70)
    print("ADVANCED MACD MOMENTUM WITH IMPULSE SYSTEM RESULTS")
    print("=" * 70)
    
    returns = perf['returns']
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    # Win rate estimation
    daily_wins = (returns > 0).sum()
    daily_total = len(returns[returns != 0])
    win_rate = daily_wins / daily_total if daily_total > 0 else 0
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Daily Win Rate: {win_rate:.2%}")
    print("=" * 70)
