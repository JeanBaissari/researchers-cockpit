# Built-in Filters

> Pre-built filters for common screening operations.

## Overview

Built-in filters provide ready-to-use boolean screening for Pipeline. They complement custom filters created from factor comparisons.

---

## Asset Selection Filters

### StaticAssets

Filter to a fixed set of assets.

```python
from zipline.pipeline.filters import StaticAssets

def initialize(context):
    my_universe = symbols('AAPL', 'MSFT', 'GOOGL', 'AMZN')
    static_filter = StaticAssets(my_universe)
```

Use in Pipeline:

```python
def make_pipeline():
    my_stocks = StaticAssets(symbols('AAPL', 'MSFT', 'GOOGL'))
    
    return Pipeline(
        columns={'price': USEquityPricing.close.latest},
        screen=my_stocks
    )
```

### StaticSids

Filter to a fixed set of security IDs.

```python
from zipline.pipeline.filters import StaticSids

# Filter by known SIDs
known_sids = [24, 8554, 5061]  # AAPL, SPY, etc.
sid_filter = StaticSids(known_sids)
```

---

## Universe Filters

### QTradableStocksUS

Filter for liquid, tradeable US equities (if available in your data).

```python
from zipline.pipeline.filters import QTradableStocksUS

def make_pipeline():
    universe = QTradableStocksUS()
    
    return Pipeline(
        columns={'momentum': Returns(window_length=20)},
        screen=universe
    )
```

### Q500US / Q1500US / Q3000US

Pre-defined universes of top US stocks by market cap (data-dependent).

```python
from zipline.pipeline.filters import Q500US

def make_pipeline():
    return Pipeline(screen=Q500US())
```

---

## Creating Filters from Factors

Most filters are created dynamically from factor operations:

### Comparison Filters

```python
from zipline.pipeline.factors import AverageDollarVolume, Returns

volume = AverageDollarVolume(window_length=20)
momentum = Returns(window_length=20)

# Comparison operators create filters
high_volume = volume > 1000000
positive_returns = momentum > 0
cheap = USEquityPricing.close.latest < 50
```

### Ranking Filters

```python
# Top/bottom N
top_100_volume = volume.top(100)
bottom_50_momentum = momentum.bottom(50)

# Percentile range
mid_volume = volume.percentile_between(25, 75)
```

### Null Checks

```python
has_volume = volume.notnull()
has_data = momentum.notnan()
```

---

## Combining Filters

### AND (&)

```python
# Both conditions must be true
liquid_and_positive = high_volume & positive_returns
```

### OR (|)

```python
# Either condition can be true
extreme_momentum = momentum.top(50) | momentum.bottom(50)
```

### NOT (~)

```python
# Invert the filter
not_restricted = ~StaticAssets(restricted_stocks)
```

### Complex Combinations

```python
universe = (
    (volume.top(500)) &
    (momentum.notnull()) &
    (~StaticAssets(excluded_stocks)) &
    (USEquityPricing.close.latest > 5)
)
```

---

## Using as Screen

```python
def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    liquid = volume.top(500)
    
    return Pipeline(
        columns={'volume': volume},
        screen=liquid  # Only output assets passing this filter
    )
```

---

## Using as Mask

```python
def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    momentum = Returns(window_length=20)
    
    liquid = volume.top(500)
    
    # Only rank within liquid stocks
    momentum_rank = momentum.rank(mask=liquid)
    
    # Top 50 of liquid stocks only
    longs = momentum.top(50, mask=liquid)
    
    return Pipeline(
        columns={'rank': momentum_rank, 'longs': longs},
        screen=liquid
    )
```

---

## Common Patterns

### Exclude Specific Assets

```python
def make_pipeline():
    excluded = StaticAssets(symbols('GE', 'F', 'SIRI'))
    tradeable = ~excluded
    
    return Pipeline(screen=tradeable)
```

### Sector-Neutral Selection

```python
def make_pipeline():
    momentum = Returns(window_length=20)
    sector = Sector()  # Classifier
    universe = volume.top(500)
    
    # Top 5 per sector
    longs = momentum.top(5, mask=universe, groupby=sector)
    
    return Pipeline(screen=longs)
```

---

## See Also

- [Filters](../06_pipeline/filters.md)
- [Factors](../06_pipeline/factors.md)
- [Pipeline Overview](../06_pipeline/pipeline_overview.md)
