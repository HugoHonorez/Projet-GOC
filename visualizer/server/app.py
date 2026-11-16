import json
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from ..config import WEB_ROOT
from ..core.instances import InstanceRepository
from .api import Api, ApiError

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
}


def make_handler(api):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            path = urlparse(self.path).path
            if path.startswith("/api/"):
                self.respond_api("GET", path)
            else:
                self.respond_static(path)

        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"null")
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Invalid JSON body."})
                return
            self.respond_api("POST", path, body)

        def respond_api(self, method, path, body=None):
            try:
                self.send_json(200, api.handle(method, path, body))
            except ApiError as error:
                self.send_json(error.status, {"error": error.message})
            except Exception as error:
                traceback.print_exc()
                self.send_json(500, {"error": f"{type(error).__name__}: {error}"})

        def respond_static(self, path):
            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (WEB_ROOT / relative).resolve()
            if WEB_ROOT not in target.parents or not target.is_file():
                self.send_bytes(404, b"Not found", "text/plain; charset=utf-8")
                return
            self.send_bytes(200, target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))

        def send_json(self, status, payload):
            self.send_bytes(status, json.dumps(payload).encode("utf-8"), "application/json")

        def send_bytes(self, status, data, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(settings, host, port, open_browser=True):
    repository = InstanceRepository(settings.instances_dir)
    server = ThreadingHTTPServer((host, port), make_handler(Api(settings, repository)))
    url = f"http://{host}:{port}/"
    print(f"Instances: {settings.instances_dir}")
    print(f"Solutions: {', '.join(str(p) for p in settings.solution_dirs)}")
    print(f"Visualizer running at {url} (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
