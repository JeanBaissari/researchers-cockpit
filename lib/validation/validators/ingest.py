"""
Pre-ingestion validation functions.

Validates data before ingesting into bundles:
- validate_before_ingest(): Single DataFrame validation
- validate_csv_files_pre_ingestion(): Batch CSV file validation
"""

import logging
from pathlib import Path
from typing import Any, List, Literal, Optional

import pandas as pd

from ..core import ValidationResult
from ..config import ValidationConfig

logger = logging.getLogger('cockpit.validation')


def validate_before_ingest(
    df: pd.DataFrame,
    asset_name: str = "unknown",
    timeframe: Optional[str] = None,
    calendar: Optional[Any] = None,
    calendar_name: Optional[str] = None,
    asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
    strict_mode: bool = False,
    suggest_fixes: bool = False,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate data before ingestion into a bundle.

    This is the main entry point for pre-ingestion validation.

    Args:
        df: DataFrame with OHLCV data
        asset_name: Asset name for logging
        timeframe: Data timeframe (e.g., '1m', '1h', '1d')
        calendar: Optional trading calendar
        calendar_name: Calendar name for context-aware validation
        asset_type: Asset type ('equity', 'forex', 'crypto') for context-aware validation
        strict_mode: If True, warnings become errors
        suggest_fixes: If True, add fix suggestions to result metadata
        config: Optional ValidationConfig (overrides other params)

    Returns:
        ValidationResult with all check outcomes

    Example:
        >>> result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
        >>> if not result:
        ...     raise ValueError(result.summary())
    """
    # Lazy import to avoid circular dependency
    from ..data_validator import DataValidator

    if config is None:
        config = ValidationConfig(
            timeframe=timeframe,
            strict_mode=strict_mode,
            asset_type=asset_type,
            calendar_name=calendar_name,
            suggest_fixes=suggest_fixes
        )
    else:
        # Update config with provided values if not already set
        if asset_type is not None:
            config.asset_type = asset_type
        if calendar_name is not None:
            config.calendar_name = calendar_name
        if suggest_fixes:
            config.suggest_fixes = suggest_fixes

    validator = DataValidator(config=config)
    return validator.validate(
        df=df,
        calendar=calendar,
        asset_name=asset_name,
        calendar_name=calendar_name,
        asset_type=asset_type,
        suggest_fixes=suggest_fixes
    )


def validate_csv_files_pre_ingestion(
    timeframe: str,
    symbols: Optional[List[str]] = None,
    data_dir: Optional[Path] = None
) -> ValidationResult:
    """
    Pre-ingestion hook that validates CSV files in data/processed/{timeframe}/.

    Args:
        timeframe: Timeframe directory to validate (e.g., '1h', 'daily')
        symbols: Optional list of symbols to validate. If None, validates all CSVs.
        data_dir: Optional custom data directory. Defaults to data/processed/{timeframe}/

    Returns:
        ValidationResult with detailed check results
    """
    # Lazy imports to avoid circular dependency
    from ...utils import get_project_root
    from ..data_validator import DataValidator

    result = ValidationResult(passed=True)

    if data_dir is None:
        data_dir = get_project_root() / 'data' / 'processed' / timeframe

    if not data_dir.exists():
        result.add_check(
            name='directory_exists',
            passed=False,
            message=f"Data directory does not exist: {data_dir}"
        )
        return result

    result.add_check(
        name='directory_exists',
        passed=True,
        message=f"Data directory exists: {data_dir}"
    )

    # Find CSV files
    if symbols:
        csv_files = [data_dir / f"{symbol}.csv" for symbol in symbols]
        csv_files = [f for f in csv_files if f.exists()]
        missing = [s for s in symbols if not (data_dir / f"{s}.csv").exists()]
        if missing:
            result.add_warning(f"Missing CSV files for symbols: {missing}")
    else:
        csv_files = list(data_dir.glob('*.csv'))

    if not csv_files:
        result.add_check(
            name='csv_files_found',
            passed=False,
            message=f"No CSV files found in {data_dir}"
        )
        return result

    result.add_check(
        name='csv_files_found',
        passed=True,
        message=f"Found {len(csv_files)} CSV file(s)"
    )

    # Validate each CSV file
    validator = DataValidator(config=ValidationConfig(timeframe=timeframe))

    for csv_file in csv_files:
        symbol = csv_file.stem
        try:
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            file_result = validator.validate(df, asset_name=symbol)
            result = result.merge(file_result)
        except Exception as e:
            result.add_check(
                name=f'csv_load_{symbol}',
                passed=False,
                message=f"Failed to load {csv_file.name}: {e}"
            )

    return result
