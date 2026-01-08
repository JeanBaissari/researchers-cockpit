"""
Test walk-forward validation.

Tests for walk-forward validation.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validate import walk_forward


class TestWalkForwardValidator:
    """Test walk-forward validation."""
    
    @pytest.mark.unit
    def test_walk_forward_function_exists(self):
        """Test that walk_forward function exists."""
        assert walk_forward is not None
        assert callable(walk_forward)
    
    @pytest.mark.unit
    @pytest.mark.slow
    def test_walk_forward_function_signature(self):
        """Test walk_forward has correct signature."""
        import inspect
        sig = inspect.signature(walk_forward)
        params = list(sig.parameters.keys())
        
        # Should have parameters
        assert len(params) > 0

