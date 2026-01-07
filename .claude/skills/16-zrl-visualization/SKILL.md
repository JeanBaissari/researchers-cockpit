---
name: zrl-visualization
description: This skill should be used when creating charts and visualizations from backtest results. It provides patterns for equity curves, drawdown charts, return distributions, rolling metrics, and interactive dashboards using matplotlib, plotly, and seaborn.
---

# Zipline Visualization

Create professional charts and dashboards from Zipline backtest results.

## Purpose

Transform raw backtest data into insightful visualizations including equity curves, drawdown analysis, return distributions, and comprehensive performance dashboards.

## When to Use

- Visualizing backtest equity curves and returns
- Creating drawdown analysis charts
- Building interactive performance dashboards
- Comparing multiple strategy results visually
- Generating presentation-ready charts

## Visualization Categories

### 1. Equity & Returns

| Chart Type | Use Case |
|------------|----------|
| Equity Curve | Overall strategy performance over time |
| Log Equity | Long-term growth perspective |
| Cumulative Returns | Percentage-based performance |
| Underwater Plot | Drawdown depth visualization |

### 2. Risk Analysis

| Chart Type | Use Case |
|------------|----------|
| Rolling Sharpe | Time-varying risk-adjusted return |
| Rolling Volatility | Volatility regime changes |
| Drawdown Periods | Visualize recovery times |
| VaR Histogram | Return distribution with risk metrics |

### 3. Comparison

| Chart Type | Use Case |
|------------|----------|
| Multi-Strategy | Compare equity curves |
| Scatter Matrix | Factor correlation analysis |
| Monthly Heatmap | Return patterns by month |
| Regime Analysis | Performance across market conditions |

## Core Workflow

### Step 1: Load Results

```python
import pandas as pd
from visualization import BacktestVisualizer

# From run_algorithm
results = run_algorithm(...)

# Or load saved results
results = pd.read_pickle('backtest_results.pickle')
```

### Step 2: Create Visualizer

```python
viz = BacktestVisualizer(results, benchmark_returns=spy_returns)
```

### Step 3: Generate Charts

```python
# Individual charts
viz.plot_equity_curve(figsize=(12, 6))
viz.plot_drawdown(figsize=(12, 4))
viz.plot_monthly_returns(figsize=(10, 8))

# Full dashboard
viz.create_dashboard(output='dashboard.html')
```

## Script Reference

### plot_results.py

Quick visualization from command line:

```bash
python scripts/plot_results.py results.pickle \
    --charts equity,drawdown,monthly \
    --output charts/ \
    --format png
```

Options:
- `--charts`: Comma-separated chart types
- `--output`: Output directory
- `--format`: png, pdf, svg, html
- `--benchmark`: Benchmark ticker for comparison

### create_dashboard.py

Generate interactive HTML dashboard:

```bash
python scripts/create_dashboard.py results.pickle \
    --output dashboard.html \
    --title "Momentum Strategy Backtest"
```

### compare_strategies.py

Visual comparison of multiple strategies:

```bash
python scripts/compare_strategies.py \
    strat1.pickle strat2.pickle strat3.pickle \
    --names "Momentum" "Value" "Combined" \
    --output comparison.html
```

## BacktestVisualizer Class

```python
class BacktestVisualizer:
    """Professional visualizations for backtest results."""
    
    def __init__(self, results: pd.DataFrame,
                 benchmark_returns: pd.Series = None,
                 style: str = 'seaborn'):
        """
        Parameters
        ----------
        results : pd.DataFrame
            Output from run_algorithm()
        benchmark_returns : pd.Series, optional
            Benchmark for comparison
        style : str
            Matplotlib style ('seaborn', 'ggplot', 'dark')
        """
    
    # Equity charts
    def plot_equity_curve(self, log_scale=False, figsize=(12, 6))
    def plot_cumulative_returns(self, figsize=(12, 6))
    def plot_equity_vs_benchmark(self, figsize=(12, 6))
    
    # Drawdown charts  
    def plot_drawdown(self, figsize=(12, 4))
    def plot_underwater(self, figsize=(12, 4))
    def plot_drawdown_periods(self, top_n=5, figsize=(12, 6))
    
    # Return analysis
    def plot_returns_distribution(self, figsize=(10, 6))
    def plot_monthly_heatmap(self, figsize=(12, 8))
    def plot_yearly_returns(self, figsize=(10, 6))
    
    # Risk analysis
    def plot_rolling_sharpe(self, window=252, figsize=(12, 4))
    def plot_rolling_volatility(self, window=21, figsize=(12, 4))
    def plot_rolling_beta(self, window=252, figsize=(12, 4))
    
    # Dashboard
    def create_dashboard(self, output='dashboard.html')
    def create_tearsheet(self, output='tearsheet.pdf')
```

## Chart Examples

### Equity Curve with Drawdown

```python
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                               gridspec_kw={'height_ratios': [3, 1]})

# Equity curve
results['portfolio_value'].plot(ax=ax1, linewidth=1.5)
ax1.set_title('Portfolio Equity Curve')
ax1.set_ylabel('Portfolio Value ($)')
ax1.grid(True, alpha=0.3)

# Drawdown
drawdown = (results['portfolio_value'] / 
            results['portfolio_value'].expanding().max() - 1)
drawdown.plot(ax=ax2, color='red', linewidth=1)
ax2.fill_between(drawdown.index, drawdown.values, 0, 
                 color='red', alpha=0.3)
ax2.set_title('Drawdown')
ax2.set_ylabel('Drawdown (%)')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('equity_drawdown.png', dpi=150)
```

### Monthly Returns Heatmap

```python
import seaborn as sns

# Calculate monthly returns
monthly = results['returns'].resample('M').apply(
    lambda x: (1 + x).prod() - 1
)

# Reshape for heatmap
monthly_df = monthly.to_frame('return')
monthly_df['year'] = monthly_df.index.year
monthly_df['month'] = monthly_df.index.month
pivot = monthly_df.pivot(index='year', columns='month', values='return')

# Plot
fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(pivot, annot=True, fmt='.1%', cmap='RdYlGn', 
            center=0, ax=ax, cbar_kws={'label': 'Return'})
ax.set_title('Monthly Returns Heatmap')
plt.savefig('monthly_heatmap.png', dpi=150)
```

### Rolling Sharpe Ratio

```python
def rolling_sharpe(returns, window=252, risk_free=0.0):
    excess = returns - risk_free / 252
    roll_mean = excess.rolling(window).mean()
    roll_std = excess.rolling(window).std()
    return np.sqrt(252) * roll_mean / roll_std

sharpe = rolling_sharpe(results['returns'])

fig, ax = plt.subplots(figsize=(12, 4))
sharpe.plot(ax=ax, linewidth=1)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Sharpe=1')
ax.axhline(y=2, color='blue', linestyle='--', alpha=0.5, label='Sharpe=2')
ax.fill_between(sharpe.index, sharpe.values, 0, 
                where=sharpe > 0, color='green', alpha=0.2)
ax.fill_between(sharpe.index, sharpe.values, 0,
                where=sharpe < 0, color='red', alpha=0.2)
ax.set_title('Rolling 1-Year Sharpe Ratio')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('rolling_sharpe.png', dpi=150)
```

## Interactive Dashboards (Plotly)

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_interactive_dashboard(results):
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=('Equity Curve', 'Drawdown',
                       'Monthly Returns', 'Return Distribution',
                       'Rolling Sharpe', 'Cumulative Returns'),
        vertical_spacing=0.08
    )
    
    # Equity curve
    fig.add_trace(
        go.Scatter(x=results.index, y=results['portfolio_value'],
                  name='Portfolio', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Drawdown
    dd = (results['portfolio_value'] / 
          results['portfolio_value'].expanding().max() - 1)
    fig.add_trace(
        go.Scatter(x=dd.index, y=dd, fill='tozeroy',
                  name='Drawdown', line=dict(color='red')),
        row=1, col=2
    )
    
    # More traces...
    
    fig.update_layout(height=900, showlegend=True,
                     title_text="Backtest Performance Dashboard")
    fig.write_html('dashboard.html')
```

## Style Guidelines

### Color Schemes

```python
COLORS = {
    'equity': '#1f77b4',      # Blue
    'benchmark': '#7f7f7f',   # Gray
    'drawdown': '#d62728',    # Red
    'positive': '#2ca02c',    # Green
    'negative': '#d62728',    # Red
    'neutral': '#9467bd',     # Purple
}
```

### Chart Defaults

```python
CHART_DEFAULTS = {
    'figsize': (12, 6),
    'dpi': 150,
    'grid_alpha': 0.3,
    'line_width': 1.5,
    'title_fontsize': 14,
    'label_fontsize': 12,
}
```

## Integration with analyze()

```python
def analyze(context, perf):
    """Automatic visualization in analyze function."""
    from visualization import BacktestVisualizer
    
    viz = BacktestVisualizer(perf)
    
    # Save all standard charts
    viz.plot_equity_curve()
    plt.savefig('equity_curve.png', dpi=150)
    
    viz.plot_drawdown()
    plt.savefig('drawdown.png', dpi=150)
    
    viz.plot_monthly_heatmap()
    plt.savefig('monthly_returns.png', dpi=150)
    
    # Create interactive dashboard
    viz.create_dashboard('dashboard.html')
    
    print("Visualizations saved!")
```

## References

See `references/chart_templates.md` for reusable chart code.
See `references/color_palettes.md` for professional color schemes.
