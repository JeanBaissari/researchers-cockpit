"""
Test bundle access functions.

Tests for load_bundle, get_bundle_symbols, and list_bundles functions.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.access import (
    load_bundle,
    get_bundle_symbols,
    list_bundles,
)


class TestLoadBundle:
    """Tests for load_bundle function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_load_bundle_success(self, mock_load, mock_init):
        """Test load_bundle successfully loads a registered bundle."""
        mock_bundle_data = MagicMock()
        mock_load.return_value = mock_bundle_data
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = load_bundle("test_bundle")

        # ensure_bundles_initialized is called in both load_bundle and ensure_bundle_registered
        assert mock_init.call_count >= 1
        mock_load.assert_called_once_with("test_bundle")
        assert result == mock_bundle_data

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_load_bundle_not_registered(self, mock_init):
        """Test load_bundle raises FileNotFoundError for unregistered bundle."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_bundle("missing")

            error_msg = str(exc_info.value)
            assert "Bundle 'missing' not found" in error_msg
            assert "Available bundles:" in error_msg
            assert "Please ingest the bundle first" in error_msg

        # ensure_bundles_initialized is called in both load_bundle and ensure_bundle_registered
        assert mock_init.call_count >= 1

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_load_bundle_error_message_includes_available_bundles(self, mock_init):
        """Test load_bundle error message includes available bundles."""
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_bundle("missing")

            error_msg = str(exc_info.value)
            assert "bundle1" in error_msg or "bundle2" in error_msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_load_bundle_load_failure(self, mock_load, mock_init):
        """Test load_bundle raises RuntimeError when load() fails."""
        mock_bundles = {"test_bundle": MagicMock()}
        original_error = ValueError("Database connection failed")
        mock_load.side_effect = original_error

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(RuntimeError, match="Failed to load bundle 'test_bundle'"):
                load_bundle("test_bundle")

        mock_init.assert_called()
        mock_load.assert_called_once_with("test_bundle")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_load_bundle_exception_chaining(self, mock_load, mock_init):
        """Test load_bundle preserves exception context via exception chaining."""
        mock_bundles = {"test_bundle": MagicMock()}
        original_error = ConnectionError("Database unavailable")
        mock_load.side_effect = original_error

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(RuntimeError) as exc_info:
                load_bundle("test_bundle")

            # Verify exception chaining (__cause__ is set)
            assert exc_info.value.__cause__ == original_error
            assert isinstance(exc_info.value.__cause__, ConnectionError)

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    @patch("lib.bundles.access.logger")
    def test_load_bundle_logging(self, mock_logger, mock_load, mock_init):
        """Test load_bundle logs success message."""
        mock_bundles = {"test_bundle": MagicMock()}
        mock_bundle_data = MagicMock()
        mock_load.return_value = mock_bundle_data

        with patch("zipline.data.bundles.bundles", mock_bundles):
            load_bundle("test_bundle")

        mock_logger.info.assert_called_once_with("Loaded bundle 'test_bundle' successfully")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    @patch("lib.bundles.access.logger")
    def test_load_bundle_logs_exception(self, mock_logger, mock_load, mock_init):
        """Test load_bundle logs exception when load() fails."""
        mock_bundles = {"test_bundle": MagicMock()}
        mock_load.side_effect = ValueError("Load failed")

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(RuntimeError):
                load_bundle("test_bundle")

        mock_logger.exception.assert_called_once_with("Failed to load bundle 'test_bundle'")


class TestGetBundleSymbols:
    """Tests for get_bundle_symbols function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_success(self, mock_extract, mock_init):
        """Test get_bundle_symbols returns symbols for registered bundle."""
        mock_extract.return_value = ["AAPL", "MSFT"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = get_bundle_symbols("test_bundle")

        # ensure_bundles_initialized is called in both get_bundle_symbols and ensure_bundle_registered
        assert mock_init.call_count >= 1
        mock_extract.assert_called_once_with("test_bundle")
        assert result == ["AAPL", "MSFT"]

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_not_registered(self, mock_extract, mock_init):
        """Test get_bundle_symbols raises FileNotFoundError for unregistered bundle."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                get_bundle_symbols("missing")

            error_msg = str(exc_info.value)
            assert "Bundle 'missing' not found" in error_msg
            assert "Please ingest the bundle first" in error_msg

        # ensure_bundles_initialized is called in both get_bundle_symbols and ensure_bundle_registered
        assert mock_init.call_count >= 1
        # Should not call extract_symbols if bundle not registered
        mock_extract.assert_not_called()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_empty_extraction(self, mock_extract, mock_init):
        """Test get_bundle_symbols returns empty list when extraction fails."""
        mock_extract.return_value = []
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = get_bundle_symbols("test_bundle")

        # ensure_bundles_initialized is called in both get_bundle_symbols and ensure_bundle_registered
        assert mock_init.call_count >= 1
        mock_extract.assert_called_once_with("test_bundle")
        assert result == []

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    @patch("lib.bundles.access.logger")
    def test_get_bundle_symbols_empty_warning(self, mock_logger, mock_extract, mock_init):
        """Test get_bundle_symbols logs warning when extraction returns empty list."""
        mock_extract.return_value = []
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = get_bundle_symbols("test_bundle")

        assert result == []
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Could not extract symbols from bundle 'test_bundle'" in warning_msg
        assert "Bundle may be empty or corrupted" in warning_msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_none_extraction(self, mock_extract, mock_init):
        """Test get_bundle_symbols handles None return from extract_symbols_from_bundle."""
        mock_extract.return_value = None
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = get_bundle_symbols("test_bundle")

        # None should be treated as falsy, so empty list returned
        assert result == []

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_duplicate_symbols(self, mock_extract, mock_init):
        """Test get_bundle_symbols handles duplicate symbols correctly."""
        # extract_symbols_from_bundle should return deduplicated list, but test edge case
        mock_extract.return_value = ["AAPL", "MSFT", "AAPL", "GOOGL", "MSFT"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = get_bundle_symbols("test_bundle")

        # Function returns whatever extract_symbols_from_bundle returns
        # (extract_symbols_from_bundle handles deduplication)
        assert result == ["AAPL", "MSFT", "AAPL", "GOOGL", "MSFT"]


class TestListBundles:
    """Tests for list_bundles function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_success(self, mock_init):
        """Test list_bundles returns list of registered bundles."""
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = list_bundles()

        mock_init.assert_called_once()
        assert set(result) == {"bundle1", "bundle2"}

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_empty(self, mock_init):
        """Test list_bundles returns empty list when no bundles registered."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = list_bundles()

        mock_init.assert_called_once()
        assert result == []

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_preserves_order(self, mock_init):
        """Test list_bundles preserves bundle order from Zipline registry."""
        # Use OrderedDict-like behavior (Python 3.7+ dicts preserve insertion order)
        mock_bundles = {
            "bundle_a": MagicMock(),
            "bundle_b": MagicMock(),
            "bundle_c": MagicMock(),
        }

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = list_bundles()

        mock_init.assert_called_once()
        assert result == ["bundle_a", "bundle_b", "bundle_c"]

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_large_registry(self, mock_init):
        """Test list_bundles handles large number of bundles."""
        mock_bundles = {f"bundle_{i}": MagicMock() for i in range(100)}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = list_bundles()

        mock_init.assert_called_once()
        assert len(result) == 100
        assert all(f"bundle_{i}" in result for i in range(100))


class TestBundleAccessEdgeCases:
    """Tests for edge cases and access patterns in bundle access functions."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_load_bundle_empty_name(self, mock_init):
        """Test load_bundle handles empty bundle name."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_bundle("")

            error_msg = str(exc_info.value)
            assert "Bundle '' not found" in error_msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_load_bundle_special_characters_in_name(self, mock_init):
        """Test load_bundle handles special characters in bundle name."""
        mock_bundles = {"test-bundle_123": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("zipline.data.bundles.load") as mock_load:
                mock_load.return_value = MagicMock()
                result = load_bundle("test-bundle_123")

                assert result is not None
                mock_load.assert_called_once_with("test-bundle_123")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_load_bundle_very_long_name(self, mock_init):
        """Test load_bundle handles very long bundle names."""
        long_name = "a" * 1000
        mock_bundles = {long_name: MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("zipline.data.bundles.load") as mock_load:
                mock_load.return_value = MagicMock()
                result = load_bundle(long_name)

                assert result is not None
                mock_load.assert_called_once_with(long_name)

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_load_bundle_initialization_failure(self, mock_load, mock_init):
        """Test load_bundle handles initialization failure gracefully."""
        mock_init.side_effect = RuntimeError("Initialization failed")
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(RuntimeError, match="Initialization failed"):
                load_bundle("test_bundle")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_get_bundle_symbols_empty_name(self, mock_init):
        """Test get_bundle_symbols handles empty bundle name."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                get_bundle_symbols("")

            error_msg = str(exc_info.value)
            assert "Bundle '' not found" in error_msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_get_bundle_symbols_extraction_exception(self, mock_extract, mock_init):
        """Test get_bundle_symbols handles exception from extract_symbols_from_bundle."""
        mock_extract.side_effect = Exception("Extraction failed")
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            # extract_symbols_from_bundle is called, but exception should propagate
            with pytest.raises(Exception, match="Extraction failed"):
                get_bundle_symbols("test_bundle")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_initialization_failure(self, mock_init):
        """Test list_bundles handles initialization failure gracefully."""
        mock_init.side_effect = RuntimeError("Initialization failed")

        with patch("zipline.data.bundles.bundles", {}):
            with pytest.raises(RuntimeError, match="Initialization failed"):
                list_bundles()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_bundles_special_characters(self, mock_init):
        """Test list_bundles handles bundles with special characters in names."""
        mock_bundles = {
            "bundle-1": MagicMock(),
            "bundle_2": MagicMock(),
            "bundle.3": MagicMock(),
            "bundle 4": MagicMock(),
        }

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = list_bundles()

        assert len(result) == 4
        assert "bundle-1" in result
        assert "bundle_2" in result
        assert "bundle.3" in result
        assert "bundle 4" in result


class TestBundleAccessIntegration:
    """Integration tests for bundle access patterns."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_sequential_access_pattern(self, mock_extract, mock_load, mock_init):
        """Test sequential access to same bundle via different functions."""
        mock_bundle_data = MagicMock()
        mock_load.return_value = mock_bundle_data
        mock_extract.return_value = ["AAPL", "MSFT"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            # First, list bundles
            bundles_list = list_bundles()
            assert "test_bundle" in bundles_list

            # Then, load the bundle
            bundle_data = load_bundle("test_bundle")
            assert bundle_data == mock_bundle_data

            # Finally, get symbols
            symbols = get_bundle_symbols("test_bundle")
            assert symbols == ["AAPL", "MSFT"]

        # Initialization should be called multiple times (once per function)
        assert mock_init.call_count >= 3

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_multiple_bundle_access(self, mock_load, mock_init):
        """Test accessing multiple different bundles sequentially."""
        mock_bundle1 = MagicMock()
        mock_bundle2 = MagicMock()
        mock_load.side_effect = [mock_bundle1, mock_bundle2]
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result1 = load_bundle("bundle1")
            result2 = load_bundle("bundle2")

            assert result1 == mock_bundle1
            assert result2 == mock_bundle2
            assert mock_load.call_count == 2
            mock_load.assert_any_call("bundle1")
            mock_load.assert_any_call("bundle2")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    @patch("lib.bundles.access.extract_symbols_from_bundle")
    def test_load_then_get_symbols_pattern(self, mock_extract, mock_load, mock_init):
        """Test common pattern: load bundle then get its symbols."""
        mock_bundle_data = MagicMock()
        mock_load.return_value = mock_bundle_data
        mock_extract.return_value = ["AAPL", "MSFT", "GOOGL"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            # Load bundle first
            bundle_data = load_bundle("test_bundle")
            assert bundle_data == mock_bundle_data

            # Then get symbols
            symbols = get_bundle_symbols("test_bundle")
            assert symbols == ["AAPL", "MSFT", "GOOGL"]

        # Both should succeed
        mock_load.assert_called_once_with("test_bundle")
        mock_extract.assert_called_once_with("test_bundle")

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_list_then_load_pattern(self, mock_init):
        """Test common pattern: list bundles then load one."""
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            # List all bundles
            available = list_bundles()
            assert len(available) == 2

            # Load one of them
            with patch("zipline.data.bundles.load") as mock_load:
                mock_load.return_value = MagicMock()
                bundle_data = load_bundle(available[0])

                assert bundle_data is not None
                mock_load.assert_called_once_with(available[0])


class TestBundleAccessErrorMessages:
    """Tests for error message formatting and content."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_error_message_includes_ingest_command(self, mock_init):
        """Test error message includes suggested ingest command."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_bundle("missing_bundle")

            error_msg = str(exc_info.value)
            # Error message should include ingest command structure
            assert "python scripts/ingest_data.py" in error_msg or "ingest" in error_msg.lower()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_error_message_format_structure(self, mock_init):
        """Test error message has proper structure with all required components."""
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_bundle("missing")

            error_msg = str(exc_info.value)
            # Should contain bundle name
            assert "missing" in error_msg
            # Should mention available bundles
            assert (
                "Available bundles" in error_msg or "bundle1" in error_msg or "bundle2" in error_msg
            )
            # Should provide actionable guidance
            assert "ingest" in error_msg.lower() or "Please" in error_msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_load_failure_error_message_includes_exception(self, mock_load, mock_init):
        """Test load failure error message includes original exception details."""
        mock_bundles = {"test_bundle": MagicMock()}
        original_error = ValueError("Database connection timeout after 30 seconds")
        mock_load.side_effect = original_error

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(RuntimeError) as exc_info:
                load_bundle("test_bundle")

            error_msg = str(exc_info.value)
            # Should mention the bundle name
            assert "test_bundle" in error_msg
            # Should reference the failure
            assert "Failed to load" in error_msg or "load" in error_msg.lower()
            # Should chain the original exception
            assert exc_info.value.__cause__ == original_error
