import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # per-request lines would bury the simulator's event log


def start_static(host: str, port: int, web_dir: Path) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((host, port), partial(QuietHandler, directory=str(web_dir)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
