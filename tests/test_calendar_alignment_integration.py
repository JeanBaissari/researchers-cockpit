"""
Integration tests for v1.1.0 calendar alignment pipeline.

Tests the integration between SessionManager, CSV ingestion, and backtest validation.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path

from lib.calendars.sessions import SessionManager, compare_sessions
from lib.bundles.csv import normalize_csv_columns, parse_csv_filename


class TestSessionManagerIntegration:
    """Integration tests for SessionManager across modules."""

    def test_forex_session_manager_consistency(self):
        """Multiple SessionManager instances for FOREX return identical sessions."""
        # This test validates that SessionManager is deterministic across
        # bundle ingestion and backtest execution
        mgr_ingestion = SessionManager.for_asset_class('forex')
        mgr_backtest = SessionManager.for_asset_class('forex')

        start = pd.Timestamp('2024-01-01', tz='UTC')
        end = pd.Timestamp('2024-12-31', tz='UTC')

        sessions_ingestion = mgr_ingestion.get_sessions(start, end)
        sessions_backtest = mgr_backtest.get_sessions(start, end)

        assert sessions_ingestion.equals(sessions_backtest), \
            "SessionManager must return identical sessions across different instances"

    def test_csv_normalize_columns(self):
        """CSV column normalization handles various formats."""
        test_cases = [
            # Test case: (input_columns, should_succeed)
            (['Open', 'High', 'Low', 'Close', 'Volume'], True),
            (['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME'], True),
            (['open', 'high', 'low', 'close', 'volume'], True),
            (['Open', 'High', 'Low', 'Adj Close', 'Volume'], True),
            (['o', 'h', 'l', 'c', 'v'], True),
            (['Open', 'High', 'Low'], False),  # Missing columns
        ]

        for columns, should_succeed in test_cases:
            df = pd.DataFrame(columns=columns)
            if should_succeed:
                result = normalize_csv_columns(df)
                assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume']
            else:
                with pytest.raises(ValueError):
                    normalize_csv_columns(df)

    def test_csv_filename_parsing(self):
        """CSV filename parsing extracts dates correctly."""
        test_cases = [
            # (filename, symbol, timeframe, expected_start, expected_end)
            (
                'EURUSD_1h_20200102_20250717.csv',
                'EURUSD',
                '1h',
                pd.Timestamp('2020-01-02', tz='UTC'),
                pd.Timestamp('2025-07-17 23:59:59', tz='UTC')
            ),
            (
                'EURUSD_1h_2020-01-02_2025-07-17.csv',
                'EURUSD',
                '1h',
                pd.Timestamp('2020-01-02', tz='UTC'),
                pd.Timestamp('2025-07-17 23:59:59', tz='UTC')
            ),
            (
                'EURUSD_1h_20200102-050000_20250717-030000_ready.csv',
                'EURUSD',
                '1h',
                pd.Timestamp('2020-01-02', tz='UTC'),
                pd.Timestamp('2025-07-17 23:59:59', tz='UTC')
            ),
            # No dates in filename
            (
                'EURUSD_1h.csv',
                'EURUSD',
                '1h',
                None,
                None
            ),
        ]

        for filename, symbol, timeframe, expected_start, expected_end in test_cases:
            start, end = parse_csv_filename(filename, symbol, timeframe)
            if expected_start is None:
                assert start is None
                assert end is None
            else:
                assert start.normalize() == expected_start.normalize()
                assert end.normalize() == expected_end.normalize()

    def test_session_validation_workflow(self):
        """End-to-end workflow: get sessions, compare, generate report."""
        mgr = SessionManager.for_asset_class('forex')

        # Step 1: Get expected sessions
        start = pd.Timestamp('2024-01-01', tz='UTC')
        end = pd.Timestamp('2024-01-31', tz='UTC')
        expected_sessions = mgr.get_sessions(start, end)

        # Step 2: Simulate actual sessions (with 5 missing to exceed tolerance)
        actual_sessions = expected_sessions[:-5]  # Remove last 5 sessions

        # Step 3: Validate
        is_valid, error = mgr.validate_sessions(expected_sessions, actual_sessions)
        assert not is_valid, "Validation should fail with missing sessions"

        # Step 4: Generate detailed report
        report = compare_sessions(expected_sessions, actual_sessions)
        assert not report.is_valid
        assert len(report.missing_sessions) == 5
        assert len(report.recommendations) > 0

        # Step 5: Verify report serialization
        report_dict = report.to_dict()
        assert report_dict['expected_count'] == len(expected_sessions)
        assert report_dict['actual_count'] == len(actual_sessions)

        markdown = report.to_markdown()
        assert '**Status:** INVALID' in markdown


class TestBacktestPreFlightValidation:
    """Test backtest pre-flight validation integration."""

    def test_validate_calendar_parameter_propagates(self):
        """Validate that validate_calendar parameter works in runner."""
        # This is a smoke test to ensure the parameter exists
        from lib.backtest.runner import run_backtest
        import inspect

        sig = inspect.signature(run_backtest)
        assert 'validate_calendar' in sig.parameters, \
            "run_backtest must have validate_calendar parameter"

        param = sig.parameters['validate_calendar']
        assert param.default is False, \
            "validate_calendar should default to False (non-breaking)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
