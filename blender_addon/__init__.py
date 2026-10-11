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
from . import dispatcher
from . import ui


def register():
    """Register addon components and start bridge server."""
    ui.register_ui()
    try:
        bridge_server.start_server()
    except Exception as exc:
        print(f"[Blender Asset Prep] Note: Auto-start bridge server deferred: {exc}")


def unregister():
    """Unregister addon components and stop running server cleanly."""
    bridge_server.stop_server()
    ui.unregister_ui()


if __name__ == "__main__":
    register()
