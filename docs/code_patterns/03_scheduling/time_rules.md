# time_rules

> Factory class for creating time-based scheduling rules.

## Class

```python
class zipline.api.time_rules
```

## Methods

### market_open()

Triggers relative to market open.

```python
time_rules.market_open(hours=0, minutes=1)
```

**Parameters:**
- `hours` (int): Hours after market open. Default: 0
- `minutes` (int): Minutes after market open. Default: 1

**Note:** Default is 1 minute after open, not exactly at open.

**Examples:**
```python
# 1 minute after open (default)
time_rules.market_open()

# At market open (0 minutes after)
time_rules.market_open(minutes=0)

# 30 minutes after open
time_rules.market_open(minutes=30)

# 1 hour after open
time_rules.market_open(hours=1)

# 1 hour 30 minutes after open
time_rules.market_open(hours=1, minutes=30)
```

---

### market_close()

Triggers relative to market close.

```python
time_rules.market_close(hours=0, minutes=1)
```

**Parameters:**
- `hours` (int): Hours before market close. Default: 0
- `minutes` (int): Minutes before market close. Default: 1

**Note:** Offsets are **before** close, not after.

**Examples:**
```python
# 1 minute before close (default)
time_rules.market_close()

# At market close
time_rules.market_close(minutes=0)

# 30 minutes before close
time_rules.market_close(minutes=30)

# 1 hour before close
time_rules.market_close(hours=1)

# 1 hour 30 minutes before close
time_rules.market_close(hours=1, minutes=30)
```

---

## NYSE Regular Hours Reference

For NYSE-based calendars:
- Market open: 9:30 AM ET
- Market close: 4:00 PM ET
- Regular session: 6.5 hours (390 minutes)

| Time Rule | Eastern Time |
|-----------|--------------|
| `market_open()` | 9:31 AM |
| `market_open(minutes=0)` | 9:30 AM |
| `market_open(minutes=30)` | 10:00 AM |
| `market_open(hours=1)` | 10:30 AM |
| `market_close()` | 3:59 PM |
| `market_close(minutes=0)` | 4:00 PM |
| `market_close(minutes=30)` | 3:30 PM |
| `market_close(hours=1)` | 3:00 PM |

---

## Common Patterns

### Opening Bell Strategy

```python
def initialize(context):
    # Execute right at open
    schedule_function(
        opening_trade,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=0)
    )
```

### Wait for Market to Settle

```python
def initialize(context):
    # Wait 30 mins for opening volatility to pass
    schedule_function(
        trade_after_open,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )
```

### End of Day Liquidation

```python
def initialize(context):
    # Close positions 15 mins before close
    schedule_function(
        close_positions,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=15)
    )
```

### Midday Check

```python
def initialize(context):
    # Run at approximately noon (2.5 hours after open)
    schedule_function(
        midday_check,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(hours=2, minutes=30)
    )
```

---

## Multiple Time Slots

```python
def initialize(context):
    # Morning entry
    schedule_function(
        morning_entry,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )
    
    # Midday adjustment
    schedule_function(
        midday_adjust,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(hours=3)
    )
    
    # EOD exit
    schedule_function(
        eod_exit,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=15)
    )
```

---

## Half Days

Half trading days (e.g., day after Thanksgiving) have early close at 1:00 PM ET.

```python
def initialize(context):
    # This runs 30 mins before close
    # On regular days: 3:30 PM ET
    # On half days: 12:30 PM ET
    schedule_function(
        before_close,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=30),
        half_days=True  # Default
    )
    
    # Skip half days entirely
    schedule_function(
        full_days_only,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=30),
        half_days=False
    )
```

---

## Daily Frequency Note

For `data_frequency='daily'`:
- Only one bar per day
- Time rules still schedule when function runs
- All functions execute at their scheduled time

For `data_frequency='minute'`:
- Functions execute at exact minute specified

## See Also

- [schedule_function()](schedule_function.md)
- [date_rules](date_rules.md)
