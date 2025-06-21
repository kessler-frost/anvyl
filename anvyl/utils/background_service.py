"""
Background Service Manager

This module provides functionality to manage background services for Anvyl,
including starting and stopping various services in the background.
"""

import os
import sys
import json
import signal
import subprocess
import time
import logging
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundServiceManager:
    """Manages background services for Anvyl."""

    def __init__(self, service_dir: Optional[str] = None):
        """Initialize the background service manager."""
        if service_dir is None:
            # Use ~/.anvyl/services as default
            self.service_dir = Path.home() / ".anvyl" / "services"
        else:
            self.service_dir = Path(service_dir)

        # Ensure service directory exists
        self.service_dir.mkdir(parents=True, exist_ok=True)

        # Service status file
        self.status_file = self.service_dir / "services.json"

    def _get_pid_file(self, service_name: str) -> Path:
        """Get the PID file path for a service."""
        return self.service_dir / f"{service_name}.pid"

    def _get_log_file(self, service_name: str) -> Path:
        """Get the log file path for a service."""
        return self.service_dir / f"{service_name}.log"

    def _save_status(self, service_name: str, status: Dict[str, Any]):
        """Save service status to file."""
        try:
            # Load existing status
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    all_status = json.load(f)
            else:
                all_status = {}

            # Update status for this service
            all_status[service_name] = {
                **status,
                "updated_at": datetime.now().isoformat()
            }

            # Save back to file
            with open(self.status_file, 'w') as f:
                json.dump(all_status, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving service status: {e}")

    def _load_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Load service status from file."""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    all_status = json.load(f)
                return all_status.get(service_name)
        except Exception as e:
            logger.error(f"Error loading service status: {e}")
        return None

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    def start_service(self, service_name: str, command: List[str],
                     host: Optional[str] = None, port: Optional[int] = None,
                     **kwargs) -> bool:
        """Start a service in the background.

        Args:
            service_name: Name of the service
            command: List of command arguments to execute
            host: Host address (optional, for services that need it)
            port: Port number (optional, for services that need it)
            **kwargs: Additional arguments to pass to the command
        """
        pid_file = self._get_pid_file(service_name)
        log_file = self._get_log_file(service_name)

        # Check if already running
        if self.is_service_running(service_name):
            logger.info(f"Service {service_name} is already running")
            return True

        try:
            # Prepare the command with additional arguments
            cmd = command.copy()

            # Add host and port if provided
            if host is not None:
                cmd.extend(["--host", host])
            if port is not None:
                cmd.extend(["--port", str(port)])

            # Add any additional kwargs as command line arguments
            for key, value in kwargs.items():
                if value is not None:
                    cmd.extend([f"--{key}", str(value)])

            # Start the process in background
            with open(log_file, 'w') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
                    start_new_session=True
                )

            # Save PID
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            # Wait a moment to see if it starts successfully
            time.sleep(1)

            if process.poll() is None:  # Process is still running
                # Save status
                status = {
                    "pid": process.pid,
                    "command": cmd,
                    "started_at": datetime.now().isoformat(),
                    "status": "running",
                    "log_file": str(log_file)
                }

                # Add host and port to status if provided
                if host is not None:
                    status["host"] = host
                if port is not None:
                    status["port"] = port

                self._save_status(service_name, status)

                logger.info(f"Started {service_name} with PID {process.pid}")
                return True
            else:
                # Process failed to start
                logger.error(f"Failed to start {service_name}")
                return False

        except Exception as e:
            logger.error(f"Error starting {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a service.

        Args:
            service_name: Name of the service to stop
        """
        pid_file = self._get_pid_file(service_name)

        if not pid_file.exists():
            logger.info(f"Service {service_name} is not running (no PID file)")
            return True

        try:
            # Read PID
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is running
            if not self._is_process_running(pid):
                logger.info(f"Service {service_name} is not running (PID {pid} not found)")
                self._cleanup_service(service_name)
                return True

            # Try graceful shutdown first
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)

                # Check if process stopped
                if not self._is_process_running(pid):
                    logger.info(f"Stopped {service_name} gracefully")
                    self._cleanup_service(service_name)
                    return True

                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)

                if not self._is_process_running(pid):
                    logger.info(f"Force stopped {service_name}")
                    self._cleanup_service(service_name)
                    return True
                else:
                    logger.error(f"Failed to stop {service_name}")
                    return False

            except ProcessLookupError:
                logger.info(f"Service {service_name} already stopped")
                self._cleanup_service(service_name)
                return True

        except Exception as e:
            logger.error(f"Error stopping {service_name}: {e}")
            return False

    def _cleanup_service(self, service_name: str):
        """Clean up service files."""
        try:
            pid_file = self._get_pid_file(service_name)
            if pid_file.exists():
                pid_file.unlink()

            # Update status
            status = self._load_status(service_name)
            if status:
                status["status"] = "stopped"
                status["stopped_at"] = datetime.now().isoformat()
                self._save_status(service_name, status)

        except Exception as e:
            logger.error(f"Error cleaning up service {service_name}: {e}")

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running."""
        pid_file = self._get_pid_file(service_name)

        if not pid_file.exists():
            return False

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            return self._is_process_running(pid)

        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a service."""
        status = self._load_status(service_name)
        if not status:
            return None

        # Check if process is actually running
        is_running = self.is_service_running(service_name)
        status["running"] = is_running

        if not is_running and status.get("status") == "running":
            status["status"] = "stopped"
            self._save_status(service_name, status)

        return status

    def get_service_logs(self, service_name: str, lines: int = 100) -> Optional[str]:
        """Get recent logs from a service."""
        log_file = self._get_log_file(service_name)

        if not log_file.exists():
            return None

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            logger.error(f"Error reading service logs: {e}")
            return None

    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all managed services."""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    all_status = json.load(f)

                # Update running status for each service
                for service_name, status in all_status.items():
                    status["running"] = self.is_service_running(service_name)
                    if not status["running"] and status.get("status") == "running":
                        status["status"] = "stopped"
                        self._save_status(service_name, status)

                return all_status
            else:
                return {}

        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return {}

    # Convenience methods for specific services
    def start_infrastructure_api(self, host: str = "0.0.0.0", port: int = 4200) -> bool:
        """Start the infrastructure API service in the background."""
        return self.start_service(
            service_name="infrastructure_api",
            command=[sys.executable, "-m", "anvyl.infra.infrastructure_api"],
            host=host,
            port=port
        )

    def stop_infrastructure_api(self) -> bool:
        """Stop the infrastructure API service."""
        return self.stop_service("infrastructure_api")


# Global service manager instance
_service_manager = None

def get_service_manager() -> BackgroundServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = BackgroundServiceManager()
    return _service_manager