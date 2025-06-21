"""
Tests for Anvyl database models
"""

import pytest
import json
import os
import sys
import unittest
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from anvyl.database.models import Host, Container, DatabaseManager


class TestHost(unittest.TestCase):
    """Test cases for Host model."""

    def test_host_creation(self):
        """Test Host model creation."""
        host = Host(
            id="test-host-1",
            name="Test Host",
            ip="192.168.1.100",
            os="macOS",
            status="online"
        )

        # Test that host is created correctly
        self.assertEqual(host.id, "test-host-1")
        self.assertEqual(host.name, "Test Host")
        self.assertEqual(host.ip, "192.168.1.100")
        self.assertEqual(host.os, "macOS")
        self.assertEqual(host.status, "online")

    def test_host_metadata_operations(self):
        """Test Host metadata get/set operations."""
        host = Host(id="test-id", name="test-host", ip="192.168.1.100")

        # Test default metadata
        metadata = host.get_metadata()
        self.assertEqual(metadata, {})

        # Test setting metadata
        test_metadata = {"key": "value", "number": 42}
        host.set_metadata(test_metadata)

        retrieved_metadata = host.get_metadata()
        self.assertEqual(retrieved_metadata, test_metadata)

    def test_host_metadata_invalid_json(self):
        """Test Host metadata with invalid JSON."""
        host = Host(id="test-id", name="test-host", ip="192.168.1.100")
        host.host_metadata = "invalid json"

        # Should return empty dict on invalid JSON
        result = host.get_metadata()
        self.assertEqual(result, {})


class TestContainer(unittest.TestCase):
    """Test cases for Container model."""

    def test_container_creation(self):
        """Test Container model creation."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        self.assertEqual(container.id, "container-id")
        self.assertEqual(container.name, "test-container")
        self.assertEqual(container.image, "test:latest")
        self.assertEqual(container.host_id, "host-id")
        self.assertEqual(container.status, "running")

    def test_container_ports_operations(self):
        """Test Container ports get/set operations."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        # Test default ports
        ports = container.get_ports()
        self.assertEqual(ports, [])

        # Test setting ports
        test_ports = ["8080:80", "9090:90"]
        container.set_ports(test_ports)

        retrieved_ports = container.get_ports()
        self.assertEqual(retrieved_ports, test_ports)

    def test_container_volumes_operations(self):
        """Test Container volumes get/set operations."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        # Test default volumes
        volumes = container.get_volumes()
        self.assertEqual(volumes, [])

        # Test setting volumes
        test_volumes = ["/host:/container", "/data:/app/data"]
        container.set_volumes(test_volumes)

        retrieved_volumes = container.get_volumes()
        self.assertEqual(retrieved_volumes, test_volumes)

    def test_container_environment_operations(self):
        """Test Container environment get/set operations."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        # Test default environment
        env = container.get_environment()
        self.assertEqual(env, [])

        # Test setting environment
        test_env = ["ENV=production", "DEBUG=false"]
        container.set_environment(test_env)

        retrieved_env = container.get_environment()
        self.assertEqual(retrieved_env, test_env)

    def test_container_labels_operations(self):
        """Test Container labels get/set operations."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        # Test default labels
        labels = container.get_labels()
        self.assertEqual(labels, {})

        # Test setting labels
        test_labels = {"app": "test", "version": "1.0"}
        container.set_labels(test_labels)

        retrieved_labels = container.get_labels()
        self.assertEqual(retrieved_labels, test_labels)

    def test_container_invalid_json(self):
        """Test Container methods with invalid JSON."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        # Set invalid JSON
        container.ports = "invalid json"
        container.volumes = "invalid json"
        container.environment = "invalid json"
        container.labels = "invalid json"

        # Should return defaults
        self.assertEqual(container.get_ports(), [])
        self.assertEqual(container.get_volumes(), [])
        self.assertEqual(container.get_environment(), [])
        self.assertEqual(container.get_labels(), {})


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_url = f"sqlite:///{self.temp_db.name}"
        self.db_manager = DatabaseManager(self.db_url)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        self.assertIsNotNone(self.db_manager.engine)

    def test_add_host(self):
        """Test adding a host to the database."""
        host = Host(
            id="test-host-id",
            name="test-host",
            ip="192.168.1.100"
        )

        added_host = self.db_manager.add_host(host)

        self.assertEqual(added_host.id, "test-host-id")
        self.assertEqual(added_host.name, "test-host")
        self.assertEqual(added_host.ip, "192.168.1.100")

    def test_get_host(self):
        """Test getting a host from the database."""
        host = Host(
            id="test-host-id",
            name="test-host",
            ip="192.168.1.100"
        )

        self.db_manager.add_host(host)
        retrieved_host = self.db_manager.get_host("test-host-id")

        self.assertIsNotNone(retrieved_host)
        self.assertEqual(retrieved_host.id, "test-host-id")
        self.assertEqual(retrieved_host.name, "test-host")

    def test_get_nonexistent_host(self):
        """Test getting a non-existent host."""
        retrieved_host = self.db_manager.get_host("nonexistent-id")
        self.assertIsNone(retrieved_host)

    def test_list_hosts(self):
        """Test listing all hosts."""
        host1 = Host(id="host1", name="test-host1", ip="192.168.1.100")
        host2 = Host(id="host2", name="test-host2", ip="192.168.1.101")

        self.db_manager.add_host(host1)
        self.db_manager.add_host(host2)

        hosts = self.db_manager.list_hosts()

        self.assertEqual(len(hosts), 2)
        host_ids = [h.id for h in hosts]
        self.assertIn("host1", host_ids)
        self.assertIn("host2", host_ids)

    def test_update_host(self):
        """Test updating a host."""
        host = Host(
            id="test-host-id",
            name="test-host",
            ip="192.168.1.100"
        )

        self.db_manager.add_host(host)

        # Update host
        host.name = "updated-host"
        host.ip = "192.168.1.200"
        updated_host = self.db_manager.update_host(host)

        self.assertEqual(updated_host.name, "updated-host")
        self.assertEqual(updated_host.ip, "192.168.1.200")

    def test_delete_host(self):
        """Test deleting a host."""
        host = Host(
            id="test-host-id",
            name="test-host",
            ip="192.168.1.100"
        )

        self.db_manager.add_host(host)

        # Delete host
        result = self.db_manager.delete_host("test-host-id")
        self.assertTrue(result)

        # Verify host is deleted
        retrieved_host = self.db_manager.get_host("test-host-id")
        self.assertIsNone(retrieved_host)

    def test_delete_nonexistent_host(self):
        """Test deleting a non-existent host."""
        result = self.db_manager.delete_host("nonexistent-id")
        self.assertFalse(result)

    def test_add_container(self):
        """Test adding a container to the database."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        added_container = self.db_manager.add_container(container)

        self.assertEqual(added_container.id, "container-id")
        self.assertEqual(added_container.name, "test-container")
        self.assertEqual(added_container.image, "test:latest")

    def test_get_container(self):
        """Test getting a container from the database."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        self.db_manager.add_container(container)
        retrieved_container = self.db_manager.get_container("container-id")

        self.assertIsNotNone(retrieved_container)
        self.assertEqual(retrieved_container.id, "container-id")
        self.assertEqual(retrieved_container.name, "test-container")

    def test_list_containers_all(self):
        """Test listing all containers."""
        container1 = Container(
            id="container1", name="test1", image="test:1",
            host_id="host1", status="running"
        )
        container2 = Container(
            id="container2", name="test2", image="test:2",
            host_id="host2", status="stopped"
        )

        self.db_manager.add_container(container1)
        self.db_manager.add_container(container2)

        containers = self.db_manager.list_containers()

        self.assertEqual(len(containers), 2)

    def test_list_containers_by_host(self):
        """Test listing containers filtered by host."""
        container1 = Container(
            id="container1", name="test1", image="test:1",
            host_id="host1", status="running"
        )
        container2 = Container(
            id="container2", name="test2", image="test:2",
            host_id="host2", status="stopped"
        )

        self.db_manager.add_container(container1)
        self.db_manager.add_container(container2)

        containers = self.db_manager.list_containers(host_id="host1")

        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0].id, "container1")

    def test_update_container(self):
        """Test updating a container."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        self.db_manager.add_container(container)

        # Update container
        container.status = "stopped"
        container.exit_code = 0
        updated_container = self.db_manager.update_container(container)

        self.assertEqual(updated_container.status, "stopped")
        self.assertEqual(updated_container.exit_code, 0)

    def test_delete_container(self):
        """Test deleting a container."""
        container = Container(
            id="container-id",
            name="test-container",
            image="test:latest",
            host_id="host-id",
            status="running"
        )

        self.db_manager.add_container(container)

        # Delete container
        result = self.db_manager.delete_container("container-id")
        self.assertTrue(result)

        # Verify container is deleted
        retrieved_container = self.db_manager.get_container("container-id")
        self.assertIsNone(retrieved_container)

    def test_delete_nonexistent_container(self):
        """Test deleting a non-existent container."""
        result = self.db_manager.delete_container("nonexistent-id")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()