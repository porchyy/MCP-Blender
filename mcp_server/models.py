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

