# Optimization Plan for The Researcher's Cockpit

## Executive Summary

Testing of the v1.0.3 release revealed several issues that need addressing. This document outlines the findings and proposed optimizations organized by priority.

**Status Update (v1.0.4 - 2025-12-28):** All critical and high priority issues have been resolved.

---

## Issues Found During Testing

### Critical Issues (Blocking)

#### 1. Asset Metadata Missing `country_code`
**File:** `lib/data_loader.py`
**Impact:** Pipeline API fails with "Failed to find any assets with country_code 'US'"
**Status:** ✅ RESOLVED in v1.0.3

The asset metadata DataFrame passed to `asset_db_writer.write()` now includes the `country_code` column.

#### 2. Metrics Calculation Bug - Sharpe Ratio
**File:** `lib/metrics.py`
**Impact:** Sharpe ratio shows astronomically large negative values (-86.84, -561284620977090)
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Added try/except around `ep.sharpe_ratio()` and `ep.sortino_ratio()` calls
- Added NaN/Inf validation after calculation (`np.isfinite()` check)
- Added bounds check (-10 to +10 for Sharpe/Sortino, -20 to +20 for Calmar)
- Invalid values are now capped to reasonable bounds instead of propagating

#### 3. Template Strategy Attaches Pipeline Unconditionally
**File:** `strategies/_template/strategy.py`
**Impact:** Pipeline attachment fails when `use_pipeline: false` because asset metadata lacks `country_code`
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Template already had conditional check at lines 125-131
- Enhanced `parameters.yaml` with explicit documentation about Pipeline requirements
- Added `use_pipeline: false` explicitly to crypto/forex strategy parameters
- Added comments explaining Pipeline is for US equities only

---

### High Priority Issues

#### 4. Bundle Re-registration Not Working Correctly
**File:** `lib/data_loader.py`
**Impact:** Bundles can't be loaded in new Python sessions without re-ingestion
**Status:** ✅ RESOLVED in v1.0.3

Bundle registry persistence implemented using JSON file at `~/.zipline/bundle_registry.json`.

#### 5. FOREX Data Gaps with Yahoo Finance
**Impact:** FOREX bundle ingestion fails due to missing data on weekends/holidays
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Created `fill_data_gaps()` function in `lib/utils.py`
- Modified `lib/data_loader.py` to apply gap-filling for FOREX data during ingestion
- Forward-fill preserves last known price (standard forex practice)
- Volume set to 0 for synthetic bars (signals no real trades)
- Added `gap_fill` configuration to `config/data_sources.yaml`

#### 6. Crypto Strategy - No Trades with Long SMA Periods
**Impact:** Crypto backtest runs but shows 0% return
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Added pre-flight warmup validation in `lib/backtest.py`
- Added `get_warmup_days()` function in `lib/config.py` for dynamic warmup calculation
- Added `warmup_days` and `validate_warmup` parameters to strategy templates
- Added `_calculate_required_warmup()` function in strategy template `initialize()`
- Added `--skip-warmup-check` flag to `scripts/run_backtest.py`
- Updated `.agent/backtest_runner.md` with warmup validation documentation
- Updated crypto/forex strategy parameters with appropriate warmup_days values

**Behavior:**
- Backtests now fail fast with clear error if data period is too short for warmup
- Dynamic calculation extracts max of all `*_period` parameters
- Warning issued if configured warmup_days is less than calculated requirement
- Can be disabled via `validate_warmup: false` or `--skip-warmup-check` flag

---

### Medium Priority Issues

#### 7. FutureWarning in Asset Writer
**Warning:** `DataFrameGroupBy.apply operated on the grouping columns`
**File:** Zipline library (external)
**Status:** ⏳ DEFERRED (external dependency)

This is a Pandas 2.x deprecation warning in Zipline's codebase. Wait for upstream fix.

#### 8. Volume Overflow Warning for Crypto/Large Volume Assets
**Warning:** `Ignoring N values because they are out of bounds for uint32`
**Status:** ✅ RESOLVED in v1.0.4

**Root Cause:**
- Zipline's BcolzDailyBarWriter uses uint32 for volume storage (~4.29B max)
- Crypto markets (especially BTC) regularly trade >10B units daily
- The warning silently dropped data points, causing inaccurate volume-based indicators

**Fix Applied:**
- Modified `lib/data_loader.py` to use `float64` for volume at ingestion layer
- Added validation to log when volume exceeds uint32 limits
- Added NaN/Inf handling for converted volume data
- Added `volume_dtype: float64` configuration to `config/data_sources.yaml`

**Benefits:**
- Handles values up to ~1.8×10^308 (effectively unlimited for any market)
- Preserves sufficient precision (float64 has 15-17 significant digits)
- No downstream changes required to strategies or analysis code
- Zero `out of bounds for uint32` warnings during crypto ingestion

#### 9. Strategy Template Path Issues
**File:** `strategies/_template/strategy.py`
**Impact:** `_project_root` calculation may break in nested directory structures
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Created `lib/paths.py` with marker-based project root discovery
- Updated `lib/utils.py` to delegate to new paths module
- Updated strategy template with robust `_find_project_root()` function
- Searches for project markers: `pyproject.toml`, `.git`, `config/settings.yaml`, `CLAUDE.md`
- Supports environment variable override via `PROJECT_ROOT`

---

### Low Priority / Nice-to-Have

#### 10. Centralized Logging Not Implemented
**Impact:** Debug messages scattered, inconsistent formatting
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Created comprehensive `lib/logging_config.py` with:
  - `StructuredFormatter` for JSON log output
  - `ConsoleFormatter` for human-readable output
  - `LogContext` context manager for phase/strategy/run_id tracking
  - Thread-local storage for logging context
  - Rotating file handler with daily logs
- Module-level loggers for common namespaces (data, strategy, backtest, metrics, validation, report)
- Auto-configuration on lib package import
- Configuration in `config/settings.yaml`

#### 11. Data Integrity Checks Optional
**File:** `lib/backtest.py`
**Impact:** `verify_integrity=False` by default, so data quality issues may go unnoticed
**Status:** ✅ RESOLVED in v1.0.4

**Fix Applied:**
- Created comprehensive `lib/data_validation.py` with:
  - `DataValidator` class with configurable checks
  - Validation for OHLCV consistency, nulls, negatives, outliers, gaps, duplicates
  - `ValidationResult` dataclass for structured results
  - Functions: `validate_bundle()`, `verify_metrics_calculation()`, etc.
- Added `data_validation` configuration section to `config/settings.yaml`
- Asset class-specific gap tolerance settings

#### 12. Missing Hypothesis Templates
**Impact:** Some strategies missing hypothesis.md files
**Status:** 📋 DOCUMENTED (user action required)

Users should create hypothesis.md files for their strategies following the template.

---

## Implementation Summary (v1.0.4)

### Files Modified:
- `lib/metrics.py` - Added robust error handling and bounds checking
- `lib/utils.py` - Added `fill_data_gaps()` function, delegated to paths module
- `lib/data_loader.py` - Added FOREX gap-filling, float64 volume for crypto
- `lib/config.py` - Added `get_warmup_days()` function for dynamic warmup calculation
- `lib/backtest.py` - Added `_validate_warmup_period()` pre-flight validation
- `lib/__init__.py` - Updated version, added new module exports
- `strategies/_template/strategy.py` - Robust project root discovery, warmup calculation in initialize()
- `strategies/_template/parameters.yaml` - Enhanced Pipeline documentation, added warmup_days
- `strategies/crypto/simple_crypto_strategy/parameters.yaml` - Added `use_pipeline: false`, warmup_days: 200
- `strategies/forex/simple_forex_strategy/parameters.yaml` - Added `use_pipeline: false`, warmup_days: 30
- `scripts/run_backtest.py` - Added `--skip-warmup-check` flag, warmup info display
- `.agent/backtest_runner.md` - Added warmup validation documentation
- `config/settings.yaml` - Added data_validation configuration
- `config/data_sources.yaml` - Added gap_fill and volume_dtype configuration

### Files Created:
- `lib/paths.py` - Centralized path resolution with marker-based discovery
- `lib/logging_config.py` - Comprehensive centralized logging
- `lib/data_validation.py` - Multi-layer data validation

---

## Testing Recommendations

After implementing fixes:

1. **Unit Tests:** Add tests for metrics calculation edge cases
2. **Integration Tests:** Test full workflow: create strategy -> ingest data -> run backtest -> save results
3. **Cross-Asset Tests:** Verify EQUITIES, CRYPTO, and FOREX all work end-to-end
4. **Regression Tests:** Ensure spy_sma_cross still produces valid results

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.3 | 2025-12-27 | Initial release with Zipline-Reloaded 3.1.0 realignment |
| v1.0.4 | 2025-12-28 | Bug fixes for metrics, paths, logging, validation, FOREX gaps, crypto volume overflow |

---

## Notes

- All changes maintain backward compatibility with existing strategies
- No changes to the intended workflow (as documented in workflow.md)
- Focus on stability and reliability over new features
