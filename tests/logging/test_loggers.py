"""
Tests for lib.logging.loggers module.

Tests pre-configured specialized loggers.
"""

import logging

import pytest

from lib.logging.loggers import (
    data_logger,
    strategy_logger,
    backtest_logger,
    metrics_logger,
    validation_logger,
    report_logger,
    optimization_logger,
    pipeline_logger,
    ingestion_logger,
)


class TestSpecializedLoggers:
    """Test pre-configured specialized loggers."""

    def test_all_loggers_exist(self):
        """Test that all specialized loggers are defined."""
        assert data_logger is not None
        assert strategy_logger is not None
        assert backtest_logger is not None
        assert metrics_logger is not None
        assert validation_logger is not None
        assert report_logger is not None
        assert optimization_logger is not None
        assert pipeline_logger is not None
        assert ingestion_logger is not None

    def test_all_loggers_are_logging_loggers(self):
        """Test that all specialized loggers are logging.Logger instances."""
        loggers = [
            data_logger,
            strategy_logger,
            backtest_logger,
            metrics_logger,
            validation_logger,
            report_logger,
            optimization_logger,
            pipeline_logger,
            ingestion_logger,
        ]

        for logger in loggers:
            assert isinstance(logger, logging.Logger)

    def test_loggers_have_cockpit_namespace(self):
        """Test that all loggers use cockpit namespace."""
        assert data_logger.name == "cockpit.data"
        assert strategy_logger.name == "cockpit.strategy"
        assert backtest_logger.name == "cockpit.backtest"
        assert metrics_logger.name == "cockpit.metrics"
        assert validation_logger.name == "cockpit.validation"
        assert report_logger.name == "cockpit.report"
        assert optimization_logger.name == "cockpit.optimization"
        assert pipeline_logger.name == "cockpit.pipeline"
        assert ingestion_logger.name == "cockpit.ingestion"

    def test_loggers_are_different_instances(self):
        """Test that different loggers are different instances."""
        assert data_logger is not strategy_logger
        assert backtest_logger is not metrics_logger
        assert validation_logger is not report_logger

    def test_loggers_can_log(self):
        """Test that loggers can actually log messages."""
        # Configure a handler to capture logs
        handler = logging.NullHandler()
        data_logger.addHandler(handler)
        data_logger.setLevel(logging.DEBUG)

        # Should not raise
        data_logger.info("Test message")
        data_logger.debug("Debug message")
        data_logger.warning("Warning message")
        data_logger.error("Error message")

        data_logger.removeHandler(handler)
