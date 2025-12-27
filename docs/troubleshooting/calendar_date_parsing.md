# Calendar Date Parsing Issue - Zipline Reloaded & exchange_calendars

## Problem

When running backtests with Zipline-reloaded, you may encounter this error:

```
ValueError: Parameter `start` parsed as '1993-01-29 05:00:00' although a Date must have a time component of 00:00.
```

This error occurs when `exchange_calendars` tries to parse dates that have a non-zero time component (e.g., `05:00:00` instead of `00:00:00`).

## Root Cause

Zipline-reloaded migrated from the deprecated `trading_calendars` library to `exchange_calendars`. The `exchange_calendars` library is stricter about date formats:

1. **Dates must be timezone-naive** (no timezone information)
2. **Time component must be exactly `00:00:00`** (three components, not two)
3. **Calendar must match bundle's calendar exactly**
4. **Dates must represent market days in the calendar's timezone** (EST for US equities, NOT UTC)

### The UTC Mistake

**CRITICAL ERROR**: We were incorrectly converting dates to UTC. This caused:
- Dates like `2020-01-01 00:00:00 EST` became `2020-01-01 05:00:00 UTC`
- When stored as timezone-naive, they became `2020-01-01 05:00:00` (wrong time component!)
- Exchange calendars expects dates normalized to midnight in **calendar timezone** (EST), not UTC

**Standard**: For US equity markets, dates represent market days in **EST/EDT** (`America/New_York`), not UTC.

The error typically occurs when:
- Dates are converted to UTC instead of calendar timezone (EST)
- Dates have non-zero time components due to timezone conversion
- Asset metadata dates aren't normalized to midnight in calendar timezone
- Daily bar dates aren't normalized to midnight in calendar timezone

## Solution

### 1. Normalize Dates to Calendar Timezone (EST), Not UTC

**CRITICAL**: Always normalize dates to midnight in the **calendar's timezone** (EST for US equities), then make timezone-naive. Let Zipline handle timezone interpretation.

```python
import pandas as pd

# CORRECT: Normalize to EST midnight, then make timezone-naive
# Standard: Dates represent market days in EST context
calendar_tz = 'America/New_York'  # EST for US equities

# For timezone-naive dates (from yfinance, config files, etc.)
start_ts = pd.Timestamp(start_date).tz_localize(calendar_tz).normalize().tz_localize(None)
end_ts = pd.Timestamp(end_date).tz_localize(calendar_tz).normalize().tz_localize(None)

# Verify normalization
assert start_ts.time() == pd.Timestamp('00:00:00').time()
assert start_ts.tz is None  # Must be timezone-naive
```

**WRONG approaches:**
```python
# WRONG: Converting to UTC causes 5-hour shift (EST is UTC-5)
start_ts = pd.Timestamp(start_date, tz='UTC').tz_localize(None)  # ❌ Wrong!

# WRONG: Not localizing to calendar timezone first
start_ts = pd.Timestamp(start_date).normalize()  # ❌ Assumes wrong timezone!

# WRONG: Not normalizing can leave non-zero time components
start_ts = pd.Timestamp(start_date)  # ❌ May have time component!
```

**Use the helper function** `_normalize_to_calendar_timezone()` in `lib/data_loader.py` for consistent date handling.

### 2. Use Bundle's Calendar

Always use the calendar from the bundle, not a separately created calendar:

```python
from lib.data_loader import load_bundle

# CORRECT: Get calendar from bundle
bundle_data = load_bundle(bundle_name)
trading_calendar = bundle_data.equity_daily_bar_reader.trading_calendar

# WRONG: Creating calendar separately can cause mismatches
from zipline.utils.calendar_utils import get_calendar
trading_calendar = get_calendar('NYSE')  # May not match bundle's calendar
```

### 3. Calendar Codes

Zipline-reloaded uses `exchange_calendars` library codes, not common names:

| Common Name | exchange_calendars Code |
|-------------|------------------------|
| NYSE        | XNYS                   |
| NASDAQ      | XNAS                   |
| Crypto      | 24/7                   |

When registering bundles, use the proper calendar code:

```python
from zipline.data.bundles import register

@register('my-bundle', calendar_name='XNYS')  # Use XNYS, not 'NYSE'
def my_ingest(...):
    ...
```

### 4. Disable Benchmark (MVP Workaround)

If benchmark data fetching causes issues, disable it for MVP:

```python
from zipline import run_algorithm
import pandas as pd

# Create empty benchmark Series
empty_benchmark = pd.Series(dtype=float, index=pd.DatetimeIndex([], freq='D'))

perf = run_algorithm(
    start=start_ts,
    end=end_ts,
    initialize=initialize_func,
    bundle=bundle_name,
    trading_calendar=trading_calendar,
    benchmark_returns=empty_benchmark,  # Empty Series instead of None
)
```

## Common Mistakes

1. **Using 'NYSE' instead of 'XNYS'**: Always use exchange_calendars codes
2. **Not normalizing dates**: Always call `.normalize()` on timestamps
3. **Timezone-aware dates**: Remove timezone before passing to Zipline
4. **Calendar mismatch**: Use bundle's calendar, don't create a new one
5. **Non-zero time components**: Ensure time is exactly `00:00:00`

## Verification

Before running backtests, verify dates are correct:

```python
start_ts = pd.Timestamp('2020-01-01').normalize()
print(f"Date: {start_ts}")
print(f"Time: {start_ts.time()}")  # Should be 00:00:00
print(f"Timezone: {start_ts.tz}")   # Should be None
print(f"Normalized: {start_ts.normalize() == start_ts}")  # Should be True
```

## Solution Applied

We've implemented a sustainable, scalable solution:

1. **Helper Function**: `_normalize_to_calendar_timezone()` in `lib/data_loader.py`
   - Normalizes dates to midnight in calendar timezone (EST for US equities)
   - Makes dates timezone-naive
   - Includes verification assertions

2. **Consistent Application**:
   - Asset metadata dates: Normalized to EST midnight, timezone-naive
   - Daily bar dates: Normalized to EST midnight, timezone-naive
   - Uses calendar's timezone from the calendar object passed by Zipline

3. **Standard**: All dates represent market days in EST context (not UTC)
   - yfinance dates are treated as EST market days
   - Config dates are treated as EST market days
   - Zipline interprets timezone-naive dates in calendar context

## Why EST, Not UTC?

- **US equity markets operate in EST/EDT** (`America/New_York` timezone)
- **Exchange calendars (XNYS, XNAS) use EST** as their timezone
- **Zipline expects dates normalized to calendar timezone**, not UTC
- **Converting to UTC shifts dates by 5 hours**, causing the `05:00:00` time component error
- **Standard practice**: Dates represent market days in the market's local timezone

## References

- [exchange_calendars Documentation](https://github.com/gerrymanoim/exchange_calendars)
- [Zipline-reloaded Calendar Migration](https://github.com/stefan-jansen/zipline-reloaded)
- Bundle documentation: `docs/code_patterns/08_data_bundles/bundles_overview.md`
- Issue tracking: This appears to be a Zipline-reloaded bug with benchmark data fetching and calendar date parsing

