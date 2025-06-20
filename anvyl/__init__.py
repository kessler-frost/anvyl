"""
Anvyl Infrastructure Orchestrator

A self-hosted infrastructure management platform designed specifically for Apple Silicon,
providing container orchestration capabilities.
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.dev"

from .infrastructure_service import get_infrastructure_service

__all__ = [
    "get_infrastructure_service",
    "__version__",
    "__author__",
    "__email__"
]