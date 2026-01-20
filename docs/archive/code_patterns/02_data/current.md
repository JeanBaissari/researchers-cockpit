# data.current()

> Get current values of fields for given assets.

## Signature

```python
data.current(assets, fields)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assets` | Asset or iterable[Asset] | Asset(s) to query |
| `fields` | str or iterable[str] | Field(s) to retrieve |

## Valid Fields

| Field | Description | Return Type |
|-------|-------------|-------------|
| `'price'` | Last known close, forward-filled, adjusted | float |
| `'open'` | Current bar open | float |
| `'high'` | Current bar high | float |
| `'low'` | Current bar low | float |
| `'close'` | Current bar close | float |
| `'volume'` | Current bar volume | int |
| `'last_traded'` | Datetime of last trade | pd.Timestamp |

## Return Types

| Input | Return |
|-------|--------|
| Single asset + single field | Scalar |
| Single asset + multiple fields | pd.Series (index=fields) |
| Multiple assets + single field | pd.Series (index=assets) |
| Multiple assets + multiple fields | pd.DataFrame |

## Field Behavior Details

### price

- Returns last known close price
- Forward-filled from previous bars if no current trade
- Adjusted for splits, dividends, mergers
- Returns NaN if asset never traded or delisted

### open, high, low, close

- Returns value for current bar only
- Returns NaN if no trades this bar
- NOT forward-filled

### volume

- Returns trade volume for current bar
- Returns 0 if no trades this bar

### last_traded

- Returns datetime of most recent trade
- Returns pd.NaT if never traded
- Works even for delisted assets

## Examples

### Basic Price Check

```python
def handle_data(context, data):
    price = data.current(context.asset, 'price')
    print(f"Current price: {price}")
```

### Get OHLCV

```python
def handle_data(context, data):
    bars = data.current(context.asset, ['open', 'high', 'low', 'close', 'volume'])
    print(f"Open: {bars['open']}, Close: {bars['close']}")
```

### Multiple Assets

```python
def handle_data(context, data):
    prices = data.current([context.stock1, context.stock2], 'price')
    
    # Access by asset
    price1 = prices[context.stock1]
    price2 = prices[context.stock2]
    
    spread = price1 - price2
```

### Full Matrix

```python
def handle_data(context, data):
    matrix = data.current(
        context.universe, 
        ['price', 'volume']
    )
    
    # Filter by volume
    high_volume = matrix[matrix['volume'] > 1000000]
    
    # Get prices only
    prices = matrix['price']
```

### Handle Missing Data

```python
def handle_data(context, data):
    price = data.current(context.asset, 'price')
    
    if pd.isna(price):
        log.warn(f"No price for {context.asset}")
        return
    
    # Safe to use price
    order_target_value(context.asset, 10000)
```

### Non-Market Hours

When current simulation time is not a valid market time, uses most recent market close.

```python
def handle_data(context, data):
    # Even on weekends/holidays, returns last valid price
    price = data.current(context.asset, 'price')
```

## Common Patterns

### Price Comparison

```python
def handle_data(context, data):
    current = data.current(context.asset, 'price')
    yesterday = data.history(context.asset, 'price', 2, '1d').iloc[0]
    
    if current > yesterday * 1.02:
        order(context.asset, 100)
```

### Volume Filter

```python
def handle_data(context, data):
    vol = data.current(context.asset, 'volume')
    avg_vol = data.history(context.asset, 'volume', 20, '1d').mean()
    
    if vol > avg_vol * 2:
        log.info("Unusual volume detected")
```

## See Also

- [BarData](bar_data.md)
- [history()](history.md)
- [can_trade()](can_trade.md)
