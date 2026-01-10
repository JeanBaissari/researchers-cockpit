"""
Pipeline utilities for trading strategies.

Provides functions to set up and manage Zipline Pipeline API usage.
This module centralizes pipeline validation and setup logic.

This module follows the Single Responsibility Principle by focusing solely
on pipeline configuration and validation, making it reusable across all strategies.
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    # Avoid circular imports - these are Zipline types
    from zipline.api import Context
    from zipline.pipeline import Pipeline

# Configure logging
logger = logging.getLogger(__name__)

# Pipeline availability check (set at module level for efficiency)
_PIPELINE_AVAILABLE = False
try:
    from zipline.api import attach_pipeline
    _PIPELINE_AVAILABLE = True
except ImportError:
    pass


def setup_pipeline(
    context: 'Context',
    params: dict,
    make_pipeline_func: Optional[Callable[[], Optional['Pipeline']]] = None
) -> bool:
    """
    Set up pipeline if enabled and available.

    This function:
    1. Checks if pipeline is enabled in parameters
    2. Validates pipeline availability in Zipline version
    3. Validates asset class compatibility (pipeline is primarily for equities)
    4. Attaches pipeline if all checks pass

    Args:
        context: Zipline context object (will be modified with pipeline state)
        params: Strategy parameters dictionary
        make_pipeline_func: Optional function that creates and returns a Pipeline.
                          If None, pipeline will not be attached even if enabled.

    Returns:
        bool: True if pipeline is active, False otherwise

    Example:
        >>> def make_pipeline():
        ...     from zipline.pipeline import Pipeline
        ...     from zipline.pipeline.factors import SimpleMovingAverage
        ...     from zipline.pipeline.data import EquityPricing
        ...     sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
        ...     return Pipeline(columns={'sma_30': sma})
        ...
        >>> context.use_pipeline = setup_pipeline(context, params, make_pipeline)
    """
    # Initialize pipeline state in context
    context.pipeline_data = None
    context.pipeline_universe = []
    
    # Check if pipeline is enabled in parameters
    use_pipeline = params.get('strategy', {}).get('use_pipeline', False)
    
    if not use_pipeline:
        context.use_pipeline = False
        logger.debug("Pipeline disabled in parameters")
        return False
    
    # Validate pipeline availability
    if not _PIPELINE_AVAILABLE:
        warnings.warn(
            "Pipeline API not available in this Zipline version. "
            "Setting use_pipeline to False. Pipeline is primarily designed for US equities.",
            UserWarning,
            stacklevel=2
        )
        context.use_pipeline = False
        return False
    
    # Validate asset class compatibility
    asset_class = params.get('strategy', {}).get('asset_class', 'equities')
    if asset_class != 'equities':
        warnings.warn(
            f"Pipeline API is primarily designed for US equities, but asset_class is '{asset_class}'. "
            "Consider setting use_pipeline: false for crypto/forex strategies.",
            UserWarning,
            stacklevel=2
        )
        # Don't disable pipeline, just warn - user may have valid use case
    
    # Attach pipeline if make_pipeline function is provided
    if make_pipeline_func is not None:
        try:
            pipeline = make_pipeline_func()
            if pipeline is not None:
                attach_pipeline(pipeline, 'my_pipeline')
                context.use_pipeline = True
                logger.debug("Pipeline attached successfully")
                return True
            else:
                logger.warning("make_pipeline() returned None. Pipeline not attached.")
                context.use_pipeline = False
                return False
        except Exception as e:
            logger.error(f"Error creating pipeline: {e}. Pipeline not attached.")
            warnings.warn(
                f"Failed to create pipeline: {e}. Setting use_pipeline to False.",
                UserWarning,
                stacklevel=2
            )
            context.use_pipeline = False
            return False
    else:
        # Pipeline enabled but no make_pipeline function provided
        logger.warning(
            "Pipeline enabled in parameters but no make_pipeline function provided. "
            "Pipeline not attached."
        )
        context.use_pipeline = False
        return False


def is_pipeline_available() -> bool:
    """
    Check if Pipeline API is available in the current Zipline installation.

    Returns:
        bool: True if Pipeline API is available, False otherwise
    """
    return _PIPELINE_AVAILABLE


def validate_pipeline_config(params: dict) -> tuple[bool, list[str]]:
    """
    Validate pipeline configuration without setting it up.

    Useful for pre-flight validation before backtest execution.

    Args:
        params: Strategy parameters dictionary

    Returns:
        Tuple of (is_valid, list_of_warnings)
        - is_valid: True if configuration is valid
        - list_of_warnings: List of warning messages (empty if valid)

    Example:
        >>> is_valid, warnings = validate_pipeline_config(params)
        >>> if not is_valid:
        ...     for warning in warnings:
        ...         print(f"Warning: {warning}")
    """
    warnings_list = []
    use_pipeline = params.get('strategy', {}).get('use_pipeline', False)
    
    if not use_pipeline:
        return True, warnings_list
    
    # Check availability
    if not _PIPELINE_AVAILABLE:
        warnings_list.append(
            "Pipeline API not available in this Zipline version. "
            "Pipeline will be disabled."
        )
        return False, warnings_list
    
    # Check asset class
    asset_class = params.get('strategy', {}).get('asset_class', 'equities')
    if asset_class != 'equities':
        warnings_list.append(
            f"Pipeline API is primarily designed for US equities, but asset_class is '{asset_class}'. "
            "Consider setting use_pipeline: false for crypto/forex strategies."
        )
        # Not a fatal error, just a warning
    
    return True, warnings_list

