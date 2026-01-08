"""
Test SchemaValidator.

Tests for schema validation operations.
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
    SchemaValidator,
    ValidationConfig,
    ValidationResult,
    REQUIRED_OHLCV_COLUMNS,
)


class TestSchemaValidator:
    """Test SchemaValidator."""
    
    @pytest.mark.unit
    def test_schema_validator_creation(self):
        """Test creating SchemaValidator."""
        validator = SchemaValidator()
        assert validator is not None
    
    @pytest.mark.unit
    def test_schema_validator_validate_ohlcv_schema(self, valid_ohlcv_data):
        """Test validating OHLCV schema."""
        validator = SchemaValidator()
        
        # Validate that data has required columns
        required_cols = set(REQUIRED_OHLCV_COLUMNS)
        data_cols = set(valid_ohlcv_data.columns)
        has_required = required_cols.issubset(data_cols)
        
        assert has_required is True

