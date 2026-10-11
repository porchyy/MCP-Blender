"""Tests for BlenderBridgeClient (Ticket 2: Localhost Bridge Resilience)."""
import pytest
from unittest.mock import patch
import httpx
from mcp_server.bridge_client import BlenderBridgeClient
from mcp_server.models import BlenderStatus


def test_bridge_client_offline_returns_disconnected():
    """When Blender is offline (e.g. port closed), client returns connected=False without crashing."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9999, timeout=0.5)
    status = client.get_status()
    assert isinstance(status, BlenderStatus)
    assert status.connected is False
    assert status.blender_version is None
    assert any(term in status.message.lower() for term in ["unavailable", "failed", "timed out", "timeout"])


def test_bridge_client_timeout_returns_disconnected():
    """When request times out, client returns connected=False with timeout message."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=0.1)
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Request timed out")):
        status = client.get_status()
        assert status.connected is False
        assert "timeout" in status.message.lower()


def test_bridge_client_success_returns_status():
    """When Blender server responds successfully, client parses and returns full status."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_response = {
        "status": "ok",
        "data": {
            "blender_version": "5.2.2",
            "api_version": "1.0.0",
            "scene_name": "Scene",
            "objects_count": 3,
            "message": "Blender is ready",
        },
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_response
        status = client.get_status()
        assert status.connected is True
        assert status.blender_version == "5.2.2"
        assert status.scene_name == "Scene"
        assert status.objects_count == 3
        assert status.message == "Blender is ready"


def test_bridge_client_list_scene_objects_success():
    """Client successfully sends list_scene_objects and receives data."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_resp = {
        "status": "ok",
        "data": {
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
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_resp
        res = client.list_scene_objects(limit=50, offset=0)
        assert res.status == "ok"
        assert res.data["scene_name"] == "Scene"
        assert len(res.data["objects"]) == 1


def test_bridge_client_get_object_details_success():
    """Client successfully sends get_object_details and receives object data."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_resp = {
        "status": "ok",
        "data": {
            "name": "Cube",
            "type": "MESH",
            "location": [0.0, 0.0, 0.0],
            "rotation_euler": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "dimensions": [2.0, 2.0, 2.0],
            "collections": ["Collection"],
            "visible": True,
            "parent": None,
            "data_name": "Cube",
            "material_slots": [],
            "mesh_info": {"vertex_count": 8, "polygon_count": 6, "edge_count": 12},
        },
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_resp
        res = client.get_object_details("Cube")
        assert res.status == "ok"
        assert res.data["name"] == "Cube"
        assert res.data["mesh_info"]["vertex_count"] == 8


def test_bridge_client_list_scene_collections_success():
    """Client successfully sends list_scene_collections and receives hierarchy."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_resp = {
        "status": "ok",
        "data": {
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
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_resp
        res = client.list_scene_collections()
        assert res.status == "ok"
        assert res.data["master_collection"]["name"] == "Scene Collection"
        assert len(res.data["collections"]) == 1


def test_bridge_client_inspect_mesh_success():
    """Client successfully sends inspect_mesh and receives validation data."""
    client = BlenderBridgeClient(host="127.0.0.1", port=9876, timeout=1.0)
    fake_resp = {
        "status": "ok",
        "data": {
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
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = fake_resp
        res = client.inspect_mesh("Cube")
        assert res.status == "ok"
        assert res.data["name"] == "Cube"
        assert res.data["validation"]["is_watertight"] is True


