# Advanced Multi-Timeframe SMA Strategy
# ==============================================================================
# A sophisticated trend-following strategy with:
# - Multi-timeframe confirmation (short, medium, long-term alignment)
# - Volatility regime detection for adaptive positioning
# - Dynamic SMA periods based on market conditions
# - Risk parity position sizing with drawdown control
# - Trend strength filtering using ADX
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
ASSET_SYMBOL = 'SPY'              # [PLACEHOLDER] Primary asset to trade
HEDGE_SYMBOL = 'TLT'              # [PLACEHOLDER] Hedge asset (bonds/gold)
USE_HEDGE = True                  # [PLACEHOLDER] Enable hedging in risk-off

# Multi-Timeframe SMA Periods
SHORT_FAST_SMA = 5                # [PLACEHOLDER] Short-term fast (3-8)
SHORT_SLOW_SMA = 13               # [PLACEHOLDER] Short-term slow (10-20)
MEDIUM_FAST_SMA = 21              # [PLACEHOLDER] Medium-term fast (15-30)
MEDIUM_SLOW_SMA = 55              # [PLACEHOLDER] Medium-term slow (40-70)
LONG_FAST_SMA = 50                # [PLACEHOLDER] Long-term fast (40-60)
LONG_SLOW_SMA = 200               # [PLACEHOLDER] Long-term slow (150-250)

# Adaptive Period Settings
USE_ADAPTIVE_PERIODS = True       # [PLACEHOLDER] Dynamically adjust SMA periods
VOLATILITY_LOOKBACK = 20          # [PLACEHOLDER] Lookback for volatility calc
PERIOD_EXPANSION_FACTOR = 1.5     # [PLACEHOLDER] Expand periods in high vol (1.2-2.0)
PERIOD_CONTRACTION_FACTOR = 0.75  # [PLACEHOLDER] Contract in low vol (0.5-0.9)

# Regime Detection
REGIME_LOOKBACK = 60              # [PLACEHOLDER] Lookback for regime detection (40-100)
HIGH_VOL_THRESHOLD = 0.20         # [PLACEHOLDER] Annualized vol threshold (0.15-0.30)
LOW_VOL_THRESHOLD = 0.10          # [PLACEHOLDER] Low vol threshold (0.05-0.12)
TREND_REGIME_THRESHOLD = 0.02     # [PLACEHOLDER] Min trend slope (0.01-0.05)

# ADX Trend Strength Filter
USE_ADX_FILTER = True             # [PLACEHOLDER] Require strong trend
ADX_PERIOD = 14                   # [PLACEHOLDER] ADX calculation period (10-20)
ADX_THRESHOLD = 25                # [PLACEHOLDER] Minimum ADX to trade (20-35)
ADX_STRONG_TREND = 40             # [PLACEHOLDER] Strong trend threshold (35-50)

# Multi-Timeframe Confirmation
REQUIRE_ALL_TIMEFRAMES = False    # [PLACEHOLDER] Require all TFs aligned
MIN_TIMEFRAMES_ALIGNED = 2        # [PLACEHOLDER] Minimum TFs for entry (1-3)
WEIGHT_SHORT_TF = 0.5             # [PLACEHOLDER] Weight for short TF signal
WEIGHT_MEDIUM_TF = 0.3            # [PLACEHOLDER] Weight for medium TF signal
WEIGHT_LONG_TF = 0.2              # [PLACEHOLDER] Weight for long TF signal

# Position Sizing - Risk Parity
BASE_POSITION_SIZE = 0.80         # [PLACEHOLDER] Base allocation (0.5-1.0)
USE_VOLATILITY_TARGETING = True   # [PLACEHOLDER] Scale by volatility
TARGET_VOLATILITY = 0.12          # [PLACEHOLDER] Target annual vol (0.08-0.20)
MAX_LEVERAGE = 1.5                # [PLACEHOLDER] Maximum leverage (1.0-2.0)
MIN_POSITION_SIZE = 0.20          # [PLACEHOLDER] Minimum position (0.1-0.4)

# Drawdown Control
USE_DRAWDOWN_CONTROL = True       # [PLACEHOLDER] Reduce risk in drawdown
MAX_DRAWDOWN_THRESHOLD = 0.10     # [PLACEHOLDER] DD to start reducing (0.05-0.15)
CRITICAL_DRAWDOWN = 0.20          # [PLACEHOLDER] DD to go defensive (0.15-0.30)
DRAWDOWN_REDUCTION_FACTOR = 0.5   # [PLACEHOLDER] Position reduction (0.3-0.7)

# Risk Management
USE_VOLATILITY_STOP = True        # [PLACEHOLDER] ATR-based stop loss
STOP_ATR_MULTIPLIER = 3.0         # [PLACEHOLDER] ATR multiple for stop (2.0-4.0)
USE_TIME_STOP = True              # [PLACEHOLDER] Exit if no progress
TIME_STOP_DAYS = 20               # [PLACEHOLDER] Days before time stop (10-30)
PROFIT_LOCK_THRESHOLD = 0.10      # [PLACEHOLDER] Lock profits above this (0.05-0.15)
PROFIT_LOCK_PERCENT = 0.50        # [PLACEHOLDER] % of profit to lock (0.3-0.7)

# Execution
REBALANCE_FREQUENCY = 'daily'     # [PLACEHOLDER] 'daily', 'weekly'
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
SLIPPAGE_VOLUME_LIMIT = 0.025     # [PLACEHOLDER] Max volume participation
SLIPPAGE_PRICE_IMPACT = 0.1       # [PLACEHOLDER] Price impact


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Initialize strategy state and scheduling."""
    
    context.asset = symbol(ASSET_SYMBOL)
    context.hedge = symbol(HEDGE_SYMBOL) if USE_HEDGE else None
    
    # Position state
    context.in_position = False
    context.entry_price = 0.0
    context.entry_date = None
    context.highest_price = 0.0
    context.peak_portfolio_value = 0.0
    
    # Regime state
    context.current_regime = 'neutral'  # 'trending', 'ranging', 'volatile'
    context.volatility_regime = 'normal'  # 'low', 'normal', 'high'
    
    # Performance tracking
    context.max_portfolio_value = 0.0
    context.current_drawdown = 0.0
    
    set_benchmark(context.asset)
    
    set_commission(us_equities=commission.PerShare(
        cost=COMMISSION_PER_SHARE, min_trade_cost=1.0
    ))
    
    set_slippage(us_equities=slippage.VolumeShareSlippage(
        volume_limit=SLIPPAGE_VOLUME_LIMIT,
        price_impact=SLIPPAGE_PRICE_IMPACT
    ))
    
    # Schedule rebalancing
    if REBALANCE_FREQUENCY == 'daily':
        schedule_function(rebalance, date_rules.every_day(),
                         time_rules.market_open(minutes=REBALANCE_TIME))
    else:
        schedule_function(rebalance, date_rules.week_start(),
                         time_rules.market_open(minutes=REBALANCE_TIME))
    
    # Daily drawdown check
    schedule_function(update_drawdown, date_rules.every_day(),
                     time_rules.market_open(minutes=1))


def compute_ema(prices, period):
    """Exponential moving average."""
    return prices.ewm(span=period, adjust=False).mean()


def compute_sma(prices, period):
    """Simple moving average."""
    return prices.rolling(window=int(period)).mean()


def compute_atr(high, low, close, period=14):
    """Average True Range."""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(high, low, close, period=14):
    """Average Directional Index for trend strength."""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr = compute_atr(high, low, close, period)
    
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)
    adx = dx.rolling(period).mean()
    
    return adx, plus_di, minus_di


def detect_volatility_regime(returns, lookback):
    """Classify volatility regime."""
    vol = returns.rolling(lookback).std() * np.sqrt(252)
    current_vol = vol.iloc[-1]
    
    if current_vol > HIGH_VOL_THRESHOLD:
        return 'high', current_vol
    elif current_vol < LOW_VOL_THRESHOLD:
        return 'low', current_vol
    else:
        return 'normal', current_vol


def detect_trend_regime(prices, lookback):
    """Detect trending vs ranging market."""
    returns = prices.pct_change()
    
    # Linear regression slope
    x = np.arange(lookback)
    y = prices.iloc[-lookback:].values
    
    if len(y) < lookback:
        return 'neutral', 0
    
    slope = np.polyfit(x, y, 1)[0]
    normalized_slope = slope / prices.iloc[-1]
    
    # Hurst exponent approximation using R/S analysis
    log_returns = np.log(prices / prices.shift(1)).dropna().iloc[-lookback:]
    
    if len(log_returns) < lookback:
        return 'neutral', 0
    
    mean_return = log_returns.mean()
    cumulative_deviation = (log_returns - mean_return).cumsum()
    r = cumulative_deviation.max() - cumulative_deviation.min()
    s = log_returns.std()
    
    if s > 0:
        rs = r / s
        hurst = np.log(rs) / np.log(lookback) if rs > 0 else 0.5
    else:
        hurst = 0.5
    
    if abs(normalized_slope) > TREND_REGIME_THRESHOLD and hurst > 0.55:
        return 'trending', normalized_slope
    elif hurst < 0.45:
        return 'ranging', normalized_slope
    else:
        return 'neutral', normalized_slope


def get_adaptive_periods(volatility_regime):
    """Adjust SMA periods based on volatility regime."""
    if not USE_ADAPTIVE_PERIODS:
        return {
            'short_fast': SHORT_FAST_SMA, 'short_slow': SHORT_SLOW_SMA,
            'medium_fast': MEDIUM_FAST_SMA, 'medium_slow': MEDIUM_SLOW_SMA,
            'long_fast': LONG_FAST_SMA, 'long_slow': LONG_SLOW_SMA
        }
    
    if volatility_regime == 'high':
        factor = PERIOD_EXPANSION_FACTOR
    elif volatility_regime == 'low':
        factor = PERIOD_CONTRACTION_FACTOR
    else:
        factor = 1.0
    
    return {
        'short_fast': int(SHORT_FAST_SMA * factor),
        'short_slow': int(SHORT_SLOW_SMA * factor),
        'medium_fast': int(MEDIUM_FAST_SMA * factor),
        'medium_slow': int(MEDIUM_SLOW_SMA * factor),
        'long_fast': int(LONG_FAST_SMA * factor),
        'long_slow': int(LONG_SLOW_SMA * factor)
    }


def compute_timeframe_signals(prices, periods):
    """Compute signals for each timeframe."""
    signals = {}
    
    # Short-term
    short_fast = compute_sma(prices, periods['short_fast'])
    short_slow = compute_sma(prices, periods['short_slow'])
    signals['short'] = 1 if short_fast.iloc[-1] > short_slow.iloc[-1] else -1
    
    # Medium-term
    med_fast = compute_sma(prices, periods['medium_fast'])
    med_slow = compute_sma(prices, periods['medium_slow'])
    signals['medium'] = 1 if med_fast.iloc[-1] > med_slow.iloc[-1] else -1
    
    # Long-term
    long_fast = compute_sma(prices, periods['long_fast'])
    long_slow = compute_sma(prices, periods['long_slow'])
    signals['long'] = 1 if long_fast.iloc[-1] > long_slow.iloc[-1] else -1
    
    # Weighted signal
    weighted = (signals['short'] * WEIGHT_SHORT_TF +
                signals['medium'] * WEIGHT_MEDIUM_TF +
                signals['long'] * WEIGHT_LONG_TF)
    
    signals['weighted'] = weighted
    signals['aligned_count'] = sum(1 for s in [signals['short'], signals['medium'], signals['long']] if s == 1)
    
    return signals


def compute_position_size(context, data, current_vol, signal_strength):
    """Risk parity position sizing with drawdown control."""
    
    base_size = BASE_POSITION_SIZE
    
    # Volatility targeting
    if USE_VOLATILITY_TARGETING and current_vol > 0:
        vol_scalar = TARGET_VOLATILITY / current_vol
        base_size = base_size * vol_scalar
    
    # Signal strength adjustment
    base_size = base_size * abs(signal_strength)
    
    # Drawdown reduction
    if USE_DRAWDOWN_CONTROL:
        if context.current_drawdown > CRITICAL_DRAWDOWN:
            base_size = base_size * 0.25  # Aggressive reduction
        elif context.current_drawdown > MAX_DRAWDOWN_THRESHOLD:
            reduction = (context.current_drawdown - MAX_DRAWDOWN_THRESHOLD) / (CRITICAL_DRAWDOWN - MAX_DRAWDOWN_THRESHOLD)
            base_size = base_size * (1 - reduction * DRAWDOWN_REDUCTION_FACTOR)
    
    # Apply limits
    base_size = max(MIN_POSITION_SIZE, min(base_size, MAX_LEVERAGE))
    
    return base_size


def update_drawdown(context, data):
    """Update drawdown tracking."""
    current_value = context.portfolio.portfolio_value
    context.max_portfolio_value = max(context.max_portfolio_value, current_value)
    
    if context.max_portfolio_value > 0:
        context.current_drawdown = (context.max_portfolio_value - current_value) / context.max_portfolio_value
    
    record(drawdown=context.current_drawdown)


def rebalance(context, data):
    """Main rebalancing logic."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get price data
    lookback = max(LONG_SLOW_SMA + 50, REGIME_LOOKBACK + 20)
    prices = data.history(context.asset, 'price', lookback, '1d')
    high = data.history(context.asset, 'high', lookback, '1d')
    low = data.history(context.asset, 'low', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    returns = prices.pct_change().dropna()
    current_price = prices.iloc[-1]
    
    # Detect regimes
    vol_regime, current_vol = detect_volatility_regime(returns, VOLATILITY_LOOKBACK)
    trend_regime, trend_slope = detect_trend_regime(prices, REGIME_LOOKBACK)
    context.volatility_regime = vol_regime
    context.current_regime = trend_regime
    
    # Get adaptive periods
    periods = get_adaptive_periods(vol_regime)
    
    # Compute multi-timeframe signals
    signals = compute_timeframe_signals(prices, periods)
    
    # ADX filter
    adx, plus_di, minus_di = compute_adx(high, low, prices, ADX_PERIOD)
    current_adx = adx.iloc[-1]
    adx_pass = not USE_ADX_FILTER or current_adx > ADX_THRESHOLD
    
    # ATR for stops
    atr = compute_atr(high, low, prices, 14)
    current_atr = atr.iloc[-1]
    
    # Record metrics
    record(
        price=current_price,
        adx=current_adx,
        volatility=current_vol,
        signal=signals['weighted'],
        regime=hash(trend_regime) % 10
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Entry Logic
    if not context.in_position:
        # Check alignment
        if REQUIRE_ALL_TIMEFRAMES:
            should_enter = signals['aligned_count'] == 3 and signals['weighted'] > 0
        else:
            should_enter = signals['aligned_count'] >= MIN_TIMEFRAMES_ALIGNED and signals['weighted'] > 0
        
        # Apply filters
        should_enter = should_enter and adx_pass
        
        # Avoid entering in high volatility regime unless trend is strong
        if vol_regime == 'high' and current_adx < ADX_STRONG_TREND:
            should_enter = False
        
        if should_enter:
            position_size = compute_position_size(context, data, current_vol, signals['weighted'])
            order_target_percent(context.asset, position_size)
            
            context.in_position = True
            context.entry_price = current_price
            context.entry_date = data.current_dt
            context.highest_price = current_price
            
            record(entry=1)
            return
    
    # Exit Logic
    if context.in_position:
        context.highest_price = max(context.highest_price, current_price)
        pnl_pct = (current_price - context.entry_price) / context.entry_price
        
        should_exit = False
        
        # Signal reversal
        if signals['weighted'] < -0.3:
            should_exit = True
        
        # Volatility stop
        if USE_VOLATILITY_STOP:
            stop_price = context.entry_price - (current_atr * STOP_ATR_MULTIPLIER)
            if current_price < stop_price:
                should_exit = True
        
        # Time stop
        if USE_TIME_STOP and context.entry_date:
            days_held = (data.current_dt - context.entry_date).days
            if days_held > TIME_STOP_DAYS and pnl_pct < 0.02:
                should_exit = True
        
        # Profit lock trailing stop
        if pnl_pct > PROFIT_LOCK_THRESHOLD:
            lock_level = context.entry_price * (1 + pnl_pct * PROFIT_LOCK_PERCENT)
            if current_price < lock_level:
                should_exit = True
        
        if should_exit:
            # Switch to hedge if enabled and in risk-off
            if USE_HEDGE and context.hedge and vol_regime == 'high':
                order_target_percent(context.asset, 0)
                order_target_percent(context.hedge, BASE_POSITION_SIZE * 0.5)
            else:
                order_target_percent(context.asset, 0)
            
            context.in_position = False
            context.entry_price = 0.0
            context.entry_date = None
            context.highest_price = 0.0
            record(exit=1)
            return
    
    record(entry=0, exit=0)


def handle_data(context, data):
    """Called every bar."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 70)
    print("ADVANCED MULTI-TIMEFRAME SMA STRATEGY RESULTS")
    print("=" * 70)
    
    returns = perf['returns']
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdowns = (cumulative - rolling_max) / rolling_max
    max_dd = drawdowns.min()
    
    # Calmar ratio
    calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print(f"Calmar Ratio: {calmar:.2f}")
    print("=" * 70)
