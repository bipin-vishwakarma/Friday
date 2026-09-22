import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["version"] == "2.0.0"

def test_api_telemetry(client):
    res = client.get("/api/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert "cpu" in data
    assert "memory" in data

def test_process_pc_action(client):
    res = client.post("/api/process", json={"text": "mute volume", "speak": False})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "pc_control"
    assert "toggled mute" in data["reply"]

def test_process_system_monitor(client):
    res = client.post("/api/process", json={"text": "how is the cpu and ram", "speak": False})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "system_monitor"
    assert "CPU is currently at" in data["reply"]

def test_process_chat_buddy(client):
    res = client.post("/api/process", json={"text": "hello Friday", "speak": False})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "chat_buddy"
    assert len(data["reply"]) > 5
