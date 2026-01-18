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
from ..utils import normalize_to_utc
from ..calendars.sessions import SessionManager, compare_sessions
from ..bundles import load_bundle, get_bundle_symbols, load_bundle_registry

logger = logging.getLogger(__name__)


def validate_calendar_consistency(bundle: str, trading_calendar: Any) -> None:
    """
    Validate that the trading calendar used for backtest matches the calendar
    the bundle was ingested with.

    Args:
        bundle: Bundle name
        trading_calendar: Trading calendar object for backtest

    Logs:
        Warning if calendars don't match
    """
    registry = load_bundle_registry()
    if bundle not in registry:
        return

    bundle_calendar_name = registry[bundle].get('calendar_name')
    if not bundle_calendar_name:
        return

    backtest_calendar_name = getattr(trading_calendar, 'name', None)
    if not backtest_calendar_name:
        return

    # Compare calendars (case-insensitive)
    if bundle_calendar_name.upper() != backtest_calendar_name.upper():
        logger.warning(
            f"Calendar mismatch: Bundle '{bundle}' was ingested with calendar "
            f"'{bundle_calendar_name}' but backtest is using '{backtest_calendar_name}'. "
            f"This may cause session misalignment errors."
        )


def validate_session_alignment(
    bundle: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    validate_calendar_flag: bool = False
) -> None:
    """
    Validate that bundle has correct sessions for date range using SessionManager.

    This is the v1.1.0 pre-flight check that prevents shape mismatch errors.

    Args:
        bundle: Bundle name
        start_date: Backtest start date
        end_date: Backtest end date
        validate_calendar_flag: If True, raise on mismatch; if False, warn only

    Raises:
        ValueError: If validation fails and validate_calendar_flag is True
    """
    try:
        # Create SessionManager for this bundle
        session_mgr = SessionManager.for_bundle(bundle)

        # Validate bundle sessions
        is_valid, error = session_mgr.validate_bundle_sessions(bundle, start_date, end_date)

        if not is_valid:
            # Generate detailed report
            expected_sessions = session_mgr.get_sessions(start_date, end_date)
            actual_sessions = session_mgr._load_bundle_sessions(bundle, start_date, end_date)
            report = compare_sessions(expected_sessions, actual_sessions)

            # Save report for debugging
            from pathlib import Path
            debug_dir = Path('docs/debug')
            debug_dir.mkdir(parents=True, exist_ok=True)
            report_path = debug_dir / f'session_mismatch_{pd.Timestamp.now():%Y%m%d_%H%M%S}.md'
            report_path.write_text(report.to_markdown())

            error_msg = (
                f"Calendar alignment check failed for bundle '{bundle}': {error}\n"
                f"Detailed report saved to: {report_path}\n\n"
                f"Recommendations:\n"
                + "\n".join(f"  {i}. {rec}" for i, rec in enumerate(report.recommendations, 1))
            )

            if validate_calendar_flag:
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)

        else:
            logger.info(f"✓ Calendar alignment validated ({len(expected_sessions)} sessions)")

    except Exception as e:
        # If SessionManager fails, log warning but don't block
        logger.warning(f"Session alignment validation skipped for bundle '{bundle}': {e}")


def validate_strategy_symbols(
    strategy_name: str,
    bundle_name: str,
    asset_class: Optional[str] = None
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
        logger.debug(f"No parameters.yaml for strategy '{strategy_name}', skipping symbol validation")
        return

    # Get required symbol from strategy config
    strategy_config = params.get('strategy', {})
    required_symbol = strategy_config.get('asset_symbol')

    if not required_symbol:
        logger.debug(f"No asset_symbol in strategy '{strategy_name}', skipping symbol validation")
        return

    # Get available symbols in bundle
    try:
        available_symbols = get_bundle_symbols(bundle_name)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Bundle '{bundle_name}' not found. {e}") from e

    # Check if required symbol is available
    if required_symbol not in available_symbols:
        available_str = ', '.join(sorted(available_symbols)) if available_symbols else '(none)'
        raise ValueError(
            f"Strategy '{strategy_name}' requires symbol '{required_symbol}' "
            f"but bundle '{bundle_name}' contains: [{available_str}]. "
            f"Either re-ingest the bundle with the correct symbol:\n"
            f"  python scripts/ingest_data.py --source yahoo --symbols {required_symbol} --bundle-name {bundle_name}\n"
            f"Or update the strategy's parameters.yaml to use an available symbol."
        )

    logger.info(f"Symbol validation passed: '{required_symbol}' found in bundle '{bundle_name}'")


def validate_bundle_date_range(
    bundle: str,
    start_date: str,
    end_date: str,
    data_frequency: str,
    trading_calendar: Any
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

    # Verify bundle exists and check date range
    try:
        bundle_data = load_bundle(bundle)

        # Check if bundle covers requested date range
        try:
            sessions = bundle_data.equity_daily_bar_reader.sessions
            if len(sessions) > 0:
                bundle_start = pd.Timestamp(sessions[0]).normalize()
                bundle_end = pd.Timestamp(sessions[-1]).normalize()

                if start_ts < bundle_start:
                    raise ValueError(
                        f"Requested start date {start_date} is before bundle start date {bundle_start.strftime('%Y-%m-%d')}. "
                        f"Bundle '{bundle}' covers: {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Re-ingest data with extended date range: "
                        f"python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --start-date {start_date}"
                    )

                if end_ts > bundle_end:
                    raise ValueError(
                        f"Requested end date {end_date} is after bundle end date {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Bundle '{bundle}' covers: {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Re-ingest data with extended date range: "
                        f"python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --end-date {end_date}"
                    )
        except AttributeError:
            # Bundle structure might be different, skip date range check
            pass

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Bundle '{bundle}' not found. {e}. "
            f"Run: python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS>"
        )

    return start_ts, end_ts
