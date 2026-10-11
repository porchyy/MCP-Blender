"""Live end-to-end integration test verifying MCP Server over standard input/output (stdio)."""
import json
import subprocess
import sys


def test_mcp_server_stdio_initialization_and_tool_call():
    """Verify that the MCP server starts via stdio, handles initialize, lists tools, and calls get_blender_status."""
    python_exe = sys.executable

    # Spawn MCP server subprocess
    proc = subprocess.Popen(
        [python_exe, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # 1. Send JSON-RPC initialize request
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()

        init_resp_line = proc.stdout.readline()
        assert init_resp_line, "Expected initialize response from MCP server"
        init_resp = json.loads(init_resp_line)
        assert init_resp.get("id") == 1
        assert "result" in init_resp

        # 2. Send initialized notification
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        proc.stdin.write(json.dumps(init_notif) + "\n")
        proc.stdin.flush()

        # 3. Request tools/list
        tools_list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        proc.stdin.write(json.dumps(tools_list_req) + "\n")
        proc.stdin.flush()

        tools_resp_line = proc.stdout.readline()
        assert tools_resp_line, "Expected tools/list response"
        tools_resp = json.loads(tools_resp_line)
        assert tools_resp.get("id") == 2
        tools = tools_resp.get("result", {}).get("tools", [])
        tool_names = [t.get("name") for t in tools]
        assert "get_blender_status" in tool_names
        assert "list_scene_objects" in tool_names
        assert "get_object_details" in tool_names
        assert "list_scene_collections" in tool_names


        # 4. Request tools/call for get_blender_status
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_blender_status",
                "arguments": {},
            },
        }
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()

        call_resp_line = proc.stdout.readline()
        assert call_resp_line, "Expected tools/call response"
        call_resp = json.loads(call_resp_line)
        assert call_resp.get("id") == 3
        content = call_resp.get("result", {}).get("content", [])
        assert len(content) > 0
        raw_text = content[0].get("text", "")
        status_data = json.loads(raw_text)
        assert "connected" in status_data
        assert "api_version" in status_data
        assert status_data["connected"] is False  # Bridge offline

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_mcp_server_stdio_with_live_bridge_server():
    """Verify that when the Blender bridge server is live, MCP server reports connected=true."""
    from blender_addon.bridge_server import start_server, stop_server
    import time
    
    # Start live bridge server on default 9876
    stop_server()
    start_server(host="127.0.0.1", port=9876)
    time.sleep(0.1)

    python_exe = sys.executable
    proc = subprocess.Popen(
        [python_exe, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # 1. Initialize
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }) + "\n")
        proc.stdin.flush()
        proc.stdout.readline()

        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }) + "\n")
        proc.stdin.flush()

        # 2. Call tool
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_blender_status", "arguments": {}},
        }) + "\n")
        proc.stdin.flush()

        call_resp = json.loads(proc.stdout.readline())
        raw_text = call_resp["result"]["content"][0]["text"]
        status_data = json.loads(raw_text)

        assert status_data["connected"] is True
        assert status_data["api_version"] == "1.0.0"
        assert "blender_version" in status_data

        # 3. Call list_scene_objects
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_scene_objects", "arguments": {"limit": 10}},
        }) + "\n")
        proc.stdin.flush()

        call_resp2 = json.loads(proc.stdout.readline())
        raw_text2 = call_resp2["result"]["content"][0]["text"]
        objects_data = json.loads(raw_text2)
        assert "scene_name" in objects_data
        assert "objects" in objects_data
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
        stop_server()


