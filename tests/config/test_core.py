"""
Test core configuration.

Tests for configuration loading and validation.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import load_strategy_params, load_settings


class TestConfigLoading:
    """Test configuration loading."""
    
    @pytest.mark.unit
    def test_load_strategy_params_function(self):
        """Test load_strategy_params function works."""
        # Test that the function exists and can be called
        try:
            result = load_strategy_params('_template')
            assert isinstance(result, dict), "load_strategy_params should return dict"
        except FileNotFoundError:
            # Expected if template params don't exist
            pass
        except Exception as e:
            pytest.fail(f"load_strategy_params raised unexpected error: {e}")
    
    @pytest.mark.unit
    def test_load_settings(self):
        """Test load_settings function."""
        settings = load_settings()
        assert settings is not None

