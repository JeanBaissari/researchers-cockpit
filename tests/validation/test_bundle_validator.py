"""
Test BundleValidator.

Tests for bundle validation operations.
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
    BundleValidator,
    ValidationConfig,
    ValidationResult,
)


class TestBundleValidator:
    """Test BundleValidator."""
    
    @pytest.mark.unit
    def test_bundle_validator_creation(self):
        """Test creating BundleValidator."""
        config = ValidationConfig()
        validator = BundleValidator(config=config)
        assert validator is not None
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_bundle_validator_validate_nonexistent_bundle(self, temp_data_dir):
        """Test validating nonexistent bundle."""
        config = ValidationConfig()
        validator = BundleValidator(config=config)
        result = validator.validate('nonexistent_bundle', bundle_path=temp_data_dir)
        assert isinstance(result, ValidationResult)
        # Should fail for nonexistent bundle
        assert not result.passed

