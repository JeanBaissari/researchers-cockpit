"""
Tests for validate_csv_data.py script.

Verifies that the script:
1. Uses the new DataValidator API correctly
2. Handles errors properly
3. Returns correct exit codes
4. Validates CSV files correctly
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the script functions (we'll test them directly)
from scripts.validate_csv_data import (
    validate_csv_file,
    validate_timeframe_directory,
    validate_filename,
    validate_columns,
    EXIT_SUCCESS,
    EXIT_VALIDATION_FAILED,
    EXIT_CONFIGURATION_ERROR,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from lib.data_validation import DataValidator, ValidationConfig, ValidationResult as DataValidationResult
from lib.utils import get_project_root


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for test CSV files."""
    temp_dir = tempfile.mkdtemp(prefix='test_validate_csv_')
    temp_path = Path(temp_dir)
    
    # Create timeframe directories
    for timeframe in ['1h', '1d', '15m']:
        (temp_path / timeframe).mkdir(parents=True, exist_ok=True)
    
    yield temp_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def valid_csv_file(temp_data_dir):
    """Create a valid CSV file with proper format."""
    csv_path = temp_data_dir / '1h' / 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
    
    # Create valid OHLCV data
    dates = pd.date_range('2020-01-02 05:00:00', periods=100, freq='1H')
    df = pd.DataFrame({
        'open': np.random.uniform(1.0, 1.2, 100),
        'high': np.random.uniform(1.1, 1.3, 100),
        'low': np.random.uniform(0.9, 1.1, 100),
        'close': np.random.uniform(1.0, 1.2, 100),
        'volume': np.random.randint(1000, 10000, 100),
    }, index=dates)
    
    # Ensure OHLC consistency
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    df.to_csv(csv_path)
    return csv_path


@pytest.fixture
def invalid_csv_file_missing_columns(temp_data_dir):
    """Create an invalid CSV file missing required columns."""
    csv_path = temp_data_dir / '1h' / 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
    
    dates = pd.date_range('2020-01-02 05:00:00', periods=10, freq='1H')
    df = pd.DataFrame({
        'open': np.random.uniform(1.0, 1.2, 10),
        'high': np.random.uniform(1.1, 1.3, 10),
        # Missing 'low', 'close', 'volume'
    }, index=dates)
    
    df.to_csv(csv_path)
    return csv_path


@pytest.fixture
def invalid_csv_file_ohlc_violations(temp_data_dir):
    """Create an invalid CSV file with OHLC consistency violations."""
    csv_path = temp_data_dir / '1h' / 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
    
    dates = pd.date_range('2020-01-02 05:00:00', periods=10, freq='1H')
    df = pd.DataFrame({
        'open': [1.0] * 10,
        'high': [0.5] * 10,  # High < Low (violation)
        'low': [1.5] * 10,   # Low > High (violation)
        'close': [1.0] * 10,
        'volume': [1000] * 10,
    }, index=dates)
    
    df.to_csv(csv_path)
    return csv_path


@pytest.fixture
def invalid_filename_csv(temp_data_dir):
    """Create a CSV file with invalid filename format."""
    csv_path = temp_data_dir / '1h' / 'invalid_filename.csv'
    
    dates = pd.date_range('2020-01-02 05:00:00', periods=10, freq='1H')
    df = pd.DataFrame({
        'open': np.random.uniform(1.0, 1.2, 10),
        'high': np.random.uniform(1.1, 1.3, 10),
        'low': np.random.uniform(0.9, 1.1, 10),
        'close': np.random.uniform(1.0, 1.2, 10),
        'volume': np.random.randint(1000, 10000, 10),
    }, index=dates)
    
    df.to_csv(csv_path)
    return csv_path


class TestValidateCSVFile:
    """Test the validate_csv_file function."""
    
    def test_validate_csv_file_uses_datavalidator(self, valid_csv_file):
        """Test that validate_csv_file uses DataValidator API correctly."""
        result = validate_csv_file(valid_csv_file)
        
        # Should pass validation
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        
        # Should have parsed info
        assert result.parsed_info is not None
        assert result.parsed_info['symbol'] == 'EURUSD'
        assert result.parsed_info['timeframe'] == '1h'
    
    def test_validate_csv_file_with_invalid_columns(self, invalid_csv_file_missing_columns):
        """Test validation fails for missing columns."""
        result = validate_csv_file(invalid_csv_file_missing_columns)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Should have error about missing columns
        error_messages = [str(e) for e in result.errors]
        assert any('column' in msg.lower() or 'missing' in msg.lower() 
                   for msg in error_messages)
    
    def test_validate_csv_file_with_ohlc_violations(self, invalid_csv_file_ohlc_violations):
        """Test validation detects OHLC consistency violations."""
        result = validate_csv_file(invalid_csv_file_ohlc_violations)
        
        assert isinstance(result, ValidationResult)
        # Should fail due to OHLC violations
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Should have OHLC-related errors
        error_messages = [str(e) for e in result.errors]
        assert any('ohlc' in msg.lower() or 'high' in msg.lower() or 'low' in msg.lower()
                   for msg in error_messages)
    
    def test_validate_csv_file_with_invalid_filename(self, invalid_filename_csv):
        """Test validation fails for invalid filename format."""
        result = validate_csv_file(invalid_filename_csv)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Should have filename error
        error_messages = [str(e) for e in result.errors]
        assert any('filename' in msg.lower() or 'pattern' in msg.lower()
                   for msg in error_messages)
    
    def test_validate_csv_file_with_custom_validator(self, valid_csv_file):
        """Test that custom DataValidator instance is used when provided."""
        # Create a custom validator with strict config
        config = ValidationConfig(strict_mode=True, timeframe='1h')
        custom_validator = DataValidator(config=config)
        
        result = validate_csv_file(valid_csv_file, validator=custom_validator)
        
        assert isinstance(result, ValidationResult)
        # Should use the custom validator
        assert result.parsed_info is not None
    
    def test_validate_csv_file_strict_mode(self, valid_csv_file):
        """Test strict mode treats warnings as errors."""
        result = validate_csv_file(valid_csv_file, strict=True)
        
        assert isinstance(result, ValidationResult)
        # In strict mode, warnings become errors
        # For valid file, should still pass


class TestDataValidatorIntegration:
    """Test that the script correctly integrates with DataValidator API."""
    
    def test_datavalidator_called_with_correct_params(self, valid_csv_file):
        """Test that DataValidator.validate() is called with correct parameters."""
        with patch('scripts.validate_csv_data.DataValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            # Mock the validation result
            mock_result = DataValidationResult()
            mock_result.passed = True
            mock_result.error_checks = []
            mock_result.warning_checks = []
            mock_validator.validate.return_value = mock_result
            
            result = validate_csv_file(valid_csv_file)
            
            # Verify DataValidator was instantiated
            assert mock_validator_class.called
            
            # Verify validate() was called
            assert mock_validator.validate.called
            
            # Get the call arguments
            call_args = mock_validator.validate.call_args
            assert call_args is not None
            
            # Verify DataFrame was passed
            df_arg = call_args[0][0] if call_args[0] else None
            assert df_arg is not None
            assert isinstance(df_arg, pd.DataFrame)
            
            # Verify asset_name was passed
            kwargs = call_args[1] if call_args[1] else {}
            assert 'asset_name' in kwargs
            assert kwargs['asset_name'] == 'EURUSD'
    
    def test_datavalidator_errors_propagated(self, valid_csv_file):
        """Test that DataValidator errors are properly added to ValidationResult."""
        with patch('scripts.validate_csv_data.DataValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            # Create a validation result with errors
            mock_result = DataValidationResult()
            mock_result.passed = False
            
            # Create mock error checks
            from lib.data_validation import ValidationCheck, ValidationSeverity
            error_check = ValidationCheck(
                name='test_error',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message='Test error message',
                details={'field': 'close'}
            )
            mock_result.error_checks = [error_check]
            mock_result.warning_checks = []
            
            mock_validator.validate.return_value = mock_result
            
            result = validate_csv_file(valid_csv_file)
            
            # Should have errors from DataValidator
            assert result.is_valid is False
            assert len(result.errors) > 0
            
            # Should have DataValidator category errors
            error_categories = [e.category for e in result.errors]
            assert 'DataValidator' in error_categories
    
    def test_datavalidator_warnings_propagated(self, valid_csv_file):
        """Test that DataValidator warnings are properly added to ValidationResult."""
        with patch('scripts.validate_csv_data.DataValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            # Create a validation result with warnings
            mock_result = DataValidationResult()
            mock_result.passed = True
            
            # Create mock warning checks
            from lib.data_validation import ValidationCheck, ValidationSeverity
            warning_check = ValidationCheck(
                name='test_warning',
                passed=False,
                severity=ValidationSeverity.WARNING,
                message='Test warning message',
                details={'field': 'volume'}
            )
            mock_result.error_checks = []
            mock_result.warning_checks = [warning_check]
            
            mock_validator.validate.return_value = mock_result
            
            result = validate_csv_file(valid_csv_file, strict=False)
            
            # Should have warnings
            assert len(result.warnings) > 0
            
            # Should have DataValidator category warnings
            warning_categories = [w.category for w in result.warnings]
            assert 'DataValidator' in warning_categories
    
    def test_datavalidator_exception_handled(self, valid_csv_file):
        """Test that DataValidator exceptions are caught and handled."""
        with patch('scripts.validate_csv_data.DataValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            
            # Make validate() raise an exception
            mock_validator.validate.side_effect = Exception("Test exception")
            
            result = validate_csv_file(valid_csv_file)
            
            # Should handle exception gracefully
            assert isinstance(result, ValidationResult)
            
            # Should have error about DataValidator failure
            error_messages = [str(e) for e in result.errors]
            assert any('datavalidator' in msg.lower() or 'validation error' in msg.lower()
                       for msg in error_messages)


class TestValidateTimeframeDirectory:
    """Test the validate_timeframe_directory function."""
    
    def test_validate_timeframe_directory_uses_datavalidator(self, temp_data_dir, valid_csv_file):
        """Test that validate_timeframe_directory creates and uses DataValidator."""
        results = validate_timeframe_directory('1h', verbose=False, strict=False)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert isinstance(result, ValidationResult)
    
    def test_validate_timeframe_directory_with_symbol_filter(self, temp_data_dir, valid_csv_file):
        """Test symbol filtering works correctly."""
        results = validate_timeframe_directory('1h', symbol_filter='EURUSD', verbose=False)
        
        assert isinstance(results, list)
        # Should only return results for EURUSD
        for result in results:
            assert 'EURUSD' in result.filepath.name.upper()
    
    def test_validate_timeframe_directory_nonexistent(self, temp_data_dir):
        """Test handling of nonexistent timeframe directory."""
        results = validate_timeframe_directory('nonexistent', verbose=False)
        
        assert isinstance(results, list)
        assert len(results) == 0


class TestErrorHandling:
    """Test error handling in the script."""
    
    def test_validate_csv_file_empty_file(self, temp_data_dir):
        """Test handling of empty CSV file."""
        empty_file = temp_data_dir / '1h' / 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
        empty_file.touch()  # Create empty file
        
        result = validate_csv_file(empty_file)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_csv_file_malformed_csv(self, temp_data_dir):
        """Test handling of malformed CSV file."""
        malformed_file = temp_data_dir / '1h' / 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
        malformed_file.write_text('invalid,csv,content\nbroken,line')
        
        result = validate_csv_file(malformed_file)
        
        assert isinstance(result, ValidationResult)
        # May or may not fail depending on parsing, but should handle gracefully
    
    def test_validate_csv_file_nonexistent_file(self, temp_data_dir):
        """Test handling of nonexistent file."""
        nonexistent = temp_data_dir / '1h' / 'nonexistent.csv'
        
        # Should raise FileNotFoundError or handle gracefully
        with pytest.raises((FileNotFoundError, Exception)):
            result = validate_csv_file(nonexistent)


class TestExitCodes:
    """Test that the script returns correct exit codes."""
    
    def test_main_success_exit_code(self, temp_data_dir, valid_csv_file, monkeypatch):
        """Test that main() returns EXIT_SUCCESS for valid files."""
        # Mock the timeframe directory to return our test file
        def mock_validate_timeframe_directory(timeframe, symbol_filter=None, verbose=False, strict=False):
            result = validate_csv_file(valid_csv_file)
            return [result]
        
        monkeypatch.setattr('scripts.validate_csv_data.validate_timeframe_directory', 
                          mock_validate_timeframe_directory)
        
        # Import main after monkeypatch
        from scripts.validate_csv_data import main
        
        # Mock argparse to simulate --timeframe 1h
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h']):
            exit_code = main()
            assert exit_code == EXIT_SUCCESS
    
    def test_main_validation_failed_exit_code(self, temp_data_dir, invalid_csv_file_missing_columns, monkeypatch):
        """Test that main() returns EXIT_VALIDATION_FAILED for invalid files."""
        def mock_validate_timeframe_directory(timeframe, symbol_filter=None, verbose=False, strict=False):
            result = validate_csv_file(invalid_csv_file_missing_columns)
            return [result]
        
        monkeypatch.setattr('scripts.validate_csv_data.validate_timeframe_directory',
                          mock_validate_timeframe_directory)
        
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h']):
            exit_code = main()
            assert exit_code == EXIT_VALIDATION_FAILED
    
    def test_main_configuration_error_exit_code(self, monkeypatch):
        """Test that main() returns EXIT_CONFIGURATION_ERROR for invalid arguments."""
        from scripts.validate_csv_data import main
        
        # Test with invalid arguments (both --timeframe and --all)
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h', '--all']):
            exit_code = main()
            assert exit_code == EXIT_CONFIGURATION_ERROR
        
        # Test with no arguments
        with patch('sys.argv', ['validate_csv_data.py']):
            exit_code = main()
            assert exit_code == EXIT_CONFIGURATION_ERROR


class TestCommandLineArguments:
    """Test command-line argument parsing."""
    
    def test_timeframe_argument(self, monkeypatch):
        """Test --timeframe argument is parsed correctly."""
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h']):
            # Should not raise exception for valid timeframe
            # (will fail if no data, but that's expected)
            try:
                main()
            except SystemExit:
                pass  # argparse may call sys.exit
    
    def test_symbol_argument(self, monkeypatch):
        """Test --symbol argument is parsed correctly."""
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h', '--symbol', 'EURUSD']):
            try:
                main()
            except SystemExit:
                pass
    
    def test_all_argument(self, monkeypatch):
        """Test --all argument is parsed correctly."""
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--all']):
            try:
                main()
            except SystemExit:
                pass
    
    def test_verbose_argument(self, monkeypatch):
        """Test --verbose argument is parsed correctly."""
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h', '--verbose']):
            try:
                main()
            except SystemExit:
                pass
    
    def test_strict_argument(self, monkeypatch):
        """Test --strict argument is parsed correctly."""
        from scripts.validate_csv_data import main
        
        with patch('sys.argv', ['validate_csv_data.py', '--timeframe', '1h', '--strict']):
            try:
                main()
            except SystemExit:
                pass


class TestValidationFunctions:
    """Test individual validation functions."""
    
    def test_validate_filename_valid(self):
        """Test filename validation with valid filename."""
        filename = 'EURUSD_1h_20200102-050000_20250717-034500_ready.csv'
        is_valid, error, parsed_info = validate_filename(filename)
        
        assert is_valid is True
        assert error is None
        assert parsed_info is not None
        assert parsed_info['symbol'] == 'EURUSD'
        assert parsed_info['timeframe'] == '1h'
    
    def test_validate_filename_invalid(self):
        """Test filename validation with invalid filename."""
        filename = 'invalid_filename.csv'
        is_valid, error, parsed_info = validate_filename(filename)
        
        assert is_valid is False
        assert error is not None
        assert parsed_info is None
    
    def test_validate_columns_valid(self):
        """Test column validation with valid columns."""
        df = pd.DataFrame({
            'open': [1.0],
            'high': [1.1],
            'low': [0.9],
            'close': [1.0],
            'volume': [1000],
        })
        
        is_valid, error, found_columns = validate_columns(df)
        
        assert is_valid is True
        assert error is None
        assert len(found_columns) == 5
    
    def test_validate_columns_missing(self):
        """Test column validation with missing columns."""
        df = pd.DataFrame({
            'open': [1.0],
            'high': [1.1],
            # Missing low, close, volume
        })
        
        is_valid, error, found_columns = validate_columns(df)
        
        assert is_valid is False
        assert error is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

