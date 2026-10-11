"""Configuration constants for Blender Bridge."""
import os

BRIDGE_HOST: str = "127.0.0.1"
BRIDGE_PORT: int = int(os.getenv("BLENDER_BRIDGE_PORT", "9876"))
REQUEST_TIMEOUT: float = float(os.getenv("BLENDER_BRIDGE_TIMEOUT", "3.0"))
