# Order Management

> Functions for tracking, retrieving, and canceling orders.

## get_order()

Retrieve an order by its ID.

```python
zipline.api.get_order(order_id)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_id` | str | Order identifier from order functions |

### Returns

`Order` object with attributes:
- `id` - Unique identifier
- `asset` - Asset being traded
- `amount` - Total shares ordered
- `filled` - Shares filled so far
- `status` - Order status
- `limit` - Limit price (if any)
- `stop` - Stop price (if any)
- `created` - Creation timestamp

### Example

```python
def handle_data(context, data):
    order_id = order(context.asset, 100)
    
    # Later...
    my_order = get_order(order_id)
    if my_order:
        print(f"Status: {my_order.status}")
        print(f"Filled: {my_order.filled} / {my_order.amount}")
```

---

## get_open_orders()

Retrieve all open (unfilled) orders.

```python
zipline.api.get_open_orders(asset=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | Filter by asset (optional) |

### Returns

- **No asset**: `dict[Asset, list[Order]]` - All open orders by asset
- **With asset**: `list[Order]` - Open orders for that asset only

### Examples

```python
def handle_data(context, data):
    # All open orders
    all_open = get_open_orders()
    for asset, orders in all_open.items():
        print(f"{asset.symbol}: {len(orders)} open orders")
    
    # Orders for specific asset
    asset_orders = get_open_orders(context.asset)
    print(f"Open orders for {context.asset.symbol}: {len(asset_orders)}")
```

---

## cancel_order()

Cancel an open order.

```python
zipline.api.cancel_order(order_param)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_param` | str or Order | Order ID or Order object |

### Examples

```python
def handle_data(context, data):
    # Cancel by ID
    order_id = order(context.asset, 100)
    cancel_order(order_id)
    
    # Cancel by Order object
    my_order = get_order(order_id)
    cancel_order(my_order)
    
    # Cancel all open orders for an asset
    for o in get_open_orders(context.asset):
        cancel_order(o)
```

---

## Order Status Values

| Status | Description |
|--------|-------------|
| `OPEN` | Order is active, waiting to fill |
| `FILLED` | Order completely filled |
| `CANCELLED` | Order was cancelled |
| `REJECTED` | Order was rejected |
| `HELD` | Order temporarily held |

---

## Common Patterns

### Check Before Ordering

```python
def handle_data(context, data):
    # Don't place new orders if we have pending ones
    open_orders = get_open_orders(context.asset)
    
    if not open_orders:
        order_target_percent(context.asset, 0.5)
```

### Cancel Stale Orders

```python
def handle_data(context, data):
    for asset, orders in get_open_orders().items():
        for o in orders:
            # Cancel orders older than 5 bars
            age = context.bar_count - o.created_bar
            if age > 5:
                cancel_order(o)
```

### Cancel All Orders

```python
def cancel_all_orders(context, data):
    for asset, orders in get_open_orders().items():
        for o in orders:
            cancel_order(o)
```

### Order Tracking

```python
def initialize(context):
    context.order_history = []

def handle_data(context, data):
    order_id = order(context.asset, 100)
    if order_id:
        context.order_history.append({
            'id': order_id,
            'time': get_datetime(),
            'asset': context.asset,
            'amount': 100
        })
```

### Wait for Fill

```python
def handle_data(context, data):
    if context.pending_order:
        o = get_order(context.pending_order)
        if o.status == 'FILLED':
            log.info(f"Order filled at {o.filled}")
            context.pending_order = None
        elif o.status in ['CANCELLED', 'REJECTED']:
            log.warn(f"Order {o.status}")
            context.pending_order = None
        else:
            return  # Still waiting
    
    # Place new order
    context.pending_order = order(context.asset, 100)
```

### Order Fill Analysis

```python
def analyze(context, perf):
    # Check fill rates
    total_orders = len(context.order_ids)
    filled = sum(1 for oid in context.order_ids 
                 if get_order(oid).status == 'FILLED')
    
    fill_rate = filled / total_orders if total_orders > 0 else 0
    print(f"Fill rate: {fill_rate:.2%}")
```

---

## See Also

- [Basic Orders](basic_orders.md)
- [Cancel Policies](cancel_policies.md)
- [Blotter](../07-finance/blotter.md)
