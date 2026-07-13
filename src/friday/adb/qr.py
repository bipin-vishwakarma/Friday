import socket
import io
from typing import Tuple
import qrcode

from ..events import Events, fire_event


def _get_local_ip() -> str:
    """Return the most likely local IP address for Wi-Fi connections.

    This opens a UDP socket to a public address (8.8.8.8) and reads the
    socket's own address – no packets are actually sent.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        # Fallback to localhost; the QR will still be valid for manual edit.
        return "127.0.0.1"


def generate_qr_png() -> Tuple[bytes, str]:
    """Generate a QR code PNG that contains the ADB over-WiFi command.

    Returns a tuple of (png_bytes, command_string). The command is of the
    form ``adb connect <ip>:5555`` which the Android device can execute after
    scanning the QR code.
    """
    ip = _get_local_ip()
    cmd = f"adb connect {ip}:5555"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q)
    qr.add_data(cmd)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    with io.BytesIO() as buf:
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
    fire_event(Events.ADB_QR_GENERATED, {"ip": ip, "command": cmd})
    return png_bytes, cmd


def get_qr_payload() -> Tuple[bytes, str]:
    """Public function returning the QR payload for the HTTP handler."""
    return generate_qr_png()