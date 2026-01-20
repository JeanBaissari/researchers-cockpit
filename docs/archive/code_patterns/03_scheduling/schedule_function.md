# schedule_function()

> Schedule functions to run at specific times during the trading day.

## Signature

```python
zipline.api.schedule_function(
    func,
    date_rule=None,
    time_rule=None,
    half_days=True,
    calendar=None
)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `func` | callable | Function to execute. Must have same signature as `handle_data` |
| `date_rule` | EventRule | When to run (which days). Default: every trading day |
| `time_rule` | EventRule | When to run (what time). Default: market open |
| `half_days` | bool | Run on half days? Default: `True` |
| `calendar` | Sentinel | Trading calendar for rule computation |

## Function Signature

Scheduled functions must accept `(context, data)`:

```python
def my_scheduled_function(context, data):
    # Your logic here
    pass
```

## Basic Usage

```python
from zipline.api import schedule_function, date_rules, time_rules

def initialize(context):
    # Run at market open every day
    schedule_function(
        rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open()
    )

def rebalance(context, data):
    # Rebalancing logic
    pass
```

## Common Patterns

### Weekly Rebalance

```python
def initialize(context):
    schedule_function(
        rebalance,
        date_rule=date_rules.week_start(days_offset=0),
        time_rule=time_rules.market_open(minutes=30)
    )
```

### Monthly Rebalance

```python
def initialize(context):
    schedule_function(
        rebalance,
        date_rule=date_rules.month_start(days_offset=0),
        time_rule=time_rules.market_open(hours=1)
    )
```

### End of Day

```python
def initialize(context):
    schedule_function(
        end_of_day_cleanup,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=30)
    )
```

### Multiple Schedules

```python
def initialize(context):
    # Morning rebalance
    schedule_function(
        morning_rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )
    
    # Afternoon check
    schedule_function(
        afternoon_check,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(hours=1)
    )
    
    # Weekly summary
    schedule_function(
        weekly_summary,
        date_rule=date_rules.week_end(),
        time_rule=time_rules.market_close()
    )
```

## Half Days

```python
def initialize(context):
    # Won't run on half days (Thanksgiving, Christmas Eve, etc.)
    schedule_function(
        full_day_only,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=30),
        half_days=False
    )
```

## Complete Example

```python
from zipline.api import (
    schedule_function, 
    date_rules, 
    time_rules,
    order_target_percent,
    symbol,
    record
)

def initialize(context):
    context.asset = symbol('SPY')
    context.target = 0.9
    
    # Rebalance weekly at open
    schedule_function(
        rebalance,
        date_rule=date_rules.week_start(),
        time_rule=time_rules.market_open(minutes=30)
    )
    
    # Record positions daily at close
    schedule_function(
        record_positions,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close()
    )

def rebalance(context, data):
    if data.can_trade(context.asset):
        order_target_percent(context.asset, context.target)

def record_positions(context, data):
    price = data.current(context.asset, 'price')
    record(spy_price=price)

def handle_data(context, data):
    # Can be empty if all logic is in scheduled functions
    pass
```

## Notes

- Scheduled functions run **instead of** at specific times, not in addition to `handle_data`
- `handle_data` still runs every bar
- Schedules are checked at each simulation time step
- Use `schedule_function` over manual day counting in `handle_data`

## See Also

- [date_rules](date_rules.md)
- [time_rules](time_rules.md)
- [Algorithm Lifecycle](../00-getting_started/algorithm_lifecycle.md)
