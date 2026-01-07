---
name: zrl-calendar-manager
description: This skill should be used when configuring trading calendars for Zipline-Reloaded backtests. It provides patterns for using built-in calendars, creating custom calendars for global markets, and handling timezone/session alignment for 24/7 or non-US markets.
---

# Zipline Calendar Manager

Configure trading calendars for accurate simulation across global markets.

## Purpose

Properly configure trading calendars to ensure backtests respect market hours, holidays, and session boundaries. Critical for accurate simulation of order execution and data alignment.

## When to Use

- Backtesting non-US markets (XLON, XTKS, etc.)
- Trading 24/7 markets (crypto, forex)
- Creating custom calendars for specific exchanges
- Handling multi-market strategies

## Calendar Architecture

Zipline uses `exchange_calendars` library for market session management:

```
Calendar → defines:
  ├── Trading days (excludes holidays/weekends)
  ├── Session open/close times
  ├── Early closes (half-days)
  └── Timezone
```

## Built-in Calendars

### Major Exchanges

| Calendar | Exchange | Timezone | Session |
|----------|----------|----------|---------|
| `NYSE` | New York Stock Exchange | US/Eastern | 9:30-16:00 |
| `NASDAQ` | NASDAQ | US/Eastern | 9:30-16:00 |
| `XLON` | London Stock Exchange | Europe/London | 8:00-16:30 |
| `XPAR` | Euronext Paris | Europe/Paris | 9:00-17:30 |
| `XFRA` | Frankfurt | Europe/Berlin | 9:00-17:30 |
| `XTKS` | Tokyo Stock Exchange | Asia/Tokyo | 9:00-15:00 |
| `XHKG` | Hong Kong | Asia/Hong_Kong | 9:30-16:00 |
| `XASX` | Australian | Australia/Sydney | 10:00-16:00 |

### 24-Hour Calendars

| Calendar | Market | Notes |
|----------|--------|-------|
| `24/5` | Forex | Mon 00:00 - Fri 24:00 UTC |
| `24/7` | Crypto | Always open |

## Usage Patterns

### Basic Calendar Usage

```python
from zipline import run_algorithm
import pandas as pd

result = run_algorithm(
    start=pd.Timestamp('2020-01-01', tz='utc'),
    end=pd.Timestamp('2024-12-31', tz='utc'),
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    trading_calendar='NYSE',  # Specify calendar
    bundle='my-bundle'
)
```

### Get Calendar Instance

```python
import exchange_calendars as ec

# Get calendar
nyse = ec.get_calendar('NYSE')

# Check if date is trading day
nyse.is_session('2024-01-15')  # True (MLK Day is holiday: False)

# Get trading days in range
sessions = nyse.sessions_in_range('2024-01-01', '2024-12-31')

# Get session open/close
open_time = nyse.session_open('2024-01-15')
close_time = nyse.session_close('2024-01-15')
```

### Calendar Alignment

Ensure data aligns with calendar:

```python
def align_to_calendar(df: pd.DataFrame, calendar_name: str) -> pd.DataFrame:
    """Align DataFrame index to trading calendar."""
    import exchange_calendars as ec
    
    cal = ec.get_calendar(calendar_name)
    start = df.index.min()
    end = df.index.max()
    
    # Get valid sessions
    valid_sessions = cal.sessions_in_range(start, end)
    
    # Reindex to calendar
    df = df.reindex(valid_sessions)
    
    return df
```

## Custom Calendar Creation

### Extend Existing Calendar

```python
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar
from pandas.tseries.holiday import Holiday, GoodFriday
import datetime

class CustomNYSECalendar(ExchangeCalendar):
    """NYSE with additional custom holidays."""
    
    name = 'CUSTOM_NYSE'
    tz = 'US/Eastern'
    open_times = ((None, datetime.time(9, 30)),)
    close_times = ((None, datetime.time(16, 0)),)
    
    @property
    def regular_holidays(self):
        return HolidayCalendar([
            # Standard NYSE holidays
            Holiday('New Year', month=1, day=1),
            Holiday('MLK Day', month=1, day=15),  # 3rd Monday
            # ... add more
            # Custom holidays
            Holiday('Company Holiday', month=6, day=15),
        ])
```

### 24/7 Crypto Calendar

```python
from exchange_calendars import ExchangeCalendar
import datetime
import pandas as pd

class CryptoCalendar(ExchangeCalendar):
    """24/7 calendar for cryptocurrency markets."""
    
    name = 'CRYPTO'
    tz = 'UTC'
    open_times = ((None, datetime.time(0, 0)),)
    close_times = ((None, datetime.time(23, 59)),)
    
    @property
    def regular_holidays(self):
        return HolidayCalendar([])  # No holidays
    
    @property
    def weekmask(self):
        return 'Mon Tue Wed Thu Fri Sat Sun'  # All days
```

### Register Custom Calendar

```python
import exchange_calendars as ec

# Register for use
ec.register_calendar('CRYPTO', CryptoCalendar())

# Now use in algorithms
run_algorithm(
    trading_calendar='CRYPTO',
    ...
)
```

## Multi-Market Strategies

### Handle Different Sessions

```python
def initialize(context):
    import exchange_calendars as ec
    
    context.us_calendar = ec.get_calendar('NYSE')
    context.uk_calendar = ec.get_calendar('XLON')
    
    # Store for session checks
    context.calendars = {
        'US': context.us_calendar,
        'UK': context.uk_calendar
    }

def handle_data(context, data):
    current_dt = get_datetime()
    
    # Check which markets are open
    for region, cal in context.calendars.items():
        session = current_dt.normalize()
        if cal.is_session(session):
            open_time = cal.session_open(session)
            close_time = cal.session_close(session)
            
            if open_time <= current_dt <= close_time:
                # Market is open, can trade
                process_market(region, context, data)
```

## Timezone Best Practices

### Always Use UTC Internally

```python
# Correct: UTC timestamps
start = pd.Timestamp('2020-01-01', tz='utc')

# Wrong: Local timezone
start = pd.Timestamp('2020-01-01', tz='US/Eastern')  # Avoid
```

### Convert for Display

```python
def display_local_time(utc_time, timezone='US/Eastern'):
    """Convert UTC to local time for display."""
    return utc_time.tz_convert(timezone)
```

## Script Reference

### list_calendars.py

List available calendars and their properties:

```bash
python scripts/list_calendars.py
python scripts/list_calendars.py --calendar NYSE --details
```

### validate_calendar_alignment.py

Check data alignment with calendar:

```bash
python scripts/validate_calendar_alignment.py /path/to/data --calendar NYSE
```

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `NoSessionsInRange` | Date range has no trading days | Extend range or check calendar |
| `SessionNotInCalendar` | Date not a trading day | Use `calendar.is_session()` check |
| `TimezoneError` | Mixed timezones | Normalize all to UTC |
| Wrong execution times | Calendar mismatch | Verify bundle calendar matches algo |

## References

See `references/calendar_list.md` for complete calendar reference.
See `references/holiday_schedules.md` for holiday handling patterns.
