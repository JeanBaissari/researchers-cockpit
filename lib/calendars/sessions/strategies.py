"""
Session strategy interface for asset-specific session logic.

Each asset class (FOREX, CRYPTO, EQUITIES) implements a session strategy
that defines how sessions are determined and filtered.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Tuple
import pandas as pd


class SessionStrategy(ABC):
    """
    Base class for asset-specific session strategies.

    A session strategy defines:
    1. Which calendar to use (e.g., FOREX, CRYPTO, NYSE)
    2. What filters to apply (e.g., pre-session filtering, Sunday consolidation)
    3. How to validate session alignment
    """

    @abstractmethod
    def get_calendar_name(self) -> str:
        """Return the exchange calendar name (e.g., 'FOREX', 'CRYPTO', 'NYSE')."""
        pass

    @abstractmethod
    def get_session_filters(self) -> List[Callable]:
        """Return ordered list of filter functions to apply during ingestion."""
        pass

    @abstractmethod
    def validate_sessions(
        self, expected: pd.DatetimeIndex, actual: pd.DatetimeIndex
    ) -> Tuple[bool, str]:
        """Validate actual sessions match expected. Returns (is_valid, message)."""
        pass


class ForexSessionStrategy(SessionStrategy):
    """Session strategy for FOREX markets (24/5 trading)."""

    def get_calendar_name(self) -> str:
        return "FOREX"

    def get_session_filters(self) -> List[Callable]:
        """FOREX filters: presession, sunday consolidation, calendar, gap filling."""
        from ...data.filters import (
            filter_forex_presession_bars,
            consolidate_forex_sunday_to_friday,
            filter_to_calendar_sessions,
            apply_gap_filling,
        )
        return [
            filter_forex_presession_bars,
            consolidate_forex_sunday_to_friday,
            filter_to_calendar_sessions,
            apply_gap_filling,
        ]

    def validate_sessions(
        self, expected: pd.DatetimeIndex, actual: pd.DatetimeIndex
    ) -> Tuple[bool, str]:
        """FOREX validation with 0.5% tolerance for pre-session edge cases."""
        exp_count, act_count = len(expected), len(actual)
        if exp_count == act_count:
            return (True, "")
        diff = abs(exp_count - act_count)
        tolerance = max(2, int(exp_count * 0.005))
        if diff <= tolerance:
            return (True, f"Warning: {diff} session discrepancy (within tolerance)")
        missing = expected.difference(actual)
        return (False, f"Mismatch: expected {exp_count}, got {act_count}. Missing: {missing[:5].tolist()}...")


class CryptoSessionStrategy(SessionStrategy):
    """Session strategy for CRYPTO markets (24/7 trading)."""

    def get_calendar_name(self) -> str:
        return "CRYPTO"

    def get_session_filters(self) -> List[Callable]:
        """CRYPTO filters: calendar filter, gap filling (max 3 days)."""
        from ...data.filters import filter_to_calendar_sessions, apply_gap_filling
        return [filter_to_calendar_sessions, apply_gap_filling]

    def validate_sessions(
        self, expected: pd.DatetimeIndex, actual: pd.DatetimeIndex
    ) -> Tuple[bool, str]:
        """CRYPTO validation: strict matching (24/7, no filtering)."""
        exp_count, act_count = len(expected), len(actual)
        if exp_count == act_count:
            return (True, "")
        return (False, f"Mismatch: expected {exp_count}, got {act_count}. CRYPTO requires exact sessions.")


class EquitySessionStrategy(SessionStrategy):
    """Session strategy for EQUITY markets (NYSE, NASDAQ)."""

    def get_calendar_name(self) -> str:
        return "NYSE"

    def get_session_filters(self) -> List[Callable]:
        """EQUITY filters: calendar session filter only (respects holidays)."""
        from ...data.filters import filter_to_calendar_sessions
        return [filter_to_calendar_sessions]

    def validate_sessions(
        self, expected: pd.DatetimeIndex, actual: pd.DatetimeIndex
    ) -> Tuple[bool, str]:
        """EQUITY validation: strict matching (calendar-driven with holidays)."""
        exp_count, act_count = len(expected), len(actual)
        if exp_count == act_count:
            return (True, "")
        return (False, f"Mismatch: expected {exp_count}, got {act_count}. Check for missing/extra days.")
