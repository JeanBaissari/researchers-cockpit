"""
Test crypto calendar.

Tests for crypto calendar functionality.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.calendars import CryptoCalendar, register_custom_calendars


class TestCryptoCalendar:
    """Tests for CRYPTO calendar configuration."""
    
    @pytest.mark.unit
    def test_crypto_calendar_24_7(self):
        """Test CRYPTO calendar operates 24/7."""
        register_custom_calendars(['CRYPTO'])
        
        start = pd.Timestamp('2025-12-01')
        end = pd.Timestamp('2025-12-31')
        crypto = CryptoCalendar(start=start, end=end)
        
        # Should have sessions on weekends
        weekend_dates = [d for d in crypto.sessions if d.dayofweek >= 5]
        assert len(weekend_dates) > 0, "CRYPTO should have weekend sessions"

