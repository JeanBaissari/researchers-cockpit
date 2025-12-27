# SMA Cross Strategy Template
# ==============================================================================
# A classic dual moving average crossover strategy with configurable parameters,
# position sizing, and risk management.
#
# STRATEGY LOGIC:
# - BUY when fast SMA crosses above slow SMA (golden cross)
# - SELL when fast SMA crosses below slow SMA (death cross)
# - Optional: Only trade when price is above/below a trend filter SMA
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

# Moving Average Parameters
FAST_SMA_PERIOD = 10              # [PLACEHOLDER] Fast SMA lookback (5-20)
SLOW_SMA_PERIOD = 30              # [PLACEHOLDER] Slow SMA lookback (20-100)
TREND_FILTER_PERIOD = 200         # [PLACEHOLDER] Trend filter SMA (100-200), set 0 to disable

# Position Sizing
MAX_POSITION_SIZE = 0.95          # [PLACEHOLDER] Max portfolio allocation (0.0-1.0)
POSITION_SIZE_METHOD = 'fixed'    # [PLACEHOLDER] 'fixed' or 'volatility_scaled'
VOLATILITY_LOOKBACK = 20          # [PLACEHOLDER] Lookback for volatility scaling
VOLATILITY_TARGET = 0.15          # [PLACEHOLDER] Target annualized volatility

# Risk Management
USE_STOP_LOSS = True              # [PLACEHOLDER] Enable stop loss
STOP_LOSS_PCT = 0.05              # [PLACEHOLDER] Stop loss percentage (0.01-0.10)
USE_TRAILING_STOP = False         # [PLACEHOLDER] Use trailing stop instead of fixed
TRAILING_STOP_PCT = 0.08          # [PLACEHOLDER] Trailing stop percentage

# Execution Settings
REBALANCE_FREQUENCY = 'daily'     # [PLACEHOLDER] 'daily', 'weekly', 'monthly'
MINUTES_AFTER_OPEN = 30           # [PLACEHOLDER] Minutes after open to trade (0-60)

# Cost Assumptions
COMMISSION_PER_SHARE = 0.005      # [PLACEHOLDER] Commission per share
MIN_TRADE_COST = 1.0              # [PLACEHOLDER] Minimum commission per trade
SLIPPAGE_VOLUME_LIMIT = 0.025     # [PLACEHOLDER] Max volume participation
SLIPPAGE_PRICE_IMPACT = 0.1       # [PLACEHOLDER] Price impact coefficient


# ==============================================================================
# STRATEGY IMPLEMENTATION
# ==============================================================================

def initialize(context):
    """Set up the strategy."""
    
    # Store asset
    context.asset = symbol(ASSET_SYMBOL)
    
    # Strategy state
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0  # For trailing stop
    
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
    
    # Schedule rebalancing
    if REBALANCE_FREQUENCY == 'daily':
        schedule_function(
            rebalance,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=MINUTES_AFTER_OPEN)
        )
    elif REBALANCE_FREQUENCY == 'weekly':
        schedule_function(
            rebalance,
            date_rule=date_rules.week_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=MINUTES_AFTER_OPEN)
        )
    elif REBALANCE_FREQUENCY == 'monthly':
        schedule_function(
            rebalance,
            date_rule=date_rules.month_start(days_offset=0),
            time_rule=time_rules.market_open(minutes=MINUTES_AFTER_OPEN)
        )
    
    # Schedule stop loss check
    if USE_STOP_LOSS or USE_TRAILING_STOP:
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )


def compute_signals(context, data):
    """Compute trading signals."""
    
    # Need enough history for slow SMA
    lookback = max(SLOW_SMA_PERIOD, TREND_FILTER_PERIOD) + 5
    
    if not data.can_trade(context.asset):
        return None, None, None
    
    # Get price history
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return None, None, None
    
    # Calculate SMAs
    fast_sma = prices[-FAST_SMA_PERIOD:].mean()
    slow_sma = prices[-SLOW_SMA_PERIOD:].mean()
    
    # Previous SMAs for crossover detection
    fast_sma_prev = prices[-(FAST_SMA_PERIOD + 1):-1].mean()
    slow_sma_prev = prices[-(SLOW_SMA_PERIOD + 1):-1].mean()
    
    # Trend filter
    trend_bullish = True
    if TREND_FILTER_PERIOD > 0:
        trend_sma = prices[-TREND_FILTER_PERIOD:].mean()
        trend_bullish = prices.iloc[-1] > trend_sma
    
    # Detect crossovers
    golden_cross = (fast_sma > slow_sma) and (fast_sma_prev <= slow_sma_prev)
    death_cross = (fast_sma < slow_sma) and (fast_sma_prev >= slow_sma_prev)
    
    # Generate signals
    signal = 0
    if golden_cross and trend_bullish:
        signal = 1  # Buy
    elif death_cross:
        signal = -1  # Sell
    
    return signal, fast_sma, slow_sma


def compute_position_size(context, data):
    """Calculate position size based on method."""
    
    if POSITION_SIZE_METHOD == 'fixed':
        return MAX_POSITION_SIZE
    
    elif POSITION_SIZE_METHOD == 'volatility_scaled':
        prices = data.history(context.asset, 'price', VOLATILITY_LOOKBACK + 1, '1d')
        returns = prices.pct_change().dropna()
        
        if len(returns) < VOLATILITY_LOOKBACK:
            return MAX_POSITION_SIZE
        
        # Annualized volatility
        current_vol = returns.std() * np.sqrt(252)
        
        if current_vol > 0:
            # Scale position to target volatility
            size = VOLATILITY_TARGET / current_vol
            return min(size, MAX_POSITION_SIZE)
        
        return MAX_POSITION_SIZE
    
    return MAX_POSITION_SIZE


def rebalance(context, data):
    """Main rebalancing logic."""
    
    signal, fast_sma, slow_sma = compute_signals(context, data)
    
    if signal is None:
        return
    
    current_price = data.current(context.asset, 'price')
    
    # Record metrics
    record(
        fast_sma=fast_sma,
        slow_sma=slow_sma,
        signal=signal,
        price=current_price
    )
    
    # Cancel any open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Execute signals
    if signal == 1 and not context.in_position:
        # Enter long position
        position_size = compute_position_size(context, data)
        order_target_percent(context.asset, position_size)
        
        context.in_position = True
        context.entry_price = current_price
        context.highest_price = current_price
        
    elif signal == -1 and context.in_position:
        # Exit position
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0


def check_stop_loss(context, data):
    """Check and execute stop loss orders."""
    
    if not context.in_position:
        return
    
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    
    # Update highest price for trailing stop
    context.highest_price = max(context.highest_price, current_price)
    
    should_stop = False
    
    if USE_TRAILING_STOP:
        # Trailing stop from highest price
        stop_price = context.highest_price * (1 - TRAILING_STOP_PCT)
        should_stop = current_price <= stop_price
    elif USE_STOP_LOSS:
        # Fixed stop from entry
        stop_price = context.entry_price * (1 - STOP_LOSS_PCT)
        should_stop = current_price <= stop_price
    
    if should_stop:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        record(stop_triggered=1)
    else:
        record(stop_triggered=0)


def handle_data(context, data):
    """Called every bar - used for recording only."""
    pass


def analyze(context, perf):
    """Post-backtest analysis."""
    print("\n" + "=" * 60)
    print("SMA CROSS STRATEGY RESULTS")
    print("=" * 60)
    print(f"Asset: {ASSET_SYMBOL}")
    print(f"Fast SMA: {FAST_SMA_PERIOD}, Slow SMA: {SLOW_SMA_PERIOD}")
    print(f"Total Return: {perf['returns'].sum():.2%}")
    print(f"Final Portfolio Value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    
    # Calculate metrics
    returns = perf['returns']
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
