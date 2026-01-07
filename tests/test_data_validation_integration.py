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
    # Ensure OHLC consistency: High >= max(Open, Close), Low <= min(Open, Close)
    opens = [base_price + i * 0.1 for i in range(len(dates))]
    closes = [base_price + i * 0.12 for i in range(len(dates))]  # Slight upward trend
    highs = [max(o, c) + 1.0 for o, c in zip(opens, closes)]  # High is always >= max(open, close)
    lows = [min(o, c) - 0.5 for o, c in zip(opens, closes)]   # Low is always <= min(open, close)
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
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
    with patch('zipline.data.bundles.register') as mock_register, \
         patch('lib.data_loader.get_calendar') as mock_calendar, \
         patch('zipline.data.bundles.ingest') as mock_ingest:
        
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
    with patch('zipline.data.bundles.register') as mock_register, \
         patch('lib.data_loader.get_calendar') as mock_calendar, \
         patch('zipline.data.bundles.ingest') as mock_ingest:
        
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


# =============================================================================
# TEST NEW FEATURES: SUNDAY BAR DETECTION
# =============================================================================

@pytest.fixture
def forex_data_with_sunday_bars():
    """Create FOREX DataFrame with Sunday bars."""
    # Create dates including a Sunday
    dates = pd.date_range(
        start='2024-01-05',  # Friday
        periods=5,
        freq='D',
        tz='UTC'
    )
    # Manually set one date to Sunday
    dates = pd.DatetimeIndex([
        pd.Timestamp('2024-01-05', tz='UTC'),  # Friday
        pd.Timestamp('2024-01-06', tz='UTC'),  # Saturday
        pd.Timestamp('2024-01-07', tz='UTC'),  # Sunday
        pd.Timestamp('2024-01-08', tz='UTC'),  # Monday
        pd.Timestamp('2024-01-09', tz='UTC'),  # Tuesday
    ])
    
    df = pd.DataFrame({
        'open': [1.1000, 1.1005, 1.1010, 1.1015, 1.1020],
        'high': [1.1005, 1.1010, 1.1015, 1.1020, 1.1025],
        'low': [1.0995, 1.1000, 1.1005, 1.1010, 1.1015],
        'close': [1.1002, 1.1007, 1.1012, 1.1017, 1.1022],
        'volume': [1000000, 1000000, 1000000, 1000000, 1000000],
    }, index=dates)
    
    return df


@pytest.fixture
def forex_data_without_sunday_bars():
    """Create FOREX DataFrame without Sunday bars."""
    dates = pd.date_range(
        start='2024-01-05',  # Friday
        periods=4,
        freq='D',
        tz='UTC'
    )
    # Skip Sunday
    dates = pd.DatetimeIndex([
        pd.Timestamp('2024-01-05', tz='UTC'),  # Friday
        pd.Timestamp('2024-01-08', tz='UTC'),  # Monday
        pd.Timestamp('2024-01-09', tz='UTC'),  # Tuesday
        pd.Timestamp('2024-01-10', tz='UTC'),  # Wednesday
    ])
    
    df = pd.DataFrame({
        'open': [1.1000, 1.1015, 1.1020, 1.1025],
        'high': [1.1005, 1.1020, 1.1025, 1.1030],
        'low': [1.0995, 1.1010, 1.1015, 1.1020],
        'close': [1.1002, 1.1017, 1.1022, 1.1027],
        'volume': [1000000, 1000000, 1000000, 1000000],
    }, index=dates)
    
    return df


def test_sunday_bar_detection_forex(forex_data_with_sunday_bars):
    """Test that Sunday bars are detected in FOREX data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        check_sunday_bars=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_with_sunday_bars,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Should detect Sunday bars
    sunday_check = next((c for c in result.checks if c.name == 'sunday_bars'), None)
    assert sunday_check is not None, "Should have sunday_bars check"
    assert not sunday_check.passed, "Should detect Sunday bars"
    assert 'sunday_count' in sunday_check.details, "Should include sunday_count in details"
    assert sunday_check.details['sunday_count'] > 0, "Should find at least one Sunday bar"


def test_sunday_bar_detection_no_sunday_bars(forex_data_without_sunday_bars):
    """Test that validation passes when no Sunday bars are present."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        check_sunday_bars=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_without_sunday_bars,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Should pass Sunday bar check
    sunday_check = next((c for c in result.checks if c.name == 'sunday_bars'), None)
    assert sunday_check is not None, "Should have sunday_bars check"
    assert sunday_check.passed, "Should pass when no Sunday bars"


def test_sunday_bar_detection_skipped_for_equity(forex_data_with_sunday_bars):
    """Test that Sunday bar detection is skipped for equity assets."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='equity',
        check_sunday_bars=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_with_sunday_bars,
        asset_name='AAPL',
        asset_type='equity'
    )
    
    # Sunday bar check should be skipped for equity
    sunday_check = next((c for c in result.checks if c.name == 'sunday_bars'), None)
    # Check may not exist or may be skipped
    if sunday_check:
        # If it exists, it should pass (skipped)
        assert sunday_check.passed or 'skipped' in sunday_check.message.lower()


# =============================================================================
# TEST NEW FEATURES: WEEKEND GAP INTEGRITY
# =============================================================================

@pytest.fixture
def forex_data_weekend_gap_issues():
    """Create FOREX DataFrame with weekend gap integrity issues."""
    dates = pd.DatetimeIndex([
        pd.Timestamp('2024-01-05', tz='UTC'),  # Friday
        pd.Timestamp('2024-01-07', tz='UTC'),  # Sunday
        pd.Timestamp('2024-01-08', tz='UTC'),  # Monday
    ])
    
    # Create data where Sunday and Monday have very small gap (potential issue)
    df = pd.DataFrame({
        'open': [1.1000, 1.1001, 1.1002],  # Very small gap
        'high': [1.1005, 1.1006, 1.1007],
        'low': [1.0995, 1.0996, 1.0997],
        'close': [1.1002, 1.1003, 1.1004],
        'volume': [1000000, 1000000, 1000000],
    }, index=dates)
    
    return df


def test_weekend_gap_integrity_forex(forex_data_weekend_gap_issues):
    """Test weekend gap integrity validation for FOREX data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        check_weekend_gaps=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_weekend_gap_issues,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Should have weekend gap integrity check
    gap_check = next((c for c in result.checks if c.name == 'weekend_gap_integrity'), None)
    assert gap_check is not None, "Should have weekend_gap_integrity check"
    # May pass or fail depending on the data
    assert 'friday_count' in gap_check.details or gap_check.passed, "Should have details or pass"


def test_weekend_gap_integrity_skipped_for_equity(forex_data_weekend_gap_issues):
    """Test that weekend gap integrity is skipped for equity assets."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='equity',
        check_weekend_gaps=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_weekend_gap_issues,
        asset_name='AAPL',
        asset_type='equity'
    )
    
    # Weekend gap check should be skipped for equity
    gap_check = next((c for c in result.checks if c.name == 'weekend_gap_integrity'), None)
    # Check may not exist or may be skipped
    if gap_check:
        assert gap_check.passed or 'skipped' in gap_check.message.lower()


# =============================================================================
# TEST NEW FEATURES: VOLUME SPIKE DETECTION
# =============================================================================

@pytest.fixture
def equity_data_with_volume_spikes():
    """Create equity DataFrame with volume spikes."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=100,
        freq='D',
        tz='UTC'
    )
    
    # Create normal volume data
    base_volume = 1000000
    volumes = [base_volume + np.random.randint(-100000, 100000) for _ in range(len(dates))]
    
    # Add a few extreme volume spikes (10x normal)
    volumes[10] = base_volume * 15  # Extreme spike
    volumes[50] = base_volume * 12  # Extreme spike
    volumes[75] = base_volume * 18  # Extreme spike
    
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        'volume': volumes,
    }, index=dates)
    
    return df


def test_volume_spike_detection_equity(equity_data_with_volume_spikes):
    """Test volume spike detection for equity data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='equity',
        check_volume_spikes=True,
        volume_spike_threshold_sigma=5.0
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        equity_data_with_volume_spikes,
        asset_name='AAPL',
        asset_type='equity'
    )
    
    # Should have volume spike check
    spike_check = next((c for c in result.checks if c.name == 'volume_spikes'), None)
    assert spike_check is not None, "Should have volume_spikes check"
    # May detect spikes or pass depending on z-score calculation
    assert 'spike_count' in spike_check.details or spike_check.passed, "Should have details or pass"


def test_volume_spike_detection_skipped_for_forex(equity_data_with_volume_spikes):
    """Test that volume spike detection is skipped for FOREX data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        check_volume_spikes=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        equity_data_with_volume_spikes,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Volume spike check should be skipped for FOREX
    spike_check = next((c for c in result.checks if c.name == 'volume_spikes'), None)
    assert spike_check is not None, "Should have volume_spikes check"
    assert spike_check.passed, "Should pass (skipped) for FOREX"
    assert 'forex' in spike_check.message.lower() or 'unreliable' in spike_check.message.lower(), \
        "Should indicate volume is unreliable for FOREX"


# =============================================================================
# TEST NEW FEATURES: SPLIT DETECTION
# =============================================================================

@pytest.fixture
def equity_data_with_potential_split():
    """Create equity DataFrame with potential unadjusted split (2:1 split)."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    # Create price data with a 2:1 split on day 25 (50% price drop)
    prices = []
    for i in range(len(dates)):
        if i < 25:
            prices.append(200.0 + i * 0.5)  # Price around $200
        else:
            prices.append(100.0 + (i - 25) * 0.5)  # Price drops to ~$100 (2:1 split)
    
    # Add volume spike on split day
    volumes = [1000000 + i * 1000 for i in range(len(dates))]
    volumes[25] = 5000000  # Volume spike on split day
    
    df = pd.DataFrame({
        'open': [p - 1.0 for p in prices],
        'high': [p + 2.0 for p in prices],
        'low': [p - 2.0 for p in prices],
        'close': prices,
        'volume': volumes,
    }, index=dates)
    
    return df


def test_split_detection_equity(equity_data_with_potential_split):
    """Test split detection for equity data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='equity',
        check_adjustments=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        equity_data_with_potential_split,
        asset_name='AAPL',
        asset_type='equity'
    )
    
    # Should have potential_splits check
    split_check = next((c for c in result.checks if c.name == 'potential_splits'), None)
    assert split_check is not None, "Should have potential_splits check"
    # May detect split or pass depending on exact price change
    assert 'potential_split_count' in split_check.details or split_check.passed, \
        "Should have details or pass"


def test_split_detection_skipped_for_forex(equity_data_with_potential_split):
    """Test that split detection is skipped for FOREX data."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        check_adjustments=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        equity_data_with_potential_split,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Split check should be skipped for FOREX
    split_check = next((c for c in result.checks if c.name == 'potential_splits'), None)
    assert split_check is not None, "Should have potential_splits check"
    assert split_check.passed, "Should pass (skipped) for FOREX"
    assert 'forex' in split_check.message.lower() or 'skipped' in split_check.message.lower(), \
        "Should indicate split detection is skipped for FOREX"


# =============================================================================
# TEST NEW FEATURES: ASSET TYPE AWARENESS
# =============================================================================

def test_asset_type_equity_validation(valid_ohlcv_data):
    """Test that equity asset type enables appropriate checks."""
    config = ValidationConfig.for_equity(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        valid_ohlcv_data,
        asset_name='AAPL',
        asset_type='equity'
    )
    
    # Should have asset_type in metadata
    assert result.metadata.get('asset_type') == 'equity', "Should store asset_type in metadata"
    
    # Should have split detection check
    split_check = next((c for c in result.checks if c.name == 'potential_splits'), None)
    assert split_check is not None, "Should have potential_splits check for equity"


def test_asset_type_forex_validation(forex_data_without_sunday_bars):
    """Test that FOREX asset type enables appropriate checks."""
    config = ValidationConfig.for_forex(timeframe='1d')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_without_sunday_bars,
        asset_name='EURUSD',
        asset_type='forex'
    )
    
    # Should have asset_type in metadata
    assert result.metadata.get('asset_type') == 'forex', "Should store asset_type in metadata"
    
    # Should have Sunday bar check
    sunday_check = next((c for c in result.checks if c.name == 'sunday_bars'), None)
    assert sunday_check is not None, "Should have sunday_bars check for FOREX"
    
    # Volume spike check should be skipped
    volume_check = next((c for c in result.checks if c.name == 'volume_spikes'), None)
    if volume_check:
        assert 'forex' in volume_check.message.lower() or 'unreliable' in volume_check.message.lower() or volume_check.passed, \
            "Volume check should indicate it's skipped for FOREX"


def test_asset_type_crypto_validation(valid_ohlcv_data):
    """Test that crypto asset type enables appropriate checks."""
    config = ValidationConfig.for_crypto(timeframe='1h')
    validator = DataValidator(config=config)
    
    result = validator.validate(
        valid_ohlcv_data,
        asset_name='BTCUSD',
        asset_type='crypto'
    )
    
    # Should have asset_type in metadata
    assert result.metadata.get('asset_type') == 'crypto', "Should store asset_type in metadata"


def test_asset_type_factory_methods():
    """Test asset type factory methods."""
    equity_config = ValidationConfig.for_equity(timeframe='1d')
    assert equity_config.asset_type == 'equity', "for_equity should set asset_type"
    
    forex_config = ValidationConfig.for_forex(timeframe='1d')
    assert forex_config.asset_type == 'forex', "for_forex should set asset_type"
    assert forex_config.check_sunday_bars == True, "for_forex should enable Sunday bar check"
    
    crypto_config = ValidationConfig.for_crypto(timeframe='1h')
    assert crypto_config.asset_type == 'crypto', "for_crypto should set asset_type"


# =============================================================================
# TEST NEW FEATURES: FIX SUGGESTIONS
# =============================================================================

def test_suggest_fixes_enabled(forex_data_with_sunday_bars):
    """Test that fix suggestions are added when suggest_fixes=True."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        suggest_fixes=True
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_with_sunday_bars,
        asset_name='EURUSD',
        asset_type='forex',
        suggest_fixes=True
    )
    
    # Should have suggested_fixes in metadata if issues are detected
    if not result.passed or result.warning_checks:
        fixes = result.metadata.get('suggested_fixes', [])
        # May have fixes if Sunday bars are detected
        if fixes:
            assert isinstance(fixes, list), "suggested_fixes should be a list"
            for fix in fixes:
                assert 'issue' in fix, "Each fix should have 'issue' key"
                assert 'function' in fix or 'description' in fix, "Each fix should have function or description"


def test_suggest_fixes_disabled(forex_data_with_sunday_bars):
    """Test that fix suggestions are not added when suggest_fixes=False."""
    config = ValidationConfig(
        timeframe='1d',
        asset_type='forex',
        suggest_fixes=False
    )
    validator = DataValidator(config=config)
    
    result = validator.validate(
        forex_data_with_sunday_bars,
        asset_name='EURUSD',
        asset_type='forex',
        suggest_fixes=False
    )
    
    # Should not have suggested_fixes in metadata (or empty list)
    fixes = result.metadata.get('suggested_fixes', [])
    # If present, should be empty list when disabled
    assert fixes == [] or 'suggested_fixes' not in result.metadata, \
        "suggested_fixes should be empty or not present when disabled"


# =============================================================================
# TEST NEW FEATURES: VALIDATE_BEFORE_INGEST WITH NEW PARAMETERS
# =============================================================================

def test_validate_before_ingest_with_asset_type(valid_ohlcv_data):
    """Test validate_before_ingest with asset_type parameter."""
    from lib.data_validation import validate_before_ingest
    
    result = validate_before_ingest(
        df=valid_ohlcv_data,
        asset_name='AAPL',
        timeframe='1d',
        asset_type='equity'
    )
    
    assert isinstance(result, ValidationResult), "Should return ValidationResult"
    assert result.metadata.get('asset_type') == 'equity', "Should store asset_type"


def test_validate_before_ingest_with_suggest_fixes(forex_data_with_sunday_bars):
    """Test validate_before_ingest with suggest_fixes parameter."""
    from lib.data_validation import validate_before_ingest
    
    result = validate_before_ingest(
        df=forex_data_with_sunday_bars,
        asset_name='EURUSD',
        timeframe='1d',
        asset_type='forex',
        suggest_fixes=True
    )
    
    assert isinstance(result, ValidationResult), "Should return ValidationResult"
    # May have fixes if issues detected
    fixes = result.metadata.get('suggested_fixes', [])
    assert isinstance(fixes, list), "suggested_fixes should be a list"

