"""
Composite Validator.

Combines multiple validators for comprehensive validation.
"""

import logging
from typing import Optional, List

from .core import ValidationResult
from .base import BaseValidator

logger = logging.getLogger('cockpit.validation')


class CompositeValidator:
    """
    Combines multiple validators for comprehensive validation.
    
    Implements the Composite pattern to run validation pipelines.
    
    Example:
        >>> composite = CompositeValidator([
        ...     DataValidator(timeframe='1d'),
        ...     SchemaValidator(required_columns=['open', 'close'])
        ... ])
        >>> result = composite.validate(df)
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize composite validator.
        
        Args:
            validators: List of validators to run
        """
        self.validators: List[BaseValidator] = validators or []

    def add_validator(self, validator: BaseValidator) -> 'CompositeValidator':
        """
        Add a validator to the pipeline.
        
        Args:
            validator: Validator to add
            
        Returns:
            Self for method chaining
        """
        self.validators.append(validator)
        return self

    def validate(self, *args, **kwargs) -> ValidationResult:
        """
        Run all validators and merge results.
        
        Args:
            *args, **kwargs: Arguments passed to each validator
            
        Returns:
            Merged ValidationResult
        """
        result = ValidationResult()
        result.add_metadata('validator', 'CompositeValidator')
        result.add_metadata('validator_count', len(self.validators))

        for i, validator in enumerate(self.validators):
            try:
                validator_name = validator.__class__.__name__
                validator_result = validator.validate(*args, **kwargs)
                result.merge(validator_result)
                result.add_info(f"Completed {validator_name} ({i + 1}/{len(self.validators)})")
            except Exception as e:
                error_msg = f"Validator {validator.__class__.__name__} failed: {e}"
                result.add_warning(error_msg)
                logger.warning(f"Composite validation error: {e}", exc_info=True)

        return result





