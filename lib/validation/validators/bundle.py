"""
Bundle validation functions.

Validates bundle integrity and date coverage:
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

logger = logging.getLogger('cockpit.validation')


def validate_bundle(
    bundle_name: str,
    bundle_path: Optional[Path] = None,
    config: Optional[ValidationConfig] = None
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


def _normalize_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """
    Normalize a timestamp to timezone-naive midnight.

    Args:
        ts: Timestamp to normalize (may be timezone-aware or naive)

    Returns:
        Timezone-naive timestamp normalized to midnight
    """
    if ts.tz is not None:
        return ts.tz_convert(None).normalize()
    return ts.normalize()


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

    try:
        # Lazy import to avoid circular dependency
        from ...bundles.api import load_bundle
        bundle_data = load_bundle(bundle_name)

        # Get available sessions from bundle
        sessions = bundle_data.equity_daily_bar_reader.sessions
        if len(sessions) == 0:
            result.add_check(
                name='bundle_has_sessions',
                passed=False,
                message=f"Bundle '{bundle_name}' has no trading sessions"
            )
            return result

        result.add_check(
            name='bundle_has_sessions',
            passed=True,
            message=f"Bundle has {len(sessions)} trading sessions"
        )

        # Normalize timestamps
        bundle_start = _normalize_timestamp(pd.Timestamp(sessions[0]))
        bundle_end = _normalize_timestamp(pd.Timestamp(sessions[-1]))
        start_ts = _normalize_timestamp(pd.Timestamp(start_date))
        end_ts = _normalize_timestamp(pd.Timestamp(end_date))

        # Check start date
        if start_ts < bundle_start:
            result.add_check(
                name='start_date_covered',
                passed=False,
                message=f"Start date {start_date} is before bundle start {bundle_start.strftime('%Y-%m-%d')}",
                details={
                    'requested_start': start_date,
                    'bundle_start': bundle_start.strftime('%Y-%m-%d')
                }
            )
        else:
            result.add_check(
                name='start_date_covered',
                passed=True,
                message=f"Start date {start_date} is within bundle range"
            )

        # Check end date
        if end_ts > bundle_end:
            result.add_check(
                name='end_date_covered',
                passed=False,
                message=f"End date {end_date} is after bundle end {bundle_end.strftime('%Y-%m-%d')}",
                details={
                    'requested_end': end_date,
                    'bundle_end': bundle_end.strftime('%Y-%m-%d')
                }
            )
        else:
            result.add_check(
                name='end_date_covered',
                passed=True,
                message=f"End date {end_date} is within bundle range"
            )

        # Add bundle info to result
        result.add_check(
            name='bundle_date_range',
            passed=True,
            message=f"Bundle covers {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}",
            details={
                'bundle_start': bundle_start.strftime('%Y-%m-%d'),
                'bundle_end': bundle_end.strftime('%Y-%m-%d'),
                'session_count': len(sessions)
            }
        )

    except Exception as e:
        result.add_check(
            name='bundle_load',
            passed=False,
            message=f"Failed to verify bundle dates: {e}"
        )

    return result
