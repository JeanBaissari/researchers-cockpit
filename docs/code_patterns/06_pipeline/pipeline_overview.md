# Pipeline Overview

> Pre-compute cross-sectional data for all assets before trading.

## What is Pipeline?

Pipeline computes factors, filters, and classifiers across your entire asset universe, executing before each trading day. Think of it as batch processing for alpha signals.

**Analogy**: If `handle_data` is like checking your inbox message by message, Pipeline is like running a search across your entire inbox at once.

---

## Pipeline Class

```python
class zipline.pipeline.Pipeline(columns=None, screen=None, domain=GENERIC)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | dict | Named expressions to compute |
| `screen` | Filter | Assets to include in output |
| `domain` | Domain | Asset universe domain |

---

## Basic Structure

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import AverageDollarVolume, Returns
from zipline.pipeline.filters import StaticAssets

def make_pipeline():
    # Factors compute values
    avg_volume = AverageDollarVolume(window_length=20)
    returns_5d = Returns(window_length=5)
    
    # Filters compute True/False
    liquid = avg_volume.top(500)
    
    # Combine into pipeline
    return Pipeline(
        columns={
            'volume': avg_volume,
            'returns': returns_5d,
        },
        screen=liquid  # Only include top 500 by volume
    )
```

---

## Attaching to Algorithm

```python
from zipline.api import attach_pipeline, pipeline_output

def initialize(context):
    attach_pipeline(make_pipeline(), 'my_pipeline')

def before_trading_start(context, data):
    # Get results as DataFrame
    output = pipeline_output('my_pipeline')
    
    # output.index = assets
    # output.columns = ['volume', 'returns']
    
    context.longs = output[output['returns'] > 0].index.tolist()
```

---

## attach_pipeline()

```python
zipline.api.attach_pipeline(pipeline, name, chunks=None, eager=True)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline` | Pipeline | Pipeline to attach |
| `name` | str | Name for retrieval |
| `chunks` | int | Days to compute at once |
| `eager` | bool | Compute before `before_trading_start` |

### Returns

The same Pipeline object.

---

## pipeline_output()

```python
zipline.api.pipeline_output(name)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Pipeline name |

### Returns

`pd.DataFrame` - Results for current day. Index is assets, columns are factor names.

### Raises

`NoSuchPipeline` - Pipeline name not found.

---

### Best Practices

-   **Leverage for Universe Selection:** Use Pipeline to efficiently filter a large universe of assets down to a manageable watchlist based on fundamental or technical criteria.
-   **Factor Pre-computation:** All computationally intensive factor calculations should be done in the Pipeline to avoid re-calculating them inside `handle_data` or `before_trading_start`.
-   **Cross-sectional Analysis:** Pipeline excels at cross-sectional comparisons (e.g., top N stocks by momentum, relative valuation) which are difficult to do efficiently otherwise.
-   **Keep it focused:** Each pipeline should serve a specific purpose (e.g., liquidity screening, momentum calculation).
-   **Optimize factors:** Use built-in factors whenever possible, and optimize custom factors for performance.
-   **Clear naming:** Use descriptive names for your pipeline and its columns.
-   **Testing:** Thoroughly test your pipeline logic in isolation before integrating into a strategy.

---

## Pipeline with Minute Data

When working with minute-frequency data, the Pipeline API behaves similarly to daily data, but the `window_length` of factors will refer to minutes instead of days. This allows for very granular pre-computation of factors and signals.

### Example: Minute-frequency Pipeline

```python
from zipline.api import (
    attach_pipeline, pipeline_output,
    order_target_percent, schedule_function,
    date_rules, time_rules
)
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage
from zipline.pipeline.data import USEquityPricing

def make_pipeline():
    # Example: 15-minute Simple Moving Average
    # For minute data, window_length refers to minutes
    sma_15m = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=15)
    
    return Pipeline(
        columns={
            'sma_15m': sma_15m,
        },
        screen=sma_15m.isfinite() # Only consider assets with a valid 15-minute SMA
    )

def initialize(context):
    attach_pipeline(make_pipeline(), 'minute_pipeline')
    
    # Schedule function to run every minute or at specific times
    schedule_function(
        rebalance_minute,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open()
    ) # Runs at every minute bar after market open

def before_trading_start(context, data):
    context.minute_output = pipeline_output('minute_pipeline')
    context.minute_universe = context.minute_output.index.tolist()

def rebalance_minute(context, data):
    # Access minute-level pipeline data
    if context.asset in context.minute_universe:
        sma_value = context.minute_output.loc[context.asset]['sma_15m']
        current_price = data.current(context.asset, 'price')
        
        # Example: Simple minute-level signal
        if current_price > sma_value:
            order_target_percent(context.asset, 0.5)
        elif current_price < sma_value:
            order_target_percent(context.asset, 0)

def handle_data(context, data):
    pass
```

---

## Complete Example

```python
from zipline.api import (
    attach_pipeline, pipeline_output,
    order_target_percent, schedule_function,
    date_rules, time_rules
)
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import AverageDollarVolume, Returns
from zipline.pipeline.data import USEquityPricing

def make_pipeline():
    # Factor: 10-day momentum
    momentum = Returns(window_length=10)
    
    # Factor: Average dollar volume
    volume = AverageDollarVolume(window_length=20)
    
    # Filter: liquid stocks
    liquid = volume.top(500)
    
    # Filter: positive momentum
    positive_momentum = momentum > 0
    
    return Pipeline(
        columns={
            'momentum': momentum,
            'volume': volume,
        },
        screen=liquid & positive_momentum
    )

def initialize(context):
    attach_pipeline(make_pipeline(), 'momentum_pipeline')
    
    schedule_function(
        rebalance,
        date_rules.week_start(),
        time_rules.market_open(hours=1)
    )

def before_trading_start(context, data):
    context.output = pipeline_output('momentum_pipeline')
    
    # Top 10 by momentum
    ranked = context.output.sort_values('momentum', ascending=False)
    context.longs = ranked.head(10).index.tolist()

def rebalance(context, data):
    # Equal weight top 10
    weight = 1.0 / len(context.longs) if context.longs else 0
    
    for asset in context.longs:
        if data.can_trade(asset):
            order_target_percent(asset, weight)
    
    # Exit positions not in longs
    for asset in context.portfolio.positions:
        if asset not in context.longs:
            order_target_percent(asset, 0)

def handle_data(context, data):
    pass
```

---

## Pipeline vs handle_data

| Aspect | Pipeline | handle_data |
|--------|----------|-------------|
| When | Once per day (before open) | Every bar |
| Scope | All assets at once | One bar at a time |
| Use | Screening, ranking | Order execution |
| Data | Historical factors | Current prices |

---

## Key Concepts

- **Factor**: Produces numeric values (float)
- **Filter**: Produces boolean values (True/False)
- **Classifier**: Produces categorical values (int/str)
- **Screen**: Filter that limits output rows

---

## See Also

- [Factors](factors.md)
- [Filters](filters.md)
- [Custom Factors](custom_factors.md)
- [Built-in Factors](builtin_factors.md)
