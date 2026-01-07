---
name: zrl-order-manager
description: This skill should be used when implementing order management logic for Zipline strategies. It provides patterns for order placement, tracking, cancellation, fill handling, and execution analytics.
---

# Zipline Order Manager

Professional order management patterns for algorithmic trading.

## Purpose

Manage order lifecycle from placement to fill, including tracking, modification, cancellation, and execution analysis.

## When to Use

- Building order routing logic
- Tracking order status
- Managing partial fills
- Analyzing execution quality

## Order Placement Methods

### Basic Orders

```python
from zipline.api import order, order_value, order_percent

def handle_data(context, data):
    # Order by shares
    order(context.asset, 100)        # Buy 100 shares
    order(context.asset, -50)        # Sell 50 shares
    
    # Order by dollar value
    order_value(context.asset, 10000)   # Buy $10k worth
    order_value(context.asset, -5000)   # Sell $5k worth
    
    # Order by portfolio percentage
    order_percent(context.asset, 0.10)  # Buy 10% of portfolio
```

### Target Orders

```python
from zipline.api import order_target, order_target_value, order_target_percent

def rebalance(context, data):
    # Target to specific share count
    order_target(context.asset, 100)  # Adjust to hold exactly 100
    
    # Target to dollar value
    order_target_value(context.asset, 50000)  # Adjust to $50k position
    
    # Target to percentage (most common)
    order_target_percent(context.asset, 0.05)  # Adjust to 5% of portfolio
```

## Order Tracking

### Get Order Status

```python
from zipline.api import get_order, get_open_orders

def handle_data(context, data):
    # Place order and track ID
    order_id = order(context.asset, 100)
    context.pending_orders.append(order_id)
    
    # Check order status
    if order_id:
        order_obj = get_order(order_id)
        print(f"Status: {order_obj.status}")
        print(f"Filled: {order_obj.filled}/{order_obj.amount}")

def check_orders(context, data):
    # Get all open orders
    all_open = get_open_orders()  # Dict: {asset: [orders]}
    
    # Get open orders for specific asset
    asset_orders = get_open_orders(context.asset)  # List of orders
    
    for order_obj in asset_orders:
        print(f"Order {order_obj.id}: {order_obj.filled}/{order_obj.amount}")
```

### Order Object Attributes

```python
order_obj = get_order(order_id)

# Key attributes
order_obj.id           # Unique identifier
order_obj.asset        # Asset being traded
order_obj.amount       # Total shares ordered
order_obj.filled       # Shares filled so far
order_obj.status       # OPEN, FILLED, CANCELLED, REJECTED
order_obj.limit        # Limit price (if any)
order_obj.stop         # Stop price (if any)
order_obj.created      # Creation timestamp
```

## Order Cancellation

```python
from zipline.api import cancel_order, get_open_orders

def cancel_stale_orders(context, data, max_age_bars=5):
    """Cancel orders older than max_age_bars."""
    current_bar = context.bar_count
    
    for asset, orders in get_open_orders().items():
        for order_obj in orders:
            # Cancel old orders
            if current_bar - order_obj.created_bar > max_age_bars:
                cancel_order(order_obj.id)
                log.info(f"Cancelled stale order {order_obj.id}")

def cancel_all_orders(context, data):
    """Cancel all open orders."""
    for asset, orders in get_open_orders().items():
        for order_obj in orders:
            cancel_order(order_obj)
```

## Order Manager Class

```python
class OrderManager:
    """Centralized order management."""
    
    def __init__(self):
        self.order_history = []
        self.pending_orders = {}  # order_id -> metadata
    
    def place_order(self, asset, amount, context, data, 
                   limit_price=None, stop_price=None, metadata=None):
        """Place order with tracking."""
        
        # Pre-flight checks
        if not data.can_trade(asset):
            log.warn(f"Cannot trade {asset}")
            return None
        
        # Place order
        order_id = order(asset, amount, 
                        limit_price=limit_price, 
                        stop_price=stop_price)
        
        if order_id:
            self.pending_orders[order_id] = {
                'asset': asset,
                'amount': amount,
                'placed_at': get_datetime(),
                'metadata': metadata or {}
            }
            log.info(f"Placed order {order_id}: {amount} {asset.symbol}")
        
        return order_id
    
    def place_target_order(self, asset, target_pct, context, data):
        """Place target percent order with tracking."""
        
        if not data.can_trade(asset):
            return None
        
        # Check for existing open orders
        if get_open_orders(asset):
            log.debug(f"Skipping {asset}: open orders exist")
            return None
        
        order_id = order_target_percent(asset, target_pct)
        
        if order_id:
            self.pending_orders[order_id] = {
                'asset': asset,
                'target_pct': target_pct,
                'placed_at': get_datetime(),
            }
        
        return order_id
    
    def update_orders(self, context, data):
        """Update order tracking status."""
        completed = []
        
        for order_id, meta in self.pending_orders.items():
            order_obj = get_order(order_id)
            
            if order_obj is None:
                completed.append(order_id)
                continue
            
            if order_obj.status in ['FILLED', 'CANCELLED', 'REJECTED']:
                self.order_history.append({
                    **meta,
                    'order_id': order_id,
                    'status': order_obj.status,
                    'filled': order_obj.filled,
                    'completed_at': get_datetime()
                })
                completed.append(order_id)
        
        for order_id in completed:
            del self.pending_orders[order_id]
    
    def cancel_all(self):
        """Cancel all pending orders."""
        for order_id in list(self.pending_orders.keys()):
            cancel_order(order_id)
    
    def get_fill_rate(self) -> float:
        """Calculate historical fill rate."""
        if not self.order_history:
            return 0.0
        
        filled = sum(1 for o in self.order_history if o['status'] == 'FILLED')
        return filled / len(self.order_history)
```

## Safe Order Patterns

### Check Before Order

```python
def safe_order(asset, target_pct, context, data):
    """Safely place order with all checks."""
    
    # Check tradability
    if not data.can_trade(asset):
        return None
    
    # Check for existing orders
    if get_open_orders(asset):
        return None
    
    # Check position limits
    current_value = context.portfolio.portfolio_value
    target_value = current_value * abs(target_pct)
    
    if target_value > context.config.max_position_value:
        log.warn(f"Position size exceeds limit for {asset}")
        return None
    
    return order_target_percent(asset, target_pct)
```

### Batch Order Execution

```python
def execute_target_portfolio(target_weights: dict, context, data):
    """Execute portfolio to target weights."""
    
    # First: reduce/exit positions not in targets
    for asset in list(context.portfolio.positions.keys()):
        if asset not in target_weights:
            if data.can_trade(asset) and not get_open_orders(asset):
                order_target_percent(asset, 0)
    
    # Second: adjust existing and enter new positions
    for asset, weight in target_weights.items():
        if data.can_trade(asset) and not get_open_orders(asset):
            order_target_percent(asset, weight)
```

## Execution Analytics

```python
class ExecutionAnalyzer:
    """Analyze order execution quality."""
    
    def __init__(self):
        self.trades = []
    
    def record_trade(self, asset, intended_price, actual_price, shares):
        """Record trade for analysis."""
        self.trades.append({
            'asset': asset,
            'intended': intended_price,
            'actual': actual_price,
            'shares': shares,
            'slippage': (actual_price - intended_price) / intended_price
        })
    
    def get_metrics(self) -> dict:
        """Calculate execution metrics."""
        if not self.trades:
            return {}
        
        slippages = [t['slippage'] for t in self.trades]
        
        return {
            'avg_slippage': np.mean(slippages),
            'max_slippage': np.max(np.abs(slippages)),
            'total_trades': len(self.trades),
            'slippage_std': np.std(slippages)
        }
```

## Integration Example

```python
def initialize(context):
    context.order_manager = OrderManager()
    
    schedule_function(rebalance, date_rules.week_start(), 
                     time_rules.market_open(hours=1))
    schedule_function(check_orders, date_rules.every_day(),
                     time_rules.market_close(minutes=30))

def rebalance(context, data):
    target_weights = calculate_targets(context, data)
    
    for asset, weight in target_weights.items():
        context.order_manager.place_target_order(asset, weight, context, data)

def check_orders(context, data):
    context.order_manager.update_orders(context, data)
    
    # Cancel any remaining orders before close
    context.order_manager.cancel_all()

def handle_data(context, data):
    context.order_manager.update_orders(context, data)
```

## Script Reference

### order_analysis.py

Analyze order execution from backtest results:

```bash
python scripts/order_analysis.py backtest_results.csv --output execution_report.html
```

## References

See `references/order_types.md` for order type details.
See `references/execution_best_practices.md` for execution tips.
