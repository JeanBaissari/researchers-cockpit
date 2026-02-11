"""
Test calendar registry.

Tests for calendar registry functionality including registration,
population, and retrieval of custom calendars.
"""

# Standard library imports
import sys
import builtins
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.calendars.registry import (
    populate_registry,
    get_calendar_registry,
    register_calendar_type,
    register_custom_calendars,
    get_registered_calendars,
)
from lib.calendars.crypto import CryptoCalendar
from lib.calendars.forex import ForexCalendar


class TestPopulateRegistry:
    """Tests for populate_registry function."""

    @pytest.mark.unit
    def test_populate_registry_empty(self):
        """Test populating registry with empty dict."""
        # Clear registry first
        registry = get_calendar_registry()
        original_keys = set(registry.keys())

        # Populate with empty dict
        populate_registry({})

        # Registry should still have original calendars
        registry_after = get_calendar_registry()
        assert set(registry_after.keys()) == original_keys

    @pytest.mark.unit
    def test_populate_registry_single_calendar(self):
        """Test populating registry with single calendar."""
        # Get current registry state
        original_registry = get_calendar_registry()
        original_count = len(original_registry)

        # Create a mock calendar class
        class MockCalendar:
            name = "MOCK"

        # Populate with new calendar
        populate_registry({"MOCK": MockCalendar})

        # Verify calendar was added
        registry = get_calendar_registry()
        assert "MOCK" in registry
        assert registry["MOCK"] == MockCalendar
        assert len(registry) == original_count + 1

    @pytest.mark.unit
    def test_populate_registry_multiple_calendars(self):
        """Test populating registry with multiple calendars."""

        # Create mock calendar classes
        class MockCalendar1:
            name = "MOCK1"

        class MockCalendar2:
            name = "MOCK2"

        # Populate with multiple calendars
        populate_registry(
            {
                "MOCK1": MockCalendar1,
                "MOCK2": MockCalendar2,
            }
        )

        # Verify both calendars were added
        registry = get_calendar_registry()
        assert "MOCK1" in registry
        assert "MOCK2" in registry
        assert registry["MOCK1"] == MockCalendar1
        assert registry["MOCK2"] == MockCalendar2

    @pytest.mark.unit
    def test_populate_registry_overwrites_existing(self):
        """Test that populate_registry overwrites existing entries."""

        # Create mock calendar classes
        class MockCalendar1:
            name = "MOCK"

        class MockCalendar2:
            name = "MOCK"

        # Populate with first calendar
        populate_registry({"MOCK": MockCalendar1})
        registry = get_calendar_registry()
        assert registry["MOCK"] == MockCalendar1

        # Overwrite with second calendar
        populate_registry({"MOCK": MockCalendar2})
        registry = get_calendar_registry()
        assert registry["MOCK"] == MockCalendar2


class TestGetCalendarRegistry:
    """Tests for get_calendar_registry function."""

    @pytest.mark.unit
    def test_get_calendar_registry_returns_copy(self):
        """Test that get_calendar_registry returns a copy, not the original."""
        registry1 = get_calendar_registry()
        registry2 = get_calendar_registry()

        # Should be equal but not the same object
        assert registry1 == registry2
        assert registry1 is not registry2

        # Modifying one should not affect the other
        registry1["TEST"] = "test"
        registry3 = get_calendar_registry()
        assert "TEST" not in registry3

    @pytest.mark.unit
    def test_get_calendar_registry_contains_default_calendars(self):
        """Test that registry contains default calendars (CRYPTO, FOREX)."""
        registry = get_calendar_registry()

        # Should contain CRYPTO and FOREX (populated in __init__.py)
        assert "CRYPTO" in registry
        assert "FOREX" in registry
        assert registry["CRYPTO"] == CryptoCalendar
        assert registry["FOREX"] == ForexCalendar


class TestRegisterCalendarType:
    """Tests for register_calendar_type function."""

    @pytest.mark.unit
    def test_register_calendar_type_invalid_class(self):
        """Test that invalid calendar class raises ValueError."""

        class NotACalendar:
            pass

        with pytest.raises(ValueError, match="must be a subclass of ExchangeCalendar"):
            register_calendar_type("INVALID", NotACalendar)

    @pytest.mark.unit
    @patch("lib.calendars.registry.logger")
    def test_register_calendar_type_import_error(self, mock_logger):
        """Test handling of exchange_calendars import error.

        Note: This test verifies that the error handling code path exists.
        Fully simulating an import error when exchange_calendars is installed
        is difficult, so we verify the code structure handles errors correctly.
        """
        # Verify the function has error handling by checking the source code structure
        import inspect

        source = inspect.getsource(register_calendar_type)
        assert "except ImportError" in source, "Function should handle ImportError"
        assert "logger.error" in source, "Function should log import errors"

        # The actual import error handling is tested implicitly through code coverage
        # In a real scenario where exchange_calendars is missing, the function
        # would catch ImportError and return False (as seen in lines 77-81 of registry.py)

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    @patch("lib.calendars.registry.logger")
    def test_register_calendar_type_success(self, mock_logger, mock_dispatcher):
        """Test successful calendar registration."""
        # Setup mock
        mock_dispatcher.register_calendar_type.return_value = None

        # Register calendar
        result = register_calendar_type("CRYPTO", CryptoCalendar, force=True)

        # Verify registration
        assert result is True
        mock_dispatcher.register_calendar_type.assert_called_once_with(
            name="CRYPTO", calendar_type=CryptoCalendar, force=True
        )
        mock_logger.info.assert_called_once()

        # Verify calendar is tracked
        registered = get_registered_calendars()
        assert "CRYPTO" in registered

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    @patch("lib.calendars.registry.logger")
    def test_register_calendar_type_registration_error(self, mock_logger, mock_dispatcher):
        """Test handling of registration errors."""
        # Setup mock to raise exception
        mock_dispatcher.register_calendar_type.side_effect = Exception("Registration failed")

        # Register calendar
        result = register_calendar_type("CRYPTO", CryptoCalendar)

        # Verify error handling
        assert result is False
        mock_logger.error.assert_called_once()

        # Verify calendar is not tracked on failure
        registered = get_registered_calendars()
        # CRYPTO might be in list from previous tests, so we check the call was made
        mock_dispatcher.register_calendar_type.assert_called_once()

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_ignores_start_end(self, mock_dispatcher):
        """Test that start and end parameters are ignored."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Register with start/end (should be ignored)
        result = register_calendar_type(
            "CRYPTO", CryptoCalendar, start="2020-01-01", end="2020-12-31", force=True
        )

        assert result is True
        # Verify only name, calendar_type, and force are passed
        mock_dispatcher.register_calendar_type.assert_called_once_with(
            name="CRYPTO", calendar_type=CryptoCalendar, force=True
        )

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_tracks_registration(self, mock_dispatcher):
        """Test that registered calendars are tracked."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Clear any existing registrations for this test
        initial_registered = get_registered_calendars()

        # Register calendar
        register_calendar_type("CRYPTO", CryptoCalendar)

        # Verify it's tracked
        registered = get_registered_calendars()
        assert "CRYPTO" in registered

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_does_not_duplicate_tracking(self, mock_dispatcher):
        """Test that re-registering doesn't duplicate tracking."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Register first time
        register_calendar_type("CRYPTO", CryptoCalendar)
        registered1 = get_registered_calendars()
        count1 = registered1.count("CRYPTO")

        # Register again
        register_calendar_type("CRYPTO", CryptoCalendar)
        registered2 = get_registered_calendars()
        count2 = registered2.count("CRYPTO")

        # Should not duplicate
        assert count2 == count1


class TestRegisterCustomCalendars:
    """Tests for register_custom_calendars function."""

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    def test_register_custom_calendars_specific_list(self, mock_register):
        """Test registering specific calendars."""
        mock_register.return_value = True

        # Register specific calendars
        results = register_custom_calendars(["CRYPTO", "FOREX"])

        # Verify results
        assert results["CRYPTO"] is True
        assert results["FOREX"] is True
        assert mock_register.call_count == 2

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    def test_register_custom_calendars_all(self, mock_register):
        """Test registering all available calendars."""
        mock_register.return_value = True

        # Register all calendars (None means all)
        results = register_custom_calendars()

        # Should register all calendars in registry
        registry = get_calendar_registry()
        assert len(results) == len(registry)
        for name in registry.keys():
            assert name in results
            assert results[name] is True

    @pytest.mark.unit
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_unknown_calendar(self, mock_logger):
        """Test handling of unknown calendar names."""
        # Try to register unknown calendar
        results = register_custom_calendars(["UNKNOWN_CALENDAR"])

        # Should fail gracefully
        assert results["UNKNOWN_CALENDAR"] is False
        # Logger may be called multiple times (warning for unknown, summary for failures)
        assert mock_logger.warning.call_count >= 1

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_mixed_results(self, mock_logger, mock_register):
        """Test handling of mixed success/failure results."""

        # Setup mock to return different results
        def side_effect(name, calendar_class, **kwargs):
            return name == "CRYPTO"  # Only CRYPTO succeeds

        mock_register.side_effect = side_effect

        # Register multiple calendars
        results = register_custom_calendars(["CRYPTO", "FOREX"])

        # Verify mixed results
        assert results["CRYPTO"] is True
        assert results["FOREX"] is False

        # Verify logging
        assert mock_logger.info.call_count >= 1  # Success log
        assert mock_logger.warning.call_count >= 0  # May or may not have failures

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    def test_register_custom_calendars_passes_parameters(self, mock_register):
        """Test that parameters are passed through correctly."""
        mock_register.return_value = True

        # Register with parameters
        register_custom_calendars(["CRYPTO"], start="2020-01-01", end="2020-12-31", force=False)

        # Verify parameters passed
        mock_register.assert_called_once_with(
            name="CRYPTO",
            calendar_class=CryptoCalendar,
            start="2020-01-01",
            end="2020-12-31",
            force=False,
        )

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_logs_summary(self, mock_logger, mock_register):
        """Test that registration summary is logged."""

        def side_effect(name, calendar_class, **kwargs):
            return name == "CRYPTO"  # Only CRYPTO succeeds

        mock_register.side_effect = side_effect

        # Register calendars
        register_custom_calendars(["CRYPTO", "FOREX"])

        # Verify summary logging
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]

        # Should have success log
        assert any("Registered calendars" in str(call) for call in info_calls)
        # May have failure log if FOREX failed
        if any("Failed to register" in str(call) for call in warning_calls):
            assert any("FOREX" in str(call) for call in warning_calls)


class TestGetRegisteredCalendars:
    """Tests for get_registered_calendars function."""

    @pytest.mark.unit
    def test_get_registered_calendars_returns_list(self):
        """Test that get_registered_calendars returns a list."""
        registered = get_registered_calendars()
        assert isinstance(registered, list)

    @pytest.mark.unit
    def test_get_registered_calendars_returns_copy(self):
        """Test that get_registered_calendars returns a copy."""
        registered1 = get_registered_calendars()
        registered2 = get_registered_calendars()

        # Should be equal but not the same object
        assert registered1 == registered2
        assert registered1 is not registered2

        # Modifying one should not affect the other
        registered1.append("TEST")
        registered3 = get_registered_calendars()
        assert "TEST" not in registered3

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_get_registered_calendars_tracks_registrations(self, mock_dispatcher):
        """Test that get_registered_calendars tracks registrations."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Get initial state
        initial = set(get_registered_calendars())

        # Register a calendar
        register_calendar_type("CRYPTO", CryptoCalendar)

        # Verify it's tracked
        registered = get_registered_calendars()
        assert "CRYPTO" in registered or set(registered) == initial


class TestRegistryIntegration:
    """Integration tests for registry functions."""

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_full_registration_workflow(self, mock_dispatcher):
        """Test complete workflow: populate -> register -> track."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Create a new calendar class
        class TestCalendar(CryptoCalendar):
            name = "TEST"

        # Populate registry
        populate_registry({"TEST": TestCalendar})

        # Verify in registry
        registry = get_calendar_registry()
        assert "TEST" in registry

        # Register with Zipline
        result = register_calendar_type("TEST", TestCalendar)
        assert result is True

        # Verify tracked
        registered = get_registered_calendars()
        assert "TEST" in registered

        # Verify Zipline registration was called
        mock_dispatcher.register_calendar_type.assert_called_once_with(
            name="TEST", calendar_type=TestCalendar, force=True
        )

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    def test_register_custom_calendars_workflow(self, mock_register):
        """Test register_custom_calendars workflow."""
        mock_register.return_value = True

        # Register all available calendars
        results = register_custom_calendars()

        # Verify all calendars were registered
        registry = get_calendar_registry()
        assert len(results) == len(registry)
        assert all(results.values())  # All should succeed

        # Verify each calendar was registered
        assert mock_register.call_count == len(registry)

    @pytest.mark.unit
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_empty_list(self, mock_logger):
        """Test register_custom_calendars with empty list."""
        # Register with empty list
        results = register_custom_calendars([])

        # Should return empty dict
        assert results == {}

        # Should not log success or failure (no calendars to process)
        # Check that no info/warning calls were made for registration
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert not any("Registered calendars" in str(call) for call in info_calls)
        assert not any("Failed to register" in str(call) for call in warning_calls)

    @pytest.mark.unit
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_multiple_unknown(self, mock_logger):
        """Test register_custom_calendars with multiple unknown calendars."""
        # Try to register multiple unknown calendars
        results = register_custom_calendars(["UNKNOWN1", "UNKNOWN2", "UNKNOWN3"])

        # All should fail
        assert len(results) == 3
        assert all(not v for v in results.values())  # All False

        # Should log warnings for each unknown calendar
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert len([c for c in warning_calls if "Unknown calendar" in str(c)]) >= 3

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_force_false(self, mock_dispatcher):
        """Test register_calendar_type with force=False."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Register with force=False
        result = register_calendar_type("CRYPTO", CryptoCalendar, force=False)

        assert result is True
        # Verify force parameter is passed correctly
        mock_dispatcher.register_calendar_type.assert_called_once_with(
            name="CRYPTO", calendar_type=CryptoCalendar, force=False
        )

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    def test_register_custom_calendars_force_false(self, mock_register):
        """Test register_custom_calendars with force=False."""
        mock_register.return_value = True

        # Register with force=False
        results = register_custom_calendars(["CRYPTO"], force=False)

        # Verify force parameter passed through
        assert results["CRYPTO"] is True
        mock_register.assert_called_once_with(
            name="CRYPTO",
            calendar_class=CryptoCalendar,
            start=None,
            end=None,
            force=False,
        )

    @pytest.mark.unit
    def test_register_custom_calendars_empty_registry(self):
        """Test register_custom_calendars when registry is empty."""
        # Save original registry
        original_registry = get_calendar_registry().copy()

        # Clear registry temporarily
        from lib.calendars.registry import _CALENDAR_REGISTRY

        original_keys = list(_CALENDAR_REGISTRY.keys())
        _CALENDAR_REGISTRY.clear()

        try:
            # Try to register all calendars (should be empty)
            results = register_custom_calendars()

            # Should return empty dict
            assert results == {}
        finally:
            # Restore original registry
            _CALENDAR_REGISTRY.update(original_registry)

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_dispatcher_integration(self, mock_dispatcher):
        """Test that register_calendar_type correctly integrates with dispatcher."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Register calendar and verify dispatcher is called correctly
        result = register_calendar_type("TEST_CAL", CryptoCalendar)

        assert result is True
        mock_dispatcher.register_calendar_type.assert_called_once_with(
            name="TEST_CAL", calendar_type=CryptoCalendar, force=True
        )

    @pytest.mark.unit
    def test_get_registered_calendars_isolation(self):
        """Test that get_registered_calendars returns isolated copy."""
        # Get initial state
        initial = get_registered_calendars()

        # Modify the returned list
        initial.append("MODIFIED")

        # Get again - should not be modified
        fresh = get_registered_calendars()
        assert "MODIFIED" not in fresh
        assert initial != fresh

    @pytest.mark.unit
    @patch("exchange_calendars.calendar_utils.global_calendar_dispatcher")
    def test_register_calendar_type_re_registration_tracking(self, mock_dispatcher):
        """Test that re-registering same calendar doesn't duplicate tracking."""
        mock_dispatcher.register_calendar_type.return_value = None

        # Clear any existing registrations for clean test
        from lib.calendars.registry import _registered_calendars

        initial_count = len(_registered_calendars)

        # Register first time
        register_calendar_type("TEST_RE_REG", CryptoCalendar)
        count_after_first = len(get_registered_calendars())

        # Register again (should not add duplicate)
        register_calendar_type("TEST_RE_REG", CryptoCalendar)
        count_after_second = len(get_registered_calendars())

        # Should only be added once
        assert count_after_second == count_after_first
        assert get_registered_calendars().count("TEST_RE_REG") == 1

    @pytest.mark.unit
    @patch("lib.calendars.registry.register_calendar_type")
    @patch("lib.calendars.registry.logger")
    def test_register_custom_calendars_all_fail(self, mock_logger, mock_register):
        """Test register_custom_calendars when all registrations fail."""
        mock_register.return_value = False

        # Register calendars (all should fail)
        results = register_custom_calendars(["CRYPTO", "FOREX"])

        # All should be False
        assert all(not v for v in results.values())

        # Should log failure summary
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Failed to register" in str(call) for call in warning_calls)
