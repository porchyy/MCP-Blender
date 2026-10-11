"""Tests for thread-safe dispatcher (Requirement 6 & 7)."""
import pytest
from unittest.mock import MagicMock
from blender_addon.dispatcher import run_on_main_thread


def test_run_on_main_thread_standalone():
    """When bpy is None or has no timers, executes directly in calling thread."""
    def sample_func(a, b):
        return a + b

    result = run_on_main_thread(sample_func, 10, 20)
    assert result == 30


def test_run_on_main_thread_with_bpy_timer():
    """When bpy has timers, schedules via bpy.app.timers.register and waits for result."""
    mock_bpy = MagicMock()
    
    def fake_register(runner, first_interval=0.0):
        # Simulate Blender's event loop executing the timer
        runner()

    mock_bpy.app.timers.register.side_effect = fake_register

    import blender_addon.dispatcher as dispatcher
    orig_bpy = dispatcher.bpy
    try:
        dispatcher.bpy = mock_bpy
        
        def sample_func(x):
            return x * 2

        res = dispatcher.run_on_main_thread(sample_func, 21)
        assert res == 42
        mock_bpy.app.timers.register.assert_called_once()
    finally:
        dispatcher.bpy = orig_bpy


def test_run_on_main_thread_timeout():
    """When main thread never executes the task, raises TimeoutError."""
    mock_bpy = MagicMock()
    # Timer registered but never runs runner()
    mock_bpy.app.timers.register.return_value = None

    import blender_addon.dispatcher as dispatcher
    orig_bpy = dispatcher.bpy
    try:
        dispatcher.bpy = mock_bpy
        
        with pytest.raises(TimeoutError, match="timed out"):
            dispatcher.run_on_main_thread(lambda: 123, timeout=0.1)
    finally:
        dispatcher.bpy = orig_bpy
