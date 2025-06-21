"""
Utilities Package

This package provides utility functions and classes for Anvyl,
including background service management and other helper functionality.
"""

from .background_service import BackgroundServiceManager, get_service_manager

__all__ = [
    "BackgroundServiceManager",
    "get_service_manager"
]