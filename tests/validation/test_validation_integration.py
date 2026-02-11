"""
Integration tests for validation workflow.

Tests the complete validation pipeline from pre-ingestion through
post-backtest validation, ensuring all validators work together correctly.
"""

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from lib.validation import (
    validate_before_ingest,
    validate_csv_files_pre_ingestion,
    validate_backtest_results,
    verify_metrics_calculation,
    verify_returns_calculation,
    verify_positions_match_transactions,
    ValidationConfig,
    ValidationSeverity,
)


class TestPreIngestionWorkflow:
    """Test pre-ingestion validation workflow."""

    def test_pre_ingest_validation_workflow(self):
        """Test complete pre-ingestion validation workflow."""
        # Create sample OHLCV data
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        # Validate with default config
        result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
        )

        assert result.passed
        assert len(result.checks) > 0

    def test_pre_ingest_validation_with_strict_config(self):
        """Test pre-ingestion validation with strict configuration."""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        config = ValidationConfig.strict(timeframe="1d")
        result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
            config=config,
        )

        assert result.passed

    def test_pre_ingest_validation_detects_issues(self):
        """Test pre-ingestion validation detects data quality issues."""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [
                    99.0,
                    102.0,
                    103.0,
                    104.0,
                    105.0,
                    106.0,
                    107.0,
                    108.0,
                    109.0,
                    110.0,
                ],  # High < low on first row
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
        )

        assert not result.passed
        assert len(result.error_checks) > 0


class TestPostBacktestWorkflow:
    """Test post-backtest validation workflow."""

    def test_backtest_results_validation_workflow(self):
        """Test complete post-backtest validation workflow."""
        # Create sample backtest results
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")

        perf_df = pd.DataFrame(
            {
                "portfolio_value": [
                    100000.0,
                    100500.0,
                    101000.0,
                    101500.0,
                    102000.0,
                    102500.0,
                    103000.0,
                    103500.0,
                    104000.0,
                    104500.0,
                ],
                "returns": [
                    0.0,
                    0.005,
                    0.0049751,
                    0.004950495,
                    0.00492610837,
                    0.00490196078,
                    0.00487804878,
                    0.00485436893,
                    0.00483091787,
                    0.00480769231,
                ],
            },
            index=dates,
        )

        transactions_df = pd.DataFrame(
            {
                "dt": dates[:5],
                "sid": [1, 1, 1, 1, 1],
                "amount": [10, 10, 10, 10, 10],
                "price": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        positions_df = pd.DataFrame(
            {
                "amount": [10, 20, 30, 40, 50, 50, 50, 50, 50, 50],
                "last_sale_price": [
                    100.0,
                    101.0,
                    102.0,
                    103.0,
                    104.0,
                    105.0,
                    106.0,
                    107.0,
                    108.0,
                    109.0,
                ],
            },
            index=dates,
        )

        result = validate_backtest_results(perf_df, transactions_df, positions_df)

        assert result.passed
        assert len(result.checks) > 0

    def test_returns_calculation_verification(self):
        """Test returns calculation verification."""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")

        returns = pd.Series(
            [
                0.0,
                0.005,
                0.0049751,
                0.004950495,
                0.00492610837,
                0.00490196078,
                0.00487804878,
                0.00485436893,
                0.00483091787,
                0.00480769231,
            ],
            index=dates,
        )

        transactions_df = pd.DataFrame(
            {
                "dt": dates[:5],
                "sid": [1, 1, 1, 1, 1],
                "amount": [10, 10, 10, 10, 10],
                "price": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        is_valid, error_msg = verify_returns_calculation(returns, transactions_df)

        assert is_valid, f"Returns validation failed: {error_msg}"

    def test_positions_transactions_verification(self):
        """Test positions match transactions verification."""
        dates = pd.date_range("2024-01-01", "2024-01-05", freq="1d", tz="UTC")

        transactions_df = pd.DataFrame(
            {
                "dt": dates,
                "sid": [1, 1, 1, 1, 1],
                "amount": [10, 10, 10, 10, 10],
                "price": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        positions_df = pd.DataFrame(
            {
                "amount": [10, 20, 30, 40, 50],
                "last_sale_price": [100.0, 101.0, 102.0, 103.0, 104.0],
            },
            index=dates,
        )

        is_valid, error_msg = verify_positions_match_transactions(positions_df, transactions_df)

        assert is_valid, f"Position verification failed: {error_msg}"


class TestEndToEndValidation:
    """Test end-to-end validation workflows."""

    def test_complete_validation_pipeline(self):
        """Test complete validation pipeline from pre-ingest to post-backtest."""
        # 1. Pre-ingestion validation
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        pre_ingest_result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
        )

        assert pre_ingest_result.passed, "Pre-ingestion validation failed"

        # 2. Post-backtest validation
        perf_df = pd.DataFrame(
            {
                "portfolio_value": [
                    100000.0,
                    100500.0,
                    101000.0,
                    101500.0,
                    102000.0,
                    102500.0,
                    103000.0,
                    103500.0,
                    104000.0,
                    104500.0,
                ],
                "returns": [
                    0.0,
                    0.005,
                    0.0049751,
                    0.004950495,
                    0.00492610837,
                    0.00490196078,
                    0.00487804878,
                    0.00485436893,
                    0.00483091787,
                    0.00480769231,
                ],
            },
            index=dates,
        )

        transactions_df = pd.DataFrame(
            {
                "dt": dates[:5],
                "sid": [1, 1, 1, 1, 1],
                "amount": [10, 10, 10, 10, 10],
                "price": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        positions_df = pd.DataFrame(
            {
                "amount": [10, 20, 30, 40, 50, 50, 50, 50, 50, 50],
                "last_sale_price": [
                    100.0,
                    101.0,
                    102.0,
                    103.0,
                    104.0,
                    105.0,
                    106.0,
                    107.0,
                    108.0,
                    109.0,
                ],
            },
            index=dates,
        )

        backtest_result = validate_backtest_results(perf_df, transactions_df, positions_df)

        assert backtest_result.passed, "Post-backtest validation failed"

        # 3. Verify all validation stages passed
        assert pre_ingest_result.passed and backtest_result.passed


class TestAssetSpecificValidation:
    """Test asset-specific validation rules."""

    def test_equity_validation(self):
        """Test equity-specific validation."""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        result = validate_before_ingest(
            df=df,
            asset_name="AAPL",
            timeframe="1d",
            asset_type="equity",
        )

        assert result.passed

    def test_crypto_validation(self):
        """Test crypto-specific validation."""
        # Create 24/7 crypto data
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1h", tz="UTC")
        df = pd.DataFrame(
            {
                "open": np.random.uniform(30000, 35000, len(dates)),
                "high": np.random.uniform(30000, 35000, len(dates)),
                "low": np.random.uniform(30000, 35000, len(dates)),
                "close": np.random.uniform(30000, 35000, len(dates)),
                "volume": np.random.uniform(100, 1000, len(dates)),
            },
            index=dates,
        )

        # Ensure OHLC consistency
        df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
        df["low"] = df[["open", "high", "low", "close"]].min(axis=1)

        result = validate_before_ingest(
            df=df,
            asset_name="BTCUSD",
            timeframe="1h",
            asset_type="crypto",
        )

        assert result.passed or len(result.warning_checks) > 0

    def test_forex_validation(self):
        """Test forex-specific validation."""
        # Create 24/5 forex data (Monday to Friday)
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1h", tz="UTC")
        # Filter to weekdays only
        dates = dates[dates.dayofweek < 5]

        df = pd.DataFrame(
            {
                "open": np.random.uniform(1.08, 1.12, len(dates)),
                "high": np.random.uniform(1.08, 1.12, len(dates)),
                "low": np.random.uniform(1.08, 1.12, len(dates)),
                "close": np.random.uniform(1.08, 1.12, len(dates)),
                "volume": np.random.uniform(1000, 10000, len(dates)),
            },
            index=dates,
        )

        # Ensure OHLC consistency
        df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
        df["low"] = df[["open", "high", "low", "close"]].min(axis=1)

        result = validate_before_ingest(
            df=df,
            asset_name="EURUSD",
            timeframe="1h",
            asset_type="forex",
        )

        assert result.passed or len(result.warning_checks) > 0


class TestValidationConfigurationOptions:
    """Test validation with different configuration options."""

    def test_strict_vs_lenient_validation(self):
        """Test strict vs lenient validation configurations."""
        dates = pd.date_range("2024-01-01", "2024-01-05", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000000] * 5,
            },
            index=dates,
        )

        # Strict validation
        strict_config = ValidationConfig.strict(timeframe="1d")
        strict_result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
            config=strict_config,
        )

        # Lenient validation
        lenient_config = ValidationConfig.lenient(timeframe="1d")
        lenient_result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
            config=lenient_config,
        )

        # Both should pass for valid data
        assert strict_result.passed
        assert lenient_result.passed

    def test_custom_validation_config(self):
        """Test custom validation configuration."""
        dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
                "volume": [1000000] * 10,
            },
            index=dates,
        )

        config = ValidationConfig(
            timeframe="1d",
            gap_tolerance_days=5,
            outlier_threshold_sigma=5.0,
            suggest_fixes=True,
        )

        result = validate_before_ingest(
            df=df,
            asset_name="TEST",
            timeframe="1d",
            asset_type="equity",
            config=config,
        )

        assert result.passed
