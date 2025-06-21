"""
Database models for Anvyl infrastructure orchestrator
"""

from datetime import datetime, UTC
from typing import Optional, Dict, List, Any
from sqlmodel import SQLModel, Field, create_engine, Session, select
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Host(SQLModel, table=True):
    """Host model representing a macOS node in the Anvyl network."""

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    ip: str = Field(index=True)
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

class Container(SQLModel, table=True):
    """Container model representing containers managed by Anvyl."""

    id: str = Field(primary_key=True)  # Container ID
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

class SystemStatus(SQLModel, table=True):
    """System status model for tracking overall Anvyl system state."""

    id: str = Field(primary_key=True, default="system")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Component counts
    total_hosts: int = Field(default=0)
    online_hosts: int = Field(default=0)
    total_containers: int = Field(default=0)
    running_containers: int = Field(default=0)

    # Service status
    infra_api_status: str = Field(default="stopped")  # running, stopped, unhealthy
    agent_status: str = Field(default="stopped")  # running, stopped, unhealthy

    # System metadata
    last_sync: Optional[datetime] = Field(default=None)
    system_info: str = Field(default="{}")  # JSON string for system information

    def get_system_info(self) -> Dict[str, Any]:
        """Get system info as dictionary."""
        if not self.system_info:
            return {}
        try:
            return json.loads(self.system_info)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in system info")
            return {}

    def set_system_info(self, info: Dict[str, Any]) -> None:
        """Set system info from dictionary."""
        self.system_info = json.dumps(info)
        self.updated_at = datetime.now(UTC)

class DatabaseManager:
    """Database manager for Anvyl."""

    def __init__(self, database_url: str = None):
        """Initialize database manager."""
        if database_url is None:
            anvyl_home = Path.home() / ".anvyl"
            anvyl_home.mkdir(parents=True, exist_ok=True)
            db_path = anvyl_home / "anvyl.db"
            database_url = f"sqlite:///{db_path}"
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

    def get_host_by_ip(self, ip: str) -> Optional[Host]:
        """Get a host by IP address."""
        with self.get_session() as session:
            return session.exec(select(Host).where(Host.ip == ip)).first()

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

    def cleanup_duplicate_hosts(self) -> int:
        """Clean up duplicate hosts by IP address, keeping the most recent one."""
        with self.get_session() as session:
            # Get all hosts grouped by IP
            hosts = session.exec(select(Host)).all()
            ip_groups = {}

            for host in hosts:
                if host.ip not in ip_groups:
                    ip_groups[host.ip] = []
                ip_groups[host.ip].append(host)

            # For each IP with multiple hosts, keep the most recent one
            deleted_count = 0
            for ip, host_list in ip_groups.items():
                if len(host_list) > 1:
                    # Sort by last_seen (most recent first), then by created_at
                    host_list.sort(key=lambda h: (h.last_seen or h.created_at), reverse=True)

                    # Keep the first (most recent) one, delete the rest
                    for host in host_list[1:]:
                        session.delete(host)
                        deleted_count += 1

            session.commit()
            return deleted_count

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

    # System status management methods
    def get_system_status(self) -> SystemStatus:
        """Get or create system status record."""
        with self.get_session() as session:
            status = session.get(SystemStatus, "system")
            if not status:
                status = SystemStatus()
                session.add(status)
                session.commit()
                session.refresh(status)
            return status

    def update_system_status(self, **kwargs) -> SystemStatus:
        """Update system status with provided fields."""
        with self.get_session() as session:
            status = session.get(SystemStatus, "system")
            if not status:
                status = SystemStatus()
                session.add(status)

            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(status, key):
                    setattr(status, key, value)

            status.updated_at = datetime.now(UTC)
            session.add(status)
            session.commit()
            session.refresh(status)
            return status

    def refresh_system_status(self) -> SystemStatus:
        """Refresh system status by counting actual components."""
        with self.get_session() as session:
            # Count hosts
            total_hosts = session.exec(select(Host)).all()
            online_hosts = [h for h in total_hosts if h.status == "online"]

            # Count containers
            total_containers = session.exec(select(Container)).all()
            running_containers = [c for c in total_containers if c.status == "running"]

            # Update system status
            status = session.get(SystemStatus, "system")
            if not status:
                status = SystemStatus()
                session.add(status)

            status.total_hosts = len(total_hosts)
            status.online_hosts = len(online_hosts)
            status.total_containers = len(total_containers)
            status.running_containers = len(running_containers)
            status.last_sync = datetime.now(UTC)
            status.updated_at = datetime.now(UTC)

            session.add(status)
            session.commit()
            session.refresh(status)
            return status