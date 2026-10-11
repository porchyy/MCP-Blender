"""Tests for Blender Add-on action handlers (Ticket 3)."""
import pytest
from unittest.mock import MagicMock
import sys


def test_execute_action_disallows_arbitrary_actions():
    """Security check: execute_action rejects any unknown or arbitrary actions."""
    from blender_addon.handlers import execute_action
    
    with pytest.raises(ValueError, match="Action 'unknown_command' is not supported"):
        execute_action("unknown_command")

    with pytest.raises(ValueError, match="Action 'eval' is not supported"):
        execute_action("eval")

    with pytest.raises(ValueError, match="Action 'exec' is not supported"):
        execute_action("exec")


def test_execute_action_get_status_with_mocked_bpy():
    """execute_action('get_status') extracts Blender version, scene, and object count."""
    mock_bpy = MagicMock()
    mock_bpy.app.version_string = "5.2.2"
    mock_bpy.context.scene.name = "TestScene"
    mock_bpy.data.objects = ["Cube", "Light", "Camera"]
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("get_status")
        
        assert result["blender_version"] == "5.2.2"
        assert result["api_version"] == "1.0.0"
        assert result["scene_name"] == "TestScene"
        assert result["objects_count"] == 3
        assert "ready" in result["message"].lower()
