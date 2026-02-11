# Calendars API

Module for trading calendar management and session alignment in The Researcher's Cockpit.

**Location:** `lib/calendars/`
**CLI Equivalent:** N/A (used automatically by bundles and backtest)
**Version:** v1.12.0

---

## Overview

The calendars module provides custom trading calendars for different asset classes with direct Zipline integration.

**v1.12.0 Changes:**
- **SessionManager removed** → Use Zipline's `get_calendar()` directly
- **FOREX calendar updated** → Sundays now included in weekmask (root cause fix)
- **Direct calendar access** → No wrapper functions (AD-001)

**Key Features:**
- Custom calendars: `CryptoCalendar` (24/7) and `ForexCalendar` (24/5 + Sundays)
- Automatic calendar registration with Zipline
- Asset class to calendar mapping
- Direct `get_calendar()` usage throughout codebase

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

### Direct Calendar Access (v1.12.0+)

```python
from zipline.utils.calendar_utils import get_calendar
import pandas as pd

# Get calendar directly from Zipline
forex_cal = get_calendar('FOREX')

# Get trading sessions for date range
sessions = forex_cal.sessions_in_range(
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

### Session Management (v1.12.0 - Removed)

**Note:** SessionManager has been removed in v1.12.0. Use Zipline's `get_calendar()` directly:

```python
from zipline.utils.calendar_utils import get_calendar
import pandas as pd

# Get calendar
calendar = get_calendar('FOREX')

# Get trading sessions
sessions = calendar.sessions_in_range(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)

# Check if date is trading day
is_trading_day = calendar.is_session(pd.Timestamp('2024-01-15'))

# Get all trading days in range
trading_days = calendar.sessions_in_range(start, end)
```

**Why Removed:**
- FOREX calendar now includes Sundays (root cause fixed)
- No session alignment workarounds needed
- Direct Zipline calendar API is simpler and more maintainable
- Eliminates wrapper layer (AD-001: NO WRAPPERS)

---

## Module Structure (v1.12.0)

The calendars package is organized into focused submodules:

```
lib/calendars/
├── __init__.py               # Public API exports
├── crypto.py                 # CryptoCalendar (24/7)
├── forex.py                  # ForexCalendar (24/5 + Sundays)
├── registry.py               # Calendar registration
└── utils.py                  # Calendar utilities
```

**v1.12.0 Removals:**
- ~~sessions/~~ — Deleted (use direct `get_calendar()` instead)

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

### Direct Calendar Usage (v1.12.0+)

```python
import pandas as pd
from zipline.utils.calendar_utils import get_calendar

# Get calendar directly
forex_cal = get_calendar('FOREX')

# Get trading sessions
sessions = forex_cal.sessions_in_range(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)
print(f"Trading sessions: {len(sessions)}")

# Check if specific date is trading day
is_trading = forex_cal.is_session(pd.Timestamp('2024-01-15'))

# Get all sessions between dates
all_sessions = forex_cal.all_sessions
print(f"Total sessions: {len(all_sessions)}")
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

### Calendar Alignment (v1.12.0+)

Direct calendar usage ensures consistent session handling:

```python
from zipline.utils.calendar_utils import get_calendar
import pandas as pd

# Get calendar for asset class
calendar = get_calendar('FOREX')  # or 'CRYPTO', 'XNYS'

# Get sessions for date range
sessions = calendar.sessions_in_range(
    start=pd.Timestamp('2024-01-01'),
    end=pd.Timestamp('2024-01-31')
)

# Use in bundle registration (in ~/.zipline/extension.py)
register('eurusd_1m', csvdir_equities(['EURUSD'], ...),  calendar_name='FOREX')

# Calendar automatically used during backtest execution
```

**Note:** SessionManager removed in v1.12.0. FOREX calendar now includes Sundays, eliminating need for session alignment workarounds.

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

- **v1.12.0**: NO WRAPPERS refactoring - Removed SessionManager (use get_calendar() directly), FOREX calendar includes Sundays, direct calendar access throughout
- **v1.1.0**: Session management system for bundle-calendar alignment
- **v1.0.3**: Custom calendar system (CRYPTO, FOREX) with registry
- **v1.0.0**: Initial calendar support
