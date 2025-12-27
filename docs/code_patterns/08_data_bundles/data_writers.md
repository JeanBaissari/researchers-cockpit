# Data Writers

> Write market data to Zipline's storage formats.

## BcolzDailyBarWriter

```python
class zipline.data.bcolz_daily_bars.BcolzDailyBarWriter(
    filename, calendar, start_session, end_session
)
```

Write daily OHLCV data to disk.

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | str | Output file path |
| `calendar` | TradingCalendar | Trading calendar |
| `start_session` | Timestamp | First session |
| `end_session` | Timestamp | Last session |

### write()

```python
writer.write(data, assets=None, show_progress=False, invalid_data_behavior='warn')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | iterable | Tuples of (sid, DataFrame) |
| `assets` | set[int] | Expected asset IDs |
| `show_progress` | bool | Show progress bar |
| `invalid_data_behavior` | str | 'warn', 'raise', or 'ignore' |

### Example

```python
from zipline.data.bcolz_daily_bars import BcolzDailyBarWriter

writer = BcolzDailyBarWriter(
    '/path/to/daily.bcolz',
    calendar=calendar,
    start_session=start,
    end_session=end
)

def generate_data():
    for sid in [0, 1, 2]:
        df = pd.DataFrame({
            'open': [...],
            'high': [...],
            'low': [...],
            'close': [...],
            'volume': [...]
        }, index=dates)
        yield sid, df

writer.write(generate_data(), show_progress=True)
```

---

## SQLiteAdjustmentWriter

```python
class zipline.data.adjustments.SQLiteAdjustmentWriter(
    conn_or_path, equity_daily_bar_reader, overwrite=False
)
```

Write corporate action adjustments (splits, dividends, mergers).

| Parameter | Type | Description |
|-----------|------|-------------|
| `conn_or_path` | str/Connection | Database path or connection |
| `equity_daily_bar_reader` | SessionBarReader | For dividend calculations |
| `overwrite` | bool | Overwrite existing data |

### write()

```python
writer.write(splits=None, mergers=None, dividends=None, stock_dividends=None)
```

### Splits DataFrame Format

| Column | Type | Description |
|--------|------|-------------|
| `effective_date` | int | Seconds since epoch |
| `ratio` | float | Split ratio |
| `sid` | int | Asset ID |

### Dividends DataFrame Format

| Column | Type | Description |
|--------|------|-------------|
| `sid` | int | Asset ID |
| `ex_date` | datetime64 | Ex-dividend date |
| `declared_date` | datetime64 | Announcement date |
| `pay_date` | datetime64 | Payment date |
| `record_date` | datetime64 | Record date |
| `amount` | float | Cash per share |

---

## AssetDBWriter

```python
class zipline.assets.AssetDBWriter(engine)
```

Write asset metadata to SQLite database.

### write()

```python
writer.write(
    equities=None,
    futures=None,
    exchanges=None,
    root_symbols=None,
    equity_supplementary_mappings=None
)
```

### Equities DataFrame Format

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Ticker symbol |
| `asset_name` | str | Full name |
| `start_date` | datetime | First trade date |
| `end_date` | datetime | Last trade date |
| `exchange` | str | Exchange name |

### Example

```python
equities = pd.DataFrame({
    'symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'asset_name': ['Apple Inc', 'Microsoft Corp', 'Alphabet Inc'],
    'start_date': pd.Timestamp('2010-01-01'),
    'end_date': pd.Timestamp('2023-12-31'),
    'exchange': 'NYSE'
}, index=[0, 1, 2])  # sids as index

writer.write(equities=equities)
```

---

## See Also

- [Data Bundles](bundles.md)
- [Data Readers](data_readers.md)
