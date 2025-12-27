# Testing Guide

## Overview

The test suite validates the entire pipeline from strategy creation to results analysis.

## Running Tests

### Run All Tests

```bash
cd /home/jeanbaissari/Documents/Programming/python-projects/algorithmic_trading/v1_researchers_cockpit
source venv/bin/activate
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_end_to_end.py
pytest tests/test_error_handling.py
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

### Verbose Output

```bash
pytest -v tests/
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_end_to_end.py       # Test 1: Full workflow
├── test_error_handling.py   # Test 2: Error scenarios
├── test_data_integrity.py   # Test 3: Data validation
├── test_multi_strategy.py   # Test 4: Multi-strategy workflow
└── test_edge_cases.py       # Test 5: Boundary conditions
```

## Test Coverage

### Test 1: End-to-End Workflow
- Strategy creation from template
- Parameter configuration
- Data ingestion
- Backtest execution
- Results saving
- Output verification

### Test 2: Error Handling
- Missing strategy errors
- Missing bundle errors
- Invalid parameter validation
- Insufficient data handling
- Broken symlink auto-fix

### Test 3: Data Integrity
- Bundle date range verification
- Returns calculation verification
- Positions/transactions consistency
- Metrics calculation verification

### Test 4: Multi-Strategy Workflow
- Creating multiple strategies
- Running parallel backtests
- Comparing results
- Verifying no conflicts

### Test 5: Edge Cases
- Very short backtests (1 month)
- Very long backtests (10 years)
- Single trade strategies
- No trades strategies
- Extreme parameters
- Missing data periods

## Test Markers

- `@pytest.mark.integration` - Integration tests (require data/bundles)
- `@pytest.mark.slow` - Slow tests (can be skipped with `-m "not slow"`)
- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)

## Prerequisites

- Virtual environment activated
- Required dependencies installed (`pip install -r requirements.txt`)
- At least one data bundle ingested (for integration tests)

## Skipping Tests

Tests that require data bundles will skip gracefully if bundles are not available:

```python
if len(bundles) == 0:
    pytest.skip("No bundles available for testing")
```

## Interpreting Results

### All Tests Pass
- Pipeline is working correctly
- All features are functional

### Some Tests Skip
- Missing data bundles (expected in fresh environments)
- Run `python scripts/ingest_data.py` to create bundles

### Tests Fail
- Check error messages for specific issues
- Verify data bundles exist
- Check strategy files are valid

## Continuous Integration

For CI/CD, run:

```bash
# Fast tests only (skip slow/integration)
pytest -m "not slow and not integration"

# Or run all but allow skips
pytest --tb=short tests/
```

## Date Created

2025-12-23 

