---
name: zrl-parameter-optimizer
description: This skill should be used when optimizing strategy parameters through grid search, random search, or Bayesian optimization. It provides systematic approaches to find optimal parameter combinations while avoiding overfitting through cross-validation and walk-forward methods.
---

# Zipline Parameter Optimizer

Optimize strategy parameters systematically while guarding against overfitting.

## Purpose

Find optimal strategy parameter combinations through grid search, random search, or Bayesian optimization while implementing safeguards against curve-fitting.

## When to Use

- Finding optimal lookback periods, thresholds, weights
- Comparing performance across parameter ranges
- Performing sensitivity analysis on strategy parameters
- Validating parameter stability through cross-validation
- Implementing walk-forward parameter optimization

## Optimization Methods

### 1. Grid Search

Exhaustive search over specified parameter grid.

| Pros | Cons |
|------|------|
| Complete coverage | Computationally expensive |
| Easy to parallelize | Curse of dimensionality |
| Reproducible | Many redundant evaluations |

### 2. Random Search

Random sampling from parameter space.

| Pros | Cons |
|------|------|
| More efficient for high dimensions | May miss optimal region |
| Handles continuous params well | Less reproducible |
| Good for initial exploration | No convergence guarantee |

### 3. Bayesian Optimization

Intelligent search using surrogate models.

| Pros | Cons |
|------|------|
| Sample efficient | Complex implementation |
| Balances exploration/exploitation | Overhead for simple problems |
| Works well with noise | Sequential (hard to parallelize) |

## Core Workflow

### Step 1: Define Parameter Space

```python
from parameter_optimizer import ParameterSpace

param_space = ParameterSpace({
    'fast_period': {'type': 'int', 'low': 5, 'high': 30, 'step': 5},
    'slow_period': {'type': 'int', 'low': 20, 'high': 100, 'step': 10},
    'threshold': {'type': 'float', 'low': 0.01, 'high': 0.10, 'step': 0.01},
    'stop_loss': {'type': 'float', 'low': 0.02, 'high': 0.10, 'step': 0.02},
})
```

### Step 2: Create Strategy Function

```python
def run_strategy(params: dict) -> dict:
    """Run strategy with given parameters and return metrics."""
    
    def initialize(context):
        context.fast = params['fast_period']
        context.slow = params['slow_period']
        context.threshold = params['threshold']
        context.stop_loss = params['stop_loss']
        # ... setup strategy
    
    results = run_algorithm(
        start=start,
        end=end,
        initialize=initialize,
        handle_data=handle_data,
        capital_base=100000,
        bundle='my-bundle'
    )
    
    return {
        'sharpe': calculate_sharpe(results),
        'total_return': results['returns'].sum(),
        'max_drawdown': calculate_max_dd(results),
    }
```

### Step 3: Run Optimization

```python
from parameter_optimizer import GridSearchOptimizer

optimizer = GridSearchOptimizer(
    param_space=param_space,
    objective='sharpe',
    n_jobs=4  # Parallel workers
)

results = optimizer.optimize(run_strategy)
print(f"Best parameters: {results.best_params}")
print(f"Best Sharpe: {results.best_score:.2f}")
```

## Script Reference

### optimize_params.py

Run parameter optimization from command line:

```bash
python scripts/optimize_params.py \
    --strategy strategy.py \
    --params params.yaml \
    --method grid \
    --objective sharpe \
    --output results/
```

### sensitivity_analysis.py

Analyze parameter sensitivity:

```bash
python scripts/sensitivity_analysis.py \
    --results optimization_results.pickle \
    --param fast_period \
    --output sensitivity.png
```

### cross_validate.py

Cross-validate optimal parameters:

```bash
python scripts/cross_validate.py \
    --strategy strategy.py \
    --params best_params.yaml \
    --folds 5 \
    --output cv_results.csv
```

## Parameter Space Definition

### YAML Format

```yaml
# params.yaml
parameters:
  fast_period:
    type: int
    low: 5
    high: 50
    step: 5
  
  slow_period:
    type: int
    low: 20
    high: 200
    step: 10
  
  threshold:
    type: float
    low: 0.01
    high: 0.20
  
  rebalance_freq:
    type: categorical
    choices: ['daily', 'weekly', 'monthly']

constraints:
  - "slow_period > fast_period"
  - "slow_period >= 2 * fast_period"

objective:
  metric: sharpe
  direction: maximize
```

### Programmatic Definition

```python
from parameter_optimizer import ParameterSpace, IntParam, FloatParam, CategoricalParam

param_space = ParameterSpace()
param_space.add('fast_period', IntParam(5, 50, step=5))
param_space.add('slow_period', IntParam(20, 200, step=10))
param_space.add('threshold', FloatParam(0.01, 0.20))
param_space.add('rebalance', CategoricalParam(['daily', 'weekly', 'monthly']))

# Add constraints
param_space.add_constraint(lambda p: p['slow_period'] > p['fast_period'])
```

## Optimizer Classes

### GridSearchOptimizer

```python
class GridSearchOptimizer:
    """Exhaustive grid search optimization."""
    
    def __init__(self, param_space: ParameterSpace,
                 objective: str = 'sharpe',
                 n_jobs: int = 1):
        """
        Parameters
        ----------
        param_space : ParameterSpace
            Parameter definitions
        objective : str
            Metric to optimize ('sharpe', 'return', 'calmar')
        n_jobs : int
            Parallel workers (-1 for all cores)
        """
    
    def optimize(self, strategy_fn: Callable) -> OptimizationResult
    def get_param_grid(self) -> List[Dict]
```

### RandomSearchOptimizer

```python
class RandomSearchOptimizer:
    """Random search optimization."""
    
    def __init__(self, param_space: ParameterSpace,
                 objective: str = 'sharpe',
                 n_iter: int = 100,
                 n_jobs: int = 1,
                 random_state: int = None):
        """
        Parameters
        ----------
        n_iter : int
            Number of random samples
        random_state : int
            Random seed for reproducibility
        """
```

### BayesianOptimizer

```python
class BayesianOptimizer:
    """Bayesian optimization with Gaussian Process surrogate."""
    
    def __init__(self, param_space: ParameterSpace,
                 objective: str = 'sharpe',
                 n_iter: int = 50,
                 n_initial: int = 10,
                 acquisition: str = 'ei'):
        """
        Parameters
        ----------
        n_iter : int
            Total optimization iterations
        n_initial : int
            Random samples before GP fitting
        acquisition : str
            Acquisition function ('ei', 'ucb', 'poi')
        """
```

## Overfitting Prevention

### 1. Walk-Forward Validation

```python
from parameter_optimizer import WalkForwardOptimizer

optimizer = WalkForwardOptimizer(
    param_space=param_space,
    train_period='2Y',
    test_period='6M',
    step='3M',
    objective='sharpe'
)

results = optimizer.optimize(run_strategy, start='2015-01-01', end='2023-12-31')
# Returns average out-of-sample performance
```

### 2. K-Fold Cross-Validation

```python
from parameter_optimizer import CrossValidator

cv = CrossValidator(n_folds=5, shuffle=True)
cv_results = cv.validate(run_strategy, best_params)

print(f"CV Sharpe: {cv_results['sharpe'].mean():.2f} +/- {cv_results['sharpe'].std():.2f}")
```

### 3. Robustness Checks

```python
# Parameter sensitivity analysis
sensitivity = optimizer.sensitivity_analysis(
    best_params,
    param='fast_period',
    variation=0.2  # +/- 20%
)

# Monte Carlo simulation
mc_results = optimizer.monte_carlo_validation(
    best_params,
    n_simulations=1000,
    noise_level=0.1
)
```

## Results Analysis

### OptimizationResult

```python
@dataclass
class OptimizationResult:
    best_params: Dict
    best_score: float
    all_results: pd.DataFrame
    optimization_time: float
    
    def plot_convergence(self)
    def plot_param_importance(self)
    def top_n_params(self, n: int) -> pd.DataFrame
    def to_pickle(self, path: str)
```

### Visualization

```python
# Parameter importance
results.plot_param_importance()

# Optimization convergence
results.plot_convergence()

# 2D parameter heatmap
results.plot_heatmap('fast_period', 'slow_period', metric='sharpe')
```

## Parallel Execution

```python
from parameter_optimizer import ParallelOptimizer

optimizer = ParallelOptimizer(
    param_space=param_space,
    n_jobs=8,
    backend='multiprocessing'  # or 'ray', 'dask'
)

# Progress tracking
results = optimizer.optimize(run_strategy, progress=True)
```

## Best Practices

### 1. Start Coarse, Refine Fine

```python
# Phase 1: Coarse search
coarse_space = ParameterSpace({
    'period': {'type': 'int', 'low': 5, 'high': 100, 'step': 20},
})
coarse_results = GridSearchOptimizer(coarse_space).optimize(run_strategy)

# Phase 2: Fine search around best
best = coarse_results.best_params['period']
fine_space = ParameterSpace({
    'period': {'type': 'int', 'low': best-10, 'high': best+10, 'step': 2},
})
fine_results = GridSearchOptimizer(fine_space).optimize(run_strategy)
```

### 2. Multiple Objectives

```python
# Pareto optimization
results = optimizer.optimize_multi_objective(
    run_strategy,
    objectives=['sharpe', 'max_drawdown'],
    directions=['maximize', 'minimize']
)

# Get Pareto frontier
pareto_front = results.get_pareto_front()
```

### 3. Save Intermediate Results

```python
optimizer = GridSearchOptimizer(
    param_space,
    checkpoint_dir='optimization_checkpoints/',
    checkpoint_freq=10
)

# Resume from checkpoint
optimizer.resume_from_checkpoint('checkpoint_50.pickle')
```

## Integration Pattern

```python
def optimize_strategy():
    """Complete optimization workflow."""
    
    # 1. Define parameter space
    param_space = ParameterSpace({...})
    
    # 2. Split data: train/validation/test
    train_end = pd.Timestamp('2020-12-31', tz='utc')
    test_start = pd.Timestamp('2021-01-01', tz='utc')
    
    # 3. Optimize on training data
    optimizer = GridSearchOptimizer(param_space)
    train_results = optimizer.optimize(
        lambda p: run_strategy(p, end=train_end)
    )
    
    # 4. Validate on test data
    test_metrics = run_strategy(train_results.best_params, 
                                start=test_start)
    
    # 5. Compare in-sample vs out-of-sample
    print(f"Train Sharpe: {train_results.best_score:.2f}")
    print(f"Test Sharpe:  {test_metrics['sharpe']:.2f}")
    
    return train_results.best_params

## References

See `references/optimization_methods.md` for algorithm details.
See `references/overfitting_guide.md` for overfitting prevention.
```
