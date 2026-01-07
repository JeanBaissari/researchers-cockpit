---
name: zrl-risk-controls
description: This skill should be used when implementing risk management and trading controls for Zipline strategies. It provides patterns for drawdown limits, position limits, exposure controls, stop-losses, and circuit breakers.
---

# Zipline Risk Controls

Implement comprehensive risk management for trading strategies.

## Purpose

Protect capital through systematic risk controls including drawdown limits, position constraints, exposure management, and automated circuit breakers.

## When to Use

- Implementing position and portfolio limits
- Building stop-loss mechanisms
- Creating drawdown-based circuit breakers
- Managing leverage and exposure
- Enforcing trading rules

## Risk Control Architecture

```
Order Intent → Pre-Trade Checks → Position Limits → Exposure Limits → Execute
                                                                        ↓
Portfolio State ← Post-Trade Update ← Risk Metrics ← Filled Order ←────┘
```

## Zipline Built-in Controls

### Position Limits

```python
from zipline.api import set_max_position_size, set_max_order_size

def initialize(context):
    # Max 1000 shares or $100k per position
    set_max_position_size(
        max_shares=1000,
        max_notional=100000
    )
    
    # Max 500 shares per order
    set_max_order_size(
        max_shares=500,
        max_notional=50000
    )
```

### Order Limits

```python
from zipline.api import set_max_order_count

def initialize(context):
    # Max 50 orders per day
    set_max_order_count(50)
```

### Leverage Control

```python
from zipline.api import set_max_leverage, set_long_only

def initialize(context):
    # No leverage
    set_max_leverage(1.0)
    
    # Prevent short selling
    set_long_only()
```

### Restricted List

```python
from zipline.api import set_do_not_order_list

def initialize(context):
    restricted = [symbol('PENNY'), symbol('RISKY')]
    set_do_not_order_list(restricted)
```

## Custom Risk Manager

### RiskManager Class

```python
class RiskManager:
    """Comprehensive risk management."""
    
    def __init__(self, config):
        self.config = config
        self.peak_value = 0
        self.daily_pnl = 0
        self.trade_count = 0
        self.circuit_breaker_active = False
    
    def pre_trade_check(self, asset, amount, context, data) -> bool:
        """Check if trade is allowed."""
        if self.circuit_breaker_active:
            return False
        
        # Position size check
        if not self._check_position_size(asset, amount, context, data):
            return False
        
        # Exposure check
        if not self._check_exposure(asset, amount, context):
            return False
        
        # Concentration check
        if not self._check_concentration(asset, amount, context, data):
            return False
        
        return True
    
    def _check_position_size(self, asset, amount, context, data) -> bool:
        price = data.current(asset, 'price')
        value = abs(amount * price)
        max_value = context.portfolio.portfolio_value * self.config.max_position_size
        return value <= max_value
    
    def _check_exposure(self, asset, amount, context) -> bool:
        current_exposure = sum(
            abs(pos.amount * pos.last_sale_price) 
            for pos in context.portfolio.positions.values()
        )
        new_exposure = current_exposure + abs(amount * data.current(asset, 'price'))
        max_exposure = context.portfolio.portfolio_value * self.config.max_gross_exposure
        return new_exposure <= max_exposure
    
    def _check_concentration(self, asset, amount, context, data) -> bool:
        # Check sector concentration if applicable
        return True
    
    def update_metrics(self, context):
        """Update risk metrics after each bar."""
        pv = context.portfolio.portfolio_value
        
        # Track peak value for drawdown
        self.peak_value = max(self.peak_value, pv)
        
        # Calculate current drawdown
        self.current_drawdown = (self.peak_value - pv) / self.peak_value
        
        # Check circuit breaker conditions
        self._check_circuit_breaker(context)
    
    def _check_circuit_breaker(self, context):
        """Activate circuit breaker if conditions met."""
        # Drawdown limit
        if self.current_drawdown >= self.config.max_drawdown:
            self.circuit_breaker_active = True
            log.warning(f"Circuit breaker: drawdown {self.current_drawdown:.1%}")
        
        # Daily loss limit
        if self.daily_pnl <= -self.config.daily_loss_limit:
            self.circuit_breaker_active = True
            log.warning(f"Circuit breaker: daily loss {self.daily_pnl:,.0f}")
    
    def reset_daily(self):
        """Reset daily metrics."""
        self.daily_pnl = 0
        self.trade_count = 0
```

## Stop-Loss Implementation

### Position-Level Stop-Loss

```python
class StopLossManager:
    """Manage stop-losses for positions."""
    
    def __init__(self, stop_pct: float = 0.05, trailing: bool = False):
        self.stop_pct = stop_pct
        self.trailing = trailing
        self.entry_prices = {}
        self.high_water_marks = {}
    
    def record_entry(self, asset, price):
        """Record position entry."""
        self.entry_prices[asset] = price
        self.high_water_marks[asset] = price
    
    def update_high_water(self, asset, current_price):
        """Update high water mark for trailing stops."""
        if asset in self.high_water_marks:
            self.high_water_marks[asset] = max(
                self.high_water_marks[asset], 
                current_price
            )
    
    def check_stop(self, asset, current_price) -> bool:
        """Check if stop-loss triggered."""
        if asset not in self.entry_prices:
            return False
        
        if self.trailing:
            reference = self.high_water_marks.get(asset, self.entry_prices[asset])
        else:
            reference = self.entry_prices[asset]
        
        loss_pct = (reference - current_price) / reference
        return loss_pct >= self.stop_pct
    
    def process_stops(self, context, data):
        """Check all positions for stop-loss triggers."""
        to_exit = []
        
        for asset in context.portfolio.positions:
            current_price = data.current(asset, 'price')
            self.update_high_water(asset, current_price)
            
            if self.check_stop(asset, current_price):
                to_exit.append(asset)
        
        for asset in to_exit:
            order_target(asset, 0)
            self._cleanup(asset)
        
        return to_exit
    
    def _cleanup(self, asset):
        """Clean up tracking after exit."""
        self.entry_prices.pop(asset, None)
        self.high_water_marks.pop(asset, None)
```

## Drawdown Protection

### Drawdown Monitor

```python
class DrawdownMonitor:
    """Monitor and act on drawdowns."""
    
    def __init__(self, 
                 reduce_at: float = 0.10,  # Reduce at 10% DD
                 halt_at: float = 0.20,    # Halt at 20% DD
                 recovery_pct: float = 0.50):  # Resume at 50% recovery
        self.reduce_at = reduce_at
        self.halt_at = halt_at
        self.recovery_pct = recovery_pct
        self.peak_value = 0
        self.halted = False
        self.reduced = False
    
    def update(self, portfolio_value: float) -> str:
        """Update and return status."""
        self.peak_value = max(self.peak_value, portfolio_value)
        drawdown = (self.peak_value - portfolio_value) / self.peak_value
        
        if drawdown >= self.halt_at:
            self.halted = True
            return 'HALT'
        elif drawdown >= self.reduce_at:
            self.reduced = True
            return 'REDUCE'
        elif self.halted and drawdown < self.halt_at * self.recovery_pct:
            self.halted = False
            return 'RESUME'
        
        return 'NORMAL'
    
    def get_scale_factor(self) -> float:
        """Get position scaling factor based on drawdown state."""
        if self.halted:
            return 0.0
        elif self.reduced:
            return 0.5
        return 1.0
```

## Integration Example

```python
def initialize(context):
    # Built-in controls
    set_max_leverage(1.0)
    set_max_position_size(max_shares=5000, max_notional=100000)
    
    # Custom risk manager
    context.risk = RiskManager(context.config)
    context.stops = StopLossManager(stop_pct=0.05, trailing=True)
    context.drawdown = DrawdownMonitor(reduce_at=0.10, halt_at=0.20)
    
    schedule_function(check_risk, date_rules.every_day(), 
                     time_rules.market_close(minutes=30))

def handle_data(context, data):
    # Update risk metrics
    context.risk.update_metrics(context)
    
    # Check stop-losses
    context.stops.process_stops(context, data)
    
    # Update drawdown monitor
    status = context.drawdown.update(context.portfolio.portfolio_value)
    
    if status == 'HALT':
        liquidate_all(context, data)

def rebalance(context, data):
    # Get target weights from signal
    raw_weights = get_signal_weights(context, data)
    
    # Apply drawdown scaling
    scale = context.drawdown.get_scale_factor()
    scaled_weights = {k: v * scale for k, v in raw_weights.items()}
    
    # Execute with risk checks
    for asset, weight in scaled_weights.items():
        if context.risk.pre_trade_check(asset, weight, context, data):
            order_target_percent(asset, weight)
```

## Script Reference

### risk_report.py

Generate risk analysis report:

```bash
python scripts/risk_report.py \
    --backtest results.csv \
    --output risk_report.html
```

## References

See `references/risk_metrics.md` for metric definitions.
See `references/circuit_breaker_rules.md` for breaker configurations.
