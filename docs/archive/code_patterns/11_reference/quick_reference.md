# Quick Reference

> Essential Zipline API at a glance.

## Algorithm Structure

```python
from zipline.api import *

def initialize(context):
    # Run once at start
    context.asset = symbol('AAPL')
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())

def before_trading_start(context, data):
    # Run daily before market open
    context.pipeline_output = pipeline_output('my_pipe')

def handle_data(context, data):
    # Run every bar (minute or daily)
    price = data.current(context.asset, 'price')

def analyze(context, perf):
    # Run once at end
    perf.portfolio_value.plot()
```

---

## Data Access

| Method | Description |
|--------|-------------|
| `data.current(asset, field)` | Current value |
| `data.current(assets, fields)` | Multiple current values |
| `data.history(asset, field, bars, freq)` | Historical data |
| `data.can_trade(asset)` | Tradability check |
| `data.is_stale(asset)` | Stale data check |

**Fields:** `'open'`, `'high'`, `'low'`, `'close'`, `'volume'`, `'price'`

---

## Orders

### Basic Orders

| Function | Description |
|----------|-------------|
| `order(asset, amount)` | Order shares |
| `order_value(asset, value)` | Order by dollar value |
| `order_percent(asset, percent)` | Order by portfolio % |

### Target Orders

| Function | Description |
|----------|-------------|
| `order_target(asset, target)` | Target share count |
| `order_target_value(asset, value)` | Target dollar value |
| `order_target_percent(asset, percent)` | Target portfolio % |

### Order Management

| Function | Description |
|----------|-------------|
| `get_order(order_id)` | Get order details |
| `get_open_orders(asset=None)` | Get open orders |
| `cancel_order(order_id)` | Cancel order |

### Execution Styles

```python
order(asset, 100)                              # Market
order(asset, 100, style=LimitOrder(50.0))      # Limit
order(asset, 100, style=StopOrder(45.0))       # Stop
order(asset, 100, style=StopLimitOrder(50, 45)) # Stop-Limit
```

---

## Scheduling

```python
schedule_function(
    func,
    date_rule=date_rules.every_day(),
    time_rule=time_rules.market_open()
)
```

### Date Rules

| Rule | Description |
|------|-------------|
| `every_day()` | Every trading day |
| `week_start(days_offset=0)` | Start of week |
| `week_end(days_offset=0)` | End of week |
| `month_start(days_offset=0)` | Start of month |
| `month_end(days_offset=0)` | End of month |

### Time Rules

| Rule | Description |
|------|-------------|
| `market_open(offset=0)` | Minutes after open |
| `market_close(offset=0)` | Minutes before close |

---

## Asset Lookup

| Function | Description |
|----------|-------------|
| `symbol('AAPL')` | Single asset |
| `symbols('AAPL', 'MSFT')` | Multiple assets |
| `sid(24)` | By security ID |
| `future_symbol('ES', '2024-03')` | Future contract |

---

## Portfolio Access

```python
context.portfolio.cash              # Available cash
context.portfolio.portfolio_value   # Total value
context.portfolio.positions         # Dict of positions
context.portfolio.returns           # Cumulative returns

# Position details
pos = context.portfolio.positions[asset]
pos.amount                          # Shares held
pos.cost_basis                      # Average cost
pos.last_sale_price                 # Current price
```

---

## Pipeline (Quick)

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume

def make_pipeline():
    returns = Returns(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    return Pipeline(
        columns={
            'returns': returns,
            'volume': volume
        },
        screen=volume.top(500)
    )

def initialize(context):
    attach_pipeline(make_pipeline(), 'my_pipe')

def before_trading_start(context, data):
    output = pipeline_output('my_pipe')
```

---

## Simulation Settings

```python
def initialize(context):
    # Commission
    set_commission(us_equities=commission.PerShare(0.001))
    
    # Slippage
    set_slippage(us_equities=slippage.VolumeShareSlippage(0.1, 0.1))
    
    # Benchmark
    set_benchmark(symbol('SPY'))
    
    # Cancel policy
    set_cancel_policy(cancel_policy.EODCancel())
```

---

## Recording

```python
def handle_data(context, data):
    record(
        price=data.current(context.asset, 'price'),
        cash=context.portfolio.cash
    )
```

---

## run_algorithm()

```python
from zipline import run_algorithm
import pandas as pd

result = run_algorithm(
    start=pd.Timestamp('2020-01-01', tz='UTC'),
    end=pd.Timestamp('2020-12-31', tz='UTC'),
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    bundle='quandl'
)
```

---

## Import Cheatsheet

```python
# Core API
from zipline.api import (
    order, order_target_percent,
    symbol, symbols,
    schedule_function,
    date_rules, time_rules,
    record, get_open_orders,
    set_commission, set_slippage,
    attach_pipeline, pipeline_output
)

# Commission/Slippage
from zipline.finance import commission, slippage

# Pipeline
from zipline.pipeline import Pipeline, CustomFactor
from zipline.pipeline.factors import Returns, AverageDollarVolume, VWAP
from zipline.pipeline.filters import StaticAssets
from zipline.pipeline.data import USEquityPricing

# Running
from zipline import run_algorithm
```
