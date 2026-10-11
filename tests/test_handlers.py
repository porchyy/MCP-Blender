"""Tests for Blender Add-on action handlers (Ticket 3)."""
import pytest
from unittest.mock import MagicMock
import sys


def test_execute_action_disallows_arbitrary_actions():
    """Security check: execute_action rejects any unknown or arbitrary actions."""
    from blender_addon.handlers import execute_action
    
    with pytest.raises(ValueError, match="Action 'unknown_command' is not supported"):
        execute_action("unknown_command")

    with pytest.raises(ValueError, match="Action 'eval' is not supported"):
        execute_action("eval")

    with pytest.raises(ValueError, match="Action 'exec' is not supported"):
        execute_action("exec")


def test_execute_action_get_status_with_mocked_bpy():
    """execute_action('get_status') extracts Blender version, scene, and object count."""
    mock_bpy = MagicMock()
    mock_bpy.app.version_string = "5.2.2"
    mock_bpy.context.scene.name = "TestScene"
    mock_bpy.data.objects = ["Cube", "Light", "Camera"]
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("get_status")
        
        assert result["blender_version"] == "5.2.2"
        assert result["api_version"] == "1.0.0"
        assert result["scene_name"] == "TestScene"
        assert result["objects_count"] == 3
        assert "ready" in result["message"].lower()


def test_list_scene_objects_empty_scene():
    """Empty scene returns 0 objects gracefully."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "EmptyScene"
    mock_bpy.context.scene.objects = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("list_scene_objects", {"limit": 50, "offset": 0})
        assert result["scene_name"] == "EmptyScene"
        assert result["total_count"] == 0
        assert result["objects"] == []
        assert result["limit"] == 50
        assert result["offset"] == 0


def test_list_scene_objects_multiple_and_pagination():
    """Multiple objects return transforms, types, and pagination works correctly."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    def make_obj(name, obj_type, loc):
        obj = MagicMock()
        obj.name = name
        obj.type = obj_type
        obj.location = loc
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
        col = MagicMock()
        col.name = "Collection"
        obj.users_collection = [col]
        return obj

    objs = [
        make_obj("Cube", "MESH", (0.0, 0.0, 0.0)),
        make_obj("Camera", "CAMERA", (0.0, -10.0, 5.0)),
        make_obj("Light", "LIGHT", (4.0, 1.0, 5.0)),
        make_obj("Empty", "EMPTY", (0.0, 0.0, 2.0)),
    ]
    mock_bpy.context.scene.objects = objs

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        # Full query (sorted by name: Camera, Cube, Empty, Light)
        result = execute_action("list_scene_objects")
        assert result["total_count"] == 4
        assert len(result["objects"]) == 4
        assert result["objects"][0]["name"] == "Camera"
        assert result["objects"][0]["type"] == "CAMERA"
        assert result["objects"][1]["name"] == "Cube"
        assert result["objects"][1]["location"] == [0.0, 0.0, 0.0]
        assert result["objects"][1]["collections"] == ["Collection"]

        # Pagination query
        paged = execute_action("list_scene_objects", {"limit": 2, "offset": 1})
        assert paged["total_count"] == 4
        assert len(paged["objects"]) == 2
        assert paged["objects"][0]["name"] == "Cube"
        assert paged["objects"][1]["name"] == "Empty"

        # Out-of-bounds limits clamping
        clamped = execute_action("list_scene_objects", {"limit": -5, "offset": -2})
        assert clamped["limit"] == 1
        assert clamped["offset"] == 0


def test_get_object_details_found_mesh():
    """Found mesh returns detailed metrics, material slots, and dimensions."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.type = "MESH"
    mock_obj.location = (1.0, 2.0, 3.0)
    mock_obj.rotation_euler = (0.1, 0.2, 0.3)
    mock_obj.scale = (1.0, 1.0, 1.0)
    mock_obj.dimensions = (2.0, 2.0, 2.0)
    mock_obj.hide_viewport = False
    mock_obj.parent = None
    mock_obj.data.name = "CubeMesh"
    mock_obj.data.vertices = [1, 2, 3, 4, 5, 6, 7, 8]
    mock_obj.data.polygons = [1, 2, 3, 4, 5, 6]
    mock_obj.data.edges = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    mat_slot = MagicMock()
    mat_slot.material.name = "Material_Default"
    mock_obj.material_slots = [mat_slot]

    col = MagicMock()
    col.name = "MainCollection"
    mock_obj.users_collection = [col]

    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        details = execute_action("get_object_details", {"object_name": "Cube"})

        assert details["name"] == "Cube"
        assert details["type"] == "MESH"
        assert details["location"] == [1.0, 2.0, 3.0]
        assert details["dimensions"] == [2.0, 2.0, 2.0]
        assert details["visible"] is True
        assert details["data_name"] == "CubeMesh"
        assert details["material_slots"] == ["Material_Default"]
        assert details["collections"] == ["MainCollection"]
        assert details["mesh_info"]["vertex_count"] == 8
        assert details["mesh_info"]["polygon_count"] == 6
        assert details["mesh_info"]["edge_count"] == 12


def test_get_object_details_not_found():
    """Non-existent object name raises ValueError with descriptive message."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "TestScene"
    mock_bpy.context.scene.objects.get.return_value = None
    mock_bpy.data.objects.get.return_value = None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        with pytest.raises(ValueError, match="Object 'Ghost' not found in active scene 'TestScene'"):
            execute_action("get_object_details", {"object_name": "Ghost"})


def test_get_object_details_invalid_input():
    """Missing or empty object_name raises ValueError."""
    from blender_addon.handlers import execute_action
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("get_object_details", {})
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("get_object_details", {"object_name": "   "})
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("get_object_details", {"object_name": 123})


def test_list_scene_collections_nested():
    """Nested collections are properly traversed with parent relationships and object lists."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    master = MagicMock()
    master.name = "Scene Collection"
    cam = MagicMock(name="Cam")
    cam.name = "Cam"
    master.objects = [cam]

    col1 = MagicMock()
    col1.name = "Characters"
    hero = MagicMock(name="Hero")
    hero.name = "Hero"
    col1.objects = [hero]

    subcol = MagicMock()
    subcol.name = "Weapons"
    sword = MagicMock(name="Sword")
    sword.name = "Sword"
    subcol.objects = [sword]
    subcol.children = []

    col1.children = [subcol]
    master.children = [col1]

    mock_bpy.context.scene.collection = master

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("list_scene_collections")

        assert result["scene_name"] == "Scene"
        assert result["master_collection"]["name"] == "Scene Collection"
        assert result["master_collection"]["objects"] == ["Cam"]
        assert result["master_collection"]["children"] == ["Characters"]

        cols = {c["name"]: c for c in result["collections"]}
        assert "Characters" in cols
        assert cols["Characters"]["parent"] == "Scene Collection"
        assert cols["Characters"]["objects"] == ["Hero"]
        assert cols["Characters"]["children"] == ["Weapons"]

        assert "Weapons" in cols
        assert cols["Weapons"]["parent"] == "Characters"
        assert cols["Weapons"]["objects"] == ["Sword"]
        assert cols["Weapons"]["children"] == []

