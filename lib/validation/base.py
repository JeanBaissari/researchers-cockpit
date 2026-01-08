"""
Base validator abstract class.

Provides the BaseValidator ABC that all validators inherit from.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Callable

from .core import ValidationResult
from .config import ValidationConfig

logger = logging.getLogger('cockpit.validation')


class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    
    Provides common functionality and enforces consistent interface.
    Implements the Template Method pattern for validation workflow.
    
    Subclasses must implement:
    - _register_checks(): Register validation check methods
    - validate(): Perform validation and return results
    
    Attributes:
        config: ValidationConfig for this validator
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Validation configuration (uses defaults if None)
        """
        self.config = config or ValidationConfig()
        self._check_registry: List[Callable] = []
        self._register_checks()

    @abstractmethod
    def _register_checks(self) -> None:
        """Register validation checks. Must be overridden in subclasses."""
        pass

    @abstractmethod
    def validate(self, *args, **kwargs) -> ValidationResult:
        """Perform validation. Must be overridden in subclasses."""
        pass

    def _create_result(self) -> ValidationResult:
        """Create a new ValidationResult with common metadata."""
        result = ValidationResult()
        result.add_metadata('validator', self.__class__.__name__)
        result.add_metadata('config', {
            'strict_mode': self.config.strict_mode,
            'timeframe': self.config.timeframe
        })
        result.add_metadata('timestamp', datetime.utcnow().isoformat() + 'Z')
        result.add_metadata('timezone', 'UTC')
        result.add_metadata('timezone_aware', True)
        return result

    def _run_check(
        self,
        result: ValidationResult,
        check_func: Callable[..., ValidationResult],
        *args,
        **kwargs
    ) -> ValidationResult:
        """
        Run a single check with error handling.
        
        Catches any exceptions and logs them as warnings rather than
        failing the entire validation process.
        
        Args:
            result: ValidationResult to update
            check_func: Check function to run
            *args, **kwargs: Arguments for check function
            
        Returns:
            Updated ValidationResult
        """
        try:
            return check_func(result, *args, **kwargs)
        except Exception as e:
            check_name = check_func.__name__.replace('_check_', '')
            error_msg = f"Check '{check_name}' failed with error: {str(e)}"
            result.add_warning(error_msg)
            logger.warning(f"Validation check {check_name} raised exception: {e}", exc_info=True)
            return result

    def _should_skip_check(self, check_name: str) -> bool:
        """
        Determine if a check should be skipped based on configuration.
        
        Args:
            check_name: Name of the check function
            
        Returns:
            True if check should be skipped
        """
        config_map = {
            '_check_no_negative_values': self.config.check_negative_values,
            '_check_no_future_dates': self.config.check_future_dates,
            '_check_zero_volume': self.config.check_zero_volume,
            '_check_price_jumps': self.config.check_price_jumps,
            '_check_stale_data': self.config.check_stale_data,
            '_check_price_outliers': self.config.check_outliers,
            '_check_sorted_index': self.config.check_sorted_index,
            '_check_volume_spikes': self.config.check_volume_spikes,
            '_check_potential_splits': self.config.check_adjustments,
            '_check_sunday_bars': self.config.check_sunday_bars,
            '_check_weekend_gap_integrity': self.config.check_weekend_gaps,
        }
        return not config_map.get(check_name, True)

