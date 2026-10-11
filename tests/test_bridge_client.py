"""Tests for BlenderBridgeClient (Ticket 2: Localhost Bridge Resilience)."""
import pytest
from unittest.mock import patch
import httpx
from mcp_server.bridge_client import BlenderBridgeClient
from mcp_server.models import BlenderStatus


def test_bridge_client_offline_returns_disconnected():
    """When Blender is offline (e.g. port closed), client returns connected=False without crashing."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9999, timeout=0.5)
    status = client.get_status()
    assert isinstance(status, BlenderStatus)
    assert status.connected is False
    assert status.blender_version is None
    assert any(term in status.message.lower() for term in ["unavailable", "failed", "timed out", "timeout"])


def test_bridge_client_timeout_returns_disconnected():
    """When request times out, client returns connected=False with timeout message."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=0.1)
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Request timed out")):
        status = client.get_status()
        assert status.connected is False
        assert "timeout" in status.message.lower()


def test_bridge_client_success_returns_status():
    """When Blender server responds successfully, client parses and returns full status."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_response = {
        "status": "ok",
        "data": {
            "blender_version": "5.2.2",
            "api_version": "1.0.0",
            "scene_name": "Scene",
            "objects_count": 3,
            "message": "Blender is ready",
        },
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_response
        status = client.get_status()
        assert status.connected is True
        assert status.blender_version == "5.2.2"
        assert status.scene_name == "Scene"
        assert status.objects_count == 3
        assert status.message == "Blender is ready"
