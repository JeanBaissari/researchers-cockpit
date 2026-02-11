"""
Bundle error message helpers.

These helpers centralize actionable, user-facing guidance when bundle-related
operations fail (e.g., bundle missing from Zipline's registry).

Note:
This module does NOT wrap Zipline APIs. It only formats messages so the rest of
the codebase stays DRY and consistent.
"""

from __future__ import annotations

from typing import Iterable, Optional


def format_ingest_command(
    *,
    bundle_name: str,
    source: str = "<SOURCE>",
    symbols: str = "<SYMBOLS>",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    Format a suggested ingestion command for a bundle.

    Args:
        bundle_name: Bundle name to ingest.
        source: Data source hint (default placeholder).
        symbols: Symbols hint (default placeholder).
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).

    Returns:
        CLI command string suitable for display in error messages.
    """
    cmd = (
        f"python scripts/ingest_data.py --source {source} --symbols {symbols} "
        f"--bundle-name {bundle_name}"
    )
    if start_date:
        cmd += f" --start-date {start_date}"
    if end_date:
        cmd += f" --end-date {end_date}"
    return cmd


def format_bundle_not_found_message(
    *,
    bundle_name: str,
    available_bundles: Iterable[str],
    ingest_command: str,
) -> str:
    """
    Format a standardized "bundle not found" message.

    Args:
        bundle_name: Missing bundle name.
        available_bundles: Iterable of available bundle names.
        ingest_command: Suggested ingestion command.

    Returns:
        Error message string with actionable guidance.
    """
    available_list = list(available_bundles)
    available_str = ", ".join(sorted(available_list)) if available_list else "(none)"
    return (
        f"Bundle '{bundle_name}' not found in Zipline registry. "
        f"Available bundles: [{available_str}]. "
        "Please ingest the bundle first:\n"
        f"  {ingest_command}"
    )


def format_bundle_load_failure_message(*, bundle_name: str, exc: BaseException) -> str:
    """
    Format a standardized "bundle load failed" message.

    Args:
        bundle_name: Bundle name that failed to load.
        exc: The underlying exception raised by Zipline.

    Returns:
        Error message string suitable for raising/chaining.
    """
    return f"Failed to load bundle '{bundle_name}': {exc}"


def format_bundle_date_out_of_range_message(
    *,
    bundle_name: str,
    requested_date: str,
    bundle_start_date: str,
    bundle_end_date: str,
    which: str,
    ingest_command: str,
) -> str:
    """
    Format a standardized message for requested date outside bundle coverage.

    This is used by both backtest preprocessing (exceptions) and validation checks (messages).

    Args:
        bundle_name: Bundle name.
        requested_date: The requested boundary date (YYYY-MM-DD).
        bundle_start_date: The bundle's first covered date (YYYY-MM-DD).
        bundle_end_date: The bundle's last covered date (YYYY-MM-DD).
        which: Either 'start' or 'end' to indicate which boundary is invalid.
        ingest_command: Suggested ingestion command string.

    Returns:
        Error message string with actionable guidance.

    Raises:
        ValueError: If which is not 'start' or 'end'.
    """
    if which not in {"start", "end"}:
        raise ValueError("which must be 'start' or 'end'")

    if which == "start":
        return (
            f"Requested start date {requested_date} is before bundle start date {bundle_start_date}. "
            f"Bundle '{bundle_name}' covers: {bundle_start_date} to {bundle_end_date}. "
            "Re-ingest data with extended date range: "
            f"{ingest_command}"
        )

    return (
        f"Requested end date {requested_date} is after bundle end date {bundle_end_date}. "
        f"Bundle '{bundle_name}' covers: {bundle_start_date} to {bundle_end_date}. "
        "Re-ingest data with extended date range: "
        f"{ingest_command}"
    )
