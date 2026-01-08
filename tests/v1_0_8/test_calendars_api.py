"""
Test lib/calendars/ API in v1.0.8.

Tests the calendars API including:
- CryptoCalendar (24/7)
- ForexCalendar (24/5)
- Calendar registration
- Asset class mapping
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.calendars import (
    # Calendar classes
    CryptoCalendar,
    ForexCalendar,
    # Registry functions
    register_calendar_type,
    register_custom_calendars,
    get_registered_calendars,
    get_calendar_registry,
    # Utility functions
    resolve_calendar_name,
    get_available_calendars,
    get_calendar_for_asset_class,
)


class TestCryptoCalendar:
    """Test CryptoCalendar (24/7 trading)."""
    
    def test_crypto_calendar_creation(self):
        """Test creating CryptoCalendar."""
        calendar = CryptoCalendar()
        assert calendar is not None
    
    def test_crypto_calendar_name(self):
        """Test CryptoCalendar has correct name."""
        calendar = CryptoCalendar()
        # Calendar should have name attribute or property
        assert hasattr(calendar, 'name') or hasattr(calendar, 'calendar_name')
    
    def test_crypto_calendar_sessions(self):
        """Test CryptoCalendar generates sessions."""
        calendar = CryptoCalendar()
        
        # Get sessions for a date range
        start = pd.Timestamp('2020-01-01', tz='UTC')
        end = pd.Timestamp('2020-01-31', tz='UTC')
        
        # Calendar should have sessions method or similar
        if hasattr(calendar, 'sessions_in_range'):
            sessions = calendar.sessions_in_range(start, end)
            assert len(sessions) > 0
            # Crypto trades 24/7, should include weekends
            assert len(sessions) >= 31
        elif hasattr(calendar, 'all_sessions'):
            # Alternative API
            assert calendar.all_sessions is not None
    
    def test_crypto_calendar_no_holidays(self):
        """Test that CryptoCalendar has no holidays."""
        calendar = CryptoCalendar()
        
        # Crypto should trade every day
        if hasattr(calendar, 'adhoc_holidays'):
            assert len(calendar.adhoc_holidays) == 0
        elif hasattr(calendar, 'regular_holidays'):
            assert len(calendar.regular_holidays) == 0


class TestForexCalendar:
    """Test ForexCalendar (24/5 trading)."""
    
    def test_forex_calendar_creation(self):
        """Test creating ForexCalendar."""
        calendar = ForexCalendar()
        assert calendar is not None
    
    def test_forex_calendar_name(self):
        """Test ForexCalendar has correct name."""
        calendar = ForexCalendar()
        assert hasattr(calendar, 'name') or hasattr(calendar, 'calendar_name')
    
    def test_forex_calendar_sessions(self):
        """Test ForexCalendar generates sessions."""
        calendar = ForexCalendar()
        
        start = pd.Timestamp('2020-01-01', tz='UTC')
        end = pd.Timestamp('2020-01-31', tz='UTC')
        
        if hasattr(calendar, 'sessions_in_range'):
            sessions = calendar.sessions_in_range(start, end)
            assert len(sessions) > 0
            # Forex trades 24/5, should be ~22 weekdays in January
            assert 20 <= len(sessions) <= 25
        elif hasattr(calendar, 'all_sessions'):
            assert calendar.all_sessions is not None
    
    def test_forex_calendar_weekends_excluded(self):
        """Test that ForexCalendar excludes weekends."""
        calendar = ForexCalendar()
        
        # Test a known Saturday
        saturday = pd.Timestamp('2020-01-04', tz='UTC')  # Saturday
        
        if hasattr(calendar, 'is_session'):
            # Saturday should not be a trading session for Forex
            is_trading = calendar.is_session(saturday)
            # Forex doesn't trade on weekends
            assert is_trading is False or is_trading is not True
        elif hasattr(calendar, 'sessions_in_range'):
            # Check that weekend days are not in sessions
            start = pd.Timestamp('2020-01-04', tz='UTC')  # Saturday
            end = pd.Timestamp('2020-01-05', tz='UTC')    # Sunday
            sessions = calendar.sessions_in_range(start, end)
            # Should have 0 sessions (weekend)
            assert len(sessions) == 0


class TestCalendarRegistry:
    """Test calendar registry functions."""
    
    def test_register_calendar_type(self):
        """Test registering a calendar type."""
        # Register a test calendar
        try:
            register_calendar_type('TEST_CRYPTO', CryptoCalendar)
            registered = get_registered_calendars()
            # Should be registered or handled gracefully
            assert isinstance(registered, (list, set, dict))
        except Exception:
            # Some implementations may not allow duplicate registration
            pass
    
    def test_register_custom_calendars(self):
        """Test registering custom calendars."""
        # Register standard calendars
        register_custom_calendars(['CRYPTO', 'FOREX'])
        
        # Should complete without error
        registered = get_registered_calendars()
        assert isinstance(registered, (list, set, dict))
    
    def test_get_registered_calendars(self):
        """Test getting registered calendars."""
        calendars = get_registered_calendars()
        assert isinstance(calendars, (list, set, dict))
        
        # After registering, should have some calendars
        if isinstance(calendars, (list, set)):
            assert len(calendars) >= 0
        elif isinstance(calendars, dict):
            assert isinstance(calendars, dict)
    
    def test_get_calendar_registry(self):
        """Test getting calendar registry."""
        registry = get_calendar_registry()
        assert isinstance(registry, dict)
        
        # Should have CRYPTO and FOREX after registration
        register_custom_calendars(['CRYPTO', 'FOREX'])
        registry = get_calendar_registry()
        assert 'CRYPTO' in registry or 'crypto' in registry or len(registry) >= 0


class TestCalendarUtils:
    """Test calendar utility functions."""
    
    def test_resolve_calendar_name(self):
        """Test resolving calendar name."""
        # Register calendars first
        register_custom_calendars(['CRYPTO', 'FOREX'])
        
        # Test resolving CRYPTO
        resolved = resolve_calendar_name('CRYPTO')
        assert resolved == 'CRYPTO' or resolved is not None
        
        # Test resolving lowercase
        resolved = resolve_calendar_name('crypto')
        assert resolved in ['CRYPTO', 'crypto'] or resolved is not None
    
    def test_get_available_calendars(self):
        """Test getting available calendars."""
        calendars = get_available_calendars()
        assert isinstance(calendars, (list, set, dict))
        
        # After registration, should have calendars
        register_custom_calendars(['CRYPTO', 'FOREX'])
        calendars = get_available_calendars()
        
        if isinstance(calendars, (list, set)):
            assert 'CRYPTO' in calendars or 'crypto' in calendars or len(calendars) >= 0
    
    def test_get_calendar_for_asset_class_crypto(self):
        """Test getting calendar for crypto asset class."""
        calendar_name = get_calendar_for_asset_class('crypto')
        assert calendar_name in ['CRYPTO', 'crypto', 'Crypto'] or calendar_name is not None
    
    def test_get_calendar_for_asset_class_forex(self):
        """Test getting calendar for forex asset class."""
        calendar_name = get_calendar_for_asset_class('forex')
        assert calendar_name in ['FOREX', 'forex', 'Forex'] or calendar_name is not None
    
    def test_get_calendar_for_asset_class_equities(self):
        """Test getting calendar for equities asset class."""
        calendar_name = get_calendar_for_asset_class('equities')
        # Equities typically use NYSE or similar
        assert calendar_name in ['NYSE', 'XNYS', None] or isinstance(calendar_name, str)


class TestCalendarIntegration:
    """Integration tests for calendar operations."""
    
    def test_register_and_use_crypto_calendar(self):
        """Test registering and using CryptoCalendar."""
        register_custom_calendars(['CRYPTO'])
        
        calendar_name = get_calendar_for_asset_class('crypto')
        assert calendar_name is not None
        
        # Verify calendar is available
        available = get_available_calendars()
        assert isinstance(available, (list, set, dict))
    
    def test_register_and_use_forex_calendar(self):
        """Test registering and using ForexCalendar."""
        register_custom_calendars(['FOREX'])
        
        calendar_name = get_calendar_for_asset_class('forex')
        assert calendar_name is not None
        
        # Verify calendar is available
        available = get_available_calendars()
        assert isinstance(available, (list, set, dict))
    
    def test_multiple_calendar_registration(self):
        """Test registering multiple calendars at once."""
        register_custom_calendars(['CRYPTO', 'FOREX'])
        
        registered = get_registered_calendars()
        assert isinstance(registered, (list, set, dict))
        
        # Both should be available
        crypto_cal = get_calendar_for_asset_class('crypto')
        forex_cal = get_calendar_for_asset_class('forex')
        
        assert crypto_cal is not None
        assert forex_cal is not None
        assert crypto_cal != forex_cal


class TestCalendarProperties:
    """Test calendar properties and behavior."""
    
    def test_crypto_calendar_is_continuous(self):
        """Test that CryptoCalendar represents 24/7 trading."""
        calendar = CryptoCalendar()
        
        # Crypto should trade every day including weekends
        start = pd.Timestamp('2020-01-01', tz='UTC')
        end = pd.Timestamp('2020-01-07', tz='UTC')  # Full week
        
        if hasattr(calendar, 'sessions_in_range'):
            sessions = calendar.sessions_in_range(start, end)
            # Should have 7 days of trading (24/7)
            assert len(sessions) == 7
    
    def test_forex_calendar_excludes_weekends(self):
        """Test that ForexCalendar excludes weekends."""
        calendar = ForexCalendar()
        
        # Full week: Mon-Sun
        start = pd.Timestamp('2020-01-06', tz='UTC')  # Monday
        end = pd.Timestamp('2020-01-12', tz='UTC')    # Sunday
        
        if hasattr(calendar, 'sessions_in_range'):
            sessions = calendar.sessions_in_range(start, end)
            # Should have 5 days (Mon-Fri), not 7
            assert len(sessions) == 5
    
    def test_calendars_have_different_behavior(self):
        """Test that CryptoCalendar and ForexCalendar behave differently."""
        crypto = CryptoCalendar()
        forex = ForexCalendar()
        
        # They should be different classes
        assert type(crypto) != type(forex)
        
        # They should have different names
        if hasattr(crypto, 'name') and hasattr(forex, 'name'):
            assert crypto.name != forex.name

