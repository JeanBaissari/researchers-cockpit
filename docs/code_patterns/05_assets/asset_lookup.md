# Asset Lookup Functions

> Functions for retrieving assets by symbol or identifier.

## symbol()

Look up an Equity by ticker symbol.

```python
zipline.api.symbol(symbol_str, country_code=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol_str` | str | Ticker symbol |
| `country_code` | str | Two-letter country code (optional) |

### Returns

`zipline.assets.Equity`

### Raises

`SymbolNotFound` - Symbol not found on current lookup date.

### Example

```python
def initialize(context):
    context.asset = symbol('AAPL')
    context.msft = symbol('MSFT')
```

---

## symbols()

Look up multiple Equities at once.

```python
zipline.api.symbols(*args, country_code=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `*args` | str | Ticker symbols |
| `country_code` | str | Two-letter country code (optional) |

### Returns

`list[zipline.assets.Equity]`

### Raises

`SymbolNotFound` - Any symbol not found.

### Example

```python
def initialize(context):
    context.assets = symbols('AAPL', 'MSFT', 'GOOGL', 'AMZN')
    
    # Unpack to individual variables
    context.tech1, context.tech2, context.tech3, context.tech4 = symbols(
        'AAPL', 'MSFT', 'GOOGL', 'AMZN'
    )
```

---

## sid()

Look up an Asset by its unique identifier.

```python
zipline.api.sid(sid)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sid` | int | Security identifier |

### Returns

`zipline.assets.Asset`

### Raises

`SidsNotFound` - SID doesn't exist.

### Example

```python
def initialize(context):
    # SID is stable even if symbol changes
    context.asset = sid(24)
    
def handle_data(context, data):
    # SID from position
    for asset in context.portfolio.positions:
        print(f"SID {asset.sid}: {asset.symbol}")
```

---

## future_symbol()

Look up a futures contract by symbol.

```python
zipline.api.future_symbol(symbol)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Futures contract symbol |

### Returns

`zipline.assets.Future`

### Raises

`SymbolNotFound` - Contract not found.

### Example

```python
def initialize(context):
    # Crude oil January 2021
    context.oil = future_symbol('CLF21')
    
    # E-mini S&P 500
    context.es = future_symbol('ESH21')
```

---

## set_symbol_lookup_date()

Set the date for symbol resolution.

```python
zipline.api.set_symbol_lookup_date(dt)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `dt` | datetime | Lookup date |

### Purpose

Symbols can map to different assets over time:
- Ticker changes
- Mergers/acquisitions
- Symbol reuse

### Example

```python
def initialize(context):
    # Look up GOOG before Alphabet restructuring
    set_symbol_lookup_date(pd.Timestamp('2015-01-01', tz='utc'))
    context.old_google = symbol('GOOG')
    
    # Look up current
    set_symbol_lookup_date(pd.Timestamp('2023-01-01', tz='utc'))
    context.new_google = symbol('GOOG')
```

---

## Common Patterns

### Initialize Universe

```python
def initialize(context):
    context.universe = symbols(
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'TSLA', 'NVDA', 'JPM', 'V', 'JNJ'
    )
```

### Dynamic Universe from Pipeline

```python
def before_trading_start(context, data):
    output = pipeline_output('my_pipeline')
    context.longs = output[output['longs']].index.tolist()
    context.shorts = output[output['shorts']].index.tolist()
```

### Handle Missing Symbols

```python
def initialize(context):
    try:
        context.asset = symbol('AAPL')
    except SymbolNotFound:
        log.error("AAPL not found in bundle")
        context.asset = None

def handle_data(context, data):
    if context.asset and data.can_trade(context.asset):
        order(context.asset, 100)
```

### SID-Based References

```python
def initialize(context):
    # Store SIDs instead of symbols for stability
    context.asset_sids = [24, 8554, 5061]  # AAPL, SPY, etc.

def handle_data(context, data):
    for asset_sid in context.asset_sids:
        asset = sid(asset_sid)
        if data.can_trade(asset):
            order(asset, 100)
```

### International Assets

```python
def initialize(context):
    # US stocks
    context.us_stocks = symbols('AAPL', 'MSFT', country_code='US')
    
    # Specific country
    context.stock = symbol('VOD', country_code='GB')
```

---

## Notes

- `symbol()` uses current simulation date for lookup by default
- Use `set_symbol_lookup_date()` for historical symbol resolution
- SIDs are immutable; symbols can change
- Future symbols include root + month code + year

---

## See Also

- [Asset Types](asset_types.md)
- [Asset Finder](asset_finder.md)
- [Pipeline](../06_pipeline/pipeline_overview.md)
