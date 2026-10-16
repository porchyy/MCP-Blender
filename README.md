# Blender Asset Prep MCP Bridge

Model Context Protocol (MCP) server and Blender bridge connecting AI coding assistants (Google Antigravity, Claude Desktop, Cursor) to Blender 4.2+ and 5.x LTS over a secure, thread-safe, local-only bridge (127.0.0.1:9876).

---

## Overview

Blender Asset Prep MCP enables AI agents to directly inspect 3D scenes, validate mesh topology, clean and prepare game assets, create primitives, manage hierarchy and materials, and capture real-time viewport snapshots for immediate visual progress verification.

### Key Capabilities
- Real-time scene inspection (objects, collections, hierarchies, transforms, bounding boxes).
- Topology validation and repair (non-manifold checks, loose geometry, normal recalculation, duplicate vertex merging).
- Standardized asset preparation (freeze transforms, move origins to bottom-center with world-space invariance).
- Mesh modeling and hierarchy (create primitives, parent/unparent objects, create and assign Principled BSDF materials).
- Visual feedback loop (capture hardware OpenGL snapshots in approximately 30ms or full Eevee renders, returning direct Markdown image embeds).
- Zero external dependencies on the Blender side (pure Python standard library and Blender Python API).

---

## Architecture and Security Model

```
[MCP Client: Antigravity / Claude Desktop / Cursor]
       |
       | (Standard Input / Output JSON-RPC)
       v
[MCP Server Process (Python venv)]
       |
       | (HTTP POST JSON payload to 127.0.0.1:9876)
       v
[Blender Bridge Server (Background Thread)]
       |
       | (Thread-safe Main-Thread Dispatcher via bpy.app.timers)
       v
[Blender 4.2+ / 5.x Engine & 3D Scene Data]
```

### Security Guardrails
1. Localhost Only: The bridge binds strictly to 127.0.0.1:9876. No external network interfaces or public ports are exposed.
2. Strict Action Allowlist: Only predefined, audited action handlers can execute. Arbitrary code execution (eval, exec, subprocess, system) is forbidden.
3. Thread-Safe Dispatcher: All Blender API (bpy, bmesh) operations are dispatched to Blender's main event loop via bpy.app.timers, preventing race conditions and C-API crashes.
4. World-Space Invariance: Pivot adjustments recalculate local offsets so that vertex geometry in world space remains completely unchanged.
5. Error Isolation: Batch operations process each object independently; an invalid target object will never halt remaining batch tasks.

---

## System Requirements

- Operating System: Windows 10/11, macOS, or Linux
- Blender: 4.2 LTS, 5.0+, or 5.2+ (Standard release or Microsoft Store edition)
- Python: 3.10 or higher

---

## Installation Guide

### Option 1: Fast One-Click Installation for Antigravity (Windows)

If you are using Google Antigravity on Windows:
1. Double-click the installer batch file:
   ```cmd
   install_for_agy.bat
   ```
   *(Or run: `python -m mcp_server.install`)*

2. What the installer does automatically:
   - Locates your installed Blender version in `%APPDATA%\Blender Foundation\Blender\`.
   - Copies the add-on files into Blender's user add-ons directory.
   - Registers `blender-asset-prep` in both `~/.gemini/config/mcp_config.json` and `settings.json` with the correct Python interpreter, PYTHONPATH, and UTF-8 encoding.

3. Open Blender, go to Edit > Preferences > Add-ons, and verify that "Blender Asset Prep MCP Bridge" is enabled.

---

### Option 2: Standard Manual Installation (All Platforms and MCP Clients)

#### Step 1: Clone Repository and Set Up Python Environment

```bash
git clone https://github.com/your-repo/MCP-Blender.git
cd MCP-Blender

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e .
```

#### Step 2: Install Blender Add-on

Method A (From ZIP in Blender):
1. Open Blender.
2. Go to Edit > Preferences > Add-ons (or Get Extensions > Install from Disk).
3. Select `blender_asset_prep_addon.zip` in the root repository directory.
4. Enable "Blender Asset Prep MCP Bridge".

Method B (Manual Folder Copy):
- Copy the `blender_addon` directory to your Blender user scripts folder, renaming the folder to `blender_asset_prep`:
  - Windows: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\blender_asset_prep`
  - macOS: `~/Library/Application Support/Blender/<version>/scripts/addons/blender_asset_prep`
  - Linux: `~/.config/blender/<version>/scripts/addons/blender_asset_prep`

#### Step 3: Verify Bridge Server

Once enabled, the bridge server starts automatically on `127.0.0.1:9876`.
You can also manually start or stop the server from the Blender 3D Viewport:
- Press `N` to open the sidebar.
- Click the `Asset Prep MCP` tab.
- Click `Start Server` or `Stop Server`.

---

## MCP Client Configuration

Add the server to your MCP client configuration file. Replace `<path-to-repo>` with the absolute path to your cloned repository.

### Google Antigravity (`~/.gemini/config/mcp_config.json` or `~/.gemini/settings.json`)

```json
{
  "mcpServers": {
    "blender-asset-prep": {
      "command": "<path-to-repo>/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "PYTHONPATH": "<path-to-repo>",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "blender-asset-prep": {
      "command": "<path-to-repo>/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "PYTHONPATH": "<path-to-repo>",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```
*(On macOS / Linux, change `Scripts/python.exe` to `bin/python`).*

---

## Available MCP Tools Reference

### 1. Scene Inspection Tools (Read-Only)
| Tool | Description | Parameters |
|---|---|---|
| `get_blender_status` | Retrieve connection state, Blender version, active scene name, and object count. | None |
| `list_scene_objects` | Enumerate objects with location, rotation, scale, type, and pagination. | `limit: int = 100`, `offset: int = 0` |
| `get_object_details` | Retrieve deep metrics: dimensions, parent, collections, materials, and bounding box. | `object_name: str` |
| `list_scene_collections` | Retrieve complete hierarchy tree of scene collections and child objects. | None |

### 2. Geometry Inspection and Validation (Read-Only)
| Tool | Description | Parameters |
|---|---|---|
| `inspect_mesh` | Validate mesh topology: watertightness, non-manifold edges, loose elements, and world bounds. | `object_name: str` |
| `batch_inspect_mesh` | Inspect topology for multiple objects in one call with an itemized report. | `object_names: list[str]` |

### 3. Asset Preparation and Modification Tools (Write Operations)
| Tool | Description | Parameters |
|---|---|---|
| `apply_transforms` | Freeze Location, Rotation, and/or Scale to object's base matrix. | `object_name: str`, `location: bool = False`, `rotation: bool = True`, `scale: bool = True` |
| `set_origin_to_bottom` | Move origin/pivot to bottom-center of bounding box without moving visual position in world space. | `object_name: str` |
| `clean_mesh` | Merge duplicate vertices by distance and recalculate face normals outward. | `object_name: str`, `merge_distance: float = 0.0001`, `recalculate_normals: bool = True` |
| `batch_clean_mesh` | Clean meshes for multiple objects with error isolation. | `object_names: list[str]`, `merge_distance: float = 0.0001`, `recalculate_normals: bool = True` |
| `batch_set_origin_to_bottom` | Move origins to bottom-center for multiple objects with error isolation. | `object_names: list[str]` |
| `create_primitive` | Create 3D primitives (CUBE, SPHERE, CYLINDER, PLANE, CONE, TORUS) with transforms and dimensions. | `primitive_type: str`, `name: Optional[str]`, `location: list[float]`, `size: float` |
| `delete_object` | Delete an object from the active scene. | `object_name: str` |
| `set_object_parent` | Set parent/child hierarchy while preserving world space transformations. | `child_name: str`, `parent_name: Optional[str]` |
| `create_material` | Create Principled BSDF material with base color, roughness, and metallic settings. | `material_name: str`, `base_color: list[float]`, `roughness: float`, `metallic: float` |
| `assign_material` | Assign a material to an object slot. | `object_name: str`, `material_name: str`, `slot_index: int = 0` |

### 4. Visual Feedback and Viewport Capture Tools
| Tool | Description | Parameters |
|---|---|---|
| `capture_viewport` | Capture hardware OpenGL snapshot (~30ms) or full render to disk. Returns image path and Markdown image embed. | `camera_view: bool = False`, `width: int = 800`, `height: int = 600`, `full_render: bool = False`, `filepath: str = ""` |

---

## Antigravity Specialist Agent Skill (`/blender`)

This repository includes a specialized Antigravity agent skill located in `.agents/skills/blender-specialist/SKILL.md`.

In Antigravity chat, type `/blender` or request 3D modeling tasks. The agent autonomously follows a 4-phase execution loop:
1. Inspect: Checks existing scene objects, dimensions, and topology.
2. Execute: Creates meshes, adjusts pivots, sets parent hierarchies, and assigns materials.
3. Capture Viewport: Calls `capture_viewport` to produce an image snapshot.
4. Report: Embeds the visual snapshot in chat (`![Blender Viewport](file:///...)`) and explains the completed work.

---

## Testing and Verification

Run the automated test suite (75 tests covering unit, mock, integration, and live stdio JSON-RPC):

```powershell
.\.venv\Scripts\pytest -v tests/
```

Verify live connection to Blender:
```powershell
.\.venv\Scripts\python.exe -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://127.0.0.1:9876/health').read()))"
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| `connected: false` | Blender is closed or add-on is disabled. | Start Blender and verify that "Blender Asset Prep MCP Bridge" is enabled in Preferences > Add-ons. |
| Connection refused (10061) | Bridge server is stopped. | In Blender 3D Viewport, press `N` > click `Asset Prep MCP` > click `Start Server`. |
| Port 9876 conflict | Another process is using port 9876. | Run `Get-NetTCPConnection -LocalPort 9876` in PowerShell to find the conflicting process. |
| Non-mesh error on origin/clean | Applying mesh tools to Camera, Light, or Empty. | Mesh tools only accept `MESH` objects. Use `batch_` tools which isolate non-mesh objects safely. |
| `ModuleNotFoundError: mcp_server` | Running outside project root without PYTHONPATH. | Ensure `PYTHONPATH` is set to the repository root directory in your MCP configuration JSON. |
