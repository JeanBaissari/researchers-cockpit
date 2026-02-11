# Zipline-Reloaded Metrics System Inventory

> Comprehensive catalog of Zipline-Reloaded's native metrics system, performance DataFrame columns, and metrics API for Zipline-Reloaded v3.0+

**Source:** [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
**Version:** Zipline-Reloaded v3.0+  
**Last Updated:** 2026-01-27

---

## Table of Contents

1. [Overview](#overview)
2. [Performance DataFrame Columns](#performance-dataframe-columns)
3. [Metrics System Architecture](#metrics-system-architecture)
4. [Built-in Metrics Classes](#built-in-metrics-classes)
5. [Metrics Sets](#metrics-sets)
6. [Custom Metrics with record()](#custom-metrics-with-record)
7. [Metrics API Functions](#metrics-api-functions)
8. [Comparison with Project Metrics](#comparison-with-project-metrics)
9. [Usage Patterns](#usage-patterns)
10. [Best Practices](#best-practices)

---

## Overview

Zipline-Reloaded tracks algorithm performance through a metrics system that records data every bar and aggregates into daily/cumulative results. The final performance DataFrame returned by `run_algorithm()` contains all recorded metrics.

### Key Concepts

- **Performance DataFrame**: The main output from `run_algorithm()` containing time-series metrics
- **Metrics Classes**: Components that track specific performance aspects (returns, positions, etc.)
- **Metrics Sets**: Pre-configured collections of metrics (default, minimal, custom)
- **Custom Metrics**: User-defined values tracked via `record()` function

---

## Performance DataFrame Columns

The `run_algorithm()` function returns a DataFrame with these columns:

### Portfolio Value Columns

| Column | Type | Description |
|--------|------|-------------|
| `portfolio_value` | float64 | Total portfolio value (cash + positions) |
| `starting_value` | float64 | Portfolio value at period start |
| `ending_value` | float64 | Portfolio value at period end |
| `starting_cash` | float64 | Cash balance at period start |
| `ending_cash` | float64 | Cash balance at period end |
| `pnl` | float64 | Profit and loss for the period |
| `returns` | float64 | Period returns (ending_value / starting_value - 1) |
| `capital_used` | float64 | Cash flow (capital in/out) for the period |

**Usage:**
```python
results = run_algorithm(...)

# Access portfolio value
final_value = results['portfolio_value'].iloc[-1]
total_return = results['returns'].sum()

# Plot equity curve
results['portfolio_value'].plot()
```

### Position Columns

| Column | Type | Description |
|--------|------|-------------|
| `positions` | object | List of position dictionaries (one per asset) |
| `gross_leverage` | float64 | Gross leverage ratio (total exposure / portfolio_value) |
| `net_leverage` | float64 | Net leverage ratio (net exposure / portfolio_value) |
| `long_value` | float64 | Total value of long positions |
| `short_value` | float64 | Total value of short positions |
| `long_exposure` | float64 | Long exposure amount |
| `short_exposure` | float64 | Short exposure amount |

**Usage:**
```python
# Check leverage
max_leverage = results['gross_leverage'].max()

# Analyze positions
positions = results['positions'].iloc[-1]
for asset, position in positions.items():
    print(f"{asset}: {position['amount']} shares")
```

### Transaction Columns

| Column | Type | Description |
|--------|------|-------------|
| `orders` | object | List of orders placed this period |
| `transactions` | object | List of executed transactions (fills) this period |

**Usage:**
```python
# Count total transactions
all_transactions = []
for transactions_list in results['transactions']:
    all_transactions.extend(transactions_list)

print(f"Total trades: {len(all_transactions)}")
```

### Benchmark Columns

| Column | Type | Description |
|--------|------|-------------|
| `benchmark_period_return` | float64 | Benchmark return for the period |
| `algorithm_period_return` | float64 | Algorithm return for the period |
| `alpha` | float64 | Alpha vs benchmark (Jensen's alpha) |
| `beta` | float64 | Beta vs benchmark (market exposure) |
| `sharpe` | float64 | Sharpe ratio (rolling calculation) |
| `sortino` | float64 | Sortino ratio (rolling calculation) |
| `max_drawdown` | float64 | Maximum drawdown (rolling calculation) |
| `max_drawdown_duration` | float64 | Duration of maximum drawdown in days |
| `recovery_time` | float64 | Time to recover from max drawdown in days |

**Usage:**
```python
# Access final metrics
final_sharpe = results['sharpe'].iloc[-1]
final_alpha = results['alpha'].iloc[-1]
final_beta = results['beta'].iloc[-1]

# Plot drawdown
results['max_drawdown'].plot()
```

**Note:** These benchmark metrics are calculated by Zipline's metrics system. For more comprehensive metrics, use `lib/metrics/calculate_metrics()` which provides additional risk metrics and trade-level analysis.

---

## Metrics System Architecture

### Metrics Package Location

```python
from zipline.finance import metrics
```

**Package:** `zipline.finance.metrics`

### Core Components

1. **Metric Classes**: Track specific performance aspects
2. **Metrics Sets**: Collections of metrics registered by name
3. **Ledger Fields**: Access to portfolio ledger data
4. **Returns Statistics**: Return-based calculations

### Metrics Registration

```python
from zipline.finance import metrics

@metrics.register('my_custom_set')
def my_custom_metrics():
    from zipline.finance.metrics import Returns, Positions
    return {Returns(), Positions()}

# Use in run_algorithm
results = run_algorithm(..., metrics_set='my_custom_set')
```

---

## Built-in Metrics Classes

### Returns Metrics

#### Returns
```python
from zipline.finance.metrics import Returns

Returns()
```

**Purpose:** Tracks daily and cumulative returns.

**Output Columns:**
- `returns` - Period returns
- `algorithm_period_return` - Algorithm return for period

#### ReturnsStatistic
```python
from zipline.finance.metrics.metric import ReturnsStatistic

ReturnsStatistic()
```

**Purpose:** Calculates return-based statistics (Sharpe, Sortino, etc.).

**Output Columns:**
- `sharpe` - Sharpe ratio
- `sortino` - Sortino ratio
- `max_drawdown` - Maximum drawdown

### Position Metrics

#### Positions
```python
from zipline.finance.metrics import Positions

Positions()
```

**Purpose:** Tracks positions at end of each day.

**Output Columns:**
- `positions` - List of position dictionaries
- `long_value` - Total long position value
- `short_value` - Total short position value
- `gross_leverage` - Gross leverage ratio
- `net_leverage` - Net leverage ratio

### Transaction Metrics

#### Orders
```python
from zipline.finance.metrics import Orders

Orders()
```

**Purpose:** Records all orders placed each day.

**Output Columns:**
- `orders` - List of orders

#### Transactions
```python
from zipline.finance.metrics import Transactions

Transactions()
```

**Purpose:** Records all executed transactions (fills) each day.

**Output Columns:**
- `transactions` - List of transactions

#### CashFlow
```python
from zipline.finance.metrics.metric import CashFlow

CashFlow()
```

**Purpose:** Tracks daily and cumulative cash flow.

**Output Columns:**
- `capital_used` - Cash flow (capital in/out)

### Benchmark Metrics

#### BenchmarkReturnsAndVolatility
```python
from zipline.finance.metrics import BenchmarkReturnsAndVolatility

BenchmarkReturnsAndVolatility()
```

**Purpose:** Tracks benchmark returns and volatility for comparison.

**Output Columns:**
- `benchmark_period_return` - Benchmark return

**Note:** This metric has known bugs in Zipline-Reloaded v3.0+ when used with certain calendars (especially FOREX). Use `metrics_set='none'` or custom metrics sets to avoid issues.

#### AlphaBeta
```python
from zipline.finance.metrics import AlphaBeta

AlphaBeta()
```

**Purpose:** Calculates end-of-simulation alpha and beta vs benchmark.

**Output Columns:**
- `alpha` - Jensen's alpha
- `beta` - Beta coefficient

### Risk Metrics

#### MaxLeverage
```python
from zipline.finance.metrics import MaxLeverage

MaxLeverage()
```

**Purpose:** Tracks maximum account leverage reached.

**Output Columns:**
- `max_leverage` - Maximum leverage value

---

## Metrics Sets

### Default Metrics Set

The default metrics set includes:
- Returns and benchmark returns
- Portfolio values and cash
- Leverage metrics
- Orders and transactions
- Alpha, beta, Sharpe, Sortino
- Maximum drawdown

**Usage:**
```python
# Default metrics (no need to specify)
results = run_algorithm(...)
```

### Minimal Metrics Set

```python
from zipline.finance import metrics

@metrics.register('minimal')
def minimal_metrics():
    from zipline.finance.metrics import Returns, Positions
    return {Returns(), Positions()}

# Use minimal set
results = run_algorithm(..., metrics_set='minimal')
```

**Purpose:** Reduces computation by tracking only essential metrics.

### No Metrics Set

```python
results = run_algorithm(..., metrics_set='none')
```

**Purpose:** Disables all metrics tracking. Useful for:
- FOREX strategies (avoids metrics tracker bugs)
- Performance optimization
- Custom metrics calculation

**Note:** When `metrics_set='none'`, the performance DataFrame may not include `returns` or `portfolio_value` columns. These must be reconstructed from transactions/positions if needed.

### Custom Metrics Sets

```python
from zipline.finance import metrics

@metrics.register('my_custom_set')
def my_custom_metrics():
    from zipline.finance.metrics import (
        Returns,
        Positions,
        Transactions,
        CashFlow
    )
    return {
        Returns(),
        Positions(),
        Transactions(),
        CashFlow(),
    }

# Use custom set
results = run_algorithm(..., metrics_set='my_custom_set')
```

**Project Example:** `lib/backtest/custom_metrics.py` defines `'minimal-essential'` set:

```python
@metrics.register('minimal-essential')
def minimal_essential_metrics():
    from zipline.finance.metrics.metric import (
        ReturnsStatistic,
        CashFlow,
    )
    return {
        ReturnsStatistic(),  # Tracks returns
        CashFlow(),  # Tracks cash flow
    }
```

---

## Custom Metrics with record()

Track custom values using the `record()` function:

```python
from zipline.api import record

def handle_data(context, data):
    price = data.current(context.asset, 'price')
    signal = calculate_signal(context, data)
    
    record(
        price=price,
        signal=signal,
        position_size=context.portfolio.positions[context.asset].amount,
        custom_indicator=context.my_indicator
    )
```

**Access in Results:**
```python
results = run_algorithm(...)

# Custom metrics become DataFrame columns
results['price'].plot()
results['signal'].plot()
results['custom_indicator'].plot()
```

**Best Practices:**
- Use descriptive names for recorded values
- Record scalar values (not complex objects)
- Avoid recording too frequently (performance impact)
- Use for debugging and analysis, not core metrics

---

## Metrics API Functions

### Register Metrics Set

```python
from zipline.finance import metrics

@metrics.register('set_name')
def my_metrics():
    # Return set of metric objects
    return {Returns(), Positions()}
```

### Load Metrics Set

```python
from zipline.finance import metrics

metrics_set = metrics.load('set_name')
```

### List Registered Sets

```python
from zipline.finance import metrics

registered_sets = metrics.list_registered()
```

---

## Comparison with Project Metrics

### Zipline-Reloaded Native Metrics

**Strengths:**
- Integrated with backtest execution
- Automatic calculation during simulation
- Time-series tracking (every bar)
- Built-in benchmark comparison

**Limitations:**
- Limited risk metrics (only Sharpe, Sortino, max_drawdown)
- No trade-level analysis
- Known bugs with certain calendars (FOREX)
- Rolling calculations may be less accurate than full-period

### Project Metrics (`lib/metrics/`)

**Strengths:**
- Comprehensive risk metrics (omega, tail_ratio, VaR, CVaR)
- Trade-level analysis (win rate, profit factor, trade statistics)
- More accurate full-period calculations
- Better edge case handling
- Customizable (risk-free rate, trading days per year)

**Usage:**
```python
from lib.metrics import calculate_metrics

# Calculate comprehensive metrics from returns
metrics = calculate_metrics(
    returns=results['returns'],
    transactions=transactions_df,
    benchmark_returns=results['benchmark_period_return'],
    risk_free_rate=0.04,
    trading_days_per_year=252
)

# Access additional metrics
print(f"Omega Ratio: {metrics['omega']:.2f}")
print(f"Win Rate: {metrics['win_rate']:.1%}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

### Recommended Approach

1. **Use Zipline metrics for:**
   - Real-time tracking during backtest
   - Time-series analysis (plotting equity curves)
   - Basic performance metrics (returns, leverage)

2. **Use `lib/metrics/` for:**
   - Comprehensive risk analysis
   - Trade-level statistics
   - Final performance reporting
   - Strategy comparison

3. **Hybrid Approach:**
   ```python
   # Run backtest with minimal Zipline metrics
   results = run_algorithm(..., metrics_set='minimal-essential')
   
   # Calculate comprehensive metrics post-backtest
   from lib.metrics import calculate_metrics
   from lib.backtest.results_serialization import extract_transactions_dataframe
   
   transactions_df = extract_transactions_dataframe(results)
   comprehensive_metrics = calculate_metrics(
       returns=results['returns'],
       transactions=transactions_df
   )
   ```

---

## Usage Patterns

### Basic Backtest with Default Metrics

```python
from zipline import run_algorithm

def initialize(context):
    context.asset = symbol('AAPL')

def handle_data(context, data):
    # Trading logic
    pass

results = run_algorithm(
    start=pd.Timestamp('2020-01-01', tz='UTC'),
    end=pd.Timestamp('2024-01-01', tz='UTC'),
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    bundle='quandl'
)

# Access metrics
print(f"Total Return: {results['returns'].sum():.2%}")
print(f"Sharpe: {results['sharpe'].iloc[-1]:.2f}")
print(f"Max Drawdown: {results['max_drawdown'].min():.2%}")
```

### FOREX Strategy with No Metrics

```python
# FOREX strategies use metrics_set='none' to avoid bugs
results = run_algorithm(
    ...,
    metrics_set='none'
)

# Reconstruct portfolio_value and returns
from lib.backtest.results_serialization import (
    normalize_performance_dataframe,
    calculate_and_save_metrics
)

perf_normalized = normalize_performance_dataframe(results)
# Portfolio value and returns are reconstructed during save_results()
```

### Custom Metrics Tracking

```python
from zipline.api import record

def handle_data(context, data):
    # Calculate custom indicators
    rsi = calculate_rsi(context, data)
    macd = calculate_macd(context, data)
    
    # Record custom metrics
    record(
        rsi=rsi,
        macd=macd,
        signal_strength=context.signal_strength
    )

results = run_algorithm(...)

# Analyze custom metrics
results['rsi'].plot()
results['macd'].plot()
```

### Comprehensive Metrics Analysis

```python
from lib.metrics import calculate_metrics
from lib.backtest.results_serialization import extract_transactions_dataframe

# Run backtest
results = run_algorithm(...)

# Extract transactions
transactions_df = extract_transactions_dataframe(results)

# Calculate comprehensive metrics
metrics = calculate_metrics(
    returns=results['returns'],
    transactions=transactions_df,
    benchmark_returns=results.get('benchmark_period_return'),
    risk_free_rate=0.04,
    trading_days_per_year=252
)

# Print comprehensive report
print("=== Performance Metrics ===")
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Annual Return: {metrics['annual_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")
print(f"Sortino Ratio: {metrics['sortino']:.2f}")

print("\n=== Risk Metrics ===")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Omega Ratio: {metrics['omega']:.2f}")
print(f"Tail Ratio: {metrics['tail_ratio']:.2f}")

print("\n=== Trade Metrics ===")
print(f"Trade Count: {metrics['trade_count']}")
print(f"Win Rate: {metrics['win_rate']:.1%}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

---

## Best Practices

### 1. Choose Appropriate Metrics Set

- **Default**: Use for most strategies (equities, crypto)
- **Minimal**: Use for performance-critical backtests
- **None**: Use for FOREX or when calculating custom metrics

### 2. Use Zipline Metrics for Time-Series

Zipline's native metrics are optimized for time-series tracking:

```python
# Good: Use Zipline metrics for plotting
results['portfolio_value'].plot()
results['returns'].cumsum().plot()
results['max_drawdown'].plot()
```

### 3. Use lib/metrics/ for Final Analysis

For comprehensive reporting, use `lib/metrics/`:

```python
# Good: Comprehensive metrics for reporting
from lib.metrics import calculate_metrics
metrics = calculate_metrics(returns, transactions)
```

### 4. Handle Missing Columns

When `metrics_set='none'` is used, columns may be missing:

```python
# Safe access pattern
if 'portfolio_value' in results.columns:
    final_value = results['portfolio_value'].iloc[-1]
else:
    # Reconstruct from transactions
    final_value = reconstruct_portfolio_value(results)
```

### 5. Avoid Metrics Tracker Bugs

For FOREX strategies, use `metrics_set='none'`:

```python
# FOREX: Avoid metrics tracker bugs
results = run_algorithm(..., metrics_set='none')

# Calculate metrics post-backtest
metrics = calculate_metrics_from_transactions(results)
```

### 6. Record Custom Metrics Sparingly

Only record values that add value:

```python
# Good: Record key indicators
record(signal_strength=signal, rsi=rsi)

# Bad: Record everything (performance impact)
record(
    price=price,
    volume=volume,
    high=high,
    low=low,
    close=close,
    # ... too many values
)
```

### 7. Combine Native and Custom Metrics

Best of both worlds:

```python
# Native metrics for time-series
equity_curve = results['portfolio_value']

# Custom metrics for analysis
comprehensive_metrics = calculate_metrics(
    returns=results['returns'],
    transactions=transactions_df
)
```

---

## References

### Official Documentation

- [Zipline-Reloaded Repository](https://github.com/stefan-jansen/zipline-reloaded)
- [Zipline Documentation](https://zipline.ml4trading.io)

### Project Documentation

- `docs/api/metrics.md` - Project metrics API documentation
- `lib/metrics/` - Project metrics implementation
- `lib/backtest/custom_metrics.py` - Custom metrics set example
- `docs/archive/code_patterns/09_metrics/` - Metrics code patterns

### Related Components

- `lib/backtest/` - Backtest execution
- `lib/backtest/results_serialization.py` - Results processing
- `lib/plots/` - Visualization utilities

---

## Version History

- **2026-01-27**: Initial inventory created
- **Source**: Zipline-Reloaded v3.0+ (stefan-jansen/zipline-reloaded)
- **Status**: Complete inventory of Zipline-Reloaded metrics system

---

**Note:** This inventory is based on Zipline-Reloaded v3.0+. For legacy Quantopian zipline patterns, refer to migration guides. Always use Zipline-Reloaded patterns exclusively.
