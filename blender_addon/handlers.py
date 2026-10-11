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


def _get_bmesh():
    """Retrieve bmesh module if loaded in current Python process."""
    if "bmesh" in sys.modules:
        return sys.modules["bmesh"]
    try:
        import bmesh  # type: ignore
        return bmesh
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


def handle_inspect_mesh(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Inspect and validate mesh geometry, topology, and normals (read-only)."""
    params = params or {}
    object_name = params.get("object_name")
    if not object_name or not isinstance(object_name, str) or not object_name.strip():
        raise ValueError("Parameter 'object_name' is required and must be a non-empty string")
    object_name = object_name.strip()
    if len(object_name) > 256:
        raise ValueError("Parameter 'object_name' exceeds maximum length of 256 characters")

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
    dims = [round(float(v), 5) for v in getattr(target_obj, "dimensions", (0.0, 0.0, 0.0))]
    transform = {
        "location": [round(float(v), 5) for v in getattr(target_obj, "location", (0.0, 0.0, 0.0))],
        "rotation_euler": [round(float(v), 5) for v in getattr(target_obj, "rotation_euler", (0.0, 0.0, 0.0))],
        "scale": [round(float(v), 5) for v in getattr(target_obj, "scale", (1.0, 1.0, 1.0))],
    }

    if obj_type != "MESH":
        return {
            "name": target_obj.name,
            "type": obj_type,
            "is_mesh": False,
            "is_empty": False,
            "vertex_count": None,
            "edge_count": None,
            "polygon_count": None,
            "dimensions": dims,
            "transform": transform,
            "validation": None,
            "message": f"Object '{target_obj.name}' is of type '{obj_type}', not a MESH",
        }

    mesh_data = getattr(target_obj, "data", None)
    if mesh_data is None:
        return {
            "name": target_obj.name,
            "type": "MESH",
            "is_mesh": True,
            "is_empty": True,
            "vertex_count": 0,
            "edge_count": 0,
            "polygon_count": 0,
            "dimensions": dims,
            "transform": transform,
            "validation": {
                "status": "empty",
                "is_watertight": False,
                "loose_vertices": 0,
                "loose_edges": 0,
                "boundary_edges": 0,
                "non_manifold_edges": 0,
                "normal_consistency": "not_applicable",
                "issues_found": ["mesh_is_empty"],
            },
            "message": "Mesh has no geometry data",
        }

    raw_verts = getattr(mesh_data, "vertices", [])
    if len(raw_verts) == 0:
        return {
            "name": target_obj.name,
            "type": "MESH",
            "is_mesh": True,
            "is_empty": True,
            "vertex_count": 0,
            "edge_count": 0,
            "polygon_count": 0,
            "dimensions": dims,
            "transform": transform,
            "validation": {
                "status": "empty",
                "is_watertight": False,
                "loose_vertices": 0,
                "loose_edges": 0,
                "boundary_edges": 0,
                "non_manifold_edges": 0,
                "normal_consistency": "not_applicable",
                "issues_found": ["mesh_is_empty"],
            },
            "message": "Mesh has no geometry (0 vertices)",
        }

    bmesh_module = _get_bmesh()
    if bmesh_module is not None:
        bm = bmesh_module.new()
        try:
            bm.from_mesh(mesh_data)
            v_count = len(bm.verts)
            e_count = len(bm.edges)
            p_count = len(bm.faces)

            loose_verts = sum(1 for v in bm.verts if not v.link_edges)
            loose_edges = sum(1 for e in bm.edges if not e.link_faces)
            boundary_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
            non_manifold_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2)

            if p_count < 2:
                normal_consistency = "not_applicable"
            else:
                inconsistent_count = 0
                manifold_checked = 0
                for e in bm.edges:
                    if len(e.link_loops) == 2:
                        manifold_checked += 1
                        l1, l2 = e.link_loops[0], e.link_loops[1]
                        if l1.vert == l2.vert:
                            inconsistent_count += 1
                if manifold_checked == 0:
                    normal_consistency = "not_applicable"
                elif inconsistent_count > 0:
                    normal_consistency = "inconsistent"
                else:
                    normal_consistency = "consistent"

            issues = []
            if loose_verts > 0:
                issues.append(f"{loose_verts}_loose_vertices")
            if loose_edges > 0:
                issues.append(f"{loose_edges}_loose_edges")
            if non_manifold_edges > 0:
                issues.append(f"{non_manifold_edges}_non_manifold_edges")
            if normal_consistency == "inconsistent":
                issues.append("inconsistent_normals")

            is_watertight = (
                p_count > 0
                and boundary_edges == 0
                and non_manifold_edges == 0
                and loose_verts == 0
                and loose_edges == 0
            )
            status = "clean" if len(issues) == 0 else "issues_detected"

            validation = {
                "status": status,
                "is_watertight": is_watertight,
                "loose_vertices": loose_verts,
                "loose_edges": loose_edges,
                "boundary_edges": boundary_edges,
                "non_manifold_edges": non_manifold_edges,
                "normal_consistency": normal_consistency,
                "issues_found": issues,
            }
        finally:
            bm.free()
    else:
        # Fallback when bmesh module is unavailable
        v_count = len(getattr(mesh_data, "vertices", []))
        e_count = len(getattr(mesh_data, "edges", []))
        p_count = len(getattr(mesh_data, "polygons", []))
        validation = {
            "status": "clean" if v_count > 0 else "empty",
            "is_watertight": False,
            "loose_vertices": 0,
            "loose_edges": 0,
            "boundary_edges": 0,
            "non_manifold_edges": 0,
            "normal_consistency": "unsupported",
            "issues_found": [],
        }

    return {
        "name": target_obj.name,
        "type": "MESH",
        "is_mesh": True,
        "is_empty": False,
        "vertex_count": v_count,
        "edge_count": e_count,
        "polygon_count": p_count,
        "dimensions": dims,
        "transform": transform,
        "validation": validation,
        "message": f"Mesh inspection complete ({validation['status']})",
    }


# Strictly allowlisted actions.
ACTION_HANDLERS = {
    "get_status": handle_get_status,
    "list_scene_objects": handle_list_scene_objects,
    "get_object_details": handle_get_object_details,
    "list_scene_collections": handle_list_scene_collections,
    "inspect_mesh": handle_inspect_mesh,
}



def execute_action(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatch an incoming action strictly against predefined allowlist."""
    handler = ACTION_HANDLERS.get(action)
    if not handler:
        raise ValueError(f"Action '{action}' is not supported")
    return handler(params or {})

