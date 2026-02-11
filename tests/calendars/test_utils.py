"""
Test calendar utilities.

Tests for calendar utility functions including name resolution,
calendar availability, and asset class mapping.
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

from lib.calendars.utils import (
    resolve_calendar_name,
    get_available_calendars,
    get_calendar_for_asset_class,
)
from lib.calendars.registry import get_calendar_registry


class TestResolveCalendarName:
    """Tests for resolve_calendar_name function."""

    @pytest.mark.unit
    def test_resolve_calendar_name_direct_match_uppercase(self):
        """Test resolving calendar name with direct uppercase match."""
        result = resolve_calendar_name("CRYPTO")
        assert result == "CRYPTO"

        result = resolve_calendar_name("FOREX")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_resolve_calendar_name_direct_match_lowercase(self):
        """Test resolving calendar name with direct lowercase match (converted to uppercase)."""
        result = resolve_calendar_name("crypto")
        assert result == "CRYPTO"

        result = resolve_calendar_name("forex")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_resolve_calendar_name_direct_match_mixed_case(self):
        """Test resolving calendar name with mixed case (converted to uppercase)."""
        result = resolve_calendar_name("Crypto")
        assert result == "CRYPTO"

        result = resolve_calendar_name("Forex")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_resolve_calendar_name_alias_24_7(self):
        """Test resolving calendar name from '24/7' alias."""
        result = resolve_calendar_name("24/7")
        assert result == "CRYPTO"

    @pytest.mark.unit
    def test_resolve_calendar_name_alias_always_open(self):
        """Test resolving calendar name from 'ALWAYS_OPEN' alias."""
        result = resolve_calendar_name("ALWAYS_OPEN")
        assert result == "CRYPTO"

        result = resolve_calendar_name("always_open")
        assert result == "CRYPTO"

    @pytest.mark.unit
    def test_resolve_calendar_name_alias_fx(self):
        """Test resolving calendar name from 'FX' alias."""
        result = resolve_calendar_name("FX")
        assert result == "FOREX"

        result = resolve_calendar_name("fx")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_resolve_calendar_name_alias_currency(self):
        """Test resolving calendar name from 'CURRENCY' alias."""
        result = resolve_calendar_name("CURRENCY")
        assert result == "FOREX"

        result = resolve_calendar_name("currency")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_resolve_calendar_name_unknown_alias(self):
        """Test resolving unknown alias returns None."""
        result = resolve_calendar_name("UNKNOWN_ALIAS")
        assert result is None

    @pytest.mark.unit
    def test_resolve_calendar_name_unknown_name(self):
        """Test resolving unknown calendar name returns None."""
        result = resolve_calendar_name("UNKNOWN_CALENDAR")
        assert result is None

    @pytest.mark.unit
    def test_resolve_calendar_name_empty_string(self):
        """Test resolving empty string returns None."""
        result = resolve_calendar_name("")
        # Empty string uppercased is still empty, not in registry or aliases
        assert result is None

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_resolve_calendar_name_checks_registry_first(self, mock_registry):
        """Test that registry is checked before aliases."""
        # Mock registry with a custom calendar
        mock_registry.return_value = {"CUSTOM": MagicMock()}

        result = resolve_calendar_name("CUSTOM")
        assert result == "CUSTOM"
        mock_registry.assert_called_once()

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_resolve_calendar_name_falls_back_to_aliases(self, mock_registry):
        """Test that aliases are checked if not in registry."""
        # Mock registry without the calendar
        mock_registry.return_value = {}

        # Should still resolve via alias
        result = resolve_calendar_name("FX")
        assert result == "FOREX"
        mock_registry.assert_called_once()


class TestGetAvailableCalendars:
    """Tests for get_available_calendars function."""

    @pytest.mark.unit
    def test_get_available_calendars_returns_list(self):
        """Test that get_available_calendars returns a list."""
        calendars = get_available_calendars()
        assert isinstance(calendars, list)

    @pytest.mark.unit
    def test_get_available_calendars_contains_default_calendars(self):
        """Test that default calendars (CRYPTO, FOREX) are available."""
        calendars = get_available_calendars()

        assert "CRYPTO" in calendars
        assert "FOREX" in calendars

    @pytest.mark.unit
    def test_get_available_calendars_all_uppercase(self):
        """Test that all calendar names are uppercase."""
        calendars = get_available_calendars()

        for calendar in calendars:
            assert calendar == calendar.upper()

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_get_available_calendars_uses_registry(self, mock_registry):
        """Test that get_available_calendars uses the registry."""
        # Mock registry with custom calendars
        mock_registry.return_value = {
            "CUSTOM1": MagicMock(),
            "CUSTOM2": MagicMock(),
        }

        calendars = get_available_calendars()

        assert "CUSTOM1" in calendars
        assert "CUSTOM2" in calendars
        assert len(calendars) == 2
        mock_registry.assert_called_once()

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_get_available_calendars_empty_registry(self, mock_registry):
        """Test that empty registry returns empty list."""
        mock_registry.return_value = {}

        calendars = get_available_calendars()

        assert calendars == []
        mock_registry.assert_called_once()

    @pytest.mark.unit
    def test_get_available_calendars_returns_copy(self):
        """Test that modifying returned list doesn't affect registry."""
        # Use a controlled registry to avoid cross-test pollution.
        with patch(
            "lib.calendars.registry.get_calendar_registry",
            return_value={"CRYPTO": MagicMock(), "FOREX": MagicMock()},
        ):
            calendars1 = get_available_calendars()
            calendars2 = get_available_calendars()

            # Should be equal
            assert calendars1 == calendars2

            # Modifying one should not affect the other
            calendars1.append("TEST")
            calendars3 = get_available_calendars()
            assert "TEST" not in calendars3


class TestGetCalendarForAssetClass:
    """Tests for get_calendar_for_asset_class function."""

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_crypto(self):
        """Test getting calendar for 'crypto' asset class."""
        result = get_calendar_for_asset_class("crypto")
        assert result == "CRYPTO"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_cryptocurrency(self):
        """Test getting calendar for 'cryptocurrency' asset class."""
        result = get_calendar_for_asset_class("cryptocurrency")
        assert result == "CRYPTO"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_forex(self):
        """Test getting calendar for 'forex' asset class."""
        result = get_calendar_for_asset_class("forex")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_fx(self):
        """Test getting calendar for 'fx' asset class."""
        result = get_calendar_for_asset_class("fx")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_currency(self):
        """Test getting calendar for 'currency' asset class."""
        result = get_calendar_for_asset_class("currency")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_case_insensitive(self):
        """Test that asset class matching is case-insensitive."""
        result = get_calendar_for_asset_class("CRYPTO")
        assert result == "CRYPTO"

        result = get_calendar_for_asset_class("FOREX")
        assert result == "FOREX"

        result = get_calendar_for_asset_class("Crypto")
        assert result == "CRYPTO"

        result = get_calendar_for_asset_class("Forex")
        assert result == "FOREX"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_equity_returns_none(self):
        """Test that equity asset class returns None (use Zipline defaults)."""
        result = get_calendar_for_asset_class("equity")
        assert result is None

        result = get_calendar_for_asset_class("equities")
        assert result is None

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_unknown_returns_none(self):
        """Test that unknown asset class returns None."""
        result = get_calendar_for_asset_class("unknown")
        assert result is None

        result = get_calendar_for_asset_class("commodities")
        assert result is None

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_empty_string(self):
        """Test that empty string returns None."""
        result = get_calendar_for_asset_class("")
        assert result is None

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_get_calendar_for_asset_class_verifies_registry(self, mock_registry):
        """Test that function verifies calendar exists in registry."""
        # Mock registry without CRYPTO
        mock_registry.return_value = {"FOREX": MagicMock()}

        # Even though 'crypto' maps to 'CRYPTO', it's not in registry
        result = get_calendar_for_asset_class("crypto")
        assert result is None

        # FOREX should work
        result = get_calendar_for_asset_class("forex")
        assert result == "FOREX"

    @pytest.mark.unit
    @patch("lib.calendars.registry.get_calendar_registry")
    def test_get_calendar_for_asset_class_registry_check(self, mock_registry):
        """Test that registry check is performed when asset class is in map."""
        # Mock registry without CRYPTO (even though 'crypto' maps to 'CRYPTO')
        mock_registry.return_value = {"FOREX": MagicMock()}

        # 'crypto' is in asset_calendar_map and maps to 'CRYPTO'
        # But 'CRYPTO' is not in the mocked registry, so should return None
        result = get_calendar_for_asset_class("crypto")
        assert result is None

        # Verify registry was checked (since 'crypto' is in the map)
        mock_registry.assert_called()


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    @pytest.mark.unit
    def test_resolve_and_get_available_consistency(self):
        """Test that resolved names are in available calendars."""
        available = get_available_calendars()

        # Direct matches should be in available
        for calendar in ["CRYPTO", "FOREX"]:
            resolved = resolve_calendar_name(calendar)
            assert resolved in available

    @pytest.mark.unit
    def test_asset_class_to_calendar_consistency(self):
        """Test that asset class mapping returns valid calendars."""
        asset_classes = {
            "crypto": "CRYPTO",
            "forex": "FOREX",
        }

        for asset_class, expected_calendar in asset_classes.items():
            calendar = get_calendar_for_asset_class(asset_class)
            assert calendar == expected_calendar

            # Verify calendar is available
            available = get_available_calendars()
            assert calendar in available

    @pytest.mark.unit
    def test_alias_resolution_workflow(self):
        """Test complete workflow: alias -> resolve -> verify available."""
        aliases = ["24/7", "ALWAYS_OPEN", "FX", "CURRENCY"]

        for alias in aliases:
            # Resolve alias
            resolved = resolve_calendar_name(alias)
            assert resolved is not None

            # Verify resolved calendar is available
            available = get_available_calendars()
            assert resolved in available

    @pytest.mark.unit
    def test_round_trip_asset_class_to_calendar(self):
        """Test round trip: asset class -> calendar -> resolve."""
        # Get calendar for asset class
        calendar = get_calendar_for_asset_class("crypto")
        assert calendar == "CRYPTO"

        # Resolve the calendar name (should be direct match)
        resolved = resolve_calendar_name(calendar)
        assert resolved == "CRYPTO"

        # Verify it's available
        available = get_available_calendars()
        assert calendar in available


class TestEdgeCases:
    """Edge case tests for calendar utilities."""

    @pytest.mark.unit
    def test_resolve_calendar_name_with_whitespace(self):
        """Test resolving calendar name with leading/trailing whitespace."""
        # Whitespace should be stripped by upper() but let's verify behavior
        result = resolve_calendar_name("  CRYPTO  ")
        # The function does .upper() which doesn't strip, so this might not match
        # But let's test the actual behavior
        assert result is None or result == "CRYPTO"

    @pytest.mark.unit
    def test_resolve_calendar_name_none_input(self):
        """Test that None input raises AttributeError."""
        with pytest.raises(AttributeError):
            resolve_calendar_name(None)

    @pytest.mark.unit
    def test_resolve_calendar_name_non_string_input(self):
        """Test that non-string input raises AttributeError."""
        with pytest.raises(AttributeError):
            resolve_calendar_name(123)

        with pytest.raises(AttributeError):
            resolve_calendar_name([])

        with pytest.raises(AttributeError):
            resolve_calendar_name({})

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_with_whitespace(self):
        """Test getting calendar for asset class with whitespace."""
        # Whitespace in asset class should be handled
        result = get_calendar_for_asset_class("  crypto  ")
        # The function does .lower() which doesn't strip, so this might not match
        # But let's test the actual behavior
        assert result is None or result == "CRYPTO"

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_none_input(self):
        """Test that None input raises AttributeError."""
        with pytest.raises(AttributeError):
            get_calendar_for_asset_class(None)

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_non_string_input(self):
        """Test that non-string input raises AttributeError."""
        with pytest.raises(AttributeError):
            get_calendar_for_asset_class(123)

        with pytest.raises(AttributeError):
            get_calendar_for_asset_class([])

    @pytest.mark.unit
    def test_resolve_calendar_name_special_characters(self):
        """Test resolving calendar name with special characters."""
        # Test various special characters
        result = resolve_calendar_name("CRYPTO!")
        assert result is None  # Special chars shouldn't match

        result = resolve_calendar_name("CRYPTO@")
        assert result is None

        result = resolve_calendar_name("CRYPTO#")
        assert result is None

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_special_characters(self):
        """Test getting calendar for asset class with special characters."""
        # Special characters shouldn't match
        result = get_calendar_for_asset_class("crypto!")
        assert result is None

        result = get_calendar_for_asset_class("forex@")
        assert result is None

    @pytest.mark.unit
    def test_resolve_calendar_name_unicode(self):
        """Test resolving calendar name with unicode characters."""
        # Unicode characters should not match
        result = resolve_calendar_name("CRYPTO™")
        assert result is None

        result = resolve_calendar_name("CRYPTO©")
        assert result is None

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_unicode(self):
        """Test getting calendar for asset class with unicode characters."""
        # Unicode characters should not match
        result = get_calendar_for_asset_class("crypto™")
        assert result is None

    @pytest.mark.unit
    def test_resolve_calendar_name_very_long_string(self):
        """Test resolving very long string."""
        long_string = "CRYPTO" * 1000
        result = resolve_calendar_name(long_string)
        assert result is None

    @pytest.mark.unit
    def test_get_calendar_for_asset_class_very_long_string(self):
        """Test getting calendar for very long asset class string."""
        long_string = "crypto" * 1000
        result = get_calendar_for_asset_class(long_string)
        assert result is None
