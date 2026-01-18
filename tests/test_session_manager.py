"""
Unit tests for SessionManager (v1.1.0 calendar alignment).

Tests the core SessionManager functionality including strategies,
manager operations, and session validation.
"""

import pytest
import pandas as pd
from datetime import datetime

from lib.calendars.sessions import (
    SessionManager,
    SessionStrategy,
    ForexSessionStrategy,
    CryptoSessionStrategy,
    EquitySessionStrategy,
    SessionMismatchReport,
    compare_sessions,
)


class TestSessionStrategies:
    """Test SessionStrategy implementations."""

    def test_forex_strategy_calendar_name(self):
        """ForexSessionStrategy returns correct calendar name."""
        strategy = ForexSessionStrategy()
        assert strategy.get_calendar_name() == "FOREX"

    def test_forex_strategy_filters(self):
        """ForexSessionStrategy returns 4 filters in correct order."""
        strategy = ForexSessionStrategy()
        filters = strategy.get_session_filters()
        assert len(filters) == 4
        # Verify filter names
        filter_names = [f.__name__ for f in filters]
        expected = [
            'filter_forex_presession_bars',
            'consolidate_forex_sunday_to_friday',
            'filter_to_calendar_sessions',
            'apply_gap_filling',
        ]
        assert filter_names == expected

    def test_forex_strategy_validation_tolerant(self):
        """ForexSessionStrategy allows small discrepancies."""
        strategy = ForexSessionStrategy()
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            # Missing 2024-01-02 (1 missing session)
            pd.Timestamp('2024-01-03'),
        ])
        is_valid, msg = strategy.validate_sessions(expected, actual)
        # Should pass with warning (1 missing < tolerance of 2)
        assert is_valid
        assert "within tolerance" in msg

    def test_crypto_strategy_calendar_name(self):
        """CryptoSessionStrategy returns correct calendar name."""
        strategy = CryptoSessionStrategy()
        assert strategy.get_calendar_name() == "CRYPTO"

    def test_crypto_strategy_filters(self):
        """CryptoSessionStrategy returns 2 filters."""
        strategy = CryptoSessionStrategy()
        filters = strategy.get_session_filters()
        assert len(filters) == 2
        filter_names = [f.__name__ for f in filters]
        expected = ['filter_to_calendar_sessions', 'apply_gap_filling']
        assert filter_names == expected

    def test_crypto_strategy_validation_strict(self):
        """CryptoSessionStrategy enforces strict matching."""
        strategy = CryptoSessionStrategy()
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            # Missing 2024-01-02
        ])
        is_valid, msg = strategy.validate_sessions(expected, actual)
        # Should fail (CRYPTO has no tolerance)
        assert not is_valid
        assert "CRYPTO requires exact sessions" in msg

    def test_equity_strategy_calendar_name(self):
        """EquitySessionStrategy returns correct calendar name."""
        strategy = EquitySessionStrategy()
        assert strategy.get_calendar_name() == "NYSE"

    def test_equity_strategy_filters(self):
        """EquitySessionStrategy returns 1 filter."""
        strategy = EquitySessionStrategy()
        filters = strategy.get_session_filters()
        assert len(filters) == 1
        assert filters[0].__name__ == 'filter_to_calendar_sessions'


class TestSessionManager:
    """Test SessionManager core functionality."""

    def test_for_asset_class_forex(self):
        """SessionManager.for_asset_class('forex') creates ForexSessionStrategy."""
        mgr = SessionManager.for_asset_class('forex')
        assert isinstance(mgr.strategy, ForexSessionStrategy)
        assert mgr.calendar_name == "FOREX"

    def test_for_asset_class_crypto(self):
        """SessionManager.for_asset_class('crypto') creates CryptoSessionStrategy."""
        mgr = SessionManager.for_asset_class('crypto')
        assert isinstance(mgr.strategy, CryptoSessionStrategy)
        assert mgr.calendar_name == "CRYPTO"

    def test_for_asset_class_equity(self):
        """SessionManager.for_asset_class('equity') creates EquitySessionStrategy."""
        mgr = SessionManager.for_asset_class('equity')
        assert isinstance(mgr.strategy, EquitySessionStrategy)
        assert mgr.calendar_name == "NYSE"

    def test_for_asset_class_invalid(self):
        """SessionManager.for_asset_class() raises on invalid asset class."""
        with pytest.raises(ValueError, match="Unknown asset class"):
            SessionManager.for_asset_class('invalid')

    def test_get_sessions_deterministic(self):
        """SessionManager.get_sessions() is deterministic."""
        mgr1 = SessionManager.for_asset_class('forex')
        mgr2 = SessionManager.for_asset_class('forex')

        start = pd.Timestamp('2024-01-01', tz='UTC')
        end = pd.Timestamp('2024-01-31', tz='UTC')

        sessions1 = mgr1.get_sessions(start, end)
        sessions2 = mgr2.get_sessions(start, end)

        assert sessions1.equals(sessions2), "SessionManager must be deterministic"

    def test_get_sessions_timezone_naive(self):
        """SessionManager.get_sessions() returns timezone-naive."""
        mgr = SessionManager.for_asset_class('forex')
        start = pd.Timestamp('2024-01-01', tz='UTC')
        end = pd.Timestamp('2024-01-31', tz='UTC')

        sessions = mgr.get_sessions(start, end)
        assert sessions.tz is None, "Sessions must be timezone-naive"

    def test_apply_filters_forex(self):
        """SessionManager.apply_filters() applies FOREX filters."""
        mgr = SessionManager.for_asset_class('forex')

        # Create sample data (daily)
        dates = pd.date_range('2024-01-01', '2024-01-10', freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0] * len(dates),
            'high': [101.0] * len(dates),
            'low': [99.0] * len(dates),
            'close': [100.5] * len(dates),
            'volume': [1000] * len(dates),
        }, index=dates)

        # Apply filters (should not raise)
        try:
            filtered = mgr.apply_filters(df, show_progress=False)
            assert isinstance(filtered, pd.DataFrame)
        except Exception as e:
            pytest.fail(f"apply_filters() raised unexpected exception: {e}")


class TestSessionValidation:
    """Test session validation utilities."""

    def test_compare_sessions_exact_match(self):
        """compare_sessions() returns valid for exact match."""
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
        ])

        report = compare_sessions(expected, actual)
        assert report.is_valid
        assert report.expected_count == 2
        assert report.actual_count == 2
        assert len(report.missing_sessions) == 0
        assert len(report.extra_sessions) == 0

    def test_compare_sessions_missing(self):
        """compare_sessions() detects missing sessions."""
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            # Missing 2024-01-02
            pd.Timestamp('2024-01-03'),
        ])

        report = compare_sessions(expected, actual)
        assert not report.is_valid
        assert report.expected_count == 3
        assert report.actual_count == 2
        assert len(report.missing_sessions) == 1
        assert report.missing_sessions[0] == pd.Timestamp('2024-01-02')
        assert "re-ingest" in " ".join(report.recommendations).lower()

    def test_compare_sessions_extra(self):
        """compare_sessions() detects extra sessions."""
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),  # Extra
        ])

        report = compare_sessions(expected, actual)
        assert not report.is_valid
        assert len(report.extra_sessions) == 1
        assert report.extra_sessions[0] == pd.Timestamp('2024-01-03')

    def test_compare_sessions_tolerance(self):
        """compare_sessions() respects tolerance parameter."""
        expected = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02'),
            pd.Timestamp('2024-01-03'),
        ])
        actual = pd.DatetimeIndex([
            pd.Timestamp('2024-01-01'),
            # Missing 2024-01-02
            pd.Timestamp('2024-01-03'),
        ])

        # Tolerance of 0 (default) - should fail
        report = compare_sessions(expected, actual, tolerance=0)
        assert not report.is_valid

        # Tolerance of 1 - should pass
        report = compare_sessions(expected, actual, tolerance=1)
        assert report.is_valid

    def test_session_mismatch_report_to_dict(self):
        """SessionMismatchReport.to_dict() serializes correctly."""
        expected = pd.DatetimeIndex([pd.Timestamp('2024-01-01')])
        actual = pd.DatetimeIndex([])

        report = compare_sessions(expected, actual)
        report_dict = report.to_dict()

        assert isinstance(report_dict, dict)
        assert 'is_valid' in report_dict
        assert 'expected_count' in report_dict
        assert 'actual_count' in report_dict
        assert 'missing_sessions' in report_dict
        assert 'recommendations' in report_dict

    def test_session_mismatch_report_to_markdown(self):
        """SessionMismatchReport.to_markdown() generates markdown."""
        expected = pd.DatetimeIndex([pd.Timestamp('2024-01-01')])
        actual = pd.DatetimeIndex([])

        report = compare_sessions(expected, actual)
        markdown = report.to_markdown()

        assert isinstance(markdown, str)
        assert '# Session Alignment Report' in markdown
        assert '**Status:** INVALID' in markdown
        assert 'Missing Sessions' in markdown
        assert 'Recommendations' in markdown


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
