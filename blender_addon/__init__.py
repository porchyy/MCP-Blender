"""Blender Asset Prep Add-on Package."""
bl_info = {
    "name": "Blender Asset Prep MCP Bridge",
    "author": "Antigravity Pair",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Asset Prep MCP",
    "description": "Local bridge connecting Blender to Google Antigravity via MCP",
    "category": "Development",
}

from . import handlers
from . import bridge_server
from . import ui


def register():
    """Register addon components."""
    ui.register_ui()


def unregister():
    """Unregister addon components and stop running server cleanly."""
    bridge_server.stop_server()
    ui.unregister_ui()


if __name__ == "__main__":
    register()
