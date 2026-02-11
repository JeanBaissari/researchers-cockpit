"""
Unit tests for bundle utility helpers.

Focused tests for `lib.bundles.utils.get_bundle_session_date_range`.
"""

# ruff: noqa: E402

from __future__ import annotations

# Standard library
import sys
from pathlib import Path

# Third-party
import pandas as pd
import pytest

# Local imports (ensure `lib.*` resolves)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.utils import get_bundle_session_date_range


class _FakeDailyBarReader:
    def __init__(self, sessions):
        self.sessions = sessions


class _FakeBundleData:
    def __init__(self, sessions):
        self.equity_daily_bar_reader = _FakeDailyBarReader(sessions=sessions)


@pytest.mark.unit
def test_get_bundle_session_date_range_returns_normalized_naive_dates():
    bundle = _FakeBundleData(
        sessions=[
            pd.Timestamp("2020-01-02 15:30:00", tz="UTC"),
            pd.Timestamp("2020-01-03 15:30:00", tz="UTC"),
        ]
    )
    start, end = get_bundle_session_date_range(bundle)
    assert start == pd.Timestamp("2020-01-02")
    assert end == pd.Timestamp("2020-01-03")
    assert start.tz is None
    assert end.tz is None


@pytest.mark.unit
def test_get_bundle_session_date_range_returns_none_for_missing_sessions_attr():
    class _WeirdBundle:
        pass

    assert get_bundle_session_date_range(_WeirdBundle()) is None


@pytest.mark.unit
def test_get_bundle_session_date_range_returns_none_for_empty_sessions():
    bundle = _FakeBundleData(sessions=[])
    assert get_bundle_session_date_range(bundle) is None
