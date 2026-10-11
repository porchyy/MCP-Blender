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
    BatchOperationResponse,
    CreatePrimitiveResponse,
    DeleteObjectResponse,
    SetObjectParentResponse,
    CreateMaterialResponse,
    AssignMaterialResponse,
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


@mcp.tool()
def batch_inspect_mesh(object_names: list[str]) -> str:
    """Inspect and validate mesh geometry and topology for multiple objects with error isolation.
    
    Parameters:
    - object_names: List of exact object names to inspect in the active Blender scene.
    """
    client = BlenderBridgeClient()
    res = client.batch_inspect_mesh(object_names=object_names)
    if res.status == "ok":
        try:
            parsed = BatchOperationResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to batch inspect meshes"}, indent=2)


@mcp.tool()
def batch_clean_mesh(
    object_names: list[str],
    merge_distance: float = 0.0001,
    recalculate_normals: bool = True,
) -> str:
    """Clean meshes for multiple objects with error isolation.
    
    Parameters:
    - object_names: List of exact object names to clean.
    - merge_distance: Maximum distance between vertices to merge (default 0.0001).
    - recalculate_normals: Whether to recalculate face normals outward (default True).
    """
    client = BlenderBridgeClient()
    res = client.batch_clean_mesh(
        object_names=object_names,
        merge_distance=merge_distance,
        recalculate_normals=recalculate_normals,
    )
    if res.status == "ok":
        try:
            parsed = BatchOperationResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to batch clean meshes"}, indent=2)


@mcp.tool()
def batch_set_origin_to_bottom(object_names: list[str]) -> str:
    """Set origin to bottom-center for multiple objects with error isolation.
    
    Parameters:
    - object_names: List of exact object names to set origin.
    """
    client = BlenderBridgeClient()
    res = client.batch_set_origin_to_bottom(object_names=object_names)
    if res.status == "ok":
        try:
            parsed = BatchOperationResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to batch set origins"}, indent=2)


@mcp.tool()
def create_primitive(
    primitive_type: str = "CUBE",
    name: str = "",
    location: list[float] = [0.0, 0.0, 0.0],
    rotation_euler: list[float] = [0.0, 0.0, 0.0],
    scale: list[float] = [1.0, 1.0, 1.0],
    dimensions: list[float] = [],
) -> str:
    """Create a 3D mesh primitive object in the active Blender scene.
    
    Parameters:
    - primitive_type: Primitive type ("CUBE", "CYLINDER", "UV_SPHERE", "PLANE").
    - name: Optional custom object name.
    - location: 3D coordinates [X, Y, Z].
    - rotation_euler: Euler rotation in radians [X, Y, Z].
    - scale: Scale factors [X, Y, Z].
    - dimensions: Optional target bounding dimensions [X, Y, Z].
    """
    client = BlenderBridgeClient()
    res = client.create_primitive(
        primitive_type=primitive_type,
        name=name if name else None,
        location=location,
        rotation_euler=rotation_euler,
        scale=scale,
        dimensions=dimensions if dimensions else None,
    )
    if res.status == "ok":
        try:
            parsed = CreatePrimitiveResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or "Failed to create primitive"}, indent=2)


@mcp.tool()
def delete_object(object_name: str) -> str:
    """Safely delete an object from the active scene.
    
    Parameters:
    - object_name: Name of the object to delete.
    """
    client = BlenderBridgeClient()
    res = client.delete_object(object_name=object_name)
    if res.status == "ok":
        try:
            parsed = DeleteObjectResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to delete object '{object_name}'"}, indent=2)


@mcp.tool()
def set_object_parent(child_name: str, parent_name: str = "", keep_transform: bool = True) -> str:
    """Set or clear a parent-child hierarchy relationship between objects.
    
    Parameters:
    - child_name: Name of the child object.
    - parent_name: Name of the parent object (leave empty to unparent).
    - keep_transform: Whether to maintain the child object's current world transform.
    """
    client = BlenderBridgeClient()
    res = client.set_object_parent(
        child_name=child_name,
        parent_name=parent_name if parent_name else None,
        keep_transform=keep_transform,
    )
    if res.status == "ok":
        try:
            parsed = SetObjectParentResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to set parent for '{child_name}'"}, indent=2)


@mcp.tool()
def create_material(
    material_name: str,
    base_color: list[float] = [0.8, 0.8, 0.8, 1.0],
    roughness: float = 0.5,
    metallic: float = 0.0,
) -> str:
    """Create or update a Principled BSDF material.
    
    Parameters:
    - material_name: Name of the material.
    - base_color: RGBA color values [R, G, B, A] from 0.0 to 1.0.
    - roughness: Surface roughness from 0.0 to 1.0.
    - metallic: Metallic factor from 0.0 to 1.0.
    """
    client = BlenderBridgeClient()
    res = client.create_material(
        material_name=material_name,
        base_color=base_color,
        roughness=roughness,
        metallic=metallic,
    )
    if res.status == "ok":
        try:
            parsed = CreateMaterialResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to create material '{material_name}'"}, indent=2)


@mcp.tool()
def assign_material(object_name: str, material_name: str, slot_index: int = 0) -> str:
    """Assign a material to a mesh object.
    
    Parameters:
    - object_name: Target object name.
    - material_name: Name of the material to assign.
    - slot_index: Material slot index (default 0).
    """
    client = BlenderBridgeClient()
    res = client.assign_material(
        object_name=object_name,
        material_name=material_name,
        slot_index=slot_index,
    )
    if res.status == "ok":
        try:
            parsed = AssignMaterialResponse(**res.data)
            return parsed.model_dump_json(indent=2)
        except Exception:
            return json.dumps(res.data, indent=2)
    return json.dumps({"status": "error", "error": res.error or f"Failed to assign material to '{object_name}'"}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")





