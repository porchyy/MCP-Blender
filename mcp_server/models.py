"""Pydantic models for Blender Asset Prep MCP."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BlenderStatus(BaseModel):
    """Schema representing the connection state and environment of Blender."""
    connected: bool = Field(..., description="Whether Blender bridge connection is active")
    blender_version: Optional[str] = Field(None, description="Blender version string if connected")
    api_version: str = Field("1.0.0", description="Bridge API protocol version")
    scene_name: Optional[str] = Field(None, description="Current active scene name")
    objects_count: Optional[int] = Field(None, description="Total objects in the active scene")
    message: str = Field("", description="Status message or error details")


class BridgeActionRequest(BaseModel):
    """Payload sent to Blender bridge server."""
    action: str = Field(..., description="Predefined action identifier")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action arguments")


class BridgeActionResponse(BaseModel):
    """Payload returned from Blender bridge server."""
    status: str = Field(..., description="'ok' or 'error'")
    data: Dict[str, Any] = Field(default_factory=dict, description="Returned payload")
    error: Optional[str] = Field(None, description="Error message if status is error")


class ObjectSummary(BaseModel):
    """Summary of an object in the scene."""
    name: str = Field(..., description="Object name")
    type: str = Field(..., description="Object type (e.g. MESH, CAMERA, LIGHT)")
    location: list[float] = Field(..., description="Local/World location [X, Y, Z]")
    rotation_euler: list[float] = Field(..., description="Euler rotation in radians [X, Y, Z]")
    scale: list[float] = Field(..., description="Scale [X, Y, Z]")
    collections: list[str] = Field(default_factory=list, description="Collections this object belongs to")


class SceneObjectsResponse(BaseModel):
    """List of objects in the active scene with pagination."""
    scene_name: str
    total_count: int
    limit: int
    offset: int
    objects: list[ObjectSummary]


class MeshInfo(BaseModel):
    """Geometry metrics for a mesh object."""
    vertex_count: int
    polygon_count: int
    edge_count: int


class ObjectDetails(BaseModel):
    """Detailed inspection of a specific object."""
    name: str
    type: str
    location: list[float]
    rotation_euler: list[float]
    scale: list[float]
    dimensions: list[float]
    collections: list[str] = Field(default_factory=list)
    visible: bool
    parent: Optional[str] = None
    data_name: Optional[str] = None
    material_slots: list[str] = Field(default_factory=list)
    mesh_info: Optional[MeshInfo] = None


class CollectionSummary(BaseModel):
    """Summary of a scene collection."""
    name: str
    parent: Optional[str] = None
    objects: list[str] = Field(default_factory=list)
    children: list[str] = Field(default_factory=list)


class SceneCollectionsResponse(BaseModel):
    """Hierarchical list of collections in the scene."""
    scene_name: str
    master_collection: CollectionSummary
    collections: list[CollectionSummary]


class MeshValidationSummary(BaseModel):
    """Mesh topological and geometric validation summary."""
    status: str = Field(..., description="'clean', 'issues_detected', 'empty', or 'not_applicable'")
    is_watertight: bool = Field(..., description="True if mesh is closed, manifold, and has no holes or loose parts")
    loose_vertices: int = Field(0, description="Vertices not connected to any edges")
    loose_edges: int = Field(0, description="Edges not connected to any faces")
    boundary_edges: int = Field(0, description="Edges belonging to exactly one face (open borders)")
    non_manifold_edges: int = Field(0, description="Edges shared by 3 or more faces")
    normal_consistency: str = Field(..., description="'consistent', 'inconsistent', 'not_applicable', or 'unsupported'")
    issues_found: list[str] = Field(default_factory=list, description="List of detected topological issues")


class MeshInspectionResponse(BaseModel):
    """Detailed inspection and validation metrics of an object's mesh."""
    name: str = Field(..., description="Object name")
    type: str = Field(..., description="Object type (e.g. MESH, CAMERA, LIGHT)")
    is_mesh: bool = Field(..., description="Whether this object is a MESH")
    is_empty: bool = Field(False, description="Whether mesh has 0 vertices")
    vertex_count: Optional[int] = Field(None, description="Total vertices count")
    edge_count: Optional[int] = Field(None, description="Total edges count")
    polygon_count: Optional[int] = Field(None, description="Total polygons/faces count")
    dimensions: list[float] = Field(..., description="Bounding box dimensions [X, Y, Z]")
    transform: Dict[str, list[float]] = Field(..., description="Transforms: location, rotation_euler, scale")
    validation: Optional[MeshValidationSummary] = Field(None, description="Validation summary if MESH")
    message: str = Field("", description="Status notes or explanation")


