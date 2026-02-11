# Scripts Reference Guide

**Complete command-line interface reference for The Researcher's Cockpit.**

---

## Purpose

This document provides comprehensive reference for all command-line scripts in the `scripts/` directory. These scripts form the primary interface for data ingestion, backtesting, optimization, analysis, and validation workflows.

Each script is designed for both interactive use and automation, with consistent CLI patterns, helpful error messages, and integration with the project's logging system.

---

## Scope

### What This Document Covers

- Complete CLI reference for all user-facing scripts
- Usage examples for common workflows
- Parameter descriptions and valid values
- Error handling and troubleshooting tips
- Integration with lib/ modules

### What This Document Does NOT Cover

- Internal script implementation details (see source code)
- Library API documentation (see [API Reference](api/README.md))
- Strategy development (see [Strategy Catalog](strategy_catalog.md))
- Archived one-time utility scripts (see `scripts/archive/`)

---

## Quick Navigation

| Script | Purpose | Common Usage |
|--------|---------|--------------|
| [ingest_data.py](#ingest_datapy) | Ingest market data into Zipline bundles | `python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY` |
| [run_backtest.py](#run_backtestpy) | Execute strategy backtests | `python scripts/run_backtest.py --strategy my_strategy` |
| [run_optimization.py](#run_optimizationpy) | Optimize strategy parameters | `python scripts/run_optimization.py --strategy my_strategy --param strategy.fast:5:20:5` |
| [generate_report.py](#generate_reportpy) | Generate markdown reports | `python scripts/generate_report.py --strategy my_strategy` |
| [validate_bundles.py](#validate_bundlespy) | Validate bundle integrity | `python scripts/validate_bundles.py` |
| [bundle_info.py](#bundle_infopy) | Display bundle information | `python scripts/bundle_info.py my_bundle` |

---

## Core Scripts

### ingest_data.py

**Purpose:** Ingest market data from various sources into Zipline bundles.

**Path:** `scripts/ingest_data.py`

**Dependencies:** `lib.bundles`, `lib.logging`

#### Synopsis

```bash
python scripts/ingest_data.py [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source` | choice | required | Data source: `yahoo`, `binance`, `oanda`, `csv` |
| `--assets` | choice | required | Asset class: `crypto`, `forex`, `equities` |
| `--symbols` | text | required | Comma-separated symbol list (e.g., `SPY,AAPL`) |
| `--bundle-name` | text | optional | Custom bundle name base (timeframe appended) |
| `--start-date` | date | optional | Start date in YYYY-MM-DD format |
| `--end-date` | date | optional | End date in YYYY-MM-DD format |
| `--calendar` | text | optional | Trading calendar (auto-detected if omitted) |
| `--timeframe` | choice | `daily` | Data timeframe (see [Timeframes](#timeframes)) |
| `--ingest-daily` | flag | false | Ingest daily data bundle |
| `--ingest-intraday` | flag | false | Ingest intraday bundle (uses --timeframe) |
| `--force` | flag | false | Force re-ingestion even if bundle exists |
| `--list-timeframes` | flag | false | Display available timeframes and limits |

#### Timeframes

| Timeframe | Yahoo API Limit | Notes |
|-----------|-----------------|-------|
| `1m` | 7 days | One-minute bars |
| `5m` | 60 days | Five-minute bars |
| `15m` | 60 days | Fifteen-minute bars |
| `30m` | 60 days | Thirty-minute bars |
| `1h` | 730 days | Hourly bars |
| `daily` | unlimited | End-of-day bars |

**Note:** Limits apply to Yahoo Finance API only. CSV sources use full available data.

#### Bundle Naming Convention (v1.12.0+)

- **Format:** `{symbol}_{timeframe}` (e.g., `spy_daily`, `btcusd_1h`)
- **Legacy format:** `{source}_{assets}_{timeframe}` (deprecated)

#### Usage Examples

**Basic daily equity data:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets equities \
  --symbols SPY
```

**Hourly crypto data:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets crypto \
  --symbols BTC-USD \
  --timeframe 1h
```

**Multiple symbols with custom bundle name:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets forex \
  --symbols EURUSD=X,GBPUSD=X \
  --bundle-name forex_majors \
  --timeframe daily
```

**Both daily and hourly data:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets equities \
  --symbols SPY \
  --timeframe 1h \
  --ingest-daily \
  --ingest-intraday
```

**CSV ingestion (full historical data):**
```bash
python scripts/ingest_data.py \
  --source csv \
  --assets forex \
  --symbols EURUSD,NZDJPY \
  --timeframe 1m
```

#### Output

- Success: Ingested bundle name and next steps
- Failure: Error message with suggested fix

#### Related

- [API: bundles](api/bundles.md) - Bundle management API
- [Code Pattern: CSV Ingestion](code_patterns/csv_ingestion_best_practices.md)
- [Troubleshooting: Data Ingestion](troubleshooting/data_ingestion.md)

---

### run_backtest.py

**Purpose:** Execute strategy backtests with automatic result storage.

**Path:** `scripts/run_backtest.py`

**Dependencies:** `lib.backtest`, `lib.config`, `lib.strategies`, `lib.logging`

#### Synopsis

```bash
python scripts/run_backtest.py [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | text | required | Strategy name (e.g., `spy_sma_cross`) |
| `--start` | date | optional | Start date (YYYY-MM-DD) |
| `--end` | date | optional | End date (YYYY-MM-DD) |
| `--capital` | float | optional | Starting capital (overrides config) |
| `--bundle` | text | optional | Bundle name (auto-detected from strategy) |
| `--asset-class` | choice | optional | Asset class hint: `crypto`, `forex`, `equities` |
| `--data-frequency` | choice | optional | Data frequency: `daily`, `minute` (auto-detected) |
| `--skip-warmup-check` | flag | false | Skip warmup period validation |
| `--validate-calendar` | flag | false | Strict calendar validation (v1.1.0+) |

#### Usage Examples

**Basic backtest:**
```bash
python scripts/run_backtest.py --strategy spy_sma_cross
```

**Custom date range:**
```bash
python scripts/run_backtest.py \
  --strategy my_forex_strategy \
  --start 2020-01-01 \
  --end 2023-12-31
```

**Specify bundle and capital:**
```bash
python scripts/run_backtest.py \
  --strategy crypto_momentum \
  --bundle btcusd_daily \
  --capital 50000
```

**Strict validation for forex:**
```bash
python scripts/run_backtest.py \
  --strategy forex_breakout \
  --asset-class forex \
  --validate-calendar
```

#### Output Structure

Results saved to `results/{strategy_name}/{timestamp}/`:
- `performance.csv` - Full Zipline performance DataFrame
- `metrics.json` - Calculated performance metrics
- `parameters.yaml` - Strategy parameters used
- `calendar_info.json` - Trading calendar metadata
- `recorded_vars/` - Strategy-recorded variables

Symlink created: `results/{strategy_name}/latest/` → most recent run

#### Performance Metrics Displayed

- Total Return (%)
- Annual Return (%)
- Sharpe Ratio
- Max Drawdown (%)

#### Related

- [API: backtest](api/backtest.md) - Backtest execution API
- [API: metrics](api/metrics.md) - Performance metrics
- [Troubleshooting: Backtesting](troubleshooting/backtesting.md)

---

### run_optimization.py

**Purpose:** Run grid search or random search parameter optimization.

**Path:** `scripts/run_optimization.py`

**Dependencies:** `lib.optimize`, `lib.config`, `lib.paths`, `lib.logging`

#### Synopsis

```bash
python scripts/run_optimization.py [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | text | required | Strategy name |
| `--method` | choice | `grid` | Optimization method: `grid`, `random` |
| `--param` | text | required | Parameter range (repeatable) |
| `--start` | date | optional | Start date (YYYY-MM-DD) |
| `--end` | date | optional | End date (YYYY-MM-DD) |
| `--objective` | choice | `sharpe` | Objective: `sharpe`, `sortino`, `total_return`, `calmar` |
| `--train-pct` | float | `0.7` | Training data percentage (0-1) |
| `--n-iter` | int | `100` | Number of iterations (random search only) |
| `--capital` | float | optional | Starting capital |
| `--bundle` | text | optional | Bundle name |
| `--asset-class` | choice | optional | Asset class hint |

#### Parameter Range Formats

**Range with step:**
```
--param strategy.fast_period:5:20:5
# Values: [5, 10, 15, 20]
```

**Explicit values:**
```
--param strategy.slow_period:30,50,100
# Values: [30, 50, 100]
```

**Multiple parameters:**
```
--param strategy.fast:5:20:5 \
--param strategy.slow:30:100:10
# Grid: 4 × 8 = 32 combinations
```

#### Usage Examples

**Grid search optimization:**
```bash
python scripts/run_optimization.py \
  --strategy spy_sma_cross \
  --method grid \
  --param strategy.fast_period:5:20:5 \
  --param strategy.slow_period:30:100:10 \
  --objective sharpe
```

**Random search with explicit values:**
```bash
python scripts/run_optimization.py \
  --strategy momentum_strategy \
  --method random \
  --param strategy.lookback:10,20,30,60 \
  --param strategy.threshold:0.01,0.02,0.05 \
  --n-iter 50 \
  --train-pct 0.8
```

**Custom date range and objective:**
```bash
python scripts/run_optimization.py \
  --strategy mean_reversion \
  --param strategy.z_score:1.5:3.0:0.5 \
  --start 2015-01-01 \
  --end 2023-12-31 \
  --objective sortino
```

#### Output

Results saved to `results/{strategy_name}/latest/`:
- `optimization_results.csv` - All parameter combinations and metrics
- `best_params.json` - Best parameters found
- `overfit_score.json` - Overfitting analysis (efficiency, PBO)

#### Displayed Information

- Parameter grid
- Total combinations tested
- Best parameters
- Best performance (train/test)
- Overfit analysis (efficiency, PBO, verdict)

#### Related

- [API: optimize](api/optimize.md) - Optimization API
- [API: validate](api/validate.md) - Walk-forward validation

---

### generate_report.py

**Purpose:** Generate markdown reports from strategy results.

**Path:** `scripts/generate_report.py`

**Dependencies:** `lib.report`, `lib.paths`, `lib.logging`

#### Synopsis

```bash
python scripts/generate_report.py [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | text | required | Strategy name |
| `--type` | choice | `backtest` | Result type: `backtest`, `optimization`, `walkforward` |
| `--output` | path | optional | Custom output path |
| `--asset-class` | choice | optional | Asset class hint |
| `--update-catalog` | flag | false | Update strategy catalog |
| `--status` | choice | `testing` | Strategy status: `testing`, `validated`, `abandoned` |

#### Usage Examples

**Basic backtest report:**
```bash
python scripts/generate_report.py --strategy spy_sma_cross
```

**Optimization report:**
```bash
python scripts/generate_report.py \
  --strategy momentum_strategy \
  --type optimization
```

**Generate report and update catalog:**
```bash
python scripts/generate_report.py \
  --strategy validated_strategy \
  --update-catalog \
  --status validated
```

**Custom output location:**
```bash
python scripts/generate_report.py \
  --strategy my_strategy \
  --output reports/custom_report.md
```

#### Output

- Default location: `reports/{strategy}_report_{timestamp}.md`
- Strategy catalog updated (if `--update-catalog` flag set)

#### Report Contents

**Backtest Report:**
- Strategy overview
- Parameters used
- Performance metrics
- Risk metrics
- Trade analysis
- Equity curve (if plots exist)

**Optimization Report:**
- Parameter grid
- Best parameters
- Train/test performance
- Overfitting analysis
- Parameter sensitivity

**Walkforward Report:**
- Analysis windows
- In-sample/out-of-sample results
- Consistency metrics
- Robustness assessment

#### Related

- [API: report](api/report.md) - Report generation API
- [Strategy Catalog](strategy_catalog.md)

---

### validate_bundles.py

**Purpose:** Validate bundle registry integrity and detect corruption.

**Path:** `scripts/validate_bundles.py`

**Dependencies:** `lib.bundles`, `lib.calendars`, `lib.logging`, `exchange_calendars`

#### Synopsis

```bash
python scripts/validate_bundles.py [OPTIONS]
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--bundle` | text | optional | Specific bundle to validate |
| `--fix` | flag | false | Auto-fix corrupted entries |
| `--verbose` | flag | false | Detailed validation output |

#### Usage Examples

**Validate all bundles:**
```bash
python scripts/validate_bundles.py
```

**Validate specific bundle:**
```bash
python scripts/validate_bundles.py --bundle spy_daily
```

**Auto-fix corrupted entries:**
```bash
python scripts/validate_bundles.py --fix
```

**Detailed validation:**
```bash
python scripts/validate_bundles.py --bundle my_bundle --verbose
```

#### Validation Checks

1. **Registry file integrity** - JSON syntax and structure
2. **Bundle data existence** - Directories on disk
3. **Calendar validity** - Registered calendars
4. **Timeframe validity** - Valid timeframe values
5. **Data frequency validity** - Valid Zipline frequencies
6. **Source validity** - Valid data sources
7. **Asset class validity** - Valid asset classes
8. **Date ranges** - Logical start/end dates

#### Output Format

```
Bundle: spy_daily
  Status: ✓ Valid
  Source: yahoo
  Assets: equities
  Calendar: NYSE
  Timeframe: daily
  Date Range: 2010-01-04 to 2024-12-31
  Data Exists: ✓ Yes

Bundle: corrupted_bundle
  Status: ✗ Invalid
  Issues:
    - Calendar 'INVALID' not registered
    - Bundle data directory missing
  Fix: python scripts/validate_bundles.py --bundle corrupted_bundle --fix
```

#### Related

- [API: bundles](api/bundles.md) - Bundle management
- [API: validation](api/validation.md) - Data validation
- [Troubleshooting: Data Ingestion](troubleshooting/data_ingestion.md)

---

### bundle_info.py

**Purpose:** Display detailed bundle information including symbols, dates, and bar counts.

**Path:** `scripts/bundle_info.py`

**Dependencies:** `lib.bundles`, `lib.logging`

#### Synopsis

```bash
python scripts/bundle_info.py [BUNDLE_NAME] [OPTIONS]
```

#### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `BUNDLE_NAME` | text | Bundle name (required unless `--list` used) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--list` | flag | false | List all available bundles |
| `--verbose` | flag | false | Show detailed health check |

#### Usage Examples

**Show bundle information:**
```bash
python scripts/bundle_info.py spy_daily
```

**List all bundles:**
```bash
python scripts/bundle_info.py --list
```

**Detailed health check:**
```bash
python scripts/bundle_info.py spy_daily --verbose
```

#### Output Format

**Standard output:**
```
Bundle: spy_daily
Source: yahoo
Calendar: NYSE
Timeframe: daily

Symbols (1):
  - SPY

Date Range: 2010-01-04 to 2024-12-31 (3,762 trading days)
Total Bars: 3,762

Health Status: ✓ Healthy
```

**Verbose output includes:**
- Per-symbol date ranges
- Bar count per symbol
- Data quality metrics
- Missing data periods
- Trading calendar info

#### Related

- [API: bundles](api/bundles.md)
- [Bundle Inventory](api/bundle_inventory.md)

---

## Utility Scripts

### verify_exports.py

**Purpose:** Verify `lib/` package exports are consistent.

**Path:** `scripts/verify_exports.py`

**Usage:**
```bash
python scripts/verify_exports.py
```

**Output:** Lists all `__init__.py` files and verifies exports match modules.

---

### verify_critical_coverage.py

**Purpose:** Verify test coverage for critical modules.

**Path:** `scripts/verify_critical_coverage.py`

**Usage:**
```bash
python scripts/verify_critical_coverage.py
```

**Output:** Coverage report for backtest, bundles, validation, metrics modules.

---

### coverage_report.py

**Purpose:** Generate comprehensive test coverage report.

**Path:** `scripts/coverage_report.py`

**Usage:**
```bash
python scripts/coverage_report.py
```

**Output:** HTML coverage report in `htmlcov/` directory.

---

## Archived Scripts

One-time utility scripts have been moved to `scripts/archive/`. These completed specific migration or setup tasks and are preserved for historical reference.

**Notable archived scripts:**
- `enforce_doc_standards.py` - Documentation standardization (completed)
- `apply_doc_fixes.py` - API doc fixes (completed)
- Migration scripts (v1.0-v1.12 refactoring tasks)

See `scripts/archive/README.md` for complete list and purposes.

---

## Common Workflows

### Complete Research Pipeline

**1. Ingest data:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets equities \
  --symbols SPY,QQQ
```

**2. Run backtest:**
```bash
python scripts/run_backtest.py --strategy spy_sma_cross
```

**3. Optimize parameters:**
```bash
python scripts/run_optimization.py \
  --strategy spy_sma_cross \
  --param strategy.fast_period:5:20:5 \
  --param strategy.slow_period:30:100:10
```

**4. Generate report:**
```bash
python scripts/generate_report.py \
  --strategy spy_sma_cross \
  --type optimization \
  --update-catalog \
  --status validated
```

### Multi-Timeframe Analysis

**Ingest both daily and hourly:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets crypto \
  --symbols BTC-USD \
  --timeframe 1h \
  --ingest-daily \
  --ingest-intraday
```

**Backtest on hourly data:**
```bash
python scripts/run_backtest.py \
  --strategy crypto_scalper \
  --bundle btcusd_1h \
  --data-frequency minute
```

### Bundle Maintenance

**Validate all bundles:**
```bash
python scripts/validate_bundles.py
```

**Check specific bundle info:**
```bash
python scripts/bundle_info.py spy_daily --verbose
```

**Re-ingest with force:**
```bash
python scripts/ingest_data.py \
  --source yahoo \
  --assets equities \
  --symbols SPY \
  --force
```

---

## Error Handling

All scripts follow consistent error handling patterns:

### Common Error Messages

**Missing strategy:**
```
✗ Error: Strategy 'unknown_strategy' not found
  Searched in: strategies/equities/
  Create strategy: Copy strategies/_template/ to strategies/equities/unknown_strategy/
```

**Missing bundle:**
```
✗ Error: Bundle 'unknown_bundle' not found
  Ingest data first: python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY
```

**Parameter validation failure:**
```
✗ Parameter validation failed:
  - strategy.fast_period must be less than strategy.slow_period
  - backtest.capital_base must be positive
  Fix: Edit parameters.yaml in strategies/equities/my_strategy/
```

**Calendar validation failure:**
```
✗ Error: Calendar 'INVALID' not registered
  Valid calendars: NYSE, NASDAQ, CRYPTO, FOREX
  Fix: Use --calendar NYSE or register custom calendar
```

### Exit Codes

- `0` - Success
- `1` - Error (with message on stderr)

### Logging

All scripts use `lib/logging/` system:
- Console output: User-facing messages via `click.echo`
- Log files: Detailed logs in `logs/` directory
- Structured logging: LogContext for phase/strategy/asset tracking

---

## Script Development Guidelines

When creating new scripts:

1. **Use click for CLI** - Consistent option parsing
2. **Import from lib/** - Use modular library functions
3. **Logging via lib.logging** - Never use basic `logging` module
4. **Clear help text** - Document all options and usage examples
5. **Helpful errors** - Suggest fixes in error messages
6. **Exit codes** - 0 for success, 1 for errors
7. **Path resolution** - Use `lib.paths.get_project_root()`

**Template structure:**
```python
#!/usr/bin/env python3
"""
Script description.

Usage examples:
    python scripts/my_script.py --option value
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from lib.module import function
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging
configure_logging(level="INFO", console=False, file=False)
logger = get_logger(__name__)

@click.command()
@click.option("--option", required=True, help="Option description")
def main(option):
    """Script purpose."""
    with LogContext(phase="script_name", option=option):
        logger.info(f"Starting script with option: {option}")
        try:
            # Script logic
            result = function(option)
            logger.info("Script complete")
            click.echo(f"✓ Success: {result}")
        except Exception as e:
            logger.error(f"Script failed: {e}", exc_info=True)
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Related Documentation

- [API Reference](api/README.md) - Complete module documentation
- [Code Patterns](code_patterns/README.md) - Reusable recipes
- [Troubleshooting](troubleshooting/README.md) - Problem-solution guides
- [CLAUDE.md](../CLAUDE.md) - Implementation guide for AI agents
- [workflow.md](../workflow.md) - Research workflow overview

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
