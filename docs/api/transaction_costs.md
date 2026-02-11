# Transaction Costs API

Integration guide for Zipline-Reloaded's `set_commission()` and `set_slippage()` methods.

Provides comprehensive documentation for configuring realistic transaction costs in backtests using Zipline-Reloaded's built-in commission and slippage models.

**Zipline-Reloaded API:** `zipline.api.set_commission()`, `zipline.api.set_slippage()`

**Location:** Configured in `initialize()` function of strategy files

---

## Overview

Transaction costs are critical for realistic backtests. Zipline-Reloaded provides built-in models for commission and slippage that simulate real-world trading costs. This guide documents how to integrate these models into strategies following The Researcher's Cockpit patterns.

> **📖 Related:** See [Risk Management Guide](../code_patterns/risk_management_guide.md) for when to use transaction costs vs other risk controls.

**Key Features:**
- Commission models: PerShare, PerTrade, PerDollar, NoCommission
- Slippage models: VolumeShareSlippage, FixedSlippage, FixedBasisPointsSlippage, NoSlippage
- Configuration via `parameters.yaml` (recommended)
- Asset-class-specific configurations (equities, crypto, forex)
- Integration with strategy template

**Best Practices:**
- ✅ Always configure realistic costs for valid backtests
- ✅ Use `parameters.yaml` for configuration (not hardcoded)
- ✅ Test strategy sensitivity to different cost levels
- ✅ Document cost assumptions in strategy notes

---

## Quick Start

```python
from zipline.api import set_commission, set_slippage
from zipline.finance import commission, slippage

def initialize(context):
    # Load parameters from YAML
    params = context.params
    
    # Configure commission from parameters.yaml
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )
    
    # Configure slippage from parameters.yaml
    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_share: 0.005      # $0.005 per share
    min_cost: 1.0         # $1.00 minimum per trade
  slippage:
    volume_limit: 0.025   # Max 2.5% of bar volume
    price_impact: 0.1     # Price impact coefficient
```

---

## Commission Models

### set_commission()

Configure commission model for backtest execution.

**Zipline-Reloaded API:**
```python
from zipline.api import set_commission

set_commission(us_equities=None, us_futures=None)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `us_equities` | CommissionModel | Commission model for equities (or None) |
| `us_futures` | CommissionModel | Commission model for futures (or None) |

**When to Call:**
- Must be called in `initialize()` function
- Called once at backtest start
- Applies to all trades during backtest

**Note:** For crypto and forex strategies, use `us_equities` parameter (Zipline-Reloaded uses the same commission model interface for all asset classes).

---

### PerShare

Fixed cost per share traded with minimum trade cost.

**API:**
```python
from zipline.finance import commission

commission.PerShare(cost=0.005, min_trade_cost=1.0)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cost` | float | required | Cost per share (e.g., 0.005 = $0.005/share) |
| `min_trade_cost` | float | 0.0 | Minimum commission per trade |

**Example Calculation:**
```
Buy 100 shares at $0.005/share:
  100 × $0.005 = $0.50
  But minimum is $1.00
  Commission = $1.00

Buy 500 shares at $0.005/share:
  500 × $0.005 = $2.50
  Commission = $2.50 (exceeds minimum)
```

**Use Cases:**
- ✅ US equities (Interactive Brokers style)
- ✅ Most retail brokerages
- ✅ Commission scales with position size

**Example:**
```python
def initialize(context):
    set_commission(
        us_equities=commission.PerShare(
            cost=0.005,           # $0.005 per share
            min_trade_cost=1.0   # $1.00 minimum
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_share: 0.005
    min_cost: 1.0
```

---

### PerTrade

Fixed cost per trade regardless of size.

**API:**
```python
from zipline.finance import commission

commission.PerTrade(cost=9.99)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cost` | float | required | Fixed cost per trade |

**Example Calculation:**
```
Buy 100 shares: Commission = $9.99
Buy 10,000 shares: Commission = $9.99 (same)
```

**Use Cases:**
- ✅ Full-service brokerages
- ✅ Fixed-fee brokers
- ✅ Strategies with large position sizes

**Example:**
```python
def initialize(context):
    set_commission(
        us_equities=commission.PerTrade(cost=9.99)
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_trade: 9.99
```

**Note:** Strategy template uses `per_share` and `min_cost`. For `PerTrade`, add custom logic or modify template.

---

### PerDollar

Cost as percentage of trade value.

**API:**
```python
from zipline.finance import commission

commission.PerDollar(cost=0.001)  # 0.1% of trade value
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cost` | float | required | Cost as decimal (0.001 = 0.1%) |

**Example Calculation:**
```
Buy $10,000 of stock at 0.1%:
  $10,000 × 0.001 = $10.00
  Commission = $10.00
```

**Use Cases:**
- ✅ Institutional trading
- ✅ Percentage-based fee structures
- ✅ Crypto exchanges (maker/taker fees)

**Example:**
```python
def initialize(context):
    set_commission(
        us_equities=commission.PerDollar(cost=0.001)  # 0.1%
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_dollar: 0.001  # 0.1% of trade value
```

---

### NoCommission

No commission (unrealistic for production backtests).

**API:**
```python
from zipline.finance import commission

commission.NoCommission()
```

**Use Cases:**
- ⚠️ Testing only (not recommended for production)
- ⚠️ Comparing strategy performance with/without costs
- ❌ Not recommended for realistic backtests

**Example:**
```python
def initialize(context):
    set_commission(us_equities=commission.NoCommission())
```

---

## Slippage Models

### set_slippage()

Configure slippage model for backtest execution.

**Zipline-Reloaded API:**
```python
from zipline.api import set_slippage

set_slippage(us_equities=None, us_futures=None)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `us_equities` | SlippageModel | Slippage model for equities (or None) |
| `us_futures` | SlippageModel | Slippage model for futures (or None) |

**When to Call:**
- Must be called in `initialize()` function
- Called once at backtest start
- Applies to all trades during backtest

**Note:** For crypto and forex strategies, use `us_equities` parameter (Zipline-Reloaded uses the same slippage model interface for all asset classes).

---

### VolumeShareSlippage

Price impact based on order size relative to bar volume (recommended).

**API:**
```python
from zipline.finance import slippage

slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `volume_limit` | float | required | Max % of bar volume to fill (0.025 = 2.5%) |
| `price_impact` | float | required | Price impact coefficient |

**How It Works:**

1. **Volume Constraint**: Can only fill up to `volume_limit` × bar_volume per bar
2. **Price Impact**: Execution price is worse than bar price
3. **Multi-Bar Fills**: Large orders split across multiple bars

**Price Impact Formula:**
```
volume_share = filled_shares / bar_volume
price_impact_pct = volume_share × price_impact
execution_price = bar_price × (1 + price_impact_pct)  # for buys
execution_price = bar_price × (1 - price_impact_pct)  # for sells
```

**Example:**
```
Order: Buy 10,000 shares
Bar volume: 100,000 shares
volume_limit: 0.025 (2.5%)
price_impact: 0.1

Max fillable per bar = 100,000 × 0.025 = 2,500 shares
Remaining 7,500 shares carry to next bar

Volume share = 2,500 / 100,000 = 0.025
Price impact = 0.025 × 0.1 = 0.0025 (0.25%)

If bar_price = $100:
  Execution = $100 × 1.0025 = $100.25 per share
  Total cost = 2,500 × $100.25 = $250,625
```

**Use Cases:**
- ✅ Most realistic slippage model
- ✅ Accounts for market impact
- ✅ Handles large orders across multiple bars
- ✅ Recommended for most strategies

**Example:**
```python
def initialize(context):
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=0.025,   # 2.5% of bar volume
            price_impact=0.1      # 10% impact coefficient
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  slippage:
    volume_limit: 0.025
    price_impact: 0.1
```

---

### FixedSlippage

Fixed spread per share (simpler model).

**API:**
```python
from zipline.finance import slippage

slippage.FixedSlippage(spread=0.01)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `spread` | float | required | Fixed spread per share |

**How It Works:**
```
Buy: execution_price = bar_price + spread/2
Sell: execution_price = bar_price - spread/2
```

**Example:**
```
Bar price: $100.00
Spread: $0.01

Buy execution: $100.00 + $0.005 = $100.005
Sell execution: $100.00 - $0.005 = $99.995
```

**Use Cases:**
- ✅ Simple strategies with small positions
- ✅ High-liquidity assets (tight spreads)
- ✅ When volume data is unavailable

**Example:**
```python
def initialize(context):
    set_slippage(
        us_equities=slippage.FixedSlippage(spread=0.01)
    )
```

**parameters.yaml:**
```yaml
costs:
  slippage:
    fixed_spread: 0.01
```

**Note:** Strategy template uses `volume_limit` and `price_impact`. For `FixedSlippage`, add custom logic or modify template.

---

### FixedBasisPointsSlippage

Slippage as basis points of price.

**API:**
```python
from zipline.finance import slippage

slippage.FixedBasisPointsSlippage(basis_points=5.0, volume_limit=0.1)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `basis_points` | float | required | Slippage in bps (5.0 = 0.05%) |
| `volume_limit` | float | 1.0 | Max % of volume to fill |

**Example Calculation:**
```
Bar price: $100.00
Basis points: 5.0 (0.05%)

Buy execution: $100.00 × 1.0005 = $100.05
Sell execution: $100.00 × 0.9995 = $99.95
```

**Use Cases:**
- ✅ Institutional trading
- ✅ Percentage-based slippage models
- ✅ High-frequency strategies

**Example:**
```python
def initialize(context):
    set_slippage(
        us_equities=slippage.FixedBasisPointsSlippage(
            basis_points=5.0,      # 0.05%
            volume_limit=0.1       # 10% of volume
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  slippage:
    basis_points: 5.0
    volume_limit: 0.1
```

**Note:** Strategy template uses `volume_limit` and `price_impact`. For `FixedBasisPointsSlippage`, add custom logic or modify template.

---

### NoSlippage

Fill at exact bar price (unrealistic for production backtests).

**API:**
```python
from zipline.finance import slippage

slippage.NoSlippage()
```

**Use Cases:**
- ⚠️ Testing only (not recommended for production)
- ⚠️ Comparing strategy performance with/without slippage
- ❌ Not recommended for realistic backtests

**Example:**
```python
def initialize(context):
    set_slippage(us_equities=slippage.NoSlippage())
```

---

## Asset Class Configurations

### Equities (US Stocks)

**Recommended Configuration:**
```python
def initialize(context):
    # Interactive Brokers style
    set_commission(
        us_equities=commission.PerShare(
            cost=0.005,
            min_trade_cost=1.0
        )
    )
    
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=0.025,  # 2.5% of volume
            price_impact=0.1     # 10% impact
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_share: 0.005
    min_cost: 1.0
  slippage:
    volume_limit: 0.025
    price_impact: 0.1
```

---

### Crypto

**Recommended Configuration:**
```python
def initialize(context):
    # Exchange maker/taker fees (0.1% typical)
    set_commission(
        us_equities=commission.PerDollar(cost=0.001)  # 0.1%
    )
    
    # Crypto markets are very liquid, lower slippage
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=0.05,   # 5% of volume (higher liquidity)
            price_impact=0.05    # 5% impact (lower than equities)
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_dollar: 0.001  # 0.1% exchange fee
  slippage:
    volume_limit: 0.05
    price_impact: 0.05
```

**Note:** Crypto exchanges typically charge maker/taker fees as percentage of trade value, not per-share.

---

### Forex

**Recommended Configuration:**
```python
def initialize(context):
    # Forex spreads are typically built into slippage
    # Commission is usually zero or very low
    set_commission(
        us_equities=commission.PerDollar(cost=0.0001)  # 0.01% (very low)
    )
    
    # Forex spreads vary by pair (major pairs have tighter spreads)
    set_slippage(
        us_equities=slippage.FixedBasisPointsSlippage(
            basis_points=2.0,     # 0.02% (2 pips for major pairs)
            volume_limit=0.1      # 10% of volume
        )
    )
```

**parameters.yaml:**
```yaml
costs:
  commission:
    per_dollar: 0.0001  # 0.01% (very low)
  slippage:
    basis_points: 2.0   # 0.02% (2 pips)
    volume_limit: 0.1
```

**Note:** Forex costs are primarily spread-based. Consider using `FixedBasisPointsSlippage` to model typical forex spreads.

---

## Strategy Template Integration

The strategy template (`strategies/_template/strategy.py`) includes transaction cost configuration:

```python
def initialize(context):
    # ... other initialization ...
    
    # Configure commission model
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )
    
    # Configure slippage model
    slippage_config = params.get('costs', {}).get('slippage', {})
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=slippage_config.get('volume_limit', 0.025),
            price_impact=slippage_config.get('price_impact', 0.1)
        )
    )
```

**Template parameters.yaml:**
```yaml
costs:
  commission:
    per_share: 0.005
    min_cost: 1.0
  slippage:
    volume_limit: 0.025
    price_impact: 0.1
```

**Customization:**
- Modify `parameters.yaml` to change cost levels
- Override in `initialize()` for asset-specific logic
- Use different models (PerTrade, FixedSlippage) by modifying strategy code

---

## Cost Impact Analysis

### Analyzing Transaction Costs in Results

Transaction costs are automatically applied during backtest execution. Analyze their impact:

```python
def analyze(context, perf):
    """Analyze transaction costs from backtest results."""
    
    # Total commissions from transactions
    total_commission = 0.0
    for date, txns in perf['transactions'].items():
        for txn in txns:
            total_commission += txn.get('commission', 0.0)
    
    print(f"Total Commission: ${total_commission:,.2f}")
    
    # Slippage impact (difference between order price and execution price)
    total_slippage = 0.0
    for date, txns in perf['transactions'].items():
        for txn in txns:
            if 'price' in txn and 'last_price' in txn:
                slippage_cost = abs(txn['price'] - txn['last_price']) * abs(txn['amount'])
                total_slippage += slippage_cost
    
    print(f"Total Slippage: ${total_slippage:,.2f}")
    
    # Total transaction costs
    total_costs = total_commission + total_slippage
    print(f"Total Transaction Costs: ${total_costs:,.2f}")
    
    # As percentage of final portfolio value
    final_value = perf['portfolio_value'].iloc[-1]
    cost_pct = (total_costs / final_value) * 100
    print(f"Transaction Costs: {cost_pct:.2f}% of final portfolio value")
```

---

## Best Practices

### 1. Always Configure Realistic Costs

```python
# ✅ GOOD - Realistic costs
def initialize(context):
    set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0))
    set_slippage(us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))

# ❌ BAD - No costs (unrealistic)
def initialize(context):
    set_commission(us_equities=commission.NoCommission())
    set_slippage(us_equities=slippage.NoSlippage())
```

### 2. Use parameters.yaml for Configuration

```python
# ✅ GOOD - Load from YAML
def initialize(context):
    params = context.params
    commission_config = params.get('costs', {}).get('commission', {})
    set_commission(
        us_equities=commission.PerShare(
            cost=commission_config.get('per_share', 0.005),
            min_trade_cost=commission_config.get('min_cost', 1.0)
        )
    )

# ❌ BAD - Hardcoded values
def initialize(context):
    set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0))
```

### 3. Test Cost Sensitivity

```python
# Test strategy with different cost levels
cost_levels = [
    {'per_share': 0.0, 'volume_limit': 1.0},      # No costs
    {'per_share': 0.005, 'volume_limit': 0.025},  # Standard
    {'per_share': 0.01, 'volume_limit': 0.01},    # High costs
]

for costs in cost_levels:
    # Run backtest with different cost configuration
    # Compare results to understand cost sensitivity
    pass
```

### 4. Document Cost Assumptions

```python
def initialize(context):
    """
    Transaction Cost Assumptions:
    - Commission: Interactive Brokers tiered pricing ($0.005/share, $1 min)
    - Slippage: VolumeShareSlippage (2.5% volume limit, 10% impact)
    - Assumes liquid assets with average daily volume > 1M shares
    """
    # ... cost configuration ...
```

### 5. Asset-Specific Configurations

```python
def initialize(context):
    asset_class = context.params.get('strategy', {}).get('asset_class', 'equities')
    
    if asset_class == 'crypto':
        # Crypto: percentage-based fees
        set_commission(us_equities=commission.PerDollar(cost=0.001))
        set_slippage(us_equities=slippage.VolumeShareSlippage(volume_limit=0.05, price_impact=0.05))
    elif asset_class == 'forex':
        # Forex: spread-based
        set_commission(us_equities=commission.PerDollar(cost=0.0001))
        set_slippage(us_equities=slippage.FixedBasisPointsSlippage(basis_points=2.0))
    else:
        # Equities: per-share commission
        set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0))
        set_slippage(us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
```

---

## Common Configurations

### Retail Broker (Interactive Brokers Style)

```python
def initialize(context):
    set_commission(
        us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0)
    )
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1)
    )
```

### Discount Broker (Free Trading)

```python
def initialize(context):
    set_commission(us_equities=commission.NoCommission())
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1)
    )
```

**Note:** Even "free" brokers have slippage. Don't use `NoSlippage()`.

### Institutional

```python
def initialize(context):
    set_commission(
        us_equities=commission.PerDollar(cost=0.0005)  # 5 basis points
    )
    set_slippage(
        us_equities=slippage.VolumeShareSlippage(
            volume_limit=0.1,      # Can access more volume
            price_impact=0.05      # Lower impact per share
        )
    )
```

### High-Frequency Trading

```python
def initialize(context):
    set_commission(
        us_equities=commission.PerDollar(cost=0.0001)  # 1 basis point
    )
    set_slippage(
        us_equities=slippage.FixedBasisPointsSlippage(
            basis_points=1.0,     # 0.01% slippage
            volume_limit=0.01      # Very liquid stocks only
        )
    )
```

---

## Troubleshooting

### Costs Not Applied

**Problem:** Transaction costs don't appear in results.

**Solution:**
- Ensure `set_commission()` and `set_slippage()` are called in `initialize()`
- Check that models are properly instantiated (e.g., `commission.PerShare(...)`)
- Verify parameters are loaded from `parameters.yaml` correctly

### Costs Too High/Low

**Problem:** Transaction costs seem unrealistic.

**Solution:**
- Review cost assumptions for your asset class
- Check `parameters.yaml` values match your broker/exchange
- Test with different cost levels to understand sensitivity
- Consider asset-specific configurations

### Large Orders Not Filling

**Problem:** Orders take multiple bars to fill.

**Solution:**
- This is expected with `VolumeShareSlippage` and `volume_limit < 1.0`
- Large orders are split across multiple bars automatically
- Increase `volume_limit` if you need faster fills (less realistic)
- Consider if your strategy size is appropriate for asset liquidity

---

## See Also

- [Risk Management Guide](../code_patterns/risk_management_guide.md) - When to use transaction costs vs other risk controls
- [Risk Management API](risk_management.md) - Strategy-level exit conditions (stop loss, take profit)
- [Strategy Template](../../strategies/_template/strategy.py) - Complete strategy example with cost configuration
- [Zipline-Reloaded Documentation](https://github.com/stefan-jansen/zipline-reloaded) - Official Zipline-Reloaded docs

---

## References

**Zipline-Reloaded Source:**
- Commission models: `zipline.finance.commission`
- Slippage models: `zipline.finance.slippage`
- API functions: `zipline.api.set_commission()`, `zipline.api.set_slippage()`

**Project Integration:**
- Strategy template: `strategies/_template/strategy.py` (lines 319-335)
- Parameters: `strategies/_template/parameters.yaml` (lines 126-133)
- Risk management guide: `docs/code_patterns/risk_management_guide.md` (section 6)
