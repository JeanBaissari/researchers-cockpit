# Data Readers

> Read market data from Zipline's storage formats.

## BcolzDailyBarReader

```python
class zipline.data.bcolz_daily_bars.BcolzDailyBarReader(
    table, read_all_threshold=3000
)
```

Read daily OHLCV data written by BcolzDailyBarWriter.

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | bcolz.ctable | The data table |
| `read_all_threshold` | int | Asset count threshold for read strategy |

### Key Methods

#### get_value()

```python
reader.get_value(sid, dt, field)
```

Get a single value for one asset on one day.

| Parameter | Type | Description |
|-----------|------|-------------|
| `sid` | int | Asset identifier |
| `dt` | datetime64 | Midnight UTC of day |
| `field` | str | 'open', 'high', 'low', 'close', 'volume' |

#### load_raw_arrays()

```python
reader.load_raw_arrays(columns, start_date, end_date, assets)
```

Load data for multiple assets over a date range.

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | list[str] | Fields to load |
| `start_date` | Timestamp | Start of range |
| `end_date` | Timestamp | End of range |
| `assets` | list[int] | Asset IDs |

**Returns:** List of ndarrays, shape (days, assets)

#### get_last_traded_dt()

```python
reader.get_last_traded_dt(asset, day)
```

Get the last trading date on or before `day` for an asset.

### Properties

| Property | Description |
|----------|-------------|
| `last_available_dt` | Last session with data |

---

## SQLiteAdjustmentReader

```python
class zipline.data.adjustments.SQLiteAdjustmentReader(conn)
```

Read corporate action adjustments from SQLite.

| Parameter | Type | Description |
|-----------|------|-------------|
| `conn` | str/Connection | Database path or connection |

### load_adjustments()

```python
reader.load_adjustments(
    dates, assets,
    should_include_splits,
    should_include_mergers,
    should_include_dividends,
    adjustment_type
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `dates` | DatetimeIndex | Dates to load |
| `assets` | Int64Index | Assets to load |
| `adjustment_type` | str | 'price', 'volume', or both |

### unpack_db_to_component_dfs()

```python
reader.unpack_db_to_component_dfs(convert_dates=False)
```

Extract all tables as DataFrames for inspection.

---

## AssetFinder

```python
class zipline.assets.AssetFinder(engine, future_chain_predicates=...)
```

Interface to asset metadata database.

### Key Methods

#### Lookup Methods

```python
finder.retrieve_asset(sid)           # Get asset by sid
finder.lookup_symbol(symbol, as_of)  # Get asset by symbol
finder.retrieve_equities(sids)       # Get multiple equities
finder.retrieve_futures_contracts(sids)  # Get futures
```

#### Query Methods

```python
finder.equities_sids                         # All equity sids
finder.futures_sids                          # All futures sids
finder.equities_sids_for_country_code('US')  # By country
finder.equities_sids_for_exchange_name('NYSE')  # By exchange
```

#### group_by_type()

```python
finder.group_by_type(sids)
```

Group sids by asset type (equity, future, etc.).

---

## Data Storage Format

### Daily Bar Columns

| Column | Type | Notes |
|--------|------|-------|
| `open` | uint32 | Price × 1000 |
| `high` | uint32 | Price × 1000 |
| `low` | uint32 | Price × 1000 |
| `close` | uint32 | Price × 1000 |
| `volume` | uint32 | As-traded volume |
| `day` | uint32 | Seconds since epoch |
| `id` | uint32 | Asset sid |

Data is grouped by asset, sorted by day within each block.

---

## See Also

- [Data Writers](data_writers.md)
- [Data Bundles](bundles.md)
