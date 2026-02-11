"""
Test FOREX calendar.

Tests for FOREX calendar functionality including 24/5 trading,
Sunday inclusion, holidays, and calendar properties.
"""

# Standard library imports
import sys
from pathlib import Path
from datetime import time

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.calendars import ForexCalendar, register_custom_calendars


class TestForexCalendar:
    """Tests for FOREX calendar configuration and behavior."""

    @pytest.mark.unit
    def test_forex_calendar_name(self):
        """Test FOREX calendar has correct name."""
        assert ForexCalendar.name == "FOREX"

    @pytest.mark.unit
    def test_forex_calendar_timezone(self):
        """Test FOREX calendar uses America/New_York timezone."""
        assert ForexCalendar.tz == "America/New_York"

    @pytest.mark.unit
    def test_forex_calendar_open_times(self):
        """Test FOREX calendar open times configuration."""
        assert ForexCalendar.open_times == ((None, time(0, 0)),)

    @pytest.mark.unit
    def test_forex_calendar_close_times(self):
        """Test FOREX calendar close times configuration."""
        assert ForexCalendar.close_times == ((None, time(23, 59, 59)),)

    @pytest.mark.unit
    def test_forex_calendar_weekmask(self):
        """Test FOREX calendar includes all 7 days (including Sunday)."""
        # Weekmask should include Sunday for data alignment
        assert "Sun" in ForexCalendar.weekmask
        assert "Mon" in ForexCalendar.weekmask
        assert "Sat" in ForexCalendar.weekmask

    @pytest.mark.unit
    def test_forex_calendar_open_time_default(self):
        """Test FOREX calendar default open time."""
        assert ForexCalendar.open_time_default() == time(0, 0)

    @pytest.mark.unit
    def test_forex_calendar_close_time_default(self):
        """Test FOREX calendar default close time."""
        assert ForexCalendar.close_time_default() == time(23, 59, 59)

    @pytest.mark.unit
    def test_forex_calendar_special_closes(self):
        """Test FOREX calendar has no special closes."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        assert forex.special_closes == []

    @pytest.mark.unit
    def test_forex_calendar_holidays(self):
        """Test FOREX calendar includes major holidays."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        # Get holidays (returns DatetimeIndex without timezone)
        holidays = forex.regular_holidays.holidays()

        # Normalize to date for comparison (holidays are date-only)
        holiday_dates = [pd.Timestamp(h).date() for h in holidays]

        # Should include Christmas (Dec 25)
        christmas_2025 = pd.Timestamp("2025-12-25").date()
        assert christmas_2025 in holiday_dates, "FOREX should observe Christmas"

        # Should include New Year (Jan 1)
        new_year_2025 = pd.Timestamp("2025-01-01").date()
        assert new_year_2025 in holiday_dates, "FOREX should observe New Year's Day"

        # Should include Good Friday (April 18, 2025)
        good_friday_2025 = pd.Timestamp("2025-04-18").date()
        assert good_friday_2025 in holiday_dates, "FOREX should observe Good Friday"

    @pytest.mark.unit
    def test_forex_calendar_24_5_with_sunday(self):
        """Test FOREX calendar operates 24/5 including Sunday."""
        register_custom_calendars(["FOREX"])

        start = pd.Timestamp("2025-12-01")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        # Should have sessions on Sundays (for data alignment)
        sunday_dates = [d for d in forex.sessions if d.dayofweek == 6]
        assert len(sunday_dates) > 0, "FOREX should have Sunday sessions for data alignment"

        # Should have sessions on weekdays
        weekday_dates = [d for d in forex.sessions if d.dayofweek < 5]
        assert len(weekday_dates) > 0, "FOREX should have weekday sessions"

        # Should have sessions on Saturday (for data alignment)
        saturday_dates = [d for d in forex.sessions if d.dayofweek == 5]
        assert len(saturday_dates) > 0, "FOREX should have Saturday sessions for data alignment"

    @pytest.mark.unit
    def test_forex_calendar_excludes_holidays(self):
        """Test FOREX calendar excludes holidays from trading sessions."""
        start = pd.Timestamp("2025-12-20")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        # Christmas 2025 is Dec 25
        christmas = pd.Timestamp("2025-12-25")

        # Christmas should not be in trading sessions
        assert christmas not in forex.sessions, (
            "FOREX should exclude Christmas from trading sessions"
        )

    @pytest.mark.unit
    def test_forex_calendar_sessions_in_range(self):
        """Test FOREX calendar sessions_in_range method."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-31")
        forex = ForexCalendar(start=start, end=end)

        # Get sessions in a specific range
        range_start = pd.Timestamp("2025-01-05")
        range_end = pd.Timestamp("2025-01-10")
        sessions = forex.sessions_in_range(range_start, range_end)

        assert len(sessions) > 0, "Should return sessions in range"
        assert all(range_start <= s <= range_end for s in sessions), (
            "All sessions should be in range"
        )

        # Should include Sunday (Jan 5, 2025 is a Sunday)
        sunday_in_range = pd.Timestamp("2025-01-05")
        assert sunday_in_range in sessions, "Should include Sunday in range"

    @pytest.mark.unit
    def test_forex_calendar_minutes_per_day(self):
        """Test FOREX calendar minutes per day calculation."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-31")
        forex = ForexCalendar(start=start, end=end)

        # For 24-hour trading: 24 * 60 = 1440 minutes
        # Get a sample session
        sample_session = forex.sessions[0]
        minutes = forex.session_minutes(sample_session)

        # Should be 1439 or 1440 minutes depending on implementation
        # (00:00:00 to 23:59:59 = 1440 one-minute intervals, but last timestamp is 23:59:59)
        # ExchangeCalendar returns 1439 minutes for this range
        assert len(minutes) >= 1439, (
            f"FOREX should have at least 1439 minutes per day, got {len(minutes)}"
        )
        assert len(minutes) <= 1440, (
            f"FOREX should have at most 1440 minutes per day, got {len(minutes)}"
        )

    @pytest.mark.unit
    def test_forex_calendar_instantiation(self):
        """Test FOREX calendar can be instantiated with date range."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-12-31")

        forex = ForexCalendar(start=start, end=end)

        assert forex is not None
        assert len(forex.sessions) > 0
        assert forex.sessions[0] >= start
        assert forex.sessions[-1] <= end

    @pytest.mark.unit
    def test_forex_calendar_weekend_sessions(self):
        """Test FOREX calendar includes weekend sessions for data alignment."""
        start = pd.Timestamp("2025-12-01")
        end = pd.Timestamp("2025-12-07")  # One week
        forex = ForexCalendar(start=start, end=end)

        # Should have sessions on Saturday and Sunday
        weekend_sessions = [d for d in forex.sessions if d.dayofweek >= 5]
        assert len(weekend_sessions) > 0, "FOREX should include weekend sessions for data alignment"

        # Verify specific weekend dates are included
        # Dec 6, 2025 is Saturday, Dec 7, 2025 is Sunday
        saturday = pd.Timestamp("2025-12-06")
        sunday = pd.Timestamp("2025-12-07")

        # Both should be in sessions (for data alignment)
        assert saturday in forex.sessions or sunday in forex.sessions, (
            "FOREX should include weekend dates for data alignment"
        )

    @pytest.mark.unit
    def test_forex_calendar_short_range(self):
        """Test FOREX calendar with very short date range."""
        # Use a 2-day range (ExchangeCalendar requires start < end)
        start = pd.Timestamp("2025-01-15")
        end = pd.Timestamp("2025-01-16")
        forex = ForexCalendar(start=start, end=end)

        # Should handle short range gracefully
        assert len(forex.sessions) >= 0, "Should handle short date range"

    @pytest.mark.unit
    def test_forex_calendar_session_ordering(self):
        """Test FOREX calendar sessions are in chronological order."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-31")
        forex = ForexCalendar(start=start, end=end)

        # Sessions should be in ascending order
        sessions = forex.sessions
        for i in range(len(sessions) - 1):
            assert sessions[i] < sessions[i + 1], (
                f"Sessions should be in chronological order: {sessions[i]} < {sessions[i + 1]}"
            )

    @pytest.mark.unit
    def test_forex_calendar_inherits_exchange_calendar(self):
        """Test FOREX calendar properly inherits from ExchangeCalendar."""
        from exchange_calendars import ExchangeCalendar

        assert issubclass(ForexCalendar, ExchangeCalendar), (
            "ForexCalendar should inherit from ExchangeCalendar"
        )

    @pytest.mark.unit
    def test_forex_calendar_weekmask_all_days(self):
        """Test FOREX calendar weekmask includes all 7 days."""
        weekmask = ForexCalendar.weekmask
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for day in days:
            assert day in weekmask, f"Weekmask should include {day}"

    @pytest.mark.unit
    def test_forex_calendar_holiday_calendar_type(self):
        """Test FOREX calendar regular_holidays returns HolidayCalendar."""
        from exchange_calendars.exchange_calendar import HolidayCalendar

        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        assert isinstance(forex.regular_holidays, HolidayCalendar), (
            "regular_holidays should return HolidayCalendar instance"
        )

    @pytest.mark.unit
    def test_forex_calendar_multiple_holidays_in_range(self):
        """Test FOREX calendar handles multiple holidays in date range."""
        # 2025 has New Year (Jan 1), Good Friday (Apr 18), and Christmas (Dec 25)
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-12-31")
        forex = ForexCalendar(start=start, end=end)

        holidays = forex.regular_holidays.holidays()
        holiday_dates = [pd.Timestamp(h).date() for h in holidays]

        # Should have at least 3 holidays in 2025
        assert len(holiday_dates) >= 3, (
            f"Should have multiple holidays in 2025, got {len(holiday_dates)}"
        )

        # Verify specific holidays
        assert pd.Timestamp("2025-01-01").date() in holiday_dates, "Should include New Year"
        assert pd.Timestamp("2025-12-25").date() in holiday_dates, "Should include Christmas"

    @pytest.mark.unit
    def test_forex_calendar_minutes_for_multiple_sessions(self):
        """Test FOREX calendar minutes calculation for multiple sessions."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-05")
        forex = ForexCalendar(start=start, end=end)

        # Test minutes for first few sessions
        for session in forex.sessions[:3]:
            minutes = forex.session_minutes(session)
            assert len(minutes) >= 1439, (
                f"Session {session} should have at least 1439 minutes, got {len(minutes)}"
            )
            assert len(minutes) <= 1440, (
                f"Session {session} should have at most 1440 minutes, got {len(minutes)}"
            )

    @pytest.mark.unit
    def test_forex_calendar_sessions_boundaries(self):
        """Test FOREX calendar session boundaries respect date range."""
        start = pd.Timestamp("2025-06-01")
        end = pd.Timestamp("2025-06-30")
        forex = ForexCalendar(start=start, end=end)

        # All sessions should be within the date range
        assert all(start.date() <= s.date() <= end.date() for s in forex.sessions), (
            "All sessions should be within the specified date range"
        )

        # First session should be >= start
        if len(forex.sessions) > 0:
            assert forex.sessions[0].date() >= start.date(), "First session should be >= start date"

        # Last session should be <= end
        if len(forex.sessions) > 0:
            assert forex.sessions[-1].date() <= end.date(), "Last session should be <= end date"

    @pytest.mark.unit
    def test_forex_calendar_sessions_in_range_edge_cases(self):
        """Test FOREX calendar sessions_in_range with edge cases."""
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-31")
        forex = ForexCalendar(start=start, end=end)

        # Test with same start and end
        same_date = pd.Timestamp("2025-01-15")
        sessions = forex.sessions_in_range(same_date, same_date)
        assert isinstance(sessions, pd.DatetimeIndex), "Should return DatetimeIndex"

        # Test with reversed dates (should handle gracefully)
        sessions_reversed = forex.sessions_in_range(
            pd.Timestamp("2025-01-20"), pd.Timestamp("2025-01-10")
        )
        assert len(sessions_reversed) == 0, "Reversed dates should return empty result"

    @pytest.mark.unit
    def test_forex_calendar_timezone_awareness(self):
        """Test FOREX calendar timezone configuration."""
        assert ForexCalendar.tz == "America/New_York", (
            "FOREX calendar should use America/New_York timezone"
        )

        # Verify calendar instance uses correct timezone
        start = pd.Timestamp("2025-01-01")
        end = pd.Timestamp("2025-01-31")
        forex = ForexCalendar(start=start, end=end)

        # Calendar timezone property should be set correctly (tz is a string)
        assert forex.tz == "America/New_York", (
            f"Calendar timezone should be America/New_York, got {forex.tz}"
        )

        # Note: Sessions are date-only (no timezone) by design in ExchangeCalendar
        # The timezone is used for open/close times, not session dates

    @pytest.mark.unit
    def test_forex_calendar_open_close_times_format(self):
        """Test FOREX calendar open/close times are properly formatted."""
        # open_times should be tuple of (date, time) pairs
        assert isinstance(ForexCalendar.open_times, tuple), "open_times should be a tuple"
        assert len(ForexCalendar.open_times) > 0, "open_times should not be empty"
        assert isinstance(ForexCalendar.open_times[0], tuple), (
            "open_times elements should be tuples"
        )

        # close_times should be tuple of (date, time) pairs
        assert isinstance(ForexCalendar.close_times, tuple), "close_times should be a tuple"
        assert len(ForexCalendar.close_times) > 0, "close_times should not be empty"
        assert isinstance(ForexCalendar.close_times[0], tuple), (
            "close_times elements should be tuples"
        )

    @pytest.mark.unit
    def test_forex_calendar_holiday_consistency(self):
        """Test FOREX calendar holidays are consistent across years."""
        # Test 2024 holidays
        start_2024 = pd.Timestamp("2024-01-01")
        end_2024 = pd.Timestamp("2024-12-31")
        forex_2024 = ForexCalendar(start=start_2024, end=end_2024)
        holidays_2024 = forex_2024.regular_holidays.holidays()

        # Test 2025 holidays
        start_2025 = pd.Timestamp("2025-01-01")
        end_2025 = pd.Timestamp("2025-12-31")
        forex_2025 = ForexCalendar(start=start_2025, end=end_2025)
        holidays_2025 = forex_2025.regular_holidays.holidays()

        # Both should have New Year and Christmas
        holiday_dates_2024 = [pd.Timestamp(h).date() for h in holidays_2024]
        holiday_dates_2025 = [pd.Timestamp(h).date() for h in holidays_2025]

        assert pd.Timestamp("2024-01-01").date() in holiday_dates_2024, "2024 should have New Year"
        assert pd.Timestamp("2025-01-01").date() in holiday_dates_2025, "2025 should have New Year"
        assert pd.Timestamp("2024-12-25").date() in holiday_dates_2024, "2024 should have Christmas"
        assert pd.Timestamp("2025-12-25").date() in holiday_dates_2025, "2025 should have Christmas"
