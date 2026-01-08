"""
Test CompositeValidator.

Tests for composite validation operations.
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
    CompositeValidator,
    DataValidator,
    SchemaValidator,
    ValidationConfig,
    ValidationResult,
)


class TestCompositeValidator:
    """Test CompositeValidator."""
    
    @pytest.mark.unit
    def test_composite_validator_creation(self):
        """Test creating CompositeValidator."""
        config = ValidationConfig(timeframe='1d')
        validators = [
            DataValidator(config=config),
            SchemaValidator(),
        ]
        composite = CompositeValidator(validators)
        assert composite is not None
    
    @pytest.mark.unit
    def test_composite_validator_validate(self, valid_ohlcv_data):
        """Test CompositeValidator validation."""
        config = ValidationConfig(timeframe='1d')
        validators = [
            DataValidator(config=config),
        ]
        composite = CompositeValidator(validators)
        result = composite.validate(valid_ohlcv_data, asset_name='TEST')
        assert isinstance(result, ValidationResult)

