"""
Tests for lib.logging.context module.

Tests context management, LogContext context manager, and thread safety.
"""

import threading
import time
from unittest.mock import patch

import pytest

from lib.logging.context import (
    LogContext,
    reset_context,
    get_context_value,
    set_context_value,
    clear_context_value,
    has_context_value,
)


class TestContextManagement:
    """Test basic context management functions."""

    def test_set_get_context_value(self):
        """Test setting and getting context values."""
        reset_context()

        set_context_value("test_key", "test_value")
        assert get_context_value("test_key") == "test_value"

        clear_context_value("test_key")
        assert get_context_value("test_key") is None

    def test_has_context_value(self):
        """Test checking if context value exists."""
        reset_context()

        assert not has_context_value("test_key")

        set_context_value("test_key", "test_value")
        assert has_context_value("test_key")

        clear_context_value("test_key")
        assert not has_context_value("test_key")

    def test_clear_nonexistent_context_value(self):
        """Test clearing non-existent context value is safe."""
        reset_context()

        # Should not raise
        clear_context_value("nonexistent_key")

    def test_reset_context(self):
        """Test resetting all context values."""
        reset_context()

        set_context_value("key1", "value1")
        set_context_value("key2", "value2")

        assert has_context_value("key1")
        assert has_context_value("key2")

        reset_context()

        assert not has_context_value("key1")
        assert not has_context_value("key2")


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_sets_values(self):
        """Test that LogContext sets context values."""
        reset_context()

        with LogContext(
            phase="backtest",
            strategy="test_strategy",
            run_id="test_run",
            asset_type="crypto",
            bundle_name="test_bundle",
            timeframe="daily",
        ):
            assert get_context_value("phase") == "backtest"
            assert get_context_value("strategy") == "test_strategy"
            assert get_context_value("run_id") == "test_run"
            assert get_context_value("asset_type") == "crypto"
            assert get_context_value("bundle_name") == "test_bundle"
            assert get_context_value("timeframe") == "daily"

        # Context should be cleared after exit
        assert get_context_value("phase") is None
        assert get_context_value("strategy") is None

    def test_log_context_restores_previous_values(self):
        """Test that LogContext restores previous context values."""
        reset_context()

        set_context_value("strategy", "original_strategy")
        set_context_value("run_id", "original_run")

        with LogContext(
            phase="backtest",
            strategy="new_strategy",
            run_id="new_run",
        ):
            assert get_context_value("strategy") == "new_strategy"
            assert get_context_value("run_id") == "new_run"

        # Should restore original values
        assert get_context_value("strategy") == "original_strategy"
        assert get_context_value("run_id") == "original_run"

        reset_context()

    def test_log_context_clears_on_exit(self):
        """Test that LogContext clears values that didn't exist before."""
        reset_context()

        # No previous values set
        with LogContext(
            phase="backtest",
            strategy="test_strategy",
        ):
            assert get_context_value("strategy") == "test_strategy"

        # Should be cleared since it didn't exist before
        assert get_context_value("strategy") is None

    def test_log_context_phase_always_set(self):
        """Test that phase is always set even if None."""
        reset_context()

        with LogContext(phase="backtest"):
            assert get_context_value("phase") == "backtest"

        # Phase should be cleared after exit
        assert get_context_value("phase") is None

    def test_log_context_nested(self):
        """Test nested LogContext usage."""
        reset_context()

        with LogContext(phase="outer", strategy="outer_strategy"):
            assert get_context_value("phase") == "outer"
            assert get_context_value("strategy") == "outer_strategy"

            with LogContext(phase="inner", strategy="inner_strategy"):
                assert get_context_value("phase") == "inner"
                assert get_context_value("strategy") == "inner_strategy"

            # Should restore outer values
            assert get_context_value("phase") == "outer"
            assert get_context_value("strategy") == "outer_strategy"

        # Should be cleared
        assert get_context_value("phase") is None
        assert get_context_value("strategy") is None

    def test_log_context_exception_handling(self):
        """Test that LogContext restores values even on exception."""
        reset_context()

        set_context_value("strategy", "original")

        try:
            with LogContext(phase="backtest", strategy="new"):
                assert get_context_value("strategy") == "new"
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should restore original value even after exception
        assert get_context_value("strategy") == "original"

        reset_context()


class TestThreadSafety:
    """Test thread safety of context operations."""

    def test_thread_safety_set_get(self):
        """Test that context operations are thread-safe."""
        reset_context()

        results = []
        errors = []

        def worker(thread_id):
            try:
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"value_{i}"
                    set_context_value(key, value)
                    time.sleep(0.001)  # Small delay to increase chance of race condition
                    retrieved = get_context_value(key)
                    results.append((thread_id, key, retrieved == value))
                    clear_context_value(key)
            except Exception as e:
                errors.append((thread_id, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should succeed
        assert len(errors) == 0
        assert all(result[2] for result in results)  # All retrievals should match

        reset_context()
