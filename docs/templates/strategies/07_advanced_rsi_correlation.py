# Advanced RSI Mean Reversion Strategy
# ==============================================================================
# A sophisticated mean reversion strategy featuring:
# - Dynamic RSI thresholds based on market volatility
# - Multi-asset correlation filter to avoid systemic moves
# - Regime-aware entry timing (avoid trending markets)
# - Kelly Criterion-inspired position sizing
# - Pyramiding with mathematical scaling
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
PRIMARY_SYMBOL = 'QQQ'            # [PLACEHOLDER] Primary trading asset
CORRELATION_ASSETS = ['SPY', 'IWM', 'DIA']  # [PLACEHOLDER] Correlation check assets
USE_CORRELATION_FILTER = True     # [PLACEHOLDER] Filter correlated moves

# RSI Parameters
RSI_PERIOD = 14                   # [PLACEHOLDER] Base RSI period (7-21)
USE_ADAPTIVE_RSI = True           # [PLACEHOLDER] Adjust period by volatility
RSI_PERIOD_MIN = 7                # [PLACEHOLDER] Minimum RSI period
RSI_PERIOD_MAX = 21               # [PLACEHOLDER] Maximum RSI period

# Dynamic Thresholds
BASE_OVERSOLD = 30                # [PLACEHOLDER] Base oversold level (25-35)
BASE_OVERBOUGHT = 70              # [PLACEHOLDER] Base overbought level (65-75)
USE_DYNAMIC_THRESHOLDS = True     # [PLACEHOLDER] Adjust thresholds dynamically
THRESHOLD_VOLATILITY_SCALAR = 0.5 # [PLACEHOLDER] How much vol affects thresholds
MIN_OVERSOLD = 15                 # [PLACEHOLDER] Minimum oversold threshold
MAX_OVERSOLD = 40                 # [PLACEHOLDER] Maximum oversold threshold

# RSI Divergence Detection
USE_RSI_DIVERGENCE = True         # [PLACEHOLDER] Trade on divergence
DIVERGENCE_LOOKBACK = 14          # [PLACEHOLDER] Bars to check divergence
DIVERGENCE_PRICE_THRESHOLD = 0.02 # [PLACEHOLDER] Min price move for divergence

# Correlation Filter Settings
CORRELATION_LOOKBACK = 20         # [PLACEHOLDER] Correlation calculation window
CORRELATION_THRESHOLD = 0.70      # [PLACEHOLDER] Min correlation to filter (0.5-0.85)
MIN_ASSETS_OVERSOLD = 2           # [PLACEHOLDER] Min correlated assets also oversold

# Regime Detection
USE_REGIME_FILTER = True          # [PLACEHOLDER] Avoid trending markets
TREND_ADX_PERIOD = 14             # [PLACEHOLDER] ADX period for trend detection
MAX_ADX_FOR_ENTRY = 30            # [PLACEHOLDER] Max ADX to allow entry (25-40)
REQUIRE_MEAN_REVERSION_REGIME = True  # [PLACEHOLDER] Hurst < 0.5 required

# Position Sizing - Kelly-Inspired
USE_KELLY_SIZING = True           # [PLACEHOLDER] Kelly criterion sizing
KELLY_FRACTION = 0.25             # [PLACEHOLDER] Fraction of Kelly (0.1-0.5)
WIN_RATE_ESTIMATE = 0.55          # [PLACEHOLDER] Estimated win rate (0.45-0.65)
AVG_WIN_LOSS_RATIO = 1.5          # [PLACEHOLDER] Avg win / avg loss (1.0-2.5)
MAX_POSITION_SIZE = 0.80          # [PLACEHOLDER] Maximum position (0.5-1.0)
MIN_POSITION_SIZE = 0.20          # [PLACEHOLDER] Minimum position (0.1-0.3)

# Pyramiding / Scaling
ENABLE_PYRAMIDING = True          # [PLACEHOLDER] Scale into positions
MAX_PYRAMID_LEVELS = 3            # [PLACEHOLDER] Maximum scale-ins (2-5)
PYRAMID_RSI_STEP = 5              # [PLACEHOLDER] RSI drop per level (3-10)
PYRAMID_SIZE_DECAY = 0.7          # [PLACEHOLDER] Size multiplier per level (0.5-0.9)
REQUIRE_LOWER_PRICE = True        # [PLACEHOLDER] Only pyramid at lower prices

# Exit Parameters
RSI_EXIT_LEVEL = 50               # [PLACEHOLDER] Base exit RSI (45-55)
USE_DYNAMIC_EXIT = True           # [PLACEHOLDER] Adjust exit level
PROFIT_TARGET_PCT = 0.08          # [PLACEHOLDER] Profit target (0.04-0.12)
MAX_HOLDING_DAYS = 15             # [PLACEHOLDER] Force exit days (10-25)
MIN_HOLDING_BARS = 2              # [PLACEHOLDER] Minimum hold before exit

# Risk Management
STOP_LOSS_PCT = 0.06              # [PLACEHOLDER] Stop loss (0.03-0.10)
USE_VOLATILITY_ADJUSTED_STOP = True  # [PLACEHOLDER] ATR-based stops
STOP_ATR_MULTIPLIER = 2.5         # [PLACEHOLDER] ATR multiple (1.5-3.5)
TRAILING_ACTIVATION_PCT = 0.04    # [PLACEHOLDER] Profit to activate trail
TRAILING_STOP_PCT = 0.03          # [PLACEHOLDER] Trailing stop distance

# Execution
REBALANCE_TIME = 30               # [PLACEHOLDER] Minutes after open

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
SLIPPAGE_BPS = 5.0                # [PLACEHOLDER] Slippage basis points


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Initialize strategy."""
    
    context.asset = symbol(PRIMARY_SYMBOL)
    context.correlation_assets = [symbol(s) for s in CORRELATION_ASSETS]
    
    # Position state
    context.position_level = 0
    context.entry_prices = []
    context.entry_date = None
    context.highest_price = 0.0
    context.trailing_active = False
    
    # Performance tracking
    context.trade_results = []
    
    set_benchmark(context.asset)
    
    set_commission(us_equities=commission.PerShare(
        cost=COMMISSION_PER_SHARE, min_trade_cost=1.0
    ))
    
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(
        basis_points=SLIPPAGE_BPS, volume_limit=0.1
    ))
    
    schedule_function(check_entry, date_rules.every_day(),
                     time_rules.market_open(minutes=REBALANCE_TIME))
    
    schedule_function(manage_position, date_rules.every_day(),
                     time_rules.market_open(minutes=REBALANCE_TIME + 5))


def compute_rsi(prices, period):
    """Calculate RSI with Wilder's smoothing."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    # Wilder's smoothing (EMA with alpha = 1/period)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_adaptive_rsi_period(volatility, vol_percentile):
    """Adjust RSI period based on volatility."""
    if not USE_ADAPTIVE_RSI:
        return RSI_PERIOD
    
    # Higher volatility = shorter period (faster reaction)
    # Lower volatility = longer period (smoother)
    period = RSI_PERIOD_MAX - (vol_percentile * (RSI_PERIOD_MAX - RSI_PERIOD_MIN))
    return int(np.clip(period, RSI_PERIOD_MIN, RSI_PERIOD_MAX))


def compute_dynamic_thresholds(volatility, vol_mean, vol_std):
    """Adjust RSI thresholds based on market volatility."""
    if not USE_DYNAMIC_THRESHOLDS:
        return BASE_OVERSOLD, BASE_OVERBOUGHT
    
    # Higher vol = more extreme thresholds (wider bands)
    vol_z = (volatility - vol_mean) / vol_std if vol_std > 0 else 0
    adjustment = vol_z * THRESHOLD_VOLATILITY_SCALAR * 5
    
    oversold = BASE_OVERSOLD - adjustment  # Lower in high vol
    overbought = BASE_OVERBOUGHT + adjustment  # Higher in high vol
    
    oversold = np.clip(oversold, MIN_OVERSOLD, MAX_OVERSOLD)
    overbought = np.clip(overbought, 100 - MAX_OVERSOLD, 100 - MIN_OVERSOLD)
    
    return oversold, overbought


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
    
    return adx


def compute_hurst_exponent(prices, max_lag=20):
    """Estimate Hurst exponent for regime detection."""
    lags = range(2, max_lag)
    tau = [np.std(np.subtract(prices[lag:].values, prices[:-lag].values)) 
           for lag in lags]
    
    if len(tau) < 2 or min(tau) <= 0:
        return 0.5
    
    reg = np.polyfit(np.log(lags), np.log(tau), 1)
    return reg[0]


def detect_rsi_divergence(prices, rsi, lookback):
    """Detect bullish RSI divergence."""
    if len(prices) < lookback or len(rsi) < lookback:
        return False
    
    recent_prices = prices.iloc[-lookback:]
    recent_rsi = rsi.iloc[-lookback:]
    
    # Find lows
    price_min_idx = recent_prices.idxmin()
    current_price = prices.iloc[-1]
    current_rsi = rsi.iloc[-1]
    
    price_at_low = recent_prices[price_min_idx]
    rsi_at_low = recent_rsi[price_min_idx]
    
    # Bullish divergence: price makes lower low, RSI makes higher low
    price_lower = current_price < price_at_low * (1 + DIVERGENCE_PRICE_THRESHOLD)
    rsi_higher = current_rsi > rsi_at_low
    
    return price_lower and rsi_higher and current_rsi < 40


def check_correlation_filter(context, data, primary_rsi, oversold_threshold):
    """Check if move is correlated (systemic) or idiosyncratic."""
    if not USE_CORRELATION_FILTER:
        return True
    
    oversold_count = 0
    
    for asset in context.correlation_assets:
        if not data.can_trade(asset):
            continue
        
        try:
            prices = data.history(asset, 'price', RSI_PERIOD + 5, '1d')
            asset_rsi = compute_rsi(prices, RSI_PERIOD).iloc[-1]
            
            if asset_rsi < oversold_threshold + 10:  # Slightly looser threshold
                oversold_count += 1
        except:
            continue
    
    # If too many correlated assets are oversold, it's a systemic move
    # We want idiosyncratic opportunities
    if oversold_count >= MIN_ASSETS_OVERSOLD:
        return False  # Skip - too correlated
    
    return True


def compute_kelly_position_size(context):
    """Kelly Criterion-inspired position sizing."""
    if not USE_KELLY_SIZING:
        return MAX_POSITION_SIZE
    
    # Kelly formula: f* = (bp - q) / b
    # where b = win/loss ratio, p = win prob, q = loss prob
    b = AVG_WIN_LOSS_RATIO
    p = WIN_RATE_ESTIMATE
    q = 1 - p
    
    kelly = (b * p - q) / b
    
    # Apply fractional Kelly for safety
    position_size = kelly * KELLY_FRACTION
    
    return np.clip(position_size, MIN_POSITION_SIZE, MAX_POSITION_SIZE)


def check_entry(context, data):
    """Check for entry signals."""
    
    if not data.can_trade(context.asset):
        return
    
    # Get price data
    lookback = max(RSI_PERIOD_MAX + 20, DIVERGENCE_LOOKBACK + 10, CORRELATION_LOOKBACK + 5)
    prices = data.history(context.asset, 'price', lookback, '1d')
    high = data.history(context.asset, 'high', lookback, '1d')
    low = data.history(context.asset, 'low', lookback, '1d')
    
    if len(prices) < lookback:
        return
    
    returns = prices.pct_change().dropna()
    current_price = prices.iloc[-1]
    
    # Volatility analysis
    volatility = returns.rolling(20).std() * np.sqrt(252)
    current_vol = volatility.iloc[-1]
    vol_mean = volatility.mean()
    vol_std = volatility.std()
    vol_percentile = (volatility.rank(pct=True)).iloc[-1]
    
    # Adaptive RSI
    rsi_period = compute_adaptive_rsi_period(current_vol, vol_percentile)
    rsi = compute_rsi(prices, rsi_period)
    current_rsi = rsi.iloc[-1]
    
    # Dynamic thresholds
    oversold, overbought = compute_dynamic_thresholds(current_vol, vol_mean, vol_std)
    
    # Regime detection
    adx = compute_adx(high, low, prices, TREND_ADX_PERIOD)
    current_adx = adx.iloc[-1]
    
    hurst = compute_hurst_exponent(prices.iloc[-60:]) if len(prices) >= 60 else 0.5
    
    # RSI divergence
    has_divergence = detect_rsi_divergence(prices, rsi, DIVERGENCE_LOOKBACK) if USE_RSI_DIVERGENCE else False
    
    # Record metrics
    record(
        rsi=current_rsi,
        oversold_threshold=oversold,
        adx=current_adx,
        hurst=hurst,
        position_level=context.position_level
    )
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Initial entry
    if context.position_level == 0:
        should_enter = current_rsi < oversold
        
        # Divergence can override
        if has_divergence:
            should_enter = True
        
        # Regime filters
        if USE_REGIME_FILTER:
            if current_adx > MAX_ADX_FOR_ENTRY:
                should_enter = False  # Market trending too strongly
            
            if REQUIRE_MEAN_REVERSION_REGIME and hurst > 0.55:
                should_enter = False  # Not a mean-reverting regime
        
        # Correlation filter
        if should_enter and not check_correlation_filter(context, data, current_rsi, oversold):
            should_enter = False
        
        if should_enter:
            position_size = compute_kelly_position_size(context)
            order_target_percent(context.asset, position_size)
            
            context.position_level = 1
            context.entry_prices = [current_price]
            context.entry_date = data.current_dt
            context.highest_price = current_price
            context.trailing_active = False
            
            record(entry=1)
            return
    
    # Pyramiding
    elif context.position_level > 0 and ENABLE_PYRAMIDING:
        if context.position_level < MAX_PYRAMID_LEVELS:
            # Check if RSI dropped further
            pyramid_rsi_threshold = oversold - (context.position_level * PYRAMID_RSI_STEP)
            
            should_pyramid = current_rsi < pyramid_rsi_threshold
            
            if REQUIRE_LOWER_PRICE:
                avg_entry = np.mean(context.entry_prices)
                should_pyramid = should_pyramid and current_price < avg_entry * 0.98
            
            if should_pyramid:
                # Calculate new position size
                base_size = compute_kelly_position_size(context)
                level_size = base_size * (PYRAMID_SIZE_DECAY ** context.position_level)
                total_size = min(MAX_POSITION_SIZE, 
                               base_size + (level_size * context.position_level))
                
                order_target_percent(context.asset, total_size)
                
                context.position_level += 1
                context.entry_prices.append(current_price)
                
                record(pyramid=1)
                return
    
    record(entry=0, pyramid=0)


def manage_position(context, data):
    """Manage existing position."""
    
    if context.position_level == 0:
        return
    
    if not data.can_trade(context.asset):
        return
    
    prices = data.history(context.asset, 'price', RSI_PERIOD + 5, '1d')
    high = data.history(context.asset, 'high', 15, '1d')
    low = data.history(context.asset, 'low', 15, '1d')
    
    current_price = prices.iloc[-1]
    context.highest_price = max(context.highest_price, current_price)
    
    rsi = compute_rsi(prices, RSI_PERIOD)
    current_rsi = rsi.iloc[-1]
    
    # Average entry price
    avg_entry = np.mean(context.entry_prices)
    pnl_pct = (current_price - avg_entry) / avg_entry
    
    # ATR for volatility-adjusted stop
    tr = pd.concat([high - low,
                    abs(high - prices.shift(1)),
                    abs(low - prices.shift(1))], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    
    # Dynamic exit level
    if USE_DYNAMIC_EXIT:
        # Exit earlier if volatile, later if calm
        volatility = prices.pct_change().std() * np.sqrt(252)
        exit_adjustment = (volatility - 0.15) * 20  # Adjust by vol
        exit_level = RSI_EXIT_LEVEL - exit_adjustment
        exit_level = np.clip(exit_level, 40, 60)
    else:
        exit_level = RSI_EXIT_LEVEL
    
    should_exit = False
    exit_reason = ""
    
    # RSI exit
    if current_rsi >= exit_level:
        should_exit = True
        exit_reason = "rsi_target"
    
    # Profit target
    if pnl_pct >= PROFIT_TARGET_PCT:
        should_exit = True
        exit_reason = "profit_target"
    
    # Activate trailing stop
    if pnl_pct >= TRAILING_ACTIVATION_PCT:
        context.trailing_active = True
    
    # Trailing stop
    if context.trailing_active:
        trail_stop = context.highest_price * (1 - TRAILING_STOP_PCT)
        if current_price < trail_stop:
            should_exit = True
            exit_reason = "trailing_stop"
    
    # Stop loss
    if USE_VOLATILITY_ADJUSTED_STOP:
        stop_price = avg_entry - (atr * STOP_ATR_MULTIPLIER)
    else:
        stop_price = avg_entry * (1 - STOP_LOSS_PCT)
    
    if current_price < stop_price:
        should_exit = True
        exit_reason = "stop_loss"
    
    # Time stop
    if context.entry_date:
        days_held = (data.current_dt - context.entry_date).days
        if days_held >= MAX_HOLDING_DAYS:
            should_exit = True
            exit_reason = "time_stop"
    
    if should_exit:
        order_target_percent(context.asset, 0)
        
        context.position_level = 0
        context.entry_prices = []
        context.entry_date = None
        context.highest_price = 0.0
        context.trailing_active = False
        
        record(exit=1, exit_type=hash(exit_reason) % 10)
    else:
        record(exit=0)


def handle_data(context, data):
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 70)
    print("ADVANCED RSI MEAN REVERSION STRATEGY RESULTS")
    print("=" * 70)
    
    returns = perf['returns']
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    # Sortino ratio
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    sortino = annual_return / downside_std if downside_std > 0 else 0
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Sortino Ratio: {sortino:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 70)
