"""
Namespace Registry Module

Provides centralized registry management for all namespace modules with
taxonomy-compliant naming and instant execution capabilities.

Components:
- PlatformRegistryManager: Main registry management
- PlatformRegistryValidator: Registry validation
- PlatformRegistryCache: High-performance caching

Compliance:
- Taxonomy: All names follow taxonomy standards
- INSTANT: <100ms operations, 64-256 parallel support
"""

from .registry_manager import PlatformRegistryManager
from .registry_validator import PlatformRegistryValidator
from .registry_cache import PlatformRegistryCache

__all__ = [
    'PlatformRegistryManager',
    'PlatformRegistryValidator',
    'PlatformRegistryCache',
]

__version__ = '1.0.0'