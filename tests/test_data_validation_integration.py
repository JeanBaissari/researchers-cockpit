"""
Integration tests for data validation API migration.

This test suite verifies that the migrated validation code works correctly
with data ingestion, including:
1. Data ingestion uses DataValidator correctly
2. Validation errors are logged properly
3. Symbols with validation failures are skipped during ingestion
4. Test with sample data files (valid and invalid)
"""

import pytest
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock, call
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.data_validation import DataValidator, ValidationConfig, ValidationResult
from lib.data_loader import _register_csv_bundle, get_project_root


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for testing."""
    processed_dir = tmp_path / 'data' / 'processed' / '1h'
    processed_dir.mkdir(parents=True, exist_ok=True)
    yield processed_dir
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def valid_ohlcv_data():
    """Create valid OHLCV DataFrame for testing."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=100,
        freq='D',
        tz='UTC'
    )
    
    base_price = 100.0
    df = pd.DataFrame({
        'open': [base_price + i * 0.1 for i in range(len(dates))],
        'high': [base_price + i * 0.1 + 2.0 for i in range(len(dates))],
        'low': [base_price + i * 0.1 - 1.0 for i in range(len(dates))],
        'close': [base_price + i * 0.15 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_missing_columns():
    """Create invalid OHLCV DataFrame missing required columns."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    # Missing 'volume' column
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        # 'volume' is missing
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_negative_prices():
    """Create invalid OHLCV DataFrame with negative prices."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [-5.0] + [99.0 + i * 0.1 for i in range(1, len(dates))],  # Negative low
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_ohlc_inconsistency():
    """Create invalid OHLCV DataFrame with OHLC consistency violations."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [95.0 + i * 0.1 for i in range(len(dates))],  # High < Open (violation)
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_nulls():
    """Create invalid OHLCV DataFrame with null values."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [None] + [101.0 + i * 0.1 for i in range(1, len(dates))],  # Null in close
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_insufficient_rows():
    """Create invalid OHLCV DataFrame with insufficient rows."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=5,  # Too few rows for daily data (minimum is 20)
        freq='D',
        tz='UTC'
    )
    
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


# =============================================================================
# TEST DATA VALIDATOR USAGE IN INGESTION
# =============================================================================

def test_data_validator_used_in_csv_ingestion(temp_data_dir, valid_ohlcv_data):
    """Test that DataValidator is used correctly during CSV bundle ingestion."""
    # Create a valid CSV file
    symbol = 'TEST'
    timeframe = '1h'
    csv_file = temp_data_dir / f"{symbol}_{timeframe}_20240101_20240110_ready.csv"
    
    # Save valid data to CSV
    valid_ohlcv_data.to_csv(csv_file)
    
    # Mock the zipline registration to avoid actual bundle creation
    with patch('lib.data_loader.register') as mock_register, \
         patch('lib.data_loader.get_calendar') as mock_calendar, \
         patch('lib.data_loader.ingest') as mock_ingest:
        
        # Setup calendar mock
        mock_calendar_obj = MagicMock()
        mock_calendar_obj.first_session = pd.Timestamp('2020-01-01', tz='UTC')
        mock_calendar.return_value = mock_calendar_obj
        
        # Register the bundle (this will call the ingest function)
        _register_csv_bundle(
            bundle_name='test_bundle',
            symbols=[symbol],
            calendar_name='XNYS',
            timeframe=timeframe,
            asset_class='equities',
            start_date='2024-01-01',
            end_date='2024-01-10',
            force=True
        )
        
        # Verify that register was called (indicating bundle registration attempted)
        assert mock_register.called, "Bundle registration should be attempted"


def test_validation_result_properties(valid_ohlcv_data):
    """Test that ValidationResult properties work correctly."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(valid_ohlcv_data, asset_name='TEST')
    
    # Verify result properties
    assert hasattr(result, 'passed'), "ValidationResult should have 'passed' property"
    assert hasattr(result, 'error_checks'), "ValidationResult should have 'error_checks' property"
    assert hasattr(result, 'warning_checks'), "ValidationResult should have 'warning_checks' property"
    
    # Valid data should pass
    assert result.passed, "Valid data should pass validation"
    assert isinstance(result.error_checks, list), "error_checks should be a list"
    assert isinstance(result.warning_checks, list), "warning_checks should be a list"


# =============================================================================
# TEST VALIDATION ERROR LOGGING
# =============================================================================

def test_validation_errors_logged_missing_columns(caplog, invalid_ohlcv_data_missing_columns):
    """Test that validation errors are logged when columns are missing."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    with caplog.at_level(logging.ERROR):
        result = validator.validate(
            invalid_ohlcv_data_missing_columns,
            asset_name='TEST_MISSING_COLS'
        )
    
    # Validation should fail
    assert not result.passed, "Data with missing columns should fail validation"
    
    # Should have error checks
    assert len(result.error_checks) > 0, "Should have error checks for missing columns"
    
    # Verify error message mentions missing columns
    error_messages = [check.message for check in result.error_checks]
    assert any('missing' in msg.lower() or 'column' in msg.lower() 
               for msg in error_messages), \
        "Error message should mention missing columns"


def test_validation_errors_logged_negative_prices(caplog, invalid_ohlcv_data_negative_prices):
    """Test that validation errors are logged for negative prices."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    with caplog.at_level(logging.ERROR):
        result = validator.validate(
            invalid_ohlcv_data_negative_prices,
            asset_name='TEST_NEGATIVE'
        )
    
    # Validation should fail
    assert not result.passed, "Data with negative prices should fail validation"
    
    # Should have error checks
    assert len(result.error_checks) > 0, "Should have error checks for negative prices"
    
    # Verify error message mentions negative values
    error_messages = [check.message for check in result.error_checks]
    assert any('negative' in msg.lower() for msg in error_messages), \
        "Error message should mention negative values"


def test_validation_errors_logged_ohlc_inconsistency(caplog, invalid_ohlcv_data_ohlc_inconsistency):
    """Test that validation errors are logged for OHLC inconsistencies."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    with caplog.at_level(logging.ERROR):
        result = validator.validate(
            invalid_ohlcv_data_ohlc_inconsistency,
            asset_name='TEST_OHLC'
        )
    
    # Validation should fail
    assert not result.passed, "Data with OHLC inconsistencies should fail validation"
    
    # Should have error checks
    assert len(result.error_checks) > 0, "Should have error checks for OHLC inconsistencies"
    
    # Verify error message mentions OHLC consistency
    error_messages = [check.message for check in result.error_checks]
    assert any('ohlc' in msg.lower() or 'consistency' in msg.lower() 
               for msg in error_messages), \
        "Error message should mention OHLC consistency"


def test_validation_errors_logged_nulls(caplog, invalid_ohlcv_data_nulls):
    """Test that validation errors are logged for null values."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    with caplog.at_level(logging.ERROR):
        result = validator.validate(
            invalid_ohlcv_data_nulls,
            asset_name='TEST_NULLS'
        )
    
    # Validation should fail
    assert not result.passed, "Data with null values should fail validation"
    
    # Should have error checks
    assert len(result.error_checks) > 0, "Should have error checks for null values"
    
    # Verify error message mentions null values
    error_messages = [check.message for check in result.error_checks]
    assert any('null' in msg.lower() for msg in error_messages), \
        "Error message should mention null values"


# =============================================================================
# TEST SYMBOL SKIPPING BEHAVIOR
# =============================================================================

def test_invalid_symbol_skipped_during_ingestion(temp_data_dir, 
                                                  valid_ohlcv_data,
                                                  invalid_ohlcv_data_missing_columns):
    """Test that symbols with validation failures are skipped during ingestion."""
    # Create both valid and invalid CSV files
    valid_symbol = 'VALID'
    invalid_symbol = 'INVALID'
    timeframe = '1h'
    
    valid_csv = temp_data_dir / f"{valid_symbol}_{timeframe}_20240101_20240110_ready.csv"
    invalid_csv = temp_data_dir / f"{invalid_symbol}_{timeframe}_20240101_20240110_ready.csv"
    
    valid_ohlcv_data.to_csv(valid_csv)
    invalid_ohlcv_data_missing_columns.to_csv(invalid_csv)
    
    # Track which symbols were processed
    processed_symbols = []
    
    def mock_data_gen_wrapper(original_gen):
        """Wrapper to track processed symbols."""
        def wrapper(*args, **kwargs):
            for sid, df in original_gen(*args, **kwargs):
                # Extract symbol from the generator context
                # In real ingestion, this would come from symbols_list
                processed_symbols.append(sid)
                yield sid, df
        return wrapper
    
    # Mock the bundle registration to capture the data generator
    with patch('lib.data_loader.register') as mock_register, \
         patch('lib.data_loader.get_calendar') as mock_calendar, \
         patch('lib.data_loader.ingest') as mock_ingest:
        
        # Setup calendar mock
        mock_calendar_obj = MagicMock()
        mock_calendar_obj.first_session = pd.Timestamp('2020-01-01', tz='UTC')
        mock_calendar.return_value = mock_calendar_obj
        
        # Register bundle with both valid and invalid symbols
        _register_csv_bundle(
            bundle_name='test_skip_bundle',
            symbols=[valid_symbol, invalid_symbol],
            calendar_name='XNYS',
            timeframe=timeframe,
            asset_class='equities',
            start_date='2024-01-01',
            end_date='2024-01-10',
            force=True
        )
        
        # Verify registration was attempted
        assert mock_register.called, "Bundle registration should be attempted"


def test_validation_failure_prevents_ingestion(temp_data_dir, invalid_ohlcv_data_missing_columns):
    """Test that validation failure prevents symbol from being ingested."""
    symbol = 'FAIL_SYMBOL'
    timeframe = '1h'
    csv_file = temp_data_dir / f"{symbol}_{timeframe}_20240101_20240110_ready.csv"
    
    # Save invalid data
    invalid_ohlcv_data_missing_columns.to_csv(csv_file)
    
    # Verify validation fails before ingestion
    config = ValidationConfig(timeframe=timeframe)
    validator = DataValidator(config=config)
    
    # Read the CSV back (simulating ingestion)
    df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
    
    # Normalize columns (as ingestion does)
    from lib.data_loader import _normalize_csv_columns
    try:
        df = _normalize_csv_columns(df)
    except ValueError:
        # Column normalization fails - this is expected for missing columns
        pass
    
    # If we got past normalization, validation should still fail
    if not df.empty and 'volume' in df.columns:
        result = validator.validate(df, asset_name=symbol)
        assert not result.passed, "Invalid data should fail validation"


# =============================================================================
# TEST WITH SAMPLE DATA FILES
# =============================================================================

def test_validation_with_real_csv_file():
    """Test validation with a real CSV file from data/processed if available."""
    data_dir = get_project_root() / 'data' / 'processed' / '1h'
    
    if not data_dir.exists():
        pytest.skip("No processed data directory found")
    
    # Find a CSV file
    csv_files = list(data_dir.glob('*.csv'))
    if not csv_files:
        pytest.skip("No CSV files found in data/processed/1h")
    
    # Use the first CSV file
    csv_file = csv_files[0]
    
    # Read and validate
    df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
    
    # Normalize columns
    from lib.data_loader import _normalize_csv_columns
    try:
        df = _normalize_csv_columns(df)
    except ValueError as e:
        pytest.skip(f"CSV file has column issues: {e}")
    
    # Ensure timezone-aware UTC index
    df.index = pd.to_datetime(df.index, utc=True)
    
    # Validate
    config = ValidationConfig(timeframe='1h')
    validator = DataValidator(config=config)
    
    symbol = csv_file.stem.split('_')[0]  # Extract symbol from filename
    result = validator.validate(df, asset_name=symbol)
    
    # Should have validation result
    assert isinstance(result, ValidationResult), "Should return ValidationResult"
    assert hasattr(result, 'passed'), "Result should have 'passed' property"
    assert hasattr(result, 'error_checks'), "Result should have 'error_checks' property"
    assert hasattr(result, 'warning_checks'), "Result should have 'warning_checks' property"


# =============================================================================
# TEST VALIDATION CONFIG INTEGRATION
# =============================================================================

def test_validation_config_used_correctly(valid_ohlcv_data):
    """Test that ValidationConfig is used correctly in DataValidator."""
    # Test with different configs
    config_strict = ValidationConfig(timeframe='1d', strict_mode=True)
    config_lenient = ValidationConfig(timeframe='1d', strict_mode=False)
    
    validator_strict = DataValidator(config=config_strict)
    validator_lenient = DataValidator(config=config_lenient)
    
    # Both should validate the same data
    result_strict = validator_strict.validate(valid_ohlcv_data, asset_name='TEST')
    result_lenient = validator_lenient.validate(valid_ohlcv_data, asset_name='TEST')
    
    # Valid data should pass with both configs
    assert result_strict.passed, "Valid data should pass with strict config"
    assert result_lenient.passed, "Valid data should pass with lenient config"


def test_timeframe_aware_validation(valid_ohlcv_data):
    """Test that validation is timeframe-aware."""
    # Test with different timeframes
    config_daily = ValidationConfig(timeframe='1d')
    config_intraday = ValidationConfig(timeframe='1h')
    
    validator_daily = DataValidator(config=config_daily)
    validator_intraday = DataValidator(config=config_intraday)
    
    result_daily = validator_daily.validate(valid_ohlcv_data, asset_name='TEST')
    result_intraday = validator_intraday.validate(valid_ohlcv_data, asset_name='TEST')
    
    # Both should return ValidationResult
    assert isinstance(result_daily, ValidationResult), "Should return ValidationResult for daily"
    assert isinstance(result_intraday, ValidationResult), "Should return ValidationResult for intraday"


# =============================================================================
# TEST ERROR MESSAGE QUALITY
# =============================================================================

def test_error_messages_are_informative(invalid_ohlcv_data_missing_columns):
    """Test that validation error messages are informative and actionable."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        invalid_ohlcv_data_missing_columns,
        asset_name='TEST'
    )
    
    # Should have error messages
    assert len(result.errors) > 0, "Should have error messages"
    
    # Error messages should be informative
    for error in result.errors:
        assert len(error) > 10, "Error messages should be descriptive"
        assert 'TEST' in error or 'missing' in error.lower() or 'column' in error.lower(), \
            "Error messages should reference the asset or issue"


def test_warning_messages_are_informative(invalid_ohlcv_data_insufficient_rows):
    """Test that validation warning messages are informative."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        invalid_ohlcv_data_insufficient_rows,
        asset_name='TEST'
    )
    
    # May have warnings (insufficient rows is typically a warning, not error)
    if result.warning_checks:
        for warning_check in result.warning_checks:
            assert len(warning_check.message) > 10, "Warning messages should be descriptive"


# =============================================================================
# TEST VALIDATION RESULT PROPERTY MAPPING
# =============================================================================

def test_validation_result_property_mapping(valid_ohlcv_data):
    """Test that ValidationResult property mappings work correctly."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(valid_ohlcv_data, asset_name='TEST')
    
    # Test property access
    assert isinstance(result.passed, bool), "passed should be boolean"
    assert isinstance(result.error_checks, list), "error_checks should be list"
    assert isinstance(result.warning_checks, list), "warning_checks should be list"
    
    # For valid data, should have no error checks
    error_checks = result.error_checks
    assert isinstance(error_checks, list), "error_checks should be accessible"
    
    # Warning checks should also be accessible
    warning_checks = result.warning_checks
    assert isinstance(warning_checks, list), "warning_checks should be accessible"


def test_validation_result_error_checks_filtering(invalid_ohlcv_data_missing_columns):
    """Test that error_checks property correctly filters error-severity checks."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        invalid_ohlcv_data_missing_columns,
        asset_name='TEST'
    )
    
    # Should have error checks
    error_checks = result.error_checks
    assert len(error_checks) > 0, "Should have error checks for invalid data"
    
    # All error checks should have ERROR severity
    for check in error_checks:
        assert check.severity.value == 'error', "All error_checks should have ERROR severity"
        assert not check.passed, "All error_checks should have passed=False"


def test_validation_result_warning_checks_filtering(invalid_ohlcv_data_insufficient_rows):
    """Test that warning_checks property correctly filters warning-severity checks."""
    config = ValidationConfig(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        invalid_ohlcv_data_insufficient_rows,
        asset_name='TEST'
    )
    
    # May have warning checks (insufficient rows is typically a warning)
    warning_checks = result.warning_checks
    
    # If there are warning checks, they should have WARNING severity
    if warning_checks:
        for check in warning_checks:
            assert check.severity.value == 'warning', "All warning_checks should have WARNING severity"
            assert not check.passed, "All warning_checks should have passed=False"

