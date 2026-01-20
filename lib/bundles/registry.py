"""
Bundle registry management for Zipline bundles.

Handles persistence and retrieval of bundle metadata.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils import get_project_root
from .utils import is_valid_date_string

logger = logging.getLogger(__name__)

# Store registered bundles to avoid re-registration
_registered_bundles: Set[str] = set()


def get_registered_bundles() -> Set[str]:
    """Get the set of currently registered bundles."""
    return _registered_bundles.copy()


def add_registered_bundle(bundle_name: str) -> None:
    """Add a bundle to the registered set."""
    _registered_bundles.add(bundle_name)


def discard_registered_bundle(bundle_name: str) -> None:
    """Remove a bundle from the registered set."""
    _registered_bundles.discard(bundle_name)


def get_bundle_registry_path() -> Path:
    """Get the path to the bundle registry file."""
    return Path.home() / '.zipline' / 'bundle_registry.json'


def load_bundle_registry() -> dict:
    """Load the bundle registry from disk."""
    registry_path = get_bundle_registry_path()
    if registry_path.exists():
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_bundle_registry(registry: dict) -> None:
    """Save the bundle registry to disk."""
    registry_path = get_bundle_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


def register_bundle_metadata(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily'
) -> None:
    """
    Persist bundle metadata to registry file.

    Args:
        bundle_name: Name of the bundle
        symbols: List of symbols in the bundle
        calendar_name: Trading calendar name
        start_date: Start date for data (YYYY-MM-DD format, validated)
        end_date: End date for data (YYYY-MM-DD format, validated)
        data_frequency: Zipline data frequency ('daily' or 'minute')
        timeframe: Actual data timeframe ('1m', '5m', '1h', 'daily', etc.)
    
    Note:
        Dates are validated before storage to prevent registry corruption.
        Invalid dates are stored as None rather than corrupted values.
    """
    registry = load_bundle_registry()
    
    # Validate dates before storing to prevent registry corruption
    validated_start_date = start_date if is_valid_date_string(start_date) else None
    validated_end_date = end_date if is_valid_date_string(end_date) else None
    
    # Log warning if dates were invalid
    if start_date and not validated_start_date:
        logger.warning(f"Invalid start_date '{start_date}' for bundle {bundle_name}, storing as None")
    if end_date and not validated_end_date:
        logger.warning(f"Invalid end_date '{end_date}' for bundle {bundle_name}, storing as None")
    
    registry[bundle_name] = {
        'symbols': symbols,
        'calendar_name': calendar_name,
        'start_date': validated_start_date,
        'end_date': validated_end_date,
        'data_frequency': data_frequency,
        'timeframe': timeframe,
        'registered_at': datetime.now().isoformat()
    }
    save_bundle_registry(registry)


def get_bundle_path(bundle_name: str) -> Path:
    """
    Get the path where a bundle should be stored.
    
    Args:
        bundle_name: Name of the bundle
        
    Returns:
        Path: Path to bundle directory
    """
    root = get_project_root()
    return root / 'data' / 'bundles' / bundle_name


def list_bundles() -> List[str]:
    """
    List all available Zipline bundles.
    
    Returns:
        list: List of bundle names
    """
    try:
        from zipline.data.bundles import bundles
        return list(bundles.keys())
    except ImportError:
        return []


def unregister_bundle(bundle_name: str) -> bool:
    """
    Unregister a bundle from Zipline's registry.

    This removes the bundle registration from Zipline's in-memory registry,
    allowing it to be re-registered with new parameters. Does not delete
    the bundle data from disk.

    Args:
        bundle_name: Name of the bundle to unregister

    Returns:
        True if bundle was unregistered, False if it wasn't registered
    """
    from zipline.data.bundles import bundles, unregister as zipline_unregister

    if bundle_name in bundles:
        zipline_unregister(bundle_name)
        discard_registered_bundle(bundle_name)
        return True
    return False















