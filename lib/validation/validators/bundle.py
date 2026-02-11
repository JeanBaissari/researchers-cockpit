"""
Bundle validation functions.

Validates bundle INTEGRITY after ingestion. This complements Zipline's runtime
validation that occurs during backtest execution.

**What We Validate (Post-Ingestion):**
- Bundle existence (directory, files present)
- Metadata integrity (metadata.json validity)
- Asset files (SQLite/bcolz files present)
- Date coverage (bundle covers requested range)
- Symbol availability (required symbols exist)

**What Zipline Validates (Runtime):**
- Data availability (data exists for requested dates)
- Calendar alignment (backtest dates align with bundle calendar)
- Symbol resolution (symbols can be resolved to assets)
- Bar access (data.history() requests are valid)

See docs/validation/validation_architecture.md for complete distinction.

Functions:
- validate_bundle(): Full bundle integrity validation
- verify_bundle_dates(): Date range coverage verification
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from ..core import ValidationResult
from ..config import ValidationConfig
from ..bundle_validator import BundleValidator
from ...bundles.utils import get_bundle_session_date_range

logger = logging.getLogger("cockpit.validation")


def validate_bundle(
    bundle_name: str,
    bundle_path: Optional[Path] = None,
    config: Optional[ValidationConfig] = None,
) -> ValidationResult:
    """
    Validate an existing bundle.

    Args:
        bundle_name: Name of the bundle to validate
        bundle_path: Optional path to bundle directory. If None, uses default resolver
            from data_loader.get_bundle_path (with graceful degradation if unavailable)
        config: Optional ValidationConfig

    Returns:
        ValidationResult
    """
    # BundleValidator will use get_bundle_path as default resolver if bundle_path_resolver is None
    validator = BundleValidator(config=config)
    return validator.validate(bundle_name, bundle_path)


def verify_bundle_dates(bundle_name: str, start_date: str, end_date: str) -> ValidationResult:
    """
    Verify that a bundle covers the requested date range.

    Args:
        bundle_name: Name of bundle to check
        start_date: Requested start date (YYYY-MM-DD)
        end_date: Requested end date (YYYY-MM-DD)

    Returns:
        ValidationResult with check details
    """
    result = ValidationResult(passed=True)

    # Check bundle registration first using shared error handling
    from ...bundles.utils import ensure_bundle_registered
    from ...bundles.errors import (
        format_ingest_command,
        format_bundle_date_out_of_range_message,
    )

    try:
        ensure_bundle_registered(
            bundle_name,
            raise_on_missing=True,
            exception_type=FileNotFoundError,
            start_date_hint=start_date,
            end_date_hint=end_date,
        )
    except FileNotFoundError as e:
        result.add_check(name="bundle_load", passed=False, message=str(e))
        return result

    try:
        # Lazy import to avoid circular dependency
        from ...bundles import load_bundle

        bundle_data = load_bundle(bundle_name)

        date_range = get_bundle_session_date_range(bundle_data)
        if date_range is None:
            result.add_check(
                name="bundle_has_sessions",
                passed=False,
                message=f"Bundle '{bundle_name}' has no readable trading sessions",
            )
            return result

        bundle_start, bundle_end = date_range

        result.add_check(
            name="bundle_has_sessions",
            passed=True,
            message="Bundle exposes trading sessions",
        )

        start_ts = pd.Timestamp(start_date).normalize()
        end_ts = pd.Timestamp(end_date).normalize()

        # Check start date
        if start_ts < bundle_start:
            ingest_cmd = format_ingest_command(
                bundle_name=bundle_name,
                start_date=start_date,
                end_date=end_date,
            )
            result.add_check(
                name="start_date_covered",
                passed=False,
                message=format_bundle_date_out_of_range_message(
                    bundle_name=bundle_name,
                    requested_date=start_date,
                    bundle_start_date=bundle_start.strftime("%Y-%m-%d"),
                    bundle_end_date=bundle_end.strftime("%Y-%m-%d"),
                    which="start",
                    ingest_command=ingest_cmd,
                ),
                details={
                    "requested_start": start_date,
                    "bundle_start": bundle_start.strftime("%Y-%m-%d"),
                },
            )
        else:
            result.add_check(
                name="start_date_covered",
                passed=True,
                message=f"Start date {start_date} is within bundle range",
            )

        # Check end date
        if end_ts > bundle_end:
            ingest_cmd = format_ingest_command(
                bundle_name=bundle_name,
                start_date=start_date,
                end_date=end_date,
            )
            result.add_check(
                name="end_date_covered",
                passed=False,
                message=format_bundle_date_out_of_range_message(
                    bundle_name=bundle_name,
                    requested_date=end_date,
                    bundle_start_date=bundle_start.strftime("%Y-%m-%d"),
                    bundle_end_date=bundle_end.strftime("%Y-%m-%d"),
                    which="end",
                    ingest_command=ingest_cmd,
                ),
                details={
                    "requested_end": end_date,
                    "bundle_end": bundle_end.strftime("%Y-%m-%d"),
                },
            )
        else:
            result.add_check(
                name="end_date_covered",
                passed=True,
                message=f"End date {end_date} is within bundle range",
            )

        # Add bundle info to result
        result.add_check(
            name="bundle_date_range",
            passed=True,
            message=f"Bundle covers {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}",
            details={
                "bundle_start": bundle_start.strftime("%Y-%m-%d"),
                "bundle_end": bundle_end.strftime("%Y-%m-%d"),
            },
        )

    except Exception as e:
        result.add_check(
            name="bundle_load",
            passed=False,
            message=f"Failed to verify bundle dates: {e}",
        )

    return result
