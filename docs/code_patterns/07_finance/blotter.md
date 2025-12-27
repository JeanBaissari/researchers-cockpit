# Blotters

> Trade execution and order management infrastructure.

## Overview

A blotter documents trades and their details over time. It records orders, manages execution, and tracks transactions.

---

## Blotter Base Class

```python
class zipline.finance.blotter.Blotter(cancel_policy=None)
```

Abstract base class for order management.

### Methods

| Method | Description |
|--------|-------------|
| `order()` | Place an order |
| `cancel()` | Cancel a single order |
| `cancel_all_orders_for_asset()` | Cancel all orders for an asset |
| `get_transactions()` | Get transactions for current bar |
| `hold()` | Mark order as held |
| `reject()` | Mark order as rejected |
| `process_splits()` | Adjust orders for splits |
| `batch_order()` | Place multiple orders at once |

---

## order()

```python
blotter.order(asset, amount, style, order_id=None)
```

Place an order.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | The asset to trade |
| `amount` | int | Shares to order (+buy, -sell) |
| `style` | ExecutionStyle | Order type |
| `order_id` | str | Optional custom ID |

### Returns

| Type | Description |
|------|-------------|
| `str` or `None` | Order ID, or None if not placed |

---

## cancel()

```python
blotter.cancel(order_id, relay_status=True)
```

Cancel a single order by ID.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_id` | str | The order to cancel |
| `relay_status` | bool | Record cancellation status |

---

## get_transactions()

```python
blotter.get_transactions(bar_data)
```

Process open orders and generate transactions.

### Returns

| Return | Type | Description |
|--------|------|-------------|
| `transactions_list` | list | Filled transactions |
| `commissions_list` | list | Commission charges |
| `closed_orders` | list | Completed orders |

---

## SimulationBlotter

```python
class zipline.finance.blotter.SimulationBlotter(
    equity_slippage=None,
    future_slippage=None,
    equity_commission=None,
    future_commission=None,
    cancel_policy=None
)
```

Blotter implementation for backtesting. Simulates order execution with configurable slippage and commission models.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `equity_slippage` | SlippageModel | Equity slippage model |
| `future_slippage` | SlippageModel | Futures slippage model |
| `equity_commission` | CommissionModel | Equity commission model |
| `future_commission` | CommissionModel | Futures commission model |
| `cancel_policy` | CancelPolicy | Order cancellation policy |

---

## Order Status Flow

```
OPEN → FILLED (complete)
     → CANCELLED (user cancelled)
     → REJECTED (validation failed)
     → HELD (temporarily paused)
```

### hold()

```python
blotter.hold(order_id, reason='')
```

Mark order as held. Status returns to open/filled when fill arrives.

### reject()

```python
blotter.reject(order_id, reason='')
```

Mark order as rejected (involuntary cancellation, usually from broker).

---

## batch_order()

```python
blotter.batch_order(order_arg_lists)
```

Place multiple orders efficiently.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_arg_lists` | list[tuple] | List of order argument tuples |

### Example

```python
orders = [
    (asset1, 100, MarketOrder()),
    (asset2, -50, LimitOrder(150.0)),
    (asset3, 200, StopOrder(45.0))
]
order_ids = blotter.batch_order(orders)
```

---

## process_splits()

```python
blotter.process_splits(splits)
```

Adjust open orders for stock splits.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `splits` | list | List of (asset, ratio) tuples |

---

## Integration with Algorithm

The blotter is used internally by Zipline. Algorithm API functions like `order()`, `cancel_order()`, and `get_open_orders()` delegate to the blotter.

```python
# These API calls use the blotter internally
order(asset, 100)  # → blotter.order(...)
cancel_order(order_id)  # → blotter.cancel(...)
get_open_orders()  # → blotter.open_orders
```

---

## See Also

- [Basic Orders](../04_orders/basic_orders.md)
- [Order Management](../04_orders/order_management.md)
- [Commission Models](commission_models.md)
- [Slippage Models](slippage_models.md)
