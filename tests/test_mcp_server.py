"""Tests for MCP Server tool registration and execution (Ticket 3)."""
import json
from unittest.mock import patch
from mcp_server.server import get_blender_status
from mcp_server.models import BlenderStatus


def test_get_blender_status_tool_offline():
    """Tool execution when Blender is offline produces valid JSON BlenderStatus."""
    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_status") as mock_get_status:
        mock_get_status.return_value = BlenderStatus(
            connected=False,
            blender_version=None,
            api_version="1.0.0",
            scene_name=None,
            objects_count=None,
            message="Bridge unavailable",
        )
        res_json = get_blender_status()
        assert isinstance(res_json, str)
        parsed = json.loads(res_json)
        assert parsed["connected"] is False
        assert parsed["blender_version"] is None
        assert "Bridge unavailable" in parsed["message"]


def test_get_blender_status_tool_online():
    """Tool execution when Blender is online produces valid JSON BlenderStatus."""
    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_status") as mock_get_status:
        mock_get_status.return_value = BlenderStatus(
            connected=True,
            blender_version="5.2.2",
            api_version="1.0.0",
            scene_name="MainScene",
            objects_count=5,
            message="Blender is ready",
        )
        res_json = get_blender_status()
        parsed = json.loads(res_json)
        assert parsed["connected"] is True
        assert parsed["blender_version"] == "5.2.2"
        assert parsed["scene_name"] == "MainScene"
        assert parsed["objects_count"] == 5


def test_list_scene_objects_tool_offline():
    """Tool returns error json when bridge is offline."""
    from mcp_server.server import list_scene_objects
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.list_scene_objects") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="error",
            error="Blender bridge unavailable at 127.0.0.1:9876",
        )
        res_json = list_scene_objects()
        parsed = json.loads(res_json)
        assert parsed["status"] == "error"
        assert "unavailable" in parsed["error"]


def test_list_scene_objects_tool_online():
    """Tool returns serialized SceneObjectsResponse when bridge is online."""
    from mcp_server.server import list_scene_objects
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.list_scene_objects") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "scene_name": "Scene",
                "total_count": 1,
                "limit": 100,
                "offset": 0,
                "objects": [
                    {
                        "name": "Cube",
                        "type": "MESH",
                        "location": [0.0, 0.0, 0.0],
                        "rotation_euler": [0.0, 0.0, 0.0],
                        "scale": [1.0, 1.0, 1.0],
                        "collections": ["Collection"],
                    }
                ],
            },
        )
        res_json = list_scene_objects()
        parsed = json.loads(res_json)
        assert parsed["scene_name"] == "Scene"
        assert parsed["total_count"] == 1
        assert parsed["objects"][0]["name"] == "Cube"


def test_get_object_details_tool_not_found():
    """Tool returns error json when object does not exist."""
    from mcp_server.server import get_object_details
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_object_details") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="error",
            error="Object 'NonExistent' not found in active scene 'Scene'",
        )
        res_json = get_object_details("NonExistent")
        parsed = json.loads(res_json)
        assert parsed["status"] == "error"
        assert "not found" in parsed["error"]


def test_get_object_details_tool_found():
    """Tool returns detailed object properties when object exists."""
    from mcp_server.server import get_object_details
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.get_object_details") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "name": "Cube",
                "type": "MESH",
                "location": [1.0, 2.0, 3.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "dimensions": [2.0, 2.0, 2.0],
                "collections": ["Collection"],
                "visible": True,
                "parent": None,
                "data_name": "Cube",
                "material_slots": ["Mat"],
                "mesh_info": {"vertex_count": 8, "polygon_count": 6, "edge_count": 12},
            },
        )
        res_json = get_object_details("Cube")
        parsed = json.loads(res_json)
        assert parsed["name"] == "Cube"
        assert parsed["mesh_info"]["vertex_count"] == 8


def test_list_scene_collections_tool():
    """Tool returns collection hierarchy JSON."""
    from mcp_server.server import list_scene_collections
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.list_scene_collections") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "scene_name": "Scene",
                "master_collection": {
                    "name": "Scene Collection",
                    "parent": None,
                    "objects": ["Cam"],
                    "children": ["Collection"],
                },
                "collections": [
                    {
                        "name": "Collection",
                        "parent": "Scene Collection",
                        "objects": ["Cube"],
                        "children": [],
                    }
                ],
            },
        )
        res_json = list_scene_collections()
        parsed = json.loads(res_json)
        assert parsed["scene_name"] == "Scene"
        assert parsed["master_collection"]["name"] == "Scene Collection"
        assert len(parsed["collections"]) == 1


def test_inspect_mesh_tool_online():
    """Tool returns serialized MeshInspectionResponse when online."""
    from mcp_server.server import inspect_mesh
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.inspect_mesh") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "name": "Cube",
                "type": "MESH",
                "is_mesh": True,
                "is_empty": False,
                "vertex_count": 8,
                "edge_count": 12,
                "polygon_count": 6,
                "dimensions": [2.0, 2.0, 2.0],
                "transform": {
                    "location": [0.0, 0.0, 0.0],
                    "rotation_euler": [0.0, 0.0, 0.0],
                    "scale": [1.0, 1.0, 1.0],
                },
                "validation": {
                    "status": "clean",
                    "is_watertight": True,
                    "loose_vertices": 0,
                    "loose_edges": 0,
                    "boundary_edges": 0,
                    "non_manifold_edges": 0,
                    "normal_consistency": "consistent",
                    "issues_found": [],
                },
                "message": "Mesh inspection complete (clean)",
            },
        )
        res_json = inspect_mesh("Cube")
        parsed = json.loads(res_json)
        assert parsed["name"] == "Cube"
        assert parsed["validation"]["status"] == "clean"
        assert parsed["validation"]["is_watertight"] is True


def test_inspect_mesh_tool_offline():
    """Tool returns error json when bridge is offline."""
    from mcp_server.server import inspect_mesh
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.inspect_mesh") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="error",
            error="Blender bridge unavailable at 127.0.0.1:9876",
        )
        res_json = inspect_mesh("Cube")
        parsed = json.loads(res_json)
        assert parsed["status"] == "error"
        assert "unavailable" in parsed["error"]


def test_apply_transforms_tool():
    """Tool returns ApplyTransformsResponse when online."""
    from mcp_server.server import apply_transforms
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.apply_transforms") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "name": "Cube",
                "applied": {"location": False, "rotation": True, "scale": True},
                "transforms_before": {"scale": [2.0, 2.0, 2.0]},
                "transforms_after": {"scale": [1.0, 1.0, 1.0]},
                "message": "Transforms applied successfully",
            },
        )
        res_json = apply_transforms("Cube", rotation=True, scale=True)
        parsed = json.loads(res_json)
        assert parsed["name"] == "Cube"
        assert parsed["applied"]["rotation"] is True


def test_set_origin_to_bottom_tool():
    """Tool returns SetOriginResponse when online."""
    from mcp_server.server import set_origin_to_bottom
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.set_origin_to_bottom") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "name": "Cube",
                "origin_type": "BOTTOM_CENTER",
                "delta_applied": [0.0, 0.0, -1.0],
                "location_before": [0.0, 0.0, 0.0],
                "location_after": [0.0, 0.0, -1.0],
                "message": "Origin set successfully",
            },
        )
        res_json = set_origin_to_bottom("Cube")
        parsed = json.loads(res_json)
        assert parsed["name"] == "Cube"
        assert parsed["origin_type"] == "BOTTOM_CENTER"


def test_clean_mesh_tool():
    """Tool returns CleanMeshResponse when online."""
    from mcp_server.server import clean_mesh
    from mcp_server.models import BridgeActionResponse

    with patch("mcp_server.bridge_client.BlenderBridgeClient.clean_mesh") as mock_call:
        mock_call.return_value = BridgeActionResponse(
            status="ok",
            data={
                "name": "Cube",
                "verts_before": 10,
                "verts_after": 8,
                "merged_vertices": 2,
                "normals_recalculated": True,
                "message": "Cleaned mesh",
            },
        )
        res_json = clean_mesh("Cube", merge_distance=0.001, recalculate_normals=True)
        parsed = json.loads(res_json)
        assert parsed["name"] == "Cube"
        assert parsed["merged_vertices"] == 2



