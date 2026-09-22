"""
PC Controller Agent
Executes native Windows desktop automation, media controls, app launching,
and hardware actions using Win32 API and PyAutoGUI.
"""

import os
import sys
import ctypes
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("friday.pc_controller")

# Virtual-Key Codes for Windows Media & System
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

COMMON_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "spotify": "spotify",
    "code": "code",
    "vs code": "code",
    "visual studio code": "code",
    "notepad": "notepad",
    "calc": "calc",
    "calculator": "calc",
    "explorer": "explorer",
    "files": "explorer",
    "cmd": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "settings": "ms-settings:"
}

class PCControllerAgent:
    def __init__(self):
        self._user32 = ctypes.windll.user32

    def _send_key(self, vk_code: int):
        """Simulate Windows virtual key press."""
        self._user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        self._user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

    def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a desktop command."""
        params = params or {}
        logger.info(f"Executing PC action: {action} with params: {params}")

        try:
            if action == "set_volume":
                # Relative volume adjust approximation via keys or COM
                level = max(0, min(100, params.get("level", 50)))
                # Set volume by sending keys or via PowerShell audio script
                cmd = f"(New-Object -ComObject WScript.Shell).SendKeys([char]174*50); (New-Object -ComObject WScript.Shell).SendKeys([char]175*{int(level/2)})"
                subprocess.run(["powershell", "-Command", cmd], capture_output=True)
                return {"status": "success", "message": f"Volume set to approximately {level}%"}

            elif action == "volume_up":
                steps = params.get("steps", 5)
                for _ in range(steps):
                    self._send_key(VK_VOLUME_UP)
                return {"status": "success", "message": "Volume increased"}

            elif action == "volume_down":
                steps = params.get("steps", 5)
                for _ in range(steps):
                    self._send_key(VK_VOLUME_DOWN)
                return {"status": "success", "message": "Volume decreased"}

            elif action == "mute_volume":
                self._send_key(VK_VOLUME_MUTE)
                return {"status": "success", "message": "Volume toggled mute"}

            elif action == "media_play_pause":
                self._send_key(VK_MEDIA_PLAY_PAUSE)
                return {"status": "success", "message": "Media playback toggled"}

            elif action == "media_next":
                self._send_key(VK_MEDIA_NEXT_TRACK)
                return {"status": "success", "message": "Skipped to next track"}

            elif action == "media_prev":
                self._send_key(VK_MEDIA_PREV_TRACK)
                return {"status": "success", "message": "Went to previous track"}

            elif action == "lock_workstation":
                self._user32.LockWorkStation()
                return {"status": "success", "message": "Workstation locked"}

            elif action == "sleep_pc":
                subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
                return {"status": "success", "message": "PC entering sleep mode"}

            elif action == "open_application":
                app_query = params.get("app", "").lower().strip()
                target = COMMON_APPS.get(app_query, app_query)
                try:
                    if target.startswith("ms-"):
                        os.startfile(target)
                    else:
                        subprocess.Popen(f"start {target}", shell=True)
                    return {"status": "success", "message": f"Launched {app_query}"}
                except Exception as e:
                    return {"status": "error", "message": f"Failed to launch {app_query}: {e}"}

            elif action == "close_application":
                app_query = params.get("app", "").lower().strip()
                target = COMMON_APPS.get(app_query, app_query)
                if not target.endswith(".exe"):
                    target += ".exe"
                res = subprocess.run(["taskkill", "/F", "/IM", target], capture_output=True, text=True)
                if res.returncode == 0:
                    return {"status": "success", "message": f"Closed {app_query}"}
                else:
                    return {"status": "error", "message": f"Could not find or close {app_query}"}

            elif action == "take_screenshot":
                import pyautogui
                from pathlib import Path
                shots_dir = Path.home() / "Pictures" / "FridayScreenshots"
                shots_dir.mkdir(parents=True, exist_ok=True)
                import time
                filename = shots_dir / f"screenshot_{int(time.time())}.png"
                pyautogui.screenshot(str(filename))
                return {"status": "success", "message": f"Screenshot saved to {filename}"}

            elif action == "show_desktop":
                import pyautogui
                pyautogui.hotkey('win', 'd')
                return {"status": "success", "message": "Toggled desktop"}

            else:
                return {"status": "unknown_action", "message": f"Action '{action}' not recognized."}

        except Exception as e:
            logger.error(f"Error executing PC action {action}: {e}")
            return {"status": "error", "message": str(e)}
