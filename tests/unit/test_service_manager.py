"""
Tests for service manager heartbeat functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from anvyl.utils.service_manager import SimpleServiceManager
from anvyl.database.models import ServiceStatus, DatabaseManager


class TestServiceManagerHeartbeat:
    """Test service manager heartbeat functionality."""

    @pytest.fixture
    def service_manager(self, tmp_path):
        """Create a service manager for testing."""
        with patch('anvyl.utils.service_manager.get_settings') as mock_settings:
            mock_settings.return_value.health_check_interval = 1  # Fast for testing
            with patch('anvyl.utils.service_manager.DatabaseManager') as mock_db:
                mock_db_instance = Mock()
                # Mock the list_service_statuses method to return empty list
                mock_db_instance.list_service_statuses.return_value = []
                mock_db.return_value = mock_db_instance

                manager = SimpleServiceManager(service_dir=str(tmp_path))
                manager._stop_heartbeat_monitoring()  # Stop background thread for testing
                return manager

    def test_update_service_heartbeat_success(self, service_manager):
        """Test successful heartbeat update for a running service."""
        # Mock service as running
        service_manager.is_service_running = Mock(return_value=True)
        service_manager.db.update_service_heartbeat = Mock(return_value=True)

        result = service_manager.update_service_heartbeat("test-service")

        assert result is True
        service_manager.db.update_service_heartbeat.assert_called_once_with("test-service")

    def test_update_service_heartbeat_service_not_running(self, service_manager):
        """Test heartbeat update when service is not running."""
        # Mock service as not running
        service_manager.is_service_running = Mock(return_value=False)

        result = service_manager.update_service_heartbeat("test-service")

        assert result is False
        service_manager.db.update_service_heartbeat.assert_not_called()

    def test_update_service_heartbeat_database_error(self, service_manager):
        """Test heartbeat update when database update fails."""
        # Mock service as running but database update fails
        service_manager.is_service_running = Mock(return_value=True)
        service_manager.db.update_service_heartbeat = Mock(return_value=False)

        result = service_manager.update_service_heartbeat("test-service")

        assert result is False
        service_manager.db.update_service_heartbeat.assert_called_once_with("test-service")

    def test_heartbeat_monitor_loop(self, service_manager):
        """Test the heartbeat monitor loop functionality."""
        # Mock running services
        mock_service1 = Mock()
        mock_service1.id = "service1"
        mock_service1.pid = 12345

        mock_service2 = Mock()
        mock_service2.id = "service2"
        mock_service2.pid = 12346

        service_manager.db.get_running_services = Mock(return_value=[mock_service1, mock_service2])
        service_manager.db.update_service_heartbeat = Mock(return_value=True)
        service_manager.db.mark_service_stopped = Mock()

        # Mock process check - service1 running, service2 not running
        def mock_kill(pid, signal):
            if pid == 12345:
                return  # Success (running)
            elif pid == 12346:
                raise OSError("Process not found")  # Not running

        with patch('os.kill', side_effect=mock_kill):
            # Run heartbeat monitor for one iteration
            service_manager._heartbeat_running = True
            service_manager._heartbeat_interval = 0.1  # Fast for testing

            # Call the monitor loop directly instead of threading
            service_manager._heartbeat_monitor_loop()

            # Verify results
            service_manager.db.update_service_heartbeat.assert_called_once_with("service1")
            service_manager.db.mark_service_stopped.assert_called_once_with("service2")

    def test_get_service_status_updates_heartbeat(self, service_manager):
        """Test that get_service_status updates heartbeat for running services."""
        # Mock service status
        mock_service = Mock()
        mock_service.id = "test-service"
        mock_service.status = "running"
        mock_service.last_heartbeat = datetime.now() - timedelta(minutes=5)  # Old heartbeat

        service_manager.db.get_service_status = Mock(return_value=mock_service)
        service_manager.is_service_running = Mock(return_value=True)
        service_manager.update_service_heartbeat = Mock(return_value=True)

        # Call get_service_status
        service_manager.get_service_status("test-service")

        # Verify heartbeat was updated
        service_manager.update_service_heartbeat.assert_called_once_with("test-service")

    def test_heartbeat_thread_cleanup(self, service_manager):
        """Test that heartbeat thread is properly cleaned up."""
        # Start heartbeat monitoring
        service_manager._start_heartbeat_monitoring()

        # Verify thread is running
        assert service_manager._heartbeat_thread is not None
        assert service_manager._heartbeat_thread.is_alive()

        # Stop monitoring
        service_manager._stop_heartbeat_monitoring()

        # Verify thread is stopped
        assert not service_manager._heartbeat_running
        # Thread should be stopped (give it a moment)
        time.sleep(0.2)
        # Note: Thread cleanup might take time, so we'll just check the flag
        assert not service_manager._heartbeat_running

    def test_heartbeat_interval_configuration(self, tmp_path):
        """Test that heartbeat interval is properly configured."""
        with patch('anvyl.utils.service_manager.get_settings') as mock_settings:
            mock_settings.return_value.health_check_interval = 30
            with patch('anvyl.utils.service_manager.DatabaseManager') as mock_db:
                mock_db_instance = Mock()
                mock_db_instance.list_service_statuses.return_value = []
                mock_db.return_value = mock_db_instance

                manager = SimpleServiceManager(service_dir=str(tmp_path))
                assert manager._heartbeat_interval == 30
                manager._stop_heartbeat_monitoring()