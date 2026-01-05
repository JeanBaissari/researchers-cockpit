# Utils API

Utility functions for path resolution, OHLCV aggregation, gap-filling, and strategy management.

**Location:** `lib/utils.py`

---

## OHLCV Aggregation

### aggregate_ohlcv()

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
| `target_timeframe` | str | required | Target timeframe (see table below) |
| `method` | str | `'standard'` | Aggregation method |

**Supported Timeframes:**
- `'5m'`, `'5min'` - 5 minutes
- `'15m'`, `'15min'` - 15 minutes
- `'30m'`, `'30min'` - 30 minutes
- `'1h'`, `'60m'` - 1 hour
- `'4h'` - 4 hours
- `'D'`, `'1d'`, `'daily'` - Daily

**Returns:** `pd.DataFrame` - Aggregated OHLCV data

**Example:**
```python
from lib.utils import aggregate_ohlcv

# Aggregate 1-minute to 5-minute
df_5m = aggregate_ohlcv(df_1m, '5m')

# Aggregate 1-minute to hourly
df_1h = aggregate_ohlcv(df_1m, '1h')

# Aggregate to daily
df_daily = aggregate_ohlcv(df_1m, 'daily')
```

**Aggregation Rules:**
- `open`: First value of period
- `high`: Maximum value
- `low`: Minimum value
- `close`: Last value
- `volume`: Sum of volumes

---

### resample_to_timeframe()

Validate and resample OHLCV data (wrapper around `aggregate_ohlcv()`).

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
| `df` | pd.DataFrame | required | DataFrame with OHLCV columns |
| `source_timeframe` | str | required | Current timeframe (e.g., `'1m'`) |
| `target_timeframe` | str | required | Target timeframe (e.g., `'1h'`) |

**Returns:** `pd.DataFrame` - Resampled data

**Raises:**
- `ValueError`: If trying to downsample (e.g., 1h to 1m)

**Example:**
```python
from lib.utils import resample_to_timeframe

# Valid: upsample from 1m to 1h
df_hourly = resample_to_timeframe(df_minute, '1m', '1h')

# Invalid: downsample (raises ValueError)
# df_minute = resample_to_timeframe(df_hourly, '1h', '1m')
```

---

### create_multi_timeframe_data()

Create multiple timeframe views of the same data.

**Signature:**
```python
def create_multi_timeframe_data(
    df: pd.DataFrame,
    source_timeframe: str,
    target_timeframes: list
) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | Source OHLCV data |
| `source_timeframe` | str | required | Timeframe of source (e.g., `'1m'`) |
| `target_timeframes` | list | required | List of targets (e.g., `['5m', '15m', '1h']`) |

**Returns:** `dict` - Mapping of timeframe to DataFrame

**Example:**
```python
from lib.utils import create_multi_timeframe_data

mtf_data = create_multi_timeframe_data(df_1m, '1m', ['5m', '15m', '1h'])

df_5m = mtf_data['5m']
df_15m = mtf_data['15m']
df_1h = mtf_data['1h']
```

---

### get_timeframe_multiplier()

Calculate bars ratio between timeframes.

**Signature:**
```python
def get_timeframe_multiplier(base_tf: str, target_tf: str) -> int
```

**Example:**
```python
from lib.utils import get_timeframe_multiplier

get_timeframe_multiplier('1m', '5m')   # Returns: 5
get_timeframe_multiplier('1m', '1h')   # Returns: 60
get_timeframe_multiplier('5m', '1h')   # Returns: 12
```

---

## Gap Filling

### fill_data_gaps()

Fill gaps in OHLCV data to match trading calendar sessions.

**Signature:**
```python
def fill_data_gaps(
    df: pd.DataFrame,
    calendar: 'TradingCalendar',
    method: str = 'ffill',
    max_gap_days: int = 5
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with DatetimeIndex and OHLCV |
| `calendar` | TradingCalendar | required | Trading calendar object |
| `method` | str | `'ffill'` | Fill method (`'ffill'` or `'bfill'`) |
| `max_gap_days` | int | 5 | Max consecutive days to fill |

**Returns:** `pd.DataFrame` - Data with gaps filled

**Gap-Filling Strategy:**
- Forward-fills OHLC prices (preserves last known price)
- Sets volume to 0 for synthetic bars (signals no real trades)
- Logs warnings for gaps exceeding `max_gap_days`

**Example:**
```python
from lib.utils import fill_data_gaps
from zipline.utils.calendar_utils import get_calendar

calendar = get_calendar('FOREX')
df_filled = fill_data_gaps(df, calendar, max_gap_days=5)
```

---

## Timezone Handling

### normalize_to_utc()

Normalize datetime to UTC timezone-naive timestamp.

**Signature:**
```python
def normalize_to_utc(dt: Union[pd.Timestamp, datetime, str]) -> pd.Timestamp
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dt` | Timestamp/datetime/str | required | Datetime to normalize |

**Returns:** `pd.Timestamp` - Timezone-naive UTC timestamp

**Example:**
```python
from lib.utils import normalize_to_utc

# From string
ts = normalize_to_utc('2024-01-01')

# From timezone-aware timestamp
ts = normalize_to_utc(pd.Timestamp('2024-01-01', tz='US/Eastern'))
# Returns timezone-naive UTC timestamp
```

**Notes:**
- Zipline-Reloaded uses UTC internally
- All timestamps should be timezone-naive (Zipline interprets as UTC)

---

## Path Resolution

### get_project_root()

Get the project root directory using marker-based discovery.

**Signature:**
```python
def get_project_root() -> Path
```

**Returns:** `Path` - Absolute path to project root

**Markers searched:** `pyproject.toml`, `.git`, `config/settings.yaml`, `CLAUDE.md`

---

### get_strategy_path()

Locate a strategy directory.

**Signature:**
```python
def get_strategy_path(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Strategy name (e.g., `'spy_sma_cross'`) |
| `asset_class` | str | None | Asset class (`'crypto'`, `'forex'`, `'equities'`) |

**Returns:** `Path` - Path to strategy directory

**Raises:**
- `FileNotFoundError`: If strategy not found

**Example:**
```python
from lib.utils import get_strategy_path

path = get_strategy_path('spy_sma_cross')
# Returns: /project/strategies/equities/spy_sma_cross

path = get_strategy_path('btc_momentum', 'crypto')
# Returns: /project/strategies/crypto/btc_momentum
```

---

## Strategy Management

### create_strategy_from_template()

Create a new strategy from template with asset symbol configured.

**Signature:**
```python
def create_strategy_from_template(
    name: str,
    asset_class: str,
    asset_symbol: str
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Strategy name |
| `asset_class` | str | required | Asset class |
| `asset_symbol` | str | required | Asset symbol (e.g., `'SPY'`) |

**Returns:** `Path` - Path to created strategy directory

**Actions performed:**
1. Copies `strategies/_template/` to new location
2. Updates `parameters.yaml` with `asset_symbol`
3. Creates `results/` directory
4. Creates results symlink

**Example:**
```python
from lib.utils import create_strategy_from_template

path = create_strategy_from_template(
    name='my_new_strategy',
    asset_class='equities',
    asset_symbol='SPY'
)
```

---

### check_and_fix_symlinks()

Check and repair broken symlinks in strategy results.

**Signature:**
```python
def check_and_fix_symlinks(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> list[Path]
```

**Returns:** `list[Path]` - List of fixed symlink paths

---

## File Operations

### ensure_dir()

Create directory if it doesn't exist.

```python
def ensure_dir(path: Path) -> Path
```

### timestamp_dir()

Create a timestamped directory.

```python
def timestamp_dir(base_path: Path, prefix: str) -> Path
```

**Example:**
```python
from lib.utils import timestamp_dir
from pathlib import Path

dir_path = timestamp_dir(Path('results/my_strategy'), 'backtest')
# Returns: results/my_strategy/backtest_20241228_143022
```

### load_yaml() / save_yaml()

Load and save YAML files with safe parsing.

```python
def load_yaml(path: Path) -> dict
def save_yaml(data: dict, path: Path) -> None
```

### update_symlink()

Create or update a symlink.

```python
def update_symlink(target: Path, link_path: Path) -> None
```

---

## See Also

- [Data Loader API](data_loader.md)
- [Backtest API](backtest.md)
