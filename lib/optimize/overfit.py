"""
Overfitting detection and scoring.

Provides metrics to assess the probability of overfitting in optimization results.
"""

from typing import Any, Dict


def calculate_overfit_score(
    in_sample_metric: float,
    out_sample_metric: float,
    n_trials: int
) -> Dict[str, Any]:
    """
    Calculate overfit probability score.
    
    Args:
        in_sample_metric: In-sample metric value
        out_sample_metric: Out-of-sample metric value
        n_trials: Number of trials/combinations tested
        
    Returns:
        Dictionary with overfit score and verdict
    """
    # Simple overfit score: ratio of OOS to IS performance
    if abs(in_sample_metric) > 1e-10:
        efficiency = out_sample_metric / in_sample_metric
    else:
        efficiency = 0.0
    
    # Probability of overfitting (simplified)
    # Lower efficiency = higher overfit probability
    if efficiency < 0.3:
        pbo = 0.8  # High probability of overfitting
        verdict = "high_overfit"
    elif efficiency < 0.5:
        pbo = 0.6
        verdict = "moderate_overfit"
    elif efficiency < 0.7:
        pbo = 0.4
        verdict = "acceptable"
    else:
        pbo = 0.2
        verdict = "robust"
    
    return {
        'efficiency': float(efficiency),
        'pbo': float(pbo),
        'verdict': verdict,
        'in_sample': float(in_sample_metric),
        'out_sample': float(out_sample_metric),
    }





