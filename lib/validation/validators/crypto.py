"""
Crypto-specific OHLCV data validator.

Validates cryptocurrency data with crypto-specific rules:
- 24/7 market continuous trading
- Extreme volatility detection
- Flash crash detection
- Exchange-specific quirks
- High-frequency anomaly detection
"""

import logging
from typing import Any, Optional

import pandas as pd

from ..base import BaseValidator
from ..core import ValidationResult, ValidationSeverity
from ..column_mapping import ColumnMapping
from ..utils import safe_divide, calculate_z_scores, ensure_timezone

logger = logging.getLogger('cockpit.validation.crypto')


class CryptoValidator(BaseValidator):
    """
    Validator for cryptocurrency-specific OHLCV data checks.

    Performs crypto-specific validation including:
    - 24/7 continuous market validation
    - Extreme volatility detection
    - Flash crash detection
    - Exchange anomaly detection

    Inherits common OHLCV checks from BaseValidator.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize crypto validator with configuration."""
        super().__init__(config)

    def _register_checks(self) -> None:
        """Register crypto-specific validation checks."""
        self._check_registry = [
            self._check_extreme_volatility,
            self._check_flash_crashes,
        ]

    def validate(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str = "unknown"
    ) -> ValidationResult:
        """
        Validate crypto-specific characteristics.

        Args:
            df: DataFrame with OHLCV data
            col_map: Column mapping for OHLCV columns
            asset_name: Asset name for logging

        Returns:
            ValidationResult with crypto-specific check outcomes
        """
        result = self._create_result()
        result.add_metadata('asset_name', asset_name)
        result.add_metadata('asset_type', 'crypto')

        if df.empty:
            result.add_check('empty_data', False, f"DataFrame is empty for {asset_name}")
            return result

        # Run registered checks
        for check_func in self._check_registry:
            if not self._should_skip_check(check_func.__name__):
                result = self._run_check(result, check_func, df, col_map, asset_name)

        return result

    def _check_extreme_volatility(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for extreme volatility in crypto markets."""
        close_col = col_map.close

        if not close_col:
            return result

        # Edge case: Single-row DataFrame
        if len(df) < 2:
            result.add_check(
                'extreme_volatility', True,
                "Insufficient data for volatility check (need at least 2 rows)"
            )
            return result

        # Calculate returns
        returns = df[close_col].pct_change().dropna()

        if len(returns) < 2:
            result.add_check(
                'extreme_volatility', True,
                "Insufficient returns for volatility check"
            )
            return result

        # Crypto-specific: Use higher threshold for extreme moves (>50% in single period)
        crypto_extreme_threshold = 0.50  # 50% move
        extreme_moves = int((returns.abs() > crypto_extreme_threshold).sum())

        if extreme_moves > 0:
            extreme_pct = safe_divide(extreme_moves, len(returns)) * 100
            extreme_dates = returns[returns.abs() > crypto_extreme_threshold].index[:5]
            extreme_values = [f"{r*100:.2f}%" for r in returns[returns.abs() > crypto_extreme_threshold][:5].values]

            msg = (
                f"Found {extreme_moves} extreme volatility events (>{crypto_extreme_threshold*100}%) in {asset_name}. "
                f"While high volatility is common in crypto, review these dates for potential data errors or flash crashes."
            )

            result.add_check(
                'extreme_volatility', False, msg,
                {
                    'extreme_count': extreme_moves,
                    'extreme_pct': extreme_pct,
                    'extreme_dates': [str(d) for d in extreme_dates],
                    'extreme_values': extreme_values,
                    'max_return': float(returns.abs().max())
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'extreme_volatility', True,
                f"No extreme volatility events (>{crypto_extreme_threshold*100}%) detected"
            )
        return result

    def _check_flash_crashes(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """
        Detect flash crashes: rapid price drop followed by recovery.

        A flash crash is characterized by:
        1. Large price drop (>20%) within a short period
        2. Recovery within next few bars (>50% retracement)
        """
        close_col = col_map.close
        low_col = col_map.low
        high_col = col_map.high

        if not all([close_col, low_col, high_col]):
            return result

        # Need at least 5 bars to detect flash crash pattern
        if len(df) < 5:
            result.add_check(
                'flash_crashes', True,
                "Insufficient data for flash crash detection (need at least 5 rows)"
            )
            return result

        flash_crashes = []
        flash_crash_threshold = 0.20  # 20% drop

        # Iterate through data looking for flash crash patterns
        for i in range(len(df) - 3):
            # Check if current bar has a large intrabar drop
            bar_high = df.iloc[i][high_col]
            bar_low = df.iloc[i][low_col]
            bar_close = df.iloc[i][close_col]

            if bar_high == 0:
                continue

            # Calculate intrabar drop
            intrabar_drop = (bar_high - bar_low) / bar_high

            if intrabar_drop > flash_crash_threshold:
                # Check if price recovered in next few bars
                next_3_bars = df.iloc[i+1:i+4]
                if len(next_3_bars) > 0:
                    max_recovery = next_3_bars[high_col].max()
                    recovery_pct = (max_recovery - bar_low) / (bar_high - bar_low) if (bar_high - bar_low) > 0 else 0

                    # Flash crash if recovery > 50%
                    if recovery_pct > 0.5:
                        flash_crashes.append({
                            'date': str(df.index[i]),
                            'drop_pct': float(intrabar_drop * 100),
                            'recovery_pct': float(recovery_pct * 100),
                            'high': float(bar_high),
                            'low': float(bar_low),
                            'close': float(bar_close)
                        })

        if flash_crashes:
            msg = (
                f"Found {len(flash_crashes)} potential flash crash(es) in {asset_name}. "
                f"These rapid drops with quick recovery may indicate exchange issues, "
                f"liquidation cascades, or data errors. Review these dates carefully."
            )

            result.add_check(
                'flash_crashes', False, msg,
                {
                    'flash_crash_count': len(flash_crashes),
                    'flash_crashes': flash_crashes[:5]  # First 5
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('flash_crashes', True, "No flash crashes detected")
        return result
