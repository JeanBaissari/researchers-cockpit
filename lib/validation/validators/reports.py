"""
Validation report I/O functions.

Handles saving and loading validation reports:
- save_validation_report(): Save ValidationResult to JSON
- load_validation_report(): Load ValidationResult from JSON
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Union

from ..core import ValidationResult, ValidationCheck, ValidationSeverity

logger = logging.getLogger('cockpit.validation')


def save_validation_report(
    result: ValidationResult,
    output_path: Union[str, Path],
    include_summary: bool = True,
    pretty_print: bool = True
) -> None:
    """
    Save validation report to JSON file.

    Args:
        result: ValidationResult to save
        output_path: Path for output file
        include_summary: Whether to include human-readable summary
        pretty_print: Whether to format JSON with indentation
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = result.to_dict()

    if include_summary:
        report['human_summary'] = result.summary()

    indent = 2 if pretty_print else None

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=indent, default=str)

    logger.info(f"Saved validation report to {output_path}")


def load_validation_report(report_path: Union[str, Path]) -> ValidationResult:
    """
    Load a validation report from JSON file.

    Args:
        report_path: Path to the report file

    Returns:
        ValidationResult reconstructed from the file

    Raises:
        FileNotFoundError: If the report file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the report structure is invalid
    """
    report_path = Path(report_path)

    if not report_path.exists():
        raise FileNotFoundError(f"Validation report not found: {report_path}")

    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in validation report: {e}", e.doc, e.pos) from e
    except Exception as e:
        raise ValueError(f"Error reading validation report: {e}") from e

    # Reconstruct ValidationResult
    result = ValidationResult()
    result.passed = report_data.get('passed', True)

    # Reconstruct checks
    checks_data = report_data.get('checks', [])
    for check_data in checks_data:
        check = ValidationCheck(
            name=check_data.get('name', 'unknown'),
            passed=check_data.get('passed', False),
            severity=ValidationSeverity(check_data.get('severity', 'error')),
            message=check_data.get('message', ''),
            details=check_data.get('details', {}),
            timestamp=datetime.fromisoformat(check_data.get('timestamp', datetime.utcnow().isoformat()).replace('Z', '+00:00'))
        )
        result.checks.append(check)

    # Reconstruct lists
    result.warnings = report_data.get('warnings', [])
    result.errors = report_data.get('errors', [])
    result.info = report_data.get('info', [])
    result.metadata = report_data.get('metadata', {})

    # Restore start time if available (for duration calculation)
    validated_at = report_data.get('validated_at')
    if validated_at:
        try:
            result._start_time = datetime.fromisoformat(validated_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # If we can't parse it, use current time (duration will be inaccurate)
            pass

    return result
