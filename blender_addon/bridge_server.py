"""Localhost HTTP Bridge Server running inside Blender using Python standard library."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from blender_addon.handlers import execute_action

_server_instance: Optional[ThreadingHTTPServer] = None
_server_thread: Optional[threading.Thread] = None
_server_port: Optional[int] = None
_lock = threading.Lock()


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for local Blender bridge."""

    def log_message(self, format: str, *args) -> None:
        """Suppress standard logging to keep Blender console clean."""
        pass

    def _send_json(self, status_code: int, data: dict) -> None:
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_GET(self) -> None:
        """Handle health check endpoint."""
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "blender-asset-prep-bridge"})
        else:
            self._send_json(404, {"status": "error", "error": "Not Found"})

    def do_POST(self) -> None:
        """Handle action execution endpoint."""
        if self.path != "/api/v1/action":
            self._send_json(404, {"status": "error", "error": "Not Found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._send_json(400, {"status": "error", "error": "Empty body"})
            return

        try:
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
            action = payload.get("action")
            params = payload.get("params", {})

            if not action or not isinstance(action, str):
                self._send_json(400, {"status": "error", "error": "Missing or invalid 'action' field"})
                return

            result = execute_action(action, params)
            self._send_json(200, {"status": "ok", "data": result})
        except ValueError as err:
            self._send_json(400, {"status": "error", "error": str(err)})
        except Exception as exc:
            self._send_json(500, {"status": "error", "error": f"Internal error: {str(exc)}"})


def is_server_running() -> bool:
    """Return whether the bridge server is currently running."""
    with _lock:
        return _server_instance is not None


def get_server_port() -> Optional[int]:
    """Return the currently bound port of the bridge server."""
    with _lock:
        return _server_port


def start_server(host: str = "127.0.0.1", port: int = 9876) -> bool:
    """Start the bridge server on localhost in a background daemon thread."""
    global _server_instance, _server_thread, _server_port

    with _lock:
        if _server_instance is not None:
            return True  # Already running

        try:
            server = ThreadingHTTPServer((host, port), BridgeRequestHandler)
            _server_instance = server
            _server_port = server.server_address[1]

            thread = threading.Thread(target=server.serve_forever, daemon=True)
            _server_thread = thread
            thread.start()
            return True
        except Exception:
            _server_instance = None
            _server_thread = None
            _server_port = None
            raise


def stop_server() -> bool:
    """Stop the bridge server cleanly and join thread."""
    global _server_instance, _server_thread, _server_port

    with _lock:
        if _server_instance is None:
            return True

        server = _server_instance
        thread = _server_thread

        _server_instance = None
        _server_thread = None
        _server_port = None

    try:
        server.shutdown()
        server.server_close()
        if thread and thread.is_alive():
            thread.join(timeout=1.0)
        return True
    except Exception:
        return False
