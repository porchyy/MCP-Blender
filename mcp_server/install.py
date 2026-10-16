"""One-click installer for Blender Asset Prep MCP & Antigravity (AGY) Integration."""
import json
import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_repo_root() -> Path:
    """Return the absolute path to the repository root."""
    return Path(__file__).resolve().parent.parent


def get_venv_python(repo_root: Path) -> str:
    """Locate the Python executable in the virtual environment."""
    if os.name == "nt":
        venv_py = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = repo_root / ".venv" / "bin" / "python"
    
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def detect_blender_addon_dirs() -> list[Path]:
    """Detect all installed Blender user add-on directories."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return []

    blender_base = Path(appdata) / "Blender Foundation" / "Blender"
    if not blender_base.exists():
        return []

    addon_dirs = []
    for item in blender_base.iterdir():
        if item.is_dir():
            addons_dir = item / "scripts" / "addons"
            addon_dirs.append(addons_dir)

    # Sort descending so newer versions come first (e.g. 5.2 before 4.2)
    addon_dirs.sort(key=lambda p: p.parent.parent.name, reverse=True)
    return addon_dirs


def install_blender_addon(repo_root: Path) -> list[str]:
    """Copy the blender_addon files into all detected Blender add-on directories."""
    addon_source = repo_root / "blender_addon"
    if not addon_source.exists():
        raise FileNotFoundError(f"Source add-on directory not found at {addon_source}")

    detected = detect_blender_addon_dirs()
    installed_paths = []

    if not detected:
        # Default fallback to 5.2
        appdata = os.environ.get("APPDATA", "")
        fallback = Path(appdata) / "Blender Foundation" / "Blender" / "5.2" / "scripts" / "addons"
        detected = [fallback]

    for target_base in detected:
        target_dir = target_base / "blender_asset_prep"
        target_dir.mkdir(parents=True, exist_ok=True)

        for src_file in addon_source.glob("*.*"):
            shutil.copy2(src_file, target_dir / src_file.name)

        installed_paths.append(str(target_dir))

    return installed_paths


def register_antigravity_mcp(python_exe: str, repo_root: Path) -> list[str]:
    """Register or update blender-asset-prep in Antigravity MCP config files."""
    user_home = Path.home()
    config_paths = [
        user_home / ".gemini" / "config" / "mcp_config.json",
        user_home / ".gemini" / "settings.json",
        user_home / ".gemini" / "antigravity-cli" / "settings.json",
    ]

    server_entry = {
        "command": python_exe,
        "args": ["-m", "mcp_server.server"],
        "env": {
            "PYTHONPATH": str(repo_root),
            "PYTHONIOENCODING": "utf-8",
        },
    }

    updated_files = []
    for cfg_path in config_paths:
        try:
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if cfg_path.exists():
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
                data["mcpServers"] = {}

            data["mcpServers"]["blender-asset-prep"] = server_entry

            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            updated_files.append(str(cfg_path))
        except Exception as e:
            print(f"[Warning] Failed to update {cfg_path}: {e}")

    return updated_files


def install_global_skills(repo_root: Path) -> list[str]:
    """Deploy the /blender skill to global AGY skills directory."""
    user_home = Path.home()
    global_skill_dir = user_home / ".agents" / "skills" / "blender"
    source_skill = repo_root / ".agents" / "skills" / "blender" / "SKILL.md"

    installed = []
    if source_skill.exists():
        try:
            global_skill_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_skill, global_skill_dir / "SKILL.md")
            installed.append(str(global_skill_dir / "SKILL.md"))
        except Exception as e:
            print(f"[Warning] Failed to deploy global skill: {e}")
    return installed


def main():
    """CLI entrypoint for installer."""
    print("==================================================")
    print("   Blender Asset Prep MCP - AGY Installer")
    print("==================================================")

    repo_root = get_repo_root()
    python_exe = get_venv_python(repo_root)

    print(f"[1/3] Repository root: {repo_root}")
    print(f"      Python executable: {python_exe}")

    print("\n[2/3] Deploying Blender Add-on...")
    try:
        destinations = install_blender_addon(repo_root)
        for dest in destinations:
            print(f"      + Installed to: {dest}")
    except Exception as exc:
        print(f"      [Error] Could not copy add-on: {exc}")
        sys.exit(1)

    print("\n[3/4] Registering in Antigravity (AGY) configs...")
    updated_configs = register_antigravity_mcp(python_exe, repo_root)
    for cfg in updated_configs:
        print(f"      + Updated config: {cfg}")

    print("\n[4/4] Deploying /blender slash command skill...")
    skills_installed = install_global_skills(repo_root)
    for sk in skills_installed:
        print(f"      + Installed skill: {sk}")

    print("\n--------------------------------------------------")
    print("Installation Complete!")
    print("1. Open Blender -> Check 'Blender Asset Prep MCP Bridge' in Preferences > Add-ons.")
    print("2. Server auto-starts on 127.0.0.1:9876.")
    print("3. Antigravity can now communicate with Blender via MCP tools and /blender command!")
    print("==================================================")


if __name__ == "__main__":
    main()
