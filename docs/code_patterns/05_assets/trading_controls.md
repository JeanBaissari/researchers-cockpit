# Trading Controls

> Safety mechanisms to protect against unintended trading behavior.

## Overview

Trading controls prevent algorithms from:
- Trading restricted assets
- Exceeding position limits
- Creating excessive leverage
- Placing orders during wrong times

---

## set_do_not_order_list()

Prevent trading specific assets.

```python
zipline.api.set_do_not_order_list(restricted_list, on_error='fail')
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `restricted_list` | iterable | Assets to restrict |
| `on_error` | str | `'fail'` (raise) or `'log'` (warn) |

### Example

```python
def initialize(context):
    # Prevent trading penny stocks or specific assets
    restricted = symbols('SIRI', 'F', 'GE')
    set_do_not_order_list(restricted, on_error='fail')
```

---

## set_long_only()

Prevent short selling.

```python
zipline.api.set_long_only()
```

### Example

```python
def initialize(context):
    set_long_only()

def handle_data(context, data):
    # This will raise an error
    order(context.asset, -100)  # TradingControlViolation
```

---

## set_max_position_size()

Limit position size per asset.

```python
zipline.api.set_max_position_size(
    asset=None,
    max_shares=None,
    max_notional=None,
    on_error='fail'
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Specific asset (None = all) |
| `max_shares` | int | Maximum share count |
| `max_notional` | float | Maximum dollar value |
| `on_error` | str | `'fail'` or `'log'` |

### Example

```python
def initialize(context):
    # Max 1000 shares or $100k per position
    set_max_position_size(
        max_shares=1000,
        max_notional=100000
    )
    
    # Stricter limit for specific asset
    set_max_position_size(
        asset=symbol('TSLA'),
        max_shares=100,
        max_notional=50000
    )
```

---

## set_max_order_size()

Limit individual order size.

```python
zipline.api.set_max_order_size(
    asset=None,
    max_shares=None,
    max_notional=None,
    on_error='fail'
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Specific asset (None = all) |
| `max_shares` | int | Maximum shares per order |
| `max_notional` | float | Maximum value per order |
| `on_error` | str | `'fail'` or `'log'` |

### Example

```python
def initialize(context):
    # Max 500 shares per order
    set_max_order_size(max_shares=500)
    
    # Max $10k per order for volatile stock
    set_max_order_size(
        asset=symbol('GME'),
        max_notional=10000
    )
```

---

## set_max_order_count()

Limit orders placed per day.

```python
zipline.api.set_max_order_count(max_count, on_error='fail')
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_count` | int | Maximum orders per day |
| `on_error` | str | `'fail'` or `'log'` |

### Example

```python
def initialize(context):
    # Max 50 orders per day
    set_max_order_count(50)
```

---

## set_max_leverage()

Limit portfolio leverage.

```python
zipline.api.set_max_leverage(max_leverage)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_leverage` | float | Maximum leverage ratio |

### Example

```python
def initialize(context):
    # No more than 2x leverage
    set_max_leverage(2.0)
    
    # Long-only, no leverage
    set_long_only()
    set_max_leverage(1.0)
```

---

## Common Control Sets

### Conservative Long-Only

```python
def initialize(context):
    set_long_only()
    set_max_leverage(1.0)
    set_max_position_size(max_notional=50000)
    set_max_order_size(max_notional=10000)
    set_max_order_count(20)
```

### Moderate Risk

```python
def initialize(context):
    set_max_leverage(1.5)
    set_max_position_size(max_shares=5000, max_notional=100000)
    set_max_order_size(max_shares=1000, max_notional=25000)
    set_max_order_count(100)
```

### With Restricted List

```python
def initialize(context):
    # Create restricted list
    penny_stocks = symbols('SIRI', 'NAKD', 'CTRM')
    delisted_risk = symbols('GE', 'F')
    
    set_do_not_order_list(penny_stocks + delisted_risk)
    set_long_only()
    set_max_leverage(1.0)
```

---

## Error Handling

### Fail Mode (Default)

```python
def initialize(context):
    set_max_order_size(max_shares=100, on_error='fail')

def handle_data(context, data):
    try:
        order(context.asset, 500)  # Exceeds limit
    except TradingControlViolation as e:
        log.error(f"Control violation: {e}")
```

### Log Mode

```python
def initialize(context):
    set_max_order_size(max_shares=100, on_error='log')

def handle_data(context, data):
    # Will log warning but not raise
    order(context.asset, 500)
```

---

## Notes

- Controls checked at order placement time
- Multiple controls can be set (all must pass)
- Asset-specific limits override general limits
- Use `on_error='log'` for soft limits during development

---

## See Also

- [Basic Orders](../04_orders/basic_orders.md)
- [Asset Types](asset_types.md)
- [Commission Models](../07_finance/commission_models.md)
