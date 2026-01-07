---
name: zrl-walk-forward
description: This skill should be used when performing walk-forward analysis and out-of-sample testing for strategy validation. It provides frameworks for rolling window optimization, anchored walk-forward, and regime-based validation to assess strategy robustness.
---

# Zipline Walk-Forward Analysis

Validate strategy robustness through rigorous out-of-sample testing.

## Purpose

Implement walk-forward analysis to test strategy performance on unseen data, detect overfitting, and estimate realistic future performance expectations.

## When to Use

- Validating optimized parameters on out-of-sample data
- Testing strategy robustness across different time periods
- Comparing in-sample vs out-of-sample performance
- Estimating realistic performance expectations
- Detecting curve-fitting and parameter instability

## Walk-Forward Methods

### 1. Rolling Window

Sliding training and test windows of fixed size.

```
|---Train---|--Test--|
      |---Train---|--Test--|
            |---Train---|--Test--|
```

### 2. Anchored (Expanding)

Training window starts from beginning, test window rolls forward.

```
|---Train---|--Test--|
|------Train------|--Test--|
|---------Train---------|--Test--|
```

### 3. Purged K-Fold

K-fold with gaps to prevent look-ahead bias.

```
|--Train--|gap|Test|gap|--Train--|
|--Test--|gap|------Train-------|
```

## Core Workflow

### Step 1: Define Walk-Forward Parameters

```python
from walk_forward import WalkForwardConfig

config = WalkForwardConfig(
    train_period='2Y',      # 2-year training window
    test_period='6M',       # 6-month test window
    step='3M',              # Step forward 3 months
    method='rolling',       # 'rolling' or 'anchored'
    gap='5D',               # Gap between train/test (optional)
)
```

### Step 2: Create Walk-Forward Analyzer

```python
from walk_forward import WalkForwardAnalyzer

analyzer = WalkForwardAnalyzer(
    config=config,
    param_space=param_space,
    optimizer='grid',
    objective='sharpe'
)
```

### Step 3: Run Analysis

```python
results = analyzer.run(
    strategy_fn=run_strategy,
    start='2010-01-01',
    end='2023-12-31',
    bundle='my-bundle'
)

print(f"In-Sample Sharpe:  {results.in_sample_sharpe:.2f}")
print(f"Out-of-Sample Sharpe: {results.oos_sharpe:.2f}")
print(f"Efficiency Ratio: {results.efficiency_ratio:.2%}")
```

## Script Reference

### walk_forward.py

Run walk-forward analysis:

```bash
python scripts/walk_forward.py \
    --strategy strategy.py \
    --params params.yaml \
    --train-period 2Y \
    --test-period 6M \
    --step 3M \
    --start 2010-01-01 \
    --end 2023-12-31 \
    --output wf_results/
```

### analyze_wf_results.py

Analyze walk-forward results:

```bash
python scripts/analyze_wf_results.py \
    wf_results/results.pickle \
    --output report.html
```

### compare_methods.py

Compare different walk-forward configurations:

```bash
python scripts/compare_methods.py \
    --strategy strategy.py \
    --configs rolling.yaml anchored.yaml \
    --output comparison.csv
```

## WalkForwardAnalyzer Class

```python
class WalkForwardAnalyzer:
    """Walk-forward analysis for strategy validation."""
    
    def __init__(self, config: WalkForwardConfig,
                 param_space: ParameterSpace,
                 optimizer: str = 'grid',
                 objective: str = 'sharpe'):
        """
        Parameters
        ----------
        config : WalkForwardConfig
            Walk-forward window configuration
        param_space : ParameterSpace
            Parameters to optimize each window
        optimizer : str
            Optimization method ('grid', 'random', 'bayesian')
        objective : str
            Metric to optimize
        """
    
    def run(self, strategy_fn: Callable,
            start: str, end: str,
            bundle: str) -> WalkForwardResult
    
    def generate_windows(self, start: str, end: str) -> List[Window]
    
    def analyze_stability(self) -> pd.DataFrame
```

## Window Generation

### Rolling Windows

```python
def generate_rolling_windows(start, end, train_period, test_period, step):
    """Generate rolling train/test windows."""
    windows = []
    current = pd.Timestamp(start, tz='utc')
    end_date = pd.Timestamp(end, tz='utc')
    
    while current + train_period + test_period <= end_date:
        train_start = current
        train_end = current + train_period
        test_start = train_end
        test_end = test_start + test_period
        
        windows.append(Window(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end
        ))
        
        current += step
    
    return windows
```

### Anchored Windows

```python
def generate_anchored_windows(start, end, min_train, test_period, step):
    """Generate anchored (expanding) windows."""
    windows = []
    anchor = pd.Timestamp(start, tz='utc')
    current = anchor + min_train
    end_date = pd.Timestamp(end, tz='utc')
    
    while current + test_period <= end_date:
        train_end = current
        test_start = train_end
        test_end = test_start + test_period
        
        windows.append(Window(
            train_start=anchor,  # Always starts from anchor
            train_end=train_end,
            test_start=test_start,
            test_end=test_end
        ))
        
        current += step
    
    return windows
```

## Results Analysis

### WalkForwardResult

```python
@dataclass
class WalkForwardResult:
    # Per-window results
    windows: List[WindowResult]
    
    # Aggregate metrics
    in_sample_sharpe: float      # Average IS Sharpe
    oos_sharpe: float            # Average OOS Sharpe
    efficiency_ratio: float      # OOS / IS Sharpe
    
    # Parameter stability
    param_stability: Dict[str, float]  # Std of params across windows
    
    # Equity curve (combined OOS periods)
    oos_equity: pd.Series
    oos_returns: pd.Series
    
    def plot_efficiency(self)
    def plot_param_evolution(self, param: str)
    def plot_oos_equity(self)
    def summary_report(self) -> str
```

### Efficiency Ratio

The efficiency ratio measures how well in-sample performance translates to out-of-sample:

```python
efficiency_ratio = oos_sharpe / in_sample_sharpe
```

| Ratio | Interpretation |
|-------|----------------|
| > 1.0 | OOS better than IS (rare) |
| 0.7 - 1.0 | Good generalization |
| 0.5 - 0.7 | Acceptable, some overfitting |
| < 0.5 | Significant overfitting |

### Parameter Stability

Measure how much optimal parameters vary across windows:

```python
def parameter_stability(results: WalkForwardResult) -> Dict[str, float]:
    """Calculate coefficient of variation for each parameter."""
    stability = {}
    
    for param in results.windows[0].best_params.keys():
        values = [w.best_params[param] for w in results.windows]
        mean = np.mean(values)
        std = np.std(values)
        stability[param] = std / mean if mean != 0 else np.inf
    
    return stability
```

Low stability scores (CV < 0.3) suggest robust parameters.

## Visualization

### Walk-Forward Timeline

```python
def plot_wf_timeline(results: WalkForwardResult):
    """Visualize walk-forward windows and performance."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # Window timeline
    ax1 = axes[0]
    for i, w in enumerate(results.windows):
        ax1.barh(i, (w.train_end - w.train_start).days, 
                left=w.train_start, color='blue', alpha=0.5, label='Train')
        ax1.barh(i, (w.test_end - w.test_start).days,
                left=w.test_start, color='green', alpha=0.5, label='Test')
    ax1.set_title('Walk-Forward Windows')
    
    # IS vs OOS Sharpe
    ax2 = axes[1]
    window_nums = range(len(results.windows))
    is_sharpes = [w.is_sharpe for w in results.windows]
    oos_sharpes = [w.oos_sharpe for w in results.windows]
    ax2.bar(window_nums, is_sharpes, alpha=0.5, label='In-Sample')
    ax2.bar(window_nums, oos_sharpes, alpha=0.5, label='Out-of-Sample')
    ax2.set_title('Sharpe Ratio by Window')
    ax2.legend()
    
    # OOS Equity Curve
    ax3 = axes[2]
    results.oos_equity.plot(ax=ax3)
    ax3.set_title('Combined Out-of-Sample Equity')
    
    plt.tight_layout()
```

### Parameter Evolution

```python
def plot_param_evolution(results: WalkForwardResult, param: str):
    """Plot how a parameter changes across windows."""
    values = [w.best_params[param] for w in results.windows]
    dates = [w.test_start for w in results.windows]
    
    plt.figure(figsize=(12, 4))
    plt.plot(dates, values, 'o-')
    plt.axhline(np.mean(values), color='red', linestyle='--', 
               label=f'Mean: {np.mean(values):.2f}')
    plt.fill_between(dates, np.mean(values) - np.std(values),
                    np.mean(values) + np.std(values), alpha=0.2)
    plt.title(f'Parameter Evolution: {param}')
    plt.legend()
```

## Advanced Configurations

### Purged Walk-Forward

Add gaps to prevent look-ahead bias in overlapping features:

```python
config = WalkForwardConfig(
    train_period='2Y',
    test_period='6M',
    step='3M',
    gap='20D',  # 20-day gap between train and test
    embargo='5D',  # Additional embargo at end of test
)
```

### Combinatorial Purged Cross-Validation

```python
from walk_forward import CombinatorialPurgedCV

cv = CombinatorialPurgedCV(
    n_splits=5,
    n_test_splits=2,
    purge_gap=10,
    embargo_gap=5
)

for train_idx, test_idx in cv.split(dates):
    # Train on train_idx, test on test_idx
    pass
```

## Best Practices

### 1. Choose Appropriate Windows

```python
# Rule of thumb:
# - Train period: 2-5x test period
# - Test period: Long enough for statistical significance
# - Step: 50-100% of test period

config = WalkForwardConfig(
    train_period='3Y',    # 3 years training
    test_period='1Y',     # 1 year testing
    step='6M',            # Step every 6 months
)
```

### 2. Track Performance Decay

```python
def analyze_decay(results: WalkForwardResult):
    """Check if OOS performance decays over time."""
    oos_sharpes = [w.oos_sharpe for w in results.windows]
    window_nums = np.arange(len(oos_sharpes))
    
    # Linear regression
    slope, intercept = np.polyfit(window_nums, oos_sharpes, 1)
    
    if slope < -0.1:
        print("WARNING: OOS performance declining over time")
    
    return slope
```

### 3. Multiple Metrics

```python
# Don't just optimize Sharpe
results_sharpe = analyzer.run(strategy_fn, objective='sharpe')
results_calmar = analyzer.run(strategy_fn, objective='calmar')
results_sortino = analyzer.run(strategy_fn, objective='sortino')

# Compare stability across objectives
```

## Integration with Optimization

```python
def full_validation_pipeline():
    """Complete parameter optimization with walk-forward validation."""
    
    # 1. Initial optimization on first 70% of data
    train_end = pd.Timestamp('2020-12-31', tz='utc')
    
    optimizer = GridSearchOptimizer(param_space)
    opt_results = optimizer.optimize(
        lambda p: run_strategy(p, end=train_end)
    )
    
    # 2. Walk-forward validation on full period
    wf_config = WalkForwardConfig(
        train_period='2Y',
        test_period='6M',
        step='3M'
    )
    
    wf_analyzer = WalkForwardAnalyzer(wf_config, param_space)
    wf_results = wf_analyzer.run(
        run_strategy,
        start='2010-01-01',
        end='2023-12-31'
    )
    
    # 3. Final out-of-sample test
    final_test = run_strategy(
        opt_results.best_params,
        start='2021-01-01',
        end='2023-12-31'
    )
    
    return {
        'optimization': opt_results,
        'walk_forward': wf_results,
        'final_test': final_test
    }
```

## References

See `references/wf_methodology.md` for theoretical background.
See `references/sample_size.md` for statistical significance guidelines.
