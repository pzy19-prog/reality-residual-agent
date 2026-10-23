#!/usr/bin/env python3
"""Read-only JSON row server for one L3 REST source group."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--group", choices=("telemetry", "ops"), required=True)
p.add_argument("--directory", type=Path, required=True)
p.add_argument("--port", type=int, required=True)
a = p.parse_args()
names = ("observation_samples", "presence_events", "command_feedback") if a.group == "telemetry" else ("known_config", "ops_context")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        table = self.path.strip("/").split("/")[-1]
        if table not in names:
            self.send_error(404)
            return
        rows = [json.loads(line) for line in (a.directory / f"{table}.jsonl").read_text(encoding="utf-8").splitlines() if line]
        payload = json.dumps(rows, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *_):
        pass

HTTPServer(("0.0.0.0", a.port), Handler).serve_forever()
