"""
Tests for lib.logging.error_codes module.

Tests error code definitions and properties.
"""

import pytest

from lib.logging.error_codes import (
    ErrorCode,
    ErrorCodeInfo,
)


class TestErrorCodeInfo:
    """Test ErrorCodeInfo NamedTuple."""

    def test_error_code_info_creation(self):
        """Test creating ErrorCodeInfo."""
        info = ErrorCodeInfo(
            code="TEST_001",
            category="test",
            description="Test error",
        )

        assert info.code == "TEST_001"
        assert info.category == "test"
        assert info.description == "Test error"


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_error_code_properties(self):
        """Test error code properties."""
        error = ErrorCode.DATA_LOAD_FAILED

        assert error.code == "DATA_001"
        assert error.category == "data"
        assert error.description == "Failed to load data from source"

    def test_error_code_str(self):
        """Test error code string representation."""
        error = ErrorCode.DATA_LOAD_FAILED

        assert str(error) == "DATA_001: Failed to load data from source"

    def test_error_code_categories(self):
        """Test that error codes are properly categorized."""
        # Data errors
        assert ErrorCode.DATA_LOAD_FAILED.category == "data"
        assert ErrorCode.DATA_MISSING.category == "data"

        # Validation errors
        assert ErrorCode.VALIDATION_ERROR.category == "validation"
        assert ErrorCode.VALIDATION_SCHEMA_ERROR.category == "validation"

        # Configuration errors
        assert ErrorCode.CONFIG_LOAD_ERROR.category == "config"

        # Strategy errors
        assert ErrorCode.STRATEGY_LOAD_ERROR.category == "strategy"

        # Backtest errors
        assert ErrorCode.BACKTEST_INIT_ERROR.category == "backtest"

        # Optimization errors
        assert ErrorCode.OPTIMIZATION_ERROR.category == "optimization"

        # Metrics errors
        assert ErrorCode.METRICS_CALCULATION_ERROR.category == "metrics"

        # IO errors
        assert ErrorCode.IO_READ_ERROR.category == "io"

        # Network errors
        assert ErrorCode.NETWORK_ERROR.category == "network"

        # General errors
        assert ErrorCode.UNKNOWN_ERROR.category == "general"

    def test_error_code_uniqueness(self):
        """Test that error codes are unique."""
        codes = [error.code for error in ErrorCode]
        assert len(codes) == len(set(codes))  # All unique

    def test_all_error_codes_have_info(self):
        """Test that all error codes have complete information."""
        for error in ErrorCode:
            assert error.code is not None
            assert error.category is not None
            assert error.description is not None
            assert len(error.code) > 0
            assert len(error.category) > 0
            assert len(error.description) > 0
