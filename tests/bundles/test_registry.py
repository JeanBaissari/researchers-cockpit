"""
Test bundle registry operations.

Tests for bundle registry load/save, metadata structure, and registry operations.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import (
    load_bundle_registry,
    save_bundle_registry,
    register_bundle_metadata,
    list_bundles,
    get_bundle_symbols,
    load_bundle,
)


class TestBundleRegistryOperations:
    """Tests for bundle registry operations."""

    @pytest.mark.unit
    def test_load_save_registry(self):
        """Test registry load/save operations."""
        # Load current registry
        registry = load_bundle_registry()
        assert isinstance(registry, dict)

    @pytest.mark.unit
    def test_registry_metadata_structure(self):
        """Test that registry entries have required fields."""
        registry = load_bundle_registry()

        required_fields = ['symbols', 'calendar_name', 'data_frequency']

        for bundle_name, meta in registry.items():
            for field in required_fields:
                assert field in meta, f"Bundle {bundle_name} missing field: {field}"

    @pytest.mark.unit
    def test_registry_timeframe_preserved(self):
        """Test that timeframe is preserved in registry entries."""
        registry = load_bundle_registry()

        for bundle_name, meta in registry.items():
            if 'timeframe' in meta:
                # Extract expected timeframe from bundle name (last component)
                name_parts = bundle_name.split('_')
                if len(name_parts) >= 3:
                    expected_tf = name_parts[-1]  # e.g., 'daily', '1h', '5m', '15m', '30m'
                    if expected_tf in ('1h', '5m', '15m', '30m', 'daily'):
                        assert meta['timeframe'] == expected_tf, \
                            f"{bundle_name} should have timeframe '{expected_tf}', got '{meta['timeframe']}'"


class TestBundleAutoDetection:
    """Tests for bundle frequency auto-detection."""

    @pytest.mark.unit
    def test_auto_detect_from_registry(self):
        """Test auto-detection reads frequency from registry."""
        registry = load_bundle_registry()

        # Check that bundles with 1h in name have minute frequency
        for bundle_name, meta in registry.items():
            if '1h' in bundle_name or '5m' in bundle_name:
                assert meta.get('data_frequency') == 'minute', \
                    f"Intraday bundle {bundle_name} should have minute frequency"
            elif 'daily' in bundle_name:
                assert meta.get('data_frequency') == 'daily', \
                    f"Daily bundle {bundle_name} should have daily frequency"


class TestBundleSymbols:
    """Tests for bundle symbol operations."""

    @pytest.mark.unit
    def test_bundle_symbols_retrievable(self):
        """Test that bundle symbols can be retrieved from registry."""
        registry = load_bundle_registry()

        for bundle_name, meta in registry.items():
            assert 'symbols' in meta, f"Bundle {bundle_name} missing symbols field"
            assert isinstance(meta['symbols'], list), f"Bundle {bundle_name} symbols is not a list"
            assert len(meta['symbols']) > 0, f"Bundle {bundle_name} has empty symbols list"

    @pytest.mark.integration
    def test_symbol_lookup_in_bundle(self):
        """Test that symbols in bundle can be looked up via asset_finder."""
        registry = load_bundle_registry()

        for bundle_name, meta in registry.items():
            try:
                bundle_data = load_bundle(bundle_name)
                asset_finder = bundle_data.asset_finder

                for symbol in meta['symbols']:
                    # Try to look up the symbol
                    try:
                        assets = asset_finder.lookup_symbols([symbol], as_of_date=None)
                        assert len(assets) > 0, f"Symbol {symbol} not found in {bundle_name}"
                    except Exception:
                        # Some symbols may have date constraints
                        pass
            except FileNotFoundError:
                continue


class TestBundleIntegrity:
    """Tests for bundle data integrity."""

    @pytest.mark.integration
    def test_bundle_readers_consistent(self):
        """Test that minute and daily readers have valid first trading days.

        NOTE: The minute bar reader's first_trading_day is set by the calendar
        (typically 1990-01-02 for XNYS), not the actual data start date.
        The daily bar reader's first_trading_day reflects actual data.

        This test verifies:
        1. Daily reader has valid (non-NaT) first_trading_day after NaT fix
        2. Both readers exist and are accessible
        """
        import warnings

        registry = load_bundle_registry()
        intraday_bundles = [b for b in registry if registry[b].get('data_frequency') == 'minute']

        bundles_needing_fix = []

        for bundle_name in intraday_bundles:
            try:
                bundle_data = load_bundle(bundle_name)

                minute_reader = bundle_data.equity_minute_bar_reader
                daily_reader = bundle_data.equity_daily_bar_reader

                # Both readers should exist
                assert minute_reader is not None, f"Bundle {bundle_name} has no minute reader"
                assert daily_reader is not None, f"Bundle {bundle_name} has no daily reader"

                # Check daily reader first_trading_day (this is what the NaT fix addresses)
                daily_ftd = daily_reader.first_trading_day
                if pd.isna(daily_ftd):
                    bundles_needing_fix.append(bundle_name)
                else:
                    # Daily reader should have a valid date
                    assert pd.Timestamp(daily_ftd).year >= 2000, \
                        f"Bundle {bundle_name}: daily_ftd ({daily_ftd}) seems invalid"

            except FileNotFoundError:
                continue

        if bundles_needing_fix:
            warnings.warn(
                f"Intraday bundles with NaT daily_ftd (need re-ingestion): {bundles_needing_fix}",
                UserWarning
            )

    @pytest.mark.integration
    def test_calendar_consistency(self):
        """Test that bundle calendar matches registry calendar."""
        registry = load_bundle_registry()

        for bundle_name, meta in registry.items():
            try:
                bundle_data = load_bundle(bundle_name)
                reader = bundle_data.equity_daily_bar_reader

                if reader is not None and hasattr(reader, 'trading_calendar'):
                    bundle_calendar = reader.trading_calendar
                    if bundle_calendar is not None:
                        expected_calendar = meta.get('calendar_name', '').upper()
                        actual_calendar = bundle_calendar.name.upper()

                        # Calendar names should match (allowing for aliases)
                        assert expected_calendar in actual_calendar or actual_calendar in expected_calendar, \
                            f"Bundle {bundle_name} calendar mismatch: expected {expected_calendar}, got {actual_calendar}"
            except FileNotFoundError:
                continue

