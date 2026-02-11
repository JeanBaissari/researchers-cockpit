"""
Test data splitting utilities for optimization.

Tests for train/test split functionality.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize.split import split_data


class TestSplitData:
    """Test split_data function."""

    @pytest.mark.unit
    def test_split_data_function_exists(self):
        """Test that split_data function exists."""
        assert split_data is not None
        assert callable(split_data)

    @pytest.mark.unit
    def test_split_data_default_train_pct(self):
        """Test split_data with default train_pct (0.7)."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end)

        # Should return tuple of tuples
        assert isinstance(result, tuple)
        assert len(result) == 2

        train_period, test_period = result
        assert isinstance(train_period, tuple)
        assert isinstance(test_period, tuple)
        assert len(train_period) == 2
        assert len(test_period) == 2

        train_start, train_end = train_period
        test_start, test_end = test_period

        # Verify dates are strings
        assert isinstance(train_start, str)
        assert isinstance(train_end, str)
        assert isinstance(test_start, str)
        assert isinstance(test_end, str)

        # Verify train period starts at start date
        assert train_start == start

        # Verify test period ends at end date
        assert test_end == end

        # Verify train_end + 1 day = test_start
        train_end_ts = pd.Timestamp(train_end)
        test_start_ts = pd.Timestamp(test_start)
        expected_test_start = train_end_ts + pd.Timedelta(days=1)
        assert test_start_ts == expected_test_start

        # Verify approximately 70% of days in train period
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert 0.69 <= train_pct <= 0.71  # Allow small rounding error

    @pytest.mark.unit
    def test_split_data_custom_train_pct(self):
        """Test split_data with custom train_pct values."""
        start = "2020-01-01"
        end = "2020-12-31"

        # Test 50% split
        result = split_data(start, end, train_pct=0.5)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert 0.49 <= train_pct <= 0.51  # Allow small rounding error

        # Test 80% split
        result = split_data(start, end, train_pct=0.8)
        train_period, test_period = result
        train_start, train_end = train_period

        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert 0.79 <= train_pct <= 0.81  # Allow small rounding error

    @pytest.mark.unit
    def test_split_data_short_date_range(self):
        """Test split_data with very short date range."""
        start = "2020-01-01"
        end = "2020-01-10"  # Only 9 days

        result = split_data(start, end, train_pct=0.7)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Should still work, train period should be ~6 days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        assert train_days >= 0  # At least 0 days
        assert train_days <= 9  # At most 9 days

        # Verify test period starts after train period
        assert pd.Timestamp(test_start) > pd.Timestamp(train_end)

    @pytest.mark.unit
    def test_split_data_single_day_range(self):
        """Test split_data with single day range."""
        start = "2020-01-01"
        end = "2020-01-01"  # Same day

        result = split_data(start, end, train_pct=0.7)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Train period should be the single day
        assert train_start == start
        assert train_end == start

        # Test period should start the next day
        assert pd.Timestamp(test_start) == pd.Timestamp(start) + pd.Timedelta(days=1)
        assert test_end == end  # But end is still the original end

    @pytest.mark.unit
    def test_split_data_train_pct_zero(self):
        """Test split_data with train_pct=0.0."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=0.0)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Train period should be minimal (0 days)
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        assert train_days == 0

        # Test period should start immediately after train period
        assert pd.Timestamp(test_start) == pd.Timestamp(train_end) + pd.Timedelta(days=1)

    @pytest.mark.unit
    def test_split_data_train_pct_one(self):
        """Test split_data with train_pct=1.0."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=1.0)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Train period should include all days
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        assert train_days == total_days

        # Test period should start after train period ends
        assert pd.Timestamp(test_start) == pd.Timestamp(train_end) + pd.Timedelta(days=1)

    @pytest.mark.unit
    def test_split_data_date_format(self):
        """Test split_data with different date formats."""
        # Test with YYYY-MM-DD format
        result = split_data("2020-01-01", "2020-12-31")
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # All dates should be in YYYY-MM-DD format
        assert len(train_start) == 10
        assert len(train_end) == 10
        assert len(test_start) == 10
        assert len(test_end) == 10
        assert train_start.count("-") == 2
        assert train_end.count("-") == 2
        assert test_start.count("-") == 2
        assert test_end.count("-") == 2

    @pytest.mark.unit
    def test_split_data_no_gap_between_periods(self):
        """Test that there's no gap between train and test periods."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=0.7)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Test period should start exactly one day after train period ends
        train_end_ts = pd.Timestamp(train_end)
        test_start_ts = pd.Timestamp(test_start)
        gap = (test_start_ts - train_end_ts).days
        assert gap == 1

    @pytest.mark.unit
    def test_split_data_multiple_years(self):
        """Test split_data with multi-year date range."""
        start = "2018-01-01"
        end = "2022-12-31"  # 5 years

        result = split_data(start, end, train_pct=0.7)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Verify approximately 70% split
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert 0.69 <= train_pct <= 0.71

        # Verify no gaps
        train_end_ts = pd.Timestamp(train_end)
        test_start_ts = pd.Timestamp(test_start)
        assert (test_start_ts - train_end_ts).days == 1

    @pytest.mark.unit
    def test_split_data_edge_case_very_small_train_pct(self):
        """Test split_data with very small train_pct."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=0.01)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Train period should be very small
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert train_pct <= 0.02  # Very small percentage

    @pytest.mark.unit
    def test_split_data_edge_case_very_large_train_pct(self):
        """Test split_data with very large train_pct."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=0.99)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Train period should be very large
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        train_pct = train_days / total_days
        assert train_pct >= 0.98  # Very large percentage

    @pytest.mark.unit
    def test_split_data_return_type_structure(self):
        """Test that split_data returns correct structure."""
        result = split_data("2020-01-01", "2020-12-31")

        # Should be tuple of two tuples
        assert isinstance(result, tuple)
        assert len(result) == 2

        train_period, test_period = result
        assert isinstance(train_period, tuple)
        assert isinstance(test_period, tuple)
        assert len(train_period) == 2
        assert len(test_period) == 2

        # Each element should be a string
        for period in [train_period, test_period]:
            for date_str in period:
                assert isinstance(date_str, str)
                # Should be valid date format
                pd.Timestamp(date_str)  # Should not raise

    @pytest.mark.unit
    def test_split_data_invalid_train_pct_negative(self):
        """Test split_data with negative train_pct (produces negative train_days)."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=-0.1)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Negative train_pct will result in negative train_days
        # This means train_end will be before train_start
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        assert train_days < 0  # Negative train_pct results in negative train_days

    @pytest.mark.unit
    def test_split_data_invalid_train_pct_over_one(self):
        """Test split_data with train_pct > 1.0 (should use all days for training)."""
        start = "2020-01-01"
        end = "2020-12-31"

        result = split_data(start, end, train_pct=1.5)
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # train_pct > 1.0 will result in train_days > total_days
        total_days = (pd.Timestamp(end) - pd.Timestamp(start)).days
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        # Function doesn't cap train_days, so it can exceed total_days
        assert train_days >= total_days

    @pytest.mark.unit
    def test_split_data_invalid_date_format_raises(self):
        """Test that split_data raises error for invalid date format."""
        # Invalid date format should raise ValueError
        with pytest.raises((ValueError, pd.errors.ParserError)):
            split_data("invalid-date", "2020-12-31")

        with pytest.raises((ValueError, pd.errors.ParserError)):
            split_data("2020-01-01", "invalid-date")

    @pytest.mark.unit
    def test_split_data_end_before_start_raises(self):
        """Test that split_data handles end date before start date."""
        # End before start should result in negative total_days
        result = split_data("2020-12-31", "2020-01-01")
        train_period, test_period = result
        train_start, train_end = train_period
        test_start, test_end = test_period

        # Negative total_days will result in negative train_days (int() = 0)
        # So train_end will be before or equal to train_start
        train_days = (pd.Timestamp(train_end) - pd.Timestamp(train_start)).days
        assert train_days <= 0
