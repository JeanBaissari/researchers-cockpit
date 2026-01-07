---
name: zrl-rebalancer
description: This skill should be used when implementing portfolio rebalancing in Zipline strategies. It provides calendar-based, threshold-based, and drift-based rebalancing with efficient order generation and turnover constraints.
---

# Zipline Portfolio Rebalancer

Professional portfolio rebalancing with configurable triggers and constraints.

## Purpose

Automate portfolio rebalancing decisions. Minimize unnecessary turnover while maintaining target allocations. Handle complex rebalancing schedules and drift tolerances.

## When to Use

- Implementing periodic rebalancing strategies
- Managing allocation drift tolerances
- Minimizing transaction costs from rebalancing
- Building smart beta or index-tracking strategies

## Rebalancing Triggers

| Type | Trigger | Best For |
|------|---------|----------|
| Calendar | Fixed schedule | Systematic strategies |
| Threshold | Weight deviation | Drift control |
| Volatility | Vol-adjusted bands | Risk management |
| Hybrid | Multiple conditions | Sophisticated strategies |

## Core Implementation

### Rebalancing Configuration

```python
# scripts/rebalancer/config.py

from dataclasses import dataclass
from typing import Dict, Optional, Callable
from enum import Enum

class RebalanceFrequency(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'

@dataclass
class RebalanceConfig:
    """Rebalancing configuration."""
    
    # Calendar-based
    frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    day_offset: int = 0  # Days after period start
    
    # Threshold-based
    drift_threshold: float = 0.05  # 5% absolute drift
    relative_threshold: float = 0.20  # 20% relative drift
    
    # Constraints
    min_trade_value: float = 1000  # Minimum trade size
    max_turnover: float = 0.25  # Max single-day turnover
    
    # Execution timing
    execution_time: str = 'open'  # 'open' or 'close'
    execution_minutes: int = 30  # Minutes after open
```

### Drift Calculator

```python
# scripts/rebalancer/drift.py

import pandas as pd
import numpy as np
from typing import Dict

class DriftCalculator:
    """Calculate portfolio drift from targets."""
    
    def __init__(self, target_weights: Dict['Asset', float]):
        self.target_weights = target_weights
        self._normalize_targets()
    
    def _normalize_targets(self):
        """Ensure targets sum to 1."""
        total = sum(self.target_weights.values())
        if total > 0:
            self.target_weights = {
                k: v / total for k, v in self.target_weights.items()
            }
    
    def calculate_current_weights(self, portfolio) -> Dict['Asset', float]:
        """Get current portfolio weights."""
        total_value = portfolio.portfolio_value
        if total_value <= 0:
            return {}
        
        weights = {}
        for asset, position in portfolio.positions.items():
            weights[asset] = (position.amount * position.last_sale_price) / total_value
        
        # Include cash
        weights['cash'] = portfolio.cash / total_value
        return weights
    
    def calculate_drift(self, portfolio) -> Dict['Asset', float]:
        """Calculate absolute drift per asset."""
        current = self.calculate_current_weights(portfolio)
        drift = {}
        
        for asset, target in self.target_weights.items():
            current_weight = current.get(asset, 0.0)
            drift[asset] = current_weight - target
        
        return drift
    
    def max_absolute_drift(self, portfolio) -> float:
        """Maximum absolute drift across assets."""
        drift = self.calculate_drift(portfolio)
        return max(abs(d) for d in drift.values()) if drift else 0.0
    
    def max_relative_drift(self, portfolio) -> float:
        """Maximum relative drift (drift / target)."""
        drift = self.calculate_drift(portfolio)
        max_rel = 0.0
        
        for asset, d in drift.items():
            target = self.target_weights.get(asset, 0)
            if target > 0:
                max_rel = max(max_rel, abs(d) / target)
        
        return max_rel
    
    def needs_rebalance(self, portfolio, config: RebalanceConfig) -> bool:
        """Check if rebalancing is needed based on drift."""
        abs_drift = self.max_absolute_drift(portfolio)
        rel_drift = self.max_relative_drift(portfolio)
        
        return (abs_drift > config.drift_threshold or 
                rel_drift > config.relative_threshold)
```

### Rebalance Scheduler

```python
# scripts/rebalancer/scheduler.py

from zipline.api import schedule_function, date_rules, time_rules

class RebalanceScheduler:
    """Schedule rebalancing based on configuration."""
    
    def __init__(self, config: RebalanceConfig):
        self.config = config
    
    def get_date_rule(self):
        """Get appropriate date rule."""
        freq = self.config.frequency
        offset = self.config.day_offset
        
        if freq == RebalanceFrequency.DAILY:
            return date_rules.every_day()
        elif freq == RebalanceFrequency.WEEKLY:
            return date_rules.week_start(days_offset=offset)
        elif freq == RebalanceFrequency.MONTHLY:
            return date_rules.month_start(days_offset=offset)
        elif freq == RebalanceFrequency.QUARTERLY:
            # Quarterly = every 3 months
            return date_rules.month_start(days_offset=offset)
    
    def get_time_rule(self):
        """Get appropriate time rule."""
        if self.config.execution_time == 'open':
            return time_rules.market_open(minutes=self.config.execution_minutes)
        else:
            return time_rules.market_close(minutes=self.config.execution_minutes)
    
    def schedule(self, func):
        """Schedule the rebalancing function."""
        schedule_function(
            func,
            date_rule=self.get_date_rule(),
            time_rule=self.get_time_rule()
        )
```

### Order Generator

```python
# scripts/rebalancer/orders.py

from typing import Dict, List, Tuple
from zipline.api import order_target_percent, get_open_orders

@dataclass
class RebalanceOrder:
    """Single rebalancing order."""
    asset: 'Asset'
    target_weight: float
    current_weight: float
    trade_value: float
    direction: str  # 'buy' or 'sell'

class OrderGenerator:
    """Generate rebalancing orders with constraints."""
    
    def __init__(self, config: RebalanceConfig):
        self.config = config
    
    def generate_orders(self, portfolio, target_weights: Dict['Asset', float],
                       data) -> List[RebalanceOrder]:
        """Generate constrained rebalancing orders."""
        total_value = portfolio.portfolio_value
        current_weights = self._get_current_weights(portfolio)
        
        orders = []
        total_turnover = 0.0
        
        # Calculate all trades needed
        trades = []
        for asset, target in target_weights.items():
            current = current_weights.get(asset, 0.0)
            diff = target - current
            trade_value = abs(diff) * total_value
            
            if trade_value >= self.config.min_trade_value:
                trades.append({
                    'asset': asset,
                    'target': target,
                    'current': current,
                    'diff': diff,
                    'value': trade_value,
                    'direction': 'buy' if diff > 0 else 'sell'
                })
        
        # Sort: sells first (generate cash), then buys
        sells = [t for t in trades if t['direction'] == 'sell']
        buys = [t for t in trades if t['direction'] == 'buy']
        sorted_trades = sells + buys
        
        # Apply turnover constraint
        for trade in sorted_trades:
            turnover = trade['value'] / total_value
            if total_turnover + turnover > self.config.max_turnover:
                # Partial trade
                remaining = self.config.max_turnover - total_turnover
                if remaining > 0:
                    trade['value'] *= remaining / turnover
                    trade['diff'] *= remaining / turnover
                    total_turnover = self.config.max_turnover
                else:
                    continue
            else:
                total_turnover += turnover
            
            orders.append(RebalanceOrder(
                asset=trade['asset'],
                target_weight=trade['target'],
                current_weight=trade['current'],
                trade_value=trade['value'],
                direction=trade['direction']
            ))
        
        return orders
    
    def _get_current_weights(self, portfolio) -> Dict['Asset', float]:
        """Calculate current weights."""
        total = portfolio.portfolio_value
        if total <= 0:
            return {}
        
        return {
            asset: (pos.amount * pos.last_sale_price) / total
            for asset, pos in portfolio.positions.items()
        }
    
    def execute_orders(self, orders: List[RebalanceOrder], data):
        """Execute rebalancing orders."""
        for order in orders:
            if data.can_trade(order.asset):
                # Check no pending orders
                if not get_open_orders(order.asset):
                    order_target_percent(order.asset, order.target_weight)
```

## Complete Rebalancer

```python
# scripts/rebalancer/rebalancer.py

class PortfolioRebalancer:
    """Complete rebalancing solution."""
    
    def __init__(self, target_weights: Dict['Asset', float],
                 config: RebalanceConfig = None):
        self.target_weights = target_weights
        self.config = config or RebalanceConfig()
        self.drift_calc = DriftCalculator(target_weights)
        self.order_gen = OrderGenerator(self.config)
        self.scheduler = RebalanceScheduler(self.config)
        self.last_rebalance = None
    
    def check_and_rebalance(self, context, data):
        """Check drift and rebalance if needed."""
        portfolio = context.portfolio
        
        # Always rebalance on schedule (calendar-based)
        # Or check drift threshold
        if self.drift_calc.needs_rebalance(portfolio, self.config):
            self.rebalance(context, data)
    
    def rebalance(self, context, data):
        """Execute rebalancing."""
        orders = self.order_gen.generate_orders(
            context.portfolio, 
            self.target_weights,
            data
        )
        
        self.order_gen.execute_orders(orders, data)
        self.last_rebalance = get_datetime()
        
        # Log rebalancing
        log.info(f"Rebalanced {len(orders)} positions")
    
    def update_targets(self, new_weights: Dict['Asset', float]):
        """Update target weights."""
        self.target_weights = new_weights
        self.drift_calc = DriftCalculator(new_weights)
```

## Usage Pattern

```python
from zipline.api import symbols
from rebalancer import PortfolioRebalancer, RebalanceConfig, RebalanceFrequency

def initialize(context):
    assets = symbols('SPY', 'TLT', 'GLD', 'VNQ')
    
    # 60/40/10/10 portfolio
    targets = {
        assets[0]: 0.60,  # SPY
        assets[1]: 0.25,  # TLT
        assets[2]: 0.10,  # GLD
        assets[3]: 0.05,  # VNQ
    }
    
    config = RebalanceConfig(
        frequency=RebalanceFrequency.MONTHLY,
        day_offset=0,
        drift_threshold=0.05,
        max_turnover=0.20
    )
    
    context.rebalancer = PortfolioRebalancer(targets, config)
    context.rebalancer.scheduler.schedule(rebalance)

def rebalance(context, data):
    context.rebalancer.rebalance(context, data)

def handle_data(context, data):
    # Optional: check drift between scheduled rebalances
    context.rebalancer.check_and_rebalance(context, data)
```

## Script Reference

### analyze_turnover.py

Analyze historical turnover:

```bash
python scripts/analyze_turnover.py results.csv --threshold 0.05
```

### optimize_frequency.py

Find optimal rebalancing frequency:

```bash
python scripts/optimize_frequency.py --strategies daily weekly monthly
```

## Best Practices

1. **Set minimum trade sizes** to avoid tiny orders
2. **Use turnover constraints** to control costs
3. **Prioritize sells before buys** for cash management
4. **Check for open orders** before placing new ones
5. **Log all rebalancing** for analysis
