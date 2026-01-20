# Metrics Overview

> Understanding Zipline's performance metrics system.

## Overview

Zipline tracks algorithm performance through a metrics system that records data every bar and aggregates into daily/cumulative results. The final performance DataFrame contains all recorded metrics.

---

## Performance DataFrame

The `run_algorithm()` function returns a DataFrame with these key columns:

### Value Columns

| Column | Description |
|--------|-------------|
| `portfolio_value` | Total portfolio value |
| `starting_value` | Value at period start |
| `ending_value` | Value at period end |
| `starting_cash` | Cash at period start |
| `ending_cash` | Cash at period end |
| `pnl` | Profit and loss for period |
| `returns` | Period returns |
| `capital_used` | Cash flow (capital in/out) |

### Position Columns

| Column | Description |
|--------|-------------|
| `positions` | List of position dicts |
| `gross_leverage` | Gross leverage ratio |
| `net_leverage` | Net leverage ratio |
| `long_value` | Total long position value |
| `short_value` | Total short position value |
| `long_exposure` | Long exposure |
| `short_exposure` | Short exposure |

### Transaction Columns

| Column | Description |
|--------|-------------|
| `orders` | Orders placed this period |
| `transactions` | Executed transactions |

### Benchmark Columns

| Column | Description |
|--------|-------------|
| `benchmark_period_return` | Benchmark return |
| `algorithm_period_return` | Algorithm return |
| `alpha` | Alpha vs benchmark |
| `beta` | Beta vs benchmark |
| `sharpe` | Sharpe ratio |
| `sortino` | Sortino ratio |
| `max_drawdown` | Maximum drawdown |
| `max_drawdown_duration` | Duration of the maximum drawdown (in days) |
| `recovery_time` | Time taken to recover from the maximum drawdown (in days) |

---

## Accessing Metrics

### From run_algorithm()

```python
results = run_algorithm(...)

# Time series
results['portfolio_value'].plot()
results['returns'].cumsum().plot()

# Final values
final_value = results['portfolio_value'].iloc[-1]
total_return = results['returns'].sum()
max_dd = results['max_drawdown'].min()
```

### In analyze()

```python
def analyze(context, perf):
    # perf is the same DataFrame
    print(f"Final value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
    print(f"Total return: {perf['returns'].sum():.2%}")
    print(f"Sharpe: {perf['sharpe'].iloc[-1]:.2f}")
```

---

## Custom Metrics with record()

Track custom values using `record()`:

```python
def handle_data(context, data):
    price = data.current(context.asset, 'price')
    
    record(
        price=price,
        signal=context.signal_value,
        position_size=context.portfolio.positions.get(context.asset, 0)
    )
```

Access in results:

```python
results = run_algorithm(...)

results['price'].plot()
results['signal'].plot()
```

---

## Metrics Sets

### Default Metrics

The default metrics set includes:

- Returns and benchmark returns
- Portfolio values and cash
- Leverage metrics
- Orders and transactions
- Alpha, beta, Sharpe, Sortino
- Maximum drawdown

### Custom Metrics Sets

```python
from zipline.finance.metrics import register, load

@register('minimal')
def minimal_metrics():
    from zipline.finance.metrics import Returns, Positions
    return {Returns(), Positions()}

# Use custom set
results = run_algorithm(..., metrics_set='minimal')
```

---

## Key Performance Calculations

### Returns

```python
# Daily return
daily_return = (ending_value - starting_value) / starting_value

# Cumulative return
cumulative_return = results['returns'].cumsum()
```

### Sharpe Ratio

```python
import numpy as np

returns = results['returns']
sharpe = np.sqrt(252) * returns.mean() / returns.std()
```

### Maximum Drawdown

```python
cumulative = (1 + results['returns']).cumprod()
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min()
```

### Beta

```python
algo_returns = results['returns']
bench_returns = results['benchmark_period_return']

covariance = algo_returns.cov(bench_returns)
variance = bench_returns.var()
beta = covariance / variance
```

---

## Analyzing Results

```python
def analyze(context, perf):
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Portfolio value
    perf['portfolio_value'].plot(ax=axes[0], title='Portfolio Value')
    
    # Cumulative returns
    perf['returns'].cumsum().plot(ax=axes[1], title='Cumulative Returns')
    
    # Drawdown
    cumulative = (1 + perf['returns']).cumprod()
    drawdown = (cumulative - cumulative.cummax()) / cumulative.cummax()
    drawdown.plot(ax=axes[2], title='Drawdown')
    
    plt.tight_layout()
    plt.savefig('backtest_analysis.png')
```

---

## Performance Summary

```python
def print_summary(results):
    total_return = results['returns'].sum()
    annual_return = (1 + total_return) ** (252 / len(results)) - 1
    volatility = results['returns'].std() * np.sqrt(252)
    sharpe = annual_return / volatility
    max_dd = ((1 + results['returns']).cumprod().cummax() - 
              (1 + results['returns']).cumprod()).max()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Volatility: {volatility:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")
```

---

## See Also

- [Risk Metrics](risk_metrics.md)
- [Algorithm State](algorithm_state.md)
- [Recording Values](../01_core/record.md)
