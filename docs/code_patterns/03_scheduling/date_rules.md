# date_rules

> Factory class for creating date-based scheduling rules.

## Class

```python
class zipline.api.date_rules
```

## Methods

### every_day()

Triggers every trading day.

```python
date_rules.every_day()
```

**Example:**
```python
schedule_function(
    my_func,
    date_rule=date_rules.every_day()
)
```

---

### week_start()

Triggers at the start of each week.

```python
date_rules.week_start(days_offset=0)
```

**Parameters:**
- `days_offset` (int): Trading days to wait after week start. Default: 0 (first day)

**Examples:**
```python
# First trading day of week (usually Monday)
date_rules.week_start()
date_rules.week_start(days_offset=0)

# Second trading day of week (usually Tuesday)
date_rules.week_start(days_offset=1)

# Third trading day of week (usually Wednesday)
date_rules.week_start(days_offset=2)
```

---

### week_end()

Triggers before the end of each week.

```python
date_rules.week_end(days_offset=0)
```

**Parameters:**
- `days_offset` (int): Trading days before week end. Default: 0 (last day)

**Examples:**
```python
# Last trading day of week (usually Friday)
date_rules.week_end()
date_rules.week_end(days_offset=0)

# Second to last day (usually Thursday)
date_rules.week_end(days_offset=1)
```

---

### month_start()

Triggers at the start of each month.

```python
date_rules.month_start(days_offset=0)
```

**Parameters:**
- `days_offset` (int): Trading days after month start. Default: 0 (first day)

**Examples:**
```python
# First trading day of month
date_rules.month_start()
date_rules.month_start(days_offset=0)

# Second trading day of month
date_rules.month_start(days_offset=1)

# Fifth trading day of month
date_rules.month_start(days_offset=4)
```

---

### month_end()

Triggers before the end of each month.

```python
date_rules.month_end(days_offset=0)
```

**Parameters:**
- `days_offset` (int): Trading days before month end. Default: 0 (last day)

**Examples:**
```python
# Last trading day of month
date_rules.month_end()
date_rules.month_end(days_offset=0)

# Second to last trading day
date_rules.month_end(days_offset=1)

# Third to last trading day
date_rules.month_end(days_offset=2)
```

---

## Common Patterns

### Weekly Monday Open

```python
def initialize(context):
    schedule_function(
        rebalance,
        date_rule=date_rules.week_start(days_offset=0),
        time_rule=time_rules.market_open()
    )
```

### Monthly First Day

```python
def initialize(context):
    schedule_function(
        monthly_rebalance,
        date_rule=date_rules.month_start(days_offset=0),
        time_rule=time_rules.market_open(minutes=30)
    )
```

### Last Day of Month

```python
def initialize(context):
    schedule_function(
        month_end_report,
        date_rule=date_rules.month_end(days_offset=0),
        time_rule=time_rules.market_close(minutes=15)
    )
```

### Avoid First/Last Day Volatility

```python
def initialize(context):
    # Rebalance on 2nd trading day of month
    schedule_function(
        rebalance,
        date_rule=date_rules.month_start(days_offset=1),
        time_rule=time_rules.market_open(hours=1)
    )
```

### Friday Close (End of Week)

```python
def initialize(context):
    schedule_function(
        weekly_closeout,
        date_rule=date_rules.week_end(days_offset=0),
        time_rule=time_rules.market_close(minutes=30)
    )
```

## Multiple Schedules Example

```python
def initialize(context):
    # Daily morning check
    schedule_function(
        daily_check,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=15)
    )
    
    # Weekly rebalance on Tuesday
    schedule_function(
        weekly_rebalance,
        date_rule=date_rules.week_start(days_offset=1),
        time_rule=time_rules.market_open(hours=1)
    )
    
    # Monthly portfolio review
    schedule_function(
        monthly_review,
        date_rule=date_rules.month_end(days_offset=2),
        time_rule=time_rules.market_close(hours=1)
    )
```

## Notes

- All rules use **trading days**, not calendar days
- Holidays and market closures are automatically handled
- `days_offset` counts from the reference point (start/end)
- Week boundaries follow the trading calendar

## See Also

- [schedule_function()](schedule_function.md)
- [time_rules](time_rules.md)
