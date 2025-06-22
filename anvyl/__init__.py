"""
Anvyl - AI-Powered Infrastructure Management

A modern infrastructure management system that uses AI agents to manage
infrastructure across multiple hosts using modern AI/ML tools.
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.ai"

# Database models - these are safe to import
from anvyl.database import DatabaseManager, Host, Container

# Infrastructure client (async) - this is safe to import
from anvyl.infra.client import get_infrastructure_client

# Agent system - import lazily to avoid pydantic conflicts
def get_anvyl_agent():
    """Get the AnvylAgent class lazily to avoid import issues."""
    from anvyl.agent import AnvylAgent
    return AnvylAgent

__all__ = [
    "get_infrastructure_client",
    "get_anvyl_agent",
    "DatabaseManager",
    "Host",
    "Container",
    "__version__",
    "__author__",
    "__email__"
]