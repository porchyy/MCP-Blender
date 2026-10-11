"""MCP Server exposing Blender tools to Google Antigravity."""
from mcp.server.mcpserver import MCPServer
from mcp_server.bridge_client import BlenderBridgeClient
from mcp_server.models import BlenderStatus

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


if __name__ == "__main__":
    mcp.run(transport="stdio")
