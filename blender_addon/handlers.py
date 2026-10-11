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


def handle_list_scene_objects(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve objects in the active scene with transforms, types, and collections."""
    params = params or {}
    try:
        limit = min(max(int(params.get("limit", 100)), 1), 500)
    except (ValueError, TypeError):
        limit = 100
    try:
        offset = max(int(params.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    bpy_module = _get_bpy()
    if bpy_module is None:
        return {
            "scene_name": "unknown",
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "objects": [],
        }

    scene = getattr(bpy_module.context, "scene", None)
    if not scene:
        return {
            "scene_name": "unknown",
            "total_count": 0,
            "limit": limit,
            "offset": offset,
            "objects": [],
        }

    scene_name = getattr(scene, "name", "Scene")
    raw_objects = getattr(scene, "objects", [])
    try:
        all_objects = sorted(list(raw_objects), key=lambda o: getattr(o, "name", ""))
    except Exception:
        all_objects = list(raw_objects)

    total_count = len(all_objects)
    page_objects = all_objects[offset : offset + limit]

    result_objects = []
    for obj in page_objects:
        obj_name = getattr(obj, "name", "Unnamed")
        obj_type = str(getattr(obj, "type", "UNKNOWN"))
        loc = [round(float(v), 5) for v in getattr(obj, "location", (0.0, 0.0, 0.0))]
        rot = [round(float(v), 5) for v in getattr(obj, "rotation_euler", (0.0, 0.0, 0.0))]
        scale = [round(float(v), 5) for v in getattr(obj, "scale", (1.0, 1.0, 1.0))]
        colls = [str(c.name) for c in getattr(obj, "users_collection", []) if hasattr(c, "name")]

        result_objects.append({
            "name": obj_name,
            "type": obj_type,
            "location": loc,
            "rotation_euler": rot,
            "scale": scale,
            "collections": colls,
        })

    return {
        "scene_name": scene_name,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "objects": result_objects,
    }


def handle_get_object_details(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve detailed properties of a specific object."""
    params = params or {}
    object_name = params.get("object_name")
    if not object_name or not isinstance(object_name, str) or not object_name.strip():
        raise ValueError("Parameter 'object_name' is required and must be a non-empty string")
    object_name = object_name.strip()

    bpy_module = _get_bpy()
    if bpy_module is None:
        raise RuntimeError("bpy module not found (standalone mode)")

    scene = getattr(bpy_module.context, "scene", None)
    scene_name = getattr(scene, "name", "unknown") if scene else "unknown"

    target_obj = None
    if scene and hasattr(scene, "objects"):
        target_obj = scene.objects.get(object_name)
    if target_obj is None and hasattr(bpy_module, "data") and hasattr(bpy_module.data, "objects"):
        target_obj = bpy_module.data.objects.get(object_name)

    if target_obj is None:
        raise ValueError(f"Object '{object_name}' not found in active scene '{scene_name}'")

    obj_type = str(getattr(target_obj, "type", "UNKNOWN"))
    loc = [round(float(v), 5) for v in getattr(target_obj, "location", (0.0, 0.0, 0.0))]
    rot = [round(float(v), 5) for v in getattr(target_obj, "rotation_euler", (0.0, 0.0, 0.0))]
    scale = [round(float(v), 5) for v in getattr(target_obj, "scale", (1.0, 1.0, 1.0))]
    dims = [round(float(v), 5) for v in getattr(target_obj, "dimensions", (0.0, 0.0, 0.0))]
    colls = [str(c.name) for c in getattr(target_obj, "users_collection", []) if hasattr(c, "name")]
    visible = not bool(getattr(target_obj, "hide_viewport", False))

    parent = None
    parent_obj = getattr(target_obj, "parent", None)
    if parent_obj and hasattr(parent_obj, "name"):
        parent = str(parent_obj.name)

    data_name = None
    data_obj = getattr(target_obj, "data", None)
    if data_obj and hasattr(data_obj, "name"):
        data_name = str(data_obj.name)

    mat_slots = []
    for slot in getattr(target_obj, "material_slots", []):
        mat = getattr(slot, "material", None)
        if mat and hasattr(mat, "name"):
            mat_slots.append(str(mat.name))

    mesh_info = None
    if obj_type == "MESH" and data_obj:
        v_count = len(getattr(data_obj, "vertices", []))
        p_count = len(getattr(data_obj, "polygons", []))
        e_count = len(getattr(data_obj, "edges", []))
        mesh_info = {
            "vertex_count": v_count,
            "polygon_count": p_count,
            "edge_count": e_count,
        }

    return {
        "name": target_obj.name,
        "type": obj_type,
        "location": loc,
        "rotation_euler": rot,
        "scale": scale,
        "dimensions": dims,
        "collections": colls,
        "visible": visible,
        "parent": parent,
        "data_name": data_name,
        "material_slots": mat_slots,
        "mesh_info": mesh_info,
    }


def handle_list_scene_collections(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve the hierarchy of collections and their objects in the active scene."""
    bpy_module = _get_bpy()
    if bpy_module is None:
        return {
            "scene_name": "unknown",
            "master_collection": {
                "name": "Scene Collection",
                "parent": None,
                "objects": [],
                "children": [],
            },
            "collections": [],
        }

    scene = getattr(bpy_module.context, "scene", None)
    if not scene or not hasattr(scene, "collection"):
        return {
            "scene_name": "unknown",
            "master_collection": {
                "name": "Scene Collection",
                "parent": None,
                "objects": [],
                "children": [],
            },
            "collections": [],
        }

    scene_name = getattr(scene, "name", "Scene")
    master = scene.collection

    master_summary = {
        "name": getattr(master, "name", "Scene Collection"),
        "parent": None,
        "objects": sorted([str(o.name) for o in getattr(master, "objects", []) if hasattr(o, "name")]),
        "children": sorted([str(c.name) for c in getattr(master, "children", []) if hasattr(c, "name")]),
    }

    collections_list = []
    visited = set()

    def traverse(col, parent_name: str):
        col_id = id(col)
        if col_id in visited:
            return
        visited.add(col_id)

        col_name = getattr(col, "name", "Unnamed Collection")
        objs = sorted([str(o.name) for o in getattr(col, "objects", []) if hasattr(o, "name")])
        child_names = sorted([str(c.name) for c in getattr(col, "children", []) if hasattr(c, "name")])

        collections_list.append({
            "name": col_name,
            "parent": parent_name,
            "objects": objs,
            "children": child_names,
        })

        for child in getattr(col, "children", []):
            traverse(child, parent_name=col_name)

    for child in getattr(master, "children", []):
        traverse(child, parent_name=master_summary["name"])

    return {
        "scene_name": scene_name,
        "master_collection": master_summary,
        "collections": collections_list,
    }


# Strictly allowlisted actions.
ACTION_HANDLERS = {
    "get_status": handle_get_status,
    "list_scene_objects": handle_list_scene_objects,
    "get_object_details": handle_get_object_details,
    "list_scene_collections": handle_list_scene_collections,
}


def execute_action(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatch an incoming action strictly against predefined allowlist."""
    handler = ACTION_HANDLERS.get(action)
    if not handler:
        raise ValueError(f"Action '{action}' is not supported")
    return handler(params or {})

