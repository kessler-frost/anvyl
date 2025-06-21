"""
Anvyl - AI-Powered Infrastructure Management

A modern infrastructure management system that uses AI agents to manage
infrastructure across multiple hosts using modern AI/ML tools.
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.ai"

# Agent system
from anvyl.agent import HostAgent

# Database models
from anvyl.database import DatabaseManager, Host, Container

# Infrastructure client (async)
from anvyl.infra.client import get_infrastructure_client

__all__ = [
    "get_infrastructure_client",
    "HostAgent",
    "DatabaseManager",
    "Host",
    "Container",
    "__version__",
    "__author__",
    "__email__"
]