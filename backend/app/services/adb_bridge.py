"""
Samsung J2 ADB Bridge Service
Automates ADB reverse port forwarding, screen wake-lock,
and native Friday HUD kiosk launching on the connected Samsung Galaxy J2 Core.
"""

import logging
import subprocess
from typing import Dict, Any, List
from ..config import settings

logger = logging.getLogger("friday.adb_bridge")

class ADBBridgeService:
    def __init__(self):
        self.device_id = settings.J2_DEVICE_ID

    def get_connected_devices(self) -> List[str]:
        """List serial IDs of connected and authorized ADB devices."""
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            lines = res.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception as e:
            logger.error(f"Failed to check ADB devices: {e}")
            return []

    def setup_j2_hud(self) -> Dict[str, Any]:
        """
        Reverse-forward ports and launch native Friday HUD on the Samsung J2.
        """
        devices = self.get_connected_devices()
        if not devices:
            return {
                "status": "not_connected",
                "message": "No ADB device detected. Ensure USB debugging is ON and cable is plugged in."
            }

        target_dev = self.device_id if self.device_id in devices else devices[0]
        logger.info(f"Configuring ADB bridge for device {target_dev}...")

        try:
            # 1. Reverse forward HUD port (5173) and Backend port (8000)
            subprocess.run(["adb", "-s", target_dev, "reverse", f"tcp:{settings.HUD_PORT}", f"tcp:{settings.HUD_PORT}"], check=True)
            subprocess.run(["adb", "-s", target_dev, "reverse", f"tcp:{settings.PORT}", f"tcp:{settings.PORT}"], check=True)

            # 2. Keep screen on while charging via USB
            subprocess.run(["adb", "-s", target_dev, "shell", "svc", "power", "stayon", "true"], check=True)

            # 3. Wake up and unlock screen
            subprocess.run(["adb", "-s", target_dev, "shell", "input", "keyevent", "224"], check=True)
            subprocess.run(["adb", "-s", target_dev, "shell", "input", "keyevent", "82"], check=True)

            # 4. Launch Native Friday HUD Android Application (Zero Browser!)
            subprocess.run([
                "adb", "-s", target_dev, "shell", "am", "start",
                "-n", "com.friday.hud/.MainActivity"
            ], check=True)

            return {
                "status": "success",
                "device": target_dev,
                "message": f"Native Friday HUD successfully launched on device {target_dev}"
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB command failed: {e}")
            return {"status": "error", "message": f"ADB error: {e}"}
