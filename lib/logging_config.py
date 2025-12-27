"""Centralized logging configuration for The Researcher's Cockpit."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[Path] = None
) -> logging.Logger:
    """Configure logging for the application."""
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    root_logger = logging.getLogger('researchers_cockpit')
    root_logger.setLevel(getattr(logging, level.upper()))

    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format_string))
        root_logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(format_string))
            root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module."""
    return logging.getLogger(f'researchers_cockpit.{name}')
