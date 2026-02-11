"""
Tests for lib.logging.formatters module.

Tests StructuredFormatter and ConsoleFormatter functionality.
"""

import json
import logging
from io import StringIO

import pytest

from lib.logging.formatters import (
    StructuredFormatter,
    ConsoleFormatter,
)
from lib.logging.context import (
    get_context_value,
    set_context_value,
    clear_context_value,
    reset_context,
)


class TestStructuredFormatter:
    """Test StructuredFormatter for JSON output."""

    def test_structured_formatter_basic(self):
        """Test basic structured formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_structured_formatter_with_context(self):
        """Test structured formatting includes context."""
        reset_context()
        formatter = StructuredFormatter()

        set_context_value("strategy", "test_strategy")
        set_context_value("phase", "backtest")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "context" in data
        assert data["context"]["strategy"] == "test_strategy"
        assert data["context"]["phase"] == "backtest"

        reset_context()

    def test_structured_formatter_with_exception(self):
        """Test structured formatting includes exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path",
                lineno=10,
                msg="Test error",
                args=(),
                exc_info=(type(e), e, e.__traceback__),
            )

            output = formatter.format(record)
            data = json.loads(output)

            assert "exception" in data
            assert data["exception"]["type"] == "ValueError"
            assert "Test exception" in data["exception"]["message"]

    def test_structured_formatter_debug_source(self):
        """Test structured formatting includes source info for DEBUG level."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.DEBUG,
            pathname="/test/path.py",
            lineno=42,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        # Set funcName after creation (LogRecord doesn't accept it in constructor)
        record.funcName = "test_function"

        output = formatter.format(record)
        data = json.loads(output)

        assert "source" in data
        assert data["source"]["file"] == "/test/path.py"
        assert data["source"]["line"] == 42
        assert data["source"]["function"] == "test_function"

    def test_structured_formatter_no_source_for_info(self):
        """Test structured formatting doesn't include source for INFO level."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Info message",
            args=(),
            exc_info=None,
            funcName="test_function",
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "source" not in data


class TestConsoleFormatter:
    """Test ConsoleFormatter for human-readable output."""

    def test_console_formatter_basic(self):
        """Test basic console formatting."""
        formatter = ConsoleFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "Test message" in output
        assert "INFO" in output
        assert "test_logger" in output or "logger" in output

    def test_console_formatter_with_context(self):
        """Test console formatting includes context."""
        reset_context()
        formatter = ConsoleFormatter(use_colors=False)

        set_context_value("strategy", "test_strategy")
        set_context_value("phase", "backtest")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "strategy=test_strategy" in output
        assert "phase=backtest" in output

        reset_context()

    def test_console_formatter_colors(self):
        """Test console formatting with colors."""
        formatter = ConsoleFormatter(use_colors=True)

        # Test different log levels have different colors
        levels = [
            (logging.DEBUG, "\033[2m"),
            (logging.WARNING, "\033[33m"),
            (logging.ERROR, "\033[31m"),
            (logging.CRITICAL, "\033[1;31m"),
        ]

        for level, color_code in levels:
            record = logging.LogRecord(
                name="test_logger",
                level=level,
                pathname="/test/path",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)

            if color_code:
                assert color_code in output
                assert "\033[0m" in output  # Reset code

    def test_console_formatter_no_colors(self):
        """Test console formatting without colors."""
        formatter = ConsoleFormatter(use_colors=False)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should not contain ANSI color codes
        assert "\033[" not in output

    def test_console_formatter_with_exception(self):
        """Test console formatting includes exception traceback."""
        formatter = ConsoleFormatter(use_colors=False)

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/test/path",
                lineno=10,
                msg="Test error",
                args=(),
                exc_info=(type(e), e, e.__traceback__),
            )

            output = formatter.format(record)

            assert "Test error" in output
            assert "ValueError" in output
            assert "Test exception" in output

    def test_console_formatter_logger_name_abbreviation(self):
        """Test that logger names are abbreviated in console output."""
        formatter = ConsoleFormatter(use_colors=False)

        record = logging.LogRecord(
            name="cockpit.backtest.runner",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should show only last part of logger name
        assert "runner" in output
        # Should not show full path
        assert "cockpit.backtest.runner" not in output
