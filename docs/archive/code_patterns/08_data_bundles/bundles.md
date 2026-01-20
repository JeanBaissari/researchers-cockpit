# Data Bundles

> Register, ingest, and load market data.

## Overview

Data bundles are Zipline's mechanism for managing market data. A bundle defines how to fetch, process, and store data for backtesting.

---

## register()

```python
zipline.data.bundles.register(
    name,
    f,
    calendar_name='NYSE',
    start_session=None,
    end_session=None,
    minutes_per_day=390,
    create_writers=True
)
```

Register a data bundle ingest function.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Bundle identifier |
| `f` | callable | Ingest function |
| `calendar_name` | str | Trading calendar (default: 'NYSE') |
| `start_session` | Timestamp | First session to ingest |
| `end_session` | Timestamp | Last session to ingest |
| `minutes_per_day` | int | Trading minutes per day |
| `create_writers` | bool | Auto-create data writers |

### Ingest Function Signature

```python
def my_ingest(environ, asset_db_writer, minute_bar_writer,
              daily_bar_writer, adjustment_writer, calendar,
              start_session, end_session, cache, show_progress):
    # Fetch and write data
    pass
```

### Decorator Usage

```python
from zipline.data.bundles import register

@register('my-bundle')
def my_bundle_ingest(environ, asset_db_writer, minute_bar_writer,
                     daily_bar_writer, adjustment_writer, calendar,
                     start_session, end_session, cache, show_progress):
    
    # Write asset metadata
    asset_db_writer.write(equities=equities_df)
    
    # Write daily bars
    daily_bar_writer.write(data_generator(), show_progress=show_progress)
    
    # Write adjustments (splits, dividends)
    adjustment_writer.write(splits=splits_df, dividends=dividends_df)
```

---

## ingest()

```python
zipline.data.bundles.ingest(
    name,
    environ=os.environ,
    date=None,
    show_progress=True
)
```

Run the ingest function for a bundle.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Bundle name |
| `environ` | mapping | Environment variables |
| `date` | datetime | Timestamp for ingestion |
| `show_progress` | bool | Display progress bar |

### CLI Usage

```bash
zipline ingest -b my-bundle
```

---

## load()

```python
zipline.data.bundles.load(
    name,
    environ=os.environ,
    date=None
)
```

Load a previously ingested bundle.

### Returns

`BundleData` namedtuple with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `asset_finder` | AssetFinder | Asset metadata |
| `equity_daily_bar_reader` | BcolzDailyBarReader | Daily OHLCV |
| `equity_minute_bar_reader` | BcolzMinuteBarReader | Minute OHLCV |
| `adjustment_reader` | SQLiteAdjustmentReader | Corporate actions |

### Example

```python
from zipline.data.bundles import load

bundle_data = load('quandl')

# Access components
finder = bundle_data.asset_finder
daily_reader = bundle_data.equity_daily_bar_reader
```

---

## unregister()

```python
zipline.data.bundles.unregister(name)
```

Remove a bundle registration.

---

## bundles

```python
zipline.data.bundles.bundles
```

Immutable mapping of registered bundles. Updated only via `register()` and `unregister()`.

```python
from zipline.data.bundles import bundles

print(list(bundles.keys()))
# ['quandl', 'my-bundle', ...]
```

---

## Custom Bundle Example

```python
import pandas as pd
from zipline.data.bundles import register

@register('custom-equities', calendar_name='NYSE')
def custom_ingest(environ, asset_db_writer, minute_bar_writer,
                  daily_bar_writer, adjustment_writer, calendar,
                  start_session, end_session, cache, show_progress):
    
    # 1. Define assets
    equities = pd.DataFrame({
        'symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'asset_name': ['Apple Inc', 'Microsoft Corp', 'Alphabet Inc'],
        'exchange': ['NASDAQ', 'NASDAQ', 'NASDAQ'],
    })
    equities.index = pd.Index([0, 1, 2], name='sid')
    
    asset_db_writer.write(equities=equities)
    
    # 2. Generate daily bar data
    def data_gen():
        for sid, symbol in enumerate(['AAPL', 'MSFT', 'GOOGL']):
            df = fetch_historical_data(symbol, start_session, end_session)
            yield sid, df
    
    daily_bar_writer.write(data_gen(), show_progress=show_progress)
    
    # 3. Write adjustments
    splits = pd.DataFrame({
        'sid': [0],
        'effective_date': [pd.Timestamp('2020-08-31').value // 10**9],
        'ratio': [0.25]  # 4:1 split
    })
    adjustment_writer.write(splits=splits)
```

---

## See Also

- [Data Writers](data_writers.md)
- [Data Readers](data_readers.md)
- [Asset Metadata](asset_metadata.md)
