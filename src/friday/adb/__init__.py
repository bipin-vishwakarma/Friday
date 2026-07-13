"""ADB (Android Debug Bridge) manager for FRIDAY.

Provides a lightweight wrapper around the `adb` command-line tool using the standard library
`subprocess` module. All operations are non‑blocking when possible and fail gracefully –
if `adb` is not installed or no device is connected the methods log a warning and return a
fallback value instead of raising an exception.

The manager is exposed as a module‑level singleton `adb_manager` and a helper
`get_adb_manager()` for convenient imports.
"""

import os
import subprocess
import shlex
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from src.friday.events import fire_event, Events
from src.friday.config import settings

logger = logging.getLogger(__name__)


def _which_adb() -> Optional[Path]:
    """Return the path to `adb.exe` if it exists.

    Search order:
    1. settings.ADB_PATH (project‑specific location)
    2. Common Android SDK install locations on Windows
    3. System PATH via `shutil.which`
    """
    # 1. Project‑specific location
    if getattr(settings, "ADB_PATH", None):
        p = Path(settings.ADB_PATH)
        if p.is_file():
            return p
    # 2. Common SDK locations
    common_paths = [
        Path(os.getenv("LOCALAPPDATA", ""))
        / "Android"
        / "Sdk"
        / "platform-tools"
        / "adb.exe",
        Path("C:/Program Files/Android/Android Studio/sdk/platform-tools/adb.exe"),
    ]
    for p in common_paths:
        if p.is_file():
            return p
    # 3. System PATH
    from shutil import which

    which_path = which("adb")
    if which_path:
        return Path(which_path)
    return None


class ADBManager:
    """Small wrapper around the `adb` CLI.

    All public methods return a tuple ``(success: bool, result)`` where *result*
    contains the command output or a sensible default. When the tool cannot be
    executed, ``success`` is ``False`` and ``result`` is ``None`` (or ``0`` for
    numeric queries).
    """

    def __init__(self):
        self.adb_path: Optional[Path] = _which_adb()
        self._connected_device: Optional[str] = None
        if not self.adb_path:
            logger.warning("adb executable not found – ADBManager will be inert")
        else:
            logger.info("ADB executable found at %s", self.adb_path)

    # ---------------------------------------------------------------------
    # Helper utilities
    # ---------------------------------------------------------------------
    def _run(self, args: List[str], capture_output: bool = True) -> Tuple[bool, Optional[str]]:
        """Run an adb command and return ``(ok, output)``.

        ``args`` should not include the executable itself – it is prepended
        automatically. Errors are caught, logged and result in ``(False, None)``.
        """
        if not self.adb_path:
            logger.warning("Attempted to run adb command but adb is missing")
            return False, None
        cmd = [str(self.adb_path)] + args
        try:
            completed = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            ok = completed.returncode == 0
            out = completed.stdout.strip() if capture_output else None
            if not ok:
                logger.warning("adb command failed: %s – %s", " ".join(cmd), completed.stderr)
            return ok, out
        except Exception as e:
            logger.exception("Exception while running adb command %s", " ".join(cmd))
            return False, None

    def _device_arg(self) -> List[str]:
        """Return a list containing ``-s <serial>`` if a device is selected.
        """
        return ["-s", self._connected_device] if self._connected_device else []

    # ---------------------------------------------------------------------
    # Connection handling
    # ---------------------------------------------------------------------
    def is_connected(self) -> bool:
        return self._connected_device is not None

    def list_devices(self) -> List[Tuple[str, str]]:
        """Return a list of ``(serial, status)`` for each device.
        """
        ok, out = self._run(["devices"])
        if not ok or not out:
            return []
        lines = out.splitlines()[1:]  # first line is header
        devices = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) == 2:
                devices.append((parts[0], parts[1]))
        return devices

    def connect(self, ip: str, port: int = 5555) -> bool:
        """Connect to a device over TCP/IP.
        """
        ok, _ = self._run(["connect", f"{ip}:{port}"])
        if ok:
            # Refresh the device list and pick the first connected one
            devs = self.list_devices()
            for serial, status in devs:
                if status == "device":
                    self._connected_device = serial
                    fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "connect", "target": f"{ip}:{port}"})
                    return True
        return False

    def disconnect(self) -> bool:
        """Disconnect the current device (if any)."""
        if not self._connected_device:
            return True
        ok, _ = self._run(["disconnect", self._connected_device])
        if ok:
            fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "disconnect", "device": self._connected_device})
        self._connected_device = None
        return ok

    # ---------------------------------------------------------------------
    # Simple UI actions
    # ---------------------------------------------------------------------
    def tap(self, x: int, y: int) -> bool:
        ok, _ = self._run(self._device_arg() + ["shell", "input", "tap", str(x), str(y)])
        fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "tap", "x": x, "y": y})
        return ok

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        ok, _ = self._run(
            self._device_arg()
            + [
                "shell",
                "input",
                "swipe",
                str(x1),
                str(y1),
                str(x2),
                str(y2),
                str(duration_ms),
            ]
        )
        fire_event(
            Events.ADB_COMMAND_EXECUTED,
            {"action": "swipe", "from": [x1, y1], "to": [x2, y2], "duration_ms": duration_ms},
        )
        return ok

    def press_key(self, keycode: int) -> bool:
        ok, _ = self._run(self._device_arg() + ["shell", "input", "keyevent", str(keycode)])
        fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "press_key", "keycode": keycode})
        return ok

    def open_app(self, package: str) -> bool:
        ok, _ = self._run(self._device_arg() + ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
        fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "open_app", "package": package})
        return ok

    def get_battery(self) -> Optional[int]:
        ok, out = self._run(self._device_arg() + ["shell", "dumpsys", "battery"])
        if not ok or not out:
            return None
        for line in out.splitlines():
            if "level:" in line:
                try:
                    return int(line.split("level:")[1].strip())
                except ValueError:
                    continue
        return None

    def get_screenshot(self, path: str) -> bool:
        # Pull a screenshot from the device to the host.
        ok, _ = self._run(self._device_arg() + ["exec-out", "screencap", "-p"], capture_output=False)
        # For simplicity we fallback to the `adb exec-out` pipe and write directly.
        # If that fails we log and return False.
        if not ok:
            return False
        # The command already writes image data to stdout; we redirect it to a file.
        try:
            with open(path, "wb") as f:
                subprocess.run([str(self.adb_path)] + self._device_arg() + ["exec-out", "screencap", "-p"], stdout=f)
            fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "screenshot", "path": path})
            return True
        except Exception:
            logger.exception("Failed to write screenshot to %s", path)
            return False

    def send_text(self, text: str) -> bool:
        # Escape spaces for the shell – using shlex.quote works for POSIX, but adb on Windows
        # is tolerant of plain strings, so we simply pass the raw text.
        ok, _ = self._run(self._device_arg() + ["shell", "input", "text", text])
        fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "send_text", "text": text})
        return ok

    def run_shell(self, cmd: str) -> Optional[str]:
        ok, out = self._run(self._device_arg() + ["shell", cmd])
        fire_event(Events.ADB_COMMAND_EXECUTED, {"action": "run_shell", "cmd": cmd, "output": out})
        return out if ok else None

    # ---------------------------------------------------------------------
    # Convenience API surface for FastAPI
    # ---------------------------------------------------------------------
    def get_actions(self) -> dict:
        """Return a dictionary of lightweight actions that can be called from HTTP.
        The values are callables that accept ``**kwargs`` matching the method signatures.
        """
        return {
            "tap": lambda x, y: self.tap(int(x), int(y)),
            "swipe": lambda x1, y1, x2, y2, duration_ms=300: self.swipe(int(x1), int(y1), int(x2), int(y2), int(duration_ms)),
            "press_key": lambda keycode: self.press_key(int(keycode)),
            "open_app": lambda package: self.open_app(package),
            "get_battery": lambda: self.get_battery(),
            "screenshot": lambda path: self.get_screenshot(path),
            "send_text": lambda text: self.send_text(text),
            "run_shell": lambda cmd: self.run_shell(cmd),
        }


# Export a module‑level singleton for easy import
adb_manager = ADBManager()


def get_adb_manager() -> ADBManager:
    """Return the global ``adb_manager`` instance.
    This helper mirrors the pattern used by other FRIDAY subsystems.
    """
    return adb_manager
