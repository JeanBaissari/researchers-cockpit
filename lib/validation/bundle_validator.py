"""
Bundle Validator.

Validates existing data bundles for integrity and consistency.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Callable

from .core import ValidationResult, ValidationSeverity
from .config import ValidationConfig
from .base import BaseValidator

logger = logging.getLogger('cockpit.validation')


class BundleValidator(BaseValidator):
    """
    Validates existing data bundles for integrity and consistency.
    
    Checks performed:
    - Bundle existence
    - Metadata file validity
    - Asset file presence
    - Data integrity
    
    Example:
        >>> validator = BundleValidator(bundle_path_resolver=lambda name: Path(f'bundles/{name}'))
        >>> result = validator.validate('my_bundle')
        >>> print(result.summary())
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        bundle_path_resolver: Optional[Callable[[str], Optional[Path]]] = None
    ):
        """
        Initialize bundle validator.
        
        Args:
            config: ValidationConfig object (uses default if None)
            bundle_path_resolver: Optional callable that takes bundle_name and returns Path.
                If None, attempts to use get_bundle_path from data_loader with lazy import.
                Falls back to None if data_loader is unavailable (graceful degradation).
        """
        super().__init__(config)
        if bundle_path_resolver is None:
            # Lazy import to avoid circular dependency
            try:
                from ..data_loader import get_bundle_path
                self.bundle_path_resolver = get_bundle_path
            except ImportError:
                self.bundle_path_resolver = None
        else:
            self.bundle_path_resolver = bundle_path_resolver

    def _register_checks(self) -> None:
        """Register bundle validation checks."""
        self._check_registry = [
            self._check_bundle_exists,
            self._check_bundle_metadata,
            self._check_bundle_assets,
        ]

    def validate(
        self,
        bundle_name: str,
        bundle_path: Optional[Path] = None
    ) -> ValidationResult:
        """
        Validate an existing bundle.

        Args:
            bundle_name: Name of the bundle
            bundle_path: Optional path to bundle directory

        Returns:
            ValidationResult
        """
        result = self._create_result()
        result.add_metadata('bundle_name', bundle_name)

        # Resolve bundle path using dependency injection
        if bundle_path is None:
            if self.bundle_path_resolver is not None:
                try:
                    bundle_path = self.bundle_path_resolver(bundle_name)
                except Exception as e:
                    result.add_warning(f"Error resolving bundle path with resolver: {e}")
                    bundle_path = None
            else:
                result.add_warning(
                    "No bundle_path provided and no bundle_path_resolver configured. "
                    "Please provide bundle_path or configure bundle_path_resolver in BundleValidator.__init__"
                )

        # Check bundle existence
        if not bundle_path or not bundle_path.exists():
            result.add_check(
                'bundle_exists', False,
                f"Bundle path does not exist: {bundle_path}"
            )
            return result

        result.add_check(
            'bundle_exists', True,
            f"Bundle '{bundle_name}' exists at {bundle_path}"
        )
        result.add_metadata('bundle_path', str(bundle_path))

        # Run remaining checks
        result = self._run_check(result, self._check_bundle_metadata, bundle_path)
        result = self._run_check(result, self._check_bundle_assets, bundle_path)

        return result

    def _check_bundle_exists(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check bundle directory exists (handled in validate_bundle)."""
        return result

    def _check_bundle_metadata(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check bundle metadata file exists and is valid."""
        metadata_path = bundle_path / 'metadata.json'

        if not metadata_path.exists():
            result.add_check(
                'bundle_metadata', False,
                f"Metadata file missing: {metadata_path}",
                severity=ValidationSeverity.WARNING
            )
            return result

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            required_fields = ['created_at', 'assets']
            missing_fields = [f for f in required_fields if f not in metadata]

            if missing_fields:
                result.add_check(
                    'bundle_metadata', False,
                    f"Missing metadata fields: {missing_fields}",
                    {'missing_fields': missing_fields},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check(
                    'bundle_metadata', True,
                    "Metadata is valid",
                    {'metadata_keys': list(metadata.keys())}
                )
                result.add_metadata('bundle_metadata', metadata)

        except json.JSONDecodeError as e:
            result.add_check('bundle_metadata', False, f"Invalid JSON: {e}")
        except Exception as e:
            result.add_check('bundle_metadata', False, f"Error reading metadata: {e}")

        return result

    def _check_bundle_assets(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check that bundle assets exist and are valid."""
        data_path = bundle_path / 'data'

        if not data_path.exists():
            # Try alternate locations
            alternate_paths = [bundle_path / 'assets', bundle_path]
            for alt_path in alternate_paths:
                if alt_path.exists():
                    data_path = alt_path
                    break
            else:
                result.add_check('bundle_assets', False, f"Data directory missing: {data_path}")
                return result

        # Find asset files
        asset_files = (
            list(data_path.glob('*.parquet')) +
            list(data_path.glob('*.csv')) +
            list(data_path.glob('*.h5'))
        )

        if len(asset_files) == 0:
            result.add_check('bundle_assets', False, "No asset files found in bundle")
            return result

        result.add_check(
            'bundle_assets', True,
            f"Found {len(asset_files)} asset files",
            {
                'asset_count': len(asset_files),
                'file_formats': list(set(f.suffix for f in asset_files))
            }
        )
        result.add_metadata('asset_count', len(asset_files))
        result.add_metadata('asset_files', [f.name for f in asset_files])

        return result

