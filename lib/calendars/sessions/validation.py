"""Session validation utilities for diagnosing calendar alignment issues."""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SessionMismatchReport:
    """Detailed report of session misalignment between calendar and bundle."""

    is_valid: bool
    expected_count: int
    actual_count: int
    missing_sessions: List[pd.Timestamp]
    extra_sessions: List[pd.Timestamp]
    error_message: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "expected_count": self.expected_count,
            "actual_count": self.actual_count,
            "missing_sessions": [str(ts) for ts in self.missing_sessions],
            "extra_sessions": [str(ts) for ts in self.extra_sessions],
            "error_message": self.error_message,
            "recommendations": self.recommendations,
        }

    def to_markdown(self) -> str:
        """Generate markdown report for documentation."""
        diff = self.expected_count - self.actual_count
        status = "VALID" if self.is_valid else "INVALID"
        lines = [
            "# Session Alignment Report", "",
            f"**Status:** {status}",
            f"**Expected Sessions:** {self.expected_count}",
            f"**Actual Sessions:** {self.actual_count}",
            f"**Difference:** {diff} sessions", "",
        ]
        if not self.is_valid:
            lines.extend(["## Error", "", self.error_message, ""])
        if self.missing_sessions:
            lines.extend(self._format_session_list(
                "Missing Sessions",
                "expected by the calendar but missing from the bundle",
                self.missing_sessions
            ))
        if self.extra_sessions:
            lines.extend(self._format_session_list(
                "Extra Sessions",
                "in the bundle but not expected by the calendar",
                self.extra_sessions
            ))
        if self.recommendations:
            lines.extend(["## Recommendations", ""])
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        return "\n".join(lines)

    def _format_session_list(
        self, title: str, desc: str, sessions: List[pd.Timestamp]
    ) -> List[str]:
        """Format a list of sessions for markdown output."""
        lines = [
            f"## {title}", "",
            f"The following {len(sessions)} sessions are {desc}:", "",
        ]
        for ts in sessions[:10]:
            lines.append(f"- {ts}")
        if len(sessions) > 10:
            lines.append(f"- ... ({len(sessions) - 10} more)")
        lines.append("")
        return lines


def compare_sessions(
    expected_sessions: pd.DatetimeIndex,
    actual_sessions: pd.DatetimeIndex,
    tolerance: int = 0,
) -> SessionMismatchReport:
    """Compare expected and actual sessions, generate detailed report."""
    expected_count, actual_count = len(expected_sessions), len(actual_sessions)

    # Normalize both to timezone-naive for comparison
    if expected_sessions.tz is not None:
        expected_sessions = expected_sessions.tz_convert(None)
    if actual_sessions.tz is not None:
        actual_sessions = actual_sessions.tz_convert(None)

    # Find missing and extra sessions
    missing = expected_sessions.difference(actual_sessions).tolist()
    extra = actual_sessions.difference(expected_sessions).tolist()
    is_valid = len(missing) <= tolerance and len(extra) == 0

    error_message = "Sessions are aligned." if is_valid else (
        f"Session count mismatch: expected {expected_count}, got {actual_count}. "
        f"Missing: {len(missing)}, Extra: {len(extra)}."
    )

    return SessionMismatchReport(
        is_valid=is_valid,
        expected_count=expected_count,
        actual_count=actual_count,
        missing_sessions=missing,
        extra_sessions=extra,
        error_message=error_message,
        recommendations=_generate_recommendations(missing, extra),
    )


def _generate_recommendations(
    missing: List[pd.Timestamp], extra: List[pd.Timestamp]
) -> List[str]:
    """Generate actionable recommendations based on mismatch type."""
    recommendations = []
    if missing:
        recommendations.append(
            f"Re-ingest bundle with gap filling enabled (max_gap_days >= {len(missing)})"
        )
        if len(missing) > 10:
            recommendations.append(
                "Large number of missing sessions suggests data source issue or holiday mismatch"
            )
    if extra:
        recommendations.append(
            "Extra sessions indicate calendar mismatch. Verify calendar definition includes these days."
        )
    return recommendations
