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

def register():
    pass

def unregister():
    pass
