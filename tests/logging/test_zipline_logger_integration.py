"""
Tests for Zipline-Reloaded named logger integration.

We ensure that Zipline's internal loggers route through the project's handlers
when requested, so Zipline logs show up in the same sinks/formatters as
`cockpit.*` logs.
"""

import logging

from lib.logging import configure_logging, integrate_zipline_loggers, shutdown_logging


def test_integrate_zipline_loggers_adds_project_handlers_and_disables_propagation(
    tmp_path,
):
    root = configure_logging(level="INFO", console=False, file=False, log_dir=tmp_path)
    assert root.name == "cockpit"
    assert root.handlers == []

    # Add a deterministic handler so we can assert wiring.
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    root.addHandler(handler)

    try:
        integrate_zipline_loggers(
            blotter_level="INFO",
            zipline_level="WARNING",
            portal_level="INFO",
            algo_warning_level="WARNING",
            use_project_handlers=True,
        )

        for name in ("Blotter", "ZiplineLog", "DataPortal", "AlgoWarning"):
            zlogger = logging.getLogger(name)
            assert zlogger.propagate is False
            # Project handler should be directly attached to Zipline logger.
            assert handler in zlogger.handlers
    finally:
        # Cleanup: avoid leaking handlers across tests.
        for name in ("Blotter", "ZiplineLog", "DataPortal", "AlgoWarning"):
            zlogger = logging.getLogger(name)
            zlogger.handlers = []
            zlogger.propagate = True
        shutdown_logging()
