"""
Zipline run_algorithm() parameter extraction from config.

This module bridges lib/config/ with Zipline's run_algorithm() API,
ensuring our YAML-based configuration complements Zipline's direct parameter API.

Zipline's run_algorithm() accepts:
- start, end (pd.Timestamp)
- capital_base (float)
- bundle (str)
- data_frequency ('daily' or 'minute')
- trading_calendar (TradingCalendar)
- benchmark_returns (pd.Series, optional)
- metrics_set (str or iterable, optional)
- Plus callables: initialize, handle_data, analyze, before_trading_start

Our lib/config/ provides:
- YAML-based strategy parameter loading
- Asset class configuration
- Data source configuration
- Parameter validation
- Warmup days calculation

This module extracts run_algorithm() parameters from our config system.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pandas as pd

from .strategy import load_strategy_params
from .assets import get_default_bundle
from .validation_backtest import validate_backtest_section

logger = logging.getLogger(__name__)


@dataclass
class ZiplineRunParams:
    """
    Parameters for Zipline's run_algorithm() extracted from config.

    This dataclass represents the parameters that will be passed to
    run_algorithm(), ensuring type safety and clear documentation.
    """

    start: pd.Timestamp
    end: pd.Timestamp
    capital_base: float
    bundle: str
    data_frequency: str
    trading_calendar: Any  # TradingCalendar from zipline
    benchmark_returns: Optional[pd.Series] = None
    metrics_set: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for passing to run_algorithm().

        Excludes None values and trading_calendar (passed separately).
        """
        result = {
            "start": self.start,
            "end": self.end,
            "capital_base": self.capital_base,
            "bundle": self.bundle,
            "data_frequency": self.data_frequency,
        }

        if self.benchmark_returns is not None:
            result["benchmark_returns"] = self.benchmark_returns

        if self.metrics_set is not None:
            result["metrics_set"] = self.metrics_set

        return result


def extract_zipline_params(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    data_frequency: Optional[str] = None,
    asset_class: Optional[str] = None,
    trading_calendar: Optional[Any] = None,
    benchmark_returns: Optional[pd.Series] = None,
    metrics_set: Optional[str] = None,
) -> ZiplineRunParams:
    """
    Extract Zipline run_algorithm() parameters from strategy config.

    This function bridges our YAML-based config system with Zipline's
    direct parameter API. It loads strategy parameters and extracts
    values needed for run_algorithm(), with proper precedence:

    Precedence (highest to lowest):
    1. Function arguments (explicit overrides)
    2. Strategy parameters.yaml
    3. Default values

    Args:
        strategy_name: Name of strategy
        start_date: Start date string (YYYY-MM-DD) or None
        end_date: End date string (YYYY-MM-DD) or None
        capital_base: Starting capital or None
        bundle: Bundle name or None
        data_frequency: 'daily' or 'minute' or None
        asset_class: Asset class hint or None
        trading_calendar: Trading calendar object or None
        benchmark_returns: Benchmark returns series or None
        metrics_set: Metrics set name or None

    Returns:
        ZiplineRunParams: Parameters ready for run_algorithm()

    Raises:
        FileNotFoundError: If strategy parameters.yaml not found
        ValueError: If required parameters missing or invalid
    """
    # Load strategy parameters
    try:
        params = load_strategy_params(strategy_name, asset_class)
    except FileNotFoundError:
        logger.warning(
            f"Strategy '{strategy_name}' has no parameters.yaml. "
            "Using function arguments and defaults only."
        )
        params = {}

    backtest_config = params.get("backtest", {}) or {}

    # Extract dates (function args > params.yaml > defaults)
    if start_date:
        start_ts = pd.Timestamp(start_date)
    elif "start_date" in backtest_config:
        start_ts = pd.Timestamp(backtest_config["start_date"])
    else:
        raise ValueError(
            f"start_date required. Provide via argument or backtest.start_date in parameters.yaml"
        )

    if end_date:
        end_ts = pd.Timestamp(end_date)
    elif "end_date" in backtest_config:
        end_ts = pd.Timestamp(backtest_config["end_date"])
    else:
        # Default to today
        end_ts = pd.Timestamp.today().normalize()
        logger.info(f"Using default end_date: {end_ts.date()}")

    # Ensure timezone-naive (Zipline requirement)
    if start_ts.tz is not None:
        start_ts = start_ts.tz_localize(None)
    if end_ts.tz is not None:
        end_ts = end_ts.tz_localize(None)

    # Extract capital_base
    if capital_base is not None:
        capital = float(capital_base)
    elif "capital" in backtest_config:
        capital = float(backtest_config["capital"])
    else:
        # Default capital
        capital = 100000.0
        logger.info(f"Using default capital_base: ${capital:,.0f}")

    if capital <= 0:
        raise ValueError(f"capital_base must be positive, got: {capital}")

    # Extract bundle
    if bundle:
        bundle_name = bundle
    elif "bundle" in backtest_config:
        bundle_name = backtest_config["bundle"]
    elif asset_class:
        # Try default bundle for asset class
        try:
            bundle_name = get_default_bundle(asset_class)
            logger.info(f"Using default bundle for '{asset_class}': {bundle_name}")
        except KeyError:
            raise ValueError(
                f"bundle required. Provide via argument, backtest.bundle in "
                f"parameters.yaml, or configure default_{asset_class} in settings.yaml"
            )
    else:
        raise ValueError(
            "bundle required. Provide via argument, backtest.bundle in "
            "parameters.yaml, or asset_class for default lookup"
        )

    # Extract data_frequency
    if data_frequency:
        freq = data_frequency
    elif "data_frequency" in backtest_config:
        freq = backtest_config["data_frequency"]
    else:
        freq = "daily"
        logger.info("Using default data_frequency: daily")

    if freq not in ("daily", "minute"):
        raise ValueError(f"data_frequency must be 'daily' or 'minute', got: {freq}")

    # Validate trading_calendar is provided (required by Zipline)
    if trading_calendar is None:
        raise ValueError(
            "trading_calendar required. This should be obtained from "
            "lib/calendars or bundle metadata before calling extract_zipline_params()"
        )

    return ZiplineRunParams(
        start=start_ts,
        end=end_ts,
        capital_base=capital,
        bundle=bundle_name,
        data_frequency=freq,
        trading_calendar=trading_calendar,
        benchmark_returns=benchmark_returns,
        metrics_set=metrics_set,
    )


def validate_zipline_params(params: ZiplineRunParams) -> Tuple[bool, list[str]]:
    """
    Validate Zipline run_algorithm() parameters.

    Performs additional validation beyond what extract_zipline_params()
    does, checking for logical consistency and Zipline requirements.

    Args:
        params: ZiplineRunParams to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Date validation
    if params.start >= params.end:
        errors.append(f"start ({params.start.date()}) must be before end ({params.end.date()})")

    # Capital validation
    if params.capital_base <= 0:
        errors.append(f"capital_base must be positive, got: {params.capital_base}")

    # Bundle validation (basic - existence checked elsewhere)
    if not params.bundle or not isinstance(params.bundle, str):
        errors.append(f"bundle must be a non-empty string, got: {params.bundle}")

    # Data frequency validation
    if params.data_frequency not in ("daily", "minute"):
        errors.append(f"data_frequency must be 'daily' or 'minute', got: {params.data_frequency}")

    # Trading calendar validation (basic - type check)
    if params.trading_calendar is None:
        errors.append("trading_calendar is required")

    return len(errors) == 0, errors
