# Plots API

Visualization utilities for backtest results analysis.

Provides comprehensive plotting functions for equity curves, drawdown charts, monthly returns, trade analysis, and rolling metrics.

**Location:** `lib/plots/`

**Note:** This module requires `matplotlib` and `seaborn` as optional dependencies. If these packages are not installed, plotting functions will silently return without generating plots.

---

## Overview

The `lib/plots` package provides visualization utilities for analyzing backtest results. It follows the Single Responsibility Principle by focusing solely on visualization, making it reusable across all analysis workflows.

**Key Features:**
- Equity curve and drawdown visualization
- Monthly returns heatmap
- Trade analysis (win/loss distribution)
- Rolling metrics (Sharpe, Sortino)
- Batch plotting with `plot_all()`
- Automatic figure saving
- Non-interactive backend (Agg) for server environments

**Supported Plot Types:**
1. **Equity Curve** - Portfolio value over time
2. **Drawdown Chart** - Underwater plot showing drawdown periods
3. **Monthly Returns** - Heatmap of monthly returns by year
4. **Trade Analysis** - Win/loss distribution and cumulative trade returns
5. **Rolling Metrics** - Rolling Sharpe and Sortino ratios over time

---

## Installation/Dependencies

**Required:**
- `pandas` - For data handling
- `numpy` - For numerical operations

**Optional (for plotting):**
- `matplotlib` - For plotting (uses 'Agg' backend for non-interactive environments)
- `seaborn` - For heatmap visualization (monthly returns)

**Note:** If matplotlib is not available, all plotting functions will silently return without generating plots. This allows the codebase to function without visualization dependencies.

---

## Quick Start

```python
from lib.plots import plot_all, plot_equity_curve
from lib.backtest import run_backtest, save_results
import pandas as pd

# Run backtest
perf, _ = run_backtest('spy_sma_cross')

# Generate all standard plots
plot_all(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    transactions=perf['transactions'],
    save_dir=Path('results/spy_sma_cross/latest'),
    strategy_name='SPY SMA Cross'
)

# Or plot individual charts
plot_equity_curve(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    save_path=Path('equity_curve.png')
)
```

---

## Public API Reference

### plot_all()

Generate all standard plots and save to directory.

**Signature:**
```python
def plot_all(
    returns: pd.Series,
    save_dir: Path,
    portfolio_value: Optional[pd.Series] = None,
    transactions: Optional[pd.DataFrame] = None,
    strategy_name: str = 'Strategy'
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Series of daily returns |
| `save_dir` | Path | required | Directory to save plots |
| `portfolio_value` | Optional[pd.Series] | None | Optional Series of portfolio values |
| `transactions` | Optional[pd.DataFrame] | None | Optional DataFrame of transactions |
| `strategy_name` | str | 'Strategy' | Strategy name for plot titles |

**Generated Plots:**
- `equity_curve.png` - Equity curve chart
- `drawdown.png` - Drawdown chart
- `monthly_returns.png` - Monthly returns heatmap
- `rolling_metrics.png` - Rolling Sharpe and Sortino ratios
- `trade_analysis.png` - Trade analysis (if transactions provided)

**Example:**
```python
from lib.plots import plot_all
from pathlib import Path

plot_all(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    transactions=perf['transactions'],
    save_dir=Path('results/my_strategy/latest'),
    strategy_name='My Strategy'
)
```

---

### plot_equity_curve()

Plot equity curve from returns or portfolio value.

**Signature:**
```python
def plot_equity_curve(
    returns: pd.Series,
    portfolio_value: Optional[pd.Series] = None,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Series of daily returns |
| `portfolio_value` | Optional[pd.Series] | None | Optional Series of portfolio values (if provided, used instead of returns) |
| `save_path` | Optional[Path] | None | Optional path to save figure |
| `title` | Optional[str] | None | Optional plot title |

**Returns:** `None` (saves plot to file if `save_path` provided)

**Example:**
```python
from lib.plots import plot_equity_curve
from pathlib import Path

# Plot from returns (calculates cumulative returns)
plot_equity_curve(
    returns=perf['returns'].dropna(),
    save_path=Path('equity_curve.png'),
    title='My Strategy - Equity Curve'
)

# Plot from portfolio value (more accurate)
plot_equity_curve(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    save_path=Path('equity_curve.png')
)
```

---

### plot_drawdown()

Plot drawdown chart (underwater plot).

**Signature:**
```python
def plot_drawdown(
    returns: pd.Series,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Series of daily returns |
| `save_path` | Optional[Path] | None | Optional path to save figure |
| `title` | Optional[str] | None | Optional plot title |

**Returns:** `None` (saves plot to file if `save_path` provided)

**Example:**
```python
from lib.plots import plot_drawdown
from pathlib import Path

plot_drawdown(
    returns=perf['returns'].dropna(),
    save_path=Path('drawdown.png'),
    title='My Strategy - Drawdown Chart'
)
```

---

### plot_monthly_returns()

Plot monthly returns heatmap.

**Signature:**
```python
def plot_monthly_returns(
    returns: pd.Series,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Series of daily returns |
| `save_path` | Optional[Path] | None | Optional path to save figure |
| `title` | Optional[str] | None | Optional plot title |

**Returns:** `None` (saves plot to file if `save_path` provided)

**Note:** Requires `seaborn` for heatmap visualization.

**Example:**
```python
from lib.plots import plot_monthly_returns
from pathlib import Path

plot_monthly_returns(
    returns=perf['returns'].dropna(),
    save_path=Path('monthly_returns.png'),
    title='My Strategy - Monthly Returns'
)
```

---

### plot_trade_analysis()

Plot trade distribution analysis (win/loss histogram).

**Signature:**
```python
def plot_trade_analysis(
    transactions: pd.DataFrame,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transactions` | pd.DataFrame | required | DataFrame with columns: `date`, `sid`, `amount`, `price`, `commission` |
| `save_path` | Optional[Path] | None | Optional path to save figure |
| `title` | Optional[str] | None | Optional plot title |

**Returns:** `None` (saves plot to file if `save_path` provided)

**Plot Contents:**
- Left panel: Win/loss distribution histogram
- Right panel: Cumulative trade returns over time

**Example:**
```python
from lib.plots import plot_trade_analysis
from pathlib import Path

plot_trade_analysis(
    transactions=perf['transactions'],
    save_path=Path('trade_analysis.png'),
    title='My Strategy - Trade Analysis'
)
```

---

### plot_rolling_metrics()

Plot rolling Sharpe and Sortino ratios.

**Signature:**
```python
def plot_rolling_metrics(
    returns: pd.Series,
    window: int = 63,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Series of daily returns |
| `window` | int | 63 | Rolling window size in days (default: 63 trading days ≈ 3 months) |
| `save_path` | Optional[Path] | None | Optional path to save figure |
| `title` | Optional[str] | None | Optional plot title |

**Returns:** `None` (saves plot to file if `save_path` provided)

**Plot Contents:**
- Top panel: Rolling Sharpe ratio
- Bottom panel: Rolling Sortino ratio

**Example:**
```python
from lib.plots import plot_rolling_metrics
from pathlib import Path

# Default 63-day window
plot_rolling_metrics(
    returns=perf['returns'].dropna(),
    save_path=Path('rolling_metrics.png')
)

# Custom 252-day window (1 year)
plot_rolling_metrics(
    returns=perf['returns'].dropna(),
    window=252,
    save_path=Path('rolling_metrics_1y.png'),
    title='My Strategy - Rolling Metrics (1 Year)'
)
```

---

## Module Structure

The `lib/plots` package contains:

**Equity Visualization** (`equity.py`):
- `plot_equity_curve()` - Equity curve chart
- `plot_drawdown()` - Drawdown chart

**Returns Visualization** (`returns.py`):
- `plot_monthly_returns()` - Monthly returns heatmap

**Trade Visualization** (`trade.py`):
- `plot_trade_analysis()` - Trade distribution and cumulative returns

**Rolling Metrics Visualization** (`rolling.py`):
- `plot_rolling_metrics()` - Rolling Sharpe and Sortino ratios

**Optimization Visualization** (`optimization.py`):
- `_plot_optimization_heatmap()` - Internal function for optimization heatmaps
- `_plot_monte_carlo_distribution()` - Internal function for Monte Carlo distributions

**Orchestration** (`__init__.py`):
- `plot_all()` - Generate all standard plots

---

## Examples

### Complete Plotting Workflow

```python
from lib.plots import plot_all
from lib.backtest import run_backtest, save_results
from pathlib import Path

# Run backtest
perf, calendar = run_backtest(
    strategy_name='spy_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Save results (includes automatic plotting)
result_dir = save_results(
    strategy_name='spy_sma_cross',
    perf=perf,
    params=params
)
# Plots are automatically generated in result_dir

# Or generate plots manually
plot_all(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    transactions=perf['transactions'],
    save_dir=result_dir,
    strategy_name='SPY SMA Cross'
)
```

### Individual Plot Examples

```python
from lib.plots import (
    plot_equity_curve,
    plot_drawdown,
    plot_monthly_returns,
    plot_trade_analysis,
    plot_rolling_metrics
)
from pathlib import Path

save_dir = Path('results/my_strategy/latest')
save_dir.mkdir(parents=True, exist_ok=True)

# Equity curve
plot_equity_curve(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    save_path=save_dir / 'equity_curve.png',
    title='My Strategy - Equity Curve'
)

# Drawdown
plot_drawdown(
    returns=perf['returns'].dropna(),
    save_path=save_dir / 'drawdown.png'
)

# Monthly returns
plot_monthly_returns(
    returns=perf['returns'].dropna(),
    save_path=save_dir / 'monthly_returns.png'
)

# Trade analysis (if transactions available)
if len(perf['transactions']) > 0:
    plot_trade_analysis(
        transactions=perf['transactions'],
        save_path=save_dir / 'trade_analysis.png'
    )

# Rolling metrics
plot_rolling_metrics(
    returns=perf['returns'].dropna(),
    window=63,  # 3 months
    save_path=save_dir / 'rolling_metrics.png'
)
```

### Integration with Backtest Results

```python
from lib.backtest import run_backtest, save_results
from lib.plots import plot_all
from pathlib import Path

# Run backtest
perf, calendar = run_backtest('btc_sma_cross')

# Save results (automatically generates plots)
result_dir = save_results(
    strategy_name='btc_sma_cross',
    perf=perf,
    params=params
)

# Verify plots were generated
plot_files = list(result_dir.glob('*.png'))
print(f"Generated {len(plot_files)} plots:")
for plot_file in plot_files:
    print(f"  - {plot_file.name}")
```

---

## Configuration

### Matplotlib Backend

The plotting module uses the 'Agg' backend by default, which is non-interactive and suitable for server environments:

```python
import matplotlib
matplotlib.use('Agg')  # Set before importing pyplot
```

This allows plots to be generated without a display, making it suitable for:
- Server environments
- Automated backtest execution
- CI/CD pipelines
- Docker containers

### Plot Format and Quality

**Default Settings:**
- **DPI**: 150 (high quality)
- **Format**: PNG
- **Figure Size**: 12x6 inches (equity, drawdown), 14x6 inches (monthly returns)
- **Bbox**: Tight layout (minimal whitespace)

**Customization:**
To customize plot appearance, modify the plotting functions directly or create wrapper functions:

```python
from lib.plots import plot_equity_curve
import matplotlib.pyplot as plt

# Custom plot with different settings
def plot_custom_equity(returns, save_path):
    fig, ax = plt.subplots(figsize=(16, 8))  # Larger figure
    # ... custom plotting code ...
    plt.savefig(save_path, dpi=300, bbox_inches='tight')  # Higher DPI
    plt.close()
```

---

## Error Handling

**Optional Dependency Handling:**
- If `matplotlib` is not installed, all plotting functions silently return without generating plots
- No exceptions are raised, allowing the codebase to function without visualization dependencies
- Check for plot files after calling plotting functions to verify plots were generated

**Common Issues:**

1. **Plots Not Generated:**
   - Verify `matplotlib` is installed: `pip install matplotlib`
   - For monthly returns, also install `seaborn`: `pip install seaborn`
   - Check that `save_path` directory exists and is writable

2. **Empty Plots:**
   - Ensure returns series has data: `len(returns) > 0`
   - Check that returns are not all NaN: `returns.notna().any()`
   - Verify portfolio_value or transactions have data if used

3. **Import Errors:**
   - If `seaborn` is missing, `plot_monthly_returns()` will fail
   - Install with: `pip install seaborn`

---

## Best Practices

1. **Use `plot_all()` for Standard Workflows:**
   ```python
   # Generate all standard plots at once
   plot_all(returns, save_dir, portfolio_value, transactions, strategy_name)
   ```

2. **Save Plots to Results Directory:**
   ```python
   # Save plots alongside backtest results
   result_dir = save_results(strategy_name, perf, params)
   plot_all(returns, result_dir, portfolio_value, transactions, strategy_name)
   ```

3. **Check for Optional Dependencies:**
   ```python
   from lib.plots import plot_equity_curve
   from pathlib import Path
   
   plot_equity_curve(returns, save_path=Path('plot.png'))
   
   # Verify plot was generated
   if Path('plot.png').exists():
       print("Plot generated successfully")
   else:
       print("Warning: Plot not generated (matplotlib may not be installed)")
   ```

4. **Use Appropriate Window Sizes:**
   ```python
   # For daily data: 63 days ≈ 3 months, 252 days ≈ 1 year
   plot_rolling_metrics(returns, window=63)   # Short-term
   plot_rolling_metrics(returns, window=252)  # Long-term
   ```

5. **Include Strategy Name in Titles:**
   ```python
   plot_equity_curve(
       returns=returns,
       save_path=save_path,
       title=f'{strategy_name} - Equity Curve'  # Descriptive title
   )
   ```

---

## See Also

- [Metrics API](metrics.md) - Performance metrics calculation
- [Backtest API](backtest.md) - Backtest execution (automatically generates plots)
- [Report API](report.md) - Report generation (includes plots)
- [Results Management](../.cursor/rules/results.mdc) - Result directory structure
