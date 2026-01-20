# Calendars API

Module for trading calendar management and session alignment in The Researcher's Cockpit.

**Location:** `lib/calendars/`  
**CLI Equivalent:** N/A (used automatically by bundles and backtest)  
**Version:** v1.11.0

---

## Overview

The calendars module provides custom trading calendars for different asset classes and a session management system for ensuring calendar alignment between bundle ingestion and backtest execution.

**Key Features:**
- Custom calendars: `CryptoCalendar` (24/7) and `ForexCalendar` (24/5)
- Automatic calendar registration with Zipline
- Session management for bundle-calendar alignment (v1.1.0)
- Asset class to calendar mapping
- Calendar registry system

**Supported Calendars:**
- `CRYPTO` - 24/7 trading (365 days/year, no holidays)
- `FOREX` - 24/5 trading (Monday-Friday, 24 hours/day)
- `XNYS` - Standard NYSE calendar (used for equities, default)

---

## Installation/Dependencies

**Required:**
- `zipline-reloaded` >= 3.1.0
- `exchange-calendars` >= 4.0.0
- `pandas` >= 1.3.0

**Note:** Custom calendars are automatically registered when needed by bundle ingestion or backtest execution.

---

## Quick Start

### Register Custom Calendars

```python
from lib.calendars import register_custom_calendars

# Register CRYPTO and FOREX calendars
results = register_custom_calendars(['CRYPTO', 'FOREX'])
print(results)  # {'CRYPTO': True, 'FOREX': True}
```

### Get Calendar for Asset Class

```python
from lib.calendars import get_calendar_for_asset_class

# Automatically get the correct calendar
crypto_cal = get_calendar_for_asset_class('crypto')  # Returns 'CRYPTO'
forex_cal = get_calendar_for_asset_class('forex')    # Returns 'FOREX'
equity_cal = get_calendar_for_asset_class('equity')  # Returns None (uses XNYS)
```

### Use Session Manager for Alignment

```python
from lib.calendars.sessions import SessionManager

# Create session manager for asset class
session_mgr = SessionManager.for_asset_class('forex')

# Get trading sessions for date range
import pandas as pd
sessions = session_mgr.get_sessions(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)
print(f"Trading sessions: {len(sessions)}")
```

---

## Public API Reference

### Calendar Classes

#### `CryptoCalendar`

24/7 trading calendar for cryptocurrency markets.

**Attributes:**
- `name`: `"CRYPTO"`
- `tz`: `UTC`
- `open_times`: `((None, time(0, 0)),)`
- `close_times`: `((None, time(23, 59, 59)),)`
- `weekmask`: `"Mon Tue Wed Thu Fri Sat Sun"`

**Properties:**
- `regular_holidays`: Empty `pd.DatetimeIndex` (no holidays)
- `special_closes`: Empty list (no special closes)

**Example:**
```python
from lib.calendars import CryptoCalendar

# Crypto calendar trades 24/7
calendar = CryptoCalendar()
print(calendar.name)  # 'CRYPTO'
print(calendar.weekmask)  # 'Mon Tue Wed Thu Fri Sat Sun'
```

---

#### `ForexCalendar`

24/5 trading calendar for forex markets (weekdays only).

**Attributes:**
- `name`: `"FOREX"`
- `tz`: `"America/New_York"`
- `open_times`: `((None, time(0, 0)),)`
- `close_times`: `((None, time(23, 59, 59)),)`
- `weekmask`: `"Mon Tue Wed Thu Fri"`

**Properties:**
- `regular_holidays`: `pd.DatetimeIndex` (can be extended with holidays)
- `special_closes`: Empty list (no special closes)

**Example:**
```python
from lib.calendars import ForexCalendar

# Forex calendar trades 24/5 (weekdays only)
calendar = ForexCalendar()
print(calendar.name)  # 'FOREX'
print(calendar.weekmask)  # 'Mon Tue Wed Thu Fri'
```

---

### Registry Functions

#### `register_custom_calendars()`

Register custom calendars with Zipline.

**Signature:**
```python
def register_custom_calendars(
    calendars: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    force: bool = True
) -> Dict[str, bool]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `calendars` | List[str] | None | List of calendar names to register. If None, registers all available |
| `start` | str | None | Ignored parameter (kept for API compatibility) |
| `end` | str | None | Ignored parameter (kept for API compatibility) |
| `force` | bool | True | If True, overwrite existing calendar registrations |

**Returns:**
- `Dict[str, bool]`: Dictionary mapping calendar names to registration success (True/False)

**Raises:**
- `ValueError`: If calendar class is not a valid ExchangeCalendar subclass

**Example:**
```python
from lib.calendars import register_custom_calendars

# Register specific calendars
results = register_custom_calendars(['CRYPTO', 'FOREX'])
print(results)  # {'CRYPTO': True, 'FOREX': True}

# Register all available calendars
results = register_custom_calendars()
print(results)  # {'CRYPTO': True, 'FOREX': True}
```

**Note:** This function should be called explicitly from entry points (e.g., `lib/backtest/runner.py`) rather than relying on auto-registration at import time.

---

#### `get_registered_calendars()`

Get list of calendars that have been registered with Zipline.

**Signature:**
```python
def get_registered_calendars() -> List[str]
```

**Returns:**
- `List[str]`: List of calendar names currently registered

**Example:**
```python
from lib.calendars import get_registered_calendars

registered = get_registered_calendars()
print(registered)  # ['CRYPTO', 'FOREX']
```

---

#### `register_calendar_type()`

Register a custom calendar TYPE (factory) with Zipline.

**Signature:**
```python
def register_calendar_type(
    name: str,
    calendar_class: Type[ExchangeCalendar],
    start: Optional[str] = None,
    end: Optional[str] = None,
    force: bool = True
) -> bool
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Calendar name (e.g., `'CRYPTO'`, `'FOREX'`) |
| `calendar_class` | Type[ExchangeCalendar] | required | Calendar class (subclass of ExchangeCalendar) |
| `start` | str | None | Ignored parameter (not used, kept for API compatibility) |
| `end` | str | None | Ignored parameter (not used, kept for API compatibility) |
| `force` | bool | True | If True, overwrite existing calendar registration |

**Returns:**
- `bool`: `True` if registration successful, `False` otherwise

**Raises:**
- `ValueError`: If calendar_class is not a valid ExchangeCalendar subclass

**Note:** This registers the calendar class (factory), not an instance, allowing Zipline to lazily instantiate it with appropriate date bounds during bundle ingestion and backtest execution.

---

### Utility Functions

#### `get_calendar_for_asset_class()`

Get the appropriate calendar name for a given asset class.

**Signature:**
```python
def get_calendar_for_asset_class(asset_class: str) -> Optional[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asset_class` | str | required | Asset class name (e.g., `'crypto'`, `'forex'`, `'equity'`) |

**Returns:**
- `Optional[str]`: Calendar name string, or `None` if no custom calendar needed (uses Zipline default)

**Example:**
```python
from lib.calendars import get_calendar_for_asset_class

# Get calendar for different asset classes
crypto_cal = get_calendar_for_asset_class('crypto')      # 'CRYPTO'
forex_cal = get_calendar_for_asset_class('forex')       # 'FOREX'
equity_cal = get_calendar_for_asset_class('equity')     # None (uses XNYS)
```

**Asset Class Mapping:**
- `'crypto'`, `'cryptocurrency'` → `'CRYPTO'`
- `'forex'`, `'fx'`, `'currency'` → `'FOREX'`
- `'equity'`, `'equities'` → `None` (uses Zipline default: `XNYS`)

---

#### `get_available_calendars()`

Get list of available custom calendar names.

**Signature:**
```python
def get_available_calendars() -> List[str]
```

**Returns:**
- `List[str]`: List of calendar names that can be registered

**Example:**
```python
from lib.calendars import get_available_calendars

calendars = get_available_calendars()
print(calendars)  # ['CRYPTO', 'FOREX']
```

---

#### `resolve_calendar_name()`

Resolve calendar name from alias.

**Signature:**
```python
def resolve_calendar_name(name_or_alias: str) -> Optional[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name_or_alias` | str | required | Calendar name or alias |

**Returns:**
- `Optional[str]`: Resolved calendar name, or `None` if not found

**Example:**
```python
from lib.calendars import resolve_calendar_name

# Resolve aliases
resolve_calendar_name('FX')        # 'FOREX'
resolve_calendar_name('24/7')      # 'CRYPTO'
resolve_calendar_name('ALWAYS_OPEN')  # 'CRYPTO'
resolve_calendar_name('CURRENCY')  # 'FOREX'
```

**Supported Aliases:**
- `'24/7'`, `'ALWAYS_OPEN'` → `'CRYPTO'`
- `'FX'`, `'CURRENCY'` → `'FOREX'`

---

### Session Management (v1.1.0)

#### `SessionManager`

Centralized session manager for trading calendars. Ensures bundle ingestion and backtest execution use identical session logic.

**Class Methods:**

##### `SessionManager.for_asset_class()`

Create SessionManager for a specific asset class.

**Signature:**
```python
@classmethod
def for_asset_class(cls, asset_class: str) -> 'SessionManager'
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asset_class` | str | required | Asset class (`'forex'`, `'crypto'`, `'equity'`) |

**Returns:**
- `SessionManager`: Session manager instance

**Raises:**
- `ValueError`: If asset class is unknown

**Example:**
```python
from lib.calendars.sessions import SessionManager

# Create session manager for forex
session_mgr = SessionManager.for_asset_class('forex')
```

---

##### `SessionManager.for_bundle()`

Create SessionManager based on bundle metadata.

**Signature:**
```python
@classmethod
def for_bundle(cls, bundle_name: str) -> 'SessionManager'
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Bundle name (e.g., `'csv_eurusd_1m'`) |

**Returns:**
- `SessionManager`: Session manager instance

**Raises:**
- `ValueError`: If bundle not found in registry

**Example:**
```python
from lib.calendars.sessions import SessionManager

# Create session manager from bundle
session_mgr = SessionManager.for_bundle('csv_eurusd_1m')
```

---

**Instance Methods:**

##### `get_sessions()`

Get trading sessions for date range (canonical method).

**Signature:**
```python
def get_sessions(
    start: pd.Timestamp,
    end: pd.Timestamp
) -> pd.DatetimeIndex
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | pd.Timestamp | required | Start date |
| `end` | pd.Timestamp | required | End date |

**Returns:**
- `pd.DatetimeIndex`: Trading sessions in the date range

**Note:** Both bundle ingestion and backtest execution MUST use this method to ensure session alignment.

**Example:**
```python
import pandas as pd
from lib.calendars.sessions import SessionManager

session_mgr = SessionManager.for_asset_class('forex')
sessions = session_mgr.get_sessions(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)
print(f"Trading sessions: {len(sessions)}")
```

---

##### `validate_bundle_sessions()`

Validate that bundle has correct sessions for date range (pre-flight check).

**Signature:**
```python
def validate_bundle_sessions(
    bundle_name: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp
) -> tuple[bool, str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Bundle name |
| `start_date` | pd.Timestamp | required | Start date |
| `end_date` | pd.Timestamp | required | End date |

**Returns:**
- `tuple[bool, str]`: `(is_valid, error_message)`

**Example:**
```python
import pandas as pd
from lib.calendars.sessions import SessionManager

session_mgr = SessionManager.for_bundle('csv_eurusd_1m')
is_valid, message = session_mgr.validate_bundle_sessions(
    bundle_name='csv_eurusd_1m',
    start_date=pd.Timestamp('2024-01-01'),
    end_date=pd.Timestamp('2024-01-31')
)

if not is_valid:
    print(f"Session mismatch: {message}")
```

---

##### `apply_filters()`

Apply all session filters to DataFrame in order defined by strategy.

**Signature:**
```python
def apply_filters(
    df: pd.DataFrame,
    show_progress: bool = False,
    **kwargs: Any
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame to filter |
| `show_progress` | bool | False | Show progress messages |
| `**kwargs` | Any | - | Additional filter parameters |

**Returns:**
- `pd.DataFrame`: Filtered DataFrame

**Example:**
```python
from lib.calendars.sessions import SessionManager

session_mgr = SessionManager.for_asset_class('forex')
filtered_df = session_mgr.apply_filters(df, show_progress=True)
```

---

## Module Structure

The calendars package is organized into focused submodules:

```
lib/calendars/
├── __init__.py               # Public API exports
├── crypto.py                 # CryptoCalendar (24/7)
├── forex.py                  # ForexCalendar (24/5)
├── registry.py               # Calendar registration
├── utils.py                  # Calendar utilities
└── sessions/                 # Session management (v1.1.0)
    ├── manager.py            # SessionManager
    ├── strategies.py         # Loading strategies
    └── validation.py         # Session alignment validation
```

---

## Examples

### Calendar Registration

```python
from lib.calendars import register_custom_calendars, get_registered_calendars

# Register CRYPTO calendar
results = register_custom_calendars(['CRYPTO'])
print(results)  # {'CRYPTO': True}

# Check registered calendars
registered = get_registered_calendars()
print(registered)  # ['CRYPTO']
```

### Asset Class to Calendar Mapping

```python
from lib.calendars import get_calendar_for_asset_class

# Automatically get calendar for asset class
asset_classes = ['crypto', 'forex', 'equity']
for asset_class in asset_classes:
    calendar = get_calendar_for_asset_class(asset_class)
    print(f"{asset_class}: {calendar}")
# Output:
# crypto: CRYPTO
# forex: FOREX
# equity: None
```

### Session Management for Bundle Alignment

```python
import pandas as pd
from lib.calendars.sessions import SessionManager

# Create session manager for forex
session_mgr = SessionManager.for_asset_class('forex')

# Get expected sessions
expected_sessions = session_mgr.get_sessions(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)

# Validate bundle sessions
is_valid, message = session_mgr.validate_bundle_sessions(
    bundle_name='csv_eurusd_1m',
    start_date=pd.Timestamp('2024-01-01'),
    end_date=pd.Timestamp('2024-01-31')
)

if is_valid:
    print("Bundle sessions aligned with calendar")
else:
    print(f"Session mismatch: {message}")
```

### Using Calendars in Bundle Ingestion

```python
from lib.bundles import ingest_bundle
from lib.calendars import register_custom_calendars

# Register calendars (usually automatic)
register_custom_calendars(['CRYPTO', 'FOREX'])

# Ingest with automatic calendar selection
bundle = ingest_bundle(
    source='yahoo',
    assets=['crypto'],
    symbols=['BTC-USD'],
    timeframe='daily'
    # Calendar automatically set to 'CRYPTO'
)
```

---

## Configuration

### Calendar Selection by Asset Class

The system automatically selects the appropriate calendar based on asset class:

| Asset Class | Calendar | Trading Hours | Trading Days |
|-------------|----------|---------------|--------------|
| `equities` | `XNYS` | 9:30 AM - 4:00 PM ET | Weekdays (252/year) |
| `crypto` | `CRYPTO` | 24/7 | All days (365/year) |
| `forex` | `FOREX` | 24/5 | Weekdays (260/year) |

**Note:** For equities, the system uses Zipline's default `XNYS` calendar. Custom calendars are only needed for crypto and forex.

### Calendar Registration

Custom calendars are automatically registered when:
1. Bundle ingestion detects a crypto or forex asset class
2. Backtest execution uses a strategy with crypto or forex asset class
3. Explicitly called via `register_custom_calendars()`

**Best Practice:** Register calendars explicitly at the start of your script or notebook:

```python
from lib.calendars import register_custom_calendars

# Register all custom calendars
register_custom_calendars(['CRYPTO', 'FOREX'])
```

### Session Alignment

The SessionManager ensures that:
- Bundle ingestion uses the same session logic as backtest execution
- Session counts match between calendar and bundle data
- Pre-flight validation catches session mismatches before backtest execution

**Usage Pattern:**
```python
# During bundle ingestion
session_mgr = SessionManager.for_asset_class('forex')
sessions = session_mgr.get_sessions(start, end)
# Use sessions for data filtering

# During backtest execution
session_mgr = SessionManager.for_bundle('csv_eurusd_1m')
is_valid, message = session_mgr.validate_bundle_sessions(...)
# Validate before running backtest
```

---

## Error Handling

### Common Errors and Solutions

#### `ValueError: Unknown asset class: 'unknown'`

**Cause:** Asset class not recognized.

**Solution:**
```python
# Use supported asset classes
from lib.calendars import get_calendar_for_asset_class

# Supported: 'crypto', 'forex', 'equity'
calendar = get_calendar_for_asset_class('crypto')  # ✅
calendar = get_calendar_for_asset_class('unknown')  # ❌ Raises ValueError
```

#### `ValueError: calendar_class must be a subclass of ExchangeCalendar`

**Cause:** Invalid calendar class provided to `register_calendar_type()`.

**Solution:**
```python
from lib.calendars import register_calendar_type, CryptoCalendar

# Use valid calendar classes
register_calendar_type('CRYPTO', CryptoCalendar)  # ✅
register_calendar_type('INVALID', object)  # ❌ Raises ValueError
```

#### Session Mismatch During Validation

**Cause:** Bundle sessions don't match calendar sessions.

**Solution:**
```python
from lib.calendars.sessions import SessionManager

# Validate before backtest
session_mgr = SessionManager.for_bundle('csv_eurusd_1m')
is_valid, message = session_mgr.validate_bundle_sessions(...)

if not is_valid:
    print(f"Session mismatch: {message}")
    # Re-ingest bundle with correct calendar
    # Or adjust date range to match available sessions
```

---

## See Also

- [Bundles API](bundles.md) - Bundle ingestion with calendar integration
- [Backtest API](backtest.md) - Backtest execution with calendar selection
- [Data Processing API](data.md) - Calendar-based data filtering
- [Code Patterns: Calendars](../../code_patterns/) - Calendar usage patterns

---

## Version History

- **v1.1.0**: Session management system for bundle-calendar alignment
- **v1.0.3**: Custom calendar system (CRYPTO, FOREX) with registry
- **v1.0.0**: Initial calendar support
