---
name: zrl-performance-analyzer
description: This skill should be used when analyzing backtest results, calculating performance metrics, and generating attribution analysis. It provides comprehensive tools for evaluating strategy performance including risk-adjusted returns, drawdown analysis, and factor attribution.
---

# Zipline Performance Analyzer

Analyze backtest results with professional-grade performance metrics and attribution.

## Purpose

Transform raw backtest results into actionable insights through comprehensive performance metrics, risk analysis, drawdown characterization, and return attribution.

## When to Use

- Evaluating backtest results after `run_algorithm()`
- Comparing multiple strategy variants
- Generating performance reports for stakeholders
- Identifying strategy weaknesses and improvement areas
- Calculating risk-adjusted returns (Sharpe, Sortino, Calmar)

## Core Metrics

### Return Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Total Return | Cumulative return | `(final_value / initial_value) - 1` |
| CAGR | Compound annual growth rate | `(1 + total_return)^(252/days) - 1` |
| Daily Return | Average daily return | `mean(daily_returns)` |
| Volatility | Annualized standard deviation | `std(daily_returns) * sqrt(252)` |

### Risk-Adjusted Metrics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| Sharpe Ratio | Excess return per unit risk | >1 acceptable, >2 good, >3 excellent |
| Sortino Ratio | Excess return per unit downside risk | Higher = better downside protection |
| Calmar Ratio | CAGR / Max Drawdown | >1 preferred for trend following |
| Information Ratio | Alpha / Tracking Error | Active management skill measure |

### Drawdown Metrics

| Metric | Description |
|--------|-------------|
| Max Drawdown | Largest peak-to-trough decline |
| Max DD Duration | Longest time in drawdown |
| Average Drawdown | Mean of all drawdown periods |
| Ulcer Index | Quadratic mean of drawdowns |

## Core Workflow

### Step 1: Run Backtest

```python
from zipline import run_algorithm

results = run_algorithm(
    start=start,
    end=end,
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    bundle='my-bundle'
)
```

### Step 2: Analyze Performance

Execute `scripts/analyze_performance.py` for comprehensive analysis:

```bash
python scripts/analyze_performance.py results.pickle --benchmark SPY
```

Or use the PerformanceAnalyzer class programmatically:

```python
from performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(results, benchmark_returns=spy_returns)
metrics = analyzer.calculate_all_metrics()
analyzer.generate_report('performance_report.html')
```

### Step 3: Attribution Analysis

Decompose returns by factor exposure:

```python
# Factor attribution
attribution = analyzer.factor_attribution(
    factors=['momentum', 'value', 'size', 'volatility']
)

# Time-based attribution
monthly = analyzer.monthly_attribution()
yearly = analyzer.yearly_attribution()
```

## Script Reference

### analyze_performance.py

Comprehensive performance analysis from saved results:

```bash
python scripts/analyze_performance.py results.pickle \
    --benchmark SPY \
    --risk-free-rate 0.02 \
    --output report.html
```

Options:
- `--benchmark`: Benchmark ticker for relative metrics
- `--risk-free-rate`: Annual risk-free rate (default: 0.0)
- `--output`: HTML report output path
- `--format`: Output format (html, json, csv)

### compare_strategies.py

Compare multiple strategy results:

```bash
python scripts/compare_strategies.py \
    strategy1.pickle strategy2.pickle strategy3.pickle \
    --names "Momentum" "Mean Reversion" "Combined" \
    --output comparison.html
```

### drawdown_analysis.py

Deep drawdown characterization:

```bash
python scripts/drawdown_analysis.py results.pickle \
    --top 10 \
    --output drawdowns.csv
```

## PerformanceAnalyzer Class

```python
class PerformanceAnalyzer:
    """Comprehensive performance analysis for Zipline results."""
    
    def __init__(self, results: pd.DataFrame, 
                 benchmark_returns: pd.Series = None,
                 risk_free_rate: float = 0.0):
        """
        Parameters
        ----------
        results : pd.DataFrame
            Output from run_algorithm()
        benchmark_returns : pd.Series, optional
            Benchmark daily returns for relative metrics
        risk_free_rate : float
            Annual risk-free rate
        """
    
    # Return metrics
    def total_return(self) -> float
    def cagr(self) -> float
    def volatility(self) -> float
    def sharpe_ratio(self) -> float
    def sortino_ratio(self) -> float
    def calmar_ratio(self) -> float
    
    # Drawdown metrics
    def max_drawdown(self) -> float
    def max_drawdown_duration(self) -> int
    def drawdown_series(self) -> pd.Series
    def top_drawdowns(self, n: int = 5) -> pd.DataFrame
    
    # Risk metrics
    def var(self, confidence: float = 0.95) -> float
    def cvar(self, confidence: float = 0.95) -> float
    def beta(self) -> float
    def alpha(self) -> float
    
    # Attribution
    def monthly_returns(self) -> pd.Series
    def yearly_returns(self) -> pd.Series
    def rolling_sharpe(self, window: int = 252) -> pd.Series
    
    # Reporting
    def calculate_all_metrics(self) -> dict
    def generate_report(self, output_path: str) -> None
```

## Metric Calculations

### Sharpe Ratio

```python
def sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Sharpe = (mean_return - risk_free) / std_return * sqrt(252)
    """
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
```

### Sortino Ratio

```python
def sortino_ratio(returns, risk_free_rate=0.0, target=0.0):
    """
    Sortino = (mean_return - target) / downside_std * sqrt(252)
    Uses only negative returns for denominator.
    """
    excess_returns = returns - risk_free_rate / 252
    downside_returns = returns[returns < target]
    downside_std = np.sqrt(np.mean(downside_returns**2))
    return np.sqrt(252) * excess_returns.mean() / downside_std
```

### Maximum Drawdown

```python
def max_drawdown(equity_curve):
    """
    MaxDD = max((peak - trough) / peak)
    """
    rolling_max = equity_curve.expanding().max()
    drawdowns = (equity_curve - rolling_max) / rolling_max
    return drawdowns.min()
```

### Value at Risk (VaR)

```python
def var(returns, confidence=0.95):
    """
    VaR at specified confidence level.
    Historical VaR using percentile method.
    """
    return np.percentile(returns, (1 - confidence) * 100)
```

## Performance Report Sections

A complete performance report includes:

1. **Summary Statistics**
   - Total return, CAGR, volatility
   - Sharpe, Sortino, Calmar ratios
   - Win rate, profit factor

2. **Drawdown Analysis**
   - Max drawdown magnitude and duration
   - Top 5 drawdown periods
   - Recovery time analysis

3. **Monthly/Yearly Returns**
   - Return heatmap by month/year
   - Best/worst periods

4. **Risk Analysis**
   - VaR and CVaR at multiple confidence levels
   - Beta and alpha (if benchmark provided)
   - Rolling Sharpe ratio

5. **Trade Analysis** (if transactions available)
   - Win/loss ratio
   - Average trade duration
   - Profit per trade distribution

## Integration Pattern

```python
def analyze(context, perf):
    """Built-in analyze function for automatic reporting."""
    from performance_analyzer import PerformanceAnalyzer
    
    analyzer = PerformanceAnalyzer(perf)
    metrics = analyzer.calculate_all_metrics()
    
    # Print summary
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    
    # Generate report
    analyzer.generate_report('backtest_report.html')
```

## References

See `references/metric_formulas.md` for detailed mathematical formulas.
See `references/benchmarks.md` for benchmark comparison guidelines.
