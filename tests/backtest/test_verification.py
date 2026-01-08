"""
Test backtest verification.

Tests for backtest results validation and verification.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import validate_backtest_results, ValidationResult


class TestBacktestValidation:
    """Test backtest validation."""
    
    @pytest.mark.unit
    def test_validate_backtest_results(self, sample_backtest_results):
        """Test validating backtest results."""
        result = validate_backtest_results(
            sample_backtest_results,
            returns=sample_backtest_results['returns'],
            transactions=sample_backtest_results['transactions'],
            positions=sample_backtest_results['positions']
        )
        
        assert result is not None
        assert isinstance(result, ValidationResult)

