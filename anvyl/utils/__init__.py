"""
Utility modules for Anvyl.
"""

from .service_manager import SimpleServiceManager, get_service_manager
BackgroundServiceManager = SimpleServiceManager

__all__ = [
    "SimpleServiceManager",
    "BackgroundServiceManager",
    "get_service_manager",
]