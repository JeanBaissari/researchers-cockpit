"""
Tests for lib.logging.utils module.

Tests utility functions for structured logging, exception logging, and validation result logging.
"""

import logging
from io import StringIO
from unittest.mock import MagicMock

import pytest

from lib.logging.utils import (
    log_with_context,
    log_exception,
    log_validation_result,
    integrate_zipline_loggers,
    get_zipline_loggers,
)
from lib.logging.error_codes import ErrorCode


class TestLogWithContext:
    """Test log_with_context utility function."""

    def test_log_with_context_basic(self):
        """Test basic log_with_context functionality."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        log_with_context(logger, logging.INFO, "Test message")

        # Should not raise
        assert True

    def test_log_with_context_with_extra_fields(self):
        """Test log_with_context with additional fields."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        log_with_context(
            logger,
            logging.INFO,
            "Test message",
            field1="value1",
            field2=42,
        )

        # Verify extra fields were added to record
        # (actual verification would require custom handler)
        assert True

    def test_log_with_context_with_error_code(self):
        """Test log_with_context with error code."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        log_with_context(
            logger,
            logging.ERROR,
            "Test error",
            error_code=ErrorCode.DATA_LOAD_FAILED,
        )

        # Should not raise
        assert True

    def test_log_with_context_string_level(self):
        """Test log_with_context with string log level."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        log_with_context(logger, "INFO", "Test message")

        # Should not raise
        assert True

    def test_log_with_context_invalid_level(self):
        """Test log_with_context rejects invalid log level."""
        logger = logging.getLogger("test_logger")

        with pytest.raises(ValueError, match="Invalid log level"):
            log_with_context(logger, "INVALID", "Test message")


class TestLogException:
    """Test log_exception utility function."""

    def test_log_exception_basic(self):
        """Test basic log_exception functionality."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            log_exception(logger, "Test error message", exc=e)

        # Should not raise
        assert True

    def test_log_exception_without_exc(self):
        """Test log_exception without explicit exception (uses sys.exc_info)."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except ValueError:
            log_exception(logger, "Test error message")

        # Should not raise
        assert True

    def test_log_exception_with_error_code(self):
        """Test log_exception with error code."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            log_exception(
                logger,
                "Test error message",
                exc=e,
                error_code=ErrorCode.DATA_LOAD_FAILED,
            )

        # Should not raise
        assert True

    def test_log_exception_with_extra_fields(self):
        """Test log_exception with additional context fields."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            log_exception(
                logger,
                "Test error message",
                exc=e,
                data_source="yahoo",
                bundle_name="test_bundle",
            )

        # Should not raise
        assert True

    def test_log_exception_without_traceback(self):
        """Test log_exception without traceback."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            log_exception(
                logger,
                "Test error message",
                exc=e,
                include_traceback=False,
            )

        # Should not raise
        assert True


class TestLogValidationResult:
    """Test log_validation_result utility function."""

    def test_log_validation_result_valid(self):
        """Test logging valid validation result."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Mock validation result
        result = MagicMock()
        result.is_valid = True
        result.errors = []
        result.warnings = []
        result.fix_suggestions = []

        log_validation_result(logger, result)

        # Should not raise
        assert True

    def test_log_validation_result_with_warnings(self):
        """Test logging validation result with warnings."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Mock validation result with warnings
        result = MagicMock()
        result.is_valid = True
        result.errors = []
        result.warnings = ["Warning 1", "Warning 2"]
        result.fix_suggestions = []

        log_validation_result(logger, result)

        # Should not raise
        assert True

    def test_log_validation_result_with_errors(self):
        """Test logging validation result with errors."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Mock validation result with errors
        result = MagicMock()
        result.is_valid = False
        result.errors = ["Error 1", "Error 2"]
        result.warnings = []
        result.fix_suggestions = ["Fix 1"]

        log_validation_result(logger, result)

        # Should not raise
        assert True

    def test_log_validation_result_without_details(self):
        """Test logging validation result without detailed information."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Mock validation result
        result = MagicMock()
        result.is_valid = False
        result.errors = ["Error 1", "Error 2"]
        result.warnings = ["Warning 1"]
        result.fix_suggestions = ["Fix 1"]

        log_validation_result(logger, result, include_details=False)

        # Should not raise
        assert True

    def test_log_validation_result_missing_attributes(self):
        """Test logging validation result with missing attributes."""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Mock validation result without all attributes
        result = MagicMock()
        del result.is_valid
        del result.errors
        del result.warnings

        log_validation_result(logger, result)

        # Should not raise (gracefully handles missing attributes)
        assert True


class TestIntegrateZiplineLoggers:
    """Test integrate_zipline_loggers utility function."""

    def test_integrate_zipline_loggers_basic(self):
        """Test basic Zipline logger integration."""
        from lib.logging import configure_logging

        # Configure project logging first
        configure_logging(level="INFO", console=False, file=False)

        # Integrate Zipline loggers
        integrate_zipline_loggers(
            blotter_level="INFO",
            zipline_level="WARNING",
            portal_level="INFO",
        )

        # Verify loggers exist and have correct levels
        blotter_logger = logging.getLogger("Blotter")
        zipline_logger = logging.getLogger("ZiplineLog")
        portal_logger = logging.getLogger("DataPortal")

        assert blotter_logger.level == logging.INFO
        assert zipline_logger.level == logging.WARNING
        assert portal_logger.level == logging.INFO

    def test_integrate_zipline_loggers_with_handlers(self):
        """Test Zipline logger integration with project handlers."""
        from lib.logging import configure_logging

        # Configure project logging with handlers
        configure_logging(level="INFO", console=False, file=False)
        root_logger = logging.getLogger("cockpit")

        # Add a test handler
        test_handler = logging.StreamHandler(StringIO())
        root_logger.addHandler(test_handler)

        # Integrate Zipline loggers
        integrate_zipline_loggers(
            blotter_level="INFO",
            use_project_handlers=True,
        )

        # Verify handlers were added
        blotter_logger = logging.getLogger("Blotter")
        assert len(blotter_logger.handlers) > 0
        assert blotter_logger.propagate is False

    def test_integrate_zipline_loggers_without_handlers(self):
        """Test Zipline logger integration without project handlers."""
        from lib.logging import configure_logging

        # Configure project logging
        configure_logging(level="INFO", console=False, file=False)

        # Integrate with use_project_handlers=False
        integrate_zipline_loggers(
            blotter_level="INFO",
            use_project_handlers=False,
        )

        # Verify propagation is enabled
        blotter_logger = logging.getLogger("Blotter")
        assert blotter_logger.propagate is True

    def test_integrate_zipline_loggers_all_levels(self):
        """Test Zipline logger integration with all log levels."""
        from lib.logging import configure_logging

        configure_logging(level="INFO", console=False, file=False)

        # Test all log levels
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            integrate_zipline_loggers(
                blotter_level=level,
                zipline_level=level,
                portal_level=level,
            )

            blotter_logger = logging.getLogger("Blotter")
            expected_level = getattr(logging, level)
            assert blotter_logger.level == expected_level

    def test_integrate_zipline_loggers_invalid_level(self):
        """Test Zipline logger integration rejects invalid log level."""
        from lib.logging import configure_logging

        configure_logging(level="INFO", console=False, file=False)

        with pytest.raises(ValueError, match="Invalid log level"):
            integrate_zipline_loggers(blotter_level="INVALID")

    def test_integrate_zipline_loggers_no_project_logging(self):
        """Test Zipline logger integration warns when project logging not configured."""
        import warnings

        # Clear any existing cockpit logger
        root_logger = logging.getLogger("cockpit")
        root_logger.handlers = []

        # Should warn but not fail
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            integrate_zipline_loggers(
                blotter_level="INFO",
                use_project_handlers=True,
            )

            # Should have warned
            assert len(w) > 0
            assert "Project logging not configured" in str(w[0].message)

        # Should fall back to propagation
        blotter_logger = logging.getLogger("Blotter")
        assert blotter_logger.propagate is True


class TestGetZiplineLoggers:
    """Test get_zipline_loggers utility function."""

    def test_get_zipline_loggers_basic(self):
        """Test getting Zipline logger references."""
        loggers = get_zipline_loggers()

        # Verify all loggers are present
        assert "Blotter" in loggers
        assert "ZiplineLog" in loggers
        assert "DataPortal" in loggers

        # Verify they are logging.Logger instances
        assert isinstance(loggers["Blotter"], logging.Logger)
        assert isinstance(loggers["ZiplineLog"], logging.Logger)
        assert isinstance(loggers["DataPortal"], logging.Logger)

    def test_get_zipline_loggers_same_instances(self):
        """Test that get_zipline_loggers returns same logger instances."""
        loggers1 = get_zipline_loggers()
        loggers2 = get_zipline_loggers()

        # Should return same instances (loggers are singletons)
        assert loggers1["Blotter"] is loggers2["Blotter"]
        assert loggers1["ZiplineLog"] is loggers2["ZiplineLog"]
        assert loggers1["DataPortal"] is loggers2["DataPortal"]

    def test_get_zipline_loggers_can_configure(self):
        """Test that returned loggers can be configured."""
        loggers = get_zipline_loggers()

        # Configure a logger
        loggers["Blotter"].setLevel(logging.DEBUG)

        # Verify configuration persists
        assert logging.getLogger("Blotter").level == logging.DEBUG
