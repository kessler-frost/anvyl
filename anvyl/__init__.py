"""
Anvyl Infrastructure Orchestrator

A self-hosted infrastructure management platform designed specifically for Apple Silicon,
providing AI-powered automation and container orchestration capabilities.
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.dev"

from .infrastructure_service import get_infrastructure_service
from .agent_manager import get_agent_manager
from .ai_agent import create_ai_agent

__all__ = [
    "get_infrastructure_service",
    "get_agent_manager",
    "create_ai_agent",
    "__version__",
    "__author__",
    "__email__"
]