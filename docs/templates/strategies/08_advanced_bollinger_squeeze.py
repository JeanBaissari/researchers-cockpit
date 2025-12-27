# Advanced Bollinger Bands Strategy with Keltner Squeeze
# ==============================================================================
# A sophisticated volatility strategy featuring:
# - Bollinger Band / Keltner Channel squeeze detection
# - Adaptive band parameters based on market regime
# - Multi-factor confirmation (momentum, volume, trend)
# - Volatility breakout anticipation
# - Dynamic position sizing with volatility targeting
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
ASSET_SYMBOL = 'SPY'              # [PLACEHOLDER] Primary asset

# Bollinger Band Parameters
BB_PERIOD = 20                    # [PLACEHOLDER] Bollinger period (15-25)
BB_STD = 2.0                      # [PLACEHOLDER] Standard deviations (1.5-2.5)
USE_ADAPTIVE_BANDS = True         # [PLACEHOLDER] Adjust BB parameters dynamically
MIN_BB_PERIOD = 10                # [PLACEHOLDER] Minimum period in high vol
MAX_BB_PERIOD = 30                # [PLACEHOLDER] Maximum period in low vol

# Keltner Channel Parameters
KC_PERIOD = 20                    # [PLACEHOLDER] Keltner period (15-25)
KC_ATR_MULT = 1.5                 # [PLACEHOLDER] ATR multiplier (1.0-2.0)
ATR_PERIOD = 14                   # [PLACEHOLDER] ATR calculation period

# Squeeze Detection
SQUEEZE_LOOKBACK = 6              # [PLACEHOLDER] Bars BB inside KC for squeeze
MIN_SQUEEZE_BARS = 4              # [PLACEHOLDER] Minimum squeeze duration (3-8)
SQUEEZE_MOMENTUM_PERIOD = 12      # [PLACEHOLDER] Momentum oscillator period
USE_SQUEEZE_ANTICIPATION = True   # [PLACEHOLDER] Enter before squeeze fires

# Strategy Mode
STRATEGY_MODE = 'adaptive'        # [PLACEHOLDER] 'squeeze', 'mean_reversion', 'adaptive'
ADAPTIVE_THRESHOLD_ADX = 25       # [PLACEHOLDER] ADX threshold for mode switch

# Momentum Confirmation
USE_MOMENTUM_FILTER = True        # [PLACEHOLDER] Require momentum confirmation
MOMENTUM_PERIOD = 14              # [PLACEHOLDER] Momentum lookback
MOMENTUM_THRESHOLD = 0            # [PLACEHOLDER] Min momentum for entry

# Volume Confirmation
USE_VOLUME_FILTER = True          # [PLACEHOLDER] Require volume spike
VOLUME_LOOKBACK = 20              # [PLACEHOLDER] Volume average period
VOLUME_SPIKE_MULT = 1.3           # [PLACEHOLDER] Volume spike multiplier

# Trend Filter
USE_TREND_FILTER = True           # [PLACEHOLDER] Trade with trend only
TREND_EMA_PERIOD = 50             # [PLACEHOLDER] Trend EMA (40-100)
ADX_PERIOD = 14                   # [PLACEHOLDER] ADX period

# Position Sizing
BASE_POSITION = 0.80              # [PLACEHOLDER] Base position size
USE_VOLATILITY_SIZING = True      # [PLACEHOLDER] Scale by volatility
VOLATILITY_TARGET = 0.12          # [PLACEHOLDER] Target portfolio vol
MAX_POSITION = 1.20               # [PLACEHOLDER] Maximum position (leverage)
MIN_POSITION = 0.30               # [PLACEHOLDER] Minimum position

# Squeeze Sizing Boost
SQUEEZE_SIZE_MULTIPLIER = 1.25    # [PLACEHOLDER] Size boost for squeeze trades
BANDWIDTH_SIZING = True           # [PLACEHOLDER] Scale by bandwidth percentile

# Risk Management
USE_ATR_STOPS = True              # [PLACEHOLDER] ATR-based stops
STOP_ATR_MULT = 2.0               # [PLACEHOLDER] ATR multiplier for stops
INITIAL_STOP_PCT = 0.05           # [PLACEHOLDER] Initial stop percentage
USE_CHANDELIER_EXIT = True        # [PLACEHOLDER] Trailing chandelier exit
CHANDELIER_ATR_MULT = 3.0         # [PLACEHOLDER] Chandelier ATR mult
PROFIT_TARGET_ATR = 3.0           # [PLACEHOLDER] Profit target in ATRs

# Mean Reversion Exits
MR_EXIT_AT_MIDDLE = True          # [PLACEHOLDER] Exit at middle band
MR_EXIT_AT_OPPOSITE = False       # [PLACEHOLDER] Exit at opposite band
MR_PARTIAL_EXIT_PCT = 0.5         # [PLACEHOLDER] Partial exit percentage

# Execution
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission
SLIPPAGE_VOLUME_LIMIT = 0.025     # [PLACEHOLDER] Volume limit
SLIPPAGE_PRICE_IMPACT = 0.1       # [PLACEHOLDER] Price impact


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Initialize strategy."""
    
    context.asset = symbol(ASSET_SYMBOL)
    
    # Position state
    context.in_position = False
    context.position_side = 0  # 1 = long, -1 = short
    context.entry_price = 0.0
    context.stop_price = 0.0
    context.target_price = 0.0
    context.highest_since_entry = 0.0
    context.lowest_since_entry = float('inf')
    context.partial_exit_done = False
    
    # Squeeze state
    context.squeeze_bars = 0
    context.squeeze_fired = False
    context.last_squeeze_direction = 0
    
    # Current mode
    context.current_mode = 'mean_reversion'
    
    set_benchmark(context.asset)
    
    set_commission(us_equities=commission.PerShare(
        cost=COMMISSION_PER_SHARE, min_trade_cost=1.0
    ))
    
    set_slippage(us_equities=slippage.VolumeShareSlippage(
        volume_limit=SLIPPAGE_VOLUME_LIMIT,
        price_impact=SLIPPAGE_PRICE_IMPACT
    ))
    
    schedule_function(execute_strategy, date_rules.every_day(),
                     time_rules.market_open(minutes=REBALANCE_TIME))
    
    schedule_function(manage_exits, date_rules.every_day(),
                     time_rules.market_open(minutes=5))


def compute_bollinger_bands(prices, period, std_dev):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    
    bandwidth = (upper - lower) / sma
    percent_b = (prices - lower) / (upper - lower).replace(0, np.inf)
    
    return {
        'middle': sma, 'upper': upper, 'lower': lower,
        'bandwidth': bandwidth, 'percent_b': percent_b
    }


def compute_keltner_channels(prices, high, low, close, kc_period, atr_mult, atr_period):
    """Calculate Keltner Channels."""
    typical_price = (high + low + close) / 3
    ema = typical_price.ewm(span=kc_period, adjust=False).mean()
    
    # ATR
    tr = pd.concat([high - low,
                    abs(high - close.shift(1)),
                    abs(low - close.shift(1))], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()
    
    upper = ema + (atr_mult * atr)
    lower = ema - (atr_mult * atr)
    
    return {'middle': ema, 'upper': upper, 'lower': lower, 'atr': atr}


def detect_squeeze(bb, kc):
    """Detect Bollinger Band squeeze (BB inside KC)."""
    bb_inside_kc = (bb['lower'] > kc['lower']) & (bb['upper'] < kc['upper'])
    return bb_inside_kc


def compute_momentum_oscillator(prices, period):
    """Momentum oscillator for squeeze direction."""
    highest = prices.rolling(period).max()
    lowest = prices.rolling(period).min()
    
    midline = (highest + lowest) / 2
    
    # Linear regression of price vs midline
    momentum = prices - midline
    
    # Smooth momentum
    momentum_smooth = momentum.rolling(3).mean()
    
    return momentum_smooth


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


def get_adaptive_parameters(volatility, vol_percentile, adx):
    """Adjust BB parameters based on market conditions."""
    if not USE_ADAPTIVE_BANDS:
        return BB_PERIOD, BB_STD
    
    # Adjust period: shorter in high vol, longer in low vol
    period = BB_PERIOD
    if vol_percentile > 0.8:
        period = MIN_BB_PERIOD
    elif vol_percentile < 0.2:
        period = MAX_BB_PERIOD
    else:
        # Linear interpolation
        period = MAX_BB_PERIOD - (vol_percentile * (MAX_BB_PERIOD - MIN_BB_PERIOD))
    
    # Adjust std dev: wider in trending, tighter in ranging
    std_dev = BB_STD
    if adx > 30:
        std_dev = BB_STD * 1.1  # Slightly wider bands in trends
    elif adx < 20:
        std_dev = BB_STD * 0.9  # Tighter bands in ranges
    
    return int(period), std_dev


def determine_strategy_mode(adx, bandwidth_percentile):
    """Determine whether to use squeeze or mean reversion mode."""
    if STRATEGY_MODE != 'adaptive':
        return STRATEGY_MODE
    
    if adx > ADAPTIVE_THRESHOLD_ADX:
        return 'squeeze'  # Trending market - trade breakouts
    else:
        return 'mean_reversion'  # Ranging market - fade extremes


def compute_position_size(context, atr, bandwidth_percentile, is_squeeze):
    """Calculate position size."""
    size = BASE_POSITION
    
    # Volatility targeting
    if USE_VOLATILITY_SIZING and atr > 0:
        current_vol = atr / context.entry_price if context.entry_price > 0 else 0.01
        annual_vol = current_vol * np.sqrt(252)
        
        if annual_vol > 0:
            vol_scalar = VOLATILITY_TARGET / annual_vol
            size = size * vol_scalar
    
    # Bandwidth sizing (tighter bands = larger potential move)
    if BANDWIDTH_SIZING:
        # Lower bandwidth percentile = squeeze forming = larger size
        band_scalar = 1 + (1 - bandwidth_percentile) * 0.3
        size = size * band_scalar
    
    # Squeeze boost
    if is_squeeze:
        size = size * SQUEEZE_SIZE_MULTIPLIER
    
    return np.clip(size, MIN_POSITION, MAX_POSITION)


def execute_strategy(context, data):
    """Main strategy execution."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get data
    lookback = max(BB_PERIOD + 50, KC_PERIOD + 50, TREND_EMA_PERIOD + 10)
    prices = data.history(context.asset, 'price', lookback, '1d')
    high = data.history(context.asset, 'high', lookback, '1d')
    low = data.history(context.asset, 'low', lookback, '1d')
    close = data.history(context.asset, 'close', lookback, '1d')
    volume = data.history(context.asset, 'volume', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    current_price = prices.iloc[-1]
    returns = prices.pct_change().dropna()
    
    # Volatility analysis
    volatility = returns.rolling(20).std() * np.sqrt(252)
    vol_percentile = volatility.rank(pct=True).iloc[-1]
    
    # ADX
    adx, plus_di, minus_di = compute_adx(high, low, close, ADX_PERIOD)
    current_adx = adx.iloc[-1]
    
    # Adaptive parameters
    bb_period, bb_std = get_adaptive_parameters(volatility.iloc[-1], vol_percentile, current_adx)
    
    # Compute indicators
    bb = compute_bollinger_bands(prices, bb_period, bb_std)
    kc = compute_keltner_channels(prices, high, low, close, KC_PERIOD, KC_ATR_MULT, ATR_PERIOD)
    
    current_bb = {k: v.iloc[-1] for k, v in bb.items()}
    current_kc = {k: v.iloc[-1] for k, v in kc.items()}
    current_atr = kc['atr'].iloc[-1]
    
    # Squeeze detection
    squeeze = detect_squeeze(bb, kc)
    in_squeeze = squeeze.iloc[-1]
    
    # Count consecutive squeeze bars
    if in_squeeze:
        context.squeeze_bars += 1
    else:
        if context.squeeze_bars >= MIN_SQUEEZE_BARS:
            context.squeeze_fired = True
        context.squeeze_bars = 0
    
    # Momentum for squeeze direction
    momentum = compute_momentum_oscillator(prices, SQUEEZE_MOMENTUM_PERIOD)
    current_momentum = momentum.iloc[-1]
    prev_momentum = momentum.iloc[-2]
    
    # Determine strategy mode
    context.current_mode = determine_strategy_mode(current_adx, current_bb['bandwidth'])
    
    # Trend filter
    trend_ema = prices.ewm(span=TREND_EMA_PERIOD, adjust=False).mean()
    trend_bullish = current_price > trend_ema.iloc[-1]
    
    # Volume filter
    avg_volume = volume.rolling(VOLUME_LOOKBACK).mean()
    volume_spike = volume.iloc[-1] > (avg_volume.iloc[-1] * VOLUME_SPIKE_MULT)
    
    # Bandwidth percentile for sizing
    bandwidth_percentile = bb['bandwidth'].rank(pct=True).iloc[-1]
    
    # Record metrics
    record(
        price=current_price,
        bb_upper=current_bb['upper'],
        bb_lower=current_bb['lower'],
        percent_b=current_bb['percent_b'],
        in_squeeze=1 if in_squeeze else 0,
        squeeze_bars=context.squeeze_bars,
        momentum=current_momentum,
        mode=hash(context.current_mode) % 10
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Entry logic
    if not context.in_position:
        should_enter = False
        entry_side = 0
        is_squeeze_trade = False
        
        if context.current_mode == 'squeeze':
            # Squeeze breakout logic
            if context.squeeze_fired or (USE_SQUEEZE_ANTICIPATION and context.squeeze_bars >= MIN_SQUEEZE_BARS):
                # Momentum determines direction
                if current_momentum > MOMENTUM_THRESHOLD and current_momentum > prev_momentum:
                    should_enter = True
                    entry_side = 1
                    is_squeeze_trade = True
                elif current_momentum < -MOMENTUM_THRESHOLD and current_momentum < prev_momentum:
                    should_enter = True
                    entry_side = -1
                    is_squeeze_trade = True
                
                context.squeeze_fired = False
        
        else:  # Mean reversion mode
            # Buy at lower band
            if current_bb['percent_b'] < 0.05:
                should_enter = True
                entry_side = 1
            # Sell at upper band
            elif current_bb['percent_b'] > 0.95:
                should_enter = True
                entry_side = -1
        
        # Apply filters
        if should_enter:
            if USE_MOMENTUM_FILTER and context.current_mode != 'squeeze':
                if entry_side == 1 and current_momentum < 0:
                    should_enter = False
                elif entry_side == -1 and current_momentum > 0:
                    should_enter = False
            
            if USE_VOLUME_FILTER and not volume_spike:
                should_enter = False
            
            if USE_TREND_FILTER and context.current_mode == 'squeeze':
                if entry_side == 1 and not trend_bullish:
                    should_enter = False
                elif entry_side == -1 and trend_bullish:
                    should_enter = False
        
        if should_enter and entry_side != 0:
            position_size = compute_position_size(context, current_atr, bandwidth_percentile, is_squeeze_trade)
            
            # Long only for now (can enable short by using entry_side)
            if entry_side == 1:
                order_target_percent(context.asset, position_size)
            
                context.in_position = True
                context.position_side = entry_side
                context.entry_price = current_price
                context.highest_since_entry = current_price
                context.lowest_since_entry = current_price
                context.partial_exit_done = False
                
                # Set stops and targets
                if USE_ATR_STOPS:
                    context.stop_price = current_price - (current_atr * STOP_ATR_MULT)
                else:
                    context.stop_price = current_price * (1 - INITIAL_STOP_PCT)
                
                context.target_price = current_price + (current_atr * PROFIT_TARGET_ATR)
                
                record(entry=1, entry_type=1 if is_squeeze_trade else 0)
                return
    
    record(entry=0)


def manage_exits(context, data):
    """Manage position exits."""
    
    if not context.in_position:
        return
    
    if not data.can_trade(context.asset):
        return
    
    prices = data.history(context.asset, 'price', BB_PERIOD + 10, '1d')
    high = data.history(context.asset, 'high', 20, '1d')
    low = data.history(context.asset, 'low', 20, '1d')
    close = data.history(context.asset, 'close', 20, '1d')
    
    current_price = prices.iloc[-1]
    
    # Update tracking
    context.highest_since_entry = max(context.highest_since_entry, current_price)
    context.lowest_since_entry = min(context.lowest_since_entry, current_price)
    
    # Current indicators
    bb = compute_bollinger_bands(prices, BB_PERIOD, BB_STD)
    kc = compute_keltner_channels(prices, high, low, close, KC_PERIOD, KC_ATR_MULT, ATR_PERIOD)
    current_atr = kc['atr'].iloc[-1]
    
    should_exit = False
    exit_portion = 1.0
    
    if context.position_side == 1:  # Long position
        # Stop loss
        if current_price <= context.stop_price:
            should_exit = True
        
        # Chandelier exit (trailing)
        if USE_CHANDELIER_EXIT:
            chandelier_stop = context.highest_since_entry - (current_atr * CHANDELIER_ATR_MULT)
            if current_price <= chandelier_stop and chandelier_stop > context.stop_price:
                should_exit = True
        
        # Profit target
        if current_price >= context.target_price:
            should_exit = True
        
        # Mean reversion exits
        if context.current_mode == 'mean_reversion':
            if MR_EXIT_AT_MIDDLE and not context.partial_exit_done:
                if current_price >= bb['middle'].iloc[-1]:
                    should_exit = True
                    exit_portion = MR_PARTIAL_EXIT_PCT
                    context.partial_exit_done = True
            
            if MR_EXIT_AT_OPPOSITE:
                if bb['percent_b'].iloc[-1] >= 0.95:
                    should_exit = True
                    exit_portion = 1.0
    
    if should_exit:
        current_position = context.portfolio.positions.get(context.asset)
        if current_position:
            if exit_portion < 1.0:
                # Partial exit
                new_amount = current_position.amount * (1 - exit_portion)
                order_target_percent(context.asset, 
                    (new_amount * current_price) / context.portfolio.portfolio_value)
            else:
                # Full exit
                order_target_percent(context.asset, 0)
                
                context.in_position = False
                context.position_side = 0
                context.entry_price = 0.0
                context.stop_price = 0.0
                context.target_price = 0.0
                context.partial_exit_done = False
        
        record(exit=1)
    else:
        record(exit=0)


def handle_data(context, data):
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 70)
    print("ADVANCED BOLLINGER BANDS WITH KELTNER SQUEEZE RESULTS")
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
