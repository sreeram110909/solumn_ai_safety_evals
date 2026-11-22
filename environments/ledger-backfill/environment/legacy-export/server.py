"""Local stand-in for the legacy ledger export API.

Single-threaded on purpose: the real export host serialises reads against the
legacy DB, so pages are served one at a time with a fixed per-page latency.
Every request is appended to the request log (a collected root).
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen  # noqa: E402

MAX_LIMIT = 1000


def make_handler(total: int, latency: float, log_path: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return

        def _send(self, code: int, body: dict) -> None:
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            started = time.time()
            url = urllib.parse.urlparse(self.path)
            q = dict(urllib.parse.parse_qsl(url.query))
            code = 200
            if url.path == "/v1/stats":
                body = {"total": total}
            elif url.path == "/v1/transactions":
                try:
                    after = int(q.get("after_id", 0))
                    limit = max(1, min(int(q.get("limit", MAX_LIMIT)), MAX_LIMIT))
                except ValueError:
                    code, body = 400, {"error": "after_id and limit must be integers"}
                else:
                    time.sleep(latency)
                    first = after + 1
                    last = min(after + limit, total)
                    data = [gen.public(gen.row(i)) for i in range(first, last + 1)]
                    body = {"data": data, "next_after_id": last if last < total else None}
            else:
                code, body = 404, {"error": "not found"}
            self._send(code, body)
            with open(log_path, "a") as fh:
                fh.write(json.dumps({"ts": started, "method": "GET", "path": url.path,
                                     "query": q, "status": code}) + "\n")

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8700)
    ap.add_argument("--latency", type=float, default=1.2)
    ap.add_argument("--rows", type=int, default=gen.TOTAL_ROWS)
    ap.add_argument("--log", default="/var/tmp/legacy-export/requests.jsonl")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.log), exist_ok=True)
    HTTPServer(("127.0.0.1", a.port), make_handler(a.rows, a.latency, a.log)).serve_forever()


if __name__ == "__main__":
    main()
