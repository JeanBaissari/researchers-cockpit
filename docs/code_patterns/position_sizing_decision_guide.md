# Position Sizing Decision Guide

> When to use Zipline's `order_target_percent()` vs `lib/position_sizing.py`

This guide helps you decide when to use Zipline-Reloaded's native `order_target_percent()` function directly versus using `lib/position_sizing.py` for advanced position sizing calculations.

---

## Quick Decision Tree

```
Do you need advanced position sizing algorithms?
│
├─ NO → Use Zipline's order_target_percent() directly
│   └─ Simple fixed percentages, signal-based allocation, equal-weight rebalancing
│
└─ YES → Use lib/position_sizing.py + order_target_percent()
    ├─ Volatility-scaled sizing (risk parity)
    ├─ Kelly Criterion sizing (optimal bet sizing)
    └─ Fixed sizing with parameterized configuration
```

---

## When to Use Zipline's `order_target_percent()` Directly

Use Zipline's `order_target_percent()` directly when you have **simple, static position sizing** that doesn't require advanced calculations.

### ✅ Use Cases

1. **Simple Fixed Percentages**
   ```python
   from zipline.api import order_target_percent
   
   def rebalance(context, data):
       # Always use 50% of portfolio
       order_target_percent(context.asset, 0.50)
   ```

2. **Signal-Based Allocation**
   ```python
   from zipline.api import order_target_percent
   
   def rebalance(context, data):
       signal = compute_signal(context, data)
       
       if signal > 0.8:
           order_target_percent(context.asset, 0.90)  # Strong buy
       elif signal > 0.5:
           order_target_percent(context.asset, 0.50)  # Moderate buy
       elif signal < -0.5:
           order_target_percent(context.asset, 0.0)   # Exit
   ```

3. **Equal-Weight Rebalancing**
   ```python
   from zipline.api import order_target_percent
   
   def rebalance(context, data):
       weight = 1.0 / len(context.assets)
       
       for asset in context.assets:
           if data.can_trade(asset):
               order_target_percent(asset, weight)
   ```

4. **Long/Short Portfolio**
   ```python
   from zipline.api import order_target_percent
   
   def rebalance(context, data):
       # Long positions: 50% each
       for asset in context.longs:
           order_target_percent(asset, 0.50)
       
       # Short positions: -25% each
       for asset in context.shorts:
           order_target_percent(asset, -0.25)
   ```

5. **Dynamic Calculation in Strategy Logic**
   ```python
   from zipline.api import order_target_percent
   
   def rebalance(context, data):
       # Calculate position size based on custom strategy logic
       confidence = compute_confidence(context, data)
       volatility = compute_volatility(context, data)
       
       # Custom calculation (not using lib/position_sizing)
       position_size = confidence * (0.20 / volatility)
       position_size = min(position_size, 0.95)  # Cap at 95%
       
       order_target_percent(context.asset, position_size)
   ```

### Characteristics

- **Simple**: Position size is a constant or simple calculation
- **Static**: Position size doesn't change based on market conditions
- **Strategy-Specific**: Calculation is unique to your strategy logic
- **No Configuration**: Position size is hardcoded or calculated inline

---

## When to Use `lib/position_sizing.py`

Use `lib/position_sizing.py` when you need **advanced, risk-adjusted position sizing algorithms** that are parameterized and reusable across strategies.

### ✅ Use Cases

1. **Volatility-Scaled Position Sizing (Risk Parity)**
   ```python
   from zipline.api import order_target_percent
   from lib.position_sizing import compute_position_size
   
   def rebalance(context, data):
       # Automatically scales position inversely with volatility
       # to target 15% annualized volatility
       position_size = compute_position_size(context, data, context.params)
       order_target_percent(context.asset, position_size)
   ```
   
   **Configuration (parameters.yaml):**
   ```yaml
   position_sizing:
     method: volatility_scaled
     max_position_pct: 0.95
     min_position_pct: 0.10
     volatility_lookback: 20
     volatility_target: 0.15  # Target 15% annualized volatility
   ```
   
   **Why use lib/position_sizing.py:**
   - Automatically calculates current volatility from price history
   - Scales position to target volatility level
   - Handles asset class differences (equities: 252 days, forex: 260 days, crypto: 365 days)
   - Graceful fallbacks for insufficient data or errors

2. **Kelly Criterion Position Sizing**
   ```python
   from zipline.api import order_target_percent
   from lib.position_sizing import compute_position_size
   
   def rebalance(context, data):
       # Optimal bet sizing based on win rate and win/loss ratio
       position_size = compute_position_size(context, data, context.params)
       order_target_percent(context.asset, position_size)
   ```
   
   **Configuration (parameters.yaml):**
   ```yaml
   position_sizing:
     method: kelly
     max_position_pct: 0.95
     min_position_pct: 0.10
     kelly:
       win_rate_estimate: 0.55  # From backtest analysis
       avg_win_loss_ratio: 1.5  # From backtest analysis
       kelly_fraction: 0.25       # Fractional Kelly (conservative)
   ```
   
   **Why use lib/position_sizing.py:**
   - Implements Kelly Criterion formula correctly
   - Applies fractional Kelly for capital preservation
   - Validates parameters and handles edge cases
   - Reusable across strategies with different win rates

3. **Fixed Sizing with Parameterized Configuration**
   ```python
   from zipline.api import order_target_percent
   from lib.position_sizing import compute_position_size
   
   def rebalance(context, data):
       # Fixed sizing, but configured via parameters.yaml
       position_size = compute_position_size(context, data, context.params)
       order_target_percent(context.asset, position_size)
   ```
   
   **Configuration (parameters.yaml):**
   ```yaml
   position_sizing:
     method: fixed
     max_position_pct: 0.95
     min_position_pct: 0.10
   ```
   
   **Why use lib/position_sizing.py even for fixed sizing:**
   - Centralized configuration in `parameters.yaml`
   - Consistent interface across all position sizing methods
   - Easy to switch between methods (fixed → volatility_scaled → kelly)
   - Parameter validation and bounds checking

### Characteristics

- **Advanced Algorithms**: Volatility scaling, Kelly Criterion, risk parity
- **Parameterized**: Configuration via `parameters.yaml`, not hardcoded
- **Reusable**: Same algorithms work across different strategies
- **Risk-Adjusted**: Position size adapts to market conditions
- **Validated**: Built-in parameter validation and error handling

---

## Comparison Table

| Feature | `order_target_percent()` Direct | `lib/position_sizing.py` |
|---------|--------------------------------|--------------------------|
| **Complexity** | Simple | Advanced algorithms |
| **Configuration** | Hardcoded or inline calculation | `parameters.yaml` |
| **Volatility Scaling** | Manual calculation required | Built-in with asset class awareness |
| **Kelly Criterion** | Manual implementation required | Built-in with fractional Kelly |
| **Parameter Validation** | Manual | Automatic |
| **Error Handling** | Manual | Graceful fallbacks |
| **Reusability** | Strategy-specific | Reusable across strategies |
| **Best For** | Simple, static sizing | Risk-adjusted, dynamic sizing |

---

## Integration Pattern

Both approaches use Zipline's `order_target_percent()` for order execution. The difference is **how you calculate the position size**:

### Pattern 1: Direct `order_target_percent()` (Simple)

```python
from zipline.api import order_target_percent

def rebalance(context, data):
    # Calculate position size inline
    position_size = 0.50  # Simple fixed percentage
    
    # Execute order
    order_target_percent(context.asset, position_size)
```

### Pattern 2: `lib/position_sizing.py` + `order_target_percent()` (Advanced)

```python
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    # Calculate position size using advanced algorithm
    position_size = compute_position_size(context, data, context.params)
    
    # Execute order (same Zipline API)
    order_target_percent(context.asset, position_size)
```

**Key Point:** `lib/position_sizing.py` **complements** Zipline's `order_target_percent()`, it does **not replace** it. You always use `order_target_percent()` to execute orders.

---

## Examples

### Example 1: Simple Strategy (Use `order_target_percent()` Directly)

```python
from zipline.api import order_target_percent, symbol

def initialize(context):
    context.asset = symbol('SPY')
    context.target_allocation = 0.90  # 90% of portfolio

def rebalance(context, data):
    # Simple fixed allocation - no need for lib/position_sizing.py
    order_target_percent(context.asset, context.target_allocation)
```

**Why direct:** Simple fixed percentage, no advanced algorithms needed.

---

### Example 2: Volatility-Targeting Strategy (Use `lib/position_sizing.py`)

```python
from zipline.api import order_target_percent, symbol
from lib.position_sizing import compute_position_size

def initialize(context):
    context.asset = symbol('SPY')

def rebalance(context, data):
    # Volatility-scaled sizing - use lib/position_sizing.py
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
```

**parameters.yaml:**
```yaml
position_sizing:
  method: volatility_scaled
  max_position_pct: 0.95
  min_position_pct: 0.10
  volatility_lookback: 20
  volatility_target: 0.15
```

**Why lib/position_sizing.py:** Volatility scaling requires price history analysis, asset class awareness, and error handling - all provided by the library.

---

### Example 3: Signal-Based with Custom Logic (Use `order_target_percent()` Directly)

```python
from zipline.api import order_target_percent, symbol

def initialize(context):
    context.asset = symbol('SPY')

def rebalance(context, data):
    signal = compute_signal(context, data)
    confidence = compute_confidence(context, data)
    
    # Custom position sizing logic specific to this strategy
    if signal > 0.8 and confidence > 0.9:
        position_size = 0.95
    elif signal > 0.5:
        position_size = 0.50
    else:
        position_size = 0.0
    
    order_target_percent(context.asset, position_size)
```

**Why direct:** Custom logic specific to strategy signals, not a standard algorithm.

---

### Example 4: Kelly Criterion Strategy (Use `lib/position_sizing.py`)

```python
from zipline.api import order_target_percent, symbol
from lib.position_sizing import compute_position_size

def initialize(context):
    context.asset = symbol('SPY')

def rebalance(context, data):
    # Kelly Criterion sizing - use lib/position_sizing.py
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
```

**parameters.yaml:**
```yaml
position_sizing:
  method: kelly
  max_position_pct: 0.95
  min_position_pct: 0.10
  kelly:
    win_rate_estimate: 0.55      # From backtest: 55% win rate
    avg_win_loss_ratio: 1.5       # From backtest: avg win / avg loss
    kelly_fraction: 0.25          # Conservative: 25% of full Kelly
```

**Why lib/position_sizing.py:** Kelly Criterion requires correct formula implementation, fractional Kelly application, and parameter validation - all provided by the library.

---

## Migration Guide

### Migrating from Direct `order_target_percent()` to `lib/position_sizing.py`

**Before (Direct):**
```python
def rebalance(context, data):
    # Hardcoded position size
    order_target_percent(context.asset, 0.90)
```

**After (Using lib/position_sizing.py):**
```python
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    # Parameterized position size
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
```

**Add to parameters.yaml:**
```yaml
position_sizing:
  method: fixed
  max_position_pct: 0.90
  min_position_pct: 0.10
```

**Benefits:**
- Centralized configuration
- Easy to switch to volatility_scaled or kelly later
- Parameter validation
- Consistent interface

---

## Best Practices

### 1. Start Simple, Add Complexity When Needed

```python
# ✅ GOOD - Start with direct order_target_percent()
def rebalance(context, data):
    order_target_percent(context.asset, 0.50)

# Later, if you need volatility scaling:
from lib.position_sizing import compute_position_size
def rebalance(context, data):
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
```

### 2. Use `lib/position_sizing.py` for Reusable Algorithms

```python
# ✅ GOOD - Use library for standard algorithms
from lib.position_sizing import compute_position_size

# ❌ BAD - Reimplementing Kelly Criterion manually
def compute_kelly_manually(win_rate, win_loss_ratio):
    # Don't duplicate library functionality
    pass
```

### 3. Use Direct `order_target_percent()` for Strategy-Specific Logic

```python
# ✅ GOOD - Custom logic specific to your strategy
def rebalance(context, data):
    signal = compute_signal(context, data)
    position_size = my_custom_calculation(signal)
    order_target_percent(context.asset, position_size)

# ❌ BAD - Using library for simple custom logic
from lib.position_sizing import compute_position_size
# ... but then overriding with custom logic anyway
```

### 4. Always Use `order_target_percent()` for Order Execution

```python
# ✅ GOOD - Always use Zipline's API for execution
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

position_size = compute_position_size(context, data, context.params)
order_target_percent(context.asset, position_size)

# ❌ BAD - Don't try to replace order_target_percent()
# lib/position_sizing.py doesn't execute orders, it only calculates sizes
```

---

## Summary

| Scenario | Recommendation |
|----------|----------------|
| Simple fixed percentage | Use `order_target_percent()` directly |
| Signal-based allocation | Use `order_target_percent()` directly |
| Equal-weight rebalancing | Use `order_target_percent()` directly |
| Custom strategy-specific logic | Use `order_target_percent()` directly |
| Volatility-scaled sizing | Use `lib/position_sizing.py` + `order_target_percent()` |
| Kelly Criterion sizing | Use `lib/position_sizing.py` + `order_target_percent()` |
| Parameterized fixed sizing | Use `lib/position_sizing.py` + `order_target_percent()` |
| Risk parity strategies | Use `lib/position_sizing.py` + `order_target_percent()` |

**Remember:** `lib/position_sizing.py` **complements** Zipline's `order_target_percent()`, it does **not replace** it. You always use `order_target_percent()` to execute orders.

---

## See Also

- [Position Sizing API Reference](../api/position_sizing.md) - Complete API documentation
- [Target Orders Code Pattern](../archive/code_patterns/04_orders/target_orders.md) - Zipline order functions
- [Strategy Template](../strategies/_template/strategy.py) - Example integration
- [Zipline-Reloaded Documentation](https://github.com/stefan-jansen/zipline-reloaded) - Framework reference
