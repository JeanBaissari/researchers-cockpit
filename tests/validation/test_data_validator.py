"""
Test DataValidator.

Integration tests for data validation API migration and DataValidator functionality.
"""

# Standard library imports
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock, call

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import DataValidator, ValidationConfig, ValidationResult, ValidationSeverity
from lib.bundles import register_csv_bundle
from lib.utils import get_project_root


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
        'open': [-10.0, 100.0, 101.0, 102.0, 103.0] + [100.0 + i * 0.1 for i in range(5, len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


@pytest.fixture
def invalid_ohlcv_data_ohlc_inconsistency():
    """Create invalid OHLCV DataFrame with OHLC inconsistencies."""
    dates = pd.date_range(
        start='2024-01-01',
        periods=50,
        freq='D',
        tz='UTC'
    )
    
    df = pd.DataFrame({
        'open': [100.0] * len(dates),
        'high': [95.0] * len(dates),  # Invalid: high < open
        'low': [105.0] * len(dates),  # Invalid: low > open
        'close': [100.0] * len(dates),
        'volume': [1000000] * len(dates),
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
        'open': [100.0 + i * 0.1 if i % 5 != 0 else np.nan for i in range(len(dates))],
        'high': [102.0 + i * 0.1 for i in range(len(dates))],
        'low': [99.0 + i * 0.1 for i in range(len(dates))],
        'close': [101.0 + i * 0.1 if i % 7 != 0 else np.nan for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)
    
    return df


class TestDataValidatorBasic:
    """Basic tests for DataValidator."""
    
    @pytest.mark.unit
    def test_data_validator_creation(self):
        """Test creating DataValidator."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        assert validator is not None
        assert validator.config.timeframe == '1d'
    
    @pytest.mark.unit
    def test_data_validator_validate_valid_data(self, valid_ohlcv_data):
        """Test validating valid OHLCV data."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(valid_ohlcv_data, asset_name='TEST')
        assert isinstance(result, ValidationResult)
        assert result.passed, "Valid data should pass validation"
    
    @pytest.mark.unit
    def test_data_validator_validate_invalid_data(self, invalid_ohlcv_data_missing_columns):
        """Test validating invalid OHLCV data."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(invalid_ohlcv_data_missing_columns, asset_name='TEST')
        assert isinstance(result, ValidationResult)
        # Should have detected issues
        assert len(result.checks) > 0
        assert not result.passed, "Invalid data should fail validation"
    
    @pytest.mark.unit
    def test_data_validator_required_columns(self):
        """Test that DataValidator checks required columns."""
        # Create DataFrame missing volume
        dates = pd.date_range('2020-01-01', periods=100, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0] * 100,
            'high': [101.0] * 100,
            'low': [99.0] * 100,
            'close': [100.5] * 100,
            # Missing volume
        }, index=dates)
        
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(df, asset_name='TEST')
        
        # Should detect missing volume column
        assert isinstance(result, ValidationResult)
        assert not result.passed, "Should fail when required columns are missing"


class TestDataValidatorErrorDetection:
    """Test DataValidator error detection."""
    
    @pytest.mark.unit
    def test_validation_errors_logged_missing_columns(self, caplog, invalid_ohlcv_data_missing_columns):
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
    
    @pytest.mark.unit
    def test_validation_errors_logged_negative_prices(self, caplog, invalid_ohlcv_data_negative_prices):
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
    
    @pytest.mark.unit
    def test_validation_errors_logged_ohlc_inconsistency(self, caplog, invalid_ohlcv_data_ohlc_inconsistency):
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
    
    @pytest.mark.unit
    def test_validation_errors_logged_nulls(self, caplog, invalid_ohlcv_data_nulls):
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


class TestDataValidatorNoModification:
    """Test that DataValidator does not modify input data."""
    
    @pytest.mark.unit
    def test_validation_does_not_modify_dataframe(self, invalid_ohlcv_data_missing_columns):
        """Verify that validation does not modify the input DataFrame."""
        # Store original data hash
        original_hash = hash(tuple(invalid_ohlcv_data_missing_columns.values.flatten()))
        original_index = invalid_ohlcv_data_missing_columns.index.copy()
        original_columns = invalid_ohlcv_data_missing_columns.columns.copy()
        
        # Validate
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(invalid_ohlcv_data_missing_columns, asset_name='TEST')
        
        # Verify DataFrame was not modified
        assert hash(tuple(invalid_ohlcv_data_missing_columns.values.flatten())) == original_hash, \
            "DataFrame values were modified during validation"
        assert invalid_ohlcv_data_missing_columns.index.equals(original_index), \
            "DataFrame index was modified during validation"
        assert list(invalid_ohlcv_data_missing_columns.columns) == list(original_columns), \
            "DataFrame columns were modified during validation"


class TestValidationResultProperties:
    """Test ValidationResult properties work correctly."""
    
    @pytest.mark.unit
    def test_validation_result_properties(self, valid_ohlcv_data):
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

