"""
Service manager for Anvyl infrastructure services.
"""

import os
import sys
import time
import logging
import subprocess
import json
import signal
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import psutil

from anvyl.database.models import DatabaseManager
from anvyl.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

class SimpleServiceManager:
    """Simple service manager for Anvyl services."""

    def __init__(self, service_dir: Optional[str] = None):
        """Initialize service manager."""
        if service_dir is None:
            anvyl_home = Path.home() / ".anvyl"
            anvyl_home.mkdir(parents=True, exist_ok=True)
            self.service_dir = anvyl_home / "services"
        else:
            self.service_dir = Path(service_dir)

        # Initialize database manager
        self.db = DatabaseManager()

        # Ensure service directory exists
        self.service_dir.mkdir(parents=True, exist_ok=True)

        # Heartbeat management
        self._heartbeat_thread = None
        self._heartbeat_running = False
        self._heartbeat_interval = settings.health_check_interval

        # Sync existing services to database
        self._sync_existing_services()

        # Start heartbeat monitoring
        self._start_heartbeat_monitoring()

    def _start_heartbeat_monitoring(self):
        """Start background heartbeat monitoring for running services."""
        if self._heartbeat_thread is None or not self._heartbeat_thread.is_alive():
            self._heartbeat_running = True
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_monitor_loop,
                daemon=True,
                name="ServiceHeartbeatMonitor"
            )
            self._heartbeat_thread.start()
            logger.debug("Started service heartbeat monitoring")

    def _stop_heartbeat_monitoring(self):
        """Stop background heartbeat monitoring."""
        self._heartbeat_running = False
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2)
            logger.debug("Stopped service heartbeat monitoring")

    def _heartbeat_monitor_loop(self):
        """Background loop that updates heartbeats for running services."""
        while self._heartbeat_running:
            try:
                # Get all running services from database
                running_services = self.db.get_running_services()

                for service in running_services:
                    # Check if process is actually running
                    is_running = False
                    if service.pid:
                        try:
                            os.kill(service.pid, 0)
                            is_running = True
                        except OSError:
                            # Process not running
                            pass

                    if is_running:
                        # Update heartbeat for running service
                        self.db.update_service_heartbeat(service.id)
                        logger.debug(f"Updated heartbeat for service: {service.id}")
                    else:
                        # Process is not running, mark as stopped
                        logger.debug(f"Service {service.id} process not running, marking as stopped")
                        self.db.mark_service_stopped(service.id)

                # Sleep for the configured interval
                time.sleep(self._heartbeat_interval)

            except Exception as e:
                logger.error(f"Error in heartbeat monitor loop: {e}")
                time.sleep(self._heartbeat_interval)

    def __del__(self):
        """Cleanup when service manager is destroyed."""
        self._stop_heartbeat_monitoring()

    def _cleanup_stale_services(self):
        """Clean up stale services from database and filesystem."""
        try:
            logger.debug("Cleaning up stale services...")

            # Get all services from database
            all_services = self.db.list_service_statuses()

            for service in all_services:
                if service.status == "running":
                    # Check if process is actually running
                    is_running = False

                    if service.pid:
                        try:
                            os.kill(service.pid, 0)
                            is_running = True
                        except OSError:
                            # Process not running
                            pass

                    # Check PID file
                    pid_file = self.service_dir / f"{service.id}.pid"
                    if pid_file.exists():
                        try:
                            with open(pid_file, 'r') as f:
                                file_pid = int(f.read().strip())
                            os.kill(file_pid, 0)
                            is_running = True
                        except (OSError, ValueError):
                            # Invalid PID file
                            pid_file.unlink(missing_ok=True)

                    # If service is marked as running but not actually running, mark as stopped
                    if not is_running:
                        logger.debug(f"Marking stale service {service.id} as stopped")
                        self.db.mark_service_stopped(service.id)

            # Clean up orphaned PID files
            for pid_file in self.service_dir.glob("*.pid"):
                service_name = pid_file.stem
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    os.kill(pid, 0)  # Check if process exists
                except (OSError, ValueError):
                    # Process doesn't exist or invalid PID, remove file
                    logger.debug(f"Removing orphaned PID file: {pid_file}")
                    pid_file.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error cleaning up stale services: {e}")

    def _sync_existing_services(self):
        """Sync existing services from PID files to database."""
        try:
            # First cleanup any stale services
            self._cleanup_stale_services()

            # Check for existing PID files and sync them to database
            service_mappings = {
                "anvyl-infrastructure-api": "infra-api",
                "anvyl-agent": "agent",
                "anvyl-mcp-server": "mcp-server"
            }

            for service_name, service_type in service_mappings.items():
                pid_file = self.service_dir / f"{service_name}.pid"
                if pid_file.exists():
                    # Check if service is actually running
                    if self.is_service_running(service_name):
                        # Get PID from file
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())

                        # Check if service exists in database
                        db_status = self.db.get_service_status(service_name)
                        if not db_status:
                            # Create new service status in database
                            logger.debug(f"Syncing existing service {service_name} to database")
                            self.db.mark_service_running(
                                service_id=service_name,
                                service_type=service_type,
                                pid=pid,
                                port=self._get_default_port(service_name),
                                host="127.0.0.1"
                            )
                    else:
                        # Service not running, mark as stopped in database
                        self.db.mark_service_stopped(service_name)

        except Exception as e:
            logger.error(f"Error syncing existing services: {e}")

    def _get_default_port(self, service_name: str) -> int:
        """Get the default port for a service."""
        if service_name == "anvyl-infrastructure-api":
            return settings.infra_port
        elif service_name == "anvyl-agent":
            return settings.agent_port
        elif service_name == "anvyl-mcp-server":
            return settings.mcp_port
        else:
            return 8080  # Default fallback

    def _get_default_host(self, service_name: str) -> str:
        """Get the default host for a service."""
        return settings.infra_host

    def _build_command(self, command: List[str], host: Optional[str] = None,
                      port: Optional[int] = None, host_id: Optional[str] = None, host_ip: Optional[str] = None, **kwargs) -> str:
        """Build the command string."""
        cmd_parts = [str(part) for part in command.copy()]

        # Add host and port if provided (for infra/mcp)
        if host is not None:
            cmd_parts.extend(["--host", str(host)])
        if port is not None:
            cmd_parts.extend(["--port", str(port)])

        # Add agent-specific host_id and host_ip
        if host_id is not None:
            cmd_parts.extend(["--host-id", str(host_id)])
        if host_ip is not None:
            cmd_parts.extend(["--host-ip", str(host_ip)])

        # Add any additional kwargs as command line arguments
        for key, value in kwargs.items():
            if value is not None:
                # Convert underscores to hyphens for argument names
                arg_name = key.replace('_', '-')
                cmd_parts.extend([f"--{arg_name}", str(value)])

        return " ".join(cmd_parts)

    def _force_cleanup_service(self, service_name: str) -> bool:
        """Force cleanup any existing instances of a service.

        This method ensures that any previous instances are properly terminated
        and cleaned up before starting a new one.

        Args:
            service_name: Name of the service to cleanup

        Returns:
            True if cleanup was successful or no cleanup needed
        """
        try:
            logger.debug(f"Force cleaning up service: {service_name}")

            # Check database for running instances
            db_status = self.db.get_service_status(service_name)
            if db_status and db_status.status == "running":
                logger.debug(f"Found running instance in database for {service_name} (PID: {db_status.pid})")

                # Try to kill the process if PID exists
                if db_status.pid:
                    try:
                        # Send SIGTERM first
                        os.kill(db_status.pid, 15)
                        logger.debug(f"Sent SIGTERM to PID {db_status.pid}")

                        # Wait for graceful shutdown
                        time.sleep(1)

                        # Check if process is still running
                        try:
                            os.kill(db_status.pid, 0)
                            # Process still running, force kill with SIGKILL
                            os.kill(db_status.pid, 9)
                            logger.debug(f"Force killed PID {db_status.pid} with SIGKILL")
                            time.sleep(0.5)
                        except OSError:
                            # Process already stopped
                            logger.debug(f"Process {db_status.pid} already stopped")

                    except OSError as e:
                        logger.debug(f"Process {db_status.pid} not found or already stopped: {e}")

                # Mark as stopped in database
                self.db.mark_service_stopped(service_name)

            # Check for PID file and clean it up
            pid_file = self.service_dir / f"{service_name}.pid"
            if pid_file.exists():
                logger.debug(f"Removing stale PID file: {pid_file}")
                pid_file.unlink(missing_ok=True)

            # Check for any processes with the same name (additional safety)
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if service_name in cmdline or any(service_name in arg for arg in proc.info['cmdline'] or []):
                            logger.debug(f"Found stale process {proc.info['pid']} for {service_name}, terminating")
                            proc.terminate()
                            proc.wait(timeout=2)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        pass
            except ImportError:
                logger.debug("psutil not available, skipping process name check")

            # Wait a moment for cleanup to complete
            time.sleep(0.5)

            logger.debug(f"Cleanup completed for {service_name}")
            return True

        except Exception as e:
            logger.error(f"Error during force cleanup of {service_name}: {e}")
            return False

    def start_service(self, service_name: str, command: List[str],
                     host: Optional[str] = None, port: Optional[int] = None,
                     **kwargs) -> bool:
        """Start a service using subprocess.

        Args:
            service_name: Name of the service
            command: List of command arguments to execute
            host: Host address (optional, for services that need it)
            port: Port number (optional, for services that need it)
            **kwargs: Additional arguments to pass to the command
        """
        try:
            # Force cleanup any existing instances first
            self._force_cleanup_service(service_name)

            # Check if service is already running in database (after cleanup)
            service_status = self.db.get_service_status(service_name)
            if service_status and service_status.status == "running":
                logger.debug(f"Service {service_name} is still marked as running after cleanup, updating status")
                self.db.mark_service_stopped(service_name)

            # Check if already running (legacy check)
            if self.is_service_running(service_name):
                logger.debug(f"Service {service_name} is still running after cleanup, forcing stop")
                self.stop_service(service_name)
                time.sleep(1)  # Wait for stop to complete

            # Build the command string
            cmd_str = self._build_command(command, host, port, **kwargs)
            logger.debug(f"Starting {service_name} with command: {cmd_str}")

            # Create log file paths
            stdout_log = self.service_dir / f"{service_name}.log"
            stderr_log = self.service_dir / f"{service_name}.error.log"
            pid_file = self.service_dir / f"{service_name}.pid"

            # Open log files
            with open(stdout_log, 'w') as stdout_f, open(stderr_log, 'w') as stderr_f:
                # Run the command in background
                process = subprocess.Popen(
                    cmd_str.split(),
                    stdout=stdout_f,
                    stderr=stderr_f,
                    start_new_session=True
                )

            # Write PID to file
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            # Wait a moment for the service to start
            logger.debug(f"Waiting for {service_name} to start...")
            time.sleep(1)

            # Check if the service is running
            if self.is_service_running(service_name):
                # Update database with service status
                service_type = self._get_service_type(service_name)
                config = {
                    "command": cmd_str,
                    "host": host,
                    "port": port,
                    **kwargs
                }
                self.db.mark_service_running(
                    service_id=service_name,
                    service_type=service_type,
                    pid=process.pid,
                    port=port,
                    host=host or "127.0.0.1",
                    config=config
                )

                logger.debug(f"Started {service_name} successfully with PID {process.pid}")
                return True
            else:
                logger.error(f"Failed to start {service_name}")
                # Clean up PID file if it exists
                pid_file.unlink(missing_ok=True)
                # Mark service as error in database
                self.db.mark_service_error(service_name, "Failed to start service")
                return False

        except Exception as e:
            logger.error(f"Error starting {service_name}: {e}")
            # Mark service as error in database
            self.db.mark_service_error(service_name, str(e))
            return False

    def _get_service_type(self, service_name: str) -> str:
        """Get service type from service name."""
        if "infrastructure" in service_name:
            return "infra-api"
        elif "agent" in service_name:
            return "agent"
        elif "mcp" in service_name:
            return "mcp-server"
        else:
            return "unknown"

    def stop_service(self, service_name: str) -> bool:
        """Stop a service.

        Args:
            service_name: Name of the service to stop
        """
        try:
            logger.debug(f"Stopping service: {service_name}")

            # First check database for service status
            db_status = self.db.get_service_status(service_name)
            if db_status and db_status.status == "running":
                logger.debug(f"Found running service in database: {service_name} (PID: {db_status.pid})")

                # Try to kill the process if PID exists
                if db_status.pid:
                    try:
                        # Send SIGTERM first
                        os.kill(db_status.pid, 15)
                        logger.debug(f"Sent SIGTERM to PID {db_status.pid}")

                        # Wait for graceful shutdown
                        time.sleep(1)

                        # Check if process is still running
                        try:
                            os.kill(db_status.pid, 0)
                            # Process still running, force kill with SIGKILL
                            os.kill(db_status.pid, 9)
                            logger.debug(f"Force killed PID {db_status.pid} with SIGKILL")
                            time.sleep(0.5)
                        except OSError:
                            # Process already stopped
                            logger.debug(f"Process {db_status.pid} already stopped")

                    except OSError as e:
                        logger.debug(f"Process {db_status.pid} not found or already stopped: {e}")

                # Mark as stopped in database
                self.db.mark_service_stopped(service_name)

            # Also check PID file as backup
            pid_file = self.service_dir / f"{service_name}.pid"
            if pid_file.exists():
                logger.debug(f"Found PID file for {service_name}")
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    if not pid.isdigit():
                        logger.debug(f"Invalid PID in {pid_file}")
                        pid_file.unlink(missing_ok=True)
                        return True

                    try:
                        # Kill the process if not already handled
                        os.kill(int(pid), 15)  # SIGTERM
                        logger.debug(f"Stopped {service_name} via PID file PID {pid}")

                        # Wait a moment for graceful shutdown
                        time.sleep(1)

                        # Check if process is still running
                        try:
                            os.kill(int(pid), 0)
                            # Process still running, force kill
                            os.kill(int(pid), 9)  # SIGKILL
                            logger.debug(f"Force killed {service_name} via PID file")
                        except OSError:
                            # Process already stopped
                            pass

                    except OSError as e:
                        logger.debug(f"Service {service_name} was not running via PID file: {e}")

                # Remove PID file
                pid_file.unlink(missing_ok=True)

            # Additional cleanup: check for any processes with the same name
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if service_name in cmdline or any(service_name in arg for arg in proc.info['cmdline'] or []):
                            logger.debug(f"Found remaining process {proc.info['pid']} for {service_name}, terminating")
                            proc.terminate()
                            proc.wait(timeout=2)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        pass
            except ImportError:
                logger.debug("psutil not available, skipping process name check")

            logger.debug(f"Successfully stopped {service_name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping {service_name}: {e}")
            # Mark service as error in database
            self.db.mark_service_error(service_name, str(e))
            return False

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running.

        Args:
            service_name: Name of the service to check

        Returns:
            True if the service is running, False otherwise
        """
        try:
            pid_file = self.service_dir / f"{service_name}.pid"
            if not pid_file.exists():
                return False

            with open(pid_file, 'r') as f:
                pid = f.read().strip()
                if not pid.isdigit():
                    # Invalid PID file, remove it
                    pid_file.unlink(missing_ok=True)
                    return False

                # Check if process is still running
                try:
                    os.kill(int(pid), 0)  # Send signal 0 to check if process exists
                    return True
                except OSError:
                    # Process doesn't exist, remove PID file
                    pid_file.unlink(missing_ok=True)
                    return False

        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False

    def update_service_heartbeat(self, service_name: str) -> bool:
        """Manually update heartbeat for a specific service."""
        try:
            # Check if service is actually running
            if not self.is_service_running(service_name):
                logger.debug(f"Service {service_name} is not running, cannot update heartbeat")
                return False

            # Update heartbeat in database
            success = self.db.update_service_heartbeat(service_name)
            if success:
                logger.debug(f"Updated heartbeat for service: {service_name}")
            return success
        except Exception as e:
            logger.error(f"Error updating heartbeat for service {service_name}: {e}")
            return False

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get the status of a service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary with service status information or None if not found
        """
        try:
            # First check database
            db_status = self.db.get_service_status(service_name)
            if db_status:
                # Verify if process is actually running
                is_running = self.is_service_running(service_name)

                # If database says running but process is not, update database
                if db_status.status == "running" and not is_running:
                    self.db.mark_service_stopped(service_name)
                    db_status.status = "stopped"
                elif db_status.status == "running" and is_running:
                    # Service is running, ensure heartbeat is recent
                    self.update_service_heartbeat(service_name)
                    # Refresh the status to get updated heartbeat
                    db_status = self.db.get_service_status(service_name)

                return {
                    "name": db_status.id,
                    "type": db_status.service_type,
                    "status": db_status.status,
                    "active": is_running,
                    "pid": db_status.pid,
                    "port": db_status.port,
                    "host": db_status.host,
                    "start_time": db_status.started_at.isoformat() if db_status.started_at else None,
                    "last_heartbeat": db_status.last_heartbeat.isoformat() if db_status.last_heartbeat else None,
                    "error_count": db_status.error_count,
                    "last_error": db_status.last_error,
                    "config": db_status.get_config()
                }

            # Fallback to legacy check
            if not self.is_service_running(service_name):
                return None

            pid_file = self.service_dir / f"{service_name}.pid"
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Get process info
            try:
                process = psutil.Process(pid)
                start_time = datetime.fromtimestamp(process.create_time())
                runtime = datetime.now() - start_time
            except (ImportError, psutil.NoSuchProcess):
                start_time = None
                runtime = None

            return {
                "name": service_name,
                "type": self._get_service_type(service_name),
                "pid": pid,
                "status": "running",
                "active": True,
                "start_time": start_time.isoformat() if start_time else None,
                "runtime": str(runtime) if runtime else None,
                "command": "legacy service"
            }

        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return None

    def get_service_logs(self, service_name: str, lines: int = 100) -> Optional[str]:
        """Get the logs for a service.

        Args:
            service_name: Name of the service
            lines: Number of lines to return (default: 100)

        Returns:
            Service logs as string or None if not available
        """
        try:
            stdout_log = self.service_dir / f"{service_name}.log"
            stderr_log = self.service_dir / f"{service_name}.error.log"

            logs = []

            # Check stdout log
            if stdout_log.exists():
                with open(stdout_log, 'r') as f:
                    stdout_lines = f.readlines()
                    if stdout_lines:
                        logs.extend(stdout_lines)

            # Check stderr log
            if stderr_log.exists():
                with open(stderr_log, 'r') as f:
                    stderr_lines = f.readlines()
                    if stderr_lines:
                        logs.extend(stderr_lines)

            if logs:
                return ''.join(logs[-lines:]) if lines > 0 else ''.join(logs)

            return None

        except Exception as e:
            logger.error(f"Error getting service logs: {e}")
            return None

    def follow_service_logs(self, service_name: str, lines: int = 100):
        """Follow the logs for a service in real-time.

        Args:
            service_name: Name of the service
            lines: Number of initial lines to show (default: 100)
        """
        try:
            log_file = self.service_dir / f"{service_name}.log"
            if not log_file.exists():
                logger.error(f"Log file not found for {service_name}")
                return

            # Show initial lines
            if lines > 0:
                logs = self.get_service_logs(service_name, lines)
                if logs:
                    print(logs, end='')

            # Follow the log file
            with open(log_file, 'r') as f:
                # Seek to end of file
                f.seek(0, 2)

                try:
                    while True:
                        line = f.readline()
                        if line:
                            print(line, end='')
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    print("\nStopped following logs")

        except Exception as e:
            logger.error(f"Error following service logs: {e}")

    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all services and their status.

        Returns:
            Dictionary mapping service names to their status information
        """
        try:
            services = {}

            # Look for PID files
            for pid_file in self.service_dir.glob("*.pid"):
                service_name = pid_file.stem
                status = self.get_service_status(service_name)
                if status:
                    services[service_name] = status

            return services

        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return {}

    def restart_service(self, service_name: str) -> bool:
        """Restart a service.

        Args:
            service_name: Name of the service to restart

        Returns:
            True if restart was successful, False otherwise
        """
        try:
            logger.debug(f"Restarting service: {service_name}")

            # Get current service configuration from database
            db_status = self.db.get_service_status(service_name)
            config = db_status.get_config() if db_status else {}

            # Stop the service
            if not self.stop_service(service_name):
                logger.error(f"Failed to stop {service_name}")
                return False

            # Wait a moment for cleanup
            time.sleep(1)

            # Restart based on service type
            if service_name == "anvyl-infrastructure-api":
                host = config.get("host", settings.infra_host)
                port = config.get("port", settings.infra_port)
                return self.start_infrastructure_api(host, port)

            elif service_name == "anvyl-agent":
                host_id = config.get("host_id", "local")
                host_ip = config.get("host_ip", settings.agent_host)
                port = config.get("port", settings.agent_port)
                model_provider_url = config.get("model_provider_url", settings.model_provider_url)
                mcp_server_url = config.get("mcp_server_url", settings.mcp_server_url)
                return self.start_agent_service(host_id, host_ip, port, model_provider_url, mcp_server_url)

            elif service_name == "anvyl-mcp-server":
                port = config.get("port", settings.mcp_port)
                return self.start_mcp_server(port)

            else:
                logger.error(f"Unknown service type for restart: {service_name}")
                return False

        except Exception as e:
            logger.error(f"Error restarting {service_name}: {e}")
            return False

    # Service-specific methods
    def start_infrastructure_api(self, host: str = None, port: int = None) -> bool:
        """Start the infrastructure API service."""
        host = host or settings.infra_host
        port = port or settings.infra_port
        return self.start_service(
            "anvyl-infrastructure-api",
            command=[
                sys.executable, "-m", "anvyl.infra.api"
            ],
            host=host,
            port=port
        )

    def stop_infrastructure_api(self) -> bool:
        """Stop the infrastructure API service."""
        return self.stop_service("anvyl-infrastructure-api")

    def start_agent_service(self, host_id: str = "local", host_ip: str = None, port: int = None,
                            model_provider_url: str = None,
                            mcp_server_url: str = None) -> bool:
        """Start the agent service using subprocess."""
        try:
            port = port or settings.agent_port
            model_provider_url = model_provider_url or settings.model_provider_url
            mcp_server_url = mcp_server_url or settings.mcp_server_url
            host_ip = host_ip or settings.agent_host

            return self.start_service(
                "anvyl-agent",
                command=[
                    sys.executable, "-m", "anvyl.agent.server",
                    "--port", str(port),
                    "--host-id", host_id,
                    "--host-ip", host_ip,
                    "--mcp-server-url", mcp_server_url,
                    "--model-provider-url", model_provider_url
                ],
                port=port
            )
        except Exception as e:
            logger.error(f"Error starting agent service: {e}")
            return False

    def stop_agent_service(self) -> bool:
        """Stop the agent service."""
        return self.stop_service("anvyl-agent")

    def start_mcp_server(self, port: int = None) -> bool:
        """Start the MCP server."""
        port = port or settings.mcp_port
        # Note: The server uses streamable-http transport with its own default port
        # The port parameter is kept for CLI compatibility but not passed to the server
        return self.start_service(
            "anvyl-mcp-server",
            command=[
                sys.executable, "-m", "anvyl.mcp.server",
                "--port", str(port)
            ],
            host=settings.infra_host,
            port=port
        )

    def stop_mcp_server(self) -> bool:
        """Stop the MCP server."""
        return self.stop_service("anvyl-mcp-server")

    def start_all_services(self, infra_host: str = None, infra_port: int = None,
                           agent_host: str = None, agent_port: int = None,
                           mcp_port: int = None,
                           model_provider_url: str = None) -> bool:
        """Start all Anvyl services in the correct order."""
        try:
            infra_port = infra_port or settings.infra_port
            agent_port = agent_port or settings.agent_port
            mcp_port = mcp_port or settings.mcp_port
            model_provider_url = model_provider_url or settings.model_provider_url
            infra_host = infra_host or settings.infra_host
            agent_host = agent_host or settings.agent_host

            logger.debug("Starting all Anvyl services...")

            # Start services in order: infrastructure API, MCP server, agent
            services_started = []

            # 1. Start infrastructure API
            if self.start_infrastructure_api(host=infra_host, port=infra_port):
                services_started.append("infrastructure-api")
                logger.info("Infrastructure API started")
            else:
                logger.error("Failed to start infrastructure API")
                return False

            # 2. Start MCP server
            if self.start_mcp_server(mcp_port):
                services_started.append("mcp-server")
                logger.info("MCP server started")
            else:
                logger.error("Failed to start MCP server")
                return False

            # 3. Start agent
            if self.start_agent_service(
                host_id="local",
                host_ip=agent_host,
                port=agent_port,
                model_provider_url=model_provider_url,
                mcp_server_url=f"http://localhost:{mcp_port}/mcp/"
            ):
                services_started.append("agent")
                logger.info("Agent started")
            else:
                logger.error("Failed to start agent")
                return False

            logger.info(f"All services started: {', '.join(services_started)}")
            return True

        except Exception as e:
            logger.error(f"Error starting all services: {e}")
            return False

    def stop_all_services(self) -> bool:
        """Stop all Anvyl services."""
        try:
            logger.debug("Stopping all Anvyl services...")

            # Stop services in reverse order and track results
            results = []

            # Stop agent first (reverse dependency order)
            logger.debug("Stopping agent service...")
            agent_result = self.stop_agent_service()
            results.append(("anvyl-agent", agent_result))
            if agent_result:
                logger.debug("Agent service stopped successfully")
            else:
                logger.warning("Failed to stop agent service")

            # Stop MCP server
            logger.debug("Stopping MCP server...")
            mcp_result = self.stop_mcp_server()
            results.append(("anvyl-mcp-server", mcp_result))
            if mcp_result:
                logger.debug("MCP server stopped successfully")
            else:
                logger.warning("Failed to stop MCP server")

            # Stop infrastructure API
            logger.debug("Stopping infrastructure API...")
            infra_result = self.stop_infrastructure_api()
            results.append(("anvyl-infrastructure-api", infra_result))
            if infra_result:
                logger.debug("Infrastructure API stopped successfully")
            else:
                logger.warning("Failed to stop infrastructure API")

            # Check overall success
            failed_services = [name for name, success in results if not success]
            if failed_services:
                logger.error(f"Failed to stop services: {', '.join(failed_services)}")
                return False

            logger.debug("All Anvyl services stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Error stopping all services: {e}")
            return False

    def restart_all_services(self, infra_host: str = None, infra_port: int = None,
                             agent_host: str = None, agent_port: int = None,
                             mcp_port: int = None,
                             model_provider_url: str = None) -> bool:
        """Restart all Anvyl services."""
        try:
            infra_port = infra_port or settings.infra_port
            agent_port = agent_port or settings.agent_port
            mcp_port = mcp_port or settings.mcp_port
            model_provider_url = model_provider_url or settings.model_provider_url
            infra_host = infra_host or settings.infra_host
            agent_host = agent_host or settings.agent_host

            logger.debug("Restarting all Anvyl services...")

            # Stop all services first
            self.stop_all_services()

            # Wait a moment for services to stop
            time.sleep(2)

            # Start all services
            return self.start_all_services(infra_host, infra_port,
                                           agent_host, agent_port, mcp_port, model_provider_url)
        except Exception as e:
            logger.error(f"Error restarting all services: {e}")
            return False

    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services from database."""
        try:
            # Clean up stale services first
            self._cleanup_stale_services()

            # Get all services from database
            all_services = self.db.list_service_statuses()

            services = {}
            for service in all_services:
                # Verify if process is actually running
                is_running = False
                if service.pid:
                    try:
                        os.kill(service.pid, 0)
                        is_running = True
                    except OSError:
                        pass

                # Update database if status is inconsistent
                if service.status == "running" and not is_running:
                    self.db.mark_service_stopped(service.id)
                    service.status = "stopped"
                elif service.status == "stopped" and is_running:
                    # This shouldn't happen, but update the database
                    self.db.mark_service_running(
                        service_id=service.id,
                        service_type=service.service_type,
                        pid=service.pid,
                        port=service.port,
                        host=service.host
                    )
                    service.status = "running"

                services[service.id] = {
                    "name": service.id,
                    "type": service.service_type,
                    "status": service.status,
                    "active": is_running,
                    "pid": service.pid,
                    "port": service.port,
                    "host": service.host,
                    "start_time": service.started_at.isoformat() if service.started_at else None,
                    "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                    "error_count": service.error_count,
                    "last_error": service.last_error,
                    "config": service.get_config()
                }

            return services

        except Exception as e:
            logger.error(f"Error getting all services status: {e}")
            return {}

def get_service_manager() -> SimpleServiceManager:
    """Get the service manager instance."""
    return SimpleServiceManager()