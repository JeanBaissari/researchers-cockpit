"""
Risk management configuration validation.

Provides validation functions for the risk section of strategy parameters.
"""

from typing import List, Any


def validate_risk_section(risk: Any, errors: List[str]) -> None:
    """
    Validate the risk section of strategy parameters.
    
    Args:
        risk: Risk management configuration dictionary
        errors: List to append validation errors to
    """
    # Guard against risk being None
    if risk is None:
        errors.append("'risk' section is null/None")
        return
    
    if not isinstance(risk, dict):
        errors.append(f"'risk' section must be a dictionary, got {type(risk).__name__}")
        return
    
    if 'stop_loss_pct' in risk:
        stop_loss = risk['stop_loss_pct']
        if not isinstance(stop_loss, (int, float)):
            errors.append("'risk.stop_loss_pct' must be a number")
        elif stop_loss <= 0:
            errors.append(
                f"'risk.stop_loss_pct' must be positive. Got: {stop_loss}"
            )
        elif stop_loss > 1.0:
            errors.append(
                f"'risk.stop_loss_pct' should typically be <= 1.0 (100%). Got: {stop_loss}"
            )
    
    if 'take_profit_pct' in risk and 'stop_loss_pct' in risk:
        take_profit = risk['take_profit_pct']
        stop_loss = risk['stop_loss_pct']
        if isinstance(take_profit, (int, float)) and isinstance(stop_loss, (int, float)):
            if take_profit <= stop_loss:
                errors.append(
                    f"'risk.take_profit_pct' ({take_profit}) should be greater than "
                    f"'risk.stop_loss_pct' ({stop_loss})"
                )
    
    if 'use_stop_loss' in risk:
        if not isinstance(risk['use_stop_loss'], bool):
            errors.append("'risk.use_stop_loss' must be a boolean")
    
    if 'use_trailing_stop' in risk:
        if not isinstance(risk['use_trailing_stop'], bool):
            errors.append("'risk.use_trailing_stop' must be a boolean")
    
    if 'use_take_profit' in risk:
        if not isinstance(risk['use_take_profit'], bool):
            errors.append("'risk.use_take_profit' must be a boolean")
