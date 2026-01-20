# Asset Types

> Classes representing tradeable securities.

## Asset (Base Class)

```python
class zipline.assets.Asset
```

Base class for all tradeable assets.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sid` | int | Unique security identifier |
| `symbol` | str | Ticker symbol |
| `asset_name` | str | Full asset name |
| `exchange` | str | Exchange code |
| `exchange_full` | str | Full exchange name |
| `exchange_info` | ExchangeInfo | Exchange details |
| `country_code` | str | ISO 3166 alpha-2 country code |
| `start_date` | pd.Timestamp | First trading date |
| `end_date` | pd.Timestamp | Last trading date |
| `tick_size` | float | Minimum price increment |
| `auto_close_date` | pd.Timestamp | Auto-liquidation date |

### Methods

```python
# Check if asset is alive on a given date
asset.is_alive_for_session(session_label)

# Check if exchange is open at given minute
asset.is_exchange_open(dt_minute)

# Convert to dictionary
asset.to_dict()

# Build from dictionary
Asset.from_dict(d)
```

### Example

```python
def handle_data(context, data):
    asset = context.asset
    
    print(f"Symbol: {asset.symbol}")
    print(f"Exchange: {asset.exchange}")
    print(f"Started: {asset.start_date}")
    print(f"SID: {asset.sid}")
```

---

## Equity

Represents partial ownership in a company, trust, or partnership.

```python
class zipline.assets.Equity
```

Inherits all attributes from `Asset`.

### Usage

```python
def initialize(context):
    context.stock = symbol('AAPL')  # Returns Equity object
    
def handle_data(context, data):
    # Type check if needed
    from zipline.assets import Equity
    if isinstance(context.stock, Equity):
        order(context.stock, 100)
```

---

## Future

Represents ownership of a futures contract.

```python
class zipline.assets.Future
```

### Additional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `root_symbol` | str | Root symbol (e.g., 'CL' for crude oil) |
| `notice_date` | pd.Timestamp | First notice date |
| `expiration_date` | pd.Timestamp | Contract expiration |
| `multiplier` | float | Contract multiplier |

### Usage

```python
def initialize(context):
    context.contract = future_symbol('CLF21')  # Returns Future object
    
def handle_data(context, data):
    # Futures have exposure = shares * price * multiplier
    multiplier = context.contract.multiplier
    
    from zipline.assets import Future
    if isinstance(context.contract, Future):
        order(context.contract, 1)
```

---

## AssetConvertible

ABC for types that can be converted to Asset identifiers.

```python
class zipline.assets.AssetConvertible
```

Includes:
- `Asset` (and subclasses)
- `str` (symbols)
- `Integral` (sids)

---

## Working with Assets

### Check Asset Type

```python
from zipline.assets import Asset, Equity, Future

def handle_data(context, data):
    for asset in context.universe:
        if isinstance(asset, Equity):
            handle_equity(asset, data)
        elif isinstance(asset, Future):
            handle_future(asset, data)
```

### Asset Comparison

```python
def handle_data(context, data):
    # Assets compare by sid
    if context.asset1 == context.asset2:
        print("Same asset")
    
    # Can be used as dict keys
    positions = {
        context.asset1: 100,
        context.asset2: 200
    }
```

### Asset in Portfolio

```python
def handle_data(context, data):
    for asset, position in context.portfolio.positions.items():
        print(f"{asset.symbol}: {position.amount} shares @ ${position.cost_basis:.2f}")
```

---

## Trading Date Awareness

```python
def handle_data(context, data):
    today = get_datetime().date()
    
    # Check if asset was trading
    if context.asset.is_alive_for_session(today):
        if data.can_trade(context.asset):
            order(context.asset, 100)
    else:
        log.warn(f"{context.asset.symbol} not trading on {today}")
```

---

## Notes

- SID (Security ID) is unique across all assets
- Symbol can change over time (ticker changes)
- Use `set_symbol_lookup_date` for historical symbol resolution
- `auto_close_date` is typically 3 days after `end_date`

---

## See Also

- [Asset Lookup](asset_lookup.md)
- [Asset Finder](asset_finder.md)
- [Trading Controls](trading_controls.md)
