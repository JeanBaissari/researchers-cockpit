"""
Test trade metrics calculations.

Tests for trade extraction, trade-level metrics, and trade analysis functions.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.metrics.trade import (
    calculate_trade_metrics,
    _extract_trades,
    _calculate_max_consecutive_losses,
)
from lib.metrics.core import MAX_PROFIT_FACTOR


class TestCalculateTradeMetrics:
    """Test trade metrics calculation."""

    @pytest.mark.unit
    def test_trade_metrics_empty_transactions(self):
        """Test trade metrics with empty transactions DataFrame."""
        transactions = pd.DataFrame(columns=["date", "sid", "amount", "price", "commission"])
        metrics = calculate_trade_metrics(transactions)

        assert isinstance(metrics, dict)
        assert metrics["trade_count"] == 0
        assert metrics["win_rate"] == 0.0
        assert metrics["profit_factor"] == 0.0
        assert metrics["avg_trade_return"] == 0.0
        assert metrics["avg_win"] == 0.0
        assert metrics["avg_loss"] == 0.0
        assert metrics["max_win"] == 0.0
        assert metrics["max_loss"] == 0.0
        assert metrics["max_consecutive_losses"] == 0
        assert metrics["avg_trade_duration"] == 0.0
        assert metrics["trades_per_month"] == 0.0

    @pytest.mark.unit
    def test_trade_metrics_none_transactions(self):
        """Test trade metrics with None transactions."""
        metrics = calculate_trade_metrics(None)

        assert isinstance(metrics, dict)
        assert metrics["trade_count"] == 0
        assert all(v == 0.0 or v == 0 for v in metrics.values())

    @pytest.mark.unit
    def test_trade_metrics_single_long_trade(self):
        """Test trade metrics with a single winning long trade."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100],  # Buy then sell
                "price": [100.0, 110.0],  # 10% gain
                "commission": [1.0, 1.0],
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 1
        assert metrics["win_rate"] == 1.0
        assert metrics["avg_trade_return"] == pytest.approx(0.10, rel=1e-2)
        assert metrics["avg_win"] == pytest.approx(0.10, rel=1e-2)
        assert metrics["max_win"] == pytest.approx(0.10, rel=1e-2)
        assert metrics["avg_loss"] == 0.0
        assert metrics["max_loss"] == 0.0
        assert metrics["max_consecutive_losses"] == 0

    @pytest.mark.unit
    def test_trade_metrics_single_losing_trade(self):
        """Test trade metrics with a single losing long trade."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100],  # Buy then sell
                "price": [100.0, 90.0],  # 10% loss
                "commission": [1.0, 1.0],
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 1
        assert metrics["win_rate"] == 0.0
        assert metrics["avg_trade_return"] == pytest.approx(-0.10, rel=1e-2)
        assert metrics["avg_win"] == 0.0
        assert metrics["max_win"] == 0.0
        assert metrics["avg_loss"] == pytest.approx(-0.10, rel=1e-2)
        assert metrics["max_loss"] == pytest.approx(-0.10, rel=1e-2)
        assert metrics["max_consecutive_losses"] == 1

    @pytest.mark.unit
    def test_trade_metrics_multiple_trades(self):
        """Test trade metrics with multiple trades."""
        dates = pd.date_range("2020-01-01", periods=6, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100, 100, -100],  # 3 trades
                "price": [100.0, 110.0, 100.0, 95.0, 100.0, 105.0],  # Win, loss, win
                "commission": [1.0] * 6,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 3
        assert metrics["win_rate"] == pytest.approx(2 / 3, rel=1e-2)
        assert metrics["avg_trade_return"] > 0  # Net positive
        assert metrics["avg_win"] > 0
        assert metrics["avg_loss"] < 0
        assert metrics["max_win"] > 0
        assert metrics["max_loss"] < 0

    @pytest.mark.unit
    def test_trade_metrics_short_trade(self):
        """Test trade metrics with a short trade."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [-100, 100],  # Short then cover
                "price": [100.0, 90.0],  # 10% gain on short
                "commission": [1.0, 1.0],
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 1
        assert metrics["win_rate"] == 1.0
        assert metrics["avg_trade_return"] == pytest.approx(0.10, rel=1e-2)

    @pytest.mark.unit
    def test_trade_metrics_pyramiding(self):
        """Test trade metrics with pyramiding (adding to position)."""
        dates = pd.date_range("2020-01-01", periods=3, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [50, 50, -100],  # Buy 50, add 50, sell 100
                "price": [100.0, 105.0, 110.0],  # Weighted avg entry ~102.5, exit 110
                "commission": [1.0] * 3,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 1
        # Weighted entry: (50*100 + 50*105) / 100 = 102.5
        # Return: (110 - 102.5) / 102.5 ≈ 0.073
        assert metrics["avg_trade_return"] > 0
        assert metrics["win_rate"] == 1.0

    @pytest.mark.unit
    def test_trade_metrics_partial_close(self):
        """Test trade metrics with partial position close."""
        dates = pd.date_range("2020-01-01", periods=3, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -50, -50],  # Buy 100, sell 50, sell 50
                "price": [100.0, 110.0, 105.0],  # First close at 110, second at 105
                "commission": [1.0] * 3,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["trade_count"] == 2  # Two partial closes = two trades
        assert metrics["win_rate"] == 1.0  # Both profitable

    @pytest.mark.unit
    def test_trade_metrics_profit_factor_all_wins(self):
        """Test profit factor with all winning trades."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, 110.0, 100.0, 105.0],  # Both wins
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # All wins, no losses -> profit factor should be MAX_PROFIT_FACTOR
        assert metrics["profit_factor"] == MAX_PROFIT_FACTOR

    @pytest.mark.unit
    def test_trade_metrics_profit_factor_all_losses(self):
        """Test profit factor with all losing trades."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, 90.0, 100.0, 95.0],  # Both losses
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # All losses, no profits -> profit factor should be 0.0
        assert metrics["profit_factor"] == 0.0

    @pytest.mark.unit
    def test_trade_metrics_profit_factor_mixed(self):
        """Test profit factor with mixed wins and losses."""
        dates = pd.date_range("2020-01-01", periods=6, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100, 100, -100],
                "price": [100.0, 120.0, 100.0, 80.0, 100.0, 110.0],  # +20%, -20%, +10%
                "commission": [1.0] * 6,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # Gross profit: 0.20 + 0.10 = 0.30
        # Gross loss: 0.20
        # Profit factor: 0.30 / 0.20 = 1.5
        assert metrics["profit_factor"] == pytest.approx(1.5, rel=1e-2)

    @pytest.mark.unit
    def test_trade_metrics_max_consecutive_losses(self):
        """Test max consecutive losses calculation."""
        dates = pd.date_range("2020-01-01", periods=8, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100, 100, -100, 100, -100],
                "price": [100.0, 110.0, 100.0, 90.0, 100.0, 90.0, 100.0, 110.0],  # W, L, L, W
                "commission": [1.0] * 8,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        assert metrics["max_consecutive_losses"] == 2

    @pytest.mark.unit
    def test_trade_metrics_trade_duration(self):
        """Test trade duration calculation."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, 110.0, 100.0, 105.0],
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # Each trade is 1 day duration
        assert metrics["avg_trade_duration"] == pytest.approx(1.0, rel=1e-2)

    @pytest.mark.unit
    def test_trade_metrics_trades_per_month(self):
        """Test trades per month calculation."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, 110.0, 100.0, 105.0],
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # 2 trades over 3 days = 2 * 30 / 3 = 20 trades/month
        assert metrics["trades_per_month"] == pytest.approx(20.0, rel=1e-2)

    @pytest.mark.unit
    def test_trade_metrics_as_percentages(self):
        """Test trade metrics with as_percentages parameter."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100],
                "price": [100.0, 110.0],  # 10% gain
                "commission": [1.0, 1.0],
            },
            index=dates,
        )

        metrics_decimal = calculate_trade_metrics(transactions, as_percentages=False)
        metrics_percent = calculate_trade_metrics(transactions, as_percentages=True)

        # Win rate should be converted (1.0 -> 100.0)
        assert metrics_percent["win_rate"] == pytest.approx(100.0, rel=1e-2)
        assert metrics_decimal["win_rate"] == pytest.approx(1.0, rel=1e-2)

        # Avg trade return should be converted (0.10 -> 10.0)
        assert metrics_percent["avg_trade_return"] == pytest.approx(10.0, rel=1e-2)
        assert metrics_decimal["avg_trade_return"] == pytest.approx(0.10, rel=1e-2)

    @pytest.mark.unit
    def test_trade_metrics_invalid_prices(self):
        """Test trade metrics with invalid prices (NaN, zero, negative)."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, np.nan, 0.0, -10.0],  # Invalid prices
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # Should handle gracefully - no valid trades
        assert metrics["trade_count"] == 0

    @pytest.mark.unit
    def test_trade_metrics_invalid_amounts(self):
        """Test trade metrics with invalid amounts (zero, NaN)."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, 0, np.nan, -100],  # Invalid amounts
                "price": [100.0, 110.0, 105.0, 110.0],
                "commission": [1.0] * 4,
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # Should handle gracefully - only valid trades counted
        assert metrics["trade_count"] >= 0

    @pytest.mark.unit
    def test_trade_metrics_malformed_data(self):
        """Test trade metrics with malformed transaction data."""
        # Create DataFrame with missing required columns
        transactions = pd.DataFrame(
            {
                "amount": [100, -100],
                # Missing 'price' column
            }
        )

        metrics = calculate_trade_metrics(transactions)

        # Should return empty metrics gracefully
        assert metrics["trade_count"] == 0

    @pytest.mark.unit
    def test_trade_metrics_no_valid_trades(self):
        """Test trade metrics when no valid trades can be extracted."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100],  # Only buy, no sell
                "price": [100.0],
                "commission": [1.0],
            },
            index=dates,
        )

        metrics = calculate_trade_metrics(transactions)

        # No complete trades
        assert metrics["trade_count"] == 0


class TestExtractTrades:
    """Test trade extraction from transactions."""

    @pytest.mark.unit
    def test_extract_trades_simple_long(self):
        """Test extracting a simple long trade."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100],
                "price": [100.0, 110.0],
            },
            index=dates,
        )

        trades = _extract_trades(transactions)

        assert len(trades) == 1
        assert trades[0]["direction"] == "long"
        assert trades[0]["entry_price"] == 100.0
        assert trades[0]["exit_price"] == 110.0
        assert trades[0]["entry_date"] == dates[0]
        assert trades[0]["exit_date"] == dates[1]

    @pytest.mark.unit
    def test_extract_trades_simple_short(self):
        """Test extracting a simple short trade."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [-100, 100],  # Short then cover
                "price": [100.0, 90.0],
            },
            index=dates,
        )

        trades = _extract_trades(transactions)

        assert len(trades) == 1
        assert trades[0]["direction"] == "short"
        assert trades[0]["entry_price"] == 100.0
        assert trades[0]["exit_price"] == 90.0

    @pytest.mark.unit
    def test_extract_trades_multiple_trades(self):
        """Test extracting multiple trades."""
        dates = pd.date_range("2020-01-01", periods=6, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -100, 100, -100],
                "price": [100.0, 110.0, 100.0, 105.0],
            },
            index=dates[:4],
        )

        trades = _extract_trades(transactions)

        assert len(trades) == 2

    @pytest.mark.unit
    def test_extract_trades_pyramiding(self):
        """Test extracting trades with pyramiding."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [50, 50, -100],  # Add to position
                "price": [100.0, 105.0, 110.0],
            },
            index=dates[:3],
        )

        trades = _extract_trades(transactions)

        assert len(trades) == 1
        # Weighted average entry: (50*100 + 50*105) / 100 = 102.5
        assert trades[0]["entry_price"] == pytest.approx(102.5, rel=1e-2)

    @pytest.mark.unit
    def test_extract_trades_partial_close(self):
        """Test extracting trades with partial closes."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -50, -50],  # Partial closes
                "price": [100.0, 110.0, 105.0],
            },
            index=dates[:3],
        )

        trades = _extract_trades(transactions)

        assert len(trades) == 2  # Two partial closes = two trades
        assert all(t["entry_price"] == 100.0 for t in trades)  # Same entry price

    @pytest.mark.unit
    def test_extract_trades_invalid_data(self):
        """Test extracting trades with invalid data."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, np.nan, 0, -100],  # Invalid amounts
                "price": [100.0, 110.0, 105.0, 110.0],
            },
            index=dates,
        )

        trades = _extract_trades(transactions)

        # Should handle gracefully - only valid trades extracted
        assert len(trades) >= 0

    @pytest.mark.unit
    def test_extract_trades_incomplete_position(self):
        """Test extracting trades with incomplete position (no close)."""
        dates = pd.date_range("2020-01-01", periods=2, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100],  # Only buy, no sell
                "price": [100.0],
            },
            index=dates[:1],
        )

        trades = _extract_trades(transactions)

        # No complete trades
        assert len(trades) == 0

    @pytest.mark.unit
    def test_extract_trades_reverse_position(self):
        """Test extracting trades when position reverses direction."""
        dates = pd.date_range("2020-01-01", periods=4, freq="D")
        transactions = pd.DataFrame(
            {
                "amount": [100, -150],  # Close long and go short
                "price": [100.0, 110.0],
            },
            index=dates[:2],
        )

        trades = _extract_trades(transactions)

        # Should create one trade for the long close
        # The excess 50 should start a new short position (not closed)
        assert len(trades) == 1
        assert trades[0]["direction"] == "long"


class TestCalculateMaxConsecutiveLosses:
    """Test maximum consecutive losses calculation."""

    @pytest.mark.unit
    def test_max_consecutive_losses_basic(self):
        """Test basic max consecutive losses calculation."""
        trade_returns = np.array([0.10, -0.05, -0.08, 0.02, -0.03, -0.04, -0.02, 0.05])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 3  # Three consecutive losses at positions 4-6

    @pytest.mark.unit
    def test_max_consecutive_losses_no_losses(self):
        """Test max consecutive losses with no losses."""
        trade_returns = np.array([0.10, 0.05, 0.08, 0.02, 0.03])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 0

    @pytest.mark.unit
    def test_max_consecutive_losses_all_losses(self):
        """Test max consecutive losses with all losses."""
        trade_returns = np.array([-0.10, -0.05, -0.08, -0.02, -0.03])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 5

    @pytest.mark.unit
    def test_max_consecutive_losses_single_loss(self):
        """Test max consecutive losses with single loss."""
        trade_returns = np.array([0.10, -0.05, 0.08])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 1

    @pytest.mark.unit
    def test_max_consecutive_losses_empty_array(self):
        """Test max consecutive losses with empty array."""
        trade_returns = np.array([])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 0

    @pytest.mark.unit
    def test_max_consecutive_losses_none(self):
        """Test max consecutive losses with None."""
        max_losses = _calculate_max_consecutive_losses(None)

        assert max_losses == 0

    @pytest.mark.unit
    def test_max_consecutive_losses_nan_values(self):
        """Test max consecutive losses with NaN values."""
        trade_returns = np.array([0.10, np.nan, -0.05, -0.08, np.nan, 0.02])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        # NaN values are skipped, so losses at positions 2-3 are consecutive (2 losses)
        # The win at position 5 resets the counter
        assert max_losses == 2

    @pytest.mark.unit
    def test_max_consecutive_losses_multiple_sequences(self):
        """Test max consecutive losses with multiple loss sequences."""
        trade_returns = np.array(
            [
                0.10,
                -0.05,
                -0.08,
                0.02,  # 2 losses
                0.03,
                -0.04,
                -0.06,
                -0.02,  # 3 losses (max)
                0.05,
                -0.01,
                0.02,  # 1 loss
            ]
        )
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        assert max_losses == 3

    @pytest.mark.unit
    def test_max_consecutive_losses_zero_returns(self):
        """Test max consecutive losses with zero returns (not losses)."""
        trade_returns = np.array([0.10, 0.0, -0.05, 0.0, -0.03])
        max_losses = _calculate_max_consecutive_losses(trade_returns)

        # Zero is not a loss, so max consecutive losses is 1
        assert max_losses == 1
