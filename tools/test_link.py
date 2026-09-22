import time
import subprocess
import requests

def test_link():
    print("[*] Setting up ADB reverse port 8000...")
    subprocess.run(["adb", "-s", "ee866a9b", "reverse", "tcp:8000", "tcp:8000"])

    print("[*] Launching Friday backend in background...")
    proc = subprocess.Popen(
        [r"c:\Users\Lenovo\Desktop\Friday\.venv\Scripts\python.exe", "backend/run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for backend to be ready
        for _ in range(10):
            try:
                r = requests.get("http://localhost:8000/api/health", timeout=1)
                if r.status_code == 200:
                    print("[OK] Backend is online!")
                    break
            except Exception:
                time.sleep(0.5)

        # Wait 4 seconds for phone WebSocket to connect and receive telemetry/media
        time.sleep(4)

        print("[*] Capturing screen while connected...")
        subprocess.run(
            'adb -s ee866a9b exec-out screencap -p > "c:\\Users\\Lenovo\\Desktop\\Friday\\phone_screen_connected.png"',
            shell=True
        )
        print("[OK] Screenshot saved to phone_screen_connected.png")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_link()
