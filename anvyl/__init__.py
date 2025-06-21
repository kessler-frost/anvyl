"""
Anvyl - AI-Powered Infrastructure Management

A modern infrastructure management system that uses AI agents to manage
infrastructure across multiple hosts using modern AI/ML tools.
"""

__version__ = "0.1.0"
__author__ = "Anvyl Team"
__email__ = "team@anvyl.ai"

# Core infrastructure service
from anvyl.infra.infrastructure_service import get_infrastructure_service

# Agent system
from anvyl.agent import AgentManager, create_agent_manager, HostAgent

# Database models
from anvyl.database import DatabaseManager, Host, Container

# Infrastructure client (async)
from anvyl.infra.infrastructure_client import get_infrastructure_client

__all__ = [
    "get_infrastructure_service",
    "get_infrastructure_client",
    "AgentManager",
    "create_agent_manager",
    "HostAgent",
    "DatabaseManager",
    "Host",
    "Container",
    "__version__",
    "__author__",
    "__email__"
]