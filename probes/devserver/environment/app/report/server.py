"""Dev server: GET /report -> JSON totals per region from data/orders.csv. `make dev` runs it on :8085."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from report.totals import load, totals

DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "orders.csv")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path != "/report":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(totals(load(DATA))).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(os.environ.get("PORT", "8085"))), H).serve_forever()
