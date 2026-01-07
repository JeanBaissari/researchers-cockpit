---
name: zrl-execution-models
description: This skill should be used when implementing execution algorithms for Zipline strategies. It provides TWAP, VWAP, POV, and adaptive execution models that slice large orders into smaller pieces to minimize market impact.
---

# Zipline Execution Models

Smart order execution algorithms for professional trading simulation.

## Purpose

Simulate realistic execution of large orders. Slice orders over time to reduce market impact. Provide execution benchmarks for performance analysis.

## When to Use

- Executing large orders that would impact price
- Simulating institutional-style trading
- Benchmarking execution quality
- Testing execution algorithm behavior

## Execution Algorithm Types

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| TWAP | Time-weighted slicing | Low urgency, uniform volume |
| VWAP | Volume-weighted slicing | Matching market volume pattern |
| POV | Participate in volume | Tracking market activity |
| Adaptive | Dynamic adjustment | Varying market conditions |
| IS | Implementation shortfall | Minimizing total cost |

## Core Implementation

### Base Executor

```python
# scripts/executors/base.py

from dataclasses import dataclass
from typing import Optional, List
import pandas as pd

@dataclass
class ExecutionSlice:
    """Single execution slice."""
    time: pd.Timestamp
    shares: int
    price_limit: Optional[float] = None
    urgency: float = 0.5

@dataclass
class ExecutionPlan:
    """Complete execution schedule."""
    asset: 'Asset'
    total_shares: int
    slices: List[ExecutionSlice]
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    
    @property
    def filled_shares(self) -> int:
        return sum(s.shares for s in self.slices)
    
    @property
    def completion_pct(self) -> float:
        return self.filled_shares / self.total_shares if self.total_shares else 0

class BaseExecutor:
    """Base class for execution algorithms."""
    
    def __init__(self, data, asset, total_shares: int, 
                 start_time: pd.Timestamp, end_time: pd.Timestamp):
        self.data = data
        self.asset = asset
        self.total_shares = total_shares
        self.start_time = start_time
        self.end_time = end_time
        self.executed_shares = 0
        self.slices = []
    
    def generate_schedule(self) -> ExecutionPlan:
        """Generate execution slices. Override in subclass."""
        raise NotImplementedError
    
    def get_next_slice(self, current_time: pd.Timestamp) -> Optional[ExecutionSlice]:
        """Get next slice to execute at current time."""
        for s in self.slices:
            if s.time <= current_time and s.shares > 0:
                return s
        return None
    
    def mark_executed(self, slice_: ExecutionSlice, filled: int):
        """Record execution."""
        self.executed_shares += filled
        slice_.shares -= filled
```

### TWAP Executor

```python
# scripts/executors/twap.py

class TWAPExecutor(BaseExecutor):
    """Time-Weighted Average Price execution."""
    
    def __init__(self, data, asset, total_shares: int,
                 start_time: pd.Timestamp, end_time: pd.Timestamp,
                 num_slices: int = 10):
        super().__init__(data, asset, total_shares, start_time, end_time)
        self.num_slices = num_slices
    
    def generate_schedule(self) -> ExecutionPlan:
        """Create uniform time-based schedule."""
        duration = (self.end_time - self.start_time).total_seconds()
        interval = duration / self.num_slices
        shares_per_slice = self.total_shares // self.num_slices
        remainder = self.total_shares % self.num_slices
        
        self.slices = []
        for i in range(self.num_slices):
            slice_time = self.start_time + pd.Timedelta(seconds=i * interval)
            shares = shares_per_slice + (1 if i < remainder else 0)
            
            self.slices.append(ExecutionSlice(
                time=slice_time,
                shares=shares,
                urgency=0.5
            ))
        
        return ExecutionPlan(
            asset=self.asset,
            total_shares=self.total_shares,
            slices=self.slices,
            start_time=self.start_time,
            end_time=self.end_time
        )
```

### VWAP Executor

```python
# scripts/executors/vwap.py

import numpy as np

class VWAPExecutor(BaseExecutor):
    """Volume-Weighted Average Price execution."""
    
    def __init__(self, data, asset, total_shares: int,
                 start_time: pd.Timestamp, end_time: pd.Timestamp,
                 lookback_days: int = 20):
        super().__init__(data, asset, total_shares, start_time, end_time)
        self.lookback_days = lookback_days
    
    def generate_schedule(self) -> ExecutionPlan:
        """Create volume-proportional schedule."""
        # Get historical volume profile
        hist_volume = self.data.history(
            self.asset, 'volume', self.lookback_days, '1d'
        )
        
        # For intraday, use minute bars if available
        # Simplified: use uniform intraday profile
        minutes = int((self.end_time - self.start_time).total_seconds() / 60)
        minutes = max(1, minutes)
        
        # Weight by typical volume curve (U-shaped)
        time_pcts = np.linspace(0, 1, minutes)
        volume_weights = 1.5 - np.abs(time_pcts - 0.5)  # Higher at open/close
        volume_weights /= volume_weights.sum()
        
        self.slices = []
        remaining = self.total_shares
        
        for i, weight in enumerate(volume_weights):
            slice_time = self.start_time + pd.Timedelta(minutes=i)
            shares = int(self.total_shares * weight)
            shares = min(shares, remaining)
            remaining -= shares
            
            if shares > 0:
                self.slices.append(ExecutionSlice(
                    time=slice_time,
                    shares=shares,
                    urgency=0.5
                ))
        
        # Add remainder to last slice
        if remaining > 0 and self.slices:
            self.slices[-1].shares += remaining
        
        return ExecutionPlan(
            asset=self.asset,
            total_shares=self.total_shares,
            slices=self.slices,
            start_time=self.start_time,
            end_time=self.end_time
        )
```

### POV Executor

```python
# scripts/executors/pov.py

class POVExecutor(BaseExecutor):
    """Percentage of Volume execution."""
    
    def __init__(self, data, asset, total_shares: int,
                 start_time: pd.Timestamp, end_time: pd.Timestamp,
                 participation_rate: float = 0.1):
        super().__init__(data, asset, total_shares, start_time, end_time)
        self.participation_rate = min(max(participation_rate, 0.01), 0.25)
    
    def get_slice_for_bar(self, bar_volume: int) -> ExecutionSlice:
        """Calculate shares based on current bar volume."""
        remaining = self.total_shares - self.executed_shares
        max_shares = int(bar_volume * self.participation_rate)
        shares = min(max_shares, remaining)
        
        return ExecutionSlice(
            time=pd.Timestamp.now(tz='UTC'),
            shares=shares,
            urgency=0.3
        )
    
    def generate_schedule(self) -> ExecutionPlan:
        """POV generates slices dynamically based on volume."""
        # Initial estimate
        avg_volume = self.data.history(
            self.asset, 'volume', 20, '1d'
        ).mean()
        
        minutes = int((self.end_time - self.start_time).total_seconds() / 60)
        est_bar_volume = avg_volume / 390  # Approximate per-minute
        shares_per_bar = int(est_bar_volume * self.participation_rate)
        
        self.slices = []
        remaining = self.total_shares
        
        for i in range(minutes):
            if remaining <= 0:
                break
            slice_time = self.start_time + pd.Timedelta(minutes=i)
            shares = min(shares_per_bar, remaining)
            remaining -= shares
            
            self.slices.append(ExecutionSlice(
                time=slice_time,
                shares=shares,
                urgency=0.3
            ))
        
        return ExecutionPlan(
            asset=self.asset,
            total_shares=self.total_shares,
            slices=self.slices,
            start_time=self.start_time,
            end_time=self.end_time
        )
```

## Integration with Zipline

```python
# Usage in handle_data

from executors.twap import TWAPExecutor

def initialize(context):
    context.pending_executions = {}

def handle_data(context, data):
    current_time = get_datetime()
    
    # Process pending executions
    for asset, executor in list(context.pending_executions.items()):
        slice_ = executor.get_next_slice(current_time)
        if slice_ and slice_.shares > 0:
            if data.can_trade(asset):
                order_id = order(asset, slice_.shares)
                if order_id:
                    executor.mark_executed(slice_, slice_.shares)
        
        # Remove completed executions
        if executor.executed_shares >= executor.total_shares:
            del context.pending_executions[asset]

def execute_with_twap(context, data, asset, shares, duration_minutes=60):
    """Start TWAP execution."""
    start = get_datetime()
    end = start + pd.Timedelta(minutes=duration_minutes)
    
    executor = TWAPExecutor(data, asset, shares, start, end, num_slices=10)
    executor.generate_schedule()
    context.pending_executions[asset] = executor
```

## Execution Quality Metrics

```python
# scripts/execution_analysis.py

def calculate_execution_metrics(plan: ExecutionPlan, 
                                arrival_price: float,
                                exec_prices: List[float]) -> dict:
    """Analyze execution quality."""
    
    avg_exec_price = sum(exec_prices) / len(exec_prices) if exec_prices else 0
    
    # Implementation shortfall
    is_cost = (avg_exec_price - arrival_price) / arrival_price
    
    # VWAP comparison (if market VWAP available)
    # vwap_slippage = (avg_exec_price - market_vwap) / market_vwap
    
    return {
        'arrival_price': arrival_price,
        'avg_exec_price': avg_exec_price,
        'implementation_shortfall_bps': is_cost * 10000,
        'total_shares': plan.total_shares,
        'num_slices': len(plan.slices),
        'completion_rate': plan.completion_pct,
    }
```

## Script Reference

### simulate_execution.py

Test execution algorithm:

```bash
python scripts/simulate_execution.py --algo twap --shares 10000 --duration 60
```

### compare_algorithms.py

Compare execution algorithms:

```bash
python scripts/compare_algorithms.py --asset AAPL --shares 50000
```

## Best Practices

1. **Match algorithm to order profile**: TWAP for patient, VWAP for volume-tracking
2. **Set realistic participation rates**: 5-15% typical
3. **Monitor execution quality**: Track slippage vs benchmark
4. **Handle partial fills**: Carry forward unfilled shares
5. **Respect volume limits**: Never exceed 25% of bar volume
