#!/usr/bin/env python3
"""
Parameter optimization for Zipline strategies.
Implements grid search, random search, and supports parallel execution.
"""
import argparse
import itertools
import pickle
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
import yaml
import time


@dataclass
class ParameterSpec:
    """Specification for a single parameter."""
    name: str
    param_type: str  # 'int', 'float', 'categorical'
    low: Optional[float] = None
    high: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[List] = None
    
    def get_values(self) -> List:
        """Generate all possible values for this parameter."""
        if self.param_type == 'categorical':
            return self.choices
        elif self.param_type == 'int':
            return list(range(int(self.low), int(self.high) + 1, 
                            int(self.step or 1)))
        elif self.param_type == 'float':
            if self.step:
                return list(np.arange(self.low, self.high + self.step/2, self.step))
            else:
                return [self.low, self.high]
        return []
    
    def sample(self, rng: np.random.Generator) -> Any:
        """Sample a random value for this parameter."""
        if self.param_type == 'categorical':
            return rng.choice(self.choices)
        elif self.param_type == 'int':
            return rng.integers(int(self.low), int(self.high) + 1)
        elif self.param_type == 'float':
            return rng.uniform(self.low, self.high)


@dataclass
class ParameterSpace:
    """Definition of the parameter search space."""
    params: Dict[str, ParameterSpec] = field(default_factory=dict)
    constraints: List[Callable] = field(default_factory=list)
    
    def add(self, name: str, spec: ParameterSpec):
        """Add a parameter to the space."""
        spec.name = name
        self.params[name] = spec
    
    def add_constraint(self, constraint: Callable):
        """Add a constraint function that returns True if valid."""
        self.constraints.append(constraint)
    
    def is_valid(self, params: Dict) -> bool:
        """Check if parameter combination satisfies all constraints."""
        return all(c(params) for c in self.constraints)
    
    def get_grid(self) -> List[Dict]:
        """Generate all valid parameter combinations."""
        param_values = {name: spec.get_values() 
                       for name, spec in self.params.items()}
        
        all_combos = [dict(zip(param_values.keys(), v)) 
                     for v in itertools.product(*param_values.values())]
        
        return [p for p in all_combos if self.is_valid(p)]
    
    def sample_random(self, n: int, seed: int = None) -> List[Dict]:
        """Sample n random valid parameter combinations."""
        rng = np.random.default_rng(seed)
        samples = []
        attempts = 0
        max_attempts = n * 100
        
        while len(samples) < n and attempts < max_attempts:
            sample = {name: spec.sample(rng) 
                     for name, spec in self.params.items()}
            if self.is_valid(sample):
                samples.append(sample)
            attempts += 1
        
        return samples
    
    @classmethod
    def from_yaml(cls, path: str) -> 'ParameterSpace':
        """Load parameter space from YAML file."""
        with open(path) as f:
            config = yaml.safe_load(f)
        
        space = cls()
        for name, spec in config.get('parameters', {}).items():
            param_type = spec.get('type', 'float')
            space.add(name, ParameterSpec(
                name=name,
                param_type=param_type,
                low=spec.get('low'),
                high=spec.get('high'),
                step=spec.get('step'),
                choices=spec.get('choices'),
            ))
        
        return space


@dataclass
class OptimizationResult:
    """Results from optimization run."""
    best_params: Dict
    best_score: float
    all_results: pd.DataFrame
    optimization_time: float
    method: str
    
    def top_n(self, n: int = 10) -> pd.DataFrame:
        """Get top N parameter combinations."""
        return self.all_results.nlargest(n, 'score')
    
    def save(self, path: str):
        """Save results to pickle."""
        with open(path, 'wb') as f:
            pickle.dump(self, f)
    
    @classmethod
    def load(cls, path: str) -> 'OptimizationResult':
        """Load results from pickle."""
        with open(path, 'rb') as f:
            return pickle.load(f)
    
    def summary(self) -> str:
        """Generate summary text."""
        lines = [
            "=" * 60,
            "OPTIMIZATION RESULTS",
            "=" * 60,
            f"Method: {self.method}",
            f"Time: {self.optimization_time:.1f} seconds",
            f"Combinations tested: {len(self.all_results)}",
            "",
            "Best Parameters:",
        ]
        for k, v in self.best_params.items():
            lines.append(f"  {k}: {v}")
        lines.append(f"\nBest Score: {self.best_score:.4f}")
        lines.append("=" * 60)
        return "\n".join(lines)


class BaseOptimizer:
    """Base class for parameter optimizers."""
    
    def __init__(self, param_space: ParameterSpace,
                 objective: str = 'sharpe',
                 n_jobs: int = 1):
        self.param_space = param_space
        self.objective = objective
        self.n_jobs = n_jobs
    
    def optimize(self, strategy_fn: Callable) -> OptimizationResult:
        raise NotImplementedError


class GridSearchOptimizer(BaseOptimizer):
    """Exhaustive grid search over parameter space."""
    
    def optimize(self, strategy_fn: Callable) -> OptimizationResult:
        """Run grid search optimization."""
        start_time = time.time()
        
        param_grid = self.param_space.get_grid()
        print(f"Grid search: {len(param_grid)} combinations")
        
        results = []
        
        if self.n_jobs == 1:
            # Sequential execution
            for i, params in enumerate(param_grid):
                try:
                    metrics = strategy_fn(params)
                    score = metrics.get(self.objective, float('-inf'))
                    results.append({**params, 'score': score, **metrics})
                except Exception as e:
                    results.append({**params, 'score': float('-inf'), 'error': str(e)})
                
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{len(param_grid)}")
        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = {executor.submit(strategy_fn, p): p for p in param_grid}
                
                for i, future in enumerate(as_completed(futures)):
                    params = futures[future]
                    try:
                        metrics = future.result()
                        score = metrics.get(self.objective, float('-inf'))
                        results.append({**params, 'score': score, **metrics})
                    except Exception as e:
                        results.append({**params, 'score': float('-inf'), 'error': str(e)})
                    
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i+1}/{len(param_grid)}")
        
        df = pd.DataFrame(results)
        best_idx = df['score'].idxmax()
        best_row = df.loc[best_idx]
        
        # Extract only parameter columns for best_params
        param_names = list(self.param_space.params.keys())
        best_params = {k: best_row[k] for k in param_names}
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_row['score'],
            all_results=df,
            optimization_time=time.time() - start_time,
            method='grid_search'
        )


class RandomSearchOptimizer(BaseOptimizer):
    """Random search over parameter space."""
    
    def __init__(self, param_space: ParameterSpace,
                 objective: str = 'sharpe',
                 n_iter: int = 100,
                 n_jobs: int = 1,
                 random_state: int = None):
        super().__init__(param_space, objective, n_jobs)
        self.n_iter = n_iter
        self.random_state = random_state
    
    def optimize(self, strategy_fn: Callable) -> OptimizationResult:
        """Run random search optimization."""
        start_time = time.time()
        
        param_samples = self.param_space.sample_random(
            self.n_iter, seed=self.random_state
        )
        print(f"Random search: {len(param_samples)} samples")
        
        results = []
        best_score = float('-inf')
        best_params = None
        
        for i, params in enumerate(param_samples):
            try:
                metrics = strategy_fn(params)
                score = metrics.get(self.objective, float('-inf'))
                results.append({**params, 'score': score, **metrics})
                
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    print(f"  New best at iteration {i+1}: {self.objective}={score:.4f}")
            except Exception as e:
                results.append({**params, 'score': float('-inf'), 'error': str(e)})
        
        df = pd.DataFrame(results)
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=df,
            optimization_time=time.time() - start_time,
            method='random_search'
        )


def create_strategy_runner(strategy_path: str, bundle: str,
                          start: str, end: str, capital: float):
    """Create a strategy runner function from a strategy file."""
    
    # Import strategy module
    import importlib.util
    spec = importlib.util.spec_from_file_location("strategy", strategy_path)
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    
    def run_with_params(params: Dict) -> Dict:
        """Run strategy with given parameters."""
        from zipline import run_algorithm
        import pandas as pd
        
        # Create parameterized initialize
        original_init = strategy_module.initialize
        def parameterized_init(context):
            for k, v in params.items():
                setattr(context, k, v)
            original_init(context)
        
        results = run_algorithm(
            start=pd.Timestamp(start, tz='utc'),
            end=pd.Timestamp(end, tz='utc'),
            initialize=parameterized_init,
            handle_data=strategy_module.handle_data,
            capital_base=capital,
            bundle=bundle
        )
        
        # Calculate metrics
        returns = results['returns'].dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        total_return = (results['portfolio_value'].iloc[-1] / 
                       results['portfolio_value'].iloc[0]) - 1
        
        rolling_max = results['portfolio_value'].expanding().max()
        max_dd = ((results['portfolio_value'] - rolling_max) / rolling_max).min()
        
        return {
            'sharpe': sharpe,
            'total_return': total_return,
            'max_drawdown': max_dd,
            'volatility': returns.std() * np.sqrt(252),
        }
    
    return run_with_params


def main():
    parser = argparse.ArgumentParser(description='Optimize strategy parameters')
    parser.add_argument('--strategy', required=True, help='Path to strategy.py')
    parser.add_argument('--params', required=True, help='Path to params.yaml')
    parser.add_argument('--method', default='grid', choices=['grid', 'random'])
    parser.add_argument('--objective', default='sharpe', 
                       help='Metric to optimize')
    parser.add_argument('--n-iter', type=int, default=100,
                       help='Iterations for random search')
    parser.add_argument('--n-jobs', type=int, default=1,
                       help='Parallel workers')
    parser.add_argument('--bundle', default='quandl', help='Data bundle')
    parser.add_argument('--start', required=True, help='Start date')
    parser.add_argument('--end', required=True, help='End date')
    parser.add_argument('--capital', type=float, default=100000)
    parser.add_argument('--output', type=Path, default=Path('.'),
                       help='Output directory')
    parser.add_argument('--seed', type=int, help='Random seed')
    args = parser.parse_args()
    
    # Load parameter space
    param_space = ParameterSpace.from_yaml(args.params)
    print(f"Loaded {len(param_space.params)} parameters")
    
    # Create strategy runner
    strategy_fn = create_strategy_runner(
        args.strategy, args.bundle, args.start, args.end, args.capital
    )
    
    # Create optimizer
    if args.method == 'grid':
        optimizer = GridSearchOptimizer(
            param_space, args.objective, args.n_jobs
        )
    else:
        optimizer = RandomSearchOptimizer(
            param_space, args.objective, args.n_iter,
            args.n_jobs, args.seed
        )
    
    # Run optimization
    print(f"\nStarting {args.method} search...")
    results = optimizer.optimize(strategy_fn)
    
    # Save results
    args.output.mkdir(parents=True, exist_ok=True)
    results.save(args.output / 'optimization_results.pickle')
    results.all_results.to_csv(args.output / 'all_results.csv', index=False)
    
    # Print summary
    print(results.summary())
    
    # Save best params
    with open(args.output / 'best_params.yaml', 'w') as f:
        yaml.dump(results.best_params, f)
    
    print(f"\nResults saved to: {args.output}")
    return 0


if __name__ == '__main__':
    exit(main())
