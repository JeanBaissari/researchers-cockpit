# API Reference

The Researcher's Cockpit provides a comprehensive library for algorithmic trading research built on Zipline-Reloaded 3.1.0.

## Quick Navigation

| Module | Purpose | CLI Equivalent |
|--------|---------|----------------|
| [data_loader](data_loader.md) | Data ingestion, bundle management | `scripts/ingest_data.py` |
| [data_validation](data_validation.md) | OHLCV data validation, quality checks | `scripts/validate_csv_data.py` |
| [backtest](backtest.md) | Backtest execution, result saving | `scripts/run_backtest.py` |
| [utils](utils.md) | Utilities, aggregation, gap-filling | - |
| [metrics](metrics.md) | Performance metrics calculation | - |
| [optimize](optimize.md) | Grid/random search optimization | `scripts/run_optimization.py` |
| [config](config.md) | Configuration loading/validation | - |
| [report](report.md) | Report generation | `scripts/generate_report.py` |
| [validate](validate.md) | Walk-forward, Monte Carlo validation | - |

## Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Data Ingestion

```python
from lib.data_loader import ingest_bundle, list_bundles

# Ingest daily equities data
bundle_name = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL'],
    timeframe='daily'
)

# List available bundles
print(list_bundles())
```

**CLI:**
```bash
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY,AAPL
```

### Running Backtests

```python
from lib.backtest import run_backtest, save_results

# Run backtest
perf, calendar = run_backtest(
    strategy_name='spy_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Save results
result_dir = save_results('spy_sma_cross', perf, params, calendar)
```

**CLI:**
```bash
python scripts/run_backtest.py --strategy spy_sma_cross --start 2020-01-01
```

### Calculating Metrics

```python
from lib.metrics import calculate_metrics

# Calculate from returns series
metrics = calculate_metrics(returns)
print(f"Sharpe: {metrics['sharpe']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
```

### Parameter Optimization

```python
from lib.optimize import grid_search

# Grid search optimization
results = grid_search(
    strategy_name='spy_sma_cross',
    param_grid={
        'strategy.fast_period': [5, 10, 15],
        'strategy.slow_period': [30, 50, 100]
    },
    start_date='2020-01-01',
    end_date='2024-01-01',
    objective='sharpe'
)
```

**CLI:**
```bash
python scripts/run_optimization.py --strategy spy_sma_cross \
    --param strategy.fast_period:5:20:5 \
    --param strategy.slow_period:30:100:10
```

## Module Overview

### Core Modules

- **data_loader.py** - Multi-timeframe data ingestion from Yahoo Finance into Zipline bundles
- **backtest.py** - Strategy execution with Zipline, result persistence
- **metrics.py** - Empyrical-based performance metrics with trade-level analysis

### Support Modules

- **data_validation.py** - Comprehensive OHLCV data validation before ingestion
- **config.py** - YAML configuration loading with caching
- **utils.py** - Path resolution, OHLCV aggregation, gap-filling
- **extension.py** - Custom calendar registration (CRYPTO, FOREX)

### Analysis Modules

- **optimize.py** - Parameter optimization with overfit detection
- **validate.py** - Walk-forward analysis, Monte Carlo simulation
- **report.py** - Markdown report generation

## Timeframe Support

| Timeframe | Data Limit | Frequency |
|-----------|------------|-----------|
| `1m` | 7 days | minute |
| `5m` | 60 days | minute |
| `15m` | 60 days | minute |
| `30m` | 60 days | minute |
| `1h` | 730 days | minute |
| `daily` | Unlimited | daily |

## Bundle Naming Convention

```
{source}_{asset_class}_{timeframe}

Examples:
- yahoo_equities_daily
- yahoo_crypto_1h
- yahoo_forex_5m
```

## Calendar Support

| Calendar | Asset Class | Trading Days |
|----------|-------------|--------------|
| `XNYS` | Equities | Mon-Fri, NYSE hours |
| `CRYPTO` | Crypto | 24/7 |
| `FOREX` | Forex | Mon-Fri, 24h |

## Result Directory Structure

```
results/{strategy}/
├── backtest_{YYYYMMDD}_{HHMMSS}/
│   ├── returns.csv
│   ├── positions.csv
│   ├── transactions.csv
│   ├── metrics.json
│   ├── parameters_used.yaml
│   └── equity_curve.png
└── latest -> backtest_{YYYYMMDD}_{HHMMSS}/
```

## Error Handling

All functions provide descriptive error messages with suggested fixes:

```python
try:
    perf, cal = run_backtest('my_strategy', bundle='nonexistent')
except FileNotFoundError as e:
    print(e)  # Includes ingestion command to fix

try:
    bundle = ingest_bundle('yahoo', ['equities'], symbols=[])
except ValueError as e:
    print(e)  # "symbols parameter is required and cannot be empty"
```

## See Also

- [Troubleshooting Guide](../troubleshooting/common_issues.md)
- [Code Patterns](../code_patterns/)
- [Strategy Templates](../templates/strategies/)
