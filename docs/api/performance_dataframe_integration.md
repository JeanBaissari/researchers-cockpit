# Zipline Performance DataFrame Integration

> Comprehensive guide to integrating with Zipline-Reloaded's Performance DataFrame (38+ columns) in The Researcher's Cockpit

**Source:** [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
**Version:** Zipline-Reloaded v3.0+  
**Last Updated:** 2026-01-28

---

## Table of Contents

1. [Overview](#overview)
2. [Performance DataFrame Structure](#performance-dataframe-structure)
3. [All 38+ Columns](#all-38-columns)
4. [Project Integration Points](#project-integration-points)
5. [Usage Patterns](#usage-patterns)
6. [Edge Cases & Handling](#edge-cases--handling)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Overview

Zipline-Reloaded's `run_algorithm()` function returns a **Performance DataFrame** containing time-series metrics recorded throughout the backtest. This DataFrame is the primary interface for accessing backtest results and contains 38+ columns covering portfolio values, positions, transactions, benchmark comparisons, and risk metrics.

### Key Characteristics

- **Index**: DatetimeIndex (timezone-aware, typically UTC)
- **Shape**: One row per trading session/bar
- **Columns**: 38+ columns (varies by metrics_set)
- **Data Types**: Mix of float64, object (lists/dicts), and int64
- **Persistence**: Saved as `performance.pkl` in results directory

### Integration Flow

```
Zipline run_algorithm()
    ↓
Performance DataFrame (38+ columns)
    ↓
lib/backtest/results.py::save_results()
    ↓
lib/backtest/results_serialization.py
    ├── normalize_performance_dataframe() → Timezone normalization
    ├── extract_positions_dataframe() → Flatten positions
    ├── extract_transactions_dataframe() → Flatten transactions
    ├── save_performance_dataframe() → Pickle for later loading
    └── calculate_and_save_metrics() → Enhanced metrics calculation
    ↓
Results Directory
    ├── performance.pkl (full DataFrame)
    ├── returns.csv (extracted returns)
    ├── positions.csv (flattened positions)
    ├── transactions.csv (flattened transactions)
    └── metrics.json (calculated metrics)
```

---

## Performance DataFrame Structure

### Basic Access

```python
from zipline import run_algorithm

# Run backtest
perf = run_algorithm(
    start=pd.Timestamp('2020-01-01', tz='UTC'),
    end=pd.Timestamp('2024-01-01', tz='UTC'),
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    bundle='yahoo_btc_daily'
)

# Access DataFrame properties
print(f"Shape: {perf.shape}")  # (num_sessions, num_columns)
print(f"Columns: {len(perf.columns)}")  # 38+ columns
print(f"Index: {perf.index}")  # DatetimeIndex
print(f"Date range: {perf.index[0]} to {perf.index[-1]}")
```

### Column Categories

The Performance DataFrame columns are organized into categories:

1. **Portfolio Value Columns** (7 columns)
2. **Position Columns** (6 columns)
3. **Transaction Columns** (2 columns)
4. **Benchmark Columns** (9 columns)
5. **Risk Metrics Columns** (5 columns)
6. **Custom Metrics Columns** (variable, from `record()`)
7. **Additional Columns** (9+ columns)

**Total: 38+ columns** (varies by metrics_set and custom metrics)

---

## All 38+ Columns

### Portfolio Value Columns (7)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `portfolio_value` | float64 | Total portfolio value (cash + positions) | No* |
| `starting_value` | float64 | Portfolio value at period start | No* |
| `ending_value` | float64 | Portfolio value at period end | No* |
| `starting_cash` | float64 | Cash balance at period start | No* |
| `ending_cash` | float64 | Cash balance at period end | No* |
| `pnl` | float64 | Profit and loss for the period | No* |
| `returns` | float64 | Period returns (ending_value / starting_value - 1) | No* |
| `capital_used` | float64 | Cash flow (capital in/out) for the period | No* |

**Note:** Columns marked with `*` may be missing when `metrics_set='none'` is used (common for FOREX strategies). The project automatically reconstructs `portfolio_value` and `returns` from transactions/positions.

### Position Columns (6)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `positions` | object | List of position dictionaries (one per asset) | No* |
| `gross_leverage` | float64 | Gross leverage ratio (total exposure / portfolio_value) | No* |
| `net_leverage` | float64 | Net leverage ratio (net exposure / portfolio_value) | No* |
| `long_value` | float64 | Total value of long positions | No* |
| `short_value` | float64 | Total value of short positions | No* |
| `long_exposure` | float64 | Long exposure amount | No* |
| `short_exposure` | float64 | Short exposure amount | No* |

**Note:** `positions` column contains list of dicts with keys: `sid`, `amount`, `cost_basis`, `last_sale_price`.

### Transaction Columns (2)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `orders` | object | List of orders placed this period | No* |
| `transactions` | object | List of executed transactions (fills) this period | No* |

**Note:** `transactions` column contains list of dicts with keys: `sid`, `amount`, `price`, `commission`, `order_id`, `dt`.

### Benchmark Columns (9)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `benchmark_period_return` | float64 | Benchmark return for the period | No* |
| `algorithm_period_return` | float64 | Algorithm return for the period | No* |
| `alpha` | float64 | Alpha vs benchmark (Jensen's alpha) | No* |
| `beta` | float64 | Beta vs benchmark (market exposure) | No* |
| `benchmark_volatility` | float64 | Benchmark volatility | No* |
| `algorithm_volatility` | float64 | Algorithm volatility | No* |
| `treasury_period_return` | float64 | Risk-free rate return | No* |
| `excess_return` | float64 | Algorithm return - benchmark return | No* |
| `information_ratio` | float64 | Excess return / tracking error | No* |

**Note:** Benchmark columns require benchmark symbol to be specified in `run_algorithm()`. Alpha and beta are end-of-simulation values (not time-series).

### Risk Metrics Columns (5)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `sharpe` | float64 | Sharpe ratio (rolling calculation) | No* |
| `sortino` | float64 | Sortino ratio (rolling calculation) | No* |
| `max_drawdown` | float64 | Maximum drawdown (rolling calculation) | No* |
| `max_drawdown_duration` | float64 | Duration of maximum drawdown in days | No* |
| `recovery_time` | float64 | Time to recover from max drawdown in days | No* |

**Note:** These are **rolling calculations** from Zipline's MetricsTracker. For full-period metrics, use `lib/metrics/calculate_metrics()`.

### Additional Columns (9+)

| Column | Type | Description | Always Present |
|--------|------|-------------|----------------|
| `period_label` | object | Period label (e.g., '2020-01-01') | Yes |
| `period_close` | datetime64 | Period close timestamp | Yes |
| `period_open` | datetime64 | Period open timestamp | Yes |
| `capital_base` | float64 | Starting capital | Yes |
| `max_leverage` | float64 | Maximum leverage reached | No* |
| `trading_days` | int64 | Number of trading days | Yes |
| `benchmark_returns` | float64 | Cumulative benchmark returns | No* |
| `algorithm_returns` | float64 | Cumulative algorithm returns | No* |
| `excess_returns` | float64 | Cumulative excess returns | No* |

### Custom Metrics Columns (Variable)

Any values recorded via `record()` function become DataFrame columns:

```python
from zipline.api import record

def handle_data(context, data):
    rsi = calculate_rsi(context, data)
    record(rsi=rsi, signal_strength=0.8)

# Results DataFrame will have 'rsi' and 'signal_strength' columns
```

**Total Column Count:** 38+ base columns + custom metrics

---

## Project Integration Points

### 1. Backtest Execution (`lib/backtest/runner.py`)

The `run_backtest()` function returns the Performance DataFrame:

```python
from lib.backtest import run_backtest

perf, calendar = run_backtest(
    strategy_name='btc_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01',
    capital_base=100000
)

# perf is the Performance DataFrame with 38+ columns
print(f"Columns: {perf.columns.tolist()}")
```

### 2. Results Serialization (`lib/backtest/results_serialization.py`)

#### Normalize Performance DataFrame

```python
from lib.backtest.results_serialization import normalize_performance_dataframe

# Normalize timezone to UTC (timezone-naive)
perf_normalized = normalize_performance_dataframe(perf)
```

**Purpose:** Converts timezone-aware index to timezone-naive UTC for CSV compatibility.

#### Extract Positions DataFrame

```python
from lib.backtest.results_serialization import extract_positions_dataframe

positions_df = extract_positions_dataframe(perf)
# Returns DataFrame with columns: ['sid', 'amount', 'cost_basis', 'last_sale_price']
```

**Purpose:** Flattens nested `positions` column (list of dicts) into tabular format.

#### Extract Transactions DataFrame

```python
from lib.backtest.results_serialization import extract_transactions_dataframe

transactions_df = extract_transactions_dataframe(perf)
# Returns DataFrame with columns: ['sid', 'amount', 'price', 'commission', 'order_id']
```

**Purpose:** Flattens nested `transactions` column (list of dicts) into tabular format.

#### Save Performance DataFrame

```python
from lib.backtest.results_serialization import save_performance_dataframe

save_performance_dataframe(perf, result_dir)
# Saves to: results/{strategy}/{run_id}/performance.pkl
```

**Purpose:** Preserves all Zipline native metrics (alpha, beta, leverage, etc.) that are not available in CSV exports.

### 3. Results Persistence (`lib/backtest/results.py`)

The `save_results()` function orchestrates the entire integration:

```python
from lib.backtest import save_results

result_dir = save_results(
    strategy_name='btc_sma_cross',
    perf=perf,  # Performance DataFrame
    params=params,
    trading_calendar=calendar
)
```

**Creates:**
- `performance.pkl` - Full Performance DataFrame (38+ columns)
- `returns.csv` - Extracted returns column
- `positions.csv` - Flattened positions
- `transactions.csv` - Flattened transactions
- `metrics.json` - Calculated metrics (using `lib/metrics/`)

### 4. Metrics Calculation (`lib/backtest/results_serialization.py`)

The `calculate_and_save_metrics()` function:

1. **Extracts returns** from Performance DataFrame (or reconstructs if missing)
2. **Reconstructs portfolio_value** if `metrics_set='none'` was used
3. **Calculates comprehensive metrics** using `lib/metrics/calculate_metrics()`
4. **Adds columns to perf DataFrame** for plotting (portfolio_value, returns)

```python
from lib.backtest.results_serialization import calculate_and_save_metrics

metrics = calculate_and_save_metrics(
    perf=perf,
    transactions_df=transactions_df,
    result_dir=result_dir,
    trading_calendar=calendar,
    initial_capital=100000
)
```

### 5. Strategy Validation (`lib/strategy_validation/`)

Walk-forward analysis and Monte Carlo simulation consume the Performance DataFrame (or returns derived from it) to validate strategy robustness.

#### Data flow

```
Zipline run_algorithm() → Performance DataFrame (perf)
    ↓
lib/backtest/runner.run_backtest() → (perf, calendar)
    ↓
lib/strategy_validation/walkforward.py
    ├── _run_period_backtest() runs backtest per period → (perf, _)
    ├── Extract returns: perf["returns"] or perf["portfolio_value"].pct_change()
    ├── calculate_metrics(returns) → period metrics dict
    └── Aggregate periods → in_sample_results, out_sample_results (DataFrames of metrics)
    ↓
lib/strategy_validation/metrics.calculate_walk_forward_efficiency(is_df, oos_df)
lib/strategy_validation/results.save_walk_forward_results(...)
```

#### Walk-forward: perf → returns → metrics

Walk-forward does **not** persist the full Performance DataFrame. For each train/test period it:

1. Runs a backtest via `run_backtest()` and receives `(perf, calendar)`.
2. Derives a **returns** series from `perf`:
   - Prefers `perf["returns"]` when present.
   - If missing (e.g. `metrics_set='none'`), uses `perf["portfolio_value"].pct_change().dropna()`.
   - If both are missing, uses an empty series (metrics will be empty).
3. Calls `lib.metrics.calculate_metrics(returns)` to get a metrics dict (e.g. sharpe, max_drawdown).
4. Aggregates these dicts into in-sample and out-of-sample DataFrames (one row per period).

**Column handling (walk-forward):**

```python
# In lib/strategy_validation/walkforward._run_period_backtest()
if "returns" in perf.columns:
    returns = perf["returns"].dropna()
elif "portfolio_value" in perf.columns:
    pv = perf["portfolio_value"].dropna()
    returns = pv.pct_change().dropna() if len(pv) > 1 else pd.Series(dtype=float)
else:
    returns = pd.Series(dtype=float)
```

So strategy_validation is compatible with both full Zipline metrics and FOREX-style runs where `returns`/`portfolio_value` may be absent until reconstructed elsewhere.

#### Monte Carlo: returns from perf

Monte Carlo does **not** accept the Performance DataFrame directly. Callers must pass a **returns** series, typically taken from a single backtest’s perf:

```python
from lib.backtest import run_backtest
from lib.strategy_validation import monte_carlo

perf, _ = run_backtest(strategy_name="btc_sma_cross", start_date="2020-01-01", end_date="2024-01-01")

# Extract returns from Performance DataFrame (same convention as walk-forward)
if "returns" in perf.columns:
    returns = perf["returns"].dropna()
elif "portfolio_value" in perf.columns:
    pv = perf["portfolio_value"].dropna()
    returns = pv.pct_change().dropna() if len(pv) > 1 else pd.Series(dtype=float)
else:
    returns = pd.Series(dtype=float)

result = monte_carlo(returns, n_simulations=1000)
```

#### Outputs

- **Walk-forward:** Saves `in_sample_results.csv`, `out_sample_results.csv`, and `robustness_score.json` in a timestamped directory under `results/{strategy_name}/`. It does **not** save `performance.pkl`; only the aggregated metrics per period.
- **Monte Carlo:** Caller may pass `returns` from any source; if from perf, use the extraction pattern above. Results (paths, confidence intervals, stats) are typically saved via `save_monte_carlo_results()`.

#### Summary

| Component            | Consumes perf? | Consumes returns from perf? | Saves perf? |
|---------------------|----------------|-----------------------------|-------------|
| Walk-forward         | Yes (via run_backtest) | Yes (derived in _run_period_backtest) | No (metrics only) |
| Monte Carlo          | No             | Yes (caller passes returns) | No         |
| Walk-forward results | —              | —                           | CSV/JSON only |

### 6. Report Generation (`lib/report/sections.py`)

The report generation system loads and uses the Performance DataFrame:

```python
from lib.report.sections import load_performance_dataframe, build_zipline_metrics_section

# Load from results directory
perf = load_performance_dataframe(results_dir)

# Build report section using Zipline metrics
section = build_zipline_metrics_section(results_dir)
# Extracts: alpha, beta, leverage, benchmark comparison, rolling metrics
```

**Functions:**
- `load_performance_dataframe()` - Loads from `performance.pkl` or reconstructs from `returns.csv`
- `build_zipline_metrics_section()` - Builds markdown section with Zipline native metrics
- `build_time_series_summary()` - Summarizes rolling metrics over backtest period

---

## Usage Patterns

### Pattern 1: Basic Access

```python
from lib.backtest import run_backtest, save_results

# Run backtest
perf, calendar = run_backtest('btc_sma_cross', start_date='2020-01-01')

# Access columns
final_value = perf['portfolio_value'].iloc[-1]
total_return = perf['returns'].sum()
max_dd = perf['max_drawdown'].min()

# Save results (handles all integration)
save_results('btc_sma_cross', perf, params, calendar)
```

### Pattern 2: Direct DataFrame Manipulation

```python
# Filter by date range
perf_filtered = perf.loc['2021-01-01':'2022-01-01']

# Calculate custom metrics
perf['cumulative_returns'] = (1 + perf['returns']).cumprod()
perf['drawdown'] = perf['portfolio_value'] / perf['portfolio_value'].cummax() - 1

# Plot multiple columns
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1)
axes[0].plot(perf.index, perf['portfolio_value'])
axes[1].plot(perf.index, perf['returns'].cumsum())
```

### Pattern 3: Extract and Analyze Positions

```python
from lib.backtest.results_serialization import extract_positions_dataframe

# Extract positions
positions_df = extract_positions_dataframe(perf)

# Analyze position sizes
position_sizes = positions_df.groupby('sid')['amount'].sum()
avg_position_value = positions_df.groupby('sid')['cost_basis'].mean()

# Find largest positions
largest_positions = positions_df.nlargest(10, 'cost_basis')
```

### Pattern 4: Extract and Analyze Transactions

```python
from lib.backtest.results_serialization import extract_transactions_dataframe

# Extract transactions
transactions_df = extract_transactions_dataframe(perf)

# Calculate trade statistics
total_trades = len(transactions_df)
total_volume = transactions_df['amount'].abs().sum()
total_commission = transactions_df['commission'].sum()

# Group by asset
trades_by_asset = transactions_df.groupby('sid').size()
```

### Pattern 5: Load from Results Directory

```python
from lib.report.sections import load_performance_dataframe
from pathlib import Path

# Load saved Performance DataFrame
results_dir = Path('results/btc_sma_cross/latest')
perf = load_performance_dataframe(results_dir)

# Access all 38+ columns
if 'alpha' in perf.columns:
    final_alpha = perf['alpha'].iloc[-1]
if 'gross_leverage' in perf.columns:
    max_leverage = perf['gross_leverage'].max()
```

### Pattern 6: Strategy Validation (Walk-Forward and Monte Carlo)

```python
from lib.backtest import run_backtest
from lib.strategy_validation import walk_forward, monte_carlo

# Walk-forward: perf is used internally via run_backtest() per period
result = walk_forward(
    strategy_name="btc_sma_cross",
    start_date="2020-01-01",
    end_date="2024-01-01",
    train_period=252,
    test_period=63,
)
# result["in_sample_results"] and result["out_sample_results"] are DataFrames of metrics per period

# Monte Carlo: extract returns from a single backtest perf, then pass to monte_carlo
perf, _ = run_backtest("btc_sma_cross", start_date="2020-01-01", end_date="2024-01-01")
returns = perf["returns"].dropna() if "returns" in perf.columns else perf["portfolio_value"].pct_change().dropna()
mc_result = monte_carlo(returns, n_simulations=1000)
```

### Pattern 7: Custom Metrics Analysis

```python
# If strategy recorded custom metrics via record()
if 'rsi' in perf.columns:
    rsi_series = perf['rsi'].dropna()
    print(f"RSI mean: {rsi_series.mean():.2f}")
    print(f"RSI std: {rsi_series.std():.2f}")

# Plot custom metrics
if 'signal_strength' in perf.columns:
    perf['signal_strength'].plot(title='Signal Strength Over Time')
```

---

## Edge Cases & Handling

### Case 1: Missing Columns (metrics_set='none')

**Problem:** When `metrics_set='none'` is used (common for FOREX strategies), `returns` and `portfolio_value` columns may be missing.

**Solution:** The project automatically reconstructs these columns:

```python
# In lib/backtest/results_serialization.py::calculate_and_save_metrics()

if 'returns' not in perf.columns:
    # Reconstruct portfolio_value from transactions
    portfolio_value = calculate_portfolio_value_from_transactions(
        perf, transactions_df, positions_df, initial_capital
    )
    # Calculate returns from portfolio_value
    returns = portfolio_value.pct_change().dropna()
    # Add to perf DataFrame
    perf['portfolio_value'] = portfolio_value
    perf['returns'] = returns
```

**Usage:**
```python
# Safe access pattern
if 'portfolio_value' in perf.columns:
    final_value = perf['portfolio_value'].iloc[-1]
else:
    # Will be reconstructed during save_results()
    pass
```

### Case 2: Timezone Handling

**Problem:** Zipline returns timezone-aware DatetimeIndex, but CSV exports require timezone-naive.

**Solution:** `normalize_performance_dataframe()` converts to UTC and removes timezone:

```python
from lib.backtest.results_serialization import normalize_performance_dataframe

perf_normalized = normalize_performance_dataframe(perf)
# Index is now timezone-naive UTC
```

### Case 3: Nested Data Structures

**Problem:** `positions` and `transactions` columns contain lists of dicts, not tabular data.

**Solution:** Use extraction functions:

```python
from lib.backtest.results_serialization import (
    extract_positions_dataframe,
    extract_transactions_dataframe
)

# Flatten nested structures
positions_df = extract_positions_dataframe(perf)
transactions_df = extract_transactions_dataframe(perf)
```

### Case 4: Missing Benchmark Columns

**Problem:** Benchmark columns (alpha, beta, benchmark_period_return) are only present if benchmark is specified.

**Solution:** Check for column existence:

```python
# Safe access
if 'alpha' in perf.columns and 'beta' in perf.columns:
    alpha = perf['alpha'].iloc[-1]
    beta = perf['beta'].iloc[-1]
else:
    print("Benchmark not specified in backtest")
```

### Case 5: Rolling vs Full-Period Metrics

**Problem:** Zipline's `sharpe`, `sortino`, `max_drawdown` are rolling calculations, not full-period.

**Solution:** Use `lib/metrics/calculate_metrics()` for full-period metrics:

```python
from lib.metrics import calculate_metrics
from lib.backtest.results_serialization import extract_transactions_dataframe

# Zipline rolling metrics (time-series)
rolling_sharpe = perf['sharpe']  # Rolling calculation

# Full-period metrics (single value)
transactions_df = extract_transactions_dataframe(perf)
metrics = calculate_metrics(
    returns=perf['returns'],
    transactions=transactions_df
)
full_period_sharpe = metrics['sharpe']  # Full-period calculation
```

---

## Best Practices

### 1. Always Check Column Existence

```python
# ✅ GOOD
if 'portfolio_value' in perf.columns:
    final_value = perf['portfolio_value'].iloc[-1]

# ❌ BAD
final_value = perf['portfolio_value'].iloc[-1]  # May raise KeyError
```

### 2. Use Project Functions for Extraction

```python
# ✅ GOOD - Use project functions
from lib.backtest.results_serialization import extract_positions_dataframe
positions_df = extract_positions_dataframe(perf)

# ❌ BAD - Manual extraction (error-prone)
positions_list = []
for date, positions in perf['positions'].items():
    # Manual flattening...
```

### 3. Normalize Timezone Before CSV Export

```python
# ✅ GOOD
from lib.backtest.results_serialization import normalize_performance_dataframe
perf_normalized = normalize_performance_dataframe(perf)
perf_normalized.to_csv('results.csv')

# ❌ BAD - Timezone-aware index causes issues
perf.to_csv('results.csv')  # May have timezone issues
```

### 4. Use save_results() for Complete Integration

```python
# ✅ GOOD - Complete integration
from lib.backtest import save_results
result_dir = save_results(strategy_name, perf, params, calendar)

# ❌ BAD - Manual saving (misses integration features)
perf.to_pickle('performance.pkl')  # Missing normalization, extraction, etc.
```

### 5. Load from Results Directory When Available

```python
# ✅ GOOD - Load from saved results
from lib.report.sections import load_performance_dataframe
perf = load_performance_dataframe(results_dir)

# ❌ BAD - Re-run backtest unnecessarily
perf, _ = run_backtest(...)  # Wastes time if results already exist
```

### 6. Combine Zipline and Project Metrics

```python
# ✅ GOOD - Best of both worlds
# Zipline metrics for time-series
equity_curve = perf['portfolio_value']
rolling_sharpe = perf['sharpe']

# Project metrics for comprehensive analysis
from lib.metrics import calculate_metrics
metrics = calculate_metrics(returns=perf['returns'], transactions=transactions_df)
full_period_sharpe = metrics['sharpe']
```

### 7. Handle Missing Columns Gracefully

```python
# ✅ GOOD - Graceful degradation
def get_final_value(perf):
    if 'portfolio_value' in perf.columns:
        return perf['portfolio_value'].iloc[-1]
    elif 'ending_value' in perf.columns:
        return perf['ending_value'].iloc[-1]
    else:
        # Reconstruct from transactions
        return reconstruct_portfolio_value(perf)
```

---

## Examples

### Example 1: Complete Backtest Workflow

```python
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params

# Run backtest
perf, calendar = run_backtest(
    strategy_name='btc_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01',
    capital_base=100000
)

# Access Performance DataFrame columns
print(f"Final portfolio value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
print(f"Total return: {perf['returns'].sum():.2%}")
print(f"Max drawdown: {perf['max_drawdown'].min():.2%}")

# Save results (handles all integration)
params = load_strategy_params('btc_sma_cross')
result_dir = save_results('btc_sma_cross', perf, params, calendar)

print(f"Results saved to: {result_dir}")
```

### Example 2: Analyze Positions Over Time

```python
from lib.backtest.results_serialization import extract_positions_dataframe
import pandas as pd

# Extract positions
positions_df = extract_positions_dataframe(perf)

# Analyze position changes
position_changes = positions_df.groupby('sid')['amount'].diff().abs()
total_position_changes = position_changes.sum()

# Find most traded assets
most_traded = positions_df.groupby('sid').size().nlargest(10)
print("Most traded assets:")
print(most_traded)
```

### Example 3: Compare Zipline vs Project Metrics

```python
from lib.metrics import calculate_metrics
from lib.backtest.results_serialization import extract_transactions_dataframe

# Zipline rolling metrics
zipline_sharpe = perf['sharpe'].iloc[-1]  # Final rolling Sharpe
zipline_max_dd = perf['max_drawdown'].min()  # Rolling max drawdown

# Project full-period metrics
transactions_df = extract_transactions_dataframe(perf)
metrics = calculate_metrics(
    returns=perf['returns'],
    transactions=transactions_df
)
project_sharpe = metrics['sharpe']  # Full-period Sharpe
project_max_dd = metrics['max_drawdown']  # Full-period max drawdown

# Compare
print(f"Zipline Sharpe (rolling): {zipline_sharpe:.3f}")
print(f"Project Sharpe (full-period): {project_sharpe:.3f}")
print(f"Zipline Max DD (rolling): {zipline_max_dd:.2%}")
print(f"Project Max DD (full-period): {project_max_dd:.2%}")
```

### Example 4: Load and Analyze Saved Results

```python
from lib.report.sections import load_performance_dataframe
from pathlib import Path

# Load saved Performance DataFrame
results_dir = Path('results/btc_sma_cross/latest')
perf = load_performance_dataframe(results_dir)

# Access all columns
print(f"Available columns: {len(perf.columns)}")
print(f"Columns: {perf.columns.tolist()}")

# Analyze benchmark comparison
if 'alpha' in perf.columns and 'beta' in perf.columns:
    print(f"Alpha: {perf['alpha'].iloc[-1]:.4f}")
    print(f"Beta: {perf['beta'].iloc[-1]:.3f}")

# Analyze leverage
if 'gross_leverage' in perf.columns:
    print(f"Max gross leverage: {perf['gross_leverage'].max():.3f}")
    print(f"Avg gross leverage: {perf['gross_leverage'].mean():.3f}")
```

### Example 5: Walk-Forward and Monte Carlo with Performance DataFrame

```python
import pandas as pd
from lib.backtest import run_backtest
from lib.strategy_validation import walk_forward, monte_carlo

# Walk-forward uses perf internally (run_backtest per period); no need to pass perf
wf_result = walk_forward(
    strategy_name="btc_sma_cross",
    start_date="2020-01-01",
    end_date="2023-12-31",
    train_period=252,
    test_period=63,
)
print(f"Efficiency: {wf_result['robustness']['efficiency']:.4f}")
print(f"Consistency: {wf_result['robustness']['consistency']:.2%}")

# Monte Carlo: get returns from one backtest's perf
perf, _ = run_backtest("btc_sma_cross", start_date="2020-01-01", end_date="2024-01-01")
if "returns" in perf.columns:
    returns = perf["returns"].dropna()
elif "portfolio_value" in perf.columns:
    pv = perf["portfolio_value"].dropna()
    returns = pv.pct_change().dropna() if len(pv) > 1 else pd.Series(dtype=float)
else:
    returns = pd.Series(dtype=float)

mc_result = monte_carlo(returns, n_simulations=1000, initial_value=100000)
print(f"Final value p5: {mc_result['confidence_intervals']['p5']:,.0f}")
print(f"Final value p95: {mc_result['confidence_intervals']['p95']:,.0f}")
```

### Example 6: Custom Metrics Analysis

```python
# If strategy recorded custom metrics
if 'rsi' in perf.columns:
    rsi = perf['rsi'].dropna()
    
    # Find overbought/oversold periods
    overbought = (rsi > 70).sum()
    oversold = (rsi < 30).sum()
    
    print(f"Overbought periods: {overbought}")
    print(f"Oversold periods: {oversold}")
    
    # Plot custom metrics
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(perf.index, perf['portfolio_value'])
    axes[0].set_title('Equity Curve')
    axes[1].plot(perf.index, perf['rsi'])
    axes[1].axhline(y=70, color='r', linestyle='--', label='Overbought')
    axes[1].axhline(y=30, color='g', linestyle='--', label='Oversold')
    axes[1].set_title('RSI')
    plt.tight_layout()
    plt.savefig('custom_metrics_analysis.png')
```

---

## References

### Official Documentation

- [Zipline-Reloaded Repository](https://github.com/stefan-jansen/zipline-reloaded)
- [Zipline Documentation](https://zipline.ml4trading.io)

### Project Documentation

- `docs/api/metrics_inventory.md` - Complete Zipline metrics system inventory
- `docs/api/backtest.md` - Backtest execution API
- `docs/api/metrics.md` - Project metrics API
- `lib/backtest/results_serialization.py` - Integration implementation
- `lib/report/sections.py` - Report generation using Performance DataFrame

### Related Components

- `lib/backtest/runner.py` - Backtest execution
- `lib/backtest/results.py` - Results orchestration
- `lib/metrics/` - Enhanced metrics calculation
- `lib/plots/` - Visualization utilities
- `lib/strategy_validation/` - Walk-forward and Monte Carlo validation (consumes perf via run_backtest and returns derived from perf)

---

## Version History

- **2026-01-28**: Initial documentation created
- **2026-01-28**: Added lib/strategy_validation integration (walk-forward, Monte Carlo, returns extraction from perf)
- **Source**: Zipline-Reloaded v3.0+ (stefan-jansen/zipline-reloaded)
- **Status**: Complete integration guide for Performance DataFrame (38+ columns)

---

**Note:** This documentation is based on Zipline-Reloaded v3.0+. For legacy Quantopian zipline patterns, refer to migration guides. Always use Zipline-Reloaded patterns exclusively.
