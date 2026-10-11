"""Tests for Blender Add-on bridge server lifecycle and HTTP routes (Ticket 4)."""
import time
import httpx
import pytest
from blender_addon.bridge_server import (
    start_server,
    stop_server,
    is_server_running,
    get_server_port,
)


@pytest.fixture(autouse=True)
def ensure_server_stopped():
    """Ensure server is always stopped before and after test."""
    stop_server()
    yield
    stop_server()


def test_bridge_server_lifecycle_and_endpoints():
    """Server starts, responds to /health and /api/v1/action, then stops cleanly."""
    test_port = 19876
    assert not is_server_running()
    
    started = start_server(host="127.0.0.1", port=test_port)
    assert started is True
    assert is_server_running() is True
    assert get_server_port() == test_port
    
    time.sleep(0.1)  # Allow thread to bind
    
    # 1. Test /health
    res = httpx.get(f"http://127.0.0.1:{test_port}/health", timeout=1.0)
    assert res.status_code == 200
    assert res.json().get("status") == "ok"
    
    # 2. Test /api/v1/action (valid action)
    action_res = httpx.post(
        f"http://127.0.0.1:{test_port}/api/v1/action",
        json={"action": "get_status"},
        timeout=1.0,
    )
    assert action_res.status_code == 200
    data = action_res.json()
    assert data.get("status") == "ok"
    assert "blender_version" in data.get("data", {})
    
    # 3. Test /api/v1/action (unsupported action rejected)
    bad_res = httpx.post(
        f"http://127.0.0.1:{test_port}/api/v1/action",
        json={"action": "unsupported_action"},
        timeout=1.0,
    )
    assert bad_res.status_code == 400
    assert bad_res.json().get("status") == "error"
    
    # 4. Stop server
    stopped = stop_server()
    assert stopped is True
    assert is_server_running() is False
