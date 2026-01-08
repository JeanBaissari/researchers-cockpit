"""
Test utility functions.

Tests for utility functions.
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

from lib.utils import normalize_to_calendar_timezone, get_project_root


class TestUtilityFunctions:
    """Test utility functions."""
    
    @pytest.mark.unit
    def test_normalize_to_calendar_timezone(self):
        """Test normalize_to_calendar_timezone function."""
        dt = pd.Timestamp('2024-01-01 12:00:00', tz='UTC')
        result = normalize_to_calendar_timezone(dt)
        
        assert result.tz is None, "Result should be timezone-naive"
    
    @pytest.mark.unit
    def test_get_project_root(self):
        """Test get_project_root function."""
        root = get_project_root()
        assert root is not None
        assert root.exists()

