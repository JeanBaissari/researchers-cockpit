# Basic Order Functions

> Functions for placing orders by share count, value, or percentage.

## order()

Place an order for a fixed number of shares.

```python
zipline.api.order(asset, amount, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `amount` | int | Shares to order (positive=buy, negative=sell) |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier, or `None` if order not placed.

### Examples

```python
def handle_data(context, data):
    # Buy 100 shares
    order(context.asset, 100)
    
    # Sell 50 shares
    order(context.asset, -50)
    
    # Buy with limit price
    order(context.asset, 100, limit_price=150.00)
    
    # Sell with stop price
    order(context.asset, -100, stop_price=145.00)
```

---

## order_value()

Place an order for a target dollar value.

```python
zipline.api.order_value(asset, value, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `value` | float | Dollar value to order (positive=buy, negative=sell) |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier.

### Calculation

`shares = round(value / current_price)`

### Examples

```python
def handle_data(context, data):
    # Buy $10,000 worth of shares
    order_value(context.asset, 10000)
    
    # Sell $5,000 worth
    order_value(context.asset, -5000)
    
    # With limit
    order_value(context.asset, 10000, limit_price=150.00)
```

---

## order_percent()

Place an order for a percentage of portfolio value.

```python
zipline.api.order_percent(asset, percent, limit_price=None, stop_price=None, style=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Asset to trade |
| `percent` | float | Fraction of portfolio (0.10 = 10%) |
| `limit_price` | float | Limit price (optional) |
| `stop_price` | float | Stop price (optional) |
| `style` | ExecutionStyle | Execution style object |

### Returns

`str` - Unique order identifier.

### Calculation

`value = portfolio_value * percent`
`shares = round(value / current_price)`

### Examples

```python
def handle_data(context, data):
    # Buy shares worth 10% of portfolio
    order_percent(context.asset, 0.10)
    
    # Sell shares worth 5% of portfolio
    order_percent(context.asset, -0.05)
    
    # Buy 50% of portfolio value
    order_percent(context.asset, 0.50)
```

---

## Common Patterns

### Simple Buy

```python
def handle_data(context, data):
    if data.can_trade(context.asset):
        order(context.asset, 100)
```

### Dollar-Cost Averaging

```python
def handle_data(context, data):
    # Invest $1000 per period
    order_value(context.asset, 1000)
```

### Equal Weight Portfolio

```python
def handle_data(context, data):
    # 5 assets, 20% each
    weight = 1.0 / len(context.assets)
    for asset in context.assets:
        order_percent(asset, weight)
```

### With Price Limit

```python
def handle_data(context, data):
    current = data.current(context.asset, 'price')
    
    # Only buy if price drops to 99%
    limit = current * 0.99
    order(context.asset, 100, limit_price=limit)
```

### Order Tracking

```python
def handle_data(context, data):
    order_id = order(context.asset, 100)
    
    if order_id:
        context.pending_orders.append(order_id)
        log.info(f"Order placed: {order_id}")
    else:
        log.warn("Order not placed")
```

---

## Notes

- Orders don't fill immediately in simulation
- Use `can_trade()` to verify asset is tradeable
- Order amounts are rounded to integers
- Negative amounts mean sell/short
- For futures, consider contract multiplier

## See Also

- [Target Orders](target_orders.md)
- [Execution Styles](execution_styles.md)
- [Order Management](order_management.md)
