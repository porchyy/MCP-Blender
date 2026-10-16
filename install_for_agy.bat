@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================================
echo   Blender Asset Prep MCP + /blender Skill - AGY One-Click Setup
echo ================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10 or higher and add it to PATH.
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment if missing
if not exist .venv\Scripts\python.exe (
    echo [1/3] Creating Python virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [1/3] Installing package dependencies...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -e .
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install package dependencies.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment (.venv) detected.
)

:: 3. Run Installer (Deploys Add-on, MCP Configs, and /blender Skill)
echo.
echo [2/3] Installing Blender Add-on, MCP Server, and /blender Skill...
.venv\Scripts\python.exe -m mcp_server.install
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred during installation.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] All components installed and configured successfully!
echo You can now use the /blender command in Antigravity chat.
echo.
pause
