"""
Database models for Anvyl infrastructure orchestrator
"""

from datetime import datetime, UTC
from typing import Optional, Dict, List, Any
from sqlmodel import SQLModel, Field, create_engine, Session, select
import json
import logging

logger = logging.getLogger(__name__)

class Host(SQLModel, table=True):
    """Host model representing a macOS node in the Anvyl network."""

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    ip: str = Field(index=True)
    agents_installed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Enhanced host tracking fields
    os: Optional[str] = Field(default=None)
    last_seen: Optional[datetime] = Field(default=None)
    resources: Optional[str] = Field(default=None)  # JSON string for CPU, memory, disk info
    tags: Optional[str] = Field(default="[]")  # JSON array of tags
    netbird_ip: Optional[str] = Field(default=None)
    mac_address: Optional[str] = Field(default=None)
    os_version: Optional[str] = Field(default=None)
    architecture: Optional[str] = Field(default="arm64")  # Apple Silicon
    status: str = Field(default="online")  # online, offline, maintenance

    # Metadata as JSON - renamed to avoid SQLAlchemy conflict
    host_metadata: Optional[str] = Field(default=None)

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as a dictionary."""
        if not self.host_metadata:
            return {}
        try:
            return json.loads(self.host_metadata)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in host metadata for host {self.id}")
            return {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata from a dictionary."""
        self.host_metadata = json.dumps(metadata)
        self.updated_at = datetime.now(UTC)

    def get_resources(self) -> Dict[str, Any]:
        """Get resources as a dictionary."""
        if not self.resources:
            return {}
        try:
            return json.loads(self.resources)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in resources for host {self.id}")
            return {}

    def set_resources(self, resources: Dict[str, Any]) -> None:
        """Set resources from a dictionary."""
        self.resources = json.dumps(resources)
        self.updated_at = datetime.now(UTC)

    def get_tags(self) -> List[str]:
        """Get tags as list."""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in tags for host {self.id}")
            return []

    def set_tags(self, tags: List[str]) -> None:
        """Set tags from list."""
        self.tags = json.dumps(tags)
        self.updated_at = datetime.now(UTC)

    def has_agent(self, agent_name: str) -> bool:
        """Check if host has a specific agent installed (e.g., 'Beszel', 'Dozzle')."""
        # This would be determined by checking if agents with those names exist
        # For now, return the general agents_installed flag
        return self.agents_installed

class Container(SQLModel, table=True):
    """Container model representing Docker containers managed by Anvyl."""

    id: str = Field(primary_key=True)  # Docker container ID
    name: str = Field(index=True)
    image: str = Field(index=True)
    host_id: str = Field(foreign_key="host.id", index=True)
    status: str = Field(index=True)  # running, stopped, exited, etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Container configuration
    ports: str = Field(default="[]")  # JSON string of port mappings
    volumes: str = Field(default="[]")  # JSON string of volume mappings
    environment: str = Field(default="[]")  # JSON string of environment variables
    labels: str = Field(default="{}")  # JSON string of labels

    # Agent integration
    launched_by_agent_id: Optional[str] = Field(default=None, foreign_key="agent.id")

    # Runtime information
    started_at: Optional[datetime] = Field(default=None)
    stopped_at: Optional[datetime] = Field(default=None)
    exit_code: Optional[int] = Field(default=None)

    def get_ports(self) -> List[str]:
        """Get ports as list."""
        try:
            return json.loads(self.ports)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in ports for container {self.id}")
            return []

    def set_ports(self, ports: List[str]):
        """Set ports from list."""
        self.ports = json.dumps(ports)
        self.updated_at = datetime.now(UTC)

    def get_volumes(self) -> List[str]:
        """Get volumes as list."""
        try:
            return json.loads(self.volumes)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in volumes for container {self.id}")
            return []

    def set_volumes(self, volumes: List[str]):
        """Set volumes from list."""
        self.volumes = json.dumps(volumes)
        self.updated_at = datetime.now(UTC)

    def get_environment(self) -> List[str]:
        """Get environment variables as list."""
        try:
            return json.loads(self.environment)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in environment for container {self.id}")
            return []

    def set_environment(self, environment: List[str]):
        """Set environment variables from list."""
        self.environment = json.dumps(environment)
        self.updated_at = datetime.now(UTC)

    def get_labels(self) -> Dict[str, str]:
        """Get labels as dictionary."""
        try:
            return json.loads(self.labels)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in labels for container {self.id}")
            return {}

    def set_labels(self, labels: Dict[str, str]):
        """Set labels from dictionary."""
        self.labels = json.dumps(labels)
        self.updated_at = datetime.now(UTC)

class Agent(SQLModel, table=True):
    """Agent model representing Python agents running on hosts."""

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    host_id: str = Field(foreign_key="host.id", index=True)
    entrypoint: str = Field()  # Python module or script to run
    env: str = Field(default="[]")  # JSON string of environment variables
    container_id: Optional[str] = Field(default=None, foreign_key="container.id")  # If running in container
    status: str = Field(default="stopped", index=True)  # stopped, running, failed, starting
    persistent: bool = Field(default=True)  # Whether agent should be restarted on failure
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Runtime information
    started_at: Optional[datetime] = Field(default=None)
    stopped_at: Optional[datetime] = Field(default=None)
    exit_code: Optional[int] = Field(default=None)
    restart_count: int = Field(default=0)

    # Agent configuration
    working_directory: Optional[str] = Field(default=None)
    arguments: str = Field(default="[]")  # JSON string of command line arguments
    agent_metadata: Optional[str] = Field(default=None)  # JSON metadata

    def get_env(self) -> List[str]:
        """Get environment variables as list."""
        try:
            return json.loads(self.env)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in env for agent {self.id}")
            return []

    def set_env(self, env: List[str]):
        """Set environment variables from list."""
        self.env = json.dumps(env)
        self.updated_at = datetime.now(UTC)

    def get_arguments(self) -> List[str]:
        """Get arguments as list."""
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in arguments for agent {self.id}")
            return []

    def set_arguments(self, arguments: List[str]):
        """Set arguments from list."""
        self.arguments = json.dumps(arguments)
        self.updated_at = datetime.now(UTC)

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as a dictionary."""
        if not self.agent_metadata:
            return {}
        try:
            return json.loads(self.agent_metadata)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in agent metadata for agent {self.id}")
            return {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata from a dictionary."""
        self.agent_metadata = json.dumps(metadata)
        self.updated_at = datetime.now(UTC)

class DatabaseManager:
    """Database manager for Anvyl."""

    def __init__(self, database_url: str = "sqlite:///anvyl.db"):
        """Initialize database manager."""
        self.engine = create_engine(database_url, echo=False)
        self.create_tables()

    def create_tables(self):
        """Create all tables."""
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session."""
        return Session(self.engine)

    # Host management methods
    def add_host(self, host: Host) -> Host:
        """Add a host to the database."""
        with self.get_session() as session:
            session.add(host)
            session.commit()
            session.refresh(host)
            return host

    def get_host(self, host_id: str) -> Optional[Host]:
        """Get a host by ID."""
        with self.get_session() as session:
            return session.get(Host, host_id)

    def list_hosts(self) -> List[Host]:
        """List all hosts."""
        with self.get_session() as session:
            return list(session.exec(select(Host)).all())

    def update_host(self, host: Host) -> Host:
        """Update a host."""
        with self.get_session() as session:
            host.updated_at = datetime.now(UTC)
            session.add(host)
            session.commit()
            session.refresh(host)
            return host

    def update_host_heartbeat(self, host_id: str) -> bool:
        """Update host last_seen timestamp."""
        with self.get_session() as session:
            host = session.get(Host, host_id)
            if host:
                host.last_seen = datetime.now(UTC)
                host.status = "online"
                session.add(host)
                session.commit()
                return True
            return False

    def delete_host(self, host_id: str) -> bool:
        """Delete a host."""
        with self.get_session() as session:
            host = session.get(Host, host_id)
            if host:
                session.delete(host)
                session.commit()
                return True
            return False

    # Container management methods
    def add_container(self, container: Container) -> Container:
        """Add a container to the database."""
        with self.get_session() as session:
            session.add(container)
            session.commit()
            session.refresh(container)
            return container

    def get_container(self, container_id: str) -> Optional[Container]:
        """Get a container by ID."""
        with self.get_session() as session:
            return session.get(Container, container_id)

    def list_containers(self, host_id: Optional[str] = None) -> List[Container]:
        """List containers, optionally filtered by host."""
        with self.get_session() as session:
            if host_id:
                return list(session.exec(select(Container).where(Container.host_id == host_id)).all())
            else:
                return list(session.exec(select(Container)).all())

    def update_container(self, container: Container) -> Container:
        """Update a container."""
        with self.get_session() as session:
            container.updated_at = datetime.now(UTC)
            session.add(container)
            session.commit()
            session.refresh(container)
            return container

    def delete_container(self, container_id: str) -> bool:
        """Delete a container."""
        with self.get_session() as session:
            container = session.get(Container, container_id)
            if container:
                session.delete(container)
                session.commit()
                return True
            return False

    # Agent management methods
    def add_agent(self, agent: Agent) -> Agent:
        """Add an agent to the database."""
        with self.get_session() as session:
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        with self.get_session() as session:
            return session.get(Agent, agent_id)

    def list_agents(self, host_id: Optional[str] = None) -> List[Agent]:
        """List agents, optionally filtered by host."""
        with self.get_session() as session:
            if host_id:
                return list(session.exec(select(Agent).where(Agent.host_id == host_id)).all())
            else:
                return list(session.exec(select(Agent)).all())

    def update_agent(self, agent: Agent) -> Agent:
        """Update an agent."""
        with self.get_session() as session:
            agent.updated_at = datetime.now(UTC)
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        with self.get_session() as session:
            agent = session.get(Agent, agent_id)
            if agent:
                session.delete(agent)
                session.commit()
                return True
            return False