"""
Anvyl Infrastructure Orchestrator - Self-hosted infrastructure management for Apple Silicon
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.dev"

# Import main components for easy access
from .sdk import client
from .database import models

__all__ = ["client", "models", "__version__"]