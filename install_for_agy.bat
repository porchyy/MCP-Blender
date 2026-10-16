@echo off
setlocal
cd /d "%~dp0"

echo [Blender Asset Prep MCP] Installing for Antigravity (AGY)...

if exist .venv\Scripts\python.exe (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -m mcp_server.install
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Installation finished successfully!
) else (
    echo.
    echo An error occurred during installation.
)

pause
