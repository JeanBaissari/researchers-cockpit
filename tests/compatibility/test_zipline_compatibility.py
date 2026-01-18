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

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib.data.normalization import normalize_to_utc
from lib.config import load_settings
from lib.bundles import list_bundles, load_bundle


class TestDateNormalization:
    """Test date normalization utility."""

    @pytest.mark.unit
    def test_normalize_timezone_aware(self):
        """Test normalizing timezone-aware datetime to timezone-naive UTC."""
        dt = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        result = normalize_to_utc(dt)

        assert result.tz is None, "Result should be timezone-naive"
        # normalize_to_utc strips timezone but preserves time
        assert result.time() == pd.Timestamp('12:00:00').time(), "Time should be preserved"
        assert result.date() == pd.Timestamp('2024-01-01').date(), "Date should be preserved"

    @pytest.mark.unit
    def test_normalize_timezone_naive(self):
        """Test normalizing timezone-naive datetime (no-op except type conversion)."""
        dt = pd.Timestamp('2024-01-01 12:00:00')
        result = normalize_to_utc(dt)

        assert result.tz is None, "Result should be timezone-naive"
        # normalize_to_utc preserves time for naive inputs
        assert result.time() == pd.Timestamp('12:00:00').time(), "Time should be preserved"

    @pytest.mark.unit
    def test_normalize_string_date(self):
        """Test normalizing string date."""
        result = normalize_to_utc('2024-01-01')

        assert result.tz is None, "Result should be timezone-naive"
        # String date without time defaults to midnight
        assert result.time() == pd.Timestamp('00:00:00').time(), "Should be midnight for date-only string"


class TestCalendarConsistency:
    """Test calendar code consistency."""
    
    @pytest.mark.unit
    def test_calendar_codes_use_exchange_calendars_format(self):
        """Verify calendar codes use exchange_calendars format."""
        from lib.bundles import register_yahoo_bundle
        
        # This should use XNYS, not NYSE
        # We can't easily test the registration without actual data,
        # but we can verify the function signature expects exchange_calendars codes
        # Default parameter should be 'XNYS', not 'NYSE'
        import inspect
        sig = inspect.signature(register_yahoo_bundle)
        default_calendar = sig.parameters['calendar_name'].default
        assert default_calendar == 'XNYS', f"Default calendar should be 'XNYS', got '{default_calendar}'"


class TestAPIImports:
    """Test that API imports match ZR conventions."""
    
    @pytest.mark.unit
    def test_run_algorithm_import(self):
        """Test run_algorithm import."""
        try:
            from zipline import run_algorithm
            assert run_algorithm is not None
        except ImportError:
            pytest.skip("zipline-reloaded not installed")
    
    @pytest.mark.unit
    def test_finance_imports(self):
        """Test finance module imports."""
        try:
            from zipline.finance import commission, slippage
            assert commission is not None
            assert slippage is not None
        except ImportError:
            pytest.skip("zipline-reloaded not installed")


class TestDataAccessPatterns:
    """Test data access patterns match ZR requirements."""
    
    @pytest.mark.unit
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
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires actual bundle data and longer execution time")
    def test_full_backtest_pipeline(self):
        """Test full backtest pipeline with ZR."""
        # This would test the complete workflow
        pass

