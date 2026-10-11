"""Blender 3D Viewport sidebar UI panel and operators for MCP Bridge."""
import sys
try:
    from .bridge_server import start_server, stop_server, is_server_running, get_server_port
except ImportError:
    from blender_addon.bridge_server import start_server, stop_server, is_server_running, get_server_port

try:
    import bpy  # type: ignore
    from bpy.types import Operator, Panel  # type: ignore
except ImportError:
    bpy = None
    Operator = object
    Panel = object


class OBJECT_OT_blender_mcp_start(Operator):
    """Start the Asset Prep MCP bridge server on localhost."""
    bl_idname = "object.blender_mcp_start"
    bl_label = "Start Bridge Server"
    bl_description = "Starts the local MCP bridge server on 127.0.0.1:9876"

    def execute(self, context):
        try:
            start_server()
            self.report({"INFO"}, "Asset Prep MCP Bridge started on 127.0.0.1:9876")
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to start bridge: {str(exc)}")
            return {"CANCELLED"}
        return {"FINISHED"}


class OBJECT_OT_blender_mcp_stop(Operator):
    """Stop the Asset Prep MCP bridge server."""
    bl_idname = "object.blender_mcp_stop"
    bl_label = "Stop Bridge Server"
    bl_description = "Stops the local MCP bridge server"

    def execute(self, context):
        try:
            stop_server()
            self.report({"INFO"}, "Asset Prep MCP Bridge stopped")
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to stop bridge: {str(exc)}")
            return {"CANCELLED"}
        return {"FINISHED"}


class VIEW3D_PT_blender_mcp_panel(Panel):
    """Sidebar Panel for controlling the Asset Prep MCP Bridge."""
    bl_label = "Asset Prep MCP"
    bl_idname = "VIEW3D_PT_blender_mcp_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Asset Prep MCP"

    def draw(self, context):
        layout = self.layout
        running = is_server_running()

        col = layout.column(align=True)
        if running:
            port = get_server_port() or 9876
            col.label(text=f"Status: Active (127.0.0.1:{port})", icon="CHECKMARK")
            col.operator("object.blender_mcp_stop", icon="CANCEL", text="Stop Server")
        else:
            col.label(text="Status: Offline", icon="X")
            col.operator("object.blender_mcp_start", icon="PLAY", text="Start Server")


CLASSES = [
    OBJECT_OT_blender_mcp_start,
    OBJECT_OT_blender_mcp_stop,
    VIEW3D_PT_blender_mcp_panel,
]


def register_ui():
    """Register UI classes in Blender."""
    if bpy is not None:
        for cls in CLASSES:
            try:
                bpy.utils.register_class(cls)
            except Exception:
                pass


def unregister_ui():
    """Unregister UI classes in Blender."""
    if bpy is not None:
        for cls in reversed(CLASSES):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
