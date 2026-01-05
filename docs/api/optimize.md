# Optimize API

Parameter optimization with grid search, random search, and overfit detection.

**Location:** `lib/optimize.py`
**CLI Equivalent:** `scripts/run_optimization.py`

---

## grid_search()

Perform exhaustive grid search over parameter combinations.

**Signature:**
```python
def grid_search(
    strategy_name: str,
    param_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    objective: str = 'sharpe',
    train_pct: float = 0.7,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy to optimize |
| `param_grid` | Dict | required | Parameter names to value lists |
| `start_date` | str | required | Start date `YYYY-MM-DD` |
| `end_date` | str | required | End date `YYYY-MM-DD` |
| `objective` | str | `'sharpe'` | Metric to optimize |
| `train_pct` | float | 0.7 | Percentage for training (70%) |
| `capital_base` | float | None | Starting capital |
| `bundle` | str | None | Bundle name |
| `asset_class` | str | None | Asset class hint |

**Objective Options:** `'sharpe'`, `'sortino'`, `'total_return'`, `'calmar'`

**Returns:** `pd.DataFrame` - All combinations with train/test metrics

**Example:**
```python
from lib.optimize import grid_search

results = grid_search(
    strategy_name='spy_sma_cross',
    param_grid={
        'strategy.fast_period': [5, 10, 15, 20],
        'strategy.slow_period': [30, 50, 100]
    },
    start_date='2020-01-01',
    end_date='2024-01-01',
    objective='sharpe'
)

# View best result
best_idx = results['test_sharpe'].idxmax()
print(results.loc[best_idx])
```

**CLI Equivalent:**
```bash
# Range format: param:start:end:step
python scripts/run_optimization.py --strategy spy_sma_cross \
    --method grid \
    --param strategy.fast_period:5:20:5 \
    --param strategy.slow_period:30:100:20 \
    --objective sharpe

# Discrete format: param:val1,val2,val3
python scripts/run_optimization.py --strategy spy_sma_cross \
    --method grid \
    --param strategy.fast_period:5,10,15,20 \
    --param strategy.slow_period:30,50,100
```

**Output Files:**
```
results/{strategy}/optimization_{timestamp}/
├── grid_results.csv      # All combinations
├── best_params.yaml      # Best parameters
├── overfit_score.json    # Overfit probability
├── in_sample_metrics.json
├── out_sample_metrics.json
└── heatmap_sharpe.png    # If 2 parameters
```

---

## random_search()

Perform randomized search over parameter distributions.

**Signature:**
```python
def random_search(
    strategy_name: str,
    param_distributions: Dict[str, Any],
    n_iter: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    objective: str = 'sharpe',
    train_pct: float = 0.7,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `param_distributions` | Dict | required | Parameter distributions |
| `n_iter` | int | 100 | Number of random iterations |
| `start_date` | str | None | Start date |
| `end_date` | str | None | End date |
| `objective` | str | `'sharpe'` | Metric to optimize |
| `train_pct` | float | 0.7 | Training percentage |

**Distribution Formats:**
- `list`: Random choice from list
- `np.ndarray`: Random choice from array
- `tuple(min, max)`: Uniform random in range

**Example:**
```python
from lib.optimize import random_search
import numpy as np

results = random_search(
    strategy_name='spy_sma_cross',
    param_distributions={
        'strategy.fast_period': [5, 10, 15, 20, 25],
        'strategy.slow_period': np.arange(30, 150, 10),
        'risk.stop_loss_pct': (0.01, 0.05)  # Uniform range
    },
    n_iter=50,
    start_date='2020-01-01',
    end_date='2024-01-01'
)
```

**CLI Equivalent:**
```bash
python scripts/run_optimization.py --strategy spy_sma_cross \
    --method random \
    --n-iter 50 \
    --param strategy.fast_period:5,10,15,20,25 \
    --param strategy.slow_period:30:150:10
```

---

## split_data()

Split date range into training and testing periods.

**Signature:**
```python
def split_data(
    start: str,
    end: str,
    train_pct: float = 0.7
) -> Tuple[Tuple[str, str], Tuple[str, str]]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | str | required | Start date `YYYY-MM-DD` |
| `end` | str | required | End date `YYYY-MM-DD` |
| `train_pct` | float | 0.7 | Training percentage |

**Returns:** `Tuple[Tuple[str, str], Tuple[str, str]]` - ((train_start, train_end), (test_start, test_end))

**Example:**
```python
from lib.optimize import split_data

train_dates, test_dates = split_data('2020-01-01', '2024-01-01', 0.7)

print(f"Train: {train_dates[0]} to {train_dates[1]}")
print(f"Test: {test_dates[0]} to {test_dates[1]}")
# Train: 2020-01-01 to 2022-10-19
# Test: 2022-10-20 to 2024-01-01
```

---

## calculate_overfit_score()

Calculate probability of overfitting from IS/OOS metrics.

**Signature:**
```python
def calculate_overfit_score(
    in_sample_metric: float,
    out_sample_metric: float,
    n_trials: int
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `in_sample_metric` | float | required | In-sample metric value |
| `out_sample_metric` | float | required | Out-of-sample metric value |
| `n_trials` | int | required | Number of trials tested |

**Returns:**
```python
{
    'efficiency': float,      # OOS/IS ratio
    'pbo': float,            # Probability of backtest overfitting
    'verdict': str,          # 'robust', 'acceptable', 'moderate_overfit', 'high_overfit'
    'in_sample': float,
    'out_sample': float
}
```

**Verdict Thresholds:**

| Efficiency | PBO | Verdict |
|------------|-----|---------|
| >= 0.7 | 0.2 | `robust` |
| 0.5 - 0.7 | 0.4 | `acceptable` |
| 0.3 - 0.5 | 0.6 | `moderate_overfit` |
| < 0.3 | 0.8 | `high_overfit` |

**Example:**
```python
from lib.optimize import calculate_overfit_score

score = calculate_overfit_score(
    in_sample_metric=1.5,   # IS Sharpe
    out_sample_metric=0.8,  # OOS Sharpe
    n_trials=100
)

print(f"Efficiency: {score['efficiency']:.2f}")
print(f"Verdict: {score['verdict']}")
# Efficiency: 0.53
# Verdict: acceptable
```

---

## Parameter Path Notation

Parameters are specified using dot notation to access nested YAML values:

```yaml
# parameters.yaml
strategy:
  fast_period: 10
  slow_period: 50
risk:
  stop_loss_pct: 0.02
```

```python
# Dot notation
param_grid = {
    'strategy.fast_period': [5, 10, 15],
    'strategy.slow_period': [30, 50, 100],
    'risk.stop_loss_pct': [0.01, 0.02, 0.03]
}
```

---

## Best Practices

### Avoid Overfitting

1. **Use sufficient OOS period**: At least 20-30% of data
2. **Limit parameter combinations**: More trials = higher overfit risk
3. **Check efficiency**: OOS/IS ratio should be > 0.5
4. **Use walk-forward validation**: See [validate.md](validate.md)

### Parameter Selection

1. **Start with few parameters**: 2-3 most important
2. **Use coarse grid first**: Then refine around best values
3. **Consider random search**: For large parameter spaces
4. **Document rationale**: Why each parameter range was chosen

---

## See Also

- [Validate API](validate.md) - Walk-forward analysis
- [Backtest API](backtest.md) - Running backtests
- [Config API](config.md) - Strategy parameters
