# Target Order Functions

> Functions for adjusting positions to target amounts.

## order_target()

Adjust position to a target number of shares.

```python
zipline.api.order_target(asset, target, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `target` | int | Target number of shares |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier.

### Behavior

Orders difference between target and current position:
- Current: 100, Target: 150 → Buy 50
- Current: 100, Target: 50 → Sell 50
- Current: 0, Target: 100 → Buy 100
- Current: 100, Target: 0 → Sell 100

### Example

```python
def handle_data(context, data):
    # Always hold exactly 100 shares
    order_target(context.asset, 100)
    
    # Close position entirely
    order_target(context.asset, 0)
```

---

## order_target_value()

Adjust position to a target dollar value.

```python
zipline.api.order_target_value(asset, target, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `target` | float | Target dollar value of position |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier.

### Example

```python
def handle_data(context, data):
    # Maintain $50,000 position
    order_target_value(context.asset, 50000)
    
    # Close position
    order_target_value(context.asset, 0)
```

---

## order_target_percent()

Adjust position to a target percentage of portfolio.

```python
zipline.api.order_target_percent(asset, target, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `target` | float | Target as decimal (0.50 = 50%) |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier.

### Example

```python
def handle_data(context, data):
    # Maintain 30% of portfolio in this asset
    order_target_percent(context.asset, 0.30)
    
    # Close position
    order_target_percent(context.asset, 0.0)
```

---

## Important: Open Orders Warning

**Target functions do not account for open orders!**

```python
# BAD: Results in 20 shares, not 10
order_target(asset, 10)
order_target(asset, 10)  # First hasn't filled yet!

# GOOD: Track your orders
def handle_data(context, data):
    open_orders = get_open_orders(context.asset)
    if not open_orders:
        order_target(context.asset, 10)
```

---

## Common Patterns

### Rebalancing to Equal Weight

```python
def rebalance(context, data):
    weight = 1.0 / len(context.assets)
    
    for asset in context.assets:
        if data.can_trade(asset):
            order_target_percent(asset, weight)
```

### Exit All Positions

```python
def liquidate(context, data):
    for asset in context.portfolio.positions:
        order_target(asset, 0)
```

### Signal-Based Allocation

```python
def handle_data(context, data):
    signal = compute_signal(context, data)
    
    if signal > 0.5:
        order_target_percent(context.asset, 0.9)
    elif signal < -0.5:
        order_target_percent(context.asset, 0.0)
    else:
        order_target_percent(context.asset, 0.5)
```

### Long/Short Portfolio

```python
def rebalance(context, data):
    # Long positions: 50% each
    for asset in context.longs:
        order_target_percent(asset, 0.5)
    
    # Short positions: -25% each
    for asset in context.shorts:
        order_target_percent(asset, -0.25)
    
    # Close removed positions
    for asset in context.portfolio.positions:
        if asset not in context.longs and asset not in context.shorts:
            order_target_percent(asset, 0)
```

### Fixed Dollar Position

```python
def handle_data(context, data):
    # Always maintain exactly $10,000 position regardless of portfolio value
    order_target_value(context.asset, 10000)
```

---

## target vs non-target

| Function | Behavior |
|----------|----------|
| `order(asset, 100)` | Add 100 shares to position |
| `order_target(asset, 100)` | Adjust position TO 100 shares |
| `order_value(asset, 10000)` | Buy $10,000 more worth |
| `order_target_value(asset, 10000)` | Adjust position TO $10,000 value |
| `order_percent(asset, 0.1)` | Buy 10% of portfolio more |
| `order_target_percent(asset, 0.1)` | Adjust position TO 10% of portfolio |

---

## See Also

- [Basic Orders](basic_orders.md)
- [Execution Styles](execution_styles.md)
- [Order Management](order_management.md)
