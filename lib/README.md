# lib/ — The Researcher's Cockpit Core Library

> **Version**: v1.12.0  
> **Architecture**: NO WRAPPERS (Direct Zipline-Reloaded + pandas APIs)  
> **Status**: Production-Ready, Modular, SOLID-Compliant

---

## Philosophy

This library provides **minimal utilities** for algorithmic trading research:

- **Use Zipline-Reloaded APIs directly** where possible
- **Use pandas/numpy directly** for data processing
- **Only add value** beyond what frameworks already provide
- **No abstraction layers** over Zipline/pandas operations

**What we DON'T do:**
- Wrap `csvdir_equities()` — Use Zipline's function directly in `extension.py`
- Wrap `get_calendar()` — Use Zipline's function directly
- Wrap `pandas.resample()` — Use pandas directly for aggregation
- Wrap bundle registration — Use Zipline's `register()` directly

**What we DO provide:**
- Custom CRYPTO (24/7) and FOREX (24/5) trading calendars
- Configuration loading from YAML files
- Performance metrics calculation
- Data quality validation (pre/post-ingestion)
- Backtest execution orchestration
- Research hypothesis tracking

---

## Architecture Overview

### Directory Structure

```
lib/
├── __init__.py              # Package root with version info
├── _exports.py              # Centralized export definitions
├── paths.py                 # Project root detection
├── utils.py                 # Core utility functions
├── pipeline_utils.py        # Zipline Pipeline helpers
├── position_sizing.py       # Position sizing algorithms
├── risk_management.py       # Risk control utilities
│
├── backtest/                # Backtest execution (11 modules)
├── bundles/                 # Bundle management (8 modules + yahoo/)
├── calendars/               # Custom calendars (5 modules)
├── config/                  # Configuration loading (10 modules)
├── data/                    # Data processing (9 modules)
├── docs/                    # Documentation utilities (2 modules)
├── logging/                 # Centralized logging (7 modules)
├── metrics/                 # Performance metrics (7 modules)
├── optimize/                # Parameter optimization (6 modules)
├── plots/                   # Visualizations (6 modules)
├── report/                  # Report generation (7 modules)
├── research/                # Hypothesis tracking (2 modules)
├── strategies/              # Strategy utilities (2 modules)
├── strategy_validation/     # Walk-forward/Monte Carlo (5 modules)
└── validation/              # Data quality checks (14 modules + validators/)
```

**Total**: 14 packages, 99 modules, ~15,000 lines of focused, modular code

---

## Package Reference

### Core Utilities

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `paths.py` | Project root detection | `get_project_root()`, `ProjectRootNotFoundError` |
| `utils.py` | Core utilities | `load_yaml()`, `save_yaml()`, `timestamp_dir()`, `ensure_dir()` |
| `pipeline_utils.py` | Zipline Pipeline helpers | Pipeline factor utilities (187 lines) |
| `position_sizing.py` | Position sizing algorithms | Equal-weight, risk-parity, Kelly, vol-targeting (250 lines) |
| `risk_management.py` | Risk controls | Drawdown limits, position limits, stop-losses (300 lines) |

### Packages (14 total)

#### 1. `backtest/` — Backtest Execution (11 modules)
Execute Zipline backtests with proper configuration and result persistence.

**Key modules**: `runner.py` (orchestrator), `execution.py` (Zipline algorithm), `results.py` (saving)

```python
from lib.backtest import run_backtest, save_results

perf, calendar = run_backtest(
    strategy_name='btc_sma_cross',
    start_date='2023-01-01',
    end_date='2024-01-01',
    capital_base=100000,
    bundle='btcusd_daily'
)

result_dir = save_results('btc_sma_cross', perf, params, calendar)
```

#### 2. `bundles/` — Bundle Management (8 modules + yahoo/)
Utilities for listing, loading, and managing Zipline data bundles.

**Key modules**: `management.py` (list/load), `access.py` (symbol lookup), `yahoo/` (Yahoo Finance ingestion)

```python
from lib.bundles import list_bundles, load_bundle, get_bundle_symbols

bundles = list_bundles()  # Returns list of bundle names
symbols = get_bundle_symbols('spy_daily')
bundle = load_bundle('spy_daily')  # Verify existence
```

**Note**: For bundle registration, use Zipline's `register()` directly in `extension.py`.

#### 3. `calendars/` — Custom Trading Calendars (5 modules)
Custom 24/7 CRYPTO and 24/5 FOREX calendars (extends exchange_calendars).

**Key modules**: `crypto.py` (CryptoCalendar), `forex.py` (ForexCalendar), `registry.py` (lookup)

```python
from zipline.utils.calendar_utils import get_calendar

# Custom calendars registered in extension.py
calendar = get_calendar('FOREX')  # 24/5 with Sunday open
calendar = get_calendar('CRYPTO')  # 24/7
```

#### 4. `config/` — Configuration Loading (10 modules)
Load and validate YAML configuration files with caching.

**Key modules**: `core.py` (settings), `strategy.py` (parameters), `assets.py` (asset configs)

```python
from lib.config import load_settings, load_strategy_params, load_asset_config

settings = load_settings()  # config/settings.yaml
params = load_strategy_params('btc_sma_cross')  # strategies/{name}/parameters.yaml
assets = load_asset_config('crypto')  # config/assets/crypto.yaml
```

#### 5. `data/` — Data Processing (9 modules)
Data normalization, FOREX handling, filtering, and sanitization.

**Key modules**: `normalization.py` (UTC, timezone), `forex.py` (FOREX-specific), `filters.py` (gaps)

```python
from lib.data import normalize_to_utc, filter_forex_presessions

df['timestamp'] = normalize_to_utc(df['timestamp'])
df = filter_forex_presessions(df, calendar)
```

**Note**: Use `pandas.resample()` directly for aggregation (NO WRAPPERS).

#### 6. `docs/` — Documentation Utilities (2 modules)
Generate section indexes for docs/ directory.

**Key module**: `section_index.py` (used by `scripts/generate_docs_indexes.py`)

#### 7. `logging/` — Centralized Logging (7 modules)
Project-wide logging with context management and specialized loggers.

**Key modules**: `config.py` (setup), `loggers.py` (specialized), `context.py` (LogContext)

```python
from lib.logging import configure_logging, get_logger
from lib.logging.loggers import backtest_logger, data_logger
from lib.logging.context import LogContext

configure_logging(level='INFO')
logger = get_logger(__name__)

with LogContext(phase='backtest', strategy='btc_sma_cross'):
    backtest_logger.info("Starting backtest")
```

#### 8. `metrics/` — Performance Metrics (7 modules)
Calculate Sharpe, Sortino, drawdown, returns, and other performance metrics.

**Key modules**: `performance.py` (Sharpe, Sortino), `risk.py` (drawdown, VaR), `core.py` (orchestrator)

```python
from lib.metrics import calculate_metrics

metrics = calculate_metrics(
    returns=perf['returns'],
    transactions=perf['transactions']
)

print(f"Sharpe: {metrics['sharpe']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
```

#### 9. `optimize/` — Parameter Optimization (6 modules)
Grid search and random search for strategy parameter optimization.

**Key modules**: `grid.py` (grid search), `random.py` (random search), `overfit.py` (detection)

```python
from lib.optimize import optimize_strategy

results = optimize_strategy(
    strategy_name='btc_sma_cross',
    param_ranges={
        'fast_period': [5, 10, 20],
        'slow_period': [30, 50, 100]
    },
    method='grid'
)
```

#### 10. `plots/` — Visualizations (6 modules)
Generate equity curves, drawdown charts, and performance visualizations.

**Key modules**: `equity.py`, `trade.py`, `returns.py`

```python
from lib.plots import plot_equity_curve, plot_drawdown

fig, ax = plot_equity_curve(perf, title='BTC SMA Cross')
fig.savefig('equity_curve.png')
```

#### 11. `report/` — Report Generation (7 modules)
Generate strategy reports and maintain strategy catalog.

**Key modules**: `strategy_report.py`, `catalog.py`

```python
from lib.report import generate_strategy_report

report = generate_strategy_report(
    strategy_name='btc_sma_cross',
    result_dir=result_dir
)
```

#### 12. `research/` — Hypothesis Tracking (2 modules)
Track trading hypotheses from idea → validation → acceptance/rejection.

**Key module**: `hypothesis.py`

```python
from lib.research import create_hypothesis, link_backtest

hypothesis = create_hypothesis(
    title="BTC momentum persistence",
    asset_class="crypto"
)
link_backtest(hypothesis.id, "backtest_20260210_143022")
```

#### 13. `strategies/` — Strategy Utilities (2 modules)
Strategy directory management, path resolution, template creation.

**Key module**: `manager.py`

```python
from lib.strategies import get_strategy_path, create_strategy

path = get_strategy_path('btc_sma_cross', asset_class='crypto')
new_strategy = create_strategy('new_strategy', 'equities')
```

#### 14. `strategy_validation/` — Strategy Robustness (5 modules)
Walk-forward analysis and Monte Carlo simulation for strategy validation.

**Key modules**: `walkforward.py`, `montecarlo.py`

```python
from lib.strategy_validation import run_walkforward

wf_results = run_walkforward(
    strategy_name='btc_sma_cross',
    windows=6,
    train_size=250,
    test_size=60
)
```

**Note**: Distinct from `lib/validation/` which validates **data quality**, not strategy robustness.

#### 15. `validation/` — Data Quality Checks (14 modules + validators/)
Pre/post-ingestion OHLCV validation, bundle integrity, backtest result verification.

**Key modules**: `data_validator.py` (orchestrator), `api.py` (convenience functions), `validators/` (asset-specific)

```python
from lib.validation import DataValidator, ValidationConfig, validate_before_ingest

# Pre-ingestion validation
result = validate_before_ingest(
    df=df,
    asset_name='EURUSD',
    timeframe='1h',
    asset_type='forex'
)

if not result.is_valid:
    print(result.summary())
```

**Asset-specific validators**: `EquityValidator`, `ForexValidator`, `CryptoValidator`

---

## Import Patterns

### Standard Imports

```python
# Configuration
from lib.config import load_settings, load_strategy_params

# Backtest execution
from lib.backtest import run_backtest, save_results

# Metrics & visualization
from lib.metrics import calculate_metrics
from lib.plots import plot_equity_curve

# Data validation
from lib.validation import DataValidator, ValidationConfig

# Bundle management
from lib.bundles import list_bundles, get_bundle_symbols

# Logging
from lib.logging import configure_logging, get_logger
from lib.logging.context import LogContext
```

### Package-Level vs Module-Level Imports

```python
# ✅ GOOD - Import from package when available
from lib.metrics import calculate_metrics  # From __init__.py

# ✅ ALSO GOOD - Import from specific module if needed
from lib.metrics.performance import calculate_sharpe_ratio

# ❌ BAD - Relative imports
from ..metrics import calculate_metrics  # Never use relative!
```

---

## Architecture Standards

### File Size Limits

- **Maximum**: 350 lines per module
- **Target**: ~150-250 lines per module
- **Action**: Split into focused submodules when approaching 350

### SOLID Principles

- **Single Responsibility**: Each module has ONE concern
- **Open/Closed**: Extend via composition, not modification
- **DRY**: Extract common logic to shared utilities
- **Dependency Inversion**: Depend on abstractions (use `lib/config/`, not hardcoded values)

### Module Organization

```python
# Standard module structure:
"""
Module docstring explaining purpose.
"""

# Standard library imports
import os
from pathlib import Path

# Third-party imports
import pandas as pd
import numpy as np

# Local imports
from lib.paths import get_project_root
from lib.config import load_settings

# Functions
def main_function():
    """Function docstring."""
    pass

# Public API
__all__ = ['main_function']
```

---

## Key Distinctions

### validation/ vs strategy_validation/

- **`lib/validation/`**: Data quality checks (OHLCV, bundles, backtest results)
- **`lib/strategy_validation/`**: Strategy robustness checks (walk-forward, Monte Carlo)

### data/ vs bundles/

- **`lib/data/`**: Data processing (normalization, filtering, FOREX handling)
- **`lib/bundles/`**: Bundle management (listing, loading, symbol lookup)

### metrics/ vs plots/

- **`lib/metrics/`**: Calculate numerical metrics (returns dict/DataFrame)
- **`lib/plots/`**: Generate visualizations (returns matplotlib figures)

### report/ vs strategy_report.py

- **`lib/report/`**: Report generation package (7 modules)
- **`lib/report/strategy_report.py`**: Individual strategy report generator

---

## Version History

### v1.12.0 (2026-01-26) — NO WRAPPERS Architecture
- **Deleted**: `lib/bundles/csv/` (use `csvdir_equities()` directly)
- **Deleted**: `lib/bundles/registry.py` (use Zipline's `bundles` dict)
- **Deleted**: `lib/calendars/sessions/` (use `get_calendar()` directly)
- **Deleted**: `lib/data/aggregation.py` (use `pandas.resample()` directly)
- **Result**: 5,042 lines removed (33% reduction), 100% direct API usage

### v1.11.0 (2026-01-19) — Modular Refactoring
- Split 7 monolithic files (9,500 lines) into 35 focused modules (~220 lines avg)
- Created modular packages: `validation/`, `bundles/`, `metrics/`, `backtest/`
- Achieved 100% modularity compliance (all files < 350 lines)

### v1.10.0 (2026-01-15) — Pipeline Validation
- Fixed CSV bundle naming, gap filling, calendar alignment
- Added comprehensive testing (38 new test cases)

### v1.0.7 (2025-01-17) — Data Validation API
- Introduced `ValidationResult`, `ValidationConfig`, `DataValidator`
- Asset-specific validators (equity, forex, crypto)

---

## Usage Examples

### Complete Research Workflow

```python
# 1. Configuration
from lib.config import load_settings, load_strategy_params

settings = load_settings()
params = load_strategy_params('btc_sma_cross')

# 2. Data validation (optional but recommended)
from lib.validation import validate_bundle

result = validate_bundle('btcusd_daily')
if not result.is_valid:
    print(result.summary())

# 3. Backtest execution
from lib.backtest import run_backtest, save_results

perf, calendar = run_backtest(
    strategy_name='btc_sma_cross',
    start_date='2023-01-01',
    end_date='2024-01-01',
    capital_base=100000,
    bundle='btcusd_daily'
)

result_dir = save_results('btc_sma_cross', perf, params, calendar)

# 4. Metrics calculation
from lib.metrics import calculate_metrics

metrics = calculate_metrics(
    returns=perf['returns'],
    transactions=perf['transactions']
)

# 5. Visualization
from lib.plots import plot_equity_curve

fig, ax = plot_equity_curve(perf)
fig.savefig(result_dir / 'equity_curve.png')

# 6. Report generation
from lib.report import generate_strategy_report

report = generate_strategy_report('btc_sma_cross', result_dir)
```

### Direct Zipline Usage (Encouraged)

```python
# Bundle management
from zipline.data.bundles import bundles, ingest

bundles.keys()  # List bundles
ingest('btcusd_daily')  # Ingest bundle

# Calendar access
from zipline.utils.calendar_utils import get_calendar

calendar = get_calendar('FOREX')

# Data aggregation
import pandas as pd

daily = minute_df.resample('1D').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})
```

---

## Module Count by Package

| Package | Modules | Purpose |
|---------|---------|---------|
| `validation/` | 14 + validators/ | Data quality validation |
| `backtest/` | 11 | Backtest execution |
| `config/` | 10 | Configuration loading |
| `data/` | 9 | Data processing |
| `bundles/` | 8 + yahoo/ | Bundle management |
| `logging/` | 7 | Centralized logging |
| `metrics/` | 7 | Performance metrics |
| `report/` | 7 | Report generation |
| `optimize/` | 6 | Parameter optimization |
| `plots/` | 6 | Visualizations |
| `calendars/` | 5 | Custom calendars |
| `strategy_validation/` | 5 | Strategy robustness |
| `docs/` | 2 | Doc utilities |
| `research/` | 2 | Hypothesis tracking |
| `strategies/` | 2 | Strategy utilities |

---

## Canonical Module Map

**Use this map to avoid ghost references and ensure correct imports:**

| Purpose | Canonical Path | Do NOT Use |
|---------|----------------|------------|
| Performance metrics | `lib/metrics/` | ~~lib/analysis/~~ |
| Visualizations | `lib/plots/` | ~~lib/visualization/~~ |
| Data quality checks | `lib/validation/` | ~~lib/data/validation/~~ (different purpose) |
| Bundle ingestion | `lib/bundles/` | ~~lib/data/ingest/~~ |
| Config loading | `lib/config/core.py` | ~~lib/config/loader.py~~ |
| Report generation | `lib/report/` | ~~lib/reports/~~ (no 's') |
| Backtest execution | `lib/backtest/` | Direct Zipline also OK |

---

## Testing

All packages have corresponding test modules in `tests/`:

```bash
# Run all lib/ tests
pytest tests/ -v

# Run specific package tests
pytest tests/backtest/ -v
pytest tests/validation/ -v
pytest tests/metrics/ -v

# Import smoke test
python -c "from lib import *"
```

**Test coverage**: 34 test files covering core functionality (per v1.11.1).

---

## Development Guidelines

### Adding New Modules

1. **Check DRY**: Does this functionality exist in Zipline/pandas already?
2. **Check lib/**: Does a similar utility exist in another package?
3. **Follow SOLID**: One concern per module, < 350 lines
4. **Add tests**: Create corresponding `tests/{package}/test_{module}.py`
5. **Export**: Add to package `__init__.py` with `__all__`

### Modifying Existing Modules

1. **Verify tests pass**: `pytest tests/{package}/ -v`
2. **Check line count**: `wc -l lib/{package}/{module}.py` (must stay < 350)
3. **Update `__all__`**: If adding/removing public functions
4. **Update docs**: If changing public API

### Splitting Oversized Modules

If a module approaches 350 lines:

1. Identify separate concerns within the module
2. Extract to new focused modules
3. Keep original module as orchestrator
4. Update imports and `__all__`
5. Update tests to cover new structure

---

## Common Pitfalls

### 1. Ghost Module References
Don't reference modules that don't exist:
- ❌ `lib/analysis/` (use `lib/metrics/`)
- ❌ `lib/visualization/` (use `lib/plots/`)
- ❌ `lib/execution/` (doesn't exist)

### 2. Creating Wrappers
Don't wrap Zipline/pandas APIs:
- ❌ Custom bundle registration wrappers (use `register()` directly)
- ❌ Custom aggregation functions (use `pandas.resample()`)
- ❌ Session managers (use `get_calendar()` directly)

### 3. Hardcoded Paths
Always use `lib/paths.py`:
- ✅ `get_project_root()` for project root
- ❌ `Path(__file__).parent.parent` (fragile)

### 4. Direct Logging
Always use `lib/logging/`:
- ✅ `from lib.logging import get_logger`
- ❌ `import logging; logging.basicConfig()` (inconsistent)

---

## Related Documentation

- **Architecture rules**: `.cursor/rules/architecture.mdc`
- **Import patterns**: `.cursor/rules/imports.mdc`
- **Logging standards**: `.cursor/rules/logging.mdc`
- **Error handling**: `.cursor/rules/error-handling.mdc`
- **API documentation**: `docs/api/`
- **Code patterns**: `docs/code_patterns/`

---

## Quick Command Reference

```bash
# List all packages
ls lib/

# Count modules per package
find lib/ -name "*.py" | grep -v __pycache__ | wc -l

# Check package exports
python -c "from lib.backtest import *; print('OK')"

# Find large modules (>300 lines)
find lib/ -name "*.py" -exec wc -l {} \; | grep -v __pycache__ | awk '$1 > 300 {print}'

# Run tests for specific package
pytest tests/backtest/ -v
```

---

**Last Updated**: 2026-02-09  
**Version**: v1.12.0  
**Status**: ✅ Production-Ready, Zero Legacy Patterns, 100% Direct API Usage
