"""
Test overfitting detection and scoring.

Tests for overfitting detection functionality.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize.overfit import calculate_overfit_score


class TestCalculateOverfitScore:
    """Test calculate_overfit_score function."""

    @pytest.mark.unit
    def test_function_exists(self):
        """Test that calculate_overfit_score function exists."""
        assert calculate_overfit_score is not None
        assert callable(calculate_overfit_score)

    @pytest.mark.unit
    def test_return_type(self):
        """Test that function returns a dictionary."""
        result = calculate_overfit_score(1.0, 0.5, 100)
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_return_structure(self):
        """Test that return dictionary has required keys."""
        result = calculate_overfit_score(1.0, 0.5, 100)

        required_keys = ["efficiency", "pbo", "verdict", "in_sample", "out_sample"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.unit
    def test_high_overfit_verdict(self):
        """Test high overfit verdict (efficiency < 0.3)."""
        # Efficiency = 0.2 / 1.0 = 0.2 (< 0.3)
        result = calculate_overfit_score(1.0, 0.2, 100)

        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8
        assert result["efficiency"] == pytest.approx(0.2)
        assert result["in_sample"] == 1.0
        assert result["out_sample"] == 0.2

    @pytest.mark.unit
    def test_moderate_overfit_verdict(self):
        """Test moderate overfit verdict (0.3 <= efficiency < 0.5)."""
        # Efficiency = 0.4 / 1.0 = 0.4 (0.3 <= x < 0.5)
        result = calculate_overfit_score(1.0, 0.4, 100)

        assert result["verdict"] == "moderate_overfit"
        assert result["pbo"] == 0.6
        assert result["efficiency"] == pytest.approx(0.4)

    @pytest.mark.unit
    def test_acceptable_verdict(self):
        """Test acceptable verdict (0.5 <= efficiency < 0.7)."""
        # Efficiency = 0.6 / 1.0 = 0.6 (0.5 <= x < 0.7)
        result = calculate_overfit_score(1.0, 0.6, 100)

        assert result["verdict"] == "acceptable"
        assert result["pbo"] == 0.4
        assert result["efficiency"] == pytest.approx(0.6)

    @pytest.mark.unit
    def test_robust_verdict(self):
        """Test robust verdict (efficiency >= 0.7)."""
        # Efficiency = 0.8 / 1.0 = 0.8 (>= 0.7)
        result = calculate_overfit_score(1.0, 0.8, 100)

        assert result["verdict"] == "robust"
        assert result["pbo"] == 0.2
        assert result["efficiency"] == pytest.approx(0.8)

    @pytest.mark.unit
    def test_efficiency_boundary_0_3(self):
        """Test efficiency boundary at 0.3."""
        # Just below 0.3
        result_below = calculate_overfit_score(1.0, 0.29, 100)
        assert result_below["verdict"] == "high_overfit"
        assert result_below["pbo"] == 0.8

        # Exactly at 0.3
        result_at = calculate_overfit_score(1.0, 0.3, 100)
        assert result_at["verdict"] == "moderate_overfit"
        assert result_at["pbo"] == 0.6

    @pytest.mark.unit
    def test_efficiency_boundary_0_5(self):
        """Test efficiency boundary at 0.5."""
        # Just below 0.5
        result_below = calculate_overfit_score(1.0, 0.49, 100)
        assert result_below["verdict"] == "moderate_overfit"
        assert result_below["pbo"] == 0.6

        # Exactly at 0.5
        result_at = calculate_overfit_score(1.0, 0.5, 100)
        assert result_at["verdict"] == "acceptable"
        assert result_at["pbo"] == 0.4

    @pytest.mark.unit
    def test_efficiency_boundary_0_7(self):
        """Test efficiency boundary at 0.7."""
        # Just below 0.7
        result_below = calculate_overfit_score(1.0, 0.69, 100)
        assert result_below["verdict"] == "acceptable"
        assert result_below["pbo"] == 0.4

        # Exactly at 0.7
        result_at = calculate_overfit_score(1.0, 0.7, 100)
        assert result_at["verdict"] == "robust"
        assert result_at["pbo"] == 0.2

    @pytest.mark.unit
    def test_zero_in_sample_metric(self):
        """Test handling of zero in-sample metric."""
        # When in_sample is 0, efficiency should be 0.0
        result = calculate_overfit_score(0.0, 0.5, 100)

        assert result["efficiency"] == 0.0
        assert result["verdict"] == "high_overfit"  # efficiency 0.0 < 0.3
        assert result["pbo"] == 0.8
        assert result["in_sample"] == 0.0
        assert result["out_sample"] == 0.5

    @pytest.mark.unit
    def test_very_small_in_sample_metric(self):
        """Test handling of very small in-sample metric."""
        # Very small in_sample (below threshold 1e-10)
        result = calculate_overfit_score(1e-11, 0.5, 100)

        assert result["efficiency"] == 0.0
        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8

    @pytest.mark.unit
    def test_negative_metrics(self):
        """Test handling of negative metrics."""
        # Negative in_sample and out_sample
        result = calculate_overfit_score(-1.0, -0.5, 100)

        # Efficiency = -0.5 / -1.0 = 0.5
        assert result["efficiency"] == pytest.approx(0.5)
        assert result["verdict"] == "acceptable"
        assert result["in_sample"] == -1.0
        assert result["out_sample"] == -0.5

    @pytest.mark.unit
    def test_negative_out_sample_positive_in_sample(self):
        """Test handling of negative out-sample with positive in-sample."""
        # Negative out_sample, positive in_sample
        result = calculate_overfit_score(1.0, -0.5, 100)

        # Efficiency = -0.5 / 1.0 = -0.5
        # Since -0.5 < 0.3, verdict should be 'high_overfit'
        assert result["efficiency"] == pytest.approx(-0.5)
        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8

    @pytest.mark.unit
    def test_positive_out_sample_negative_in_sample(self):
        """Test handling of positive out-sample with negative in-sample."""
        # Positive out_sample, negative in_sample
        result = calculate_overfit_score(-1.0, 0.5, 100)

        # Efficiency = 0.5 / -1.0 = -0.5
        assert result["efficiency"] == pytest.approx(-0.5)
        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8

    @pytest.mark.unit
    def test_perfect_efficiency(self):
        """Test perfect efficiency (out_sample == in_sample)."""
        result = calculate_overfit_score(1.0, 1.0, 100)

        assert result["efficiency"] == pytest.approx(1.0)
        assert result["verdict"] == "robust"
        assert result["pbo"] == 0.2

    @pytest.mark.unit
    def test_better_out_sample_than_in_sample(self):
        """Test when out-sample performs better than in-sample."""
        # Out-sample is better (efficiency > 1.0)
        result = calculate_overfit_score(1.0, 1.5, 100)

        assert result["efficiency"] == pytest.approx(1.5)
        assert result["verdict"] == "robust"
        assert result["pbo"] == 0.2

    @pytest.mark.unit
    def test_n_trials_parameter(self):
        """Test that n_trials parameter is accepted (even if not used in calculation)."""
        # n_trials doesn't affect calculation but should be accepted
        result1 = calculate_overfit_score(1.0, 0.5, 10)
        result2 = calculate_overfit_score(1.0, 0.5, 1000)

        # Results should be identical regardless of n_trials
        assert result1["efficiency"] == result2["efficiency"]
        assert result1["verdict"] == result2["verdict"]
        assert result1["pbo"] == result2["pbo"]

    @pytest.mark.unit
    def test_return_value_types(self):
        """Test that return values are correct types."""
        result = calculate_overfit_score(1.0, 0.5, 100)

        assert isinstance(result["efficiency"], float)
        assert isinstance(result["pbo"], float)
        assert isinstance(result["verdict"], str)
        assert isinstance(result["in_sample"], float)
        assert isinstance(result["out_sample"], float)

    @pytest.mark.unit
    def test_large_metric_values(self):
        """Test handling of large metric values."""
        result = calculate_overfit_score(1000.0, 500.0, 100)

        assert result["efficiency"] == pytest.approx(0.5)
        assert result["verdict"] == "acceptable"
        assert result["in_sample"] == 1000.0
        assert result["out_sample"] == 500.0

    @pytest.mark.unit
    def test_very_small_metric_values(self):
        """Test handling of very small metric values."""
        result = calculate_overfit_score(0.001, 0.0005, 100)

        assert result["efficiency"] == pytest.approx(0.5)
        assert result["verdict"] == "acceptable"
        assert result["in_sample"] == 0.001
        assert result["out_sample"] == 0.0005

    @pytest.mark.unit
    def test_zero_out_sample(self):
        """Test handling of zero out-sample metric."""
        result = calculate_overfit_score(1.0, 0.0, 100)

        assert result["efficiency"] == pytest.approx(0.0)
        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8
        assert result["out_sample"] == 0.0

    @pytest.mark.unit
    def test_both_zero(self):
        """Test handling when both metrics are zero."""
        result = calculate_overfit_score(0.0, 0.0, 100)

        assert result["efficiency"] == 0.0
        assert result["verdict"] == "high_overfit"
        assert result["pbo"] == 0.8
        assert result["in_sample"] == 0.0
        assert result["out_sample"] == 0.0

    @pytest.mark.unit
    def test_efficiency_calculation_accuracy(self):
        """Test efficiency calculation accuracy."""
        # Test various ratios
        test_cases = [
            (1.0, 0.1, 0.1),
            (1.0, 0.25, 0.25),
            (1.0, 0.35, 0.35),
            (1.0, 0.45, 0.45),
            (1.0, 0.55, 0.55),
            (1.0, 0.65, 0.65),
            (1.0, 0.75, 0.75),
            (2.0, 1.0, 0.5),
            (10.0, 7.0, 0.7),
        ]

        for in_sample, out_sample, expected_efficiency in test_cases:
            result = calculate_overfit_score(in_sample, out_sample, 100)
            assert result["efficiency"] == pytest.approx(expected_efficiency), (
                f"Failed for in_sample={in_sample}, out_sample={out_sample}"
            )

    @pytest.mark.unit
    def test_pbo_values(self):
        """Test that PBO values are correct for each verdict."""
        test_cases = [
            (1.0, 0.1, 0.8, "high_overfit"),
            (1.0, 0.4, 0.6, "moderate_overfit"),
            (1.0, 0.6, 0.4, "acceptable"),
            (1.0, 0.8, 0.2, "robust"),
        ]

        for in_sample, out_sample, expected_pbo, expected_verdict in test_cases:
            result = calculate_overfit_score(in_sample, out_sample, 100)
            assert result["pbo"] == expected_pbo, (
                f"PBO mismatch for in_sample={in_sample}, out_sample={out_sample}"
            )
            assert result["verdict"] == expected_verdict, (
                f"Verdict mismatch for in_sample={in_sample}, out_sample={out_sample}"
            )

    @pytest.mark.unit
    def test_verdict_consistency(self):
        """Test that verdict is consistent with efficiency thresholds."""
        # Test all verdict categories
        verdicts = {
            "high_overfit": [(1.0, 0.1), (1.0, 0.2), (1.0, 0.29)],
            "moderate_overfit": [(1.0, 0.3), (1.0, 0.4), (1.0, 0.49)],
            "acceptable": [(1.0, 0.5), (1.0, 0.6), (1.0, 0.69)],
            "robust": [(1.0, 0.7), (1.0, 0.8), (1.0, 0.9), (1.0, 1.0)],
        }

        for expected_verdict, test_cases in verdicts.items():
            for in_sample, out_sample in test_cases:
                result = calculate_overfit_score(in_sample, out_sample, 100)
                assert result["verdict"] == expected_verdict, (
                    f"Verdict mismatch: expected {expected_verdict}, got {result['verdict']} "
                    f"for in_sample={in_sample}, out_sample={out_sample}"
                )
