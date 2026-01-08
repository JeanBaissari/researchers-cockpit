"""
Tests to verify that validation fails appropriately without auto-repair.

This test suite verifies that:
1. The new DataValidator does NOT modify data during validation
2. Validation correctly identifies and reports errors
3. Data with issues fails validation and is not automatically fixed
4. Error messages are clear and actionable
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from lib.validation import (
    DataValidator,
    ValidationConfig,
    ValidationResult,
    ValidationSeverity
)


class TestAutoRepairRemoval:
    """Test that validation does not auto-repair data issues."""
    
    def test_validation_does_not_modify_dataframe(self):
        """Verify that validation does not modify the input DataFrame."""
        # Create DataFrame with validation issues
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        }, index=dates)
        
        # Store original data hash
        original_hash = hash(tuple(df.values.flatten()))
        original_index = df.index.copy()
        original_columns = df.columns.copy()
        
        # Validate
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Verify DataFrame was not modified
        assert hash(tuple(df.values.flatten())) == original_hash, \
            "DataFrame values were modified during validation"
        assert df.index.equals(original_index), \
            "DataFrame index was modified during validation"
        assert list(df.columns) == list(original_columns), \
            "DataFrame columns were modified during validation"
    
    def test_missing_columns_fails_validation(self):
        """Verify that missing required columns causes validation to fail."""
        # Create DataFrame missing 'volume' column
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            # Missing 'volume' column
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when required columns are missing"
        
        # Should have error check for missing columns
        error_checks = result.error_checks
        assert len(error_checks) > 0, "Should have at least one error check"
        
        required_columns_check = next(
            (c for c in error_checks if c.name == 'required_columns'),
            None
        )
        assert required_columns_check is not None, \
            "Should have 'required_columns' error check"
        assert not required_columns_check.passed, \
            "required_columns check should have failed"
        assert 'volume' in required_columns_check.details.get('missing_columns', []), \
            "Error should indicate 'volume' is missing"
    
    def test_null_values_fail_validation(self):
        """Verify that null values cause validation to fail."""
        # Create DataFrame with null values
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, None, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when null values are present"
        
        # Should have error check for nulls
        null_check = next(
            (c for c in result.error_checks if c.name == 'no_nulls'),
            None
        )
        assert null_check is not None, "Should have 'no_nulls' error check"
        assert not null_check.passed, "no_nulls check should have failed"
        assert null_check.details.get('null_counts', {}).get('open', 0) > 0, \
            "Error should indicate null values in 'open' column"
    
    def test_ohlc_consistency_violations_fail_validation(self):
        """Verify that OHLC consistency violations cause validation to fail."""
        # Create DataFrame with OHLC violations (high < low)
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [99, 100, 101, 102, 103],  # High < Low (violation)
            'low': [100, 101, 102, 103, 104],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when OHLC consistency is violated"
        
        # Should have error check for OHLC consistency
        ohlc_check = next(
            (c for c in result.error_checks if c.name == 'ohlc_consistency'),
            None
        )
        assert ohlc_check is not None, "Should have 'ohlc_consistency' error check"
        assert not ohlc_check.passed, "ohlc_consistency check should have failed"
        assert ohlc_check.details.get('total_violations', 0) > 0, \
            "Error should indicate number of OHLC violations"
    
    def test_negative_values_fail_validation(self):
        """Verify that negative values cause validation to fail."""
        # Create DataFrame with negative prices
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, -50, 103, 104],  # Negative value
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when negative values are present"
        
        # Should have error check for negative values
        negative_check = next(
            (c for c in result.error_checks if c.name == 'no_negative_values'),
            None
        )
        assert negative_check is not None, "Should have 'no_negative_values' error check"
        assert not negative_check.passed, "no_negative_values check should have failed"
        assert negative_check.details.get('negative_prices', 0) > 0, \
            "Error should indicate number of negative prices"
    
    def test_future_dates_fail_validation(self):
        """Verify that future dates cause validation to fail."""
        # Create DataFrame with future dates
        future_date = datetime.now() + timedelta(days=10)
        dates = pd.date_range(future_date, periods=5, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when future dates are present"
        
        # Should have error check for future dates
        future_check = next(
            (c for c in result.error_checks if c.name == 'no_future_dates'),
            None
        )
        assert future_check is not None, "Should have 'no_future_dates' error check"
        assert not future_check.passed, "no_future_dates check should have failed"
        assert future_check.details.get('future_date_count', 0) > 0, \
            "Error should indicate number of future dates"
    
    def test_duplicate_dates_fail_validation(self):
        """Verify that duplicate dates cause validation to fail."""
        # Create DataFrame with duplicate dates
        dates = pd.DatetimeIndex([
            '2020-01-01',
            '2020-01-02',
            '2020-01-02',  # Duplicate
            '2020-01-03',
            '2020-01-04'
        ])
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail when duplicate dates are present"
        
        # Should have error check for duplicate dates
        duplicate_check = next(
            (c for c in result.error_checks if c.name == 'no_duplicate_dates'),
            None
        )
        assert duplicate_check is not None, "Should have 'no_duplicate_dates' error check"
        assert not duplicate_check.passed, "no_duplicate_dates check should have failed"
        assert duplicate_check.details.get('duplicate_count', 0) > 0, \
            "Error should indicate number of duplicate dates"
    
    def test_unsorted_index_fails_validation(self):
        """Verify that unsorted index causes validation to fail (in strict mode)."""
        # Create DataFrame with unsorted index
        dates = pd.DatetimeIndex([
            '2020-01-03',
            '2020-01-01',  # Out of order
            '2020-01-02',
            '2020-01-04',
            '2020-01-05'
        ])
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        # In default mode, unsorted index is a warning
        validator = DataValidator(config=ValidationConfig(timeframe='1d', strict_mode=False))
        result = validator.validate(df, asset_name='TEST')
        
        # Should have warning check for sorted index
        sorted_check = next(
            (c for c in result.checks if c.name == 'sorted_index'),
            None
        )
        assert sorted_check is not None, "Should have 'sorted_index' check"
        assert not sorted_check.passed, "sorted_index check should have failed"
        
        # In strict mode, it becomes an error
        validator_strict = DataValidator(config=ValidationConfig(timeframe='1d', strict_mode=True))
        result_strict = validator_strict.validate(df, asset_name='TEST')
        assert not result_strict.passed, "Validation should fail in strict mode for unsorted index"
    
    def test_error_messages_are_actionable(self):
        """Verify that error messages provide actionable information."""
        # Create DataFrame with multiple issues
        dates = pd.date_range('2020-01-01', periods=3, freq='D')
        df = pd.DataFrame({
            'open': [100, None, 102],  # Null value
            'high': [99, 101, 103],  # High < Low (violation)
            'low': [100, 102, 104],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, -100, 1200]  # Negative volume
        }, index=dates)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should fail
        assert not result.passed, "Validation should fail with multiple issues"
        
        # Error messages should be informative
        error_messages = [check.message for check in result.error_checks]
        
        # Check that messages contain useful information
        assert any('null' in msg.lower() for msg in error_messages), \
            "Should have error message about null values"
        assert any('ohlc' in msg.lower() or 'consistency' in msg.lower() for msg in error_messages), \
            "Should have error message about OHLC consistency"
        assert any('negative' in msg.lower() for msg in error_messages), \
            "Should have error message about negative values"
        
        # Summary should be informative
        summary = result.summary()
        assert 'FAILED' in summary, "Summary should indicate validation failed"
        assert 'TEST' in summary, "Summary should include asset name"
    
    def test_valid_data_passes_validation(self):
        """Verify that valid data passes validation (no false positives)."""
        # Create valid DataFrame
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 2000, 100).astype(int)
        }, index=dates)
        
        # Ensure OHLC consistency
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        # Validation should pass
        assert result.passed, "Validation should pass for valid data"
        assert len(result.error_checks) == 0, "Should have no error checks for valid data"
    
    def test_data_not_modified_after_validation_failure(self):
        """Verify that data is not modified even after validation fails."""
        # Create DataFrame with issues
        dates = pd.date_range('2020-01-01', periods=5, freq='D')
        original_data = {
            'open': [100, 101, None, 103, 104],
            'high': [99, 102, 103, 104, 105],  # Violation: high < low
            'low': [100, 101, 102, 103, 104],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }
        df = pd.DataFrame(original_data, index=dates)
        
        # Store original state
        original_df = df.copy()
        
        # Validate (should fail)
        validator = DataValidator(config=ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name='TEST')
        
        assert not result.passed, "Validation should fail"
        
        # Verify DataFrame is unchanged
        pd.testing.assert_frame_equal(df, original_df), \
            "DataFrame should not be modified after validation failure"
        
        # Verify specific issues still exist
        assert pd.isna(df['open'].iloc[2]), "Null value should still exist"
        assert df['high'].iloc[0] < df['low'].iloc[0], "OHLC violation should still exist"

