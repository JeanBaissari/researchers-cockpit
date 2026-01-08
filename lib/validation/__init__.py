"""
Data validation package for The Researcher's Cockpit.

Provides multi-layer validation for OHLCV data:
- Pre-ingestion source validation
- Ingestion-time bundle creation checks
- Pre-backtest bundle verification
- Post-backtest results validation

Architecture:
    - ValidationSeverity: Enum for validation severity levels
    - ValidationCheck: Individual check result container
    - ValidationResult: Aggregated validation results with merge support
    - BaseValidator: Abstract base for all validators (DRY pattern)
    - DataValidator: OHLCV data validation
    - BundleValidator: Bundle integrity validation
    - BacktestValidator: Backtest results validation
    - SchemaValidator: DataFrame schema validation
    - CompositeValidator: Pipeline multiple validators together

Design Principles:
    - Single Responsibility: Each validator handles one concern
    - Open/Closed: Easy to extend with new checks
    - Dependency Inversion: Validators depend on abstractions
    - DRY: Common logic in base class and utilities

Usage:
    >>> from lib.validation import DataValidator, ValidationConfig, ValidationResult
    >>> config = ValidationConfig.strict(timeframe='1d')
    >>> validator = DataValidator(config=config)
    >>> result = validator.validate(df, asset_name='AAPL')
    >>> if not result:
    ...     print(result.summary())
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Core types and constants
from .core import (
    # Constants
    INTRADAY_TIMEFRAMES,
    DAILY_TIMEFRAMES,
    ALL_TIMEFRAMES,
    REQUIRED_OHLCV_COLUMNS,
    OPTIONAL_OHLCV_COLUMNS,
    DEFAULT_GAP_TOLERANCE_DAYS,
    DEFAULT_GAP_TOLERANCE_BARS,
    DEFAULT_OUTLIER_THRESHOLD_SIGMA,
    DEFAULT_STALE_THRESHOLD_DAYS,
    DEFAULT_ZERO_VOLUME_THRESHOLD_PCT,
    DEFAULT_PRICE_JUMP_THRESHOLD_PCT,
    DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA,
    DEFAULT_MIN_ROWS_DAILY,
    DEFAULT_MIN_ROWS_INTRADAY,
    CONTINUOUS_CALENDARS,
    TIMEFRAME_INTERVALS,
    COLUMN_ALIASES,
    # Enums
    ValidationSeverity,
    ValidationStatus,
    # Data classes
    ValidationCheck,
    ValidationResult,
)

# Configuration
from .config import ValidationConfig

# Column mapping
from .column_mapping import ColumnMapping, build_column_mapping

# Base validator
from .base import BaseValidator

# Validators
from .data_validator import DataValidator
from .bundle_validator import BundleValidator
from .backtest_validator import BacktestValidator
from .schema_validator import SchemaValidator
from .composite import CompositeValidator

# Utility functions
from .utils import (
    normalize_dataframe_index,
    ensure_timezone,
    compute_dataframe_hash,
    parse_timeframe,
    is_intraday_timeframe,
    safe_divide,
    calculate_z_scores,
)

logger = logging.getLogger('cockpit.validation')


# =============================================================================
# Public API - Convenience Functions
# =============================================================================

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


def validate_backtest_results(
    results: Dict[str, Any],
    returns: Optional[pd.Series] = None,
    transactions: Optional[pd.DataFrame] = None,
    positions: Optional[pd.DataFrame] = None,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate backtest results.

    Args:
        results: Backtest results dictionary
        returns: Optional returns series
        transactions: Optional transactions DataFrame
        positions: Optional positions DataFrame
        config: Optional ValidationConfig

    Returns:
        ValidationResult
    """
    validator = BacktestValidator(config=config)
    return validator.validate(results, returns, transactions, positions)


def verify_metrics_calculation(
    metrics: Dict[str, Any],
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None
) -> Tuple[bool, List[str]]:
    """
    Verify that calculated metrics are within valid ranges.

    Args:
        metrics: Calculated metrics dictionary
        returns: Returns series used for calculation
        transactions: Optional transactions DataFrame

    Returns:
        Tuple of (is_valid, list of discrepancies)
    """
    discrepancies: List[str] = []

    # Sharpe ratio bounds
    sharpe = metrics.get('sharpe', metrics.get('sharpe_ratio'))
    if sharpe is not None and not -10 <= sharpe <= 10:
        discrepancies.append(f"Sharpe ratio {sharpe} outside expected range [-10, 10]")

    # Sortino ratio bounds
    sortino = metrics.get('sortino', metrics.get('sortino_ratio'))
    if sortino is not None and not -10 <= sortino <= 10:
        discrepancies.append(f"Sortino ratio {sortino} outside expected range [-10, 10]")

    # Max drawdown sign
    max_dd = metrics.get('max_drawdown')
    if max_dd is not None and max_dd > 0:
        discrepancies.append(f"Max drawdown {max_dd} should be <= 0")

    # Total return consistency
    if 'total_return' in metrics and len(returns) > 0:
        calculated = (1 + returns).prod() - 1
        reported = metrics['total_return']
        if abs(calculated - reported) > 0.001:
            discrepancies.append(
                f"Total return mismatch: calculated={calculated:.4f}, "
                f"reported={reported:.4f}"
            )

    # Win rate bounds
    win_rate = metrics.get('win_rate')
    if win_rate is not None and not 0 <= win_rate <= 1:
        discrepancies.append(f"Win rate {win_rate} should be between 0 and 1")

    return len(discrepancies) == 0, discrepancies


def verify_returns_calculation(
    returns: pd.Series,
    transactions: pd.DataFrame
) -> Tuple[bool, Optional[str]]:
    """
    Verify returns are consistent with transactions.

    Args:
        returns: Returns series
        transactions: Transactions DataFrame

    Returns:
        Tuple of (is_valid, error_message)
    """
    if returns.empty:
        return True, None

    # Check for extreme returns
    extreme = returns[returns.abs() > 0.5]
    if len(extreme) > 0:
        return False, f"Found {len(extreme)} extreme daily returns (>50%)"

    # Check for NaN values
    nan_count = returns.isna().sum()
    if nan_count > 0:
        return False, f"Found {nan_count} NaN values in returns"

    # Check for infinite values
    inf_count = np.isinf(returns).sum()
    if inf_count > 0:
        return False, f"Found {inf_count} infinite values in returns"

    return True, None


def verify_positions_match_transactions(
    positions_df: pd.DataFrame,
    transactions_df: pd.DataFrame
) -> Tuple[bool, Optional[str]]:
    """
    Verify that positions are consistent with transactions.

    Args:
        positions_df: Positions DataFrame
        transactions_df: Transactions DataFrame

    Returns:
        Tuple of (is_valid, error_message)
    """
    if transactions_df.empty:
        return True, None

    # Check transaction columns
    expected_cols = ['amount', 'price']
    missing_cols = [c for c in expected_cols if c not in transactions_df.columns]
    if missing_cols:
        return False, f"Missing transaction columns: {missing_cols}"

    # Check for negative prices
    if 'price' in transactions_df.columns:
        neg_prices = (transactions_df['price'] < 0).sum()
        if neg_prices > 0:
            return False, f"Found {neg_prices} transactions with negative prices"

    return True, None


# =============================================================================
# Report I/O Functions
# =============================================================================

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


# =============================================================================
# Additional Data Integrity Functions
# =============================================================================

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
        from ..bundles.api import load_bundle
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
    # Lazy import to avoid circular dependency
    from ..utils import get_project_root
    
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


# =============================================================================
# Public API Exports
# =============================================================================

__all__ = [
    # Constants
    'INTRADAY_TIMEFRAMES',
    'DAILY_TIMEFRAMES',
    'ALL_TIMEFRAMES',
    'REQUIRED_OHLCV_COLUMNS',
    'OPTIONAL_OHLCV_COLUMNS',
    'DEFAULT_GAP_TOLERANCE_DAYS',
    'DEFAULT_GAP_TOLERANCE_BARS',
    'DEFAULT_OUTLIER_THRESHOLD_SIGMA',
    'DEFAULT_STALE_THRESHOLD_DAYS',
    'DEFAULT_ZERO_VOLUME_THRESHOLD_PCT',
    'DEFAULT_PRICE_JUMP_THRESHOLD_PCT',
    'DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA',
    'DEFAULT_MIN_ROWS_DAILY',
    'DEFAULT_MIN_ROWS_INTRADAY',
    'CONTINUOUS_CALENDARS',
    'TIMEFRAME_INTERVALS',
    'COLUMN_ALIASES',
    # Enums
    'ValidationSeverity',
    'ValidationStatus',
    # Data classes
    'ValidationCheck',
    'ValidationResult',
    # Configuration
    'ValidationConfig',
    # Column mapping
    'ColumnMapping',
    'build_column_mapping',
    # Base validator
    'BaseValidator',
    # Validators
    'DataValidator',
    'BundleValidator',
    'BacktestValidator',
    'SchemaValidator',
    'CompositeValidator',
    # Utility functions
    'normalize_dataframe_index',
    'ensure_timezone',
    'compute_dataframe_hash',
    'parse_timeframe',
    'is_intraday_timeframe',
    'safe_divide',
    'calculate_z_scores',
    # Convenience functions
    'validate_before_ingest',
    'validate_bundle',
    'validate_backtest_results',
    'verify_metrics_calculation',
    'verify_returns_calculation',
    'verify_positions_match_transactions',
    # Data integrity functions
    'verify_bundle_dates',
    'validate_csv_files_pre_ingestion',
    # Report I/O
    'save_validation_report',
    'load_validation_report',
]

