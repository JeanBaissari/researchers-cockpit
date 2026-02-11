# Test Suite - v1.12.0

## Current Status

**As of v1.12.0:** Legacy tests for removed modules have been deleted.

**Removed (AD-005 - Task 011):**
- tests/bundles/test_api.py (289 lines)
- tests/bundles/test_ingestion_advanced.py (1,086 lines)
- tests/bundles/test_ingestion.py (389 lines)
- tests/bundles/test_registry.py (201 lines)
- tests/calendars/test_alignment_integration.py (155 lines)
- tests/calendars/test_session_manager.py (313 lines)
- tests/integration/test_multi_timeframe.py (868 lines)

**Total removed:** 3,301 lines across 7 test files

These tests validated modules deleted in Tasks 004-007:
- lib/bundles/csv/* (Task 004)
- lib/calendars/sessions/* (Task 005)
- lib/data/aggregation.py (Task 006)
- lib/bundles/registry.py and guard.py (Task 007)

## Remaining Tests

Tests for core modules that were NOT deleted (~34 test files):
- tests/backtest/* - Backtest execution tests
- tests/bundles/test_timeframes.py - Timeframe configuration tests
- tests/calendars/test_crypto.py - Crypto calendar tests
- tests/config/* - Parameter loading tests
- tests/data/* - Data processing tests
- tests/integration/* - Integration workflow tests
- tests/metrics/* - Performance metrics tests
- tests/optimize/* - Optimization tests
- tests/report/* - Report generation tests
- tests/strategies/* - Strategy management tests
- tests/utils/* - Utility function tests
- tests/validate/* - Walk-forward validation tests
- tests/validation/* - Data validation tests

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/config/ -v
pytest tests/metrics/ -v

# Run with coverage
pytest tests/ --cov=lib --cov-report=html
```

## Future Test Development

Per AD-005, comprehensive test suite will be rebuilt as separate effort post-v1.12.0.

New tests will:
- Validate direct Zipline usage patterns (NO wrappers)
- Use test factory approach for comprehensive coverage
- Focus on integration testing
- Test direct pandas.resample() usage (not aggregate_ohlcv)
- Test direct get_calendar() usage (not SessionManager)
- Validate bundle registration in extension.py

## Why Tests Were Deleted

**Decision (AD-005):** Delete legacy tests now, rebuild comprehensive test suite later.

**Rationale:**
- Tests validated code that no longer exists (wasted maintenance)
- Updating tests for deleted code is wasted effort
- Better to delete now and rebuild proper tests later
- Focus refactoring effort on implementation, not test updates
- Clean slate enables better test architecture

**Test Debt:** Acknowledged and tracked in v1.12.0 roadmap

## Architecture Notes

v1.12.0 uses NO WRAPPERS architecture:
- Direct Zipline APIs (data.history(), symbol(), schedule_function())
- Direct pandas operations (df.resample().agg())
- Direct calendar access (get_calendar('FOREX'))
- Bundle registration in .zipline/extension.py

Tests should validate this direct usage, not wrapper functions.

See: tasks/v1.11.1/001_DATA_BUNDLE/PDR.md (AD-005)
