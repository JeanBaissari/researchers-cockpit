"""
Test bundle error message helpers.

Focused unit tests for lib.bundles.errors formatting functions.
"""

# ruff: noqa: E402

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.errors import (
    format_bundle_date_out_of_range_message,
    format_bundle_load_failure_message,
    format_ingest_command,
)


@pytest.mark.unit
def test_format_bundle_load_failure_message_includes_bundle_and_exception():
    msg = format_bundle_load_failure_message(
        bundle_name="test_bundle",
        exc=ValueError("boom"),
    )
    assert "Failed to load bundle 'test_bundle':" in msg
    assert "boom" in msg


@pytest.mark.unit
def test_format_bundle_date_out_of_range_message_start_contains_ingest_command():
    msg = format_bundle_date_out_of_range_message(
        bundle_name="eurusd_1m",
        requested_date="2020-01-01",
        bundle_start_date="2020-06-01",
        bundle_end_date="2020-12-31",
        which="start",
        ingest_command="python scripts/ingest_data.py --bundle-name eurusd_1m --start-date 2020-01-01",
    )
    assert "Requested start date 2020-01-01" in msg
    assert "Bundle 'eurusd_1m' covers:" in msg
    assert "--start-date 2020-01-01" in msg


@pytest.mark.unit
def test_format_bundle_date_out_of_range_message_end_contains_ingest_command():
    msg = format_bundle_date_out_of_range_message(
        bundle_name="eurusd_1m",
        requested_date="2020-12-31",
        bundle_start_date="2020-01-01",
        bundle_end_date="2020-06-30",
        which="end",
        ingest_command="python scripts/ingest_data.py --bundle-name eurusd_1m --end-date 2020-12-31",
    )
    assert "Requested end date 2020-12-31" in msg
    assert "Bundle 'eurusd_1m' covers:" in msg
    assert "--end-date 2020-12-31" in msg


@pytest.mark.unit
def test_format_bundle_date_out_of_range_message_invalid_which_raises():
    with pytest.raises(ValueError, match="which must be 'start' or 'end'"):
        format_bundle_date_out_of_range_message(
            bundle_name="x",
            requested_date="2020-01-01",
            bundle_start_date="2020-01-02",
            bundle_end_date="2020-01-03",
            which="middle",
            ingest_command="cmd",
        )


class TestFormatIngestCommand:
    @pytest.mark.unit
    def test_default_placeholders(self):
        cmd = format_ingest_command(bundle_name="my_bundle")
        assert "--source <SOURCE>" in cmd
        assert "--symbols <SYMBOLS>" in cmd
        assert "--bundle-name my_bundle" in cmd

    @pytest.mark.unit
    def test_with_dates(self):
        cmd = format_ingest_command(
            bundle_name="my_bundle",
            start_date="2020-01-01",
            end_date="2020-12-31",
        )
        assert "--start-date 2020-01-01" in cmd
        assert "--end-date 2020-12-31" in cmd

    @pytest.mark.unit
    def test_with_source_and_symbols(self):
        cmd = format_ingest_command(
            bundle_name="my_bundle",
            source="yahoo",
            symbols="AAPL",
        )
        assert "--source yahoo" in cmd
        assert "--symbols AAPL" in cmd
