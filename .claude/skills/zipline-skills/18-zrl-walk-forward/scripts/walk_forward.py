#!/usr/bin/env python3
"""
Walk-forward analysis for Zipline strategy validation.
Implements rolling and anchored walk-forward with out-of-sample testing.
"""
import argparse
import pickle
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import yaml
from datetime import timedelta
import re


def parse_period(period_str: str) -> timedelta:
    """Parse period string like '2Y', '6M', '30D' to timedelta."""
    match = re.match(r'(\d+)([YMD])', period_str.upper())
    if not match:
        raise ValueError(f"Invalid period format: {period_str}")
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'Y':
        return timedelta(days=value * 365)
    elif unit == 'M':
        return timedelta(days=value * 30)
    elif unit == 'D':
        return timedelta(days=value)


@dataclass
class Window:
    """Single train/test window."""
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    
    @property
    def train_days(self) -> int:
        return (self.train_end - self.train_start).days
    
    @property
    def test_days(self) -> int:
        return (self.test_end - self.test_start).days


@dataclass
class WindowResult:
    """Results from a single walk-forward window."""
    window: Window
    best_params: Dict
    is_sharpe: float      # In-sample Sharpe
    oos_sharpe: float     # Out-of-sample Sharpe
    is_return: float
    oos_return: float
    oos_returns: pd.Series
    oos_equity: pd.Series


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward analysis."""
    train_period: str     # e.g., '2Y'
    test_period: str      # e.g., '6M'
    step: str             # e.g., '3M'
    method: str = 'rolling'  # 'rolling' or 'anchored'
    gap: str = '0D'       # Gap between train and test


@dataclass 
class WalkForwardResult:
    """Complete walk-forward analysis results."""
    windows: List[WindowResult]
    config: WalkForwardConfig
    
    @property
    def in_sample_sharpe(self) -> float:
        return np.mean([w.is_sharpe for w in self.windows])
    
    @property
    def oos_sharpe(self) -> float:
        return np.mean([w.oos_sharpe for w in self.windows])
    
    @property
    def efficiency_ratio(self) -> float:
        if self.in_sample_sharpe == 0:
            return 0.0
        return self.oos_sharpe / self.in_sample_sharpe
    
    @property
    def oos_equity(self) -> pd.Series:
        """Combine all OOS equity curves."""
        all_equity = pd.concat([w.oos_equity for w in self.windows])
        return all_equity.sort_index()
    
    @property
    def oos_returns(self) -> pd.Series:
        """Combine all OOS returns."""
        all_returns = pd.concat([w.oos_returns for w in self.windows])
        return all_returns.sort_index()
    
    def param_stability(self) -> Dict[str, float]:
        """Calculate coefficient of variation for each parameter."""
        if not self.windows:
            return {}
        
        stability = {}
        param_names = list(self.windows[0].best_params.keys())
        
        for param in param_names:
            values = [w.best_params.get(param) for w in self.windows]
            # Filter non-numeric
            values = [v for v in values if isinstance(v, (int, float))]
            if values:
                mean = np.mean(values)
                std = np.std(values)
                stability[param] = std / abs(mean) if mean != 0 else np.inf
        
        return stability
    
    def summary(self) -> str:
        """Generate summary report."""
        lines = [
            "=" * 60,
            "WALK-FORWARD ANALYSIS RESULTS",
            "=" * 60,
            f"Method: {self.config.method}",
            f"Train Period: {self.config.train_period}",
            f"Test Period: {self.config.test_period}",
            f"Step: {self.config.step}",
            f"Windows: {len(self.windows)}",
            "",
            "Performance:",
            f"  In-Sample Sharpe:      {self.in_sample_sharpe:>8.2f}",
            f"  Out-of-Sample Sharpe:  {self.oos_sharpe:>8.2f}",
            f"  Efficiency Ratio:      {self.efficiency_ratio:>8.1%}",
            "",
            "Window Details:",
        ]
        
        for i, w in enumerate(self.windows):
            lines.append(f"  {i+1}. Train: {w.window.train_start.date()} to "
                        f"{w.window.train_end.date()} | "
                        f"Test: {w.window.test_start.date()} to "
                        f"{w.window.test_end.date()}")
            lines.append(f"      IS Sharpe: {w.is_sharpe:.2f} | "
                        f"OOS Sharpe: {w.oos_sharpe:.2f}")
        
        lines.append("")
        lines.append("Parameter Stability (CV):")
        for param, cv in self.param_stability().items():
            lines.append(f"  {param}: {cv:.2f}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def save(self, path: str):
        """Save results to pickle."""
        with open(path, 'wb') as f:
            pickle.dump(self, f)


class WalkForwardAnalyzer:
    """Perform walk-forward analysis on a strategy."""
    
    def __init__(self, config: WalkForwardConfig,
                 param_space: Dict = None,
                 optimizer: str = 'grid',
                 objective: str = 'sharpe'):
        self.config = config
        self.param_space = param_space
        self.optimizer = optimizer
        self.objective = objective
    
    def generate_windows(self, start: str, end: str) -> List[Window]:
        """Generate train/test windows based on configuration."""
        start_date = pd.Timestamp(start, tz='utc')
        end_date = pd.Timestamp(end, tz='utc')
        
        train_delta = parse_period(self.config.train_period)
        test_delta = parse_period(self.config.test_period)
        step_delta = parse_period(self.config.step)
        gap_delta = parse_period(self.config.gap)
        
        windows = []
        
        if self.config.method == 'rolling':
            current = start_date
            while current + train_delta + gap_delta + test_delta <= end_date:
                train_start = current
                train_end = current + train_delta
                test_start = train_end + gap_delta
                test_end = test_start + test_delta
                
                windows.append(Window(
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end
                ))
                
                current += step_delta
        
        elif self.config.method == 'anchored':
            anchor = start_date
            current = anchor + train_delta
            
            while current + gap_delta + test_delta <= end_date:
                train_end = current
                test_start = train_end + gap_delta
                test_end = test_start + test_delta
                
                windows.append(Window(
                    train_start=anchor,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end
                ))
                
                current += step_delta
        
        return windows
    
    def run(self, strategy_fn: Callable,
            optimize_fn: Callable,
            start: str, end: str) -> WalkForwardResult:
        """
        Run walk-forward analysis.
        
        Parameters
        ----------
        strategy_fn : Callable
            Function that runs strategy with params and date range
            Signature: (params, start, end) -> Dict with 'sharpe', 'returns', 'equity'
        optimize_fn : Callable
            Function that optimizes parameters on training period
            Signature: (start, end) -> best_params
        """
        windows = self.generate_windows(start, end)
        print(f"Generated {len(windows)} walk-forward windows")
        
        results = []
        
        for i, window in enumerate(windows):
            print(f"\nWindow {i+1}/{len(windows)}")
            print(f"  Train: {window.train_start.date()} to {window.train_end.date()}")
            print(f"  Test:  {window.test_start.date()} to {window.test_end.date()}")
            
            # Optimize on training period
            print("  Optimizing...", end=' ')
            best_params = optimize_fn(
                str(window.train_start.date()),
                str(window.train_end.date())
            )
            print("Done")
            
            # Evaluate on training period (in-sample)
            is_metrics = strategy_fn(
                best_params,
                str(window.train_start.date()),
                str(window.train_end.date())
            )
            
            # Evaluate on test period (out-of-sample)
            oos_metrics = strategy_fn(
                best_params,
                str(window.test_start.date()),
                str(window.test_end.date())
            )
            
            print(f"  IS Sharpe: {is_metrics.get('sharpe', 0):.2f}")
            print(f"  OOS Sharpe: {oos_metrics.get('sharpe', 0):.2f}")
            
            results.append(WindowResult(
                window=window,
                best_params=best_params,
                is_sharpe=is_metrics.get('sharpe', 0),
                oos_sharpe=oos_metrics.get('sharpe', 0),
                is_return=is_metrics.get('total_return', 0),
                oos_return=oos_metrics.get('total_return', 0),
                oos_returns=oos_metrics.get('returns', pd.Series()),
                oos_equity=oos_metrics.get('equity', pd.Series()),
            ))
        
        return WalkForwardResult(windows=results, config=self.config)


def create_simple_optimizer(strategy_fn: Callable, 
                           param_grid: Dict) -> Callable:
    """Create a simple grid search optimizer function."""
    import itertools
    
    def optimize(start: str, end: str) -> Dict:
        best_params = None
        best_sharpe = float('-inf')
        
        # Generate all parameter combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        for combo in itertools.product(*values):
            params = dict(zip(keys, combo))
            
            try:
                metrics = strategy_fn(params, start, end)
                sharpe = metrics.get('sharpe', float('-inf'))
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params.copy()
            except Exception:
                continue
        
        return best_params or dict(zip(keys, [v[0] for v in values]))
    
    return optimize


def main():
    parser = argparse.ArgumentParser(description='Walk-forward analysis')
    parser.add_argument('--strategy', required=True, help='Path to strategy module')
    parser.add_argument('--params', help='Path to parameter grid YAML')
    parser.add_argument('--train-period', default='2Y', help='Training period')
    parser.add_argument('--test-period', default='6M', help='Test period')
    parser.add_argument('--step', default='3M', help='Step size')
    parser.add_argument('--method', default='rolling', choices=['rolling', 'anchored'])
    parser.add_argument('--gap', default='0D', help='Gap between train/test')
    parser.add_argument('--start', required=True, help='Start date')
    parser.add_argument('--end', required=True, help='End date')
    parser.add_argument('--bundle', default='quandl', help='Data bundle')
    parser.add_argument('--capital', type=float, default=100000)
    parser.add_argument('--output', type=Path, default=Path('.'))
    args = parser.parse_args()
    
    # Load strategy module
    import importlib.util
    spec = importlib.util.spec_from_file_location("strategy", args.strategy)
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    
    # Load parameter grid
    param_grid = {}
    if args.params:
        with open(args.params) as f:
            config = yaml.safe_load(f)
            param_grid = {
                name: spec.get('values', [spec.get('low', 0)])
                for name, spec in config.get('parameters', {}).items()
            }
    
    # Create strategy runner
    def run_strategy(params: Dict, start: str, end: str) -> Dict:
        from zipline import run_algorithm
        
        def parameterized_init(context):
            for k, v in params.items():
                setattr(context, k, v)
            strategy_module.initialize(context)
        
        results = run_algorithm(
            start=pd.Timestamp(start, tz='utc'),
            end=pd.Timestamp(end, tz='utc'),
            initialize=parameterized_init,
            handle_data=strategy_module.handle_data,
            capital_base=args.capital,
            bundle=args.bundle
        )
        
        returns = results['returns'].dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        return {
            'sharpe': sharpe,
            'total_return': (results['portfolio_value'].iloc[-1] / 
                           results['portfolio_value'].iloc[0]) - 1,
            'returns': returns,
            'equity': results['portfolio_value']
        }
    
    # Create optimizer
    optimizer = create_simple_optimizer(run_strategy, param_grid)
    
    # Configure walk-forward
    config = WalkForwardConfig(
        train_period=args.train_period,
        test_period=args.test_period,
        step=args.step,
        method=args.method,
        gap=args.gap
    )
    
    # Run analysis
    analyzer = WalkForwardAnalyzer(config)
    results = analyzer.run(run_strategy, optimizer, args.start, args.end)
    
    # Save results
    args.output.mkdir(parents=True, exist_ok=True)
    results.save(args.output / 'wf_results.pickle')
    
    # Print summary
    print("\n" + results.summary())
    
    # Save summary
    with open(args.output / 'summary.txt', 'w') as f:
        f.write(results.summary())
    
    print(f"\nResults saved to: {args.output}")
    return 0


if __name__ == '__main__':
    exit(main())
