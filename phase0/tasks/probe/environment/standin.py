import json, http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        with open("/var/tmp/probe/req.jsonl","a") as f: f.write(json.dumps({"path":self.path})+"\n")
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
http.server.ThreadingHTTPServer(("127.0.0.1",8099),H).serve_forever()
