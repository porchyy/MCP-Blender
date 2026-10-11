# Blender Asset Prep MCP (Phase 1)

Model Context Protocol (MCP) Server for connecting **Google Antigravity (AGY)** with **Blender** via a secure, local-only bridge.

---

## Architecture & Security Model

```
[Google Antigravity (AGY)]
       │ (stdio / JSON-RPC)
       ▼
[MCP Server (Python .venv)]
       │ (HTTP JSON-RPC strictly on 127.0.0.1:9876)
       ▼
[Blender Add-on Listener]
       │ (bpy API)
   [Blender Engine]
```

### Security Guardrails
1. **Localhost Only**: Binds strictly to `127.0.0.1:9876`. No external network interfaces or internet ports are opened.
2. **Strict Action Allowlist**: Only predefined action identifiers (e.g. `get_status`) can execute. **No arbitrary Python or Shell execution (`eval`, `exec`, `subprocess`) is permitted.**
3. **Resilient Failure Handling**: When Blender is offline or closed, the server gracefully returns a disconnected status without crashing or blocking Antigravity.
4. **Zero Third-Party Dependency in Blender**: The Add-on uses only Python standard library modules (`http.server`, `threading`, `json`), avoiding permission issues with Windows Store / AppX installations of Blender.

---

## Directory Structure & Files Created

| Path | Purpose |
|---|---|
| `.gitignore` | Excludes virtual environments, caches, temporary files, and test artifacts. |
| `pyproject.toml` | Project configuration, dependencies (`mcp`, `httpx`, `pydantic`, `pytest`). |
| `mcp_server/config.py` | Connection configuration (`127.0.0.1:9876`, timeouts). |
| `mcp_server/models.py` | Pydantic data schemas (`BlenderStatus`, `BridgeActionRequest`, `BridgeActionResponse`). |
| `mcp_server/bridge_client.py` | HTTP client communicating with Blender with connection error handling and timeouts. |
| `mcp_server/server.py` | MCP Server entry point exposing `get_blender_status` tool via stdio transport. |
| `blender_addon/__init__.py` | Blender add-on entry point (`bl_info`), registration, and lifecycle cleanup. |
| `blender_addon/bridge_server.py` | Localhost HTTP server running in Blender background daemon thread. |
| `blender_addon/handlers.py` | Whitelist action dispatcher inspecting `bpy` environment safely. |
| `blender_addon/ui.py` | 3D Viewport sidebar panel (`N-Panel > Asset Prep MCP`) with Start/Stop controls. |
| `blender_asset_prep_addon.zip` | Packaged Blender add-on for installation inside Blender. |
| `tests/conftest.py` | Shared pytest fixtures. |
| `tests/test_bridge_client.py` | Unit tests for client handling online, offline, and timeout scenarios. |
| `tests/test_handlers.py` | Security tests ensuring rejection of arbitrary commands & bpy query tests. |
| `tests/test_mcp_server.py` | Unit tests for `get_blender_status` MCP tool formatting. |
| `tests/test_bridge_server.py` | Integration tests for bridge server lifecycle, `/health`, and `/api/v1/action`. |
| `tests/test_addon_lifecycle.py` | Tests for addon registration and unregistration. |
| `tests/test_mcp_stdio_live.py` | Live end-to-end integration tests over stdio JSON-RPC protocol. |

---

## Installation & Setup Guide (Windows)

### 1. Setup Virtual Environment & Install Dependencies
Open PowerShell in the project directory:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
# Or install directly:
.\.venv\Scripts\python.exe -m pip install mcp httpx pydantic pytest pytest-asyncio
```

### 2. Install Blender Add-on
Option A (Direct Copy to Blender Scripts):
Copy the `blender_addon` folder into Blender's addons directory:
```powershell
Copy-Item -Recurse -Force "blender_addon" "$env:APPDATA\Blender Foundation\Blender\5.2\scripts\addons\blender_asset_prep"
```

Option B (Inside Blender GUI):
1. Open Blender.
2. Go to **Edit > Preferences > Add-ons** (or **Get Extensions > Install from Disk**).
3. Select `A:\ส่วนเสริมเขียนเอง\MCP-Blender\blender_asset_prep_addon.zip`.
4. Enable **Blender Asset Prep MCP Bridge**.
5. In the 3D Viewport, press `N` to open the sidebar, click the **Asset Prep MCP** tab, and click **Start Server**.

---

## Antigravity (AGY) Configuration

Registered in `C:\Users\aomzi\.gemini\settings.json`:
```json
{
  "mcpServers": {
    "blender-asset-prep": {
      "command": "A:\\ส่วนเสริมเขียนเอง\\MCP-Blender\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "mcp_server.server"
      ]
    }
  }
}
```

---

## Running Automated Tests

Run the full test suite with:
```powershell
.\.venv\Scripts\pytest.exe -v
```

---

## Phase 1 Limitations & Roadmap (Phase 2)

### Limitations in Phase 1
- Read-only environment inspection (`get_blender_status`).
- Does not yet create or modify 3D objects, materials, or collections.
- Manual start of Blender add-on server required if Blender is not already running.

### Planned for Phase 2+
- Tool to inspect active scene objects hierarchy and collections.
- Tools to create primitives and transform 3D objects.
- Materials and shader node management.
- Asset validation checks.
- GLB export and preview rendering.
