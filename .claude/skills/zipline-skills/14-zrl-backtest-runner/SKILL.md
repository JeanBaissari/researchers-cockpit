---
name: zrl-backtest-runner
description: This skill should be used when executing Zipline backtests programmatically. It provides configuration management, automated execution, result persistence, and batch processing for running multiple backtests efficiently.
---

# Zipline Backtest Runner

Automated backtest execution with configuration management and result persistence.

## Purpose

Standardize backtest execution workflows. Enable batch processing of multiple parameter sets. Persist and compare backtest results systematically.

## When to Use

- Running backtests from command line or scripts
- Batch testing multiple configurations
- Persisting results for later analysis
- Comparing strategy variations

## Configuration System

### Backtest Configuration

```python
# scripts/runner/config.py

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import pandas as pd
import yaml
import json

@dataclass
class BacktestConfig:
    """Complete backtest configuration."""
    
    # Required
    strategy_module: str
    bundle: str
    start_date: str
    end_date: str
    capital_base: float
    
    # Optional
    data_frequency: str = 'daily'
    benchmark_symbol: Optional[str] = None
    trading_calendar: str = 'NYSE'
    
    # Strategy parameters
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    # Execution
    live_start_date: Optional[str] = None
    
    # Output
    output_dir: str = './results'
    save_transactions: bool = True
    save_positions: bool = True
    
    @classmethod
    def from_yaml(cls, path: str) -> 'BacktestConfig':
        """Load from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BacktestConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'strategy_module': self.strategy_module,
            'bundle': self.bundle,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'capital_base': self.capital_base,
            'data_frequency': self.data_frequency,
            'benchmark_symbol': self.benchmark_symbol,
            'trading_calendar': self.trading_calendar,
            'strategy_params': self.strategy_params,
            'output_dir': self.output_dir,
        }
    
    def save_yaml(self, path: str):
        """Save to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
```

### Sample Config YAML

```yaml
# config/momentum_strategy.yaml

strategy_module: strategies.momentum
bundle: quandl
start_date: "2018-01-01"
end_date: "2023-12-31"
capital_base: 100000

data_frequency: daily
benchmark_symbol: SPY
trading_calendar: NYSE

strategy_params:
  lookback_period: 60
  num_positions: 10
  rebalance_frequency: monthly

output_dir: ./results/momentum
save_transactions: true
save_positions: true
```

## Backtest Runner

```python
# scripts/runner/runner.py

import importlib
import pandas as pd
from zipline import run_algorithm
from zipline.api import symbol
from typing import Optional
import os
import json
from datetime import datetime

class BacktestRunner:
    """Execute backtests with configuration."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.results = None
        self.run_id = None
    
    def run(self) -> pd.DataFrame:
        """Execute the backtest."""
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Import strategy module
        module = importlib.import_module(self.config.strategy_module)
        
        # Get algorithm functions
        initialize = getattr(module, 'initialize')
        handle_data = getattr(module, 'handle_data', None)
        before_trading_start = getattr(module, 'before_trading_start', None)
        analyze = getattr(module, 'analyze', None)
        
        # Wrap initialize to inject parameters
        original_init = initialize
        strategy_params = self.config.strategy_params
        
        def wrapped_initialize(context):
            context.strategy_params = strategy_params
            original_init(context)
        
        # Parse dates
        start = pd.Timestamp(self.config.start_date, tz='UTC')
        end = pd.Timestamp(self.config.end_date, tz='UTC')
        
        # Run algorithm
        self.results = run_algorithm(
            start=start,
            end=end,
            initialize=wrapped_initialize,
            handle_data=handle_data,
            before_trading_start=before_trading_start,
            analyze=analyze,
            capital_base=self.config.capital_base,
            data_frequency=self.config.data_frequency,
            bundle=self.config.bundle,
        )
        
        # Save results
        self._save_results()
        
        return self.results
    
    def _save_results(self):
        """Persist backtest results."""
        output_dir = os.path.join(self.config.output_dir, self.run_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save performance
        perf_path = os.path.join(output_dir, 'performance.csv')
        self.results.to_csv(perf_path)
        
        # Save config
        config_path = os.path.join(output_dir, 'config.yaml')
        self.config.save_yaml(config_path)
        
        # Save summary metrics
        summary = self._calculate_summary()
        summary_path = os.path.join(output_dir, 'summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save transactions
        if self.config.save_transactions and 'transactions' in self.results.columns:
            txn_path = os.path.join(output_dir, 'transactions.csv')
            self._extract_transactions().to_csv(txn_path)
    
    def _calculate_summary(self) -> dict:
        """Calculate summary metrics."""
        returns = self.results['returns']
        
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * (252 ** 0.5)
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'run_id': self.run_id,
            'start_date': self.config.start_date,
            'end_date': self.config.end_date,
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_dd),
            'final_value': float(self.results['portfolio_value'].iloc[-1]),
        }
    
    def _extract_transactions(self) -> pd.DataFrame:
        """Extract transactions to DataFrame."""
        all_txns = []
        for date, txns in self.results['transactions'].items():
            for txn in txns:
                txn['date'] = date
                all_txns.append(txn)
        return pd.DataFrame(all_txns)
```

## Batch Runner

```python
# scripts/runner/batch.py

from typing import List, Dict
import itertools
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

class BatchRunner:
    """Run multiple backtests with parameter variations."""
    
    def __init__(self, base_config: BacktestConfig):
        self.base_config = base_config
        self.results = []
    
    def run_parameter_grid(self, param_grid: Dict[str, List]) -> pd.DataFrame:
        """Run backtests for all parameter combinations."""
        
        # Generate all combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        summaries = []
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            # Create config with these parameters
            config = BacktestConfig(
                strategy_module=self.base_config.strategy_module,
                bundle=self.base_config.bundle,
                start_date=self.base_config.start_date,
                end_date=self.base_config.end_date,
                capital_base=self.base_config.capital_base,
                strategy_params={**self.base_config.strategy_params, **params},
                output_dir=self.base_config.output_dir,
            )
            
            # Run backtest
            runner = BacktestRunner(config)
            try:
                runner.run()
                summary = runner._calculate_summary()
                summary['params'] = params
                summaries.append(summary)
            except Exception as e:
                print(f"Failed for {params}: {e}")
        
        return pd.DataFrame(summaries)
    
    def run_date_ranges(self, date_ranges: List[tuple]) -> pd.DataFrame:
        """Run backtest across multiple date ranges."""
        summaries = []
        
        for start, end in date_ranges:
            config = BacktestConfig(
                strategy_module=self.base_config.strategy_module,
                bundle=self.base_config.bundle,
                start_date=start,
                end_date=end,
                capital_base=self.base_config.capital_base,
                strategy_params=self.base_config.strategy_params,
                output_dir=self.base_config.output_dir,
            )
            
            runner = BacktestRunner(config)
            try:
                runner.run()
                summary = runner._calculate_summary()
                summaries.append(summary)
            except Exception as e:
                print(f"Failed for {start}-{end}: {e}")
        
        return pd.DataFrame(summaries)
```

## CLI Interface

```python
#!/usr/bin/env python
# scripts/run_backtest.py

import argparse
from runner.config import BacktestConfig
from runner.runner import BacktestRunner

def main():
    parser = argparse.ArgumentParser(description='Run Zipline backtest')
    parser.add_argument('config', help='Path to config YAML')
    parser.add_argument('--start', help='Override start date')
    parser.add_argument('--end', help='Override end date')
    parser.add_argument('--capital', type=float, help='Override capital')
    parser.add_argument('--output', help='Override output directory')
    
    args = parser.parse_args()
    
    # Load config
    config = BacktestConfig.from_yaml(args.config)
    
    # Apply overrides
    if args.start:
        config.start_date = args.start
    if args.end:
        config.end_date = args.end
    if args.capital:
        config.capital_base = args.capital
    if args.output:
        config.output_dir = args.output
    
    # Run
    runner = BacktestRunner(config)
    results = runner.run()
    
    # Print summary
    summary = runner._calculate_summary()
    print("\n=== Backtest Summary ===")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

if __name__ == '__main__':
    main()
```

## Usage

### Single Backtest

```bash
python scripts/run_backtest.py config/momentum.yaml
```

### With Overrides

```bash
python scripts/run_backtest.py config/momentum.yaml \
    --start 2020-01-01 \
    --end 2023-12-31 \
    --capital 500000
```

### Parameter Grid Search

```python
from runner.batch import BatchRunner
from runner.config import BacktestConfig

config = BacktestConfig.from_yaml('config/momentum.yaml')
batch = BatchRunner(config)

results = batch.run_parameter_grid({
    'lookback_period': [20, 40, 60],
    'num_positions': [5, 10, 20],
})

# Find best parameters
best = results.loc[results['sharpe_ratio'].idxmax()]
print(f"Best params: {best['params']}")
```

## Script Reference

### run_backtest.py

Execute single backtest:

```bash
python scripts/run_backtest.py config.yaml
```

### batch_run.py

Execute parameter sweep:

```bash
python scripts/batch_run.py config.yaml --grid params.yaml
```

### compare_runs.py

Compare multiple backtest results:

```bash
python scripts/compare_runs.py results/run1 results/run2 results/run3
```

## Best Practices

1. **Version control configs**: Store configurations in git
2. **Use unique run IDs**: Timestamp-based for traceability
3. **Save all artifacts**: Config, results, transactions
4. **Catch exceptions**: Don't fail entire batch on one error
5. **Log progress**: Track batch execution status
