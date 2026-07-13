"""
Vision System - Camera Integration and Processing
Supports Sony Xperia J2 phone camera via USB/WiFi
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Any, Dict

import numpy as np

from src.friday.config import settings
from src.friday.events import fire_event, Events

logger = logging.getLogger("friday.vision")

@dataclass
class FrameResult:
    """Result of frame processing."""
    timestamp: float
    frame_id: int
    faces: list
    objects: list
    emotions: list
    text: str
    processed: bool
    frame: Optional[object] = None

class VisionEngine:
    """
    Vision processing engine for FRIDAY AI.

    Features:
    - Camera stream (Sony Xperia J2 via ADB/IP Webcam)
    - Face detection with MediaPipe
    - Object detection
    - OCR text extraction
    - Emotion analysis
    - Event broadcasting
    """

    def __init__(self):
        self._running = False
        self._thread = None
        self._frame_count = 0
        self._callbacks: list = []
        self._source = "camera"  # "camera", "adb", "webcam", "file", "browser"
        self._adb_path = settings.ADB_PATH
        self._frame_skip = settings.FRAME_SKIP
        self._target_width = settings.FRAME_WIDTH
        self._target_height = settings.FRAME_HEIGHT
        self._cascade = None
        self._face_cascade_path = None
        self._last_frame_result: Optional[FrameResult] = None
        self._last_frame: Optional[np.ndarray] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None  # Stored event loop reference
        self._browser_frame: Optional[np.ndarray] = None  # Latest frame from browser WebRTC
        self._browser_frame_time: float = 0  # Timestamp of last browser frame

    def load_face_cascade(self) -> bool:
        """Load OpenCV face cascade for detection."""
        import cv2
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if Path(cascade_path).exists():
            self._cascade = cv2.CascadeClassifier(cascade_path)
            self._face_cascade_path = cascade_path
            logger.info("Face cascade loaded: %s", cascade_path)
            return True
        logger.warning("Face cascade not found")
        return False

    def start(self, source: str = "adb") -> bool:
        """Start vision processing."""
        if self._running:
            return True

        self._source = source
        self._running = True

        # Capture the event loop from the calling thread so we can schedule
        # coroutines thread-safely from the background processing thread.
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop in this thread; fire_event calls will be skipped
            # until an event loop is available (e.g. via set_loop).
            self._loop = None
            logger.debug("Vision started without a running event loop")

        if source == "adb" and Path(self._adb_path).exists():
            self._start_adb_camera()
        elif source == "webcam":
            self._start_webcam()
        elif source == "file":
            pass  # Will process on demand

        threading.Thread(target=self._processing_loop, daemon=True).start()
        logger.info("Vision engine started: %s", source)
        return True

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Provide an event loop reference for thread-safe event scheduling.

        Call this from an async context (e.g. app startup) so that
        fire_event coroutines can be dispatched from the background thread.
        """
        self._loop = loop

    def stop(self):
        """Stop vision processing."""
        self._running = False
        logger.info("Vision engine stopped")

    def _start_adb_camera(self):
        """Initialize ADB connection for Xperia J2."""
        import subprocess
        try:
            result = subprocess.run(
                [str(self._adb_path), "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("ADB connected, devices: %s", result.stdout[:100])
            else:
                logger.warning("ADB not available")
        except Exception as e:
            logger.error("ADB connection failed: %s", e)

    def _start_webcam(self):
        """Initialize webcam capture."""
        import cv2
        logger.info("Webcam mode selected")
        # Will open on first frame read

    def _processing_loop(self):
        """Background processing loop."""
        while self._running:
            try:
                frame = self._read_frame()
                if frame is not None:
                    result = self._process_frame(frame)
                    self._last_frame_result = result
                    self._last_frame = frame
                    if self._callbacks:
                        for cb in self._callbacks:
                            try:
                                cb(result)
                            except Exception as e:
                                logger.error("Callback error: %s", e)

                    # Fire events using stored loop if available
                    if self._loop is not None:
                        try:
                            asyncio.run_coroutine_threadsafe(
                                fire_event(Events.SYSTEM_READY, {"frame_id": result.frame_id}),
                                self._loop
                            )
                        except RuntimeError:
                            logger.warning("Cannot schedule event - loop closed")
                    else:
                        logger.debug("Skipping event fire - no event loop available")

                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                logger.error("Processing loop error: %s", e)

    def _read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the current source."""
        import cv2
        if self._source == "adb":
            return self._read_adb_frame()
        elif self._source == "webcam":
            return self._read_webcam_frame()
        elif self._source == "file":
            return self._read_file_frame()
        elif self._source == "browser":
            return self._read_browser_frame()
        return None

    def _read_browser_frame(self) -> Optional[np.ndarray]:
        """Read the latest frame received from browser WebRTC."""
        if self._browser_frame is not None:
            return self._browser_frame.copy()
        return None

    def _read_adb_frame(self) -> Optional[np.ndarray]:
        """Read frame from Xperia J2 via ADB screen capture."""
        import subprocess
        try:
            # Use ADB screencap to get frame
            result = subprocess.run(
                [str(self._adb_path), "exec-out", "screencap", "-p"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                # Decode image
                import cv2
                nparr = np.frombuffer(result.stdout, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None:
                    # Resize for processing
                    frame = cv2.resize(frame, (self._target_width, self._target_height))
                    return frame
        except Exception as e:
            logger.debug("ADB frame read failed: %s", e)
        return None

    def _read_webcam_frame(self) -> Optional[np.ndarray]:
        """Read frame from local webcam."""
        import cv2
        if not hasattr(self, '_webcam'):
            self._webcam = cv2.VideoCapture(0)
        ret, frame = self._webcam.read()
        if ret and frame is not None:
            frame = cv2.resize(frame, (self._target_width, self._target_height))
            return frame
        return None

    def _read_file_frame(self) -> Optional[np.ndarray]:
        """Read frame from test file."""
        test_path = settings.SNAPSHOTS_DIR / "test_frame.jpg"
        if test_path.exists():
            import cv2
            frame = cv2.imread(str(test_path))
            if frame is not None:
                return cv2.resize(frame, (self._target_width, self._target_height))
        return None

    def _process_frame(self, frame: np.ndarray) -> FrameResult:
        """Process frame for faces, objects, text, emotions."""
        self._frame_count += 1
        timestamp = time.time()

        faces = []
        objects = []
        emotions = []
        text = ""
        qr_data = None

        # QR code detection
        try:
            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(frame)
            if data:
                qr_data = data
                text = data  # Expose QR content as text in FrameResult
                if self._loop is not None:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            fire_event(Events.QR_DETECTED, {"data": data, "frame_id": self._frame_count}),
                            self._loop
                        )
                    except RuntimeError:
                        pass
        except Exception as e:
            logger.debug("QR detection skipped: %s", e)

        # Face detection
        if self._cascade:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            detected = self._cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            for (x, y, w, h) in detected:
                faces.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

        # Broadcast results using stored loop if available
        if self._loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(
                    fire_event("frame_processed", {
                        "frame_id": self._frame_count,
                        "faces": faces,
                        "objects": objects,
                        "emotions": emotions,
                        "text": text
                    }),
                    self._loop
                )
            except RuntimeError:
                logger.warning("Cannot schedule frame_processed event - loop closed")
        else:
            logger.debug("Skipping frame_processed event - no event loop available")

        return FrameResult(
            timestamp=timestamp,
            frame_id=self._frame_count,
            faces=faces,
            objects=objects,
            emotions=emotions,
            text=text,
            processed=True,
            frame=frame
        )

    def register_callback(self, callback: Callable):
        """Register a callback for frame results."""
        self._callbacks.append(callback)

    def is_running(self) -> bool:
        return self._running

    def get_last_result(self) -> Optional[FrameResult]:
        return self._last_frame_result

    def get_last_frame(self) -> Optional[np.ndarray]:
        """Return the last captured frame."""
        return self._last_frame

# Global instance
vision = VisionEngine()