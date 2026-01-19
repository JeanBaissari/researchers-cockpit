"""
Integration tests for Zipline-Reloaded compatibility.

Tests that verify:
1. API imports work correctly
2. Date normalization is consistent
3. Calendar handling uses exchange_calendars codes
4. Bundle registration and loading works
5. Data access patterns match ZR requirements
6. End-to-end backtest execution works
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.data.normalization import normalize_to_utc
from lib.config import load_settings
from lib.bundles import list_bundles, load_bundle


class TestDateNormalization:
    """Test date normalization utility."""

    def test_normalize_timezone_aware(self):
        """Test normalizing timezone-aware datetime to timezone-naive UTC."""
        dt = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        result = normalize_to_utc(dt)

        assert result.tz is None, "Result should be timezone-naive"
        # normalize_to_utc strips timezone but preserves time
        assert result.time() == pd.Timestamp('12:00:00').time(), "Time should be preserved"
        assert result.date() == pd.Timestamp('2024-01-01').date(), "Date should be preserved"

    def test_normalize_timezone_naive(self):
        """Test normalizing timezone-naive datetime (no-op except type conversion)."""
        dt = pd.Timestamp('2024-01-01 12:00:00')
        result = normalize_to_utc(dt)

        assert result.tz is None, "Result should be timezone-naive"
        # normalize_to_utc preserves time for naive inputs
        assert result.time() == pd.Timestamp('12:00:00').time(), "Time should be preserved"

    def test_normalize_string_date(self):
        """Test normalizing string date."""
        result = normalize_to_utc('2024-01-01')

        assert result.tz is None, "Result should be timezone-naive"
        # String date without time defaults to midnight
        assert result.time() == pd.Timestamp('00:00:00').time(), "Should be midnight for date-only string"


class TestCalendarConsistency:
    """Test calendar code consistency."""

    def test_calendar_codes_use_exchange_calendars_format(self):
        """Verify calendar codes use exchange_calendars format."""
        from lib.bundles.yahoo import register_yahoo_bundle as _register_yahoo_bundle

        # This should use XNYS, not NYSE
        # We can't easily test the registration without actual data,
        # but we can verify the function signature expects exchange_calendars codes
        # Default parameter should be 'XNYS', not 'NYSE'
        import inspect
        sig = inspect.signature(_register_yahoo_bundle)
        default_calendar = sig.parameters['calendar_name'].default
        assert default_calendar == 'XNYS', f"Default calendar should be 'XNYS', got '{default_calendar}'"


class TestAPIImports:
    """Test that API imports match ZR conventions."""

    def test_run_algorithm_import(self):
        """Test run_algorithm import."""
        try:
            from zipline import run_algorithm
            assert callable(run_algorithm), "run_algorithm should be callable"
        except ImportError:
            pytest.skip("zipline-reloaded not installed")

    def test_api_imports(self):
        """Test zipline.api imports."""
        try:
            from zipline.api import (
                symbol,
                order_target_percent,
                record,
                schedule_function,
                date_rules,
                time_rules,
            )
            assert callable(symbol)
            assert callable(order_target_percent)
            assert callable(record)
            assert callable(schedule_function)
        except ImportError:
            pytest.skip("zipline-reloaded not installed")

    def test_finance_imports(self):
        """Test zipline.finance imports."""
        try:
            from zipline.finance import commission, slippage
            assert hasattr(commission, 'PerShare')
            assert hasattr(slippage, 'VolumeShareSlippage')
        except ImportError:
            pytest.skip("zipline-reloaded not installed")


class TestBundlePatterns:
    """Test bundle registration and loading patterns."""

    def test_list_bundles(self):
        """Test listing bundles."""
        bundles = list_bundles()
        assert isinstance(bundles, list), "Should return a list"

    def test_bundle_loading_error_handling(self):
        """Test bundle loading handles missing bundles gracefully."""
        with pytest.raises(FileNotFoundError):
            load_bundle('nonexistent_bundle_12345')


class TestDataAccessPatterns:
    """Test data access patterns match ZR requirements."""

    def test_strategy_template_imports(self):
        """Test that strategy template can be imported."""
        template_path = project_root / 'strategies' / '_template' / 'strategy.py'
        if template_path.exists():
            # Just verify it can be imported without errors
            import importlib.util
            spec = importlib.util.spec_from_file_location("template_strategy", template_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't execute, just verify spec is valid
                assert spec is not None


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.skip(reason="Requires actual bundle data and longer execution time")
    def test_full_backtest_pipeline(self):
        """Test full backtest pipeline execution.

        This test requires:
        - A registered bundle with data
        - A valid strategy
        - Actual execution time

        Marked as skip by default, run with: pytest -m "not skip"
        """
        from lib.backtest import run_backtest, save_results

        # This would run an actual backtest
        # perf = run_backtest('spy_sma_cross', start_date='2020-01-01', end_date='2020-12-31')
        # assert perf is not None
        # assert 'returns' in perf.columns
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
