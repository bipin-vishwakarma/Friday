#!/usr/bin/env python3
"""
Auto-Monitoring and Self-Healing Agent for FRIDAY AI System

This script continuously monitors system health, performs automatic recovery,
and maintains optimal performance without human intervention.

Features:
1. Voice Pipeline Health Monitoring
2. Vision System Status Tracking
3. LLM Backend Failover
4. Audio Stream Quality Assurance
5. Automatic Self-Healing Actions
6. Comprehensive Health Reporting
"""

import os
import sys
import time
import subprocess
import logging
import requests
import json
import psutil
from datetime import datetime
from threading import Thread, Event
from queue import Queue, Empty

# ======================
# Configuration Section
# ======================

# System Configuration
CHECK_INTERVAL = 30  # seconds between health checks
SHUTDOWN_TIMEOUT = 300  # max seconds to wait for graceful shutdown
MAX_CONSECUTIVE_FAILURES = 3  # consecutive failures before triggering recovery

# Service Names (match systemd service names)
BACKEND_SERVICE = "friday-backend"
VISION_SERVICE = "friday-vision"
LLM_SERVICE = "friday-llm"

# API Endpoints
BACKEND_HEALTH_URL = "http://localhost:8000/health"
VISION_STATUS_URL = "http://localhost:8000/api/v1/vision/status"
LLM_TEST_URL = "http://localhost:8000/api/v1/llm/generate"

# Recovery Actions
ENABLE_AUTO_RECOVERY = True
RESTART_TIMEOUT = 15  # seconds to wait for service restart

# Logging Configuration
LOG_DIR = "/var/log/friday_monitor"
LOG_FILE = os.path.join(LOG_DIR, "monitor.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# ======================
# Health Check Classes
# ======================

class HealthChecker:
    """Main health checking and recovery orchestrator"""

    def __init__(self):
        self.failure_counts = {
            'backend': 0,
            'vision': 0,
            'llm': 0,
            'audio': 0
        }
        self.running = Event()
        self.shutdown_event = Event()

    def log_health_status(self, service, status, details=""):
        """Log health status with consistent format"""
        status_prefix = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'recovering': '🔄',
            'recovered': '🎉'
        }.get(status, '📊')

        message = f"{status_prefix} {service.upper()} HEALTH: {status} {details}"
        logging.info(message)

    def check_backend_health(self):
        """Check backend API health and perform recovery if needed"""
        try:
            response = requests.get(BACKEND_HEALTH_URL, timeout=5)
            if response.status_code == 200:
                self.failure_counts['backend'] = 0
                self.log_health_status('backend', 'healthy')
                return True
            else:
                self.failure_counts['backend'] += 1
                self.log_health_status('backend', 'unhealthy',
                                     f'HTTP {response.status_code}')
                return False
        except Exception as e:
            self.failure_counts['backend'] += 1
            self.log_health_status('backend', 'unhealthy', str(e))
            return False

    def check_vision_health(self):
        """Check vision system health"""
        try:
            response = requests.get(VISION_STATUS_URL, timeout=5)
            if response.status_code == 200 and response.json().get('running', False):
                self.failure_counts['vision'] = 0
                self.log_health_status('vision', 'healthy')
                return True
            else:
                self.failure_counts['vision'] += 1
                self.log_health_status('vision', 'unhealthy',
                                     f'Status: {response.status_code if hasattr(response, "status_code") else "no response"}')
                return False
        except Exception as e:
            self.failure_counts['vision'] += 1
            self.log_health_status('vision', 'unhealthy', str(e))
            return False

    def check_llm_health(self):
        """Check LLM backend health"""
        try:
            response = requests.get(LLM_TEST_URL, params={"test": "pong"}, timeout=5)
            if response.status_code == 200:
                self.failure_counts['llm'] = 0
                self.log_health_status('llm', 'healthy')
                return True
            else:
                self.failure_counts['llm'] += 1
                self.log_health_status('llm', 'unhealthy',
                                     f'HTTP {response.status_code}')
                return False
        except Exception as e:
            self.failure_counts['llm'] += 1
            self.log_health_status('llm', 'unhealthy', str(e))
            return False

    def check_audio_stream(self):
        """Check audio stream health"""
        try:
            # Access audio stream stats via global variable or API
            # This is a placeholder - actual implementation may vary
            audio_stats = self._get_audio_stats()
            if audio_stats and audio_stats.get('queue_size', 0) < 90:
                self.failure_counts['audio'] = 0
                self.log_health_status('audio', 'healthy')
                return True
            else:
                self.failure_counts['audio'] += 1
                self.log_health_status('audio', 'degraded',
                                     f'Queue size: {audio_stats.get("queue_size", 0)}')
                return False
        except Exception as e:
            self.failure_counts['audio'] += 1
            self.log_health_status('audio', 'unhealthy', str(e))
            return False

    def _get_audio_stats(self):
        """Retrieve audio stream statistics (stub implementation)"""
        # In real implementation, this would interface with AudioStreamer class
        # This is a placeholder that could be enhanced to read from shared state
        return {
            'queue_size': 5,
            'samples_processed': 1000,
            'dropped_samples': 0
        }

    def perform_recovery(self, service):
        """Perform appropriate recovery action for failed service"""
        if not ENABLE_AUTO_RECOVERY:
            return

        recovery_map = {
            'backend': self._restart_backend,
            'vision': self._restart_vision,
            'llm': self._restart_llm,
            'audio': self._reset_audio
        }

        if service in recovery_map:
            try:
                self.log_health_status(service, 'recovering')
                recovery_map[service]()
                # Verify recovery succeeded
                time.sleep(RESTART_TIMEOUT)
                if self.check_health(service):
                    self.log_health_status(service, 'recovered')
                else:
                    self.log_health_status(service, 'unhealthy', 'Recovery failed')
            except Exception as e:
                self.log_health_status(service, 'unhealthy', f'Recovery error: {e}')

    def check_health(self, service):
        """Check health of specific service after recovery"""
        if service == 'backend':
            return self.check_backend_health()
        elif service == 'vision':
            return self.check_vision_health()
        elif service == 'llm':
            return self.check_llm_health()
        elif service == 'audio':
            return self.check_audio_stream()
        return False

    def _restart_backend(self):
        """Restart backend service via systemd"""
        self._execute_service_command(BACKEND_SERVICE, "restart")

    def _restart_vision(self):
        """Restart vision service via systemd"""
        self._execute_service_command(VISION_SERVICE, "restart")

    def _restart_llm(self):
        """Restart LLM service via systemd"""
        self._execute_service_command(LLM_SERVICE, "restart")

    def _reset_audio(self):
        """Reset audio stream state"""
        # Implementation would depend on audio system specifics
        logging.warning("Audio stream reset requested")

    def _execute_service_command(self, service, action):
        """Execute systemctl command for service management"""
        try:
            logging.info(f"Executing: systemctl {action} {service}")
            result = subprocess.run(
                ["sudo", "systemctl", action, service],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logging.info(f"Service {service} {action} successful")
            else:
                logging.error(f"Service {service} {action} failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logging.error(f"Service {service} {action} timed out")
        except Exception as e:
            logging.error(f"Service command execution error: {e}")

    def graceful_shutdown(self):
        """Perform graceful shutdown operations"""
        logging.info("Initiating graceful shutdown...")
        self.running.clear()
        # Add any specific cleanup here
        for _ in range(10):  # Give some time for cleanup
            if self.shutdown_event.is_set():
                break
            time.sleep(0.1)
        logging.info("Shutdown complete")

# ======================
# System Initialization
# ======================

def setup_logging():
    """Configure logging system"""
    pass  # Already configured at module level

def get_system_resources():
    """Get current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': disk.percent,
        'memory_total_mb': memory.total / (1024**2),
        'disk_total_gb': disk.total / (1024**3)
    }

# ======================
# Main Monitoring Loop
# ======================

def main():
    """Main entry point for health monitoring system"""
    logging.info("=" * 60)
    logging.info("FRIDAY AI Auto-Monitoring Agent Started")
    logging.info(f"System resources: {get_system_resources()}")
    logging.info("=" * 60)

    # Initialize health checker
    checker = HealthChecker()

    # Track last recovery actions
    last_recovery_time = time.time()

    # Main monitoring loop
    while not checker.shutdown_event.is_set():
        try:
            current_time = time.time()

            # Perform health checks
            services = ['backend', 'vision', 'llm', 'audio']
            results = {}

            for service in services:
                results[service] = checker.check_health(service)

            # Check for consecutive failures requiring recovery
            for service in services:
                if not results[service] and checker.failure_counts[service] >= MAX_CONSECUTIVE_FAILURES:
                    if current_time - last_recovery_time > 60:  # Cooldown period
                        checker.perform_recovery(service)
                        last_recovery_time = current_time

            # Log current failure counts and health metrics
            health_summary = {
                'timestamp': datetime.now().isoformat(),
                'backend_failures': checker.failure_counts['backend'],
                'vision_failures': checker.failure_counts['vision'],
                'llm_failures': checker.failure_counts['llm'],
                'audio_failures': checker.failure_counts['audio'],
                'system_resources': get_system_resources()
            }

            logging.info(f"HEALTH SUMMARY: {json.dumps(health_summary, indent=2)}")

            # Sleep until next check
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logging.info("Health checker interrupted by user")
            checker.graceful_shutdown()
            break
        except Exception as e:
            logging.error(f"Unexpected error in health checker: {e}", exc_info=True)
            time.sleep(CHECK_INTERVAL)

    logging.info("FRIDAY AI Auto-Monitoring Agent Stopped")

if __name__ == "__main__":
    main()