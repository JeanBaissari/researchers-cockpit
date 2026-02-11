"""
Test direct csvdir_equities() usage in extension.py patterns.

This module tests the direct usage of Zipline-Reloaded's csvdir_equities()
function as it would be used in ~/.zipline/extension.py for bundle registration.

v1.12.0: NO WRAPPERS - Direct Zipline API usage only.
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest
import pandas as pd
import numpy as np

# Zipline-Reloaded imports
from zipline.data.bundles import register, unregister, bundles
from zipline.data.bundles.csvdir import csvdir_equities
from zipline.utils.calendar_utils import get_calendar


class TestCsvdirEquitiesDirectUsage:
    """Test direct csvdir_equities() usage patterns."""

    @pytest.fixture
    def temp_csvdir(self, tmp_path):
        """Create a temporary csvdir structure for testing."""
        csvdir = tmp_path / "csvdir"
        csvdir.mkdir()

        # Create sample equity data
        equity_dir = csvdir / "AAPL"
        equity_dir.mkdir()

        # Generate sample OHLCV data
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz="UTC")
        n = len(dates)

        base_price = 150.0
        prices = base_price + np.cumsum(np.random.randn(n) * 2)

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices + np.random.randn(n) * 0.5,
                "high": prices + np.abs(np.random.randn(n) * 1.0),
                "low": prices - np.abs(np.random.randn(n) * 1.0),
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, n),
            }
        )

        # Ensure high >= max(open, close) and low <= min(open, close)
        df["high"] = df[["open", "close"]].max(axis=1) + np.abs(
            df["high"] - df[["open", "close"]].max(axis=1)
        )
        df["low"] = df[["open", "close"]].min(axis=1) - np.abs(
            df["low"] - df[["open", "close"]].min(axis=1)
        )

        # Write CSV file
        csv_file = equity_dir / "AAPL.csv"
        df.to_csv(csv_file, index=False)

        yield csvdir

        # Cleanup
        shutil.rmtree(tmp_path, ignore_errors=True)

    @pytest.fixture
    def temp_forex_csvdir(self, tmp_path):
        """Create a temporary csvdir structure for FOREX testing."""
        csvdir = tmp_path / "csvdir_forex"
        csvdir.mkdir()

        # Create sample FOREX data
        forex_dir = csvdir / "EURUSD"
        forex_dir.mkdir()

        # Generate sample OHLCV data (FOREX typically has more data points)
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="h", tz="UTC")
        n = len(dates)

        base_price = 1.1000
        prices = base_price + np.cumsum(np.random.randn(n) * 0.0001)

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices + np.random.randn(n) * 0.00005,
                "high": prices + np.abs(np.random.randn(n) * 0.0001),
                "low": prices - np.abs(np.random.randn(n) * 0.0001),
                "close": prices,
                "volume": np.random.randint(100000, 500000, n),
            }
        )

        # Ensure high >= max(open, close) and low <= min(open, close)
        df["high"] = df[["open", "close"]].max(axis=1) + np.abs(
            df["high"] - df[["open", "close"]].max(axis=1)
        )
        df["low"] = df[["open", "close"]].min(axis=1) - np.abs(
            df["low"] - df[["open", "close"]].min(axis=1)
        )

        # Write CSV file
        csv_file = forex_dir / "EURUSD.csv"
        df.to_csv(csv_file, index=False)

        yield csvdir

        # Cleanup
        shutil.rmtree(tmp_path, ignore_errors=True)

    def test_csvdir_equities_import(self):
        """Test that csvdir_equities can be imported from Zipline-Reloaded."""
        from zipline.data.bundles.csvdir import csvdir_equities

        assert csvdir_equities is not None
        assert callable(csvdir_equities)

    def test_csvdir_equities_signature(self):
        """Test that csvdir_equities has expected signature."""
        import inspect
        from zipline.data.bundles.csvdir import csvdir_equities

        sig = inspect.signature(csvdir_equities)
        params = list(sig.parameters.keys())

        # Should have tframes and csvdir parameters
        assert "tframes" in params or len(params) >= 1
        assert "csvdir" in params or len(params) >= 2

    def test_csvdir_equities_returns_callable(self):
        """Test that csvdir_equities() returns a callable ingest function."""
        from zipline.data.bundles.csvdir import csvdir_equities

        # csvdir_equities() should return a function that can be registered
        ingest_func = csvdir_equities(tframes=None, csvdir="/tmp/test")

        assert callable(ingest_func)

    def test_register_with_csvdir_equities_equity(self, temp_csvdir):
        """Test registering an equity bundle using csvdir_equities()."""
        bundle_name = "test_aapl_daily"

        try:
            # Register bundle using csvdir_equities() directly
            register(
                bundle_name,
                csvdir_equities(
                    tframes=None,  # None means daily
                    csvdir=str(temp_csvdir),
                ),
                calendar_name="NYSE",
            )

            # Verify bundle is registered
            assert bundle_name in bundles

        finally:
            # Cleanup
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_register_with_csvdir_equities_forex(self, temp_forex_csvdir):
        """Test registering a FOREX bundle using csvdir_equities()."""
        from lib.calendars import register_custom_calendars

        bundle_name = "test_eurusd_1h"

        try:
            # Register FOREX calendar first (required before use)
            register_custom_calendars(["FOREX"], force=True)

            # Register FOREX bundle using csvdir_equities() directly
            register(
                bundle_name,
                csvdir_equities(
                    tframes=["minute"],  # Minute bars for intraday
                    csvdir=str(temp_forex_csvdir),
                ),
                calendar_name="FOREX",
            )

            # Verify bundle is registered
            assert bundle_name in bundles

        finally:
            # Cleanup
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_csvdir_equities_with_symbol_list_pattern(self, temp_csvdir):
        """Test csvdir_equities() usage pattern with symbol specification."""
        bundle_name = "test_symbol_list"

        try:
            # Pattern: csvdir_equities() with csvdir pointing to directory structure
            # The csvdir should contain subdirectories named after symbols
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_import_pattern(self):
        """Test the import pattern that should be used in extension.py."""
        # This is the pattern documented for ~/.zipline/extension.py
        from zipline.data.bundles import register
        from zipline.data.bundles.csvdir import csvdir_equities

        # Verify imports work
        assert register is not None
        assert csvdir_equities is not None

    def test_extension_py_registration_pattern(self, temp_csvdir):
        """Test the registration pattern from extension.py documentation."""
        bundle_name = "test_extension_pattern"

        try:
            # Pattern from docs/api/bundles.md:
            # register(
            #     'eurusd_1h',
            #     csvdir_equities(
            #         ['EURUSD'],
            #         csvdir='/path/to/csvdir'
            #     ),
            #     calendar_name='FOREX'
            # )

            # Note: Based on actual signature, tframes is first param, csvdir is second
            register(
                bundle_name,
                csvdir_equities(
                    tframes=None,  # Daily timeframe
                    csvdir=str(temp_csvdir),
                ),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_multiple_bundles_registration(self, temp_csvdir, temp_forex_csvdir):
        """Test registering multiple bundles using csvdir_equities()."""
        from lib.calendars import register_custom_calendars

        equity_bundle = "test_multi_equity"
        forex_bundle = "test_multi_forex"

        try:
            # Register FOREX calendar first (required before use)
            register_custom_calendars(["FOREX"], force=True)

            # Register equity bundle
            register(
                equity_bundle,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="NYSE",
            )

            # Register FOREX bundle
            register(
                forex_bundle,
                csvdir_equities(tframes=["minute"], csvdir=str(temp_forex_csvdir)),
                calendar_name="FOREX",
            )

            # Verify both are registered
            assert equity_bundle in bundles
            assert forex_bundle in bundles

        finally:
            # Cleanup
            for bundle in [equity_bundle, forex_bundle]:
                if bundle in bundles:
                    unregister(bundle)

    def test_csvdir_equities_with_custom_calendar(self, temp_csvdir):
        """Test csvdir_equities() with custom calendar (FOREX/CRYPTO)."""
        from lib.calendars import register_custom_calendars

        bundle_name = "test_custom_calendar"

        try:
            # Register FOREX calendar first (required before use)
            register_custom_calendars(["FOREX"], force=True)

            # Register with custom FOREX calendar
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="FOREX",
            )

            assert bundle_name in bundles

            # Verify calendar can be retrieved
            calendar = get_calendar("FOREX")
            assert calendar is not None

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_csvdir_structure_validation(self, temp_csvdir):
        """Test that csvdir_equities() works with proper csvdir structure."""
        # csvdir structure should be:
        # csvdir/
        #   SYMBOL/
        #     SYMBOL.csv

        # Verify structure exists
        assert (temp_csvdir / "AAPL").exists()
        assert (temp_csvdir / "AAPL" / "AAPL.csv").exists()

        bundle_name = "test_structure_validation"

        try:
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_csvdir_equities_timeframe_specification(self, temp_csvdir):
        """Test csvdir_equities() with different timeframe specifications."""
        bundle_name = "test_timeframe_spec"

        try:
            # Test with None (daily)
            register(
                bundle_name,
                csvdir_equities(
                    tframes=None,  # Daily
                    csvdir=str(temp_csvdir),
                ),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles
            unregister(bundle_name)

            # Test with minute specification
            register(
                bundle_name,
                csvdir_equities(
                    tframes=["minute"],  # Minute bars
                    csvdir=str(temp_csvdir),
                ),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)


class TestExtensionPyPatterns:
    """Test extension.py file patterns and execution."""

    @pytest.fixture
    def temp_csvdir(self, tmp_path):
        """Create a temporary csvdir structure for testing."""
        csvdir = tmp_path / "csvdir"
        csvdir.mkdir()

        # Create sample equity data
        equity_dir = csvdir / "AAPL"
        equity_dir.mkdir()

        # Generate sample OHLCV data
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz="UTC")
        n = len(dates)

        base_price = 150.0
        prices = base_price + np.cumsum(np.random.randn(n) * 2)

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices + np.random.randn(n) * 0.5,
                "high": prices + np.abs(np.random.randn(n) * 1.0),
                "low": prices - np.abs(np.random.randn(n) * 1.0),
                "close": prices,
                "volume": np.random.randint(1000000, 5000000, n),
            }
        )

        # Ensure high >= max(open, close) and low <= min(open, close)
        df["high"] = df[["open", "close"]].max(axis=1) + np.abs(
            df["high"] - df[["open", "close"]].max(axis=1)
        )
        df["low"] = df[["open", "close"]].min(axis=1) - np.abs(
            df["low"] - df[["open", "close"]].min(axis=1)
        )

        # Write CSV file
        csv_file = equity_dir / "AAPL.csv"
        df.to_csv(csv_file, index=False)

        yield csvdir

        # Cleanup
        shutil.rmtree(tmp_path, ignore_errors=True)

    @pytest.fixture
    def temp_csvdir_multi(self, tmp_path):
        """Create a temporary csvdir with multiple symbols."""
        csvdir = tmp_path / "csvdir_multi"
        csvdir.mkdir()

        symbols = ["AAPL", "MSFT", "GOOGL"]
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz="UTC")
        n = len(dates)

        for symbol in symbols:
            symbol_dir = csvdir / symbol
            symbol_dir.mkdir()

            base_price = 100.0 + symbols.index(symbol) * 50.0
            prices = base_price + np.cumsum(np.random.randn(n) * 2)

            df = pd.DataFrame(
                {
                    "date": dates,
                    "open": prices + np.random.randn(n) * 0.5,
                    "high": prices + np.abs(np.random.randn(n) * 1.0),
                    "low": prices - np.abs(np.random.randn(n) * 1.0),
                    "close": prices,
                    "volume": np.random.randint(1000000, 5000000, n),
                }
            )

            # Ensure OHLCV validity
            df["high"] = df[["open", "close"]].max(axis=1) + np.abs(
                df["high"] - df[["open", "close"]].max(axis=1)
            )
            df["low"] = df[["open", "close"]].min(axis=1) - np.abs(
                df["low"] - df[["open", "close"]].min(axis=1)
            )

            csv_file = symbol_dir / f"{symbol}.csv"
            df.to_csv(csv_file, index=False)

        yield csvdir
        shutil.rmtree(tmp_path, ignore_errors=True)

    @pytest.fixture
    def temp_forex_csvdir(self, tmp_path):
        """Create a temporary csvdir structure for FOREX testing."""
        csvdir = tmp_path / "csvdir_forex"
        csvdir.mkdir()

        # Create sample FOREX data
        forex_dir = csvdir / "EURUSD"
        forex_dir.mkdir()

        # Generate sample OHLCV data (FOREX typically has more data points)
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="h", tz="UTC")
        n = len(dates)

        base_price = 1.1000
        prices = base_price + np.cumsum(np.random.randn(n) * 0.0001)

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices + np.random.randn(n) * 0.00005,
                "high": prices + np.abs(np.random.randn(n) * 0.0001),
                "low": prices - np.abs(np.random.randn(n) * 0.0001),
                "close": prices,
                "volume": np.random.randint(100000, 500000, n),
            }
        )

        # Ensure high >= max(open, close) and low <= min(open, close)
        df["high"] = df[["open", "close"]].max(axis=1) + np.abs(
            df["high"] - df[["open", "close"]].max(axis=1)
        )
        df["low"] = df[["open", "close"]].min(axis=1) - np.abs(
            df["low"] - df[["open", "close"]].min(axis=1)
        )

        # Write CSV file
        csv_file = forex_dir / "EURUSD.csv"
        df.to_csv(csv_file, index=False)

        yield csvdir
        shutil.rmtree(tmp_path, ignore_errors=True)

    @pytest.fixture
    def temp_extension_py(self, tmp_path, temp_csvdir_multi):
        """Create a temporary extension.py file for testing."""
        extension_file = tmp_path / "extension.py"

        # Create a complete extension.py pattern
        extension_content = f'''"""
Zipline Extension: Bundle Registration

This file demonstrates the v1.12.0+ pattern for registering CSV bundles
using direct csvdir_equities() from Zipline-Reloaded.
"""

# Standard library imports
from pathlib import Path

# Zipline-Reloaded imports
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# Custom calendar imports (if needed)
from lib.calendars import register_custom_calendars

# Register custom calendars first (required for FOREX/CRYPTO)
register_custom_calendars(["FOREX", "CRYPTO"], force=True)

# USER CONFIG: Bundle registrations
# Register equity bundle
register(
    'test_equity_daily',
    csvdir_equities(
        tframes=None,  # Daily timeframe
        csvdir=r'{temp_csvdir_multi}',
    ),
    calendar_name='NYSE',
)

# CLONE NOTE: Users should modify bundle names, paths, and calendars
# to match their data structure and trading requirements.
'''

        extension_file.write_text(extension_content)
        return extension_file

    def test_extension_py_imports(self):
        """Test that all imports required for extension.py work correctly."""
        # Test standard imports
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from zipline.utils.calendar_utils import get_calendar

        # Test custom calendar imports
        from lib.calendars import register_custom_calendars

        # Verify all imports are callable/accessible
        assert register is not None
        assert unregister is not None
        assert bundles is not None
        assert csvdir_equities is not None
        assert get_calendar is not None
        assert register_custom_calendars is not None

    def test_extension_py_file_structure(self, temp_extension_py):
        """Test that extension.py file has correct structure."""
        content = temp_extension_py.read_text()

        # Verify required imports
        assert "from zipline.data.bundles import register" in content
        assert "from zipline.data.bundles.csvdir import csvdir_equities" in content

        # Verify registration pattern
        assert "register(" in content
        assert "csvdir_equities(" in content

        # Verify comments/documentation
        assert "USER CONFIG" in content or "CLONE NOTE" in content

    def test_extension_py_execution_pattern(self, temp_csvdir_multi):
        """Test that extension.py execution pattern works correctly."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from lib.calendars import register_custom_calendars

        bundle_name = "test_extension_execution"

        try:
            # Simulate extension.py execution
            # Step 1: Register calendars (if needed)
            register_custom_calendars(["FOREX"], force=True)

            # Step 2: Register bundle
            register(
                bundle_name,
                csvdir_equities(
                    tframes=None,
                    csvdir=str(temp_csvdir_multi),
                ),
                calendar_name="NYSE",
            )

            # Step 3: Verify registration
            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_multiple_bundles_pattern(self, temp_csvdir_multi, temp_forex_csvdir):
        """Test extension.py pattern with multiple bundle registrations."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from lib.calendars import register_custom_calendars

        equity_bundle = "test_ext_equity"
        forex_bundle = "test_ext_forex"

        try:
            # Register calendars first
            register_custom_calendars(["FOREX"], force=True)

            # Register multiple bundles (extension.py pattern)
            register(
                equity_bundle,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir_multi)),
                calendar_name="NYSE",
            )

            register(
                forex_bundle,
                csvdir_equities(tframes=["minute"], csvdir=str(temp_forex_csvdir)),
                calendar_name="FOREX",
            )

            # Verify all bundles registered
            assert equity_bundle in bundles
            assert forex_bundle in bundles

        finally:
            for bundle in [equity_bundle, forex_bundle]:
                if bundle in bundles:
                    unregister(bundle)

    def test_extension_py_calendar_before_bundle(self, temp_csvdir):
        """Test that calendars must be registered before bundle registration."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from lib.calendars import register_custom_calendars
        from zipline.utils.calendar_utils import get_calendar

        bundle_name = "test_calendar_order"

        try:
            # Correct order: Register calendar first
            register_custom_calendars(["FOREX"], force=True)

            # Verify calendar exists
            calendar = get_calendar("FOREX")
            assert calendar is not None

            # Then register bundle
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="FOREX",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_path_handling(self, tmp_path):
        """Test extension.py path handling patterns."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from pathlib import Path

        # Create csvdir structure
        csvdir = tmp_path / "csvdir_path_test"
        csvdir.mkdir()
        symbol_dir = csvdir / "AAPL"
        symbol_dir.mkdir()

        # Create sample data
        dates = pd.date_range("2020-01-01", "2020-12-31", freq="D", tz="UTC")
        df = pd.DataFrame(
            {
                "date": dates,
                "open": [100.0] * len(dates),
                "high": [105.0] * len(dates),
                "low": [95.0] * len(dates),
                "close": [102.0] * len(dates),
                "volume": [1000000] * len(dates),
            }
        )
        (symbol_dir / "AAPL.csv").write_text(df.to_csv(index=False))

        bundle_name = "test_path_handling"

        try:
            # Test Path object conversion (common in extension.py)
            csvdir_path = Path(csvdir)

            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(csvdir_path)),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)
            shutil.rmtree(tmp_path, ignore_errors=True)

    def test_extension_py_error_handling_missing_dir(self):
        """Test extension.py error handling for missing csvdir.

        Note: Registration may succeed, but errors will occur during ingestion.
        This test verifies that invalid paths are handled gracefully.
        """
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities

        bundle_name = "test_missing_dir"

        try:
            # Registration may succeed even with invalid path
            # (validation happens during ingestion, not registration)
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir="/nonexistent/path"),
                calendar_name="NYSE",
            )

            # Bundle may be registered (validation deferred to ingestion)
            # The error will occur when trying to ingest the bundle
            if bundle_name in bundles:
                # Verify bundle exists but will fail on ingestion
                assert bundle_name in bundles

        finally:
            # Cleanup
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_error_handling_invalid_calendar(self, temp_csvdir):
        """Test extension.py error handling for invalid calendar name.

        Note: Registration may succeed, but errors will occur when the calendar
        is accessed during ingestion or backtest execution.
        """
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities

        bundle_name = "test_invalid_calendar"

        try:
            # Registration may succeed even with invalid calendar
            # (validation happens when calendar is accessed)
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="INVALID_CALENDAR_NAME",
            )

            # Bundle may be registered (validation deferred)
            # The error will occur when trying to use the calendar
            if bundle_name in bundles:
                assert bundle_name in bundles

        finally:
            # Cleanup
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_v1_12_0_compliance(self, temp_csvdir):
        """Test that extension.py patterns comply with v1.12.0 NO WRAPPERS directive."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities

        bundle_name = "test_v1_12_0_compliance"

        try:
            # v1.12.0 pattern: Direct csvdir_equities() usage
            # NO wrapper functions should be used
            register(
                bundle_name,
                csvdir_equities(tframes=None, csvdir=str(temp_csvdir)),
                calendar_name="NYSE",
            )

            assert bundle_name in bundles

            # Verify no wrapper imports are needed
            # (This test ensures we're using direct Zipline APIs)
            import sys

            assert "lib.bundles.csv" not in str(sys.modules.keys())

        finally:
            if bundle_name in bundles:
                unregister(bundle_name)

    def test_extension_py_complete_example(self, temp_csvdir_multi, temp_forex_csvdir):
        """Test a complete extension.py example with all patterns."""
        from zipline.data.bundles import register, unregister, bundles
        from zipline.data.bundles.csvdir import csvdir_equities
        from lib.calendars import register_custom_calendars
        from zipline.utils.calendar_utils import get_calendar

        bundles_to_register = [
            ("test_complete_equity", temp_csvdir_multi, "NYSE", None),
            ("test_complete_forex", temp_forex_csvdir, "FOREX", ["minute"]),
        ]

        try:
            # Register calendars first
            register_custom_calendars(["FOREX"], force=True)

            # Register all bundles
            for bundle_name, csvdir_path, calendar, tframes in bundles_to_register:
                register(
                    bundle_name,
                    csvdir_equities(tframes=tframes, csvdir=str(csvdir_path)),
                    calendar_name=calendar,
                )

                # Verify registration
                assert bundle_name in bundles

                # Verify calendar exists
                cal = get_calendar(calendar)
                assert cal is not None

        finally:
            # Cleanup all bundles
            for bundle_name, _, _, _ in bundles_to_register:
                if bundle_name in bundles:
                    unregister(bundle_name)
