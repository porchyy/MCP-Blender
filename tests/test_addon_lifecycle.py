"""Tests for Blender addon registration lifecycle."""
import blender_addon


def test_addon_register_and_unregister():
    """Addon register and unregister execute without exceptions in headless environment."""
    blender_addon.register()
    blender_addon.unregister()
    assert blender_addon.bridge_server.is_server_running() is False
