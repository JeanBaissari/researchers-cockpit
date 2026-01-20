# API Reference

The Researcher's Cockpit provides a comprehensive library for algorithmic trading research built on Zipline-Reloaded 3.1.0.

**Version:** v1.11.0 (Modular Architecture)

---

## Quick Navigation

### Core Data & Configuration

| Module | Purpose | CLI Equivalent |
|--------|---------|----------------|
| [bundles](bundles.md) | Data ingestion, bundle management | `scripts/ingest_data.py` |
| [validation](validation.md) | OHLCV data validation, quality checks | `scripts/validate_csv_data.py` |
| [data](data.md) | Data processing, aggregation, normalization | - |
| [calendars](calendars.md) | Trading calendars (CRYPTO, FOREX) | - |
| [config](config.md) | Configuration loading/validation | - |
| [strategies](strategies.md) | Strategy path resolution, creation | - |

### Execution & Analysis

| Module | Purpose | CLI Equivalent |
|--------|---------|----------------|
| [backtest](backtest.md) | Backtest execution, result saving | `scripts/run_backtest.py` |
| [metrics](metrics.md) | Performance metrics calculation | - |
| [optimize](optimize.md) | Grid/random search optimization | `scripts/run_optimization.py` |
| [validate](validate.md) | Walk-forward, Monte Carlo validation | - |
| [report](report.md) | Report generation | `scripts/generate_report.py` |

### Utilities & Infrastructure

| Module | Purpose | CLI Equivalent |
|--------|---------|----------------|
| [paths](paths.md) | Path resolution, project root discovery | - |
| [utils](utils.md) | File operations, YAML handling | - |
| [pipeline_utils](pipeline_utils.md) | Zipline Pipeline helper utilities | - |
| [position_sizing](position_sizing.md) | Position sizing algorithms | - |
| [risk_management](risk_management.md) | Risk management utilities | - |
| [logging](logging.md) | Centralized logging system | - |
| [plots](plots.md) | Visualization utilities (optional) | - |

---

## Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install visualization dependencies
pip install matplotlib seaborn
```

---

## Quick Start

### Data Ingestion

```python
from lib.bundles import ingest_bundle, list_bundles

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

### Data Validation

```python
from lib.validation import validate_bundle, DataValidator

# Validate bundle before backtest
result = validate_bundle('yahoo_equities_daily')
if not result.is_valid:
    print(f"Validation failed: {result.errors}")

# Pre-ingestion validation
from lib.validation import validate_before_ingest
result = validate_before_ingest(df, asset_class='equities', timeframe='daily')
```

### Running Backtests

```python
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params

# Run backtest
perf, calendar = run_backtest(
    strategy_name='spy_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Save results
params = load_strategy_params('spy_sma_cross')
result_dir = save_results(
    strategy_name='spy_sma_cross',
    perf=perf,
    params=params
)
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

### Visualization

```python
from lib.plots import plot_all
from pathlib import Path

# Generate all standard plots
plot_all(
    returns=perf['returns'].dropna(),
    portfolio_value=perf['portfolio_value'],
    transactions=perf['transactions'],
    save_dir=Path('results/my_strategy/latest'),
    strategy_name='My Strategy'
)
```

---

## Module Overview

### Core Data Modules

- **bundles/** - Multi-timeframe data ingestion from Yahoo Finance and CSV into Zipline bundles
  - Supports multiple sources (yahoo, csv)
  - Multi-timeframe support (1m, 5m, 15m, 30m, 1h, daily)
  - Bundle registry and management
  - Session alignment validation (v1.1.0)

- **validation/** - Comprehensive OHLCV data validation before ingestion
  - Asset-specific validators (equity, forex, crypto)
  - Pre-ingestion, bundle, and backtest result validation
  - ValidationConfig with strict/lenient presets
  - Automatic fix suggestions

- **data/** - Data processing utilities
  - OHLCV aggregation and resampling
  - Timezone normalization (UTC)
  - FOREX-specific processing
  - Calendar-based filtering

- **calendars/** - Trading calendar support
  - Custom CRYPTO calendar (24/7)
  - Custom FOREX calendar (24/5)
  - Calendar registry and management
  - Session alignment validation (v1.1.0)

### Execution Modules

- **backtest/** - Strategy execution with Zipline, result persistence
  - Modular structure: preprocessing, execution, results
  - BacktestConfig for configuration
  - Automatic result serialization and persistence

- **metrics/** - Performance metrics calculation
  - Performance metrics (Sharpe, Sortino, returns)
  - Risk metrics (drawdown, alpha, beta, VaR)
  - Trade-level metrics
  - Rolling window metrics

- **optimize/** - Parameter optimization with overfit detection
  - Grid search and random search
  - Train/test split utilities
  - Overfit probability calculation

- **validate/** - Strategy validation (walk-forward, Monte Carlo)
  - Walk-forward analysis
  - Monte Carlo simulation
  - Validation metrics and efficiency calculation

- **report/** - Markdown report generation
  - Individual strategy reports
  - Strategy catalog management
  - Weekly summary reports

### Utility Modules

- **paths/** - Path resolution and project root discovery
  - Marker-based root detection
  - Directory path resolution
  - Project structure validation

- **utils/** - Core utility functions
  - File operations (ensure_dir, timestamp_dir)
  - YAML loading/saving
  - Symlink management

- **pipeline_utils/** - Zipline Pipeline helper utilities
  - Pipeline setup and configuration
  - Factor construction helpers

- **position_sizing/** - Position sizing algorithms
  - Fixed, volatility-scaled, and Kelly Criterion sizing

- **risk_management/** - Risk management utilities
  - Stop loss, trailing stop, take profit
  - Exit condition checking

- **logging/** - Centralized logging system
  - Structured logging with context
  - Specialized loggers for different components
  - LogContext for enhanced logging

- **plots/** - Visualization utilities (optional dependency)
  - Equity curves, drawdown charts
  - Monthly returns heatmaps
  - Trade analysis and rolling metrics

- **strategies/** - Strategy management
  - Strategy path resolution
  - Strategy creation from template
  - Symlink management

---

## Timeframe Support

| Timeframe | Data Limit | Frequency | Notes |
|-----------|------------|-----------|-------|
| `1m` | 7 days | minute | Yahoo Finance limit |
| `5m` | 60 days | minute | Yahoo Finance limit |
| `15m` | 60 days | minute | Yahoo Finance limit |
| `30m` | 60 days | minute | Yahoo Finance limit |
| `1h` | 730 days | minute | Yahoo Finance limit |
| `daily` | Unlimited | daily | No limit |

**Note:** CSV sources have no timeframe limits. Data limits apply only to Yahoo Finance API sources.

---

## Bundle Naming Convention

```
{source}_{asset_class}_{timeframe}

Examples:
- yahoo_equities_daily
- yahoo_crypto_1h
- csv_forex_5m
- csv_eurusd_1m
```

---

## Calendar Support

| Calendar | Asset Class | Trading Days | Hours |
|----------|-------------|--------------|-------|
| `XNYS` | Equities | Mon-Fri, NYSE hours | 9:30 AM - 4:00 PM ET |
| `CRYPTO` | Crypto | 24/7 | All days, all hours |
| `FOREX` | Forex | Mon-Fri, 24h | Weekdays only, continuous |

**Custom Calendars:**
- Automatically registered via `lib/calendars/`
- Session alignment validation available (v1.1.0)
- See [Calendars API](calendars.md) for details

---

## Result Directory Structure

```
results/{strategy}/
├── backtest_{YYYYMMDD}_{HHMMSS}/
│   ├── returns.csv
│   ├── positions.csv
│   ├── transactions.csv
│   ├── metrics.json
│   ├── parameters_used.yaml
│   ├── equity_curve.png
│   ├── drawdown.png
│   ├── monthly_returns.png
│   └── rolling_metrics.png
└── latest -> backtest_{YYYYMMDD}_{HHMMSS}/
```

---

## Import Path Standards

### ✅ Canonical Imports (v1.11.0)

```python
# Data packages
from lib.bundles import ingest_bundle, list_bundles
from lib.validation import DataValidator, validate_bundle
from lib.data import aggregate_ohlcv, normalize_to_utc
from lib.calendars import register_custom_calendars, CryptoCalendar

# Execution
from lib.backtest import run_backtest, save_results
from lib.metrics import calculate_metrics
from lib.optimize import grid_search, random_search
from lib.validate import walk_forward, monte_carlo

# Utilities
from lib.paths import get_project_root, get_strategies_dir
from lib.utils import ensure_dir, timestamp_dir, load_yaml
from lib.strategies import get_strategy_path, create_strategy
from lib.pipeline_utils import setup_pipeline
from lib.position_sizing import compute_position_size
from lib.risk_management import check_exit_conditions
from lib.logging import configure_logging, LogContext
from lib.plots import plot_all, plot_equity_curve
```

### ❌ Deprecated Imports (Do Not Use)

```python
# OLD - Do not use
from lib.data_loader import ingest_bundle  # Use lib.bundles
from lib.data_validation import DataValidator  # Use lib.validation
from lib.extension import register_custom_calendars  # Use lib.calendars
from lib.utils import get_project_root  # Use lib.paths
```

---

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

---

## Architecture Notes

**v1.11.0 Modular Architecture:**
- All modules follow SOLID principles
- Single Responsibility: Each module < 150 lines
- Modular packages: `lib/bundles/`, `lib/validation/`, `lib/calendars/`, etc.
- Canonical import paths from `lib/_exports.py`
- Zero legacy patterns or deprecated modules

**Key Distinctions:**
- `lib/validate/` - Strategy validation (walk-forward, Monte Carlo)
- `lib/validation/` - Data validation (OHLCV, bundles, results)
- `lib/data/` - Data processing (aggregation, normalization)
- `lib/bundles/` - Bundle management (ingestion, registry)

---

## See Also

- [Troubleshooting Guide](../troubleshooting/common_issues.md)
- [Code Patterns](../code_patterns/)
- [Strategy Templates](../templates/strategies/)
- [Project Structure](../project_structure.md)