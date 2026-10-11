# Implementation Plan: Blender Asset Prep MCP (Phase 1)

## Overview & Goal
Build **Phase 1** of **Blender Asset Prep MCP**, connecting **Google Antigravity** to **Blender 5.2** via Model Context Protocol (MCP) using a secure, local-only bridge (`127.0.0.1`).

In Phase 1, we focus on establishing the foundation:
- MCP Server with strict input schemas and error handling
- Blender Add-on running on localhost
- Secure communication bridge without arbitrary execution risks
- Initial tool: `get_blender_status`
- Disconnection / error handling
- Automated test suite and test verification

---

## Environment Investigation Summary
- **Operating System**: Windows 11 (64-bit)
- **Host Python**: Python 3.14.7 (`C:\Program Files\Python314\python.exe`)
- **Blender**: Blender 5.2.2.0 installed via Microsoft Store (`C:\Program Files\WindowsApps\BlenderFoundation.Blender_5.2.2.0_x64__ppwjx1n5r4v9t`, user data at `C:\Users\aomzi\AppData\Roaming\Blender Foundation\Blender\5.2`)
- **Blender Internal Python**: Python 3.13 (read-only package directory under WindowsApps)
- **Antigravity MCP Config**: Configured via `C:\Users\aomzi\.gemini\settings.json` and `C:\Users\aomzi\.gemini\config\mcp_config.json`
- **MCP Python SDK**: `mcp` 2.3.0 available on PyPI

---

## User Review Required

> [!IMPORTANT]
> **Blender Python Constraint & Bridge Architecture**:
> Because Blender was installed from the Microsoft Store, its installation folder is write-protected by Windows AppX security (`Access is denied` for pip installs into Blender's embedded Python).
> 
> **Decision**: To ensure zero installation friction and prevent permissions errors:
> 1. The **Blender Add-on side** will use Python's built-in standard library (`http.server` / `socketserver` + `threading` + `bpy.app.timers`) listening on `127.0.0.1:9876` with strict JSON-RPC request-response handling. It requires **no third-party pip dependencies** inside Blender!
> 2. The **MCP Server side** runs in a dedicated virtual environment (`.venv`) using the official `mcp` SDK and `httpx`/`requests` for robust connection timeouts and retries.
> 3. Does this zero-dependency Add-on design meet your expectations?

> [!WARNING]
> **Security Guardrails Enforced**:
> - Bridge binds strictly to `127.0.0.1` (localhost only).
> - No generic `eval()`, `exec()`, or arbitrary shell/script execution tools are exposed.
> - Handlers are dispatched strictly by predefined action enum (`get_status`, etc.). Any unrecognized action is rejected.

---

## Proposed Architecture

```mermaid
flowchart LR
    AGY["Google Antigravity (AGY)"] <--> |stdio (JSON-RPC)| MCPServer["MCP Server (Python .venv)"]
    MCPServer <--> |Local HTTP/JSON (127.0.0.1:9876)| BlenderAddon["Blender Add-on (localhost listener)"]
    BlenderAddon <--> |bpy API| Blender["Blender 5.2 Engine"]
```

### Component Architecture
1. **MCP Server (`mcp_server`)**:
   - Runs as a standard MCP stdio server registered in Antigravity's `settings.json`.
   - Uses `mcp` Python SDK (FastMCP / MCPServer).
   - Validates input and output schemas with Pydantic.
   - Communicates with the Blender Bridge Client. When Blender is closed or unreachable, it returns structured disconnected status gracefully without crashing.

2. **Bridge Protocol (`bridge`)**:
   - REST / JSON-RPC over localhost (`127.0.0.1:9876`).
   - Endpoint: `/api/v1/action` with payload `{"action": "get_status", "params": {}}`.
   - Healthcheck endpoint: `/health`.
   - Timeout: 3.0s default, configurable.

3. **Blender Add-on (`blender_addon`)**:
   - Standard Blender Add-on format (`bl_info`).
   - UI Panel in the 3D Viewport Sidebar (`N` panel -> `Asset Prep MCP`).
   - Controls: "Start Bridge Server" and "Stop Bridge Server" buttons, status indicator, and auto-start preference.
   - Dispatches safe actions in Blender's main thread via `bpy.app.timers` when necessary.

---

## Proposed Directory Structure

```
A:\ส่วนเสริมเขียนเอง\MCP-Blender\
├── .gitignore                      # Git ignore rules (.venv, __pycache__, logs)
├── pyproject.toml                  # Project metadata & dependencies
├── README.md                       # Documentation, setup & Antigravity config
├── mcp_server/
│   ├── __init__.py
│   ├── config.py                   # Bridge host, port, timeouts, retry settings
│   ├── models.py                   # Pydantic schemas (StatusResponse, ErrorResponse)
│   ├── bridge_client.py            # HTTP client communicating with 127.0.0.1:9876
│   └── server.py                   # MCP server entrypoint & get_blender_status tool
├── blender_addon/
│   ├── __init__.py                 # Blender add-on metadata & registration
│   ├── bridge_server.py            # Localhost server (http.server / socketserver)
│   ├── handlers.py                 # Safe bpy status handler (version, scene, objects)
│   └── ui.py                       # 3D Viewport sidebar UI panel
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures & mock server
    ├── test_bridge_client.py       # Test bridge client (online & offline cases)
    ├── test_mcp_server.py          # Test get_blender_status MCP tool
    └── test_handlers.py            # Unit test for handlers with mock bpy
```

---

## Phase 1 Implementation Steps

### Step 1: Initialize Git & Environment Configuration
- [NEW] `.gitignore` (ignore `.venv`, `__pycache__`, `.pytest_cache`, `*.pyc`, `logs/`)
- [NEW] `pyproject.toml` (declare dependencies: `mcp>=1.2.0`, `httpx>=0.27.0`, `pydantic>=2.0.0`, `pytest>=8.0.0`)
- Set up isolated `.venv` using Python 3.14 to ensure dependencies are isolated from system Python.

### Step 2: Implement MCP Server & Models
- [NEW] `mcp_server/models.py`:
  - `BlenderStatus`: `connected (bool)`, `blender_version (str | None)`, `api_version (str)`, `scene_name (str | None)`, `objects_count (int | None)`, `message (str)`
- [NEW] `mcp_server/config.py`:
  - `BRIDGE_HOST = "127.0.0.1"`, `BRIDGE_PORT = 9876`, `REQUEST_TIMEOUT = 3.0`
- [NEW] `mcp_server/bridge_client.py`:
  - `get_status() -> BlenderStatus`: Sends request to `http://127.0.0.1:9876/api/v1/action`. Catches `ConnectError`, `TimeoutException`, returns disconnected `BlenderStatus` without raising unhandled errors.
- [NEW] `mcp_server/server.py`:
  - Exposes tool: `get_blender_status()` returning JSON-formatted status.

### Step 3: Implement Blender Add-on
- [NEW] `blender_addon/handlers.py`:
  - Action registry mapping `"get_status"` to a safe handler inspecting `bpy.app.version_string`, `bpy.context.scene.name`, and `len(bpy.data.objects)`.
- [NEW] `blender_addon/bridge_server.py`:
  - Standard library `ThreadingHTTPServer` bound strictly to `127.0.0.1:9876`.
  - Start / Stop lifecycle functions with daemon thread.
- [NEW] `blender_addon/ui.py`:
  - Sidebar panel (`VIEW_3D > UI > Asset Prep MCP`) with Start/Stop Server buttons and port display.
- [NEW] `blender_addon/__init__.py`:
  - Blender add-on entry point (`bl_info`), `register()` and `unregister()`.

### Step 4: Add Automated Tests
- [NEW] `tests/test_bridge_client.py`:
  - Test bridge client when Blender server is running (PASS).
  - Test bridge client when Blender server is offline (PASS - graceful fallback).
  - Test bridge client on timeout (PASS - graceful fallback).
- [NEW] `tests/test_mcp_server.py`:
  - Test tool invocation of `get_blender_status`.
- [NEW] `tests/test_handlers.py`:
  - Test handler action validation (rejects invalid actions).

### Step 5: Document Setup & Antigravity Configuration
- [NEW] `README.md`:
  - Detailed installation instructions for Windows.
  - Blender Add-on installation steps (copy to Blender scripts or install zip).
  - AGY configuration snippet for `C:\Users\aomzi\.gemini\settings.json`.

---

## Verification Plan

### Automated Tests
Run pytest in the project directory using the virtual environment:
```powershell
.\.venv\Scripts\pytest.exe -v tests/
```
Expected: All unit tests pass (100% PASS for mocked and offline/online bridge tests).

### Live Integration Verification
1. **Offline Test**:
   - Run `python -m mcp_server.server` or test script while Blender is closed.
   - Verify `get_blender_status()` returns `connected: false` with descriptive message and does not crash.
2. **Online Test**:
   - Start the Blender Add-on bridge server on `127.0.0.1:9876`.
   - Run test script / tool call to query `get_blender_status()`.
   - Verify `connected: true`, `blender_version: "5.2.2"` (or active version), and scene details.
3. **Antigravity MCP Registration**:
   - Validate JSON configuration for `settings.json`.
