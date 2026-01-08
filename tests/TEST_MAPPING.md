# Test File Mapping to Domain Directories

This document maps all existing test files to their target domain directories based on the lib/ package structure.

## Mapping Overview

### Bundles Domain (`tests/bundles/`)

**Target files:**
- `test_api.py` - Bundle API tests
- `test_registry.py` - Bundle registry tests
- `test_csv_bundle.py` - CSV bundle tests
- `test_yahoo_bundle.py` - Yahoo bundle tests
- `test_timeframes.py` - Timeframe configuration tests

**Source files:**
- `tests/v1_0_8/test_bundles_api.py` → `tests/bundles/test_api.py`
  - Tests bundle management API, registry operations, timeframe validation, cache operations
- `tests/v1_0_8/test_phase2_strategy_creation.py` (partial) → `tests/bundles/test_api.py`
  - Bundle-related tests from strategy creation phase

**Notes:**
- Bundle ingestion, loading, and registry operations
- Timeframe validation and configuration
- CSV and Yahoo bundle implementations

---

### Validation Domain (`tests/validation/`)

**Target files:**
- `test_data_validator.py` - Data validation tests
- `test_bundle_validator.py` - Bundle validation tests
- `test_backtest_validator.py` - Backtest validation tests
- `test_schema_validator.py` - Schema validation tests
- `test_composite_validator.py` - Composite validator tests
- `test_validation_result.py` - ValidationResult class tests

**Source files:**
- `tests/test_data_validation_integration.py` → `tests/validation/test_data_validator.py`
  - Integration tests for DataValidator API migration
  - Data ingestion validation, error logging, symbol skipping
- `tests/test_validation_result_properties.py` → `tests/validation/test_validation_result.py`
  - Unit tests for ValidationResult property mappings (passed, error_checks, warning_checks)
- `tests/test_error_message_verification.py` → `tests/validation/test_data_validator.py`
  - Error message verification for validation failures
- `tests/test_auto_repair_removal.py` → `tests/validation/test_data_validator.py`
  - Tests for auto-repair removal functionality
- `tests/test_data_integrity.py` → `tests/validation/test_data_validator.py` (partial)
  - Data integrity verification tests (returns calculation, positions matching, metrics)
- `tests/v1_0_8/test_validation_api.py` → `tests/validation/test_data_validator.py` (partial)
  - Validation API tests for v1.0.8
- `tests/test_validate_csv_data.py` → `tests/validation/test_data_validator.py` (partial)
  - CSV validation script tests (uses DataValidator)

**Notes:**
- Primary focus on DataValidator and ValidationResult
- Integration with data ingestion pipeline
- Error handling and message verification

---

### Backtest Domain (`tests/backtest/`)

**Target files:**
- `test_runner.py` - Backtest runner tests
- `test_results.py` - Backtest results tests
- `test_strategy.py` - Strategy execution tests
- `test_verification.py` - Backtest verification tests

**Source files:**
- `tests/v1_0_8/test_phase3_backtest.py` → `tests/backtest/test_runner.py`
  - Backtest configuration, execution, and results generation
  - BacktestConfig and BacktestResults tests

**Notes:**
- Backtest execution workflow
- Configuration and results handling

---

### Metrics Domain (`tests/metrics/`)

**Target files:**
- `test_core.py` - Core metrics calculation tests
- `test_rolling.py` - Rolling metrics tests
- `test_trade.py` - Trade analysis tests
- `test_comparison.py` - Strategy comparison tests

**Source files:**
- `tests/v1_0_8/test_phase4_analysis.py` → `tests/metrics/test_core.py`
  - Metrics calculation (Sharpe ratio, max drawdown, Sortino ratio)
  - Performance analysis and trade analysis

**Notes:**
- Core metrics calculations
- Performance analysis functions

---

### Optimize Domain (`tests/optimize/`)

**Target files:**
- `test_grid.py` - Grid search optimization tests
- `test_random.py` - Random search optimization tests
- `test_overfit.py` - Overfitting detection tests
- `test_results.py` - Optimization results tests

**Source files:**
- `tests/v1_0_8/test_phase5_optimization.py` → `tests/optimize/test_grid.py` (or appropriate optimizer)
  - Optimization workflow tests
  - Parameter optimization and results

**Notes:**
- Optimization algorithms and results
- Parameter search strategies

---

### Validate Domain (`tests/validate/`)

**Target files:**
- `test_walkforward.py` - Walk-forward validation tests
- `test_montecarlo.py` - Monte Carlo validation tests
- `test_metrics.py` - Validation metrics tests

**Source files:**
- `tests/v1_0_8/test_phase6_validation.py` → `tests/validate/test_walkforward.py` and `tests/validate/test_montecarlo.py`
  - Walk-forward validator tests
  - Monte Carlo validator tests

**Notes:**
- Walk-forward and Monte Carlo validation methods
- Out-of-sample validation

---

### Report Domain (`tests/report/`)

**Target files:**
- `test_strategy_report.py` - Strategy report generation tests
- `test_catalog.py` - Report catalog tests
- `test_formatters.py` - Report formatter tests

**Source files:**
- `tests/v1_0_8/test_phase7_reporting.py` → `tests/report/test_strategy_report.py`
  - Report generation workflow tests
  - Strategy report creation

**Notes:**
- Report generation and formatting
- Catalog management

---

### Calendars Domain (`tests/calendars/`)

**Target files:**
- `test_crypto.py` - Crypto calendar tests
- `test_forex.py` - Forex calendar tests
- `test_registry.py` - Calendar registry tests

**Source files:**
- `tests/v1_0_8/test_calendars_api.py` → `tests/calendars/test_registry.py` and `tests/calendars/test_crypto.py` / `tests/calendars/test_forex.py`
  - Calendar API tests
  - Crypto and forex calendar operations

**Notes:**
- Calendar registry and operations
- Crypto and forex calendar implementations

---

### Config Domain (`tests/config/`)

**Target files:**
- `test_core.py` - Core configuration tests
- `test_strategy.py` - Strategy configuration tests
- `test_assets.py` - Asset configuration tests

**Source files:**
- `tests/v1_0_8/test_phase1_hypothesis.py` → `tests/config/test_strategy.py`
  - Strategy template structure tests
  - Parameter definition and validation
- `tests/v1_0_8/test_phase2_strategy_creation.py` (partial) → `tests/config/test_strategy.py`
  - Strategy configuration tests

**Notes:**
- Strategy parameter loading and validation
- Configuration file handling

---

### Data Domain (`tests/data/`)

**Target files:**
- `test_validation.py` - Data validation tests
- `test_normalization.py` - Data normalization tests
- `test_aggregation.py` - Data aggregation tests
- `test_filters.py` - Data filter tests

**Source files:**
- `tests/test_data_ingestion_advanced.py` → `tests/data/test_validation.py` (partial)
  - Advanced data ingestion tests
  - May also belong in integration/ if it tests end-to-end workflows
- `tests/test_validate_csv_data.py` (partial) → `tests/data/test_validation.py`
  - CSV data validation (data-level validation)

**Notes:**
- Data processing and validation
- Normalization and aggregation operations

---

### Utils Domain (`tests/utils/`)

**Target files:**
- `test_utils.py` - Utility function tests

**Source files:**
- No dedicated utils test file found
  - Utils functions are tested indirectly through other tests
  - May need to extract utils tests from integration tests

**Notes:**
- Utility functions from lib/utils.py
- Path management, strategy creation helpers

---

### Integration Domain (`tests/integration/`)

**Target files:**
- `test_end_to_end.py` - Complete end-to-end workflow tests
- `test_multi_strategy.py` - Multi-strategy workflow tests
- `test_multi_timeframe.py` - Multi-timeframe workflow tests
- `test_workflow_phases.py` - 7-phase workflow tests
- `test_error_handling.py` - Error handling integration tests

**Source files:**
- `tests/test_end_to_end.py` → `tests/integration/test_end_to_end.py`
  - Complete end-to-end workflow (strategy creation → backtest → analysis → optimization → validation → reporting)
- `tests/test_multi_strategy.py` → `tests/integration/test_multi_strategy.py`
  - Multi-strategy workflow tests
- `tests/test_multi_timeframe.py` → `tests/integration/test_multi_timeframe.py`
  - Multi-timeframe workflow tests
- `tests/test_error_handling.py` → `tests/integration/test_error_handling.py`
  - Error handling across workflow
- `tests/test_edge_cases.py` → `tests/integration/test_error_handling.py` (or separate file)
  - Edge case handling in workflows
- `tests/v1_0_8/test_phase1_hypothesis.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase2_strategy_creation.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase3_backtest.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase4_analysis.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase5_optimization.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase6_validation.py` (partial) → `tests/integration/test_workflow_phases.py`
- `tests/v1_0_8/test_phase7_reporting.py` (partial) → `tests/integration/test_workflow_phases.py`
  - Note: Phase tests may be split between domain-specific tests and integration workflow tests

**Notes:**
- End-to-end workflows spanning multiple domains
- Multi-strategy and multi-timeframe scenarios
- Error handling across the system

---

### Compatibility Domain (`tests/compatibility/`)

**Target files:**
- `test_zipline_compatibility.py` - Zipline compatibility tests
- `test_edge_cases.py` - Edge case compatibility tests
- `test_import_paths.py` - Import path verification tests

**Source files:**
- `tests/test_zipline_reloaded_compatibility.py` → `tests/compatibility/test_zipline_compatibility.py`
  - Zipline Reloaded compatibility tests
  - Calendar timezone normalization
- `tests/v1_0_8/test_import_paths.py` → `tests/compatibility/test_import_paths.py`
  - Modern import path verification
  - Zipline extension tests
  - Circular import detection
- `tests/v1_0_8/test_no_deprecated_imports.py` → `tests/compatibility/test_import_paths.py` (or separate)
  - Deprecated import detection
  - Legacy code removal verification

**Notes:**
- Compatibility with Zipline/Zipline Reloaded
- Import path verification
- Deprecated code detection

---

## Summary Statistics

### Legacy Tests (tests/)
- Total: 13 test files
- Distribution:
  - Validation: 6 files
  - Integration: 5 files
  - Compatibility: 1 file
  - Data: 1 file (partial)

### v1.0.8 Tests (tests/v1_0_8/)
- Total: 14 test files
- Distribution:
  - Bundles: 1 file
  - Calendars: 1 file
  - Backtest: 1 file
  - Metrics: 1 file
  - Optimize: 1 file
  - Validate: 1 file
  - Report: 1 file
  - Config: 2 files (partial)
  - Validation: 1 file
  - Compatibility: 2 files
  - Integration: 3 files (phase tests, partial)

### Total Test Files: 27
### Target Domain Directories: 12

---

## Migration Notes

1. **Phase Tests Split**: The v1.0.8 phase tests (`test_phase*.py`) may need to be split:
   - Domain-specific functionality → domain directories
   - Workflow integration → `tests/integration/test_workflow_phases.py`

2. **Partial Mappings**: Some test files test multiple domains. These should be:
   - Split into multiple test files in appropriate domains, OR
   - Moved to `integration/` if they test cross-domain workflows

3. **Data vs Validation**: 
   - `lib/data/validation.py` → `tests/data/test_validation.py`
   - `lib/validation/` → `tests/validation/`
   - Distinguish between data-level validation and validation framework

4. **Utils Tests**: Currently no dedicated utils tests. Consider extracting utils-specific tests from integration tests.

5. **Fixtures**: Both `conftest.py` files will be merged into a single unified `tests/conftest.py` with organized fixtures by domain.

