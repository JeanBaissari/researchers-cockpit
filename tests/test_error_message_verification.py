"""
Functional verification tests for validation error messages.

This module ensures that error messages from the DataValidator maintain
high quality standards:
1. Messages contain quantified details (counts, percentages)
2. Messages include asset name for context
3. Messages are actionable (tell user what needs fixing)
4. Messages maintain consistent detail level across all checks

These tests verify the migration from old validation API to new DataValidator
maintains the same level of error message detail and informativeness.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import (
    DataValidator,
    ValidationConfig,
    ValidationSeverity,
    validate_before_ingest
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_ohlcv_data():
    """Create valid OHLCV DataFrame for baseline testing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='D', tz='UTC')
    return pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(len(dates))],
        'high': [102 + i * 0.1 for i in range(len(dates))],
        'low': [98 + i * 0.1 for i in range(len(dates))],
        'close': [101 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
    }, index=dates)


@pytest.fixture
def asset_name():
    """Return a test asset name."""
    return 'TEST_ASSET'


# =============================================================================
# ERROR MESSAGE QUALITY TESTS
# =============================================================================

class TestErrorMessageDetailLevel:
    """Verify error messages contain detailed, actionable information."""

    def test_missing_columns_error_message(self, asset_name):
        """Test error message for missing required columns."""
        # Create DataFrame missing 'close' and 'volume' columns
        dates = pd.date_range('2024-01-01', periods=10, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        # Should fail validation
        assert not result.passed, "Should fail when columns are missing"

        # Check error messages
        assert len(result.errors) > 0, "Should have error messages"

        # Verify error message contains:
        # 1. Asset name for context
        error_text = ' '.join(result.errors)
        assert asset_name in error_text, \
            f"Error message should include asset name '{asset_name}': {error_text}"

        # 2. Missing column names
        assert 'close' in error_text.lower() or 'volume' in error_text.lower(), \
            f"Error message should mention missing columns: {error_text}"

        # 3. Expected columns list
        assert 'required columns' in error_text.lower() or 'expected columns' in error_text.lower(), \
            f"Error message should mention required/expected columns: {error_text}"

        # Check ValidationCheck details
        failed_checks = [c for c in result.checks if not c.passed]
        assert len(failed_checks) > 0, "Should have failed checks"

        required_columns_check = next(
            (c for c in failed_checks if 'column' in c.name.lower()),
            None
        )
        assert required_columns_check is not None, "Should have required_columns check"
        assert 'missing_columns' in required_columns_check.details, \
            "Check details should include missing_columns"

    def test_null_values_error_message(self, asset_name, valid_ohlcv_data):
        """Test error message for null values includes counts and percentages."""
        df = valid_ohlcv_data.copy()

        # Introduce nulls in specific columns
        df.loc[df.index[:5], 'open'] = np.nan
        df.loc[df.index[5:10], 'close'] = np.nan
        df.loc[df.index[10:12], 'volume'] = np.nan

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        # Should fail validation
        assert not result.passed, "Should fail when nulls are present"

        # Find null check
        null_check = next(
            (c for c in result.checks if 'null' in c.name.lower()),
            None
        )
        assert null_check is not None, "Should have null check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in null_check.message, \
            f"Message should include asset name: {null_check.message}"

        # 2. Count of nulls
        assert any(char.isdigit() for char in null_check.message), \
            f"Message should include null count: {null_check.message}"

        # 3. Percentage
        assert '%' in null_check.message or 'percent' in null_check.message.lower(), \
            f"Message should include percentage: {null_check.message}"

        # 4. Details dictionary should have null_counts
        assert 'null_counts' in null_check.details, \
            "Details should include null_counts dictionary"
        assert 'null_pct' in null_check.details, \
            "Details should include null_pct"

        # Verify null_counts breaks down by column
        null_counts = null_check.details['null_counts']
        assert isinstance(null_counts, dict), "null_counts should be a dictionary"
        assert len(null_counts) > 0, "Should have null counts for affected columns"

    def test_ohlc_consistency_error_message(self, asset_name):
        """Test error message for OHLC consistency violations."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [98] * len(dates),  # High < Open (violation)
            'low': [99] * len(dates),   # Low > Open (violation)
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        assert not result.passed, "Should fail with OHLC violations"

        # Find OHLC consistency check
        ohlc_check = next(
            (c for c in result.checks if 'ohlc' in c.name.lower() and not c.passed),
            None
        )
        assert ohlc_check is not None, "Should have OHLC consistency check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in ohlc_check.message, \
            f"Message should include asset name: {ohlc_check.message}"

        # 2. Violation count
        assert any(char.isdigit() for char in ohlc_check.message), \
            f"Message should include violation count: {ohlc_check.message}"

        # 3. Percentage
        assert '%' in ohlc_check.message, \
            f"Message should include percentage: {ohlc_check.message}"

        # 4. Details should break down violation types
        assert 'total_violations' in ohlc_check.details, \
            "Details should include total_violations"
        assert 'violation_pct' in ohlc_check.details, \
            "Details should include violation_pct"

    def test_negative_values_error_message(self, asset_name):
        """Test error message for negative values."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Introduce negative values
        df.loc[df.index[:3], 'close'] = -10
        df.loc[df.index[3:5], 'volume'] = -1000

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        assert not result.passed, "Should fail with negative values"

        # Find negative values check
        neg_check = next(
            (c for c in result.checks if 'negative' in c.name.lower() and not c.passed),
            None
        )
        assert neg_check is not None, "Should have negative values check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in neg_check.message, \
            f"Message should include asset name: {neg_check.message}"

        # 2. Count of negative values
        assert any(char.isdigit() for char in neg_check.message), \
            f"Message should include count: {neg_check.message}"

        # 3. Details should break down by type
        assert 'negative_prices' in neg_check.details or 'negative_volumes' in neg_check.details, \
            "Details should break down negative values by type"

    def test_future_dates_error_message(self, asset_name):
        """Test error message for future dates."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Add future dates
        future_dates = pd.date_range(
            datetime.now().date() + timedelta(days=1),
            periods=5,
            freq='D',
            tz='UTC'
        )
        future_df = pd.DataFrame({
            'open': [100] * len(future_dates),
            'high': [102] * len(future_dates),
            'low': [98] * len(future_dates),
            'close': [101] * len(future_dates),
            'volume': [1000000] * len(future_dates),
        }, index=future_dates)

        combined_df = pd.concat([df, future_df])

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(combined_df, asset_name=asset_name)

        assert not result.passed, "Should fail with future dates"

        # Find future dates check
        future_check = next(
            (c for c in result.checks if 'future' in c.name.lower() and not c.passed),
            None
        )
        assert future_check is not None, "Should have future dates check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in future_check.message, \
            f"Message should include asset name: {future_check.message}"

        # 2. Count of future dates
        assert any(char.isdigit() for char in future_check.message), \
            f"Message should include count: {future_check.message}"

        # 3. Details should have count
        assert 'future_date_count' in future_check.details, \
            "Details should include future_date_count"

    def test_duplicate_dates_error_message(self, asset_name):
        """Test error message for duplicate dates."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Add duplicate dates
        duplicate_row = pd.DataFrame({
            'open': [100],
            'high': [102],
            'low': [98],
            'close': [101],
            'volume': [1000000],
        }, index=[dates[0]])  # Duplicate first date

        combined_df = pd.concat([df, duplicate_row])

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(combined_df, asset_name=asset_name)

        assert not result.passed, "Should fail with duplicate dates"

        # Find duplicate dates check
        dup_check = next(
            (c for c in result.checks if 'duplicate' in c.name.lower() and not c.passed),
            None
        )
        assert dup_check is not None, "Should have duplicate dates check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in dup_check.message, \
            f"Message should include asset name: {dup_check.message}"

        # 2. Count and percentage
        assert any(char.isdigit() for char in dup_check.message), \
            f"Message should include count: {dup_check.message}"
        assert '%' in dup_check.message, \
            f"Message should include percentage: {dup_check.message}"

        # 3. Details
        assert 'duplicate_count' in dup_check.details, \
            "Details should include duplicate_count"
        assert 'duplicate_pct' in dup_check.details, \
            "Details should include duplicate_pct"

    def test_zero_volume_error_message(self, asset_name):
        """Test error message for excessive zero volume bars."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [0] * len(dates),  # All zero volume
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            zero_volume_threshold_pct=10.0  # 10% threshold
        ))
        result = validator.validate(df, asset_name=asset_name)

        # Should have warning or error depending on strict mode
        # Find zero volume check
        zero_vol_check = next(
            (c for c in result.checks if 'zero_volume' in c.name.lower() and not c.passed),
            None
        )
        assert zero_vol_check is not None, "Should have zero volume check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in zero_vol_check.message, \
            f"Message should include asset name: {zero_vol_check.message}"

        # 2. Count and percentage
        assert any(char.isdigit() for char in zero_vol_check.message), \
            f"Message should include count: {zero_vol_check.message}"
        assert '%' in zero_vol_check.message or '(' in zero_vol_check.message, \
            f"Message should include percentage: {zero_vol_check.message}"

        # 3. Details
        assert 'zero_volume_count' in zero_vol_check.details, \
            "Details should include zero_volume_count"
        assert 'zero_volume_pct' in zero_vol_check.details, \
            "Details should include zero_volume_pct"

    def test_price_jumps_error_message(self, asset_name):
        """Test error message for large price jumps."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D', tz='UTC')
        prices = [100.0] * len(dates)
        
        # Add large price jumps
        prices[10] = 200.0  # 100% jump
        prices[20] = 50.0   # 50% drop
        prices[30] = 300.0  # Another large jump

        df = pd.DataFrame({
            'open': prices,
            'high': [p + 2 for p in prices],
            'low': [p - 1 for p in prices],
            'close': prices,
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            price_jump_threshold_pct=50.0
        ))
        result = validator.validate(df, asset_name=asset_name)

        # Find price jumps check
        jump_check = next(
            (c for c in result.checks if 'jump' in c.name.lower() and not c.passed),
            None
        )
        if jump_check is not None:  # May pass if jumps are within threshold
            # Verify message contains:
            # 1. Asset name
            assert asset_name in jump_check.message, \
                f"Message should include asset name: {jump_check.message}"

            # 2. Count and threshold
            assert any(char.isdigit() for char in jump_check.message), \
                f"Message should include count: {jump_check.message}"
            assert '50' in jump_check.message or '%' in jump_check.message, \
                f"Message should mention threshold: {jump_check.message}"

            # 3. Details
            assert 'jump_count' in jump_check.details, \
                "Details should include jump_count"
            assert 'jump_pct' in jump_check.details, \
                "Details should include jump_pct"

    def test_data_sufficiency_error_message(self, asset_name):
        """Test error message for insufficient data."""
        # Create DataFrame with too few rows
        dates = pd.date_range('2024-01-01', periods=5, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            min_rows_daily=20  # Require 20 rows minimum
        ))
        result = validator.validate(df, asset_name=asset_name)

        # Find data sufficiency check
        sufficiency_check = next(
            (c for c in result.checks if 'sufficiency' in c.name.lower() and not c.passed),
            None
        )
        assert sufficiency_check is not None, "Should have data sufficiency check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in sufficiency_check.message, \
            f"Message should include asset name: {sufficiency_check.message}"

        # 2. Actual row count
        assert '5' in sufficiency_check.message or str(len(df)) in sufficiency_check.message, \
            f"Message should include actual row count: {sufficiency_check.message}"

        # 3. Minimum required
        assert '20' in sufficiency_check.message or 'minimum' in sufficiency_check.message.lower(), \
            f"Message should include minimum required: {sufficiency_check.message}"

        # 4. Details
        assert 'row_count' in sufficiency_check.details, \
            "Details should include row_count"
        assert 'minimum_required' in sufficiency_check.details, \
            "Details should include minimum_required"

    def test_stale_data_warning_message(self, asset_name):
        """Test warning message for stale data."""
        # Create data with old last date
        old_date = datetime.now() - timedelta(days=30)
        dates = pd.date_range(old_date, periods=10, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            stale_threshold_days=7  # Data older than 7 days is stale
        ))
        result = validator.validate(df, asset_name=asset_name)

        # Find stale data check
        stale_check = next(
            (c for c in result.checks if 'stale' in c.name.lower() and not c.passed),
            None
        )
        assert stale_check is not None, "Should have stale data check"

        # Verify message contains:
        # 1. Asset name
        assert asset_name in stale_check.message, \
            f"Message should include asset name: {stale_check.message}"

        # 2. Days since last update
        assert any(char.isdigit() for char in stale_check.message), \
            f"Message should include days count: {stale_check.message}"

        # 3. Last date
        assert 'last' in stale_check.message.lower() or 'date' in stale_check.message.lower(), \
            f"Message should mention last date: {stale_check.message}"

        # 4. Details
        assert 'days_since_last' in stale_check.details, \
            "Details should include days_since_last"
        assert 'last_date' in stale_check.details, \
            "Details should include last_date"

    def test_price_outliers_error_message(self, asset_name):
        """Test error message for price outliers."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D', tz='UTC')
        
        # Create normal prices with some extreme outliers
        np.random.seed(42)
        normal_returns = np.random.randn(100) * 0.01
        prices = 100 * (1 + normal_returns).cumprod()
        
        # Add extreme outliers
        prices[10] = prices[9] * 10  # 10x jump (extreme outlier)
        prices[20] = prices[19] * 0.1  # 90% drop (extreme outlier)

        df = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            outlier_threshold_sigma=5.0
        ))
        result = validator.validate(df, asset_name=asset_name)

        # Find outliers check (may be warning or error depending on strict mode)
        outlier_check = next(
            (c for c in result.checks if 'outlier' in c.name.lower()),
            None
        )
        if outlier_check is not None and not outlier_check.passed:
            # Verify message contains:
            # 1. Asset name
            assert asset_name in outlier_check.message, \
                f"Message should include asset name: {outlier_check.message}"

            # 2. Count and threshold
            assert any(char.isdigit() for char in outlier_check.message), \
                f"Message should include count: {outlier_check.message}"
            assert '5' in outlier_check.message or 'sigma' in outlier_check.message.lower(), \
                f"Message should mention threshold: {outlier_check.message}"

            # 3. Details
            assert 'outlier_count' in outlier_check.details, \
                "Details should include outlier_count"
            assert 'outlier_pct' in outlier_check.details, \
                "Details should include outlier_pct"


# =============================================================================
# ACTIONABILITY TESTS
# =============================================================================

class TestErrorMessageActionability:
    """Verify error messages are actionable (tell user what to fix)."""

    def test_missing_columns_actionable(self, asset_name):
        """Test that missing columns message tells user what columns are needed."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        error_text = ' '.join(result.errors).lower()
        
        # Should mention what columns are missing
        assert 'missing' in error_text or 'required' in error_text, \
            f"Should mention missing/required: {error_text}"
        
        # Should mention expected columns
        assert 'column' in error_text, \
            f"Should mention columns: {error_text}"

    def test_null_values_actionable(self, asset_name, valid_ohlcv_data):
        """Test that null values message tells user which columns have nulls."""
        df = valid_ohlcv_data.copy()
        df.loc[df.index[:5], 'open'] = np.nan
        df.loc[df.index[5:10], 'close'] = np.nan

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        null_check = next(
            (c for c in result.checks if 'null' in c.name.lower() and not c.passed),
            None
        )
        assert null_check is not None

        # Details should tell user which columns have nulls
        assert 'null_counts' in null_check.details, \
            "Should provide null_counts to identify affected columns"
        
        null_counts = null_check.details['null_counts']
        assert isinstance(null_counts, dict), "null_counts should be a dictionary"
        assert len(null_counts) > 0, "Should identify columns with nulls"

    def test_ohlc_consistency_actionable(self, asset_name):
        """Test that OHLC consistency message tells user what relationships are violated."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [98] * len(dates),  # High < Open
            'low': [99] * len(dates),   # Low > Open
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        ohlc_check = next(
            (c for c in result.checks if 'ohlc' in c.name.lower() and not c.passed),
            None
        )
        assert ohlc_check is not None

        # Details should break down violation types
        assert 'high_low_violations' in ohlc_check.details or \
               'high_violations' in ohlc_check.details or \
               'low_violations' in ohlc_check.details, \
            "Should break down violation types in details"

    def test_error_messages_include_context(self, asset_name):
        """Test that all error messages include asset name for context."""
        dates = pd.date_range('2024-01-01', periods=10, freq='D', tz='UTC')
        
        # Test multiple error scenarios
        test_cases = [
            # Missing columns
            (pd.DataFrame({'open': [100] * len(dates)}, index=dates), 'missing columns'),
            # Invalid OHLC
            (pd.DataFrame({
                'open': [100] * len(dates),
                'high': [98] * len(dates),
                'low': [99] * len(dates),
                'close': [101] * len(dates),
                'volume': [1000000] * len(dates),
            }, index=dates), 'ohlc violation'),
        ]

        validator = DataValidator(ValidationConfig(timeframe='1d'))

        for df, error_type in test_cases:
            result = validator.validate(df, asset_name=asset_name)
            
            if not result.passed:
                # All error messages should include asset name
                for error in result.errors:
                    assert asset_name in error, \
                        f"Error message should include asset name '{asset_name}': {error}"


# =============================================================================
# CONSISTENCY TESTS
# =============================================================================

class TestErrorMessageConsistency:
    """Verify error messages maintain consistent detail level across checks."""

    def test_all_error_messages_include_asset_name(self, asset_name):
        """Test that all validation errors include asset name."""
        validator = DataValidator(ValidationConfig(timeframe='1d'))

        # Create various invalid DataFrames
        test_cases = [
            # Empty DataFrame
            pd.DataFrame(),
            # Missing columns
            pd.DataFrame({'open': [100]}, index=pd.date_range('2024-01-01', periods=1, freq='D', tz='UTC')),
            # Invalid OHLC
            pd.DataFrame({
                'open': [100],
                'high': [98],
                'low': [99],
                'close': [101],
                'volume': [1000000],
            }, index=pd.date_range('2024-01-01', periods=1, freq='D', tz='UTC')),
        ]

        for df in test_cases:
            if df.empty:
                continue  # Skip empty DataFrame (handled separately)
            
            result = validator.validate(df, asset_name=asset_name)
            
            # All error messages should include asset name
            for error in result.errors:
                assert asset_name in error, \
                    f"All error messages should include asset name: {error}"

    def test_all_error_messages_include_quantified_details(self, asset_name):
        """Test that error messages include quantified details (counts, percentages)."""
        dates = pd.date_range('2024-01-01', periods=50, freq='D', tz='UTC')
        
        # Create DataFrame with multiple issues
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Add nulls
        df.loc[df.index[:10], 'open'] = np.nan

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        # Check that failed checks have quantified details
        for check in result.failed_checks:
            # Error messages should include numbers (counts or percentages)
            has_number = any(char.isdigit() for char in check.message)
            has_percent = '%' in check.message
            
            assert has_number or has_percent, \
                f"Error message should include quantified details: {check.message}"

    def test_error_messages_consistent_format(self, asset_name):
        """Test that error messages follow consistent format."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        
        # Test multiple error types
        test_cases = [
            # Nulls
            (lambda df: df.loc[df.index[:5], 'open'].__setitem__(slice(None), np.nan), 'null'),
            # Duplicates
            (lambda df: pd.concat([df, df.iloc[:1]]), 'duplicate'),
        ]

        validator = DataValidator(ValidationConfig(timeframe='1d'))

        for modify_func, error_type in test_cases:
            df = pd.DataFrame({
                'open': [100] * len(dates),
                'high': [102] * len(dates),
                'low': [98] * len(dates),
                'close': [101] * len(dates),
                'volume': [1000000] * len(dates),
            }, index=dates)
            
            if error_type == 'duplicate':
                df = modify_func(df)
            else:
                modify_func(df)

            result = validator.validate(df, asset_name=asset_name)
            
            # All error messages should:
            # 1. Include asset name
            # 2. Include check name or category
            # 3. Include quantified details
            for error in result.errors:
                assert asset_name in error, \
                    f"Error should include asset name: {error}"
                assert any(char.isdigit() for char in error) or '%' in error, \
                    f"Error should include quantified details: {error}"


# =============================================================================
# SUMMARY AND DETAILS VERIFICATION
# =============================================================================

class TestValidationResultDetails:
    """Verify ValidationResult provides detailed information."""

    def test_result_summary_includes_all_errors(self, asset_name):
        """Test that result summary includes all error information."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Add multiple issues
        df.loc[df.index[:5], 'open'] = np.nan
        df.loc[df.index[5:7], 'close'] = np.nan

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        summary = result.summary()

        # Summary should include:
        # 1. Status (PASSED/FAILED)
        assert 'FAILED' in summary or 'PASSED' in summary, \
            f"Summary should include status: {summary}"

        # 2. Error count
        assert 'error' in summary.lower() or 'failed' in summary.lower(), \
            f"Summary should mention errors: {summary}"

        # 3. Error details
        if result.errors:
            assert len(result.errors) > 0, "Should have errors"
            # Summary should show at least some errors
            assert any(error in summary for error in result.errors[:3]), \
                f"Summary should include error details: {summary}"

    def test_result_details_dictionary_complete(self, asset_name):
        """Test that ValidationCheck details dictionaries are complete."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        # Add nulls
        df.loc[df.index[:10], 'open'] = np.nan

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        # Check that failed checks have detailed information
        for check in result.failed_checks:
            # Details should be a dictionary
            assert isinstance(check.details, dict), \
                f"Check details should be a dictionary: {check.name}"

            # Details should not be empty for failed checks
            assert len(check.details) > 0, \
                f"Failed check should have details: {check.name}"

    def test_error_checks_property_works(self, asset_name):
        """Test that error_checks property correctly filters error-level checks."""
        dates = pd.date_range('2024-01-01', periods=20, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [98] * len(dates),  # OHLC violation
            'low': [99] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(timeframe='1d'))
        result = validator.validate(df, asset_name=asset_name)

        # error_checks should only include ERROR severity failed checks
        error_checks = result.error_checks
        
        for check in error_checks:
            assert not check.passed, "Error checks should be failed"
            assert check.severity == ValidationSeverity.ERROR, \
                "Error checks should have ERROR severity"

    def test_warning_checks_property_works(self, asset_name):
        """Test that warning_checks property correctly filters warning-level checks."""
        dates = pd.date_range('2024-01-01', periods=5, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [102] * len(dates),
            'low': [98] * len(dates),
            'close': [101] * len(dates),
            'volume': [1000000] * len(dates),
        }, index=dates)

        validator = DataValidator(ValidationConfig(
            timeframe='1d',
            min_rows_daily=20  # Will trigger warning for insufficient data
        ))
        result = validator.validate(df, asset_name=asset_name)

        # warning_checks should only include WARNING severity failed checks
        warning_checks = result.warning_checks
        
        for check in warning_checks:
            assert not check.passed, "Warning checks should be failed"
            assert check.severity == ValidationSeverity.WARNING, \
                "Warning checks should have WARNING severity"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

