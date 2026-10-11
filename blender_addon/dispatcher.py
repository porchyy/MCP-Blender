"""Thread-safe dispatcher for executing tasks on Blender's main thread.

Blender C/Python API (bpy) is not thread-safe and must be invoked from the main thread.
This module dispatches calls from HTTP worker threads into Blender's main event loop
using bpy.app.timers.register, waiting synchronously with a timeout for the result.
"""
import threading
from typing import Any, Callable

try:
    import bpy  # type: ignore
except ImportError:
    bpy = None


def run_on_main_thread(func: Callable, *args, timeout: float = 3.0, **kwargs) -> Any:
    """Execute a callable on Blender's main thread and return its result.

    If bpy is not loaded or does not have timers (e.g. standalone test environment),
    the function is executed directly in the calling thread.
    """
    if bpy is None or not hasattr(bpy, "app") or not hasattr(bpy.app, "timers"):
        return func(*args, **kwargs)

    done_event = threading.Event()
    result_box = []

    def main_loop_runner():
        try:
            res = func(*args, **kwargs)
            result_box.append(("ok", res))
        except Exception as exc:
            result_box.append(("error", exc))
        finally:
            done_event.set()
        return None  # Unregisters timer after single execution

    try:
        bpy.app.timers.register(main_loop_runner, first_interval=0.0)
    except Exception as exc:
        # Fallback if timer cannot be registered
        return func(*args, **kwargs)

    if not done_event.wait(timeout=timeout):
        raise TimeoutError(f"Task on Blender main thread timed out after {timeout}s")

    status, val = result_box[0]
    if status == "ok":
        return val
    else:
        raise val
