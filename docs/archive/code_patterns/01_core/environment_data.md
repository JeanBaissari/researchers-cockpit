# Environment & External Data

> Query execution environment and load external CSV data.

## get_environment()

```python
zipline.api.get_environment(field='platform')
```

Query the execution environment for simulation parameters.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | str | The field to query |

### Available Fields

| Field | Description |
|-------|-------------|
| `'platform'` | Platform name (default: 'zipline') |
| `'arena'` | Execution mode ('backtest' or 'live') |
| `'data_frequency'` | 'daily' or 'minute' |
| `'start'` | Simulation start date |
| `'end'` | Simulation end date |
| `'capital_base'` | Starting capital |
| `'*'` | Returns all fields as dict |

### Example

```python
def initialize(context):
    env = get_environment('*')
    
    context.start = env['start']
    context.end = env['end']
    context.capital = env['capital_base']
    
    if env['arena'] == 'backtest':
        context.slippage_mult = 1.0
    else:
        context.slippage_mult = 2.0
```

---

## fetch_csv()

```python
zipline.api.fetch_csv(
    url,
    pre_func=None,
    post_func=None,
    date_column='date',
    date_format=None,
    timezone='UTC',
    symbol=None,
    mask=True,
    symbol_column=None,
    country_code=None,
    **kwargs
)
```

Fetch CSV from remote URL and register for data access.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | URL of the CSV file |
| `pre_func` | callable | Preprocessing callback |
| `post_func` | callable | Postprocessing callback |
| `date_column` | str | Column containing dates |
| `date_format` | str | Date format string |
| `timezone` | str | Timezone for dates |
| `symbol` | str | Symbol name for new data |
| `symbol_column` | str | Column with asset symbols |
| `country_code` | str | Country for symbol lookup |
| `**kwargs` | any | Passed to pandas.read_csv() |

### Example: Custom Index

```python
def initialize(context):
    # Fetch VIX data
    fetch_csv(
        'https://example.com/vix_daily.csv',
        symbol='VIX',
        date_column='Date',
        date_format='%Y-%m-%d'
    )

def handle_data(context, data):
    vix = data.current('VIX', 'close')
    
    if vix > 20:
        # High volatility - reduce exposure
        pass
```

### Example: Supplementary Data

```python
def pre_process(df):
    # Clean data before date parsing
    df['value'] = df['value'].replace('N/A', np.nan)
    return df

def post_process(df):
    # Process after symbol mapping
    df['signal'] = df['value'].pct_change()
    return df

def initialize(context):
    fetch_csv(
        'https://example.com/signals.csv',
        pre_func=pre_process,
        post_func=post_process,
        symbol_column='ticker',
        date_column='date'
    )
```

### Example: Economic Data

```python
def initialize(context):
    # Fetch unemployment data
    fetch_csv(
        'https://example.com/unemployment.csv',
        symbol='UNRATE',
        date_column='observation_date'
    )

def handle_data(context, data):
    unemployment = data.current('UNRATE', 'value')
    
    # Use macro data in strategy
    if unemployment < 5.0:
        context.risk_on = True
```

---

## Data Access After fetch_csv

Once registered, access data through the `data` object:

```python
# Current value
current_vix = data.current('VIX', 'close')

# Historical values
vix_history = data.history('VIX', 'close', 30, '1d')

# Check availability
if data.can_trade('VIX'):
    # Data is available
    pass
```

---

## Best Practices

1. **Use HTTPS URLs** - Ensure data security
2. **Handle missing data** - Use pre_func to clean
3. **Match timezones** - Align with trading calendar
4. **Cache locally** - For large datasets, host your own copy

---

## See Also

- [BarData Class](../02_data/bar_data.md)
- [data.current()](../02_data/current.md)
- [data.history()](../02_data/history.md)
