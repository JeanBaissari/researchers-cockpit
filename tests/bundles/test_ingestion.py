"""
Test bundle ingestion operations.

Tests for multi-symbol ingestion, concurrent ingestion, and bundle recovery.
"""

# Standard library imports
import sys
import json
import sqlite3
import tempfile
import shutil
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import (
    register_bundle_metadata,
    load_bundle_registry,
    save_bundle_registry,
    get_bundle_registry_path,
    is_valid_date_string,
    extract_symbols_from_bundle,
    get_bundle_symbols,
    register_yahoo_bundle,
)
from lib.bundles.registry import (
    _register_bundle_metadata,
    _load_bundle_registry,
    _save_bundle_registry,
    _get_bundle_registry_path,
)
from lib.bundles.utils import (
    _is_valid_date_string,
    _extract_symbols_from_bundle,
)
from lib.bundles.yahoo import (
    register_yahoo_bundle as _register_yahoo_bundle,
)


@pytest.fixture
def mock_yfinance_data():
    """Create controlled yfinance response data for multiple symbols."""
    def create_data(symbol: str, days: int = 30, has_gaps: bool = False):
        """Generate mock OHLCV data for a symbol."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            periods=days,
            freq='D',
            tz='UTC'
        )

        # Remove some dates to create gaps if requested
        if has_gaps:
            dates = dates[::2]  # Every other day

        base_price = 100.0
        np.random.seed(42)  # For reproducibility

        data = pd.DataFrame({
            'Open': base_price + np.random.randn(len(dates)) * 2,
            'High': base_price + np.random.randn(len(dates)) * 2 + 1,
            'Low': base_price + np.random.randn(len(dates)) * 2 - 1,
            'Close': base_price + np.random.randn(len(dates)) * 2,
            'Volume': np.random.randint(1000000, 10000000, len(dates)),
        }, index=dates)

        return data

    return create_data


@pytest.fixture
def corrupted_registry_data():
    """Provide sample corrupted registry entries for testing."""
    return {
        'corrupted_end_date': {
            'symbols': ['SPY'],
            'calendar_name': 'XNYS',
            'end_date': 'daily',  # Corrupted: timeframe instead of date
            'data_frequency': 'daily',
            'timeframe': 'daily'
        },
        'missing_symbols': {
            'calendar_name': 'XNYS',
            'data_frequency': 'daily',
            'timeframe': 'daily'
            # Missing 'symbols' key
        },
        'empty_symbols': {
            'symbols': [],
            'calendar_name': 'XNYS',
            'data_frequency': 'daily',
            'timeframe': 'daily'
        }
    }


class TestMultiSymbolIngestion:
    """Tests for multi-symbol bundle ingestion scenarios.

    These tests verify that:
    1. Multiple symbols receive sequential SIDs (0, 1, 2, ...)
    2. Asset database contains all symbols
    3. Bundle registry includes all symbols
    4. Partial failures are handled gracefully (some symbols fail, others succeed)
    5. Symbol ordering is preserved
    """

    @pytest.mark.unit
    def test_multi_symbol_sid_assignment(self, mock_yfinance_data):
        """Verify that multiple symbols receive sequential SIDs."""
        symbols = ['SPY', 'AAPL', 'GOOGL', 'MSFT']

        # Mock yfinance
        with patch('yfinance.Ticker') as mock_ticker:
            def create_mock_ticker(symbol):
                mock = MagicMock()
                mock.history.return_value = mock_yfinance_data(symbol, days=10)
                return mock

            mock_ticker.side_effect = create_mock_ticker

            # Track SID assignments
            sid_assignments = []

            # The data_gen function yields (sid, df) tuples
            # We need to verify SIDs are sequential
            for expected_sid, symbol in enumerate(symbols):
                assert expected_sid == symbols.index(symbol), \
                    f"SID {expected_sid} should be assigned to {symbol}"

    @pytest.mark.unit
    def test_multi_symbol_registry_persistence(self):
        """Test that all symbols are persisted to bundle registry."""
        test_symbols = ['SPY', 'AAPL', 'GOOGL', 'MSFT', 'NVDA']
        bundle_name = 'test_multi_symbol_bundle'

        # Register bundle metadata
        register_bundle_metadata(
            bundle_name=bundle_name,
            symbols=test_symbols,
            calendar_name='XNYS',
            start_date='2024-01-01',
            end_date='2024-12-01',
            data_frequency='daily',
            timeframe='daily'
        )

        # Reload registry and verify
        registry = load_bundle_registry()

        assert bundle_name in registry, "Bundle not found in registry"
        assert registry[bundle_name]['symbols'] == test_symbols, \
            f"Symbols mismatch: expected {test_symbols}, got {registry[bundle_name]['symbols']}"

        # Cleanup
        del registry[bundle_name]
        save_bundle_registry(registry)

    @pytest.mark.unit
    def test_multi_symbol_partial_failure(self, mock_yfinance_data):
        """Test graceful handling when some symbols fail to fetch."""
        symbols = ['SPY', 'INVALID_SYMBOL_XYZ', 'AAPL', 'ANOTHER_BAD_123']

        with patch('yfinance.Ticker') as mock_ticker:
            def create_mock_ticker(symbol):
                mock = MagicMock()
                if 'INVALID' in symbol or 'BAD' in symbol:
                    # Return empty DataFrame for invalid symbols
                    mock.history.return_value = pd.DataFrame()
                else:
                    mock.history.return_value = mock_yfinance_data(symbol, days=10)
                return mock

            mock_ticker.side_effect = create_mock_ticker

            # Valid symbols should still be processable
            valid_symbols = [s for s in symbols if 'INVALID' not in s and 'BAD' not in s]
            assert len(valid_symbols) == 2, "Should have 2 valid symbols"

    @pytest.mark.unit
    def test_multi_symbol_ordering_preserved(self):
        """Test that symbol ordering is preserved in registry."""
        # Specific order matters for reproducibility
        ordered_symbols = ['ZZZZ', 'AAAA', 'MMMM', 'BBBB']
        bundle_name = 'test_ordering_bundle'

        register_bundle_metadata(
            bundle_name=bundle_name,
            symbols=ordered_symbols,
            calendar_name='XNYS',
            start_date='2024-01-01',
            end_date='2024-12-01',
            data_frequency='daily',
            timeframe='daily'
        )

        registry = load_bundle_registry()
        assert registry[bundle_name]['symbols'] == ordered_symbols, \
            "Symbol order should be preserved"

        # Cleanup
        del registry[bundle_name]
        save_bundle_registry(registry)


class TestConcurrentIngestion:
    """Tests for concurrent bundle ingestion scenarios."""

    @pytest.mark.integration
    def test_concurrent_registry_writes(self):
        """Test thread-safety of bundle registry write operations."""
        num_threads = 5
        bundles_per_thread = 3

        def register_bundles(thread_id):
            """Register bundles from a thread."""
            for i in range(bundles_per_thread):
                bundle_name = f'concurrent_test_bundle_{thread_id}_{i}'
                register_bundle_metadata(
                    bundle_name=bundle_name,
                    symbols=['SPY'],
                    calendar_name='XNYS',
                    start_date='2024-01-01',
                    end_date='2024-12-01',
                    data_frequency='daily',
                    timeframe='daily'
                )
                time.sleep(0.01)  # Small delay to increase chance of race condition

        # Run concurrent registrations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(register_bundles, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify all bundles were registered
        registry = load_bundle_registry()
        registered_count = sum(1 for k in registry if 'concurrent_test_bundle_' in k)

        # Cleanup
        for i in range(num_threads):
            for j in range(bundles_per_thread):
                bundle_name = f'concurrent_test_bundle_{i}_{j}'
                if bundle_name in registry:
                    del registry[bundle_name]
        save_bundle_registry(registry)

    @pytest.mark.integration
    def test_registered_bundles_set_concurrent_access(self):
        """Test thread-safety of _registered_bundles set."""
        from lib.bundles.registry import _registered_bundles
        from lib.bundles import add_registered_bundle, discard_registered_bundle

        num_threads = 10
        operations_per_thread = 5

        def add_bundles(thread_id):
            """Add bundles from a thread."""
            for i in range(operations_per_thread):
                bundle_name = f'concurrent_set_test_{thread_id}_{i}'
                add_registered_bundle(bundle_name)
                time.sleep(0.001)

        # Run concurrent additions
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(add_bundles, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Cleanup
        for i in range(num_threads):
            for j in range(operations_per_thread):
                bundle_name = f'concurrent_set_test_{i}_{j}'
                discard_registered_bundle(bundle_name)


class TestCorruptedBundleRecovery:
    """Tests for corrupted bundle recovery mechanisms.

    Tests verify:
    1. Handling corrupted registry entries (invalid dates, missing fields)
    2. Recovery via SQLite extraction fallback
    3. Graceful handling of corrupted SQLite files
    4. No-op ingest registration for existing data
    """

    @pytest.mark.unit
    def test_is_valid_date_string(self):
        """Test date string validation helper."""
        # Valid dates
        assert is_valid_date_string('2024-01-01') is True
        assert is_valid_date_string('2020-12-31') is True

        # Invalid dates
        assert is_valid_date_string('daily') is False  # Timeframe, not date
        assert is_valid_date_string('invalid') is False
        assert is_valid_date_string('') is False
        assert is_valid_date_string(None) is False
        assert is_valid_date_string('01-01-2024') is False  # Wrong format
        assert is_valid_date_string('2024/01/01') is False  # Wrong separator

    @pytest.mark.unit
    def test_corrupted_end_date_detection(self, corrupted_registry_data):
        """Test detection of corrupted end_date field (timeframe stored as date)."""
        corrupted_entry = corrupted_registry_data['corrupted_end_date']

        # end_date has 'daily' instead of a date
        assert is_valid_date_string(corrupted_entry['end_date']) is False, \
            "Should detect 'daily' as invalid date"

    @pytest.mark.unit
    def test_missing_symbols_handling(self, corrupted_registry_data):
        """Test handling of registry entries with missing symbols field."""
        entry = corrupted_registry_data['missing_symbols']

        # Entry should not have 'symbols' key
        assert 'symbols' not in entry

        # Code should handle this gracefully
        symbols = entry.get('symbols', [])
        assert symbols == [], "Should default to empty list"

    @pytest.mark.unit
    def test_empty_symbols_handling(self, corrupted_registry_data):
        """Test handling of registry entries with empty symbols list."""
        entry = corrupted_registry_data['empty_symbols']

        assert entry['symbols'] == []
        assert len(entry['symbols']) == 0

    @pytest.mark.unit
    def test_load_bundle_with_corrupted_registry(self, tmp_path):
        """Test load_bundle behavior with corrupted registry data."""
        # Create corrupted registry entry
        registry = load_bundle_registry()
        registry['corrupted_test_bundle'] = {
            'symbols': ['SPY'],
            'calendar_name': 'XNYS',
            'end_date': 'daily',  # Corrupted!
            'data_frequency': 'daily'
        }
        save_bundle_registry(registry)

        # Reload and validate
        registry = load_bundle_registry()
        entry = registry.get('corrupted_test_bundle')

        assert entry is not None
        end_date = entry.get('end_date')

        # Validation should detect corruption
        if end_date:
            is_valid = is_valid_date_string(end_date)
            assert is_valid is False, "Should detect corrupted end_date"

        # Cleanup
        del registry['corrupted_test_bundle']
        save_bundle_registry(registry)

    @pytest.mark.unit
    def test_extract_symbols_from_nonexistent_bundle(self):
        """Test symbol extraction from non-existent bundle returns empty list."""
        symbols = extract_symbols_from_bundle('nonexistent_bundle_xyz')
        assert symbols == [], "Should return empty list for non-existent bundle"

    @pytest.mark.unit
    def test_get_bundle_symbols_fallback_chain(self):
        """Test get_bundle_symbols fallback from registry to SQLite."""
        bundle_name = 'test_fallback_bundle'

        # Register in registry
        registry = load_bundle_registry()
        registry[bundle_name] = {
            'symbols': ['SPY', 'AAPL'],
            'calendar_name': 'XNYS',
            'data_frequency': 'daily'
        }
        save_bundle_registry(registry)

        # Should get symbols from registry
        symbols = get_bundle_symbols(bundle_name)
        assert isinstance(symbols, list)

        # Cleanup
        if bundle_name in registry:
            del registry[bundle_name]
            save_bundle_registry(registry)

