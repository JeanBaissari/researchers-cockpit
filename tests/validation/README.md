# Validation Tests

Comprehensive test suite for the validation framework.

---

## Overview

This directory contains tests for `lib/validation/` - the data validation package that complements Zipline-Reloaded's runtime validation.

**Test Coverage:**
- ✅ 72 tests passing
- ✅ Unit tests for all validators
- ✅ Integration tests for workflows
- ✅ Edge cases and error handling

---

## Test Organization

```
tests/validation/
├── test_backtest_validator.py      # BacktestValidator tests (3 tests)
├── test_bundle_validator.py        # BundleValidator tests (2 tests)
├── test_composite_validator.py     # CompositeValidator tests (2 tests)
├── test_data_validator.py          # DataValidator tests (11 tests)
├── test_schema_validator.py        # SchemaValidator tests (2 tests)
├── test_validation_complements_zipline.py  # Zipline complement tests (12 tests)
├── test_validation_result.py       # ValidationResult tests (28 tests)
└── test_validation_integration.py  # Integration workflow tests (12 tests)
```

---

## Running Tests

### All Validation Tests

```bash
# Run all validation tests
python -m pytest tests/validation/ -v

# Run with coverage
python -m pytest tests/validation/ --cov=lib.validation --cov-report=html

# Run specific test file
python -m pytest tests/validation/test_data_validator.py -v
```

### Specific Test Classes

```bash
# Run specific test class
python -m pytest tests/validation/test_data_validator.py::TestDataValidatorBasic -v

# Run specific test
python -m pytest tests/validation/test_data_validator.py::TestDataValidatorBasic::test_data_validator_creation -v
```

### Quick Smoke Tests

```bash
# Run quick smoke tests (< 2s)
python -m pytest tests/validation/ -k "test_.*_creation" -v
```

---

## Test Categories

### Unit Tests

**Purpose:** Test individual validators in isolation

**Files:**
- `test_backtest_validator.py` - Backtest results validation
- `test_bundle_validator.py` - Bundle integrity validation
- `test_data_validator.py` - OHLCV data validation
- `test_schema_validator.py` - Schema validation
- `test_composite_validator.py` - Multi-validator composition

**Coverage:**
- Validator creation
- Basic validation operations
- Error detection
- Configuration options

### Integration Tests

**Purpose:** Test complete validation workflows

**File:** `test_validation_integration.py`

**Coverage:**
- Pre-ingestion workflow (data validation → ingestion)
- Post-backtest workflow (results → verification)
- End-to-end validation pipeline
- Asset-specific validation (equity, crypto, forex)
- Configuration options (strict, lenient, custom)

### Architectural Tests

**Purpose:** Ensure validation complements (not duplicates) Zipline

**File:** `test_validation_complements_zipline.py`

**Coverage:**
- Pre-ingestion focuses on quality (not format)
- Post-ingestion focuses on integrity (not availability)
- Post-backtest focuses on results (not runtime)
- No duplication of Zipline's validation

### Result Tests

**Purpose:** Test ValidationResult data structure

**File:** `test_validation_result.py`

**Coverage:**
- Passed property behavior
- Error checks filtering
- Warning checks filtering
- Result merging
- Property consistency

---

## Test Data

### Sample OHLCV Data

Tests use synthetic OHLCV data:

```python
dates = pd.date_range('2024-01-01', '2024-01-10', freq='1d', tz='UTC')
df = pd.DataFrame({
    'open': [100.0, 101.0, 102.0, ...],
    'high': [101.0, 102.0, 103.0, ...],
    'low': [99.0, 100.0, 101.0, ...],
    'close': [100.5, 101.5, 102.5, ...],
    'volume': [1000000] * 10,
}, index=dates)
```

**Characteristics:**
- Timezone-aware (UTC)
- OHLC consistent
- Realistic prices
- No missing data
- No outliers

### Invalid Data Scenarios

Tests include intentional data issues:

- Missing required columns
- OHLC inconsistencies (high < low)
- Negative prices
- NaN values
- Invalid data types
- Timezone issues

---

## Key Test Patterns

### Validator Creation

```python
def test_validator_creation(self):
    """Test creating validator."""
    config = ValidationConfig.strict(timeframe='1d')
    validator = DataValidator(config=config)
    assert validator is not None
```

### Valid Data Validation

```python
def test_validate_valid_data(self):
    """Test validating valid data."""
    df = create_valid_ohlcv_data()
    result = validate_before_ingest(df, 'TEST', '1d', 'equity')
    assert result.passed
    assert len(result.checks) > 0
```

### Error Detection

```python
def test_detect_ohlc_inconsistency(self):
    """Test detecting OHLC inconsistency."""
    df = create_invalid_ohlcv_data()  # high < low
    result = validate_before_ingest(df, 'TEST', '1d', 'equity')
    assert not result.passed
    assert len(result.error_checks) > 0
```

### Configuration Testing

```python
def test_strict_vs_lenient(self):
    """Test strict vs lenient configurations."""
    strict_result = validate_before_ingest(df, config=ValidationConfig.strict(...))
    lenient_result = validate_before_ingest(df, config=ValidationConfig.lenient(...))
    # Assert different behavior
```

---

## Common Test Fixtures

### Conftest Fixtures

Located in `tests/conftest.py`:

```python
@pytest.fixture
def sample_ohlcv_df():
    """Valid OHLCV DataFrame."""
    # Returns valid sample data

@pytest.fixture
def sample_config():
    """Default ValidationConfig."""
    return ValidationConfig.default(timeframe='1d')
```

### Local Fixtures

Defined in individual test files:

```python
@pytest.fixture
def invalid_ohlcv_df():
    """Invalid OHLCV data for error testing."""
    # Returns data with intentional issues
```

---

## Assertions and Validation

### Standard Assertions

```python
# Validation passed
assert result.passed

# Validation failed
assert not result.passed

# Error count
assert len(result.error_checks) == expected_count

# Warning count
assert len(result.warning_checks) > 0

# Specific error message
assert any("OHLC" in check.message for check in result.error_checks)
```

### Custom Assertions

```python
def assert_validation_passed(result, min_checks=0):
    """Assert validation passed with minimum checks."""
    assert result.passed, f"Validation failed: {result.summary()}"
    assert len(result.checks) >= min_checks

def assert_has_error(result, error_substring):
    """Assert result contains specific error."""
    messages = [c.message for c in result.error_checks]
    assert any(error_substring in msg for msg in messages)
```

---

## Test Statistics

**Current Status (as of v1.12.0):**

```
Total Tests: 72
├─ Passing: 72 (100%)
├─ Failing: 0 (0%)
└─ Skipped: 1 (bundle validation requires real bundle)

Execution Time: ~8 seconds
Coverage: >85% of lib/validation/
```

**Test Distribution:**

```
Unit Tests:        48 (67%)
Integration Tests: 12 (17%)
Architectural:     12 (17%)
```

---

## Adding New Tests

### 1. Unit Test Template

```python
class TestNewValidator:
    """Test NewValidator."""

    def test_creation(self):
        """Test creating NewValidator."""
        validator = NewValidator(config=ValidationConfig.default())
        assert validator is not None

    def test_validate_valid(self):
        """Test validating valid data."""
        validator = NewValidator()
        result = validator.validate(valid_data)
        assert result.passed

    def test_validate_invalid(self):
        """Test validating invalid data."""
        validator = NewValidator()
        result = validator.validate(invalid_data)
        assert not result.passed
        assert len(result.error_checks) > 0
```

### 2. Integration Test Template

```python
class TestNewWorkflow:
    """Test new validation workflow."""

    def test_complete_workflow(self):
        """Test complete workflow from start to finish."""
        # Step 1: Pre-validation
        pre_result = validate_before_operation(data)
        assert pre_result.passed

        # Step 2: Operation (simulated)
        processed_data = simulate_operation(data)

        # Step 3: Post-validation
        post_result = validate_after_operation(processed_data)
        assert post_result.passed
```

### 3. Run New Tests

```bash
# Run new test file
python -m pytest tests/validation/test_new_validator.py -v

# Run with coverage
python -m pytest tests/validation/test_new_validator.py --cov=lib.validation.new_validator

# Add to CI
git add tests/validation/test_new_validator.py
git commit -m "test: add NewValidator tests"
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'lib'`

**Solution:**
```bash
# Ensure project root in PYTHONPATH
export PYTHONPATH=/path/to/v1_researchers_cockpit:$PYTHONPATH

# Or run from project root
cd /path/to/v1_researchers_cockpit
python -m pytest tests/validation/ -v
```

### Fixture Not Found

**Problem:** `fixture 'sample_data' not found`

**Solution:**
1. Check fixture is defined in `conftest.py` or test file
2. Ensure fixture name matches exactly
3. Check fixture scope (function, class, module, session)

### Timezone Warnings

**Problem:** `UserWarning: Pandas doesn't support index without timezone`

**Solution:**
```python
# Always use timezone-aware data in tests
dates = pd.date_range('2024-01-01', periods=10, freq='1d', tz='UTC')
```

### Deprecation Warnings

**Problem:** `DeprecationWarning: datetime.utcnow() is deprecated`

**Solution:**
- These are known warnings from dependencies
- Filter with: `pytest -W ignore::DeprecationWarning`
- Will be fixed in future dependency updates

---

## See Also

- [Validation API](../../docs/api/validation.md) - Validation API documentation
- [Validation Suite](../../docs/validation/validation_suite.md) - End-to-end validation tool
- [Code Patterns](../../docs/code_patterns/) - Testing patterns and best practices
- [pytest documentation](https://docs.pytest.org/) - pytest framework

---

**Last Updated:** 2026-02-09
**Test Suite Version:** v1.12.0
**Status:** ✅ All Tests Passing
