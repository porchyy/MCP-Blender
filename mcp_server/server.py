import json
from mcp.server.mcpserver import MCPServer
from mcp_server.bridge_client import BlenderBridgeClient
from mcp_server.models import (
    BlenderStatus,
    SceneObjectsResponse,
    ObjectDetails,
    SceneCollectionsResponse,
    MeshInspectionResponse,
    ApplyTransformsResponse,
    SetOriginResponse,
    CleanMeshResponse,
)

mcp = MCPServer("blender-asset-prep")


@mcp.tool()
def get_blender_status() -> str:
    """Get the current connection status, Blender version, and active scene summary.
    
    Returns a JSON string formatted according to BlenderStatus schema.
    If Blender is offline or unreachable, returns connected=false with details.
    """
    client = BlenderBridgeClient()
    status: BlenderStatus = client.get_status()
    return status.model_dump_json(indent=2)


@mcp.tool()
def list_scene_objects(limit: int = 100, offset: int = 0) -> str:
    """List all objects in the active Blender scene with transforms, types, and collections.
    
    Parameters:
    - limit: Maximum number of objects to return (1-500, default 100).
    - offset: Number of objects to skip for pagination (default 0).
    """
    client = BlenderBridgeClient()
    res = client.list_scene_objects(limit=limit, offset=offset)
    if res.status == "ok":
        try:
            parsed = SceneObjectsResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to list scene objects"}, indent=2)


@mcp.tool()
def get_object_details(object_name: str) -> str:
    """Get detailed transforms, dimensions, materials, and geometry metrics of a specific object.
    
    Parameters:
    - object_name: Exact name of the object in Blender scene.
    """
    client = BlenderBridgeClient()
    res = client.get_object_details(object_name=object_name)
    if res.status == "ok":
        try:
            parsed = ObjectDetails(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to get details for '{object_name}'"}, indent=2)


@mcp.tool()
def list_scene_collections() -> str:
    """List the collection hierarchy and object memberships in the active Blender scene."""
    client = BlenderBridgeClient()
    res = client.list_scene_collections()
    if res.status == "ok":
        try:
            parsed = SceneCollectionsResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to list collections"}, indent=2)


@mcp.tool()
def inspect_mesh(object_name: str) -> str:
    """Inspect and validate mesh geometry, topology, and normals (read-only).
    
    Parameters:
    - object_name: Exact name of the object in Blender scene.
    
    Returns metrics (vertices, edges, polygons, dimensions, transform) and validation
    status (loose vertices/edges, boundary edges, non-manifold edges, normal consistency).
    """
    client = BlenderBridgeClient()
    res = client.inspect_mesh(object_name=object_name)
    if res.status == "ok":
        try:
            parsed = MeshInspectionResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to inspect mesh for '{object_name}'"}, indent=2)


@mcp.tool()
def apply_transforms(
    object_name: str,
    location: bool = False,
    rotation: bool = True,
    scale: bool = True,
) -> str:
    """Freeze/apply transforms to an object, setting current transform values as base.
    
    Parameters:
    - object_name: Exact name of the object in Blender scene.
    - location: Whether to apply location (default False).
    - rotation: Whether to apply rotation (default True).
    - scale: Whether to apply scale (default True).
    """
    client = BlenderBridgeClient()
    res = client.apply_transforms(
        object_name=object_name,
        location=location,
        rotation=rotation,
        scale=scale,
    )
    if res.status == "ok":
        try:
            parsed = ApplyTransformsResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to apply transforms for '{object_name}'"}, indent=2)


@mcp.tool()
def set_origin_to_bottom(object_name: str) -> str:
    """Move an object's origin/pivot point to the bottom-center of its bounding box.
    
    Parameters:
    - object_name: Exact name of the mesh object in Blender scene.
    """
    client = BlenderBridgeClient()
    res = client.set_origin_to_bottom(object_name=object_name)
    if res.status == "ok":
        try:
            parsed = SetOriginResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to set origin for '{object_name}'"}, indent=2)


@mcp.tool()
def clean_mesh(
    object_name: str,
    merge_distance: float = 0.0001,
    recalculate_normals: bool = True,
) -> str:
    """Clean a mesh by merging duplicate vertices within distance and recalculating normals outward.
    
    Parameters:
    - object_name: Exact name of the mesh object in Blender scene.
    - merge_distance: Maximum distance between vertices to merge (default 0.0001).
    - recalculate_normals: Whether to recalculate face normals outward (default True).
    """
    client = BlenderBridgeClient()
    res = client.clean_mesh(
        object_name=object_name,
        merge_distance=merge_distance,
        recalculate_normals=recalculate_normals,
    )
    if res.status == "ok":
        try:
            parsed = CleanMeshResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to clean mesh for '{object_name}'"}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")



