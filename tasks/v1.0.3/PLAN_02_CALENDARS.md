# Calendar & Asset Class Integration

Fix calendar registration timing and ensure proper integration for CRYPTO/FOREX asset classes.

## Problem Statement

The current implementation has several issues with calendar registration:

1. **Import Path Error:** `backtest.py` imports from `v1_researchers_cockpit.zipline.extension` instead of `lib.extension`
2. **Registration Timing:** Calendars are registered in `run_backtest()` but based on asset_class string, not calendar name
3. **Calendar Name Mismatch:** `register_custom_calendars(['CRYPTO'])` is called but the function expects uppercase calendar names that match `_CALENDAR_REGISTRY` keys
4. **24/7 Calendar Conflict:** `data_loader.py` uses `'24/7'` for crypto/forex but `extension.py` defines `'CRYPTO'` and `'FOREX'`

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Map current calendar registration flow
- [ ] Identify all calendar name inconsistencies

## Future Tasks

### extension.py Fixes
- [ ] Ensure `CryptoCalendar` and `ForexCalendar` can be retrieved by Zipline
- [ ] Add calendar aliases (e.g., '24/7' → 'CRYPTO')
- [ ] Validate calendar works with Zipline's `get_calendar()`
- [ ] Add `start` and `end` bounds to calendar instantiation

### backtest.py Fixes
- [ ] Fix import path: `from .extension import ...` (not v1_researchers_cockpit)
- [ ] Fix registration call: use calendar name, not asset class
- [ ] Move calendar registration to earlier in execution (before bundle loading)
- [ ] Add fallback if custom calendar fails

### data_loader.py Fixes
- [ ] Align calendar names with extension.py definitions
- [ ] Use `'CRYPTO'` instead of `'24/7'` for crypto assets
- [ ] Use `'FOREX'` instead of `'24/7'` for forex assets
- [ ] Or: register `'24/7'` as an alias in extension.py

### Integration Testing
- [ ] Test CRYPTO calendar with crypto bundle
- [ ] Test FOREX calendar with forex bundle
- [ ] Verify sessions are generated correctly (24/7 for crypto, 24/5 for forex)
- [ ] Test backtest runs with each calendar type

## Implementation Plan

### Step 1: Fix extension.py Import and Registration

First, ensure extension.py is importable from lib/:

```python
# In lib/backtest.py, change:
# FROM: from v1_researchers_cockpit.zipline.extension import (...)
# TO:
from .extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)
```

### Step 2: Add Calendar Alias Support

In `extension.py`, add support for common aliases:

```python
# Updated calendar mapping with aliases
_CALENDAR_REGISTRY = {
    'CRYPTO': CryptoCalendar,
    'FOREX': ForexCalendar,
}

_CALENDAR_ALIASES = {
    '24/7': 'CRYPTO',      # Common alias
    'ALWAYS_OPEN': 'CRYPTO',
    'FX': 'FOREX',
    'CURRENCY': 'FOREX',
}

def get_calendar_name(name_or_alias: str) -> Optional[str]:
    """Resolve calendar name from alias."""
    upper = name_or_alias.upper()
    if upper in _CALENDAR_REGISTRY:
        return upper
    return _CALENDAR_ALIASES.get(upper)
```

### Step 3: Fix Registration Flow in backtest.py

```python
def run_backtest(...):
    # ... load strategy and params ...
    
    # Prepare configuration
    config = _prepare_backtest_config(...)
    
    # Register custom calendars BEFORE getting trading calendar
    if config.asset_class:
        calendar_name = get_calendar_for_asset_class(config.asset_class)
        if calendar_name:
            register_custom_calendars(calendars=[calendar_name])
    
    # Now get trading calendar (will use registered custom calendar if applicable)
    trading_calendar = _get_trading_calendar(config.bundle, config.asset_class)
```

### Step 4: Align data_loader.py Calendar Names

```python
def ingest_bundle(...):
    # Auto-detect calendar
    if calendar_name is None:
        if 'crypto' in assets:
            calendar_name = 'CRYPTO'  # Use our custom calendar
        elif 'forex' in assets:
            calendar_name = 'FOREX'   # Use our custom calendar
        else:
            calendar_name = 'XNYS'    # NYSE for equities
    
    # Ensure custom calendars are registered before ingestion
    if calendar_name in ['CRYPTO', 'FOREX']:
        register_custom_calendars(calendars=[calendar_name])
```

### Step 5: Calendar Class Improvements

Ensure calendars work with Zipline's expected interface:

```python
class CryptoCalendar(ExchangeCalendar):
    """24/7 Trading Calendar for Cryptocurrency Markets."""
    
    name = "CRYPTO"
    tz = UTC
    
    # Use proper time representation for 24h coverage
    open_times = ((None, time(0, 0)),)
    close_times = ((None, time(23, 59, 59, 999999)),)  # Last microsecond of day
    
    weekmask = "Mon Tue Wed Thu Fri Sat Sun"
    
    # Required for exchange_calendars v4.x
    @property
    def regular_holidays(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex([])
    
    @property
    def special_closes(self) -> list:
        return []
    
    @property
    def adhoc_holidays(self) -> list:
        return []
```

## Relevant Files

- `lib/extension.py` - Calendar definitions and registration
- `lib/backtest.py` - Calendar usage in run_backtest() (line 33-36, 427-431)
- `lib/data_loader.py` - Calendar name in ingest_bundle() (line 257-262)
- `lib/config.py` - get_default_bundle() may need calendar awareness

## Testing Checklist

```python
# Test calendar registration
from lib.extension import register_custom_calendars, get_registered_calendars

results = register_custom_calendars(['CRYPTO', 'FOREX'])
assert results['CRYPTO'] == True
assert results['FOREX'] == True
assert 'CRYPTO' in get_registered_calendars()

# Test calendar retrieval
from zipline.utils.calendar_utils import get_calendar
crypto_cal = get_calendar('CRYPTO')
assert crypto_cal.name == 'CRYPTO'
assert len(crypto_cal.schedule('2024-01-01', '2024-01-07')) == 7  # All 7 days

forex_cal = get_calendar('FOREX')
assert forex_cal.name == 'FOREX'
assert len(forex_cal.schedule('2024-01-01', '2024-01-07')) == 5  # Weekdays only
```

## Key Principle

**Registration Before Use:** Custom calendars must be registered with Zipline before they can be retrieved via `get_calendar()`. The registration should happen at application startup or before any bundle/backtest operations.

**Consistent Naming:** Use `'CRYPTO'` and `'FOREX'` as the canonical names throughout the codebase. Avoid `'24/7'` which is ambiguous.
