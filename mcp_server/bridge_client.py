"""HTTP client for communicating with Blender local bridge."""
import httpx
from typing import Any, Dict, Optional
from mcp_server.config import BRIDGE_HOST, BRIDGE_PORT, REQUEST_TIMEOUT
from mcp_server.models import BlenderStatus, BridgeActionResponse


class BlenderBridgeClient:
    """Client communicating strictly with localhost Blender Add-on listener."""

    def __init__(
        self,
        host: str = BRIDGE_HOST,
        port: int = BRIDGE_PORT,
        timeout: float = REQUEST_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}"

    def send_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> BridgeActionResponse:
        """Send a predefined action to Blender bridge."""
        url = f"{self.base_url}/api/v1/action"
        payload = {"action": action, "params": params or {}}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return BridgeActionResponse(
                        status=data.get("status", "ok"),
                        data=data.get("data", {}),
                        error=data.get("error"),
                    )
                return BridgeActionResponse(
                    status="error",
                    error=f"HTTP {res.status_code}: {res.text}",
                )
        except httpx.ConnectError:
            return BridgeActionResponse(
                status="error",
                error=f"Blender bridge unavailable at {self.host}:{self.port} (Connection Refused)",
            )
        except httpx.TimeoutException:
            return BridgeActionResponse(
                status="error",
                error=f"Blender bridge request timed out after {self.timeout}s (timeout)",
            )
        except Exception as exc:
            return BridgeActionResponse(
                status="error",
                error=f"Bridge communication error: {str(exc)}",
            )

    def get_status(self) -> BlenderStatus:
        """Query Blender connection status and scene environment gracefully."""
        res = self.send_action("get_status")
        if res.status == "ok":
            data = res.data
            return BlenderStatus(
                connected=True,
                blender_version=data.get("blender_version"),
                api_version=data.get("api_version", "1.0.0"),
                scene_name=data.get("scene_name"),
                objects_count=data.get("objects_count"),
                message=data.get("message", "Connected to Blender"),
            )
        return BlenderStatus(
            connected=False,
            blender_version=None,
            api_version="1.0.0",
            scene_name=None,
            objects_count=None,
            message=res.error or "Failed to connect to Blender",
        )

    def list_scene_objects(self, limit: int = 100, offset: int = 0) -> BridgeActionResponse:
        """Query all objects in the active scene with pagination."""
        return self.send_action("list_scene_objects", {"limit": limit, "offset": offset})

    def get_object_details(self, object_name: str) -> BridgeActionResponse:
        """Query detailed metrics and transforms of a single object."""
        return self.send_action("get_object_details", {"object_name": object_name})

    def list_scene_collections(self) -> BridgeActionResponse:
        """Query collection hierarchy and membership in the active scene."""
        return self.send_action("list_scene_collections", {})

    def inspect_mesh(self, object_name: str) -> BridgeActionResponse:
        """Inspect and validate mesh geometry and topology for an object."""
        return self.send_action("inspect_mesh", {"object_name": object_name})

    def apply_transforms(
        self,
        object_name: str,
        location: bool = False,
        rotation: bool = True,
        scale: bool = True,
    ) -> BridgeActionResponse:
        """Freeze/apply transforms on an object."""
        return self.send_action(
            "apply_transforms",
            {
                "object_name": object_name,
                "location": location,
                "rotation": rotation,
                "scale": scale,
            },
        )

    def set_origin_to_bottom(self, object_name: str) -> BridgeActionResponse:
        """Adjust object origin/pivot to bottom-center of bounding box."""
        return self.send_action("set_origin_to_bottom", {"object_name": object_name})

    def clean_mesh(
        self,
        object_name: str,
        merge_distance: float = 0.0001,
        recalculate_normals: bool = True,
    ) -> BridgeActionResponse:
        """Merge duplicate vertices and recalculate normals."""
        return self.send_action(
            "clean_mesh",
            {
                "object_name": object_name,
                "merge_distance": merge_distance,
                "recalculate_normals": recalculate_normals,
            },
        )



