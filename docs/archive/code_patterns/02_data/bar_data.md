# BarData

> Interface for accessing price and volume data during algorithm execution.

## Class Definition

```python
class zipline.protocol.BarData
```

An instance is passed as `data` to `handle_data()` and `before_trading_start()`.

## Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_portal` | DataPortal | Bar pricing data provider |
| `simulation_dt_func` | callable | Returns current simulation time |
| `data_frequency` | str | `'minute'` or `'daily'` |
| `restrictions` | Restrictions | Restricted assets information |

## Methods

### current()

Returns current value of fields for assets.

```python
data.current(assets, fields)
```

**Parameters:**
- `assets`: Asset or iterable of Assets
- `fields`: str or iterable of str
  - Valid: `'price'`, `'open'`, `'high'`, `'low'`, `'close'`, `'volume'`, `'last_traded'`

**Returns:** Scalar, pd.Series, or pd.DataFrame depending on input types.

### history()

Returns trailing window of historical data.

```python
data.history(assets, fields, bar_count, frequency)
```

**Parameters:**
- `assets`: Asset or iterable of Assets
- `fields`: str or iterable of str
- `bar_count`: int - Number of bars
- `frequency`: str - `'1d'` or `'1m'`

**Returns:** pd.Series, pd.DataFrame, or pd.DataFrame with MultiIndex.

### can_trade()

Checks if asset is tradeable at current time.

```python
data.can_trade(assets)
```

**Returns:** bool or pd.Series[bool]

**True when:**
1. Asset is alive for current session
2. Asset's exchange is open
3. Asset has a known last price

### is_stale()

Checks if asset has no trade data for current time.

```python
data.is_stale(assets)
```

**Returns:** bool or pd.Series[bool]

## Return Type Rules

| assets | fields | Return Type |
|--------|--------|-------------|
| single | single | scalar |
| single | list | pd.Series (index=fields) |
| list | single | pd.Series (index=assets) |
| list | list | pd.DataFrame (index=assets, columns=fields) |

## Examples

### Single Asset, Single Field

```python
def handle_data(context, data):
    price = data.current(context.asset, 'price')
    # Returns: float (e.g., 150.25)
```

### Single Asset, Multiple Fields

```python
def handle_data(context, data):
    ohlc = data.current(context.asset, ['open', 'high', 'low', 'close'])
    # Returns: pd.Series with index ['open', 'high', 'low', 'close']
```

### Multiple Assets, Single Field

```python
def handle_data(context, data):
    prices = data.current(context.assets, 'price')
    # Returns: pd.Series with index = assets
```

### Multiple Assets, Multiple Fields

```python
def handle_data(context, data):
    ohlcv = data.current(context.assets, ['open', 'high', 'low', 'close', 'volume'])
    # Returns: pd.DataFrame (rows=assets, columns=fields)
```

### Historical Data

```python
def handle_data(context, data):
    # Get 20-day price history
    hist = data.history(context.asset, 'price', 20, '1d')
    # Returns: pd.Series with DatetimeIndex
    
    # Calculate 20-day moving average
    ma_20 = hist.mean()
    
    # Get OHLCV history for multiple assets
    multi_hist = data.history(context.assets, ['close', 'volume'], 10, '1d')
    # Returns: pd.DataFrame with MultiIndex (date, asset)
```

### Trading Checks

```python
def handle_data(context, data):
    if data.can_trade(context.asset):
        current_price = data.current(context.asset, 'price')
        order(context.asset, 100)
    
    # Check multiple assets
    tradeable = data.can_trade(context.assets)
    for asset in context.assets[tradeable]:
        order(asset, 10)
```

## Price Field Behavior

- `'price'`: Last known close, forward-filled, adjusted for splits/dividends
- `'open'`, `'high'`, `'low'`, `'close'`: Current bar values (NaN if no trades)
- `'volume'`: Current bar volume (0 if no trades)
- `'last_traded'`: datetime of last trade (pd.NaT if never traded)

## See Also

- [current()](current.md)
- [history()](history.md)
- [can_trade()](can_trade.md)
