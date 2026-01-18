"""
Main bundle API for The Researcher's Cockpit.

Provides the primary public interface for bundle ingestion and loading.
Refactored in v1.0.11 to split management and access into separate modules.
"""

# Import from refactored modules
from .management import ingest_bundle
from .access import load_bundle, get_bundle_symbols

# Re-export for backward compatibility
__all__ = [
    'ingest_bundle',
    'load_bundle',
    'get_bundle_symbols',
]
