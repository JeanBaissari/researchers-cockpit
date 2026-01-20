# can_trade() and is_stale()

> Methods for checking asset tradability and data freshness.

## can_trade()

### Signature

```python
data.can_trade(assets)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assets` | Asset or iterable[Asset] | Asset(s) to check |

### Returns

`bool` or `pd.Series[bool]`

### Conditions for True

All must be true:

1. **Asset is alive** for the current session
2. **Exchange is open** at current simulation time (or next market minute)
3. **Known last price** exists for the asset

### Exchange Hours Note

If asset's exchange differs from simulation calendar:
- Returns `False` when simulation runs during hours when asset's exchange is closed
- Example: CMES calendar simulation + NYSE-listed stock = `False` at 3:15 AM Eastern

### Examples

```python
def handle_data(context, data):
    # Single asset check
    if data.can_trade(context.asset):
        order(context.asset, 100)
    
    # Multiple assets
    tradeable = data.can_trade(context.universe)
    
    # Filter to tradeable only
    for asset in context.universe:
        if tradeable[asset]:
            order(asset, 10)
    
    # Pandas-style filtering
    universe_series = pd.Series(context.universe)
    tradeable_assets = universe_series[tradeable]
```

### Common Pattern: Safe Order

```python
def safe_order(context, data, asset, amount):
    """Only order if asset is tradeable."""
    if data.can_trade(asset):
        return order(asset, amount)
    else:
        log.warn(f"Cannot trade {asset.symbol}")
        return None

def handle_data(context, data):
    safe_order(context, data, context.asset, 100)
```

---

## is_stale()

### Signature

```python
data.is_stale(assets)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assets` | Asset or iterable[Asset] | Asset(s) to check |

### Returns

`bool` or `pd.Series[bool]`

### Conditions

- Returns `True` if asset is **alive** but has **no trade data** for current time
- Returns `False` if asset has **never traded**

### Non-Market Time Behavior

If current simulation time is not a valid market time:
- Uses current time to check if asset is alive
- Uses last market minute/day for trade data check

### Examples

```python
def handle_data(context, data):
    # Check staleness
    if data.is_stale(context.asset):
        log.info(f"{context.asset.symbol} has no recent trades")
        return
    
    # Multiple assets
    staleness = data.is_stale(context.universe)
    fresh_assets = [a for a in context.universe if not staleness[a]]
```

### Stale vs Can't Trade

```python
def handle_data(context, data):
    for asset in context.universe:
        can_trade = data.can_trade(asset)
        is_stale = data.is_stale(asset)
        
        if not can_trade and not is_stale:
            # Asset is delisted or exchange closed
            log.info(f"{asset.symbol}: Not tradeable, not stale (delisted?)")
        
        elif not can_trade and is_stale:
            # Asset exists but no recent data
            log.info(f"{asset.symbol}: Not tradeable, stale data")
        
        elif can_trade and is_stale:
            # Rare: can trade but no current bar data
            log.info(f"{asset.symbol}: Tradeable but stale")
        
        else:
            # Normal: can trade with fresh data
            order(asset, 10)
```

---

## Best Practices

### Always Check Before Trading

```python
def handle_data(context, data):
    # Bad: assumes asset is tradeable
    order(context.asset, 100)
    
    # Good: check first
    if data.can_trade(context.asset):
        order(context.asset, 100)
```

### Batch Checking

```python
def handle_data(context, data):
    # Efficient: single call for all assets
    tradeable_mask = data.can_trade(context.universe)
    
    # Less efficient: individual calls
    for asset in context.universe:
        if data.can_trade(asset):  # Separate call each time
            pass
```

### Combined Checks

```python
def handle_data(context, data):
    # Get both at once if needed
    can_trade = data.can_trade(context.universe)
    is_stale = data.is_stale(context.universe)
    
    # Fresh and tradeable
    good_assets = [
        a for a in context.universe 
        if can_trade[a] and not is_stale[a]
    ]
```

## See Also

- [BarData](bar_data.md)
- [current()](current.md)
- [Trading Controls](../05_assets/trading_controls.md)
