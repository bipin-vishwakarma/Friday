"""
Resource Monitor Agent
Collects real-time PC hardware telemetry (CPU, RAM, Disk, Network, Battery)
and streams metrics to the Samsung J2 Desk HUD via WebSocket.
"""

import time
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger("friday.monitor")

class MonitorAgent:
    def __init__(self):
        self._last_net = psutil.net_io_counters()
        self._last_time = time.time()

    def get_telemetry(self) -> Dict[str, Any]:
        """Collect current system performance metrics."""
        now = time.time()
        time_delta = max(0.1, now - self._last_time)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count(logical=True)
        
        # Memory
        mem = psutil.virtual_memory()
        mem_used_gb = round(mem.used / (1024 ** 3), 1)
        mem_total_gb = round(mem.total / (1024 ** 3), 1)
        
        # Disk
        try:
            disk = psutil.disk_usage("C:\\")
            disk_percent = disk.percent
        except Exception:
            disk_percent = 0

        # Network speed estimation
        net = psutil.net_io_counters()
        bytes_sent = (net.bytes_sent - self._last_net.bytes_sent) / time_delta
        bytes_recv = (net.bytes_recv - self._last_net.bytes_recv) / time_delta
        self._last_net = net
        self._last_time = now

        # Battery
        battery = psutil.sensors_battery()
        battery_data = {
            "percent": battery.percent if battery else 100,
            "power_plugged": battery.power_plugged if battery else True
        }

        return {
            "type": "telemetry",
            "timestamp": int(now),
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count
            },
            "memory": {
                "percent": mem.percent,
                "used_gb": mem_used_gb,
                "total_gb": mem_total_gb
            },
            "disk": {
                "percent": disk_percent
            },
            "network": {
                "kb_sent": round(bytes_sent / 1024, 1),
                "kb_recv": round(bytes_recv / 1024, 1)
            },
            "battery": battery_data
        }
