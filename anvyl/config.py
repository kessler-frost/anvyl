"""
Anvyl Configuration

This module provides centralized configuration management using pydantic-settings.
All default values for the Anvyl system are defined here.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnvylSettings(BaseSettings):
    """Centralized configuration for Anvyl."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Model Provider Configuration
    model_provider_url: str = "http://localhost:1234/v1"
    model_name: str = "qwen/qwen3-4b"

    # Infrastructure API Configuration
    infra_host: str = "127.0.0.1"
    infra_port: int = 4200

    # MCP Server Configuration
    mcp_server_url: str = "http://localhost:4201/mcp/"
    mcp_port: int = 4201

    # Agent Configuration
    agent_host: str = "127.0.0.1"
    agent_port: int = 4202
    agent_host_id: str = "local"

    # Database Configuration
    database_url: str = "sqlite:///anvyl.db"

    # Docker Configuration
    docker_host: Optional[str] = None  # Uses default Docker socket

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Service Management
    service_timeout: int = 30
    health_check_interval: int = 5

    # Development Configuration
    debug: bool = False
    reload: bool = False

    @property
    def infra_url(self) -> str:
        """Get the infrastructure API URL."""
        return f"http://{self.infra_host}:{self.infra_port}"

    @property
    def agent_url(self) -> str:
        """Get the agent API URL."""
        return f"http://{self.agent_host}:{self.agent_port}"


# Global settings instance
settings = AnvylSettings()


def get_settings() -> AnvylSettings:
    """Get the global settings instance."""
    return settings


def update_settings(**kwargs) -> None:
    """Update settings with new values."""
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)