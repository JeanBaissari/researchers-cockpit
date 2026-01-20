# Validate API

Walk-forward analysis and Monte Carlo simulation for strategy validation.

**Location:** `lib/validate/`

**Note:** This module is for **strategy validation** (walk-forward analysis, Monte Carlo simulation). For **data validation** (OHLCV data quality checks), see [Validation API](validation.md) (`lib/validation/`).

---

## walk_forward()

Perform walk-forward analysis with rolling train/test windows.

**Signature:**
```python
def walk_forward(
    strategy_name: str,
    start_date: str,
    end_date: str,
    train_period: int = 252,
    test_period: int = 63,
    optimize_params: Optional[Dict[str, Any]] = None,
    objective: str = 'sharpe',
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `start_date` | str | required | Start date `YYYY-MM-DD` |
| `end_date` | str | required | End date `YYYY-MM-DD` |
| `train_period` | int | 252 | Training period in days (~1 year) |
| `test_period` | int | 63 | Testing period in days (~3 months) |
| `optimize_params` | Dict | None | Parameter grid for optimization |
| `objective` | str | `'sharpe'` | Optimization objective |
| `capital_base` | float | None | Starting capital |
| `bundle` | str | None | Bundle name |
| `asset_class` | str | None | Asset class hint |

**Returns:**
```python
{
    'in_sample_results': pd.DataFrame,   # IS metrics per period
    'out_sample_results': pd.DataFrame,  # OOS metrics per period
    'robustness': Dict[str, float],      # Efficiency, consistency scores
    'result_dir': Path                   # Path to saved results
}
```

**Example:**
```python
from lib.validate import walk_forward

results = walk_forward(
    strategy_name='spy_sma_cross',
    start_date='2018-01-01',
    end_date='2024-01-01',
    train_period=252,  # 1 year training
    test_period=63     # 3 months testing
)

print(f"Walk-forward efficiency: {results['robustness']['efficiency']:.2f}")
print(f"Consistency: {results['robustness']['consistency']:.1%}")

# Access per-period results
for _, row in results['out_sample_results'].iterrows():
    print(f"Period {row['period']}: Sharpe={row['sharpe']:.2f}")
```

**Walk-Forward Process:**
```
|------ Train 1 ------|-- Test 1 --|
                      |------ Train 2 ------|-- Test 2 --|
                                            |------ Train 3 ------|-- Test 3 --|
```

**Output Files:**
```
results/{strategy}/walkforward_{timestamp}/
├── in_sample_results.csv
├── out_sample_results.csv
└── robustness_score.json
```

---

## monte_carlo()

Perform Monte Carlo simulation by shuffling trade returns.

**Signature:**
```python
def monte_carlo(
    returns: pd.Series,
    n_simulations: int = 1000,
    confidence_levels: List[float] = [0.05, 0.50, 0.95],
    initial_value: float = 100000.0
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Daily returns series |
| `n_simulations` | int | 1000 | Number of simulation paths |
| `confidence_levels` | List[float] | [0.05, 0.50, 0.95] | Percentile levels |
| `initial_value` | float | 100000.0 | Initial portfolio value |

**Returns:**
```python
{
    'simulation_paths': pd.DataFrame,      # All simulation paths
    'confidence_intervals': Dict[str, float],  # Percentile values
    'final_value_stats': Dict[str, float],     # Mean, std, min, max
    'n_simulations': int
}
```

**Example:**
```python
from lib.validate import monte_carlo
from lib.backtest import run_backtest

# Run backtest first
perf, _ = run_backtest('spy_sma_cross')
returns = perf['returns'].dropna()

# Monte Carlo simulation
mc_results = monte_carlo(
    returns,
    n_simulations=1000,
    initial_value=100000
)

print(f"5th percentile: ${mc_results['confidence_intervals']['p5']:,.0f}")
print(f"Median: ${mc_results['confidence_intervals']['p50']:,.0f}")
print(f"95th percentile: ${mc_results['confidence_intervals']['p95']:,.0f}")
```

**Output Files:**
```
results/{strategy}/montecarlo_{timestamp}/
├── simulation_paths.csv
├── confidence_intervals.json
├── final_value_stats.json
└── distribution.png
```

---

## calculate_overfit_probability()

Calculate probability of overfitting (PBO).

**Signature:**
```python
def calculate_overfit_probability(
    in_sample_sharpe: float,
    out_sample_sharpe: float,
    n_trials: int
) -> float
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `in_sample_sharpe` | float | required | In-sample Sharpe ratio |
| `out_sample_sharpe` | float | required | Out-of-sample Sharpe ratio |
| `n_trials` | int | required | Number of trials tested |

**Returns:** `float` - Probability of overfitting (0-1)

**Example:**
```python
from lib.validate import calculate_overfit_probability

pbo = calculate_overfit_probability(
    in_sample_sharpe=1.5,
    out_sample_sharpe=0.8,
    n_trials=100
)

print(f"Probability of overfitting: {pbo:.0%}")
# Probability of overfitting: 40%
```

---

## calculate_walk_forward_efficiency()

Calculate walk-forward efficiency and consistency metrics.

**Signature:**
```python
def calculate_walk_forward_efficiency(
    in_sample_metrics: pd.DataFrame,
    out_sample_metrics: pd.DataFrame
) -> Dict[str, float]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `in_sample_metrics` | pd.DataFrame | required | IS metrics per period |
| `out_sample_metrics` | pd.DataFrame | required | OOS metrics per period |

**Returns:**
```python
{
    'efficiency': float,       # OOS/IS Sharpe ratio
    'consistency': float,      # % of periods with positive OOS Sharpe
    'avg_is_sharpe': float,    # Average IS Sharpe
    'avg_oos_sharpe': float,   # Average OOS Sharpe
    'std_oos_sharpe': float,   # Std dev of OOS Sharpe
    'n_periods': int           # Number of periods
}
```

**Interpretation:**

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Efficiency | >= 0.7 | 0.5-0.7 | < 0.5 |
| Consistency | >= 0.7 | 0.5-0.7 | < 0.5 |

---

## Validation Best Practices

### Walk-Forward Analysis

1. **Sufficient data**: At least 3-4 complete cycles
2. **Realistic train/test split**:
   - Train: 252 days (1 year)
   - Test: 63 days (3 months)
3. **No future information leakage**

### Monte Carlo Simulation

1. **Sufficient simulations**: At least 1000 paths
2. **Focus on tail risk**: Look at 5th percentile
3. **Compare to actual results**: Median should be close

### Interpreting Results

| Scenario | Efficiency | Consistency | Assessment |
|----------|------------|-------------|------------|
| Robust | >= 0.7 | >= 70% | Ready for paper trading |
| Acceptable | 0.5-0.7 | 50-70% | Consider refinement |
| Overfitted | < 0.5 | < 50% | Needs simplification |

---

## Example Workflow

```python
from lib.backtest import run_backtest
from lib.validate import walk_forward, monte_carlo

# 1. Run walk-forward analysis
wf_results = walk_forward(
    strategy_name='spy_sma_cross',
    start_date='2018-01-01',
    end_date='2024-01-01'
)

efficiency = wf_results['robustness']['efficiency']
consistency = wf_results['robustness']['consistency']

print(f"Efficiency: {efficiency:.2f}")
print(f"Consistency: {consistency:.1%}")

# 2. If walk-forward passes, run Monte Carlo
if efficiency > 0.5 and consistency > 0.5:
    perf, _ = run_backtest('spy_sma_cross')
    mc_results = monte_carlo(perf['returns'].dropna())

    p5 = mc_results['confidence_intervals']['p5']
    print(f"5th percentile final value: ${p5:,.0f}")
```

---

## See Also

- [Optimize API](optimize.md) - Parameter optimization
- [Metrics API](metrics.md) - Performance metrics
- [Backtest API](backtest.md) - Running backtests
