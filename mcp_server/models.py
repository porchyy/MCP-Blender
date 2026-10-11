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
