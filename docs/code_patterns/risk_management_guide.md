# Risk Management Guide: Zipline Controls vs lib/risk_management.py

> **When to use Zipline's built-in controls vs lib/risk_management.py utilities**

This guide explains the distinction between Zipline-Reloaded's built-in risk controls and the strategy-level exit conditions provided by `lib/risk_management.py`.

---

## Quick Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│ Need to prevent invalid orders/positions?               │
│ → Use Zipline's Built-in Controls                       │
│   (set_max_position_size, set_max_leverage, etc.)      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Need strategy-level exit conditions?                    │
│ (stop loss, trailing stop, take profit)                  │
│ → Use lib/risk_management.py                            │
│   (check_exit_conditions)                               │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Need to configure transaction costs?                    │
│ → Use Zipline's Built-in Controls                       │
│   (set_slippage, set_commission)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Overview

### Zipline's Built-in Controls

**Purpose:** Prevent invalid orders and positions at the engine level.

**When to Use:**
- Enforce position/order size limits
- Prevent excessive leverage
- Restrict trading specific assets
- Configure transaction costs (slippage, commission)

**Characteristics:**
- ✅ Enforced automatically by Zipline engine
- ✅ Fail fast (raises `TradingControlViolation` if violated)
- ✅ Applied to ALL orders automatically
- ✅ Cannot be bypassed by strategy code

### lib/risk_management.py Utilities

**Purpose:** Strategy-level exit conditions based on price movements.

**When to Use:**
- Fixed stop loss (exit at fixed % below entry)
- Trailing stop loss (exit at % below highest price)
- Take profit (exit at fixed % above entry)

**Characteristics:**
- ✅ Strategy logic (checked in `handle_data()` or `rebalance()`)
- ✅ Returns exit type for strategy to act on
- ✅ Requires strategy code to execute exit orders
- ✅ Can be customized per strategy

---

## Zipline's Built-in Controls

### 1. Position Limits

**Use:** Prevent positions from exceeding size limits.

**Zipline API:**
```python
from zipline.api import set_max_position_size

# In initialize():
set_max_position_size(
    asset=None,              # None = all assets, or specific Asset
    max_shares=1000,         # Maximum share count
    max_notional=100000,     # Maximum dollar value
    on_error='fail'          # 'fail' (raise) or 'log' (warn)
)
```

**Example:**
```python
def initialize(context):
    # Limit all positions to 1000 shares or $100k
    set_max_position_size(
        max_shares=1000,
        max_notional=100000,
        on_error='fail'
    )
    
    # Stricter limit for specific asset
    set_max_position_size(
        asset=symbol('TSLA'),
        max_shares=100,
        max_notional=50000
    )
```

**When to Use:**
- ✅ Enforce position size limits across all strategies
- ✅ Prevent accidental oversized positions
- ✅ Compliance with regulatory limits

**When NOT to Use:**
- ❌ Don't use for stop loss logic (use `lib/risk_management.py` instead)
- ❌ Don't use for position sizing calculations (use `lib/position_sizing.py` instead)

---

### 2. Order Limits

**Use:** Prevent individual orders from exceeding size limits.

**Zipline API:**
```python
from zipline.api import set_max_order_size

# In initialize():
set_max_order_size(
    asset=None,              # None = all assets, or specific Asset
    max_shares=500,         # Maximum share count per order
    max_notional=50000,      # Maximum dollar value per order
    on_error='fail'          # 'fail' (raise) or 'log' (warn)
)
```

**Example:**
```python
def initialize(context):
    # Limit all orders to 500 shares or $50k
    set_max_order_size(
        max_shares=500,
        max_notional=50000,
        on_error='fail'
    )
```

**When to Use:**
- ✅ Prevent large single orders that could move the market
- ✅ Enforce order size limits for risk management
- ✅ Compliance with exchange order size limits

---

### 3. Leverage Controls

**Use:** Prevent excessive leverage.

**Zipline API:**
```python
from zipline.api import set_max_leverage, set_long_only

# In initialize():
set_max_leverage(2.0)        # Max 2x leverage
set_long_only(on_error='fail')  # Prevent short selling
```

**Example:**
```python
def initialize(context):
    # Limit to 2x leverage
    set_max_leverage(2.0)
    
    # Long-only strategy
    set_long_only(on_error='fail')
```

**When to Use:**
- ✅ Enforce leverage limits (e.g., 2x max leverage)
- ✅ Long-only strategies (prevent short selling)
- ✅ Compliance with margin requirements

---

### 4. Restricted Assets

**Use:** Prevent trading specific assets.

**Zipline API:**
```python
from zipline.api import set_do_not_order_list

# In initialize():
set_do_not_order_list(
    restricted_list,         # List of Assets to restrict
    on_error='fail'          # 'fail' (raise) or 'log' (warn)
)
```

**Example:**
```python
def initialize(context):
    # Prevent trading penny stocks or specific assets
    restricted = [symbol('SIRI'), symbol('F'), symbol('GE')]
    set_do_not_order_list(restricted, on_error='fail')
```

**When to Use:**
- ✅ Blacklist specific assets (penny stocks, low liquidity)
- ✅ Compliance restrictions (e.g., no crypto in retirement accounts)
- ✅ Risk management (avoid volatile assets)

---

### 5. Order Count Limits

**Use:** Prevent excessive order frequency.

**Zipline API:**
```python
from zipline.api import set_max_order_count

# In initialize():
set_max_order_count(
    max_count=10,            # Max orders per day
    on_error='fail'          # 'fail' (raise) or 'log' (warn)
)
```

**Example:**
```python
def initialize(context):
    # Limit to 10 orders per day
    set_max_order_count(10, on_error='fail')
```

**When to Use:**
- ✅ Prevent excessive trading (overtrading protection)
- ✅ Reduce transaction costs
- ✅ Compliance with trading frequency limits

---

### 6. Transaction Costs

**Use:** Configure realistic slippage and commission models.

**Zipline API:**
```python
from zipline.api import set_commission, set_slippage
from zipline.finance import commission, slippage

# In initialize():
# Commission model
set_commission(
    us_equities=commission.PerShare(
        cost=0.005,              # $0.005 per share
        min_trade_cost=1.0      # $1.00 minimum
    )
)

# Slippage model
set_slippage(
    us_equities=slippage.VolumeShareSlippage(
        volume_limit=0.025,      # Max 2.5% of bar volume
        price_impact=0.1          # Price impact coefficient
    )
)
```

**Example:**
```python
def initialize(context):
    # Configure commission from parameters.yaml
    commission_config = context.params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )
    
    # Configure slippage from parameters.yaml
    slippage_config = context.params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )
```

**When to Use:**
- ✅ Always configure for realistic backtests
- ✅ Model transaction costs accurately
- ✅ Test strategy robustness to costs

**Available Models:**

**Commission:**
- `commission.PerShare(cost, min_trade_cost)` - Per share with minimum
- `commission.PerTrade(cost)` - Fixed per trade
- `commission.PerDollar(cost)` - Percentage of trade value
- `commission.NoCommission()` - No commission (unrealistic)

**Slippage:**
- `slippage.VolumeShareSlippage(volume_limit, price_impact)` - Volume-based (recommended)
- `slippage.FixedSlippage(spread)` - Fixed spread per share
- `slippage.FixedBasisPointsSlippage(basis_points, volume_limit)` - Basis points
- `slippage.NoSlippage()` - No slippage (unrealistic)

---

## lib/risk_management.py Utilities

### 1. configure_zipline_controls() Helper

**Use:** Convenience function to configure Zipline controls from parameters.yaml.

**API:**
```python
from lib.risk_management import configure_zipline_controls

# In initialize():
configure_zipline_controls(
    context,
    context.params.get('risk_controls', {})
)
```

**Example:**
```python
def initialize(context):
    # Configure Zipline controls from parameters.yaml
    configure_zipline_controls(
        context,
        context.params.get('risk_controls', {})
    )
```

**parameters.yaml:**
```yaml
risk_controls:
  max_leverage: 2.0
  long_only: false
  max_position_shares: 1000
  max_position_notional: 100000
  max_order_shares: 500
  max_order_notional: 50000
  max_order_count: 10
  restricted_assets: ['SIRI', 'F', 'GE']
  on_error: 'fail'  # 'fail' or 'log'
```

**When to Use:**
- ✅ Configure multiple Zipline controls from YAML config
- ✅ Keep risk controls in parameters.yaml (not hardcoded)
- ✅ Simplify strategy initialization code

**When NOT to Use:**
- ❌ Don't use if you need fine-grained control per asset
- ❌ Don't use if you need dynamic control changes during backtest

---

### 2. check_exit_conditions() - Strategy Exit Logic

**Use:** Check stop loss, trailing stop, and take profit conditions.

**API:**
```python
from lib.risk_management import check_exit_conditions

# In handle_data() or rebalance():
exit_type = check_exit_conditions(
    context,
    data,
    context.params.get('risk', {})
)

if exit_type:
    # Execute exit
    order_target_percent(context.asset, 0)
    context.in_position = False
```

**Example:**
```python
from lib.risk_management import check_exit_conditions, get_exit_type_code
from zipline.api import order_target_percent, record, schedule_function
from zipline.api import date_rules, time_rules

def initialize(context):
    # Initialize position tracking
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0
    
    # Schedule risk checks (more frequent than rebalance)
    schedule_function(
        check_stop_loss,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=1)
    )

def check_stop_loss(context, data):
    """Check exit conditions and execute exit if triggered."""
    exit_type = check_exit_conditions(
        context,
        data,
        context.params.get('risk', {})
    )
    
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

**parameters.yaml:**
```yaml
risk:
  use_stop_loss: true            # Enable fixed stop loss
  stop_loss_pct: 0.05            # 5% stop loss
  
  use_trailing_stop: false       # Enable trailing stop
  trailing_stop_pct: 0.08        # 8% trailing stop from peak
  
  use_take_profit: false         # Enable take profit
  take_profit_pct: 0.10          # 10% take profit
```

**Exit Priority:**
1. **Take Profit** (highest priority - locks in gains)
2. **Trailing Stop** (takes precedence over fixed stop if both enabled)
3. **Fixed Stop Loss** (lowest priority)

**When to Use:**
- ✅ Fixed stop loss (exit at fixed % below entry)
- ✅ Trailing stop loss (exit at % below highest price)
- ✅ Take profit (exit at fixed % above entry)
- ✅ Strategy-level exit logic (not engine-level)

**When NOT to Use:**
- ❌ Don't use for position size limits (use `set_max_position_size()`)
- ❌ Don't use for leverage limits (use `set_max_leverage()`)
- ❌ Don't use for order limits (use `set_max_order_size()`)

---

## Complete Example: Using Both

```python
from zipline.api import (
    symbol, order_target_percent, schedule_function,
    date_rules, time_rules, set_commission, set_slippage,
    set_max_leverage, set_max_position_size
)
from zipline.finance import commission, slippage
from lib.risk_management import (
    configure_zipline_controls,
    check_exit_conditions,
    get_exit_type_code
)
from lib.position_sizing import compute_position_size

def initialize(context):
    params = context.params
    context.asset = symbol(params['strategy']['asset_symbol'])
    
    # Initialize position tracking for exit conditions
    context.in_position = False
    context.entry_price = 0.0
    context.highest_price = 0.0
    
    # ============================================================
    # Zipline Built-in Controls (Engine-Level)
    # ============================================================
    
    # 1. Configure Zipline controls from parameters.yaml
    configure_zipline_controls(
        context,
        params.get('risk_controls', {})
    )
    
    # 2. Configure transaction costs
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )
    
    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )
    
    # ============================================================
    # Strategy-Level Exit Conditions (lib/risk_management.py)
    # ============================================================
    
    # Schedule risk checks (more frequent than rebalance)
    if (params.get('risk', {}).get('use_stop_loss', False) or
        params.get('risk', {}).get('use_trailing_stop', False) or
        params.get('risk', {}).get('use_take_profit', False)):
        schedule_function(
            check_stop_loss,
            date_rule=date_rules.every_day(),
            time_rule=time_rules.market_open(minutes=1)
        )
    
    # Schedule main rebalancing
    schedule_function(
        rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )

def rebalance(context, data):
    """Main rebalancing logic."""
    # ... signal generation ...
    
    if signal == 1 and not context.in_position:
        # Enter position
        position_size = compute_position_size(context, data, context.params)
        order_target_percent(context.asset, position_size)
        
        # Update position tracking for exit conditions
        context.in_position = True
        context.entry_price = data.current(context.asset, 'price')
        context.highest_price = context.entry_price
    
    elif signal == -1 and context.in_position:
        # Exit position (signal-based exit)
        order_target_percent(context.asset, 0)
        context.in_position = False
        context.entry_price = 0.0
        context.highest_price = 0.0

def check_stop_loss(context, data):
    """Check exit conditions and execute exit if triggered."""
    # Use lib/risk_management.py for strategy-level exit logic
    exit_type = check_exit_conditions(
        context,
        data,
        context.params.get('risk', {})
    )
    
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

**parameters.yaml:**
```yaml
strategy:
  asset_symbol: 'SPY'

# Zipline Built-in Controls
risk_controls:
  max_leverage: 2.0
  long_only: false
  max_position_shares: 1000
  max_position_notional: 100000
  max_order_shares: 500
  max_order_count: 10
  on_error: 'fail'

# Strategy-Level Exit Conditions (lib/risk_management.py)
risk:
  use_stop_loss: true
  stop_loss_pct: 0.05
  use_trailing_stop: false
  trailing_stop_pct: 0.08
  use_take_profit: false
  take_profit_pct: 0.10

# Transaction Costs
costs:
  commission:
    per_share: 0.005
    min_cost: 1.0
  slippage:
    volume_limit: 0.025
    price_impact: 0.1
```

---

## Summary Table

| Feature | Zipline Built-in | lib/risk_management.py |
|---------|------------------|------------------------|
| **Position Limits** | ✅ `set_max_position_size()` | ❌ |
| **Order Limits** | ✅ `set_max_order_size()` | ❌ |
| **Leverage Limits** | ✅ `set_max_leverage()` | ❌ |
| **Long-Only** | ✅ `set_long_only()` | ❌ |
| **Restricted Assets** | ✅ `set_do_not_order_list()` | ❌ |
| **Order Count** | ✅ `set_max_order_count()` | ❌ |
| **Slippage** | ✅ `set_slippage()` | ❌ |
| **Commission** | ✅ `set_commission()` | ❌ |
| **Stop Loss** | ❌ | ✅ `check_exit_conditions()` |
| **Trailing Stop** | ❌ | ✅ `check_exit_conditions()` |
| **Take Profit** | ❌ | ✅ `check_exit_conditions()` |
| **Config Helper** | ❌ | ✅ `configure_zipline_controls()` |

---

## Best Practices

### 1. Use Zipline Controls for Engine-Level Protection

```python
# ✅ GOOD - Use Zipline controls for position/order limits
def initialize(context):
    set_max_position_size(max_shares=1000, max_notional=100000)
    set_max_leverage(2.0)
    set_long_only(on_error='fail')
```

### 2. Use lib/risk_management.py for Strategy Exit Logic

```python
# ✅ GOOD - Use lib/risk_management.py for exit conditions
def check_stop_loss(context, data):
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    if exit_type:
        order_target_percent(context.asset, 0)
```

### 3. Always Configure Transaction Costs

```python
# ✅ GOOD - Always configure realistic costs
def initialize(context):
    set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0))
    set_slippage(us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
```

### 4. Use configure_zipline_controls() for YAML Config

```python
# ✅ GOOD - Use helper for YAML-based config
def initialize(context):
    configure_zipline_controls(context, context.params.get('risk_controls', {}))
```

### 5. Don't Mix Concerns

```python
# ❌ BAD - Don't use position limits for stop loss
def initialize(context):
    # Wrong: Using position limits to simulate stop loss
    set_max_position_size(max_notional=95000)  # 5% stop loss? No!
    
# ✅ GOOD - Use proper stop loss
def check_stop_loss(context, data):
    exit_type = check_exit_conditions(context, data, context.params.get('risk', {}))
    if exit_type == 'fixed':
        order_target_percent(context.asset, 0)
```

---

## Related Documentation

- [Risk Management API](../api/risk_management.md) - Complete API reference for `lib/risk_management.py`
- [Position Sizing API](../api/position_sizing.md) - Position sizing algorithms
- [Trading Controls](../archive/code_patterns/05_assets/trading_controls.md) - Zipline trading controls
- [Commission Models](../archive/code_patterns/07_finance/commission_models.md) - Commission model configuration
- [Slippage Models](../archive/code_patterns/07_finance/slippage_models.md) - Slippage model configuration
- [Strategy Template](../../strategies/_template/strategy.py) - Complete strategy example

---

## Questions?

**Q: Should I use Zipline controls or lib/risk_management.py for stop loss?**  
A: Use `lib/risk_management.py` (`check_exit_conditions()`) for stop loss. Zipline controls prevent invalid orders, not exit logic.

**Q: Can I use both Zipline controls and lib/risk_management.py?**  
A: Yes! They complement each other:
- Zipline controls: Engine-level protection (position/order limits)
- lib/risk_management.py: Strategy-level exit logic (stop loss/take profit)

**Q: Do I need to configure transaction costs?**  
A: Yes, always configure realistic slippage and commission for valid backtests. Use `set_slippage()` and `set_commission()`.

**Q: Can I bypass Zipline controls?**  
A: No, Zipline controls are enforced at the engine level and cannot be bypassed by strategy code.

**Q: Can I customize exit conditions?**  
A: Yes, `check_exit_conditions()` is strategy logic. You can modify it or create custom exit logic in your strategy.
