# Write Unit Tests

## Overview

Create comprehensive pytest unit tests for Python/Zipline code following project conventions, using fixtures from tests/conftest.py and mocking Zipline/data dependencies.

## Steps

1. **Test Coverage**
   - Test all public functions in lib/ modules
   - Cover edge cases: missing data, invalid parameters, calendar errors
   - Test both positive and negative scenarios
   - Mock Zipline API calls and data bundle operations

2. **Test Structure**
   - Use pytest conventions (test_*.py files)
   - Write clear, descriptive test names (test_function_name_scenario)
   - Follow Arrange-Act-Assert pattern
   - Group related tests in classes (TestClassName)

3. **Test Cases to Include**
   - Happy path scenarios
   - Edge cases: empty data, missing files, invalid dates
   - Error handling: exception raising, validation failures
   - Mock external dependencies (Zipline, data sources)

4. **Test Quality**
   - Use fixtures from tests/conftest.py (temp_dir, valid_ohlcv_data, etc.)
   - Make tests independent and isolated
   - Ensure tests are deterministic (no random data without seeds)
   - Keep tests simple and focused on one thing

## Checklist

- [ ] Tested all public functions/methods
- [ ] Covered edge cases and error conditions
- [ ] Tested both positive and negative scenarios
- [ ] Used pytest conventions and fixtures
- [ ] Written clear, descriptive test names
- [ ] Followed Arrange-Act-Assert pattern
- [ ] Included happy path scenarios
- [ ] Included edge cases and boundary conditions
- [ ] Mocked Zipline/data dependencies appropriately
- [ ] Made tests independent and isolated
- [ ] Ensured tests are deterministic

## Test Patterns

**Basic function test:**
```python
import pytest
from lib.config.core import load_settings

def test_load_settings_returns_dict():
    """Test that load_settings returns a dictionary."""
    # Arrange
    # (No setup needed, uses real config)
    
    # Act
    settings = load_settings()
    
    # Assert
    assert isinstance(settings, dict)
    assert 'capital' in settings
```

**Test with fixtures:**
```python
import pytest
from lib.bundles.csv_bundle import ingest_csv_bundle

def test_ingest_csv_bundle_creates_bundle(temp_data_dir, valid_ohlcv_data):
    """Test CSV bundle ingestion creates bundle directory."""
    # Arrange
    csv_path = temp_data_dir / 'processed' / '1d' / 'AAPL.csv'
    valid_ohlcv_data.to_csv(csv_path)
    
    # Act
    bundle_name = ingest_csv_bundle('test_bundle', csv_path)
    
    # Assert
    bundle_path = temp_data_dir / 'bundles' / bundle_name
    assert bundle_path.exists()
```

**Test error handling:**
```python
import pytest
from lib.config.strategy import load_strategy_params

def test_load_strategy_params_raises_on_missing_file():
    """Test that missing parameters.yaml raises FileNotFoundError."""
    # Arrange
    strategy_name = 'nonexistent_strategy'
    
    # Act & Assert
    with pytest.raises(FileNotFoundError) as exc_info:
        load_strategy_params(strategy_name)
    
    assert 'parameters.yaml' in str(exc_info.value)
```

**Test with mocking:**
```python
from unittest.mock import patch, MagicMock
import pytest
from lib.backtest import run_backtest

@patch('lib.backtest.runner.run_algorithm')
def test_run_backtest_calls_zipline(mock_run_algorithm, temp_strategy_dir):
    """Test that run_backtest calls Zipline's run_algorithm."""
    # Arrange
    mock_run_algorithm.return_value = (pd.DataFrame(), MagicMock())
    
    # Act
    run_backtest('test_strategy', '2020-01-01', '2020-12-31')
    
    # Assert
    mock_run_algorithm.assert_called_once()
```

**Test class grouping:**
```python
import pytest
from lib.metrics.core import calculate_sharpe_ratio

class TestCalculateSharpeRatio:
    """Test suite for calculate_sharpe_ratio function."""
    
    def test_returns_float(self):
        """Test that function returns float."""
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        result = calculate_sharpe_ratio(returns)
        assert isinstance(result, float)
    
    def test_handles_zero_volatility(self):
        """Test that zero volatility returns zero."""
        returns = pd.Series([0.01] * 10)  # No volatility
        result = calculate_sharpe_ratio(returns)
        assert result == 0.0
```

## Notes

- Use fixtures from tests/conftest.py (temp_dir, valid_ohlcv_data, etc.)
- Mock Zipline API calls to avoid requiring full Zipline setup
- Use pytest.raises() for exception testing
- Mark slow tests with @pytest.mark.slow (requires --run-slow)
- Keep tests in tests/ directory mirroring lib/ structure
- Use descriptive test names: test_function_name_scenario

## Related Commands

- code-review.md - For reviewing test coverage
- debug-issue.md - For debugging test failures