# Strategy Template Modernization

Update the strategy template to work correctly across all asset classes and follow best practices.

## Problem Statement

The current `strategies/_template/strategy.py` has several issues:

1. **USEquityPricing Import:** Uses US-equity-specific data source
2. **Pipeline Always On:** Pipeline is attached even when not needed
3. **Missing Asset Class Awareness:** No way to specify asset class in parameters
4. **Hardcoded SMA Example:** Example factor doesn't reflect real usage patterns
5. **Verbose Boilerplate:** Too much code for a minimal working example

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Review current template structure
- [ ] Identify minimal required components

## Future Tasks

### Template Structure Updates
- [ ] Replace USEquityPricing with EquityPricing
- [ ] Make Pipeline optional (controlled by parameter)
- [ ] Add asset_class to parameters.yaml
- [ ] Simplify compute_signals() example
- [ ] Add data.history() based alternative

### Documentation Updates
- [ ] Add docstrings explaining Pipeline vs data.history()
- [ ] Add examples for each asset class
- [ ] Document required vs optional functions

### Parameters.yaml Updates
- [ ] Add asset_class field
- [ ] Add use_pipeline toggle
- [ ] Add calendar override option

## Implementation Plan

### Step 1: Update parameters.yaml Template

```yaml
# Strategy Parameters
# ==============================================================================

# Strategy Configuration
strategy:
  asset_symbol: SPY              # Asset to trade (e.g., SPY, BTC-USD, EURUSD=X)
  asset_class: equities          # Asset class: 'equities', 'crypto', 'forex'
  rebalance_frequency: daily     # 'daily', 'weekly', 'monthly'
  minutes_after_open: 30         # Minutes after market open to trade (0-60)
  
  # Pipeline configuration
  use_pipeline: false            # Enable Zipline Pipeline (default: false for simplicity)
  
  # Strategy-specific parameters (customize for your strategy)
  lookback_period: 30            # Days of historical data for signals
  # fast_period: 10              # Example: fast MA period
  # slow_period: 30              # Example: slow MA period

# Position Sizing
position_sizing:
  max_position_pct: 0.95
  method: fixed                  # 'fixed', 'volatility_scaled', 'kelly'

# Risk Management
risk:
  use_stop_loss: true
  stop_loss_pct: 0.05
  use_trailing_stop: false
  trailing_stop_pct: 0.08
  use_take_profit: false
  take_profit_pct: 0.10

# Costs
costs:
  commission:
    per_share: 0.005
    min_cost: 1.0
  slippage:
    volume_limit: 0.025
    price_impact: 0.1

# Backtest Configuration
backtest:
  data_frequency: daily          # 'daily' or 'minute'
  calendar: null                 # null = auto-detect, or 'XNYS', 'CRYPTO', 'FOREX'
```

### Step 2: Simplify strategy.py Template

```python
"""
Strategy Template for The Researcher's Cockpit
==============================================================================
QUICK START:
1. Copy this _template/ directory to strategies/{asset_class}/{strategy_name}/
2. Edit hypothesis.md with your trading rationale
3. Configure parameters.yaml with your parameter values
4. Implement compute_signals() with your strategy logic

RULES:
- NO hardcoded parameters - all params come from parameters.yaml
- Every strategy MUST have a hypothesis.md file
==============================================================================
"""

from zipline.api import (
    symbol, order_target_percent, record,
    schedule_function, date_rules, time_rules,
    set_commission, set_slippage, set_benchmark,
    get_open_orders, cancel_order,
)
from zipline.finance import commission, slippage
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for lib imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Optional Pipeline imports (only if use_pipeline=true)
_PIPELINE_AVAILABLE = False
try:
    from zipline.api import attach_pipeline, pipeline_output
    from zipline.pipeline import Pipeline
    from zipline.pipeline.data import EquityPricing
    from zipline.pipeline.factors import SimpleMovingAverage
    _PIPELINE_AVAILABLE = True
except ImportError:
    pass


def load_params():
    """Load parameters from parameters.yaml file."""
    import yaml
    params_path = Path(__file__).parent / 'parameters.yaml'
    if not params_path.exists():
        raise FileNotFoundError(f"parameters.yaml not found at {params_path}")
    with open(params_path) as f:
        return yaml.safe_load(f)


def initialize(context):
    """
    Set up the strategy. Called once at backtest start.
    """
    params = load_params()
    context.params = params
    
    # Get asset symbol
    asset_symbol = params['strategy']['asset_symbol']
    context.asset = symbol(asset_symbol)
    
    # Initialize state
    context.in_position = False
    context.entry_price = 0.0
    
    # Get lookback period for signals
    context.lookback = params['strategy'].get('lookback_period', 30)
    
    # Set benchmark (optional, may fail for non-equity assets)
    try:
        set_benchmark(context.asset)
    except:
        pass
    
    # Pipeline setup (optional)
    context.use_pipeline = params['strategy'].get('use_pipeline', False)
    if context.use_pipeline and _PIPELINE_AVAILABLE:
        attach_pipeline(make_pipeline(context.lookback), 'my_pipeline')
    
    # Configure commission
    comm = params.get('costs', {}).get('commission', {})
    set_commission(us_equities=commission.PerShare(
        cost=comm.get('per_share', 0.005),
        min_trade_cost=comm.get('min_cost', 1.0)
    ))
    
    # Configure slippage
    slip = params.get('costs', {}).get('slippage', {})
    set_slippage(us_equities=slippage.VolumeShareSlippage(
        volume_limit=slip.get('volume_limit', 0.025),
        price_impact=slip.get('price_impact', 0.1)
    ))
    
    # Schedule trading function
    freq = params['strategy'].get('rebalance_frequency', 'daily')
    minutes = params['strategy'].get('minutes_after_open', 30)
    
    if freq == 'daily':
        schedule_function(rebalance, date_rules.every_day(), 
                         time_rules.market_open(minutes=minutes))
    elif freq == 'weekly':
        schedule_function(rebalance, date_rules.week_start(), 
                         time_rules.market_open(minutes=minutes))
    elif freq == 'monthly':
        schedule_function(rebalance, date_rules.month_start(), 
                         time_rules.market_open(minutes=minutes))
    
    # Schedule stop loss check
    if params.get('risk', {}).get('use_stop_loss', False):
        schedule_function(check_stop_loss, date_rules.every_day(),
                         time_rules.market_open(minutes=1))


def make_pipeline(lookback: int = 30):
    """Create Pipeline for factor computation (optional)."""
    if not _PIPELINE_AVAILABLE:
        return None
    
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=lookback)
    return Pipeline(columns={'sma': sma}, screen=sma.isfinite())


def before_trading_start(context, data):
    """Called once per day before market open."""
    if context.use_pipeline and _PIPELINE_AVAILABLE:
        context.pipeline_data = pipeline_output('my_pipeline')
    else:
        context.pipeline_data = None


def compute_signals(context, data):
    """
    Compute trading signals based on your strategy logic.
    
    IMPLEMENT YOUR STRATEGY HERE.
    
    Returns:
        signal: 1 for buy, -1 for sell, 0 for hold
        additional_data: dict of values to record
    """
    # Skip if no data available
    if not data.can_trade(context.asset):
        return 0, {}
    
    # Get historical prices using data.history()
    # This works for ALL asset classes (equities, crypto, forex)
    prices = data.history(context.asset, 'close', context.lookback, '1d')
    
    if len(prices) < context.lookback:
        return 0, {}
    
    # Example: Simple moving average crossover
    sma = prices.mean()
    current_price = data.current(context.asset, 'close')
    
    # Generate signal
    if current_price > sma:
        signal = 1   # Buy
    elif current_price < sma:
        signal = -1  # Sell
    else:
        signal = 0   # Hold
    
    return signal, {'sma': sma, 'price': current_price}


def rebalance(context, data):
    """Main trading function called on schedule."""
    signal, metrics = compute_signals(context, data)
    
    if signal is None:
        return
    
    # Record metrics
    record(signal=signal, **metrics)
    
    # Cancel open orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Execute trades
    max_pos = context.params['position_sizing'].get('max_position_pct', 0.95)
    
    if signal == 1 and not context.in_position:
        order_target_percent(context.asset, max_pos)
        context.in_position = True
        context.entry_price = data.current(context.asset, 'close')
    elif signal == -1 and context.in_position:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0


def check_stop_loss(context, data):
    """Check and execute stop loss orders."""
    if not context.in_position or not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'close')
    risk = context.params.get('risk', {})
    
    stop_pct = risk.get('stop_loss_pct', 0.05)
    stop_price = context.entry_price * (1 - stop_pct)
    
    if current_price <= stop_price:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        record(stop_triggered=1)


def handle_data(context, data):
    """Called every bar. Use schedule_function instead for most strategies."""
    pass


def analyze(context, perf):
    """Post-backtest analysis. Prints summary statistics."""
    print("\n" + "=" * 60)
    print(f"STRATEGY RESULTS")
    print("=" * 60)
    
    returns = perf['returns']
    total_return = returns.sum()
    
    if len(returns) > 0 and returns.std() > 0:
        sharpe = np.sqrt(252) * returns.mean() / returns.std()
    else:
        sharpe = 0.0
    
    cumulative = (1 + returns).cumprod()
    max_dd = ((cumulative.cummax() - cumulative) / cumulative.cummax()).max()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
    print("=" * 60)
```

### Step 3: Update hypothesis.md Template

Add asset class considerations:

```markdown
# Strategy Hypothesis

## The Belief

**What market behavior are we exploiting?**

[Describe the inefficiency or pattern]

## Asset Class Considerations

**Asset:** [e.g., SPY, BTC-USD, EURUSD=X]
**Class:** [equities / crypto / forex]

**Market Characteristics:**
- Trading hours: [24/7 for crypto, 24/5 for forex, market hours for equities]
- Volatility profile: [describe expected volatility]
- Liquidity considerations: [note any liquidity concerns]

## The Conditions

**Works well in:**
- [condition 1]

**Fails in:**
- [condition 1]

## The Falsification

**What result would prove this wrong?**
- If Sharpe < [threshold] across [period], reject hypothesis
```

## Relevant Files

- `strategies/_template/strategy.py` - Main template
- `strategies/_template/parameters.yaml` - Parameter template
- `strategies/_template/hypothesis.md` - Hypothesis template

## Testing

After updating template:

```bash
# Create test strategy
cp -r strategies/_template strategies/equities/test_sma

# Edit parameters.yaml
# Set asset_symbol: SPY

# Run backtest
python scripts/run_backtest.py --strategy test_sma --asset-class equities

# Verify it works
cat results/test_sma/latest/metrics.json
```
