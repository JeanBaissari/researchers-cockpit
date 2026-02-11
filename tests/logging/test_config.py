"""
Tests for lib.logging.config module.

Tests logging configuration, logger creation, and shutdown functionality.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from lib.logging.config import (
    configure_logging,
    shutdown_logging,
    get_logger,
    LogLevel,
    _validate_log_level,
    _get_logging_level,
)


class TestLogLevelValidation:
    """Test log level validation and conversion."""

    def test_validate_log_level_valid(self):
        """Test validation of valid log levels."""
        assert _validate_log_level("DEBUG") == "DEBUG"
        assert _validate_log_level("INFO") == "INFO"
        assert _validate_log_level("WARNING") == "WARNING"
        assert _validate_log_level("ERROR") == "ERROR"
        assert _validate_log_level("CRITICAL") == "CRITICAL"

        # Case insensitive
        assert _validate_log_level("debug") == "DEBUG"
        assert _validate_log_level("Info") == "INFO"

    def test_validate_log_level_invalid(self):
        """Test validation rejects invalid log levels."""
        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level("INVALID")

        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level("")

    def test_get_logging_level(self):
        """Test conversion of log level string to logging constant."""
        assert _get_logging_level("DEBUG") == logging.DEBUG
        assert _get_logging_level("INFO") == logging.INFO
        assert _get_logging_level("WARNING") == logging.WARNING
        assert _get_logging_level("ERROR") == logging.ERROR
        assert _get_logging_level("CRITICAL") == logging.CRITICAL


class TestConfigureLogging:
    """Test logging configuration."""

    def test_configure_logging_defaults(self):
        """Test default logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = configure_logging(
                level="INFO",
                log_dir=log_dir,
                console=True,
                file=True,
            )

            assert logger.name == "cockpit"
            assert logger.level == logging.INFO
            assert len(logger.handlers) == 2  # Console + file

            # Cleanup
            shutdown_logging()

    def test_configure_logging_console_only(self):
        """Test console-only logging configuration."""
        logger = configure_logging(
            level="DEBUG",
            console=True,
            file=False,
        )

        assert logger.name == "cockpit"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1  # Console only

        # Cleanup
        shutdown_logging()

    def test_configure_logging_file_only(self):
        """Test file-only logging configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = configure_logging(
                level="WARNING",
                log_dir=log_dir,
                console=False,
                file=True,
            )

            assert logger.name == "cockpit"
            assert logger.level == logging.WARNING
            assert len(logger.handlers) == 1  # File only

            # Cleanup
            shutdown_logging()

    def test_configure_logging_with_context(self):
        """Test logging configuration with context values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = configure_logging(
                level="INFO",
                log_dir=log_dir,
                strategy_name="test_strategy",
                run_id="test_run_123",
                asset_type="crypto",
                bundle_name="test_bundle",
                timeframe="daily",
            )

            assert logger.name == "cockpit"

            # Verify context was set (import here to avoid circular import)
            from lib.logging.formatters import get_context_value

            assert get_context_value("strategy") == "test_strategy"
            assert get_context_value("run_id") == "test_run_123"
            assert get_context_value("asset_type") == "crypto"
            assert get_context_value("bundle_name") == "test_bundle"
            assert get_context_value("timeframe") == "daily"

            # Cleanup
            shutdown_logging()
            from lib.logging.context import reset_context

            reset_context()

    def test_configure_logging_invalid_level(self):
        """Test configuration rejects invalid log levels."""
        with pytest.raises(ValueError, match="Invalid log level"):
            configure_logging(level="INVALID")

    def test_configure_logging_reconfigures(self):
        """Test that reconfiguration replaces existing handlers."""
        logger1 = configure_logging(level="DEBUG", console=True, file=False)
        initial_handlers = len(logger1.handlers)

        logger2 = configure_logging(level="INFO", console=True, file=False)

        # Should have same number of handlers (reconfigured, not added)
        assert len(logger2.handlers) == initial_handlers
        assert logger2.level == logging.INFO

        # Cleanup
        shutdown_logging()

    def test_configure_logging_structured_file(self):
        """Test structured JSON file logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = configure_logging(
                level="INFO",
                log_dir=log_dir,
                console=False,
                file=True,
                structured=True,
            )

            # Log a message
            logger.info("Test structured logging")

            # Verify file was created
            log_files = list(log_dir.glob("cockpit_*.log"))
            assert len(log_files) > 0

            # Cleanup
            shutdown_logging()


class TestShutdownLogging:
    """Test logging shutdown functionality."""

    def test_shutdown_logging_clears_handlers(self):
        """Test that shutdown clears all handlers."""
        logger = configure_logging(level="INFO", console=True, file=False)
        assert len(logger.handlers) > 0

        shutdown_logging()

        assert len(logger.handlers) == 0

    def test_shutdown_logging_multiple_calls(self):
        """Test that multiple shutdown calls are safe."""
        configure_logging(level="INFO", console=True, file=False)
        shutdown_logging()
        shutdown_logging()  # Should not raise


class TestGetLogger:
    """Test logger creation."""

    def test_get_logger_creates_cockpit_namespace(self):
        """Test that get_logger creates loggers with cockpit namespace."""
        logger = get_logger("test_module")

        assert logger.name == "cockpit.test_module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_different_modules(self):
        """Test that different modules get different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "cockpit.module1"
        assert logger2.name == "cockpit.module2"
        assert logger1 is not logger2

    def test_get_logger_same_module_returns_same_logger(self):
        """Test that same module name returns same logger instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2
