# Order Cancellation Policies

> Control automatic order cancellation behavior.

## set_cancel_policy()

Configure automatic order cancellation.

```python
zipline.api.set_cancel_policy(cancel_policy)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cancel_policy` | CancelPolicy | Policy to use |

### Example

```python
from zipline.api import set_cancel_policy, EODCancel, NeverCancel

def initialize(context):
    # Cancel unfilled orders at end of day
    set_cancel_policy(EODCancel())
```

---

## CancelPolicy Base Class

```python
class zipline.finance.cancel_policy.CancelPolicy
```

### Abstract Method

```python
should_cancel(event) -> bool
```

**Event types:**
- `zipline.gens.sim_engine.BAR` - Each bar
- `zipline.gens.sim_engine.DAY_START` - Start of trading day
- `zipline.gens.sim_engine.DAY_END` - End of trading day
- `zipline.gens.sim_engine.MINUTE_END` - End of each minute

---

## EODCancel

Cancel all open orders at end of day.

```python
zipline.api.EODCancel(warn_on_cancel=True)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `warn_on_cancel` | bool | Log warning when orders cancelled. Default: True |

### Behavior

- Active only for **minute** simulations
- Cancels all open orders at market close
- Prevents overnight order exposure

### Example

```python
def initialize(context):
    # Cancel orders EOD with warnings
    set_cancel_policy(EODCancel(warn_on_cancel=True))
    
    # Cancel orders EOD silently
    set_cancel_policy(EODCancel(warn_on_cancel=False))
```

---

## NeverCancel

Never automatically cancel orders.

```python
zipline.api.NeverCancel()
```

### Behavior

- Orders persist until filled, manually cancelled, or simulation ends
- Useful for GTC (Good Till Cancelled) order simulation

### Example

```python
def initialize(context):
    # Keep orders open indefinitely
    set_cancel_policy(NeverCancel())
```

---

## Default Behavior

Without explicit `set_cancel_policy()`:
- Orders remain open until filled or manually cancelled
- Equivalent to `NeverCancel()`

---

## Use Cases

### Day Trading Strategy

```python
def initialize(context):
    # Always close out EOD
    set_cancel_policy(EODCancel())
    
    schedule_function(
        enter_positions,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )

def enter_positions(context, data):
    # Place limit orders that expire EOD
    current = data.current(context.asset, 'price')
    order(context.asset, 100, limit_price=current * 0.99)
```

### Swing Trading (Multi-Day)

```python
def initialize(context):
    # Keep limit orders open across days
    set_cancel_policy(NeverCancel())

def handle_data(context, data):
    # Place orders that may take days to fill
    order(context.asset, 100, limit_price=target_price)
```

### Custom Policy

```python
from zipline.finance.cancel_policy import CancelPolicy
from zipline.gens.sim_engine import MINUTE_END

class CancelAfterNMinutes(CancelPolicy):
    def __init__(self, minutes=60):
        self.minutes = minutes
        self.minute_count = 0
    
    def should_cancel(self, event):
        if event == MINUTE_END:
            self.minute_count += 1
            if self.minute_count >= self.minutes:
                self.minute_count = 0
                return True
        return False

def initialize(context):
    set_cancel_policy(CancelAfterNMinutes(minutes=60))
```

---

## Pattern: Manual EOD Cancellation

If you need more control:

```python
def initialize(context):
    set_cancel_policy(NeverCancel())
    
    schedule_function(
        eod_cleanup,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_close(minutes=5)
    )

def eod_cleanup(context, data):
    # Cancel specific orders only
    for asset, orders in get_open_orders().items():
        for o in orders:
            if should_cancel(o):
                cancel_order(o)
                log.info(f"Cancelled {o.id}")

def should_cancel(order):
    # Custom logic
    return order.limit is not None
```

---

## See Also

- [Order Management](order_management.md)
- [Blotter](../07_finance/blotter.md)
