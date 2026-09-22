import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.agents.router import RouterAgent
from app.agents.monitor import MonitorAgent
from app.agents.pc_controller import PCControllerAgent
from app.config import settings

def test_router_system_monitor():
    router = RouterAgent()
    decision = router.route("check cpu and memory usage")
    assert decision["intent"] == "system_monitor"

def test_router_pc_action_volume():
    router = RouterAgent()
    decision = router.route("mute volume")
    assert decision["intent"] == "pc_control"
    assert decision["action"] == "mute_volume"

def test_router_web_search():
    router = RouterAgent()
    decision = router.route("search for quantum computing")
    assert decision["intent"] == "web_search"
    assert "quantum computing" in decision["params"]["query"]

def test_router_chat_buddy():
    router = RouterAgent()
    decision = router.route("good morning friday, how are you?")
    assert decision["intent"] == "chat_buddy"

def test_monitor_telemetry():
    monitor = MonitorAgent()
    data = monitor.get_telemetry()
    assert "cpu" in data
    assert "percent" in data["cpu"]
    assert "memory" in data
    assert "percent" in data["memory"]

def test_pc_controller_unknown():
    controller = PCControllerAgent()
    res = controller.execute("non_existent_command_xyz")
    assert res["status"] == "unknown_action"
