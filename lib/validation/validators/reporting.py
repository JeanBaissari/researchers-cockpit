"""
Validation reporting and fix suggestion utilities.

Provides functions for formatting validation results and generating
actionable fix suggestions for common data quality issues.
"""

import logging
from typing import List, Dict, Any

from ..core import ValidationResult

logger = logging.getLogger('cockpit.validation.reporting')


def format_validation_report(result: ValidationResult, verbose: bool = True) -> str:
    """
    Format a ValidationResult into a human-readable report.

    Args:
        result: ValidationResult to format
        verbose: If True, include detailed check information

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("VALIDATION REPORT")
    lines.append("=" * 80)

    # Overall status
    status = "PASSED" if result.passed else "FAILED"
    lines.append(f"\nStatus: {status}")

    # Metadata
    if result.metadata:
        lines.append("\nMetadata:")
        for key, value in result.metadata.items():
            if key != 'suggested_fixes':  # Skip fixes in metadata section
                lines.append(f"  {key}: {value}")

    # Summary counts
    lines.append(f"\nChecks: {len(result.checks)} total")
    passed_count = sum(1 for c in result.checks if c.passed)
    failed_count = len(result.checks) - passed_count
    lines.append(f"  Passed: {passed_count}")
    lines.append(f"  Failed: {failed_count}")

    if result.warnings:
        lines.append(f"  Warnings: {len(result.warnings)}")
    if result.errors:
        lines.append(f"  Errors: {len(result.errors)}")

    # Detailed checks (if verbose)
    if verbose and result.checks:
        lines.append("\n" + "-" * 80)
        lines.append("CHECK DETAILS")
        lines.append("-" * 80)

        for check in result.checks:
            status_symbol = "✓" if check.passed else "✗"
            lines.append(f"\n{status_symbol} {check.name}")
            lines.append(f"  Status: {'PASSED' if check.passed else 'FAILED'}")
            lines.append(f"  Severity: {check.severity.value}")
            if check.message:
                lines.append(f"  Message: {check.message}")
            if check.details and verbose:
                lines.append("  Details:")
                for key, value in check.details.items():
                    # Truncate long lists
                    if isinstance(value, list) and len(value) > 5:
                        value = value[:5] + ['...']
                    lines.append(f"    {key}: {value}")

    # Warnings
    if result.warnings:
        lines.append("\n" + "-" * 80)
        lines.append("WARNINGS")
        lines.append("-" * 80)
        for warning in result.warnings:
            lines.append(f"  • {warning}")

    # Errors
    if result.errors:
        lines.append("\n" + "-" * 80)
        lines.append("ERRORS")
        lines.append("-" * 80)
        for error in result.errors:
            lines.append(f"  • {error}")

    # Fix suggestions
    if 'suggested_fixes' in result.metadata:
        lines.append("\n" + "-" * 80)
        lines.append("SUGGESTED FIXES")
        lines.append("-" * 80)
        fixes = result.metadata['suggested_fixes']
        for i, fix in enumerate(fixes, 1):
            lines.append(f"\n{i}. {fix.get('issue', 'unknown')}")
            lines.append(f"   Description: {fix.get('description', 'N/A')}")
            lines.append(f"   Function: {fix.get('function', 'N/A')}")
            lines.append(f"   Usage: {fix.get('usage', 'N/A')}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def generate_fix_suggestions(result: ValidationResult, df: Any, asset_name: str) -> List[Dict[str, Any]]:
    """
    Generate fix suggestions based on validation result.

    Args:
        result: ValidationResult with check outcomes
        df: DataFrame that was validated
        asset_name: Asset name for context

    Returns:
        List of fix suggestion dictionaries
    """
    fixes = []

    # Check for Sunday bars issue
    sunday_bars_check = result.get_check('sunday_bars')
    if sunday_bars_check and not sunday_bars_check.passed:
        try:
            # Lazy import to avoid circular dependency
            from ...utils import consolidate_sunday_to_friday
            fixes.append({
                'issue': 'sunday_bars',
                'function': 'lib.utils.consolidate_sunday_to_friday',
                'description': 'Consolidate Sunday bars into Friday to preserve weekend gap semantics',
                'usage': f'df_fixed = consolidate_sunday_to_friday(df)',
                'module': 'lib.utils'
            })
        except ImportError:
            logger.warning("Could not import consolidate_sunday_to_friday for fix suggestion")

    # Check for null values issue
    no_nulls_check = result.get_check('no_nulls')
    if no_nulls_check and not no_nulls_check.passed:
        fixes.append({
            'issue': 'no_nulls',
            'function': 'pandas.DataFrame.fillna',
            'description': 'Fill null values using forward fill or interpolation',
            'usage': "df_fixed = df.fillna(method='ffill')  # or df.interpolate()",
            'module': 'pandas'
        })
        fixes.append({
            'issue': 'no_nulls',
            'function': 'pandas.DataFrame.dropna',
            'description': 'Drop rows with null values if they are not critical',
            'usage': 'df_fixed = df.dropna()',
            'module': 'pandas'
        })

    # Check for unsorted index issue
    sorted_index_check = result.get_check('sorted_index')
    if sorted_index_check and not sorted_index_check.passed:
        fixes.append({
            'issue': 'sorted_index',
            'function': 'pandas.DataFrame.sort_index',
            'description': 'Sort DataFrame index in ascending order',
            'usage': 'df_fixed = df.sort_index()',
            'module': 'pandas'
        })

    # Check for duplicate dates issue
    duplicate_dates_check = result.get_check('duplicate_dates')
    if duplicate_dates_check and not duplicate_dates_check.passed:
        fixes.append({
            'issue': 'duplicate_dates',
            'function': 'pandas.DataFrame.drop_duplicates',
            'description': 'Remove duplicate index entries, keeping the first occurrence',
            'usage': 'df_fixed = df[~df.index.duplicated(keep="first")]',
            'module': 'pandas'
        })

    # Check for negative values issue
    negative_values_check = result.get_check('no_negative_values')
    if negative_values_check and not negative_values_check.passed:
        fixes.append({
            'issue': 'no_negative_values',
            'function': 'Data cleaning',
            'description': 'Review and correct negative OHLCV values - may indicate data corruption',
            'usage': 'df_fixed = df[df[["open", "high", "low", "close", "volume"]] >= 0]',
            'module': 'manual_review'
        })

    # Check for potential splits
    potential_splits_check = result.get_check('potential_splits')
    if potential_splits_check and not potential_splits_check.passed:
        fixes.append({
            'issue': 'potential_splits',
            'function': 'Use adjusted data',
            'description': 'Use split-adjusted close prices from data provider',
            'usage': 'df = yf.download(symbol, auto_adjust=True)  # For Yahoo Finance',
            'module': 'data_source'
        })

    # Check for price jumps
    price_jumps_check = result.get_check('price_jumps')
    if price_jumps_check and not price_jumps_check.passed:
        fixes.append({
            'issue': 'price_jumps',
            'function': 'Manual review',
            'description': 'Review large price jumps for data quality or genuine market events',
            'usage': 'df[df["close"].pct_change().abs() > threshold]  # Inspect jumps',
            'module': 'manual_review'
        })

    return fixes


def add_fix_suggestions_to_result(
    result: ValidationResult,
    df: Any,
    asset_name: str
) -> ValidationResult:
    """
    Add fix suggestions to a ValidationResult.

    Args:
        result: ValidationResult to enhance
        df: DataFrame that was validated
        asset_name: Asset name for context

    Returns:
        ValidationResult with fix suggestions added to metadata
    """
    fixes = generate_fix_suggestions(result, df, asset_name)

    if fixes:
        result.add_metadata('suggested_fixes', fixes)
        logger.debug(f"Added {len(fixes)} fix suggestions for {asset_name}")

    return result
