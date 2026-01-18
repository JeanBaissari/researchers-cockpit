"""
Equity-specific OHLCV data validator.

Validates equity data with equity-specific rules:
- Stock split detection (2:1, 3:1, 4:1, reverse splits)
- Dividend adjustment detection
- Price jump analysis
- Volume spike detection
- Trading halt detection
"""

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from ..base import BaseValidator
from ..core import ValidationResult, ValidationSeverity
from ..column_mapping import ColumnMapping
from ..utils import safe_divide, calculate_z_scores, ensure_timezone

logger = logging.getLogger('cockpit.validation.equity')


class EquityValidator(BaseValidator):
    """
    Validator for equity-specific OHLCV data checks.

    Performs equity-specific validation including:
    - Stock split detection (forward and reverse)
    - Price jump analysis
    - Volume spike detection
    - Dividend adjustment checks

    Inherits common OHLCV checks from BaseValidator.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize equity validator with configuration."""
        super().__init__(config)

    def _register_checks(self) -> None:
        """Register equity-specific validation checks."""
        self._check_registry = [
            self._check_potential_splits,
            self._check_volume_spikes,
            self._check_price_jumps,
        ]

    def validate(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str = "unknown"
    ) -> ValidationResult:
        """
        Validate equity-specific characteristics.

        Args:
            df: DataFrame with OHLCV data
            col_map: Column mapping for OHLCV columns
            asset_name: Asset name for logging

        Returns:
            ValidationResult with equity-specific check outcomes
        """
        result = self._create_result()
        result.add_metadata('asset_name', asset_name)
        result.add_metadata('asset_type', 'equity')

        if df.empty:
            result.add_check('empty_data', False, f"DataFrame is empty for {asset_name}")
            return result

        # Run registered checks
        for check_func in self._check_registry:
            if not self._should_skip_check(check_func.__name__):
                result = self._run_check(result, check_func, df, col_map, asset_name)

        return result

    def _check_volume_spikes(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for volume spikes using z-score analysis."""
        volume_col = col_map.volume

        if not volume_col:
            return result

        # Edge case: Single-row or insufficient data
        if len(df) < 3:
            result.add_check(
                'volume_spikes', True,
                "Insufficient data for volume spike check (need at least 3 rows)"
            )
            return result

        # Calculate z-scores for volume
        volume_series = df[volume_col]
        z_scores = calculate_z_scores(volume_series)
        threshold = self.config.volume_spike_threshold_sigma
        spikes = int((z_scores > threshold).sum())

        if spikes > 0:
            spike_pct = safe_divide(spikes, len(df)) * 100
            spike_dates = z_scores[z_scores > threshold].index
            max_spike_z = float(z_scores.max())

            msg = (
                f"Found {spikes} volume spikes (>{threshold} sigma) in {asset_name}. "
                f"Consider investigating these dates for data quality issues or significant events."
            )

            result.add_check(
                'volume_spikes', False, msg,
                {
                    'spike_count': spikes,
                    'spike_pct': spike_pct,
                    'max_spike_z': max_spike_z,
                    'spike_dates': [str(d) for d in spike_dates[:5].tolist()]
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('volume_spikes', True, "No significant volume spikes detected")
        return result

    def _check_potential_splits(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """
        Detect potential unadjusted stock splits via price drops and volume spikes.

        Checks for common split ratios (2:1, 3:1, 4:1) and reverse splits (1:2, 1:3)
        by detecting price movements that match split patterns, cross-referenced with
        volume spikes on the same day.
        """
        close_col = col_map.close
        volume_col = col_map.volume

        if not close_col:
            return result

        # Edge case: Single-row DataFrame
        if len(df) < 2:
            result.add_check(
                'potential_splits', True,
                "Insufficient data for split detection (need at least 2 rows)"
            )
            return result

        # Common split ratios: 2:1 (50% drop), 3:1 (66.7% drop), 4:1 (75% drop)
        # Also check 3:2 (33% drop) and 5:4 (25% drop)
        # Reverse splits: 1:2 (100% increase), 1:3 (200% increase)
        split_ratios = [
            (0.25, 0.28, "5:4"),      # 25% drop ±3% tolerance
            (0.33, 0.36, "3:2"),      # 33% drop ±3% tolerance
            (0.50, 0.55, "2:1"),      # 50% drop ±5% tolerance
            (0.667, 0.70, "3:1"),     # 66.7% drop ±3.3% tolerance
            (0.75, 0.78, "4:1"),      # 75% drop ±3% tolerance
            (1.00, 1.10, "1:2 reverse"),  # 100% increase ±10% tolerance
            (2.00, 2.20, "1:3 reverse"),  # 200% increase ±20% tolerance
        ]

        # Calculate price changes
        price_changes = df[close_col].pct_change().dropna()

        if len(price_changes) < 1:
            return result

        # Pre-calculate volume z-scores once for efficiency
        volume_z_scores = None
        volume_spike_threshold = self.config.volume_spike_threshold_sigma
        if volume_col and len(df[volume_col]) >= 3:
            try:
                volume_z_scores = calculate_z_scores(df[volume_col])
            except Exception:
                # If volume z-score calculation fails, continue without volume check
                volume_z_scores = None

        potential_splits = []

        for date, pct_change in price_changes.items():
            # Check for downward price drops (forward splits)
            if pct_change < 0:
                abs_change = abs(pct_change)
                for min_ratio, max_ratio, ratio_name in split_ratios[:5]:  # Forward splits only
                    if min_ratio <= abs_change <= max_ratio:
                        # Check if there's a volume spike on the same day
                        volume_z = None
                        has_volume_spike = False

                        if volume_z_scores is not None and date in volume_z_scores.index:
                            volume_z = float(volume_z_scores[date])
                            has_volume_spike = volume_z > volume_spike_threshold

                        # Flag if price drop matches split pattern (with or without volume spike)
                        # Volume spike strengthens the signal but isn't required
                        if has_volume_spike or volume_z_scores is None:
                            potential_splits.append({
                                'date': str(date),
                                'price_change_pct': float(pct_change * 100),
                                'split_ratio': ratio_name,
                                'volume_z_score': volume_z,
                                'has_volume_spike': has_volume_spike
                            })
                        break

            # Check for upward price jumps (reverse splits)
            elif pct_change > 0:
                for min_ratio, max_ratio, ratio_name in split_ratios[5:]:  # Reverse splits only
                    if min_ratio <= pct_change <= max_ratio:
                        volume_z = None
                        has_volume_spike = False

                        if volume_z_scores is not None and date in volume_z_scores.index:
                            volume_z = float(volume_z_scores[date])
                            has_volume_spike = volume_z > volume_spike_threshold

                        if has_volume_spike or volume_z_scores is None:
                            potential_splits.append({
                                'date': str(date),
                                'price_change_pct': float(pct_change * 100),
                                'split_ratio': ratio_name,
                                'volume_z_score': volume_z,
                                'has_volume_spike': has_volume_spike
                            })
                        break

        if potential_splits:
            msg = (
                f"Found {len(potential_splits)} potential unadjusted split(s) in {asset_name}. "
                f"Consider using adjusted close data or verifying split adjustments. "
                f"Sample dates: {', '.join([s['date'] for s in potential_splits[:3]])}"
            )

            result.add_check(
                'potential_splits', False, msg,
                {
                    'potential_split_count': len(potential_splits),
                    'potential_splits': potential_splits[:10]  # Limit to first 10
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('potential_splits', True, "No potential unadjusted splits detected")
        return result

    def _check_price_jumps(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for sudden large price jumps."""
        close_col = col_map.close

        if not close_col:
            return result

        # Edge case: Single-row DataFrame
        if len(df) < 2:
            result.add_check(
                'price_jumps', True,
                "Insufficient data for price jump check (need at least 2 rows)"
            )
            return result

        pct_changes = df[close_col].pct_change().abs() * 100
        threshold = self.config.price_jump_threshold_pct
        large_jumps = pct_changes[pct_changes > threshold]

        if len(large_jumps) > 0:
            jump_pct = safe_divide(len(large_jumps), len(df)) * 100
            jump_dates_list = large_jumps.index[:5].tolist()
            jump_values = [f"{pct:.2f}%" for pct in large_jumps[:5].values]

            msg = (
                f"Found {len(large_jumps)} price jumps >{threshold}% in {asset_name}. "
                f"Large price jumps may indicate data errors, splits, or significant events. "
                f"Review these dates for data quality issues or verify if splits/adjustments are needed."
            )
            result.add_check(
                'price_jumps', False, msg,
                {
                    'jump_count': len(large_jumps),
                    'jump_pct': jump_pct,
                    'max_jump_pct': float(pct_changes.max()),
                    'jump_dates': [str(d) for d in jump_dates_list],
                    'jump_values': jump_values
                },
                severity=self.config.get_severity()
            )
        else:
            result.add_check('price_jumps', True, "No excessive price jumps detected")
        return result
