# Filters

> Pipeline expressions that produce boolean outputs.

## Filter Class

```python
class zipline.pipeline.Filter(
    inputs=NotSpecified,
    outputs=NotSpecified,
    window_length=NotSpecified,
    mask=NotSpecified,
    domain=NotSpecified
)
```

Filters compute True/False for each asset, used for screening and masking.

---

## Creating Filters

### From Factor Comparisons

```python
from zipline.pipeline.factors import Returns, AverageDollarVolume

momentum = Returns(window_length=20)
volume = AverageDollarVolume(window_length=20)

# Comparison operators
positive_momentum = momentum > 0
high_volume = volume > 1000000
cheap = some_price_factor < 50

# Equality
at_threshold = momentum.eq(0.05)
```

### From Factor Methods

```python
# Top/Bottom N
top_100 = volume.top(100)
bottom_50 = momentum.bottom(50)

# Percentile range
mid_volume = volume.percentile_between(25, 75)

# Missing data
has_data = momentum.notnull()
valid = momentum.notnan()
```

---

## Combining Filters

### AND (&)

Both conditions must be True.

```python
# Liquid AND positive momentum
tradeable = high_volume & positive_momentum
```

### OR (|)

Either condition can be True.

```python
# Top momentum OR bottom momentum
extreme = top_momentum | bottom_momentum
```

### NOT (~)

Invert the filter.

```python
# Not in restricted list
allowed = ~restricted
```

### Complex Combinations

```python
# (A AND B) OR (C AND NOT D)
final_filter = (filter_a & filter_b) | (filter_c & ~filter_d)
```

---

## if_else()

Select values based on filter condition.

```python
filter.if_else(if_true, if_false)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `if_true` | Term | Value when True |
| `if_false` | Term | Value when False |

### Example

```python
# Use different factors based on condition
high_vol = volume > 1000000

# High volume: use momentum
# Low volume: use different alpha
alpha = high_vol.if_else(momentum_factor, value_factor)
```

### Visual Example

```
              AAPL   MSFT    MCD     BK
condition:    True  False   True  False

if_true:       1.0    2.0    3.0    4.0
if_false:     10.0   20.0   30.0   40.0

result:        1.0   20.0    3.0   40.0
```

---

## Using as Screen

```python
from zipline.pipeline import Pipeline

def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    
    # Only output assets passing this filter
    liquid = volume.top(500)
    
    return Pipeline(
        columns={'volume': volume},
        screen=liquid  # Reduces output to 500 rows
    )
```

---

## Using as Mask

```python
# Only rank liquid stocks
momentum = Returns(window_length=20)
volume = AverageDollarVolume(window_length=20)
liquid = volume.top(500)

# Rank only considers liquid stocks
momentum_rank = momentum.rank(mask=liquid)

# Top 50 of liquid stocks
top_momentum = momentum.top(50, mask=liquid)
```

---

## Built-in Filters

### StaticAssets

Filter to specific assets.

```python
from zipline.pipeline.filters import StaticAssets

def initialize(context):
    my_stocks = symbols('AAPL', 'MSFT', 'GOOGL')
    static = StaticAssets(my_stocks)
```

### StaticSids

Filter by security IDs.

```python
from zipline.pipeline.filters import StaticSids

known_sids = [24, 8554, 5061]
static = StaticSids(known_sids)
```

---

## Common Patterns

### Universe Definition

```python
def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    price = USEquityPricing.close.latest
    
    # Liquid + priced reasonably
    liquid = volume.top(1500)
    priced_ok = (price > 5) & (price < 1000)
    has_data = volume.notnull() & price.notnull()
    
    universe = liquid & priced_ok & has_data
    
    return Pipeline(screen=universe)
```

### Long/Short Selection

```python
def make_pipeline():
    alpha = SomeAlphaFactor()
    universe = volume.top(500)
    
    # Top 50 for longs, bottom 50 for shorts
    longs = alpha.top(50, mask=universe)
    shorts = alpha.bottom(50, mask=universe)
    
    return Pipeline(
        columns={
            'alpha': alpha,
            'longs': longs,
            'shorts': shorts,
        },
        screen=longs | shorts
    )
```

### Sector Neutral

```python
def make_pipeline():
    alpha = SomeAlphaFactor()
    sector = SectorClassifier()
    universe = volume.top(500)
    
    # Top 5 per sector
    longs = alpha.top(5, mask=universe, groupby=sector)
    
    return Pipeline(
        columns={'longs': longs},
        screen=longs
    )
```

---

## See Also

- [Pipeline Overview](pipeline_overview.md)
- [Factors](factors.md)
- [Built-in Filters](builtin_filters.md)
