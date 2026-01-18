"""
Centralized session management for all asset classes.

SessionManager is the single source of truth for session definitions,
ensuring bundle ingestion and backtest execution use identical session logic.
"""
import logging
from typing import Any, Dict
import pandas as pd
from zipline.utils.calendar_utils import get_calendar

# Will be available after strategies.py is created
from .strategies import (
    CryptoSessionStrategy, EquitySessionStrategy, ForexSessionStrategy, SessionStrategy,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Centralized session manager for trading calendars.

    Usage (Ingestion): session_mgr = SessionManager.for_asset_class('forex')
    Usage (Pre-Flight): session_mgr = SessionManager.for_bundle('csv_eurusd_1m')
    """

    _strategy_registry: Dict[str, SessionStrategy] = {
        'forex': ForexSessionStrategy(),
        'crypto': CryptoSessionStrategy(),
        'equity': EquitySessionStrategy(),
    }

    def __init__(self, strategy: SessionStrategy):
        """Initialize SessionManager with a specific session strategy."""
        self.strategy = strategy
        self.calendar_name = strategy.get_calendar_name()

        # Auto-register custom calendars (FOREX, CRYPTO) before get_calendar()
        if self.calendar_name in ['FOREX', 'CRYPTO']:
            from ...calendars import register_custom_calendars
            register_custom_calendars([self.calendar_name])

        self.calendar = get_calendar(self.calendar_name)
        self._filters = strategy.get_session_filters()

    @classmethod
    def for_asset_class(cls, asset_class: str) -> 'SessionManager':
        """Create SessionManager for a specific asset class."""
        asset_class_lower = asset_class.lower()
        if asset_class_lower not in cls._strategy_registry:
            available = ', '.join(cls._strategy_registry.keys())
            raise ValueError(f"Unknown asset class: {asset_class}. Available: {available}")
        return cls(cls._strategy_registry[asset_class_lower])

    @classmethod
    def for_bundle(cls, bundle_name: str) -> 'SessionManager':
        """Create SessionManager based on bundle metadata."""
        from ...bundles import load_bundle_registry

        registry = load_bundle_registry()
        if bundle_name not in registry:
            raise ValueError(f"Bundle not found: {bundle_name}")

        calendar_name = registry[bundle_name].get('calendar_name', 'NYSE')
        calendar_to_asset = {'FOREX': 'forex', 'CRYPTO': 'crypto', 'NYSE': 'equity', 'NASDAQ': 'equity'}
        asset_class = calendar_to_asset.get(calendar_name.upper(), 'equity')
        return cls.for_asset_class(asset_class)

    def get_sessions(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
        """
        Get trading sessions for date range (canonical method).
        Both bundle ingestion and backtest execution MUST use this method.
        """
        start_naive = self._normalize_to_naive_utc(start)
        end_naive = self._normalize_to_naive_utc(end)
        sessions = self.calendar.sessions_in_range(start_naive, end_naive)
        if sessions.tz is not None:
            sessions = sessions.tz_convert(None)
        return sessions

    def apply_filters(self, df: pd.DataFrame, show_progress: bool = False, **kwargs: Any) -> pd.DataFrame:
        """Apply all session filters to DataFrame in order defined by strategy."""
        if df.empty:
            return df
        result_df = df.copy()
        # Inject calendar_name into kwargs for filters that need it (like apply_gap_filling)
        filter_kwargs = {'calendar_name': self.calendar_name, **kwargs}
        for i, filter_func in enumerate(self._filters, 1):
            if show_progress:
                logger.info(f"Applying filter {i}/{len(self._filters)}: {filter_func.__name__}")
            try:
                result_df = filter_func(result_df, self.calendar, show_progress=show_progress, **filter_kwargs)
            except Exception as e:
                logger.error(f"Filter {filter_func.__name__} failed: {e}")
                raise
        return result_df

    def validate_sessions(
        self, expected_sessions: pd.DatetimeIndex, actual_sessions: pd.DatetimeIndex
    ) -> tuple[bool, str]:
        """Validate that actual sessions match expected sessions."""
        return self.strategy.validate_sessions(expected_sessions, actual_sessions)

    def validate_bundle_sessions(
        self, bundle_name: str, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> tuple[bool, str]:
        """Validate that bundle has correct sessions for date range (pre-flight check)."""
        try:
            expected_sessions = self.get_sessions(start_date, end_date)
            actual_sessions = self._load_bundle_sessions(bundle_name, start_date, end_date)
            return self.validate_sessions(expected_sessions, actual_sessions)
        except Exception as e:
            return (False, f"Validation failed: {e}")

    def _normalize_to_naive_utc(self, dt: pd.Timestamp) -> pd.Timestamp:
        """Normalize timestamp to timezone-naive UTC."""
        if dt.tz is not None:
            dt = dt.tz_convert('UTC').tz_localize(None)
        return dt

    def _load_bundle_sessions(
        self, bundle_name: str, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> pd.DatetimeIndex:
        """Load actual sessions from bundle."""
        from zipline.data.bundles import load as zipline_load

        bundle_data = zipline_load(bundle_name)
        all_sessions = bundle_data.equity_daily_bar_reader.sessions
        start_naive = self._normalize_to_naive_utc(start_date)
        end_naive = self._normalize_to_naive_utc(end_date)
        if all_sessions.tz is not None:
            all_sessions = all_sessions.tz_convert(None)
        mask = (all_sessions >= start_naive) & (all_sessions <= end_naive)
        return all_sessions[mask]


def get_session_manager(asset_class: str) -> SessionManager:
    """Get SessionManager for asset class (convenience function)."""
    return SessionManager.for_asset_class(asset_class)
