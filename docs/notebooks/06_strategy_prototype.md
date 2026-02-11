# 06 - Strategy Prototype Notebook

**File**: `notebooks/06_strategy_prototype.ipynb`
**Purpose**: Rapid prototyping of new strategy ideas before formalizing into strategy directories
**Architecture**: v1.12.0 NO WRAPPERS

## Overview

The Strategy Prototype notebook is your playground for testing trading hypotheses quickly. It allows inline strategy definition without creating a formal strategy directory structure.

## Why Use This Notebook

### Advantages ✓

- **Fast iteration**: Modify code and re-run immediately
- **No boilerplate**: Skip directory creation and YAML files
- **Immediate feedback**: See results in seconds
- **Learning tool**: Understand Zipline API interactively

### When to Formalize

Move to `strategies/{asset_class}/{name}/` when:
- Strategy shows promise (Sharpe > 0.5)
- Ready for optimization
- Need version control
- Planning production deployment

## Configuration

```python
# Strategy Configuration
strategy_name = 'prototype_sma_cross'
asset_symbol = 'SPY'
bundle_name = None  # Auto-detect

# Backtest Configuration
start_date = '2020-01-01'
end_date = '2023-12-31'
capital_base = 100000.0

# Strategy Parameters
params = {
    'fast_period': 10,
    'slow_period': 30,
    'position_size': 0.95,
}
```

**Customization**:
- `params`: Your strategy-specific parameters
- `asset_symbol`: Symbol to trade (must be in bundle)
- Date range and capital as needed

## Strategy Implementation

### Initialize Function

```python
def initialize(context):
    """
    Called once at start of backtest.
    Set up your strategy state here.
    """
    # Set asset
    context.asset = symbol(asset_symbol)

    # Store parameters
    context.fast_period = params['fast_period']
    context.slow_period = params['slow_period']

    # Initialize state
    context.invested = False

    # Set realistic costs
    set_commission(commission.PerShare(cost=0.001, min_trade_cost=1.0))
    set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025))
```

**What to include**:
- Asset selection
- Parameter storage
- State variables
- Commission/slippage models

### Handle Data Function

```python
def handle_data(context, data):
    """
    Called on each bar. Implement your trading logic here.
    """
    # Get historical prices (direct Zipline API)
    prices = data.history(
        context.asset,
        'close',
        context.slow_period + 1,
        '1d'
    )

    # Calculate indicators (direct pandas)
    fast_ma = prices.rolling(context.fast_period).mean().iloc[-1]
    slow_ma = prices.rolling(context.slow_period).mean().iloc[-1]

    # Trading logic
    if fast_ma > slow_ma and not context.invested:
        order_target_percent(context.asset, context.position_size)
        context.invested = True
    elif fast_ma < slow_ma and context.invested:
        order_target_percent(context.asset, 0.0)
        context.invested = False

    # Record for analysis
    record(
        signal=1 if context.invested else 0,
        fast_ma=fast_ma,
        slow_ma=slow_ma
    )
```

**What to implement**:
- Data fetching
- Indicator calculation
- Signal generation
- Order placement
- Recording for analysis

## Direct Zipline APIs Used

### Data Access

```python
# Get historical bars
prices = data.history(asset, 'close', bars, frequency)

# Get current price
current = data.current(asset, 'price')

# Check if tradeable
can_trade = data.can_trade(asset)
```

### Order Placement

```python
# Target percentage of portfolio
order_target_percent(asset, 0.95)  # 95% of capital

# Target number of shares
order_target(asset, 100)  # 100 shares

# Market order
order(asset, 50)  # Buy 50 shares
```

### Recording Data

```python
# Record custom variables for later analysis
record(
    signal=1,           # Buy/sell signal
    fast_ma=10.5,       # Indicator value
    price=100.23        # Current price
)
```

**Access recorded data**: Available in `perf` DataFrame after backtest.

## Run Backtest

```python
# Execute backtest
perf = run_algorithm(
    start=pd.Timestamp(start_date, tz='UTC'),
    end=pd.Timestamp(end_date, tz='UTC'),
    initialize=initialize,
    handle_data=handle_data,
    capital_base=capital_base,
    bundle=bundle_name,
)
```

**Direct API**: Uses Zipline's `run_algorithm()` directly (NO WRAPPERS).

## Analysis Features

### Metrics Calculation

```python
from lib.metrics import calculate_metrics

metrics = calculate_metrics(perf)
```

**Displays**:
- Total/Annual Return
- Sharpe/Sortino Ratio
- Max Drawdown
- Trade statistics

### Visualizations

```python
# Equity curve
plt.plot(perf.index, perf['portfolio_value'])

# Signals on price chart
plt.scatter(buy_signals.index, buy_signals['price'],
           marker='^', color='green')
```

**Plots generated**:
1. Equity curve
2. Drawdown chart
3. Price with buy/sell signals
4. Moving averages (if recorded)
5. Return distribution

## Common Patterns

### Multi-Timeframe Strategy

```python
def handle_data(context, data):
    # Daily trend
    daily_prices = data.history(context.asset, 'close', 100, '1d')
    trend = daily_prices.rolling(50).mean().iloc[-1]

    # Intraday signal
    hourly_prices = data.history(context.asset, 'close', 20, '1h')
    signal = hourly_prices.rolling(10).mean().iloc[-1]

    # Trade only if aligned
    if signal > trend and not context.invested:
        order_target_percent(context.asset, 0.9)
```

**Direct pandas**: Use `pandas.resample()` for aggregation (v1.12.0 NO WRAPPERS).

### Multiple Assets

```python
def initialize(context):
    context.assets = [
        symbol('SPY'),
        symbol('TLT'),
        symbol('GLD')
    ]

def handle_data(context, data):
    for asset in context.assets:
        prices = data.history(asset, 'close', 20, '1d')
        # Strategy logic for each asset
```

### Rebalancing

```python
from zipline.api import schedule_function, date_rules, time_rules

def initialize(context):
    # Rebalance monthly at market open
    schedule_function(
        rebalance,
        date_rules.month_start(),
        time_rules.market_open()
    )

def rebalance(context, data):
    # Rebalancing logic
    for asset, weight in target_weights.items():
        order_target_percent(asset, weight)
```

## Iteration Workflow

1. **Define hypothesis**: What are you testing?
2. **Set parameters**: In configuration cell
3. **Implement logic**: In initialize/handle_data
4. **Run backtest**: Execute cells
5. **Review results**: Check metrics and plots
6. **Iterate**: Modify and re-run
7. **Formalize**: When ready, migrate to strategy directory

## Troubleshooting

### "Symbol not found"

**Cause**: `asset_symbol` not in `bundle_name`
**Fix**: Check available symbols in `00_data_exploration.ipynb`

### "Insufficient data"

**Cause**: Not enough bars for indicators
**Fix**: Reduce `slow_period` or increase backtest start date

### "No trades executed"

**Cause**: Signal conditions never met
**Fix**:
- Check indicator calculations
- Verify signal logic
- Add debug `print()` statements in `handle_data()`

### "Performance very different from expected"

**Causes**:
- Forgot commission/slippage
- Look-ahead bias (using future data)
- Position sizing too aggressive/conservative

**Debug**:
- Add `record()` calls to track state
- Print intermediate values
- Compare to manual calculation

## Best Practices

### Do's ✓

1. **Start simple**: Test basic logic first, add complexity later
2. **Use record()**: Track all important variables
3. **Set realistic costs**: Include commission and slippage
4. **Validate assumptions**: Check if signals trigger as expected
5. **Test multiple periods**: Don't just test best-case scenario

### Don'ts ✗

1. **Don't skip data validation**: Check bundle quality first
2. **Don't optimize in notebook**: Use `02_optimize.ipynb` for that
3. **Don't forget state management**: Track `context.invested` etc.
4. **Don't use future data**: Avoid look-ahead bias
5. **Don't skip formalization**: Move to strategy directory when ready

## Formalization Guide

When ready to formalize:

```python
# 1. Uncomment formalization cell in notebook
# 2. It creates: strategies/{asset_class}/{strategy_name}/
# 3. Copy initialize() and handle_data() to strategy.py
# 4. Move params to parameters.yaml
# 5. Document hypothesis in hypothesis.md
# 6. Use scripts/run_backtest.py for future runs
```

**Manual steps**:
```bash
# Copy template
cp -r strategies/_template strategies/equities/my_strategy

# Edit files
vim strategies/equities/my_strategy/strategy.py
vim strategies/equities/my_strategy/parameters.yaml
vim strategies/equities/my_strategy/hypothesis.md

# Run formal backtest
python scripts/run_backtest.py --strategy equities/my_strategy
```

## Example Strategies

### Mean Reversion

```python
def handle_data(context, data):
    prices = data.history(context.asset, 'close', 20, '1d')
    mean = prices.mean()
    std = prices.std()
    current = data.current(context.asset, 'price')

    # Buy when 2 std devs below mean
    if current < mean - 2*std and not context.invested:
        order_target_percent(context.asset, 0.9)
        context.invested = True

    # Sell when back to mean
    elif current > mean and context.invested:
        order_target_percent(context.asset, 0.0)
        context.invested = False
```

### Momentum

```python
def handle_data(context, data):
    prices = data.history(context.asset, 'close', 252, '1d')

    # Calculate 12-month momentum
    momentum = (prices.iloc[-1] / prices.iloc[0]) - 1

    # Buy if positive momentum
    if momentum > 0 and not context.invested:
        order_target_percent(context.asset, 0.95)
        context.invested = True
    elif momentum < 0 and context.invested:
        order_target_percent(context.asset, 0.0)
        context.invested = False
```

## Related Documentation

- **[Strategy Template](../../strategies/_template/README.md)** - Formal structure
- **[Zipline API Reference](https://zipline.ml4trading.io/)** - Official docs
- **[01_backtest.ipynb](01_backtest.md)** - Formal backtest workflow
- **[02_optimize.ipynb](02_optimize.md)** - Parameter optimization

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
