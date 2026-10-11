import json
from mcp.server.mcpserver import MCPServer
from mcp_server.bridge_client import BlenderBridgeClient
from mcp_server.models import (
    BlenderStatus,
    SceneObjectsResponse,
    ObjectDetails,
    SceneCollectionsResponse,
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


if __name__ == "__main__":
    mcp.run(transport="stdio")

