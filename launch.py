#!/usr/bin/env python3
"""
launch.py – Cross-platform launch helper for Friday AI

Features
--------
* Checks Python, Node, pip & npm
* Optionally installs dependencies (--install)
* Loads .env into os.environ
* Starts uvicorn backend, health-checks it, then starts Next.js frontend
* Writes PID files (backend.pid, frontend.pid) for the companion stop script

Usage
-----
    python launch.py                # launch backend + frontend (no auto-install)
    python launch.py --install      # install missing pip/npm deps first
    python launch.py --no-frontend  # start backend only (API testing)
"""

import argparse
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

BASE = pathlib.Path(__file__).parent.resolve()
BACKEND_LOG = BASE / "backend.log"
FRONTEND_LOG = BASE / "frontend.log"
BACKEND_PID = BASE / "backend.pid"
FRONTEND_PID = BASE / "frontend.pid"


def run_cmd(cmd, cwd=None, capture=False):
    """Run a shell command, raise on failure, optionally capture stdout."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}\n{result.stdout}")
    return result.stdout if capture else None


def verify_prereqs():
    print("[INFO] Verifying Python, Node, pip, npm …")
    subprocess.run([sys.executable, "--version"], check=True)
    subprocess.run(["node", "--version"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    subprocess.run(["npm", "--version"], check=True)


def load_env():
    env_path = BASE / ".env"
    if env_path.is_file():
        print("[INFO] Loading .env variables …")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition("=")
                os.environ[key.strip()] = os.path.expandvars(val.strip())
    else:
        print("[WARN] .env file not found – proceeding without it.")


def install_deps():
    print("[INFO] Installing Python requirements …")
    run_cmd(f"{sys.executable} -m pip install -r requirements.txt")
    print("[INFO] Installing Node dependencies …")
    run_cmd("npm install", cwd=BASE / "frontend")


def start_backend(port):
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.friday.api.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    print(f"[INFO] Starting backend on http://127.0.0.1:{port} …")
    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE),
        stdout=open(BACKEND_LOG, "a"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    BACKEND_PID.write_text(str(proc.pid))
    return proc


def health_check(port, timeout=30):
    import urllib.request
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_frontend():
    print("[INFO] Starting Next.js frontend (npm run dev) …")
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(BASE / "frontend"),
        stdout=open(FRONTEND_LOG, "a"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    FRONTEND_PID.write_text(str(proc.pid))
    return proc


def main():
    parser = argparse.ArgumentParser(description="Robust Friday launcher")
    parser.add_argument("--install", action="store_true", help="install pip/npm deps")
    parser.add_argument("--port", type=int, default=8000, help="backend port")
    parser.add_argument("--no-frontend", action="store_true", help="run backend only")
    args = parser.parse_args()

    load_env()
    verify_prereqs()
    if args.install:
        install_deps()

    backend_proc = start_backend(args.port)

    print("[INFO] Waiting for backend health …")
    if not health_check(args.port):
        print("[ERROR] Backend did not become healthy – see backend.log", file=sys.stderr)
        backend_proc.terminate()
        sys.exit(1)
    print("[INFO] ✅ Backend healthy!")

    if not args.no_frontend:
        start_frontend()
        print(f"[INFO] 🚀 All systems go – backend: http://127.0.0.1:{args.port}  frontend: http://localhost:3000")
    else:
        print("[INFO] 🚀 Backend only – no frontend started.")


if __name__ == "__main__":
    main()