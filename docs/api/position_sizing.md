# Position Sizing API

Position sizing utilities for trading strategies.

Provides functions to calculate position sizes based on various methods: fixed position sizing, volatility-scaled position sizing, and Kelly Criterion position sizing.

**Location:** `lib/position_sizing.py`

---

## Overview

The `lib/position_sizing` module provides position sizing algorithms for risk-adjusted position allocation. It follows the Single Responsibility Principle by focusing solely on position sizing calculations, making it reusable across all strategies.

**Key Features:**
- Multiple position sizing algorithms
- Risk-adjusted position sizing
- Integration with strategy parameters
- Automatic bounds checking (min/max position limits)

**Supported Methods:**
1. **Fixed** - Simple percentage-based sizing
2. **Volatility Scaled** - Inverse volatility scaling to target volatility
3. **Kelly Criterion** - Optimal bet sizing based on win rate and win/loss ratio

---

## Installation/Dependencies

**Required:**
- `numpy` - For numerical calculations
- `zipline-reloaded` - For Context and DataPortal types
- Python standard library (`logging`, `typing`)

---

## Quick Start

```python
from lib.position_sizing import compute_position_size
from zipline.api import order_target_percent

# In rebalance() function
def rebalance(context, data):
    # Calculate position size based on configured method
    position_size = compute_position_size(context, data, context.params)
    
    # Execute order
    order_target_percent(context.asset, position_size)
```

---

## Public API Reference

### compute_position_size()

Calculate position size based on the configured method.

**Signature:**
```python
def compute_position_size(
    context: 'Context',
    data: 'DataPortal',
    params: dict
) -> float
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context` | Context | required | Zipline context object with params attribute |
| `data` | DataPortal | required | Zipline data object for price history |
| `params` | dict | required | Strategy parameters dictionary (can also use `context.params`) |

**Returns:**
- `float`: Position size as a percentage (0.0 to `max_position_pct`)

**Raises:**
- `ValueError`: If position sizing configuration is invalid

**Supported Methods:**
- `'fixed'` - Returns `max_position_pct` directly
- `'volatility_scaled'` - Scales position inversely with volatility to target volatility
- `'kelly'` - Uses Kelly Criterion with fractional sizing for capital preservation

**Configuration:**
Position sizing is configured in `parameters.yaml`:

```yaml
position_sizing:
  method: fixed  # 'fixed', 'volatility_scaled', or 'kelly'
  max_position_pct: 0.95  # Maximum portfolio allocation (0.10-1.00)
  min_position_pct: 0.10  # Minimum position size (0.05-0.30)
```

**Example:**
```python
from lib.position_sizing import compute_position_size
from zipline.api import order_target_percent

def rebalance(context, data):
    # Calculate position size
    position_size = compute_position_size(context, data, context.params)
    
    # Execute order with calculated size
    order_target_percent(context.asset, position_size)
```

---

## Position Sizing Methods

### Fixed Position Sizing

Simple percentage-based position sizing. Returns `max_position_pct` directly.

**Configuration:**
```yaml
position_sizing:
  method: fixed
  max_position_pct: 0.95  # Use 95% of portfolio
  min_position_pct: 0.10  # Minimum 10% (not used for fixed method)
```

**Use Cases:**
- Simple strategies with consistent position sizes
- Strategies that don't require dynamic sizing
- Initial strategy development

**Example:**
```python
# Always uses max_position_pct (0.95 = 95% of portfolio)
position_size = compute_position_size(context, data, context.params)
# Returns: 0.95
```

---

### Volatility Scaled Position Sizing

Scales position inversely with volatility to target a specific volatility level.

**Formula:**
```
position = volatility_target / current_volatility
```

**Configuration:**
```yaml
position_sizing:
  method: volatility_scaled
  max_position_pct: 0.95
  min_position_pct: 0.10
  volatility_lookback: 20  # Days for volatility calculation (10-60)
  volatility_target: 0.15  # Target annualized volatility (0.05-0.30)
```

**How It Works:**
1. Calculates current volatility from price history
2. Scales position inversely: higher volatility → smaller position
3. Clips result to `[min_position_pct, max_position_pct]` bounds

**Use Cases:**
- Risk parity strategies
- Volatility targeting
- Strategies that need consistent risk exposure

**Example:**
```python
# If current volatility is 20% and target is 15%:
# position = 0.15 / 0.20 = 0.75 (75% of portfolio)
position_size = compute_position_size(context, data, context.params)
# Returns: 0.75 (clipped to bounds)
```

**Asset Class Support:**
- Automatically uses correct trading days for annualization:
  - Equities: 252 trading days
  - Forex: 260 trading days
  - Crypto: 365 trading days

**Fallback Behavior:**
- If insufficient price history: falls back to `max_position_pct`
- If asset cannot be traded: falls back to `max_position_pct`
- If zero volatility: falls back to `max_position_pct`
- On calculation errors: falls back to `max_position_pct`

---

### Kelly Criterion Position Sizing

Uses Kelly Criterion for optimal bet sizing based on win rate and win/loss ratio.

**Kelly Formula:**
```
f* = (bp - q) / b
where:
  b = avg_win / avg_loss (win/loss ratio)
  p = win_rate
  q = 1 - p (loss rate)
```

**Fractional Kelly:**
Full Kelly can be aggressive. Fractional Kelly (typically 0.25-0.50) is recommended for capital preservation.

**Configuration:**
```yaml
position_sizing:
  method: kelly
  max_position_pct: 0.95
  min_position_pct: 0.10
  kelly:
    win_rate_estimate: 0.55  # Estimated win rate from backtests (0.40-0.70)
    avg_win_loss_ratio: 1.5  # Average win / average loss (1.0-3.0)
    kelly_fraction: 0.25  # Fraction of full Kelly to use (0.10-0.50)
    min_position_pct: 0.10  # Minimum position for Kelly (0.05-0.30)
```

**How It Works:**
1. Calculates full Kelly percentage from win rate and win/loss ratio
2. Applies fractional Kelly (typically 0.25-0.50 of full Kelly)
3. Clips result to `[kelly_min, max_position_pct]` bounds

**Use Cases:**
- Strategies with known win rates and win/loss ratios
- Long-term capital growth optimization
- Strategies with consistent edge

**Example:**
```python
# If win_rate=0.55, win_loss_ratio=1.5, kelly_fraction=0.25:
# full_kelly = (1.5 * 0.55 - 0.45) / 1.5 = 0.30
# position = 0.30 * 0.25 = 0.075 (7.5% of portfolio)
position_size = compute_position_size(context, data, context.params)
# Returns: 0.075 (clipped to bounds)
```

**Parameter Estimation:**
Kelly parameters should be estimated from:
- Backtest results (historical win rate, avg win/loss)
- Paper trading results
- Statistical analysis of strategy performance

**Important Notes:**
- Full Kelly can be > 100% for high-edge strategies (fractional Kelly prevents this)
- Kelly assumes constant win rate and win/loss ratio (may not hold in practice)
- Fractional Kelly (0.25-0.50) is recommended for capital preservation

---

## Module Structure

The `lib/position_sizing` module consists of:

1. **Main Function** (`compute_position_size()`)
   - Orchestrator that routes to appropriate method
   - Parameter validation
   - Bounds checking

2. **Volatility Scaling** (`_compute_volatility_scaled_size()`)
   - Internal function for volatility-based sizing
   - Price history analysis
   - Asset class-aware annualization

3. **Kelly Criterion** (`_compute_kelly_size()`)
   - Internal function for Kelly-based sizing
   - Fractional Kelly application
   - Parameter validation

---

## Examples

### Fixed Position Sizing

```python
from lib.position_sizing import compute_position_size
from zipline.api import order_target_percent

def rebalance(context, data):
    # Fixed 95% position size
    position_size = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, position_size)
```

**parameters.yaml:**
```yaml
position_sizing:
  method: fixed
  max_position_pct: 0.95
  min_position_pct: 0.10
```

### Volatility Scaled Position Sizing

```python
from lib.position_sizing import compute_position_size
from zipline.api import order_target_percent

def rebalance(context, data):
    # Volatility-scaled position (targets 15% annualized volatility)
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

### Kelly Criterion Position Sizing

```python
from lib.position_sizing import compute_position_size
from zipline.api import order_target_percent

def rebalance(context, data):
    # Kelly-based position sizing (25% of full Kelly)
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
    win_rate_estimate: 0.55
    avg_win_loss_ratio: 1.5
    kelly_fraction: 0.25
    min_position_pct: 0.10
```

### Integration with Strategy Template

```python
# In strategies/_template/strategy.py
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    signal, additional_data = compute_signals(context, data)
    
    if signal == 1 and not context.in_position:
        # Calculate position size based on configured method
        position_size = compute_position_size(context, data, context.params)
        order_target_percent(context.asset, position_size)
        context.in_position = True
```

---

## Configuration

### Strategy Parameters

Position sizing is configured in `parameters.yaml`:

```yaml
position_sizing:
  max_position_pct: 0.95  # Maximum portfolio allocation (Range: 0.10-1.00)
  min_position_pct: 0.10  # Minimum position size (Range: 0.05-0.30)
  method: fixed  # 'fixed', 'volatility_scaled', or 'kelly'
  
  # Volatility Scaling (if method = 'volatility_scaled')
  volatility_lookback: 20  # Days for volatility calculation (Range: 10-60)
  volatility_target: 0.15  # Target annualized volatility (Range: 0.05-0.30)
  
  # Kelly Criterion (if method = 'kelly')
  kelly:
    win_rate_estimate: 0.55  # Estimated win rate (Range: 0.40-0.70)
    avg_win_loss_ratio: 1.5  # Average win / average loss (Range: 1.0-3.0)
    kelly_fraction: 0.25  # Fraction of full Kelly (Range: 0.10-0.50)
    min_position_pct: 0.10  # Minimum position (Range: 0.05-0.30)
```

### Parameter Validation

The function validates:
- `max_position_pct` must be between 0.0 and 1.0
- `min_position_pct` must be between 0.0 and 1.0
- `min_position_pct` cannot be greater than `max_position_pct`

**Invalid Configuration:**
```python
# Raises ValueError
position_sizing:
  max_position_pct: 1.5  # Invalid: > 1.0
  min_position_pct: 0.20
  max_position_pct: 0.10  # Invalid: min > max
```

---

## Error Handling

### Invalid Configuration

If position sizing configuration is invalid:

```python
# Raises ValueError with descriptive message
try:
    position_size = compute_position_size(context, data, context.params)
except ValueError as e:
    print(f"Invalid position sizing config: {e}")
    # Handle error (e.g., use default position size)
```

### Volatility Calculation Errors

For volatility-scaled sizing, errors are handled gracefully:

- **Insufficient data**: Falls back to `max_position_pct`
- **Zero volatility**: Falls back to `max_position_pct`
- **Calculation errors**: Falls back to `max_position_pct`
- **Asset cannot be traded**: Falls back to `max_position_pct`

All fallbacks are logged at debug/warning level.

### Unknown Method

If an unknown method is specified:

```python
# Issues warning and falls back to 'fixed' method
position_sizing:
  method: unknown_method  # Will use 'fixed' with warning
```

---

## Best Practices

### 1. Choose Appropriate Method

```python
# ✅ GOOD - Fixed for simple strategies
position_sizing:
  method: fixed
  max_position_pct: 0.95

# ✅ GOOD - Volatility scaled for risk parity
position_sizing:
  method: volatility_scaled
  volatility_target: 0.15

# ✅ GOOD - Kelly for strategies with known edge
position_sizing:
  method: kelly
  kelly:
    win_rate_estimate: 0.55  # From backtests
    avg_win_loss_ratio: 1.5
    kelly_fraction: 0.25
```

### 2. Use Fractional Kelly

```python
# ❌ BAD - Full Kelly can be too aggressive
kelly:
  kelly_fraction: 1.0  # Too risky!

# ✅ GOOD - Fractional Kelly for safety
kelly:
  kelly_fraction: 0.25  # Conservative
```

### 3. Estimate Kelly Parameters from Data

```python
# ✅ GOOD - Estimate from backtest results
# After running backtest, analyze:
# - Win rate: 55%
# - Avg win: $150
# - Avg loss: $100
# - Win/loss ratio: 1.5

kelly:
  win_rate_estimate: 0.55  # From actual backtest
  avg_win_loss_ratio: 1.5  # From actual backtest
  kelly_fraction: 0.25  # Conservative fraction
```

### 4. Set Appropriate Bounds

```python
# ✅ GOOD - Reasonable bounds
position_sizing:
  max_position_pct: 0.95  # Allow most of portfolio
  min_position_pct: 0.10  # Minimum meaningful position

# ❌ BAD - Too restrictive
position_sizing:
  max_position_pct: 0.50  # Too conservative
  min_position_pct: 0.05  # Too small to matter
```

### 5. Validate Configuration

```python
# In strategy development, validate config:
try:
    position_size = compute_position_size(context, data, context.params)
    assert 0.0 <= position_size <= 1.0, f"Invalid position size: {position_size}"
except ValueError as e:
    logger.error(f"Position sizing config error: {e}")
    # Use safe default
    position_size = 0.50
```

---

## Algorithm Details

### Volatility Scaling Formula

**Annualized Volatility:**
```python
current_vol = returns.std() * sqrt(trading_days)
```

**Position Size:**
```python
size = volatility_target / current_vol
position_size = clip(size, min_position, max_position)
```

**Example:**
- Target volatility: 15% (0.15)
- Current volatility: 20% (0.20)
- Position size: 0.15 / 0.20 = 0.75 (75%)

### Kelly Criterion Formula

**Full Kelly:**
```python
b = avg_win_loss_ratio
p = win_rate
q = 1 - p
full_kelly = (b * p - q) / b
```

**Fractional Kelly:**
```python
position_size = full_kelly * kelly_fraction
position_size = clip(position_size, kelly_min, max_position)
```

**Example:**
- Win rate: 55% (0.55)
- Win/loss ratio: 1.5
- Kelly fraction: 0.25
- Full Kelly: (1.5 * 0.55 - 0.45) / 1.5 = 0.30
- Position size: 0.30 * 0.25 = 0.075 (7.5%)

---

## See Also

- [Strategies API](strategies.md) - Strategy development patterns
- [Risk Management API](risk_management.md) - Risk management utilities
- [Backtest API](backtest.md) - Backtest execution
- [Strategy Template](../templates/strategies/) - Strategy template with position sizing integration
