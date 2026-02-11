# Validation API (Data)

OHLCV data validation, bundle integrity, and backtest results verification.

**Location:** `lib/validation/`

**Note:** This module is for **data validation** (OHLCV quality, bundle integrity, results verification). For **strategy validation** (walk-forward analysis, Monte Carlo simulation), see [Validate API](validate.md) (`lib/strategy_validation/`).

---

## Overview

The Validation API provides comprehensive data quality checks for OHLCV data, bundle integrity verification, and backtest result validation. It complements Zipline-Reloaded's runtime validation with business-rule checks, data quality analysis, and integrity verification.

**Key capabilities:**
- Pre-ingestion OHLCV validation (schema, OHLC consistency, outliers)
- Bundle integrity verification (existence, metadata, date coverage)
- Post-backtest result validation (metrics consistency, position alignment)
- Asset-specific validation rules (equity, forex, crypto)
- Actionable error messages with fix suggestions

---

## How lib/validation Complements Zipline Runtime Validation

`lib/validation/` is designed to **complement**, not replace, Zipline-Reloaded’s built-in validation. The framework validates format, structure, and data availability at ingestion and backtest runtime. Our layer adds quality checks, business rules, and integrity checks that Zipline does not perform.

### What Zipline Validates (Runtime)

**During ingestion** (`zipline ingest`):

- Writer format and OHLCV column layout
- Data types (e.g. numeric for price/volume)
- Calendar alignment and bar continuity within the calendar
- Asset metadata and date ranges
- Volume within storage limits (e.g. uint32)

**During backtest** (`zipline run`):

- Data availability for requested dates
- Calendar alignment of backtest dates with the bundle
- Symbol resolution and bar access (e.g. `data.history()`)
- Session continuity

Zipline does **not** check: data quality (outliers, price jumps, volume spikes), OHLC consistency (high ≥ low, etc.), staleness, or asset-specific rules (equity splits, forex pips, crypto 24/7).

### What lib/validation Adds

| Phase            | Our checks | Zipline’s checks        |
|-----------------|------------|-------------------------|
| **Pre-ingestion** | Schema, OHLC consistency, gaps, outliers, asset-specific rules | — |
| **Post-ingestion** | Bundle existence, metadata, date coverage, symbol availability | Format, calendar, writer |
| **Post-backtest** | Metrics consistency, position/transaction alignment, returns verification | Data availability, symbol resolution |

So:

- **Before data enters a bundle:** use `lib/validation` for quality and business rules; Zipline has no role yet.
- **During ingestion and backtest:** rely on Zipline for format, calendar, and availability; use `lib/validation` for everything else.
- **After a backtest:** use `lib/validation` to verify results and metrics; Zipline does not re-validate results.

**Summary:** Zipline ensures data is in the right format and available at runtime. `lib/validation` ensures data is correct, consistent, and that backtest outputs are coherent. Together they cover from raw data to backtest results.

For the full pipeline (all five layers and when to use each), see [Validation Architecture](../validation/validation_architecture.md).

---

## Installation/Dependencies

**Required:**
- `zipline-reloaded` >= 3.1.0
- `pandas` >= 1.3.0
- `numpy` >= 1.20.0

**Optional:**
- `exchange-calendars` >= 4.0.0 (for calendar validation)

```bash
pip install zipline-reloaded pandas numpy exchange-calendars
```

---

## Main API

### Pre-ingestion

| Function | Purpose |
|----------|---------|
| `validate_before_ingest()` | Validate OHLCV DataFrame before bundle ingestion |
| `validate_csv_files_pre_ingestion()` | Validate CSV files before ingestion |

### Bundle

| Function | Purpose |
|----------|---------|
| `validate_bundle()` | Check bundle existence and integrity |
| `verify_bundle_dates()` | Check bundle covers a date range |

### Post-backtest

| Function | Purpose |
|----------|---------|
| `validate_backtest_results()` | Validate perf/transactions/positions consistency |
| `verify_metrics_calculation()` | Verify metrics vs equity/returns |
| `verify_returns_calculation()` | Verify returns vs equity curve |
| `verify_positions_match_transactions()` | Check positions match transaction history |

### Report I/O

| Function | Purpose |
|----------|---------|
| `save_validation_report()` | Save validation result to file |
| `load_validation_report()` | Load validation result from file |

---

## Example: Pre-ingestion then Ingest

## Examples

### Basic Validation

```python
from lib.validation import validate_before_ingest

result = validate_before_ingest(
    df=raw_data,
    asset_name='AAPL',
    timeframe='1d',
    asset_type='equity',
)

if not result:
    print(result.summary())  # Fix issues before ingesting
    return

# Data passes our quality checks; Zipline will still validate format during ingest
# zipline ingest ...
```

## Example: Post-ingestion and Post-backtest

```python
from lib.validation import validate_bundle, verify_bundle_dates, validate_backtest_results

# After ingestion
result = validate_bundle('my_bundle')
if not result:
    print("Bundle issues:", result.summary())

ok = verify_bundle_dates('my_bundle', '2020-01-01', '2024-01-01')

# After backtest
result = validate_backtest_results(perf_df, transactions_df, positions_df)
if not result:
    print("Results issues:", result.summary())
```

---

## See Also

- [Validation Architecture](../validation/validation_architecture.md) — Full pipeline and when to use each layer
- [Troubleshooting: Data Validation](../troubleshooting/data_validation.md)
- [Code Patterns: Filters vs Validators](../code_patterns/filters_vs_validators.md)
- [Validate API](validate.md) — Strategy validation (walk-forward, Monte Carlo)

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
