"""
Backtest preprocessing and validation for The Researcher's Cockpit.

Handles bundle validation, date range validation, calendar alignment checks,
and parameter validation before backtest execution.
Extracted from runner.py as part of v1.0.11 refactoring.
"""

import logging
from typing import Any, Tuple, Optional

import pandas as pd

from ..config import load_strategy_params
from ..data.normalization import normalize_to_utc

# SessionManager removed in v1.12.0 (Task 005) - no longer needed
from ..bundles import load_bundle, get_bundle_symbols
from ..bundles.utils import ensure_bundle_registered, get_bundle_session_date_range
from ..bundles.errors import (
    format_ingest_command,
    format_bundle_date_out_of_range_message,
)

logger = logging.getLogger(__name__)


def validate_session_alignment(
    bundle: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    validate_calendar_flag: bool = False,
) -> None:
    """
    Validate that bundle exists and has data for the date range.

    v1.12.0: Simplified - SessionManager removed (Task 005).
    FOREX calendar now includes Sundays, no session alignment workarounds needed.

    Args:
        bundle: Bundle name
        start_date: Backtest start date
        end_date: Backtest end date
        validate_calendar_flag: If True, raise on missing bundle; if False, warn only

    Raises:
        ValueError: If bundle doesn't exist and validate_calendar_flag is True
    """
    bundle_exists = ensure_bundle_registered(
        bundle,
        raise_on_missing=validate_calendar_flag,
        exception_type=ValueError,
        # In non-strict mode, emit the same actionable message without re-implementing it here.
        log_on_missing=not validate_calendar_flag,
        log_level=logging.WARNING,
    )

    if bundle_exists:
        logger.info(f"✓ Bundle '{bundle}' validated (registered with Zipline)")


def validate_strategy_symbols(
    strategy_name: str, bundle_name: str, asset_class: Optional[str] = None
) -> None:
    """
    Validate that strategy's required symbols exist in the bundle.

    Args:
        strategy_name: Name of the strategy
        bundle_name: Name of the bundle to check against
        asset_class: Optional asset class for strategy lookup

    Raises:
        ValueError: If required symbol is not in the bundle
        FileNotFoundError: If strategy parameters or bundle not found
    """
    # Load strategy parameters
    try:
        params = load_strategy_params(strategy_name, asset_class)
    except FileNotFoundError:
        logger.debug(
            f"No parameters.yaml for strategy '{strategy_name}', skipping symbol validation"
        )
        return

    # Get required symbol from strategy config
    strategy_config = params.get("strategy", {})
    required_symbol = strategy_config.get("asset_symbol")

    if not required_symbol:
        logger.debug(f"No asset_symbol in strategy '{strategy_name}', skipping symbol validation")
        return

    # Get available symbols in bundle
    # get_bundle_symbols() uses ensure_bundle_registered() internally for consistent error handling
    available_symbols = get_bundle_symbols(bundle_name)

    # Check if required symbol is available
    if required_symbol not in available_symbols:
        available_str = ", ".join(sorted(available_symbols)) if available_symbols else "(none)"
        ingest_cmd = format_ingest_command(
            bundle_name=bundle_name,
            symbols=required_symbol,
        )
        raise ValueError(
            f"Strategy '{strategy_name}' requires symbol '{required_symbol}' "
            f"but bundle '{bundle_name}' contains: [{available_str}]. "
            "Either re-ingest the bundle with the correct symbol:\n"
            f"  {ingest_cmd}\n"
            f"Or update the strategy's parameters.yaml to use an available symbol."
        )

    logger.info(f"Symbol validation passed: '{required_symbol}' found in bundle '{bundle_name}'")


def validate_bundle_date_range(
    bundle: str,
    start_date: str,
    end_date: str,
    data_frequency: str,
    trading_calendar: Any,
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Validate bundle exists and covers requested date range.

    Args:
        bundle: Bundle name
        start_date: Start date string
        end_date: End date string
        data_frequency: 'daily' or 'minute'
        trading_calendar: Trading calendar object

    Returns:
        Tuple of (start_timestamp, end_timestamp)

    Raises:
        ValueError: If date range is invalid
        FileNotFoundError: If bundle not found
    """
    # Parse dates - Zipline expects timezone-naive UTC timestamps
    start_ts = normalize_to_utc(start_date)
    end_ts = normalize_to_utc(end_date)

    # Verify bundle exists using shared error handling
    # load_bundle() uses ensure_bundle_registered() internally for consistent error handling
    bundle_data = load_bundle(bundle)

    # Check if bundle covers requested date range
    date_range = get_bundle_session_date_range(bundle_data)
    if date_range is not None:
        bundle_start, bundle_end = date_range

        if start_ts < bundle_start:
            ingest_cmd = format_ingest_command(
                bundle_name=bundle,
                start_date=start_date,
            )
            raise ValueError(
                format_bundle_date_out_of_range_message(
                    bundle_name=bundle,
                    requested_date=start_date,
                    bundle_start_date=bundle_start.strftime("%Y-%m-%d"),
                    bundle_end_date=bundle_end.strftime("%Y-%m-%d"),
                    which="start",
                    ingest_command=ingest_cmd,
                )
            )

        if end_ts > bundle_end:
            ingest_cmd = format_ingest_command(
                bundle_name=bundle,
                end_date=end_date,
            )
            raise ValueError(
                format_bundle_date_out_of_range_message(
                    bundle_name=bundle,
                    requested_date=end_date,
                    bundle_start_date=bundle_start.strftime("%Y-%m-%d"),
                    bundle_end_date=bundle_end.strftime("%Y-%m-%d"),
                    which="end",
                    ingest_command=ingest_cmd,
                )
            )

    return start_ts, end_ts
