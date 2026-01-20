# Data Processing API

Module for OHLCV data aggregation, normalization, filtering, and FOREX-specific processing in The Researcher's Cockpit.

**Location:** `lib/data/`  
**CLI Equivalent:** N/A (used internally by bundles and backtest)  
**Version:** v1.11.0

---

## Overview

The data processing module provides utilities for transforming and cleaning market data before ingestion into Zipline bundles. All functions normalize data to UTC and handle asset-class-specific quirks.

**Key Features:**
- Multi-timeframe aggregation (1m → 5m → 1h → daily)
- UTC timezone normalization
- FOREX-specific processing (Sunday consolidation, pre-session filtering)
- Calendar-based filtering and gap filling
- Modular filter system

**Processing Pipeline:**
1. **Normalization** - Convert to UTC, ensure consistent timezone
2. **Aggregation** - Resample to target timeframe
3. **Filtering** - Apply calendar-based filters
4. **Gap Filling** - Fill missing sessions according to trading calendar

---

## Installation/Dependencies

**Required:**
- `pandas` >= 1.3.0
- `numpy` >= 1.20.0
- `exchange-calendars` >= 4.0.0 (for calendar-based filtering)

**Note:** These utilities are used internally by bundle ingestion and can also be used for standalone data processing.

---

## Quick Start

### Basic Aggregation

```python
from lib.data import aggregate_ohlcv

# Aggregate 1-minute data to 5-minute
df_5m = aggregate_ohlcv(df_1m, target_timeframe='5m')

# Aggregate to hourly
df_1h = aggregate_ohlcv(df_1m, target_timeframe='1h')
```

### Timezone Normalization

```python
from lib.data import normalize_to_utc

# Normalize timestamp to UTC (timezone-naive)
timestamp = normalize_to_utc('2024-01-01 12:00:00-05:00')
print(timestamp)  # 2024-01-01 17:00:00 (UTC, naive)
```

### FOREX Sunday Consolidation

```python
from lib.data import consolidate_sunday_to_friday

# Consolidate Sunday bars into Friday (FOREX-specific)
df_forex = consolidate_sunday_to_friday(df_daily)
```

### Calendar-Based Filtering

```python
from lib.data import filter_to_calendar_sessions
from zipline.utils.calendar_utils import get_calendar

# Filter data to match trading calendar sessions
calendar = get_calendar('FOREX')
df_filtered = filter_to_calendar_sessions(df, calendar)
```

---

## Public API Reference

### Aggregation Functions

#### `aggregate_ohlcv()`

Aggregate OHLCV data to a higher timeframe.

**Signature:**
```python
def aggregate_ohlcv(
    df: pd.DataFrame,
    target_timeframe: str,
    method: str = 'standard'
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex and OHLCV columns |
| `target_timeframe` | str | required | Target timeframe (`'5m'`, `'15m'`, `'1h'`, `'daily'`, etc.) |
| `method` | str | `'standard'` | Aggregation method (currently only `'standard'` supported) |

**Returns:**
- `pd.DataFrame`: DataFrame with aggregated OHLCV data at target timeframe

**Raises:**
- `ValueError`: If required columns are missing

**Aggregation Rules:**
- `open`: First price in period
- `high`: Maximum high in period
- `low`: Minimum low in period
- `close`: Last price in period
- `volume`: Sum of volumes in period

**Supported Timeframes:**
- Minutes: `'1m'`, `'2m'`, `'5m'`, `'10m'`, `'15m'`, `'30m'`
- Hours: `'1h'`, `'2h'`, `'4h'`
- Daily: `'daily'`, `'1d'`, `'D'`
- Weekly: `'weekly'`, `'1w'`, `'W'`

**Example:**
```python
from lib.data import aggregate_ohlcv

# Aggregate 1-minute to 5-minute
df_5m = aggregate_ohlcv(df_1m, target_timeframe='5m')

# Aggregate to hourly
df_1h = aggregate_ohlcv(df_1m, target_timeframe='1h')

# Aggregate to daily
df_daily = aggregate_ohlcv(df_1h, target_timeframe='daily')
```

---

#### `resample_to_timeframe()`

Resample OHLCV data from one timeframe to another.

**Signature:**
```python
def resample_to_timeframe(
    df: pd.DataFrame,
    source_timeframe: str,
    target_timeframe: str
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex and OHLCV columns |
| `source_timeframe` | str | required | Source timeframe (e.g., `'1m'`, `'5m'`) |
| `target_timeframe` | str | required | Target timeframe (e.g., `'1h'`, `'daily'`) |

**Returns:**
- `pd.DataFrame`: DataFrame with resampled OHLCV data

**Raises:**
- `ValueError`: If trying to downsample (e.g., 1h to 1m) or unknown timeframe

**Example:**
```python
from lib.data import resample_to_timeframe

# Resample from 1-minute to hourly
df_hourly = resample_to_timeframe(df_minute, '1m', '1h')

# Resample from 5-minute to daily
df_daily = resample_to_timeframe(df_5m, '5m', 'daily')
```

**Note:** This function validates that aggregation is valid (can only aggregate up, not down).

---

#### `create_multi_timeframe_data()`

Create multiple timeframe views of the same data.

**Signature:**
```python
def create_multi_timeframe_data(
    df: pd.DataFrame,
    source_timeframe: str,
    target_timeframes: List[str]
) -> Dict[str, pd.DataFrame]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex and OHLCV columns |
| `source_timeframe` | str | required | Timeframe of source data (e.g., `'1m'`) |
| `target_timeframes` | List[str] | required | List of target timeframes (e.g., `['5m', '15m', '1h']`) |

**Returns:**
- `Dict[str, pd.DataFrame]`: Dictionary mapping timeframe to aggregated DataFrame

**Example:**
```python
from lib.data import create_multi_timeframe_data

# Create multi-timeframe views
mtf_data = create_multi_timeframe_data(df_1m, '1m', ['5m', '15m', '1h'])

# Access different timeframes
df_5m = mtf_data['5m']
df_15m = mtf_data['15m']
df_1h = mtf_data['1h']
```

**Use Case:** Multi-timeframe analysis strategies that need to reference different timeframes simultaneously.

---

#### `get_timeframe_multiplier()`

Calculate how many base timeframe bars fit into one target timeframe bar.

**Signature:**
```python
def get_timeframe_multiplier(base_tf: str, target_tf: str) -> int
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_tf` | str | required | Base timeframe (e.g., `'1m'`) |
| `target_tf` | str | required | Target timeframe (e.g., `'5m'`) |

**Returns:**
- `int`: Integer multiplier (e.g., 5 for 1m→5m, 60 for 1m→1h)

**Example:**
```python
from lib.data import get_timeframe_multiplier

multiplier = get_timeframe_multiplier('1m', '5m')
print(multiplier)  # 5

multiplier = get_timeframe_multiplier('1m', '1h')
print(multiplier)  # 60
```

---

### Normalization Functions

#### `normalize_to_utc()`

Normalize a datetime to UTC timezone-naive timestamp.

**Signature:**
```python
def normalize_to_utc(dt: Union[pd.Timestamp, datetime, str]) -> pd.Timestamp
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dt` | Union[pd.Timestamp, datetime, str] | required | Datetime (can be naive, aware, or string) |

**Returns:**
- `pd.Timestamp`: Timezone-naive Timestamp in UTC

**Note:** Zipline-Reloaded uses UTC internally. All timestamps should be:
1. Converted to UTC if timezone-aware
2. Made timezone-naive (Zipline interprets naive as UTC)

**Example:**
```python
from lib.data import normalize_to_utc

# Normalize timezone-aware timestamp
ts = normalize_to_utc('2024-01-01 12:00:00-05:00')
print(ts)  # 2024-01-01 17:00:00 (UTC, naive)

# Normalize string
ts = normalize_to_utc('2024-01-01 12:00:00')
print(ts)  # 2024-01-01 12:00:00 (naive, assumed UTC)
```

---

#### `fill_data_gaps()`

Fill gaps in OHLCV data to match trading calendar sessions.

**Signature:**
```python
def fill_data_gaps(
    df: pd.DataFrame,
    calendar: ExchangeCalendar,
    method: str = 'ffill',
    max_gap_days: int = 5
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex and OHLCV columns |
| `calendar` | ExchangeCalendar | required | Trading calendar object |
| `method` | str | `'ffill'` | Gap-filling method (`'ffill'` or `'bfill'`) |
| `max_gap_days` | int | 5 | Maximum consecutive days to fill (gaps larger are logged) |

**Returns:**
- `pd.DataFrame`: DataFrame with gaps filled according to calendar sessions

**Notes:**
- Forward-fill preserves last known price (standard forex practice)
- Volume is set to 0 for synthetic bars (signals no real trades)
- Gaps exceeding `max_gap_days` are logged as warnings but still filled

**Example:**
```python
from lib.data import fill_data_gaps
from zipline.utils.calendar_utils import get_calendar

# Fill gaps for FOREX data
calendar = get_calendar('FOREX')
df_filled = fill_data_gaps(df, calendar, method='ffill', max_gap_days=5)
```

---

### FOREX-Specific Functions

#### `consolidate_sunday_to_friday()`

Consolidate FOREX Sunday bars into the preceding Friday's close.

**Signature:**
```python
def consolidate_sunday_to_friday(
    df: pd.DataFrame,
    calendar_obj: Optional[Any] = None
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with daily OHLCV data and DatetimeIndex |
| `calendar_obj` | Optional[Any] | None | Optional ExchangeCalendar (for compatibility, not used) |

**Returns:**
- `pd.DataFrame`: DataFrame with Sunday data consolidated into Friday

**Consolidation Logic:**
- Updates Friday's `close` to Sunday's `close` (captures weekend movement)
- Updates Friday's `high` to `max(friday_high, sunday_high)`
- Updates Friday's `low` to `min(friday_low, sunday_low)`
- Aggregates Sunday `volume` into Friday
- Drops all Sunday rows

**Example:**
```python
from lib.data import consolidate_sunday_to_friday

# Consolidate Sunday bars (FOREX-specific)
df_forex = consolidate_sunday_to_friday(df_daily)
# Sunday bars are now merged into Friday, ready for Zipline
```

**Note:** FOREX markets close Friday evening and reopen Sunday evening. Sunday bars represent weekend gap activity that should be merged into Friday's bar.

---

### Filtering Functions

#### `filter_to_calendar_sessions()`

Filter data to match trading calendar sessions.

**Signature:**
```python
def filter_to_calendar_sessions(
    df: pd.DataFrame,
    calendar: ExchangeCalendar
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex |
| `calendar` | ExchangeCalendar | required | Trading calendar object |

**Returns:**
- `pd.DataFrame`: DataFrame filtered to calendar sessions

**Example:**
```python
from lib.data import filter_to_calendar_sessions
from zipline.utils.calendar_utils import get_calendar

# Filter to FOREX calendar sessions
calendar = get_calendar('FOREX')
df_filtered = filter_to_calendar_sessions(df, calendar)
```

---

#### `filter_daily_to_calendar_sessions()`

Filter daily data to match trading calendar sessions.

**Signature:**
```python
def filter_daily_to_calendar_sessions(
    df: pd.DataFrame,
    calendar: ExchangeCalendar
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with daily OHLCV data |
| `calendar` | ExchangeCalendar | required | Trading calendar object |

**Returns:**
- `pd.DataFrame`: DataFrame filtered to calendar sessions

**Note:** Specialized version for daily data that handles date normalization.

---

#### `filter_forex_presession_bars()`

Filter FOREX pre-session bars (Sunday bars before market open).

**Signature:**
```python
def filter_forex_presession_bars(df: pd.DataFrame) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with FOREX data |

**Returns:**
- `pd.DataFrame`: DataFrame with pre-session bars removed

**Note:** FOREX markets open Sunday evening. Pre-session bars (before market open) are filtered out.

---

#### `apply_gap_filling()`

Apply gap filling to DataFrame using calendar sessions.

**Signature:**
```python
def apply_gap_filling(
    df: pd.DataFrame,
    calendar: ExchangeCalendar,
    max_gap_days: int = 5,
    **kwargs
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with OHLCV data |
| `calendar` | ExchangeCalendar | required | Trading calendar object |
| `max_gap_days` | int | 5 | Maximum consecutive days to fill |
| `**kwargs` | Any | - | Additional parameters passed to `fill_data_gaps()` |

**Returns:**
- `pd.DataFrame`: DataFrame with gaps filled

**Example:**
```python
from lib.data import apply_gap_filling
from zipline.utils.calendar_utils import get_calendar

# Apply gap filling
calendar = get_calendar('FOREX')
df_filled = apply_gap_filling(df, calendar, max_gap_days=5)
```

---

#### `consolidate_forex_sunday_to_friday()`

Alias for `consolidate_sunday_to_friday()` (FOREX-specific).

**Signature:**
```python
def consolidate_forex_sunday_to_friday(df: pd.DataFrame) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with FOREX daily data |

**Returns:**
- `pd.DataFrame`: DataFrame with Sunday bars consolidated

**Note:** This is an alias for `consolidate_sunday_to_friday()` for consistency with filter naming.

---

## Module Structure

The data package is organized into focused submodules:

```
lib/data/
├── __init__.py               # Public API exports
├── aggregation.py            # OHLCV aggregation
├── normalization.py          # Timezone normalization
├── forex.py                  # FOREX-specific processing
├── filters.py                # Main filter orchestrator
├── filters_calendar.py       # Calendar-based filtering
├── filters_forex.py          # FOREX filtering
├── filters_gaps.py           # Gap detection/filling
└── sanitization.py           # Data sanitization
```

---

## Examples

### Multi-Timeframe Aggregation

```python
from lib.data import aggregate_ohlcv, create_multi_timeframe_data

# Start with 1-minute data
df_1m = load_minute_data()

# Aggregate to multiple timeframes
df_5m = aggregate_ohlcv(df_1m, '5m')
df_15m = aggregate_ohlcv(df_1m, '15m')
df_1h = aggregate_ohlcv(df_1m, '1h')
df_daily = aggregate_ohlcv(df_1h, 'daily')

# Or create all at once
mtf_data = create_multi_timeframe_data(df_1m, '1m', ['5m', '15m', '1h', 'daily'])
```

### FOREX Data Processing Pipeline

```python
from lib.data import (
    normalize_to_utc,
    consolidate_sunday_to_friday,
    filter_to_calendar_sessions,
    fill_data_gaps
)
from zipline.utils.calendar_utils import get_calendar

# Load raw FOREX data
df_raw = load_forex_data()

# Step 1: Normalize to UTC
df = df_raw.copy()
df.index = df.index.map(normalize_to_utc)

# Step 2: Consolidate Sunday bars
df = consolidate_sunday_to_friday(df)

# Step 3: Filter to calendar sessions
calendar = get_calendar('FOREX')
df = filter_to_calendar_sessions(df, calendar)

# Step 4: Fill gaps
df = fill_data_gaps(df, calendar, max_gap_days=5)

# Ready for bundle ingestion
```

### Timezone Normalization

```python
from lib.data import normalize_to_utc
import pandas as pd

# Normalize various datetime formats
timestamps = [
    '2024-01-01 12:00:00',              # Naive string
    pd.Timestamp('2024-01-01 12:00:00'), # Naive Timestamp
    pd.Timestamp('2024-01-01 12:00:00-05:00'),  # Timezone-aware
]

normalized = [normalize_to_utc(ts) for ts in timestamps]
# All normalized to UTC (timezone-naive)
```

### Calendar-Based Gap Filling

```python
from lib.data import fill_data_gaps
from zipline.utils.calendar_utils import get_calendar

# Load data with gaps
df = load_data_with_gaps()

# Fill gaps according to trading calendar
calendar = get_calendar('FOREX')
df_filled = fill_data_gaps(
    df,
    calendar,
    method='ffill',      # Forward-fill prices
    max_gap_days=5       # Warn if gap > 5 days
)

# Synthetic bars have volume=0
print(df_filled[df_filled['volume'] == 0])  # Filled bars
```

---

## Configuration

### Timeframe Support

Supported timeframes for aggregation:

| Timeframe | Alias | Minutes | Notes |
|-----------|-------|---------|-------|
| `1m` | `1min` | 1 | Base timeframe |
| `5m` | `5min`, `5T` | 5 | Common intraday |
| `15m` | `15min`, `15T` | 15 | Common intraday |
| `30m` | `30min`, `30T` | 30 | Common intraday |
| `1h` | `60m`, `1H` | 60 | Hourly |
| `4h` | `4H` | 240 | 4-hour bars |
| `daily` | `1d`, `D` | 1440 | Daily bars |
| `weekly` | `1w`, `W` | 10080 | Weekly bars |

**Note:** Aggregation only works upward (e.g., 1m → 5m → 1h → daily). Downsampling is not supported.

### Gap Filling Configuration

**Default Settings:**
- `method`: `'ffill'` (forward-fill preserves last known price)
- `max_gap_days`: `5` (warns if gap exceeds 5 consecutive days)

**Asset-Specific Recommendations:**
- **FOREX**: `max_gap_days=5` (weekends expected, holidays may cause gaps)
- **CRYPTO**: `max_gap_days=0` (24/7 trading, gaps indicate data issues)
- **EQUITIES**: `max_gap_days=4` (holidays expected)

### FOREX Processing

**Sunday Consolidation:**
- FOREX markets close Friday evening and reopen Sunday evening
- Sunday bars represent weekend gap activity
- Consolidation merges Sunday into Friday to preserve gap semantics
- Monday starts clean without Sunday bar

**Pre-Session Filtering:**
- FOREX markets open Sunday evening (5pm EST)
- Pre-session bars (before market open) are filtered out
- Ensures clean session boundaries

---

## Error Handling

### Common Errors and Solutions

#### `ValueError: Missing required columns: ['open', 'high', 'low', 'close', 'volume']`

**Cause:** DataFrame missing OHLCV columns.

**Solution:**
```python
# Ensure DataFrame has required columns
required = ['open', 'high', 'low', 'close', 'volume']
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")
```

#### `ValueError: Cannot downsample from 1h to 1m`

**Cause:** Trying to downsample (aggregate down instead of up).

**Solution:**
```python
# Only aggregate upward
df_1h = aggregate_ohlcv(df_1m, '1h')  # ✅ 1m → 1h
df_1m = aggregate_ohlcv(df_1h, '1m')  # ❌ Raises ValueError
```

#### `ValueError: Unknown timeframe`

**Cause:** Unsupported timeframe string.

**Solution:**
```python
# Use supported timeframes
supported = ['1m', '5m', '15m', '30m', '1h', '4h', 'daily']
if timeframe not in supported:
    raise ValueError(f"Unsupported timeframe: {timeframe}")
```

---

## See Also

- [Bundles API](bundles.md) - Data ingestion with processing pipeline
- [Calendars API](calendars.md) - Trading calendar management
- [Validation API](validation.md) - Data validation before processing
- [Code Patterns: Data Processing](../../code_patterns/) - Usage patterns

---

## Version History

- **v1.11.0**: Modular refactoring (filters split into specialized modules)
- **v1.0.6**: Multi-timeframe aggregation support
- **v1.0.5**: FOREX Sunday consolidation and gap filling
- **v1.0.3**: UTC timezone standardization
