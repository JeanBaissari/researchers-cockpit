# Risk Management API

Risk management utilities for trading strategies.

Provides functions to check exit conditions based on risk parameters: fixed stop loss, trailing stop loss, and take profit.

**Location:** `lib/risk_management.py`

---

## Overview

The `lib/risk_management` module provides risk management utilities for checking exit conditions during backtest execution. It follows the Single Responsibility Principle by focusing solely on risk management logic, making it reusable across all strategies.

**Key Features:**
- Fixed stop loss (percentage-based from entry price)
- Trailing stop loss (tracks highest price since entry)
- Take profit (locks in gains at target percentage)
- Priority-based exit evaluation (take profit > trailing stop > fixed stop)
- Floating-point tolerant price comparisons
- Integration with strategy parameters

**Exit Condition Priority:**
1. **Take Profit** (highest priority - locks in gains)
2. **Trailing Stop** (takes precedence over fixed stop if both enabled)
3. **Fixed Stop Loss** (lowest priority)

---

## Installation/Dependencies

**Required:**
- `zipline-reloaded` - For Context and DataPortal types
- Python standard library (`logging`, `typing`)

---

## Quick Start

```python
from lib.risk_management import check_exit_conditions, get_exit_type_code
from zipline.api import order_target_percent, record

def check_stop_loss(context, data):
    """Check and execute stop loss, trailing stop, and take profit orders."""
    # Check exit conditions
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    
    if exit_type:
        # Execute exit
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        
        # Record exit type
        exit_type_code = get_exit_type_code(exit_type)
        record(
            stop_triggered=1 if exit_type != 'take_profit' else 0,
            take_profit_triggered=1 if exit_type == 'take_profit' else 0,
            exit_type=exit_type_code
        )
```

---

## Public API Reference

### check_exit_conditions()

Check stop loss, trailing stop, and take profit conditions.

**Signature:**
```python
def check_exit_conditions(
    context: 'Context',
    data: 'DataPortal',
    risk_params: dict
) -> Optional[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context` | Context | required | Zipline context object with:<br>- `in_position`: bool indicating if position is open<br>- `asset`: Asset being traded<br>- `entry_price`: float entry price<br>- `highest_price`: float highest price since entry (for trailing stop) |
| `data` | DataPortal | required | Zipline data object for current price |
| `risk_params` | dict | required | Risk management parameters dictionary (from `context.params.get('risk', {})`) |

**Returns:**
- `Optional[str]`: Exit type as string:
  - `'take_profit'` - Take profit condition met
  - `'trailing'` - Trailing stop condition met
  - `'fixed'` - Fixed stop loss condition met
  - `None` - No exit condition met

**Raises:**
- No exceptions raised (defensive programming with early returns)

**Exit Condition Priority:**
1. **Take Profit** - Checked first (highest priority to lock in gains)
2. **Trailing Stop** - Checked second (takes precedence over fixed stop if both enabled)
3. **Fixed Stop Loss** - Checked last (lowest priority)

**Context Requirements:**
The `context` object must have the following attributes:
- `in_position` (bool): Whether a position is currently open
- `asset`: The asset being traded
- `entry_price` (float): Entry price of the position
- `highest_price` (float): Highest price since entry (for trailing stop tracking)

**Note:** The function automatically updates `context.highest_price` to track the highest price since entry for trailing stop calculations.

**Configuration:**
Risk management is configured in `parameters.yaml`:

```yaml
risk:
  use_stop_loss: true            # Enable fixed stop loss
  stop_loss_pct: 0.05            # Fixed stop loss percentage (Range: 0.01-0.15)
  
  use_trailing_stop: false       # Enable trailing stop (tracks highest price)
  trailing_stop_pct: 0.08        # Trailing stop percentage from peak (Range: 0.03-0.20)
  
  use_take_profit: false         # Enable take profit
  take_profit_pct: 0.10          # Take profit percentage (Range: 0.05-0.30)
```

**Example:**
```python
from lib.risk_management import check_exit_conditions
from zipline.api import order_target_percent

def check_stop_loss(context, data):
    """Check exit conditions and execute exit if triggered."""
    # Get risk parameters from strategy config
    risk_params = context.params.get('risk', {})
    
    # Check exit conditions
    exit_type = check_exit_conditions(context, data, risk_params)
    
    if exit_type:
        # Execute exit
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        
        # Log exit (optional)
        print(f"Exit triggered: {exit_type}")
```

**Fixed Stop Loss Example:**
```python
# Configuration in parameters.yaml:
# risk:
#   use_stop_loss: true
#   stop_loss_pct: 0.05  # 5% stop loss

# If entry_price = 100.0 and stop_loss_pct = 0.05:
# - Stop price = 100.0 * (1 - 0.05) = 95.0
# - Exit triggered when current_price <= 95.0
```

**Trailing Stop Example:**
```python
# Configuration in parameters.yaml:
# risk:
#   use_trailing_stop: true
#   trailing_stop_pct: 0.08  # 8% trailing stop

# If entry_price = 100.0, highest_price = 110.0, and trailing_stop_pct = 0.08:
# - Stop price = 110.0 * (1 - 0.08) = 101.2
# - Exit triggered when current_price <= 101.2
# - Trailing stop tracks highest price since entry
```

**Take Profit Example:**
```python
# Configuration in parameters.yaml:
# risk:
#   use_take_profit: true
#   take_profit_pct: 0.10  # 10% take profit

# If entry_price = 100.0 and take_profit_pct = 0.10:
# - Profit target = 100.0 * (1 + 0.10) = 110.0
# - Exit triggered when current_price >= 110.0
```

**Multiple Exit Conditions Example:**
```python
# Configuration with all three exit types enabled:
# risk:
#   use_stop_loss: true
#   stop_loss_pct: 0.05
#   use_trailing_stop: true
#   trailing_stop_pct: 0.08
#   use_take_profit: true
#   take_profit_pct: 0.10

# Priority order:
# 1. Take profit checked first (if price >= entry * 1.10, exit)
# 2. Trailing stop checked second (if price <= highest * 0.92, exit)
# 3. Fixed stop checked last (if price <= entry * 0.95, exit)
```

---

### get_exit_type_code()

Convert exit type string to numeric code for recording.

**Signature:**
```python
def get_exit_type_code(exit_type: Optional[str]) -> int
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exit_type` | Optional[str] | required | Exit type string from `check_exit_conditions()` |

**Returns:**
- `int`: Numeric exit type code:
  - `1` - Fixed stop loss (`'fixed'`)
  - `2` - Trailing stop (`'trailing'`)
  - `3` - Take profit (`'take_profit'`)
  - `0` - No exit (`None`)

**Example:**
```python
from lib.risk_management import check_exit_conditions, get_exit_type_code
from zipline.api import record

def check_stop_loss(context, data):
    """Check exit conditions and record exit type."""
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    
    if exit_type:
        # Execute exit
        order_target_percent(context.asset, 0)
        context.in_position = False
        
        # Record exit type as numeric code
        exit_type_code = get_exit_type_code(exit_type)
        record(
            stop_triggered=1 if exit_type != 'take_profit' else 0,
            take_profit_triggered=1 if exit_type == 'take_profit' else 0,
            exit_type=exit_type_code
        )
    else:
        record(stop_triggered=0, take_profit_triggered=0, exit_type=0)
```

---

## Module Structure

The `lib/risk_management` module contains:

**Public Functions:**
- `check_exit_conditions()` - Main orchestrator for exit condition checking
- `get_exit_type_code()` - Exit type to numeric code conversion

**Internal Functions (not part of public API):**
- `_check_take_profit()` - Take profit condition evaluation
- `_check_trailing_stop()` - Trailing stop condition evaluation
- `_check_fixed_stop()` - Fixed stop loss condition evaluation
- `_is_price_greater_or_equal()` - Floating-point tolerant price comparison
- `_is_price_less_or_equal()` - Floating-point tolerant price comparison
- `_validate_percentage_param()` - Parameter validation and normalization

**Constants:**
- `FLOAT_EPSILON = 1e-6` - Floating point comparison tolerance

---

## Examples

### Basic Stop Loss Integration

```python
from lib.risk_management import check_exit_conditions
from zipline.api import order_target_percent, schedule_function, date_rules, time_rules

def initialize(context):
    # ... strategy setup ...
    
    # Schedule risk management checks
    schedule_function(
        check_stop_loss,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )

def check_stop_loss(context, data):
    """Check and execute stop loss orders."""
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    
    if exit_type:
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
```

### Complete Risk Management Setup

```python
from lib.risk_management import check_exit_conditions, get_exit_type_code
from zipline.api import (
    order_target_percent, record, schedule_function,
    date_rules, time_rules
)

def initialize(context):
    # ... strategy setup ...
    
    # Initialize position tracking
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0
    
    # Schedule risk management checks (more frequent than rebalance)
    schedule_function(
        check_stop_loss,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )

def rebalance(context, data):
    """Main rebalancing logic."""
    # ... signal generation ...
    
    if signal == 1 and not context.in_position:
        # Enter position
        position_size = compute_position_size(context, data, context.params)
        order_target_percent(context.asset, position_size)
        context.in_position = True
        context.entry_price = data.current(context.asset, 'price')
        context.highest_price = context.entry_price  # Initialize for trailing stop
    
    elif signal == -1 and context.in_position:
        # Exit position (signal-based exit)
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0

def check_stop_loss(context, data):
    """Check and execute stop loss, trailing stop, and take profit orders."""
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    
    if exit_type:
        # Execute exit
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0
        
        # Record exit type
        exit_type_code = get_exit_type_code(exit_type)
        record(
            stop_triggered=1 if exit_type != 'take_profit' else 0,
            take_profit_triggered=1 if exit_type == 'take_profit' else 0,
            exit_type=exit_type_code
        )
    else:
        record(stop_triggered=0, take_profit_triggered=0, exit_type=0)
```

### Strategy Template Integration

The strategy template (`strategies/_template/strategy.py`) includes a complete risk management setup:

```python
# In initialize():
if (risk_params.get('use_stop_loss', False) or 
    risk_params.get('use_trailing_stop', False) or 
    risk_params.get('use_take_profit', False)):
    schedule_function(
        check_stop_loss,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )

# In rebalance():
if signal == 1 and not context.in_position:
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
    context.in_position = True
    context.entry_price = current_price
    context.highest_price = current_price  # Initialize for trailing stop
```

---

## Configuration

### Risk Parameters

Risk management parameters are configured in `parameters.yaml`:

```yaml
risk:
  # Fixed Stop Loss
  use_stop_loss: true            # Enable fixed stop loss
  stop_loss_pct: 0.05            # Fixed stop loss percentage (Range: 0.01-0.15)
  
  # Trailing Stop Loss
  use_trailing_stop: false       # Enable trailing stop (tracks highest price)
  trailing_stop_pct: 0.08        # Trailing stop percentage from peak (Range: 0.03-0.20)
  
  # Take Profit
  use_take_profit: false         # Enable take profit
  take_profit_pct: 0.10          # Take profit percentage (Range: 0.05-0.30)
```

**Parameter Validation:**
- All percentage parameters are validated to be in range (0.0, 1.0]
- Invalid parameters are logged with warnings and default values are used
- Default values: `stop_loss_pct=0.05`, `trailing_stop_pct=0.08`, `take_profit_pct=0.10`

---

## Error Handling

**Defensive Programming:**
- Early returns if not in position or asset cannot be traded
- Automatic initialization of `highest_price` if not set
- Floating-point tolerant price comparisons (uses `FLOAT_EPSILON = 1e-6`)
- Parameter validation with default fallbacks

**No Exceptions Raised:**
The module uses defensive programming and does not raise exceptions. Invalid conditions result in `None` return values or default parameter usage.

**Common Issues:**

1. **Missing Context Attributes:**
   - Ensure `context.in_position`, `context.entry_price`, `context.highest_price` are initialized
   - The function uses `getattr()` with defaults for safety

2. **Invalid Parameters:**
   - Invalid percentage parameters are logged and default values are used
   - Check logs for parameter validation warnings

3. **Floating Point Precision:**
   - Uses floating-point tolerant comparisons to handle precision issues
   - `FLOAT_EPSILON = 1e-6` ensures reliable price comparisons

---

## Best Practices

1. **Initialize Context Attributes:**
   ```python
   def initialize(context):
       context.in_position = False
       context.entry_price = 0.0
       context.highest_price = 0.0
   ```

2. **Schedule Risk Checks Separately:**
   - Schedule `check_stop_loss()` more frequently than `rebalance()` for intraday risk management
   - Example: Check every minute vs. rebalance daily

3. **Update Highest Price on Entry:**
   ```python
   if signal == 1 and not context.in_position:
       context.entry_price = current_price
       context.highest_price = current_price  # Initialize for trailing stop
   ```

4. **Record Exit Types:**
   - Use `get_exit_type_code()` to record exit types for analysis
   - Helps distinguish between different exit reasons in backtest results

5. **Test All Exit Types:**
   - Test fixed stop, trailing stop, and take profit separately
   - Verify priority order (take profit > trailing stop > fixed stop)

---

## See Also

- [Position Sizing API](position_sizing.md) - Position sizing algorithms
- [Backtest API](backtest.md) - Backtest execution
- [Strategy Template](../templates/strategies/) - Complete strategy examples
- [Strategy Development Patterns](../code_patterns/) - Strategy development patterns
- [CLI: run_backtest.py](../../scripts/run_backtest.py) - Backtest execution CLI
