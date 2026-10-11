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


def test_inspect_mesh_valid_watertight():
    """Valid watertight mesh reports clean status, 0 issues, and consistent normals."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.type = "MESH"
    mock_obj.location = (0.0, 0.0, 0.0)
    mock_obj.rotation_euler = (0.0, 0.0, 0.0)
    mock_obj.scale = (1.0, 1.0, 1.0)
    mock_obj.dimensions = (2.0, 2.0, 2.0)
    mock_obj.data.vertices = [1, 2, 3, 4, 5, 6, 7, 8]
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    # Mock BMesh
    mock_bmesh = MagicMock()
    mock_bm = MagicMock()
    mock_bmesh.new.return_value = mock_bm

    # 8 vertices, all connected
    mock_verts = [MagicMock(link_edges=[1, 2]) for _ in range(8)]
    mock_bm.verts = mock_verts

    # 6 faces
    mock_faces = [MagicMock() for _ in range(6)]
    mock_bm.faces = mock_faces

    # 12 manifold edges with consistent winding
    mock_edges = []
    for _ in range(12):
        edge = MagicMock()
        edge.link_faces = [1, 2]
        l1 = MagicMock(vert=1)
        l2 = MagicMock(vert=2)  # different vert -> consistent
        edge.link_loops = [l1, l2]
        mock_edges.append(edge)
    mock_bm.edges = mock_edges

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "bmesh", mock_bmesh)
        from blender_addon.handlers import execute_action
        result = execute_action("inspect_mesh", {"object_name": "Cube"})

        assert result["name"] == "Cube"
        assert result["type"] == "MESH"
        assert result["is_mesh"] is True
        assert result["is_empty"] is False
        assert result["vertex_count"] == 8
        assert result["polygon_count"] == 6
        assert result["edge_count"] == 12
        assert result["dimensions"] == [2.0, 2.0, 2.0]
        assert result["validation"]["status"] == "clean"
        assert result["validation"]["is_watertight"] is True
        assert result["validation"]["loose_vertices"] == 0
        assert result["validation"]["loose_edges"] == 0
        assert result["validation"]["boundary_edges"] == 0
        assert result["validation"]["non_manifold_edges"] == 0
        assert result["validation"]["normal_consistency"] == "consistent"
        assert result["validation"]["issues_found"] == []
        assert mock_bm.free.called


def test_inspect_mesh_with_topology_issues():
    """Mesh with loose parts, non-manifold edges, and flipped normals is flagged."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    mock_obj = MagicMock()
    mock_obj.name = "BadMesh"
    mock_obj.type = "MESH"
    mock_obj.location = (0.0, 0.0, 0.0)
    mock_obj.rotation_euler = (0.0, 0.0, 0.0)
    mock_obj.scale = (1.0, 1.0, 1.0)
    mock_obj.dimensions = (1.0, 1.0, 1.0)
    mock_obj.data.vertices = [1, 2, 3]
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "BadMesh" else None

    mock_bmesh = MagicMock()
    mock_bm = MagicMock()
    mock_bmesh.new.return_value = mock_bm

    # 1 connected vert, 1 loose vert
    mock_bm.verts = [MagicMock(link_edges=[1]), MagicMock(link_edges=[])]
    mock_bm.faces = [MagicMock(), MagicMock()]

    # 1 loose edge, 1 boundary edge, 1 non-manifold edge, 1 flipped normal edge
    e_loose = MagicMock(link_faces=[], link_loops=[])
    e_boundary = MagicMock(link_faces=[1], link_loops=[MagicMock()])
    e_non_manifold = MagicMock(link_faces=[1, 2, 3], link_loops=[1, 2, 3])
    # flipped normal: loop1.vert == loop2.vert
    e_flipped = MagicMock(link_faces=[1, 2], link_loops=[MagicMock(vert=1), MagicMock(vert=1)])

    mock_bm.edges = [e_loose, e_boundary, e_non_manifold, e_flipped]

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "bmesh", mock_bmesh)
        from blender_addon.handlers import execute_action
        result = execute_action("inspect_mesh", {"object_name": "BadMesh"})

        assert result["validation"]["status"] == "issues_detected"
        assert result["validation"]["is_watertight"] is False
        assert result["validation"]["loose_vertices"] == 1
        assert result["validation"]["loose_edges"] == 1
        assert result["validation"]["boundary_edges"] == 1
        assert result["validation"]["non_manifold_edges"] == 1
        assert result["validation"]["normal_consistency"] == "inconsistent"
        assert "1_loose_vertices" in result["validation"]["issues_found"]
        assert "1_loose_edges" in result["validation"]["issues_found"]
        assert "1_non_manifold_edges" in result["validation"]["issues_found"]
        assert "inconsistent_normals" in result["validation"]["issues_found"]


def test_inspect_mesh_empty_geometry():
    """Empty mesh with 0 vertices reports empty status without crashing."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    mock_obj = MagicMock()
    mock_obj.name = "EmptyMesh"
    mock_obj.type = "MESH"
    mock_obj.location = (0.0, 0.0, 0.0)
    mock_obj.rotation_euler = (0.0, 0.0, 0.0)
    mock_obj.scale = (1.0, 1.0, 1.0)
    mock_obj.dimensions = (0.0, 0.0, 0.0)
    mock_obj.data.vertices = []
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "EmptyMesh" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("inspect_mesh", {"object_name": "EmptyMesh"})

        assert result["is_mesh"] is True
        assert result["is_empty"] is True
        assert result["vertex_count"] == 0
        assert result["validation"]["status"] == "empty"
        assert result["validation"]["normal_consistency"] == "not_applicable"
        assert "mesh_is_empty" in result["validation"]["issues_found"]


def test_inspect_mesh_non_mesh_object():
    """Non-mesh object (e.g. Camera) reports is_mesh=False and not_applicable."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    mock_obj = MagicMock()
    mock_obj.name = "Camera"
    mock_obj.type = "CAMERA"
    mock_obj.location = (0.0, -10.0, 5.0)
    mock_obj.rotation_euler = (1.1, 0.0, 0.8)
    mock_obj.scale = (1.0, 1.0, 1.0)
    mock_obj.dimensions = (0.0, 0.0, 0.0)
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Camera" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("inspect_mesh", {"object_name": "Camera"})

        assert result["name"] == "Camera"
        assert result["type"] == "CAMERA"
        assert result["is_mesh"] is False
        assert result["validation"] is None
        assert "not a MESH" in result["message"]


def test_inspect_mesh_not_found():
    """Missing object raises ValueError."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"
    mock_bpy.context.scene.objects.get.return_value = None
    mock_bpy.data.objects.get.return_value = None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        with pytest.raises(ValueError, match="Object 'Ghost' not found in active scene 'Scene'"):
            execute_action("inspect_mesh", {"object_name": "Ghost"})


def test_inspect_mesh_invalid_input():
    """Malformed or missing object_name raises ValueError."""
    from blender_addon.handlers import execute_action
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("inspect_mesh", {})
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("inspect_mesh", {"object_name": "   "})
    with pytest.raises(ValueError, match="Parameter 'object_name' is required"):
        execute_action("inspect_mesh", {"object_name": 123})
    with pytest.raises(ValueError, match="exceeds maximum length"):
        execute_action("inspect_mesh", {"object_name": "a" * 257})


def test_apply_transforms_success():
    """Applying transforms invokes bpy operator on active object."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"
    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.location = [1.0, 2.0, 3.0]
    mock_obj.rotation_euler = [0.5, 0.5, 0.5]
    mock_obj.scale = [2.0, 2.0, 2.0]
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("apply_transforms", {"object_name": "Cube", "rotation": True, "scale": True, "location": False})

        assert result["name"] == "Cube"
        assert result["applied"]["rotation"] is True
        assert result["applied"]["scale"] is True
        assert result["applied"]["location"] is False
        assert mock_bpy.ops.object.transform_apply.called


def test_apply_transforms_no_channels_error():
    """Error raised when no transform channel is selected."""
    from blender_addon.handlers import execute_action
    with pytest.raises(ValueError, match="At least one transform channel"):
        execute_action("apply_transforms", {"object_name": "Cube", "location": False, "rotation": False, "scale": False})


def test_set_origin_to_bottom_success():
    """Origin is calculated to bottom center of bounding box."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"
    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.type = "MESH"
    mock_obj.location = [0.0, 0.0, 0.0]
    mock_obj.bound_box = [
        [-1.0, -1.0, -1.0],
        [1.0, -1.0, -1.0],
        [1.0, 1.0, -1.0],
        [-1.0, 1.0, -1.0],
        [-1.0, -1.0, 1.0],
        [1.0, -1.0, 1.0],
        [1.0, 1.0, 1.0],
        [-1.0, 1.0, 1.0],
    ]
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        result = execute_action("set_origin_to_bottom", {"object_name": "Cube"})

        assert result["name"] == "Cube"
        assert result["origin_type"] == "BOTTOM_CENTER"
        assert result["delta_applied"] == [0.0, 0.0, -1.0]


def test_set_origin_to_bottom_non_mesh_error():
    """Non-mesh object raises ValueError."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"
    mock_obj = MagicMock()
    mock_obj.name = "Camera"
    mock_obj.type = "CAMERA"
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Camera" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action
        with pytest.raises(ValueError, match="requires a MESH"):
            execute_action("set_origin_to_bottom", {"object_name": "Camera"})


def test_clean_mesh_success():
    """Clean mesh merges duplicates and recalculates normals."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"
    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.type = "MESH"
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    mock_bmesh = MagicMock()
    mock_bm = MagicMock()
    mock_bm.verts = [1] * 10
    mock_bm.faces = [1, 2, 3, 4, 5, 6]

    def remove_doubles_side_effect(bm, verts=None, dist=0.0):
        mock_bm.verts = [1] * 8

    mock_bmesh.ops.remove_doubles.side_effect = remove_doubles_side_effect
    mock_bmesh.new.return_value = mock_bm

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "bmesh", mock_bmesh)
        from blender_addon.handlers import execute_action
        result = execute_action("clean_mesh", {"object_name": "Cube", "merge_distance": 0.001, "recalculate_normals": True})

        assert result["name"] == "Cube"
        assert result["verts_before"] == 10
        assert result["verts_after"] == 8
        assert result["merged_vertices"] == 2
        assert result["normals_recalculated"] is True
        assert mock_bm.to_mesh.called
        assert mock_bm.free.called


def test_reload_addon():
    """Reload addon returns reloaded status."""
    from blender_addon.handlers import execute_action
    res = execute_action("reload_addon")
    assert res["status"] == "reloaded"


def test_set_origin_to_bottom_world_space_invariance():
    """Verify that world-space vertex positions remain invariant when origin moves to bottom."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    initial_local_verts = [
        [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0], [1.0, 1.0, -1.0], [-1.0, 1.0, -1.0],
        [-1.0, -1.0, 1.0], [1.0, -1.0, 1.0], [1.0, 1.0, 1.0], [-1.0, 1.0, 1.0]
    ]
    current_verts = [list(v) for v in initial_local_verts]

    mock_obj = MagicMock()
    mock_obj.name = "Cube"
    mock_obj.type = "MESH"
    mock_obj.location = [0.0, 0.0, 0.0]
    mock_obj.bound_box = [list(v) for v in initial_local_verts]
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Cube" else None

    class FakeVector(list):
        def __init__(self, seq):
            super().__init__(seq)
            self.x, self.y, self.z = seq[0], seq[1], seq[2]
        def __getitem__(self, idx):
            return super().__getitem__(idx)
        def __neg__(self):
            return FakeVector([-x for x in self])

    class FakeMatrix:
        def __init__(self, translation_vec):
            self.translation_vec = translation_vec
        @staticmethod
        def Translation(vec):
            return FakeMatrix(vec)
        def to_3x3(self):
            return self
        def __matmul__(self, other):
            return list(other)

    def fake_transform(mat):
        for v in current_verts:
            v[0] += mat.translation_vec[0]
            v[1] += mat.translation_vec[1]
            v[2] += mat.translation_vec[2]

    def fake_loc_add(delta):
        mock_obj.location[0] += delta[0]
        mock_obj.location[1] += delta[1]
        mock_obj.location[2] += delta[2]

    mock_obj.data.transform.side_effect = fake_transform
    mock_obj.matrix_world = FakeMatrix([0, 0, 0])

    # Allow += on mock_obj.location
    class LocWrapper(list):
        def __iadd__(self, other):
            self[0] += other[0]
            self[1] += other[1]
            self[2] += other[2]
            return self

    mock_obj.location = LocWrapper([0.0, 0.0, 0.0])

    mock_mathutils = MagicMock()
    mock_mathutils.Vector = FakeVector
    mock_mathutils.Matrix = FakeMatrix

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "mathutils", mock_mathutils)
        from blender_addon.handlers import execute_action

        world_verts_before = [[mock_obj.location[i] + v[i] for i in range(3)] for v in current_verts]
        res = execute_action("set_origin_to_bottom", {"object_name": "Cube"})

        assert res["location_before"] == [0.0, 0.0, 0.0]
        assert res["location_after"] == [0.0, 0.0, -1.0]

        world_verts_after = [[round(mock_obj.location[i] + v[i], 5) for i in range(3)] for v in current_verts]
        # World space vertex positions are 100% invariant
        assert world_verts_after == world_verts_before


def test_batch_inspect_mesh_with_error_isolation():
    """Batch inspect isolates errors and returns per-object PASS/FAIL validation report."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    cube = MagicMock()
    cube.name = "Cube"
    cube.type = "MESH"
    cube.location = (0.0, 0.0, 0.0)
    cube.rotation_euler = (0.0, 0.0, 0.0)
    cube.scale = (1.0, 1.0, 1.0)
    cube.dimensions = (2.0, 2.0, 2.0)
    cube.data.vertices = [1, 2, 3]

    cam = MagicMock()
    cam.name = "Camera"
    cam.type = "CAMERA"
    cam.location = (0.0, -10.0, 5.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    cam.scale = (1.0, 1.0, 1.0)
    cam.dimensions = (0.0, 0.0, 0.0)

    objects_map = {"Cube": cube, "Camera": cam}
    mock_bpy.context.scene.objects.get.side_effect = lambda n: objects_map.get(n)
    mock_bpy.data.objects.get.side_effect = lambda n: objects_map.get(n)

    mock_bmesh = MagicMock()
    mock_bm = MagicMock()
    mock_bm.verts = [MagicMock(link_edges=[1])] * 3
    mock_bm.edges = []
    mock_bm.faces = []
    mock_bmesh.new.return_value = mock_bm

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "bmesh", mock_bmesh)
        from blender_addon.handlers import execute_action

        res = execute_action("batch_inspect_mesh", {"object_names": ["Cube", "Ghost", "Camera"]})

        assert res["total"] == 3
        assert res["passed"] == 2
        assert res["failed"] == 1
        assert res["results"][0]["name"] == "Cube"
        assert res["results"][0]["status"] == "PASS"
        assert res["results"][1]["name"] == "Ghost"
        assert res["results"][1]["status"] == "FAIL"
        assert "not found" in res["results"][1]["error"]
        assert res["results"][2]["name"] == "Camera"
        assert res["results"][2]["status"] == "PASS"
        assert res["results"][2]["data"]["is_mesh"] is False


def test_batch_clean_mesh_with_error_isolation():
    """Batch clean continues processing remaining objects when one object fails."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    cube = MagicMock()
    cube.name = "Cube"
    cube.type = "MESH"

    cam = MagicMock()
    cam.name = "Camera"
    cam.type = "CAMERA"

    objects_map = {"Cube": cube, "Camera": cam}
    mock_bpy.context.scene.objects.get.side_effect = lambda n: objects_map.get(n)

    mock_bmesh = MagicMock()
    mock_bm = MagicMock()
    mock_bm.verts = [1] * 8
    mock_bm.faces = []
    mock_bmesh.new.return_value = mock_bm

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        mp.setitem(sys.modules, "bmesh", mock_bmesh)
        from blender_addon.handlers import execute_action

        res = execute_action("batch_clean_mesh", {"object_names": ["Camera", "Cube"]})

        assert res["total"] == 2
        assert res["passed"] == 1
        assert res["failed"] == 1
        assert res["results"][0]["name"] == "Camera"
        assert res["results"][0]["status"] == "FAIL"
        assert "requires a MESH" in res["results"][0]["error"]
        assert res["results"][1]["name"] == "Cube"
        assert res["results"][1]["status"] == "PASS"


def test_batch_set_origin_to_bottom_with_error_isolation():
    """Batch set origin isolates missing object errors."""
    mock_bpy = MagicMock()
    mock_bpy.context.scene.name = "Scene"

    cube = MagicMock()
    cube.name = "Cube"
    cube.type = "MESH"
    cube.location = [0.0, 0.0, 0.0]
    cube.bound_box = [[-1, -1, -1], [1, 1, 1]]

    mock_bpy.context.scene.objects.get.side_effect = lambda n: cube if n == "Cube" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        res = execute_action("batch_set_origin_to_bottom", {"object_names": ["Cube", "Ghost"]})

        assert res["total"] == 2
        assert res["passed"] == 1
        assert res["failed"] == 1
        assert res["results"][0]["status"] == "PASS"
        assert res["results"][1]["status"] == "FAIL"


def test_batch_operations_input_validation():
    """Batch operations validate inputs, empty lists, and enforce size limits."""
    from blender_addon.handlers import execute_action

    # Missing or empty object_names
    with pytest.raises(ValueError, match="Parameter 'object_names' is required"):
        execute_action("batch_inspect_mesh", {})
    with pytest.raises(ValueError, match="non-empty list"):
        execute_action("batch_inspect_mesh", {"object_names": []})
    with pytest.raises(ValueError, match="non-empty list"):
        execute_action("batch_inspect_mesh", {"object_names": "not-a-list"})

    # Exceeding batch limit
    too_many = [f"Obj{i}" for i in range(101)]
    with pytest.raises(ValueError, match="Batch size exceeds maximum limit of 100"):
        execute_action("batch_inspect_mesh", {"object_names": too_many})


def test_create_primitive_success_and_invalid_type():
    """Create primitive adds object via ops.mesh and configures transforms."""
    mock_bpy = MagicMock()
    mock_active = MagicMock()
    mock_active.name = "CustomBox"
    mock_active.location = (1.0, 2.0, 3.0)
    mock_active.rotation_euler = (0.0, 0.0, 0.0)
    mock_active.scale = (1.0, 1.0, 1.0)
    mock_active.dimensions = (2.0, 2.0, 2.0)
    mock_bpy.context.active_object = mock_active

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        res = execute_action("create_primitive", {
            "primitive_type": "CUBE",
            "name": "CustomBox",
            "location": [1.0, 2.0, 3.0]
        })
        assert res["name"] == "CustomBox"
        assert res["primitive_type"] == "CUBE"
        assert mock_bpy.ops.mesh.primitive_cube_add.called

        # Test invalid type raises ValueError
        with pytest.raises(ValueError, match="Unsupported primitive type"):
            execute_action("create_primitive", {"primitive_type": "DONUT"})


def test_delete_object_success_and_not_found():
    """Delete object removes target from bpy.data.objects."""
    mock_bpy = MagicMock()
    mock_obj = MagicMock()
    mock_obj.name = "TrashCube"
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "TrashCube" else None
    mock_bpy.data.objects.get.side_effect = lambda n: mock_obj if n == "TrashCube" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        res = execute_action("delete_object", {"object_name": "TrashCube"})
        assert res["name"] == "TrashCube"
        assert res["deleted"] is True
        assert mock_bpy.data.objects.remove.called

        # Test missing object
        with pytest.raises(ValueError, match="Object 'Ghost' not found"):
            execute_action("delete_object", {"object_name": "Ghost"})


def test_set_object_parent_success_and_errors():
    """Parenting links child to parent, supports unparenting and prevents self-parenting."""
    mock_bpy = MagicMock()
    child = MagicMock(name="Child")
    child.name = "Child"
    parent = MagicMock(name="Parent")
    parent.name = "Parent"

    objects_map = {"Child": child, "Parent": parent}
    mock_bpy.context.scene.objects.get.side_effect = lambda n: objects_map.get(n)

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        # Set parent
        res = execute_action("set_object_parent", {"child_name": "Child", "parent_name": "Parent"})
        assert res["child_name"] == "Child"
        assert res["parent_name"] == "Parent"
        assert child.parent == parent

        # Unparent
        res_un = execute_action("set_object_parent", {"child_name": "Child", "parent_name": ""})
        assert res_un["parent_name"] is None
        assert child.parent is None

        # Self-parent error
        with pytest.raises(ValueError, match="cannot be parented to itself"):
            execute_action("set_object_parent", {"child_name": "Child", "parent_name": "Child"})


def test_create_material_and_assign_material():
    """Create material configures Principled BSDF nodes and assign material attaches to mesh."""
    mock_bpy = MagicMock()
    mock_mat = MagicMock()
    mock_mat.name = "WoodMat"
    mock_node = MagicMock()

    base_color_input = MagicMock()
    roughness_input = MagicMock()
    metallic_input = MagicMock()
    inputs_dict = {
        "Base Color": base_color_input,
        "Roughness": roughness_input,
        "Metallic": metallic_input,
    }
    mock_node.inputs.__contains__.side_effect = lambda k: k in inputs_dict
    mock_node.inputs.__getitem__.side_effect = lambda k: inputs_dict[k]

    mock_mat.node_tree.nodes.get.return_value = mock_node
    mock_bpy.data.materials.get.return_value = None
    mock_bpy.data.materials.new.return_value = mock_mat

    mock_obj = MagicMock()
    mock_obj.name = "Chest"
    mock_obj.data.materials = []
    mock_bpy.context.scene.objects.get.side_effect = lambda n: mock_obj if n == "Chest" else None

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "bpy", mock_bpy)
        from blender_addon.handlers import execute_action

        # Create Material
        mat_res = execute_action("create_material", {
            "material_name": "WoodMat",
            "base_color": [0.6, 0.3, 0.1, 1.0],
            "roughness": 0.8,
            "metallic": 0.1
        })
        assert mat_res["material_name"] == "WoodMat"
        assert mat_res["roughness"] == 0.8
        assert base_color_input.default_value == (0.6, 0.3, 0.1, 1.0)
        assert roughness_input.default_value == 0.8
        assert metallic_input.default_value == 0.1

        # Assign Material
        mock_bpy.data.materials.get.side_effect = lambda n: mock_mat if n == "WoodMat" else None
        assign_res = execute_action("assign_material", {
            "object_name": "Chest",
            "material_name": "WoodMat"
        })
        assert assign_res["object_name"] == "Chest"
        assert assign_res["material_name"] == "WoodMat"
        assert len(mock_obj.data.materials) == 1







