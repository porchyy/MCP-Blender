# Blender Asset Prep MCP Bridge (v0.2.0 Release Candidate)

Model Context Protocol (MCP) Server and Blender Bridge connecting **Google Antigravity (AGY)** and other MCP clients to **Blender 4.2+ / 5.x LTS** over a secure, thread-safe, local-only bridge (`127.0.0.1:9876`).

---

## Architecture & Security Model

```
[Google Antigravity (AGY) / MCP Client]
       │ (Standard Input/Output Stdio JSON-RPC)
       ▼
[MCP Server (Python .venv)]
       │ (HTTP POST JSON payload to 127.0.0.1:9876)
       ▼
[Blender Bridge Server (Daemon Thread)]
       │ (Thread-safe Main-Thread Dispatcher via bpy.app.timers)
       ▼
[Blender 5.x Engine & Scene Data]
```

### Security & Integrity Guardrails
1. **Localhost Only**: Binds strictly to `127.0.0.1:9876`. No external network interfaces or internet ports are opened.
2. **Strict Action Allowlist**: Only predefined action handlers can execute. **Arbitrary Python or Shell execution (`eval`, `exec`, `subprocess`) is strictly forbidden.**
3. **Thread-Safe Dispatcher**: All Blender API (`bpy`, `bmesh`) calls are dispatched to Blender's main event loop via `bpy.app.timers.register`, eliminating race conditions or C-API crashes.
4. **World-Space Invariance**: Pivot adjustments recalculate local offsets such that mesh geometry in 3D world space remains strictly invariant.
5. **Batch Error Isolation**: Batch operations process each object independently; an invalid or missing target never halts remaining batch operations.
6. **Zero External Dependencies in Blender**: The Add-on uses only Python standard library modules (`http.server`, `threading`, `json`, `mathutils`, `bmesh`).

---

## Available MCP Tools (11 Tools)

### 1. Scene Inspection Tools (Read-Only)
| Tool | Description | Parameters |
|---|---|---|
| `get_blender_status` | Returns connection state, Blender version string, active scene name, and total object count. | *None* |
| `list_scene_objects` | Enumerate objects in active scene with location, rotation, scale, type, and pagination. | `limit: int = 100`, `offset: int = 0` |
| `get_object_details` | Retrieve deep object details: dimensions, parent, collection membership, and material slots. | `object_name: str` |
| `list_scene_collections`| Retrieve the complete hierarchy tree of scene collections and child objects. | *None* |

### 2. Geometry Inspection & Validation (Read-Only)
| Tool | Description | Parameters |
|---|---|---|
| `inspect_mesh` | Validate mesh topology: watertightness, non-manifold edges, loose vertices/edges, boundary edges, normal consistency, dimensions, and world-space bounding box. | `object_name: str` |
| `batch_inspect_mesh` | Inspect and validate geometry/topology for multiple objects in a single batch call with itemized PASS/FAIL report. | `object_names: list[str]` |

### 3. Asset Preparation & Modification Tools (Write Operations)
| Tool | Description | Parameters |
|---|---|---|
| `apply_transforms` | Freeze Location, Rotation, and/or Scale to object's base matrix. | `object_name: str`, `location: bool = False`, `rotation: bool = True`, `scale: bool = True` |
| `set_origin_to_bottom` | Move object origin/pivot to bottom-center of bounding box without shifting visual position in world space. | `object_name: str` |
| `clean_mesh` | Remove duplicate vertices (`merge_by_distance`) and recalculate face normals outward via BMesh. | `object_name: str`, `merge_distance: float = 0.0001`, `recalculate_normals: bool = True` |
| `batch_clean_mesh` | Clean meshes for multiple objects with error isolation. | `object_names: list[str]`, `merge_distance: float = 0.0001`, `recalculate_normals: bool = True` |
| `batch_set_origin_to_bottom` | Move origins to bottom-center for multiple objects with error isolation. | `object_names: list[str]` |

---

## Installation & Setup Guide

### 1. Requirements
- **OS**: Windows 10/11
- **Python**: 3.10+
- **Blender**: 4.2+ or 5.2.2 LTS (Standard or Microsoft Store edition)

### 2. Python Environment Setup
In the project directory (`A:\ส่วนเสริมเขียนเอง\MCP-Blender`):
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

### 3. Install Blender Add-on from ZIP
1. Open Blender.
2. Navigate to **Edit > Preferences > Add-ons** (or **Get Extensions > Install from Disk**).
3. Select `blender_asset_prep_addon.zip` located in the root repository folder.
4. Enable **Blender Asset Prep MCP Bridge**.
5. The Bridge starts automatically on port `9876` on Blender startup. (You can also control it from 3D Viewport sidebar: press `N` > **Asset Prep MCP**).

*Alternative manual installation:*
```powershell
$target = "$env:APPDATA\Blender Foundation\Blender\5.2\scripts\addons\blender_asset_prep"
Expand-Archive -Path "blender_asset_prep_addon.zip" -DestinationPath $target -Force
```

### 4. Configure MCP Client

Add to your MCP settings file (e.g. `C:\Users\<user>\.gemini\settings.json` or Claude Desktop `claude_desktop_config.json`):
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

## Testing & Verification

Run the automated test suite (61 tests covering unit, mock, integration, and stdio JSON-RPC):
```powershell
.\.venv\Scripts\python.exe -m pytest -v tests/
```

Verify live connection to active Blender:
```powershell
.\.venv\Scripts\python.exe -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://127.0.0.1:9876/health').read()))"
```

---

## Troubleshooting Guide

| Problem | Cause | Solution |
|---|---|---|
| `connected: false` | Blender is not running or Add-on is disabled. | Start Blender and verify that "Blender Asset Prep MCP Bridge" is checked in Preferences > Add-ons. |
| `WinError 10061` Connection refused | Bridge server stopped. | In Blender 3D Viewport, press `N` > click `Asset Prep MCP` > click `Start Server`. |
| Port 9876 conflict | Another process bound port 9876. | Run `Get-NetTCPConnection -LocalPort 9876` in PowerShell to find the owning process PID. |
| Non-mesh error on origin/clean | Calling mesh tools on Cameras, Lights, or Empties. | Mesh tools require `MESH` objects. Use `batch_` tools which safely isolate non-mesh errors without halting. |
