# data.history()

> Get trailing historical data window adjusted for corporate actions.

## Signature

```python
data.history(assets, fields, bar_count, frequency)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assets` | Asset or iterable[Asset] | Asset(s) to query |
| `fields` | str or iterable[str] | Field(s) to retrieve |
| `bar_count` | int | Number of bars to retrieve |
| `frequency` | str | `'1d'` (daily) or `'1m'` (minute) |

## Valid Fields

Same as `current()`: `'price'`, `'open'`, `'high'`, `'low'`, `'close'`, `'volume'`, `'last_traded'`

## Return Types

| Input | Return | Index |
|-------|--------|-------|
| Single asset + single field | pd.Series | DatetimeIndex |
| Single asset + multiple fields | pd.DataFrame | DatetimeIndex, columns=fields |
| Multiple assets + single field | pd.DataFrame | DatetimeIndex, columns=assets |
| Multiple assets + multiple fields | pd.DataFrame | MultiIndex (date/datetime, asset) |

## Examples

### Daily Frequency - Simple Moving Average

```python
def handle_data(context, data):
    # 20-day price history
    prices = data.history(context.asset, 'price', 20, '1d')
    
    sma_20 = prices.mean()
    current = prices.iloc[-1]
    
    if current > sma_20:
        order_target_percent(context.asset, 1.0)
    else:
        order_target_percent(context.asset, 0.0)
```

### Daily Frequency - Multiple Fields - OHLCV

```python
def handle_data(context, data):
    ohlcv = data.history(context.asset, ['open', 'high', 'low', 'close', 'volume'], 10, '1d')
    
    # ohlcv is DataFrame: index=dates, columns=['open','high','low','close','volume']
    avg_volume = ohlcv['volume'].mean()
    price_range = ohlcv['high'] - ohlcv['low']
```

### Daily Frequency - Multiple Assets

```python
def handle_data(context, data):
    prices = data.history(context.universe, 'close', 20, '1d')
    
    # prices is DataFrame: index=dates, columns=assets
    returns = prices.pct_change()
    
    # Correlation matrix
    corr = returns.corr()
    
    # Mean return per asset
    avg_returns = returns.mean()
```

### Daily Frequency - Multiple Assets + Multiple Fields

```python
def handle_data(context, data):
    hist = data.history(context.universe, ['close', 'volume'], 10, '1d')
    
    # hist has MultiIndex: (date, asset), columns=['close', 'volume']
    
    # Group by asset
    for asset in context.universe:
        asset_data = hist.xs(asset, level='asset')
        avg_price = asset_data['close'].mean()
```

### Minute Data - Basic Usage

When `data_frequency` in `run_algorithm` is set to `'minute'`, `data.history()` will retrieve minute-level bars. Ensure your bundle is ingested with minute data.

```python
def handle_data(context, data):
    # Last 60 minutes of price data for context.asset
    minute_prices = data.history(context.asset, 'price', 60, '1m')
    
    # Example: Calculate a simple moving average of the last 10 minutes
    if len(minute_prices) >= 10:
        sma_10_min = minute_prices.iloc[-10:].mean()
        current_price = data.current(context.asset, 'price')
        record(current_price=current_price, sma_10_min=sma_10_min)
```

### Minute Data - Intraday VWAP Approximation

```python
def handle_data(context, data):
    # Last 60 minutes of prices and volumes
    minute_prices = data.history(context.asset, 'price', 60, '1m')
    minute_vol = data.history(context.asset, 'volume', 60, '1m')
    
    if not minute_prices.empty and not minute_vol.empty and minute_vol.sum() > 0:
        # Calculate VWAP
        vwap = (minute_prices * minute_vol).sum() / minute_vol.sum()
        current_price = data.current(context.asset, 'price')
        record(current_price=current_price, vwap=vwap)
    else:
        record(current_price=data.current(context.asset, 'price'), vwap=np.nan)
```

## Technical Indicators

### Bollinger Bands

```python
def handle_data(context, data):
    prices = data.history(context.asset, 'price', 20, '1d')
    
    sma = prices.mean()
    std = prices.std()
    
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    current = prices.iloc[-1]
    
    if current < lower_band:
        order_target_percent(context.asset, 1.0)
    elif current > upper_band:
        order_target_percent(context.asset, 0.0)
```

### RSI

```python
def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Handle division by zero
    if loss.iloc[-1] == 0:
        return 100.0
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def handle_data(context, data):
    # For minute data, adjust bar_count and frequency accordingly
    prices = data.history(context.asset, 'price', 14, '1m') # Example for 14-minute RSI
    if len(prices) > 14: # Ensure enough data for RSI calculation
        rsi = compute_rsi(prices).iloc[-1]
        
        if rsi < 30:
            order_target_percent(context.asset, 1.0)
        elif rsi > 70:
            order_target_percent(context.asset, 0.0)
```

### MACD

```python
def handle_data(context, data):
    prices = data.history(context.asset, 'price', 35, '1d')
    
    ema_12 = prices.ewm(span=12).mean()
    ema_26 = prices.ewm(span=26).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9).mean()
    
    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        order_target_percent(context.asset, 1.0)
```

## Notes

- Data is adjusted for splits, dividends, and mergers.
- Missing data follows same rules as `current()`.
- If current time isn't valid market time, uses last market close.
- **Minute Data Consideration:** When working with minute data, ensure your strategy logic and `bar_count` in `data.history()` are appropriate for the shorter timeframes. Also, be mindful of the increased data volume and potential performance impact.

## See Also

- [BarData](bar_data.md)
- [current()](current.md)
