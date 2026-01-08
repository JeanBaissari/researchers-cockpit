"""
Test BacktestValidator.

Tests for backtest results validation.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import (
    BacktestValidator,
    ValidationConfig,
    ValidationResult,
)


class TestBacktestValidator:
    """Test BacktestValidator."""
    
    @pytest.mark.unit
    def test_backtest_validator_creation(self):
        """Test creating BacktestValidator."""
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        assert validator is not None
    
    @pytest.mark.unit
    def test_backtest_validator_validate_results(self, sample_backtest_results):
        """Test validating backtest results."""
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        result = validator.validate(
            sample_backtest_results,
            returns=sample_backtest_results['returns'],
            transactions=sample_backtest_results['transactions'],
            positions=sample_backtest_results['positions']
        )
        assert isinstance(result, ValidationResult)
    
    @pytest.mark.unit
    def test_backtest_validator_validate_invalid_results(self):
        """Test validating invalid backtest results."""
        invalid_results = {
            'sharpe_ratio': 999,  # Unrealistic
            'max_drawdown': 0.5,  # Should be negative
            'total_return': -2.0,  # Total loss
        }
        
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        result = validator.validate(invalid_results)
        assert isinstance(result, ValidationResult)

