"""Tests for MCP Server tool registration and execution (Ticket 3)."""
import json
from unittest.mock import patch
from mcp_server.server import get_blender_status
from mcp_server.models import BlenderStatus


def test_get_blender_status_tool_offline():
    """Tool execution when Blender is offline produces valid JSON BlenderStatus."""
    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_status") as mock_get_status:
        mock_get_status.return_value = BlenderStatus(
            connected=False,
            blender_version=None,
            api_version="1.0.0",
            scene_name=None,
            objects_count=None,
            message="Bridge unavailable",
        )
        res_json = get_blender_status()
        assert isinstance(res_json, str)
        parsed = json.loads(res_json)
        assert parsed["connected"] is False
        assert parsed["blender_version"] is None
        assert "Bridge unavailable" in parsed["message"]


def test_get_blender_status_tool_online():
    """Tool execution when Blender is online produces valid JSON BlenderStatus."""
    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_status") as mock_get_status:
        mock_get_status.return_value = BlenderStatus(
            connected=True,
            blender_version="5.2.2",
            api_version="1.0.0",
            scene_name="MainScene",
            objects_count=5,
            message="Blender is ready",
        )
        res_json = get_blender_status()
        parsed = json.loads(res_json)
        assert parsed["connected"] is True
        assert parsed["blender_version"] == "5.2.2"
        assert parsed["scene_name"] == "MainScene"
        assert parsed["objects_count"] == 5
