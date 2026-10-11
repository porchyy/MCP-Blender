"""Predefined action handlers for Blender bridge.

Security Notice:
Only registered actions in ACTION_HANDLERS are allowed to execute.
Arbitrary code execution (eval, exec, subprocess, system) is strictly forbidden.
"""
import sys
from typing import Any, Dict, Optional


def _get_bpy():
    """Retrieve bpy module if loaded in current Python process."""
    if "bpy" in sys.modules:
        return sys.modules["bpy"]
    try:
        import bpy  # type: ignore
        return bpy
    except ImportError:
        return None


def handle_get_status(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve Blender version, active scene, and object count safely."""
    bpy_module = _get_bpy()
    if bpy_module is None:
        return {
            "blender_version": "unknown",
            "api_version": "1.0.0",
            "scene_name": None,
            "objects_count": 0,
            "message": "bpy module not found (standalone mode)",
        }

    version_str = getattr(bpy_module.app, "version_string", "unknown")
    scene = getattr(bpy_module.context, "scene", None)
    scene_name = getattr(scene, "name", None) if scene else None
    
    objects_data = getattr(bpy_module.data, "objects", [])
    try:
        objects_count = len(objects_data)
    except Exception:
        objects_count = 0

    return {
        "blender_version": version_str,
        "api_version": "1.0.0",
        "scene_name": scene_name,
        "objects_count": objects_count,
        "message": "Blender is ready and bridge is active",
    }


# Strictly allowlisted actions.
ACTION_HANDLERS = {
    "get_status": handle_get_status,
}


def execute_action(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatch an incoming action strictly against predefined allowlist."""
    handler = ACTION_HANDLERS.get(action)
    if not handler:
        raise ValueError(f"Action '{action}' is not supported")
    return handler(params or {})
