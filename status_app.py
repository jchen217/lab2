"""Classroom health-check app for a Linux guest on the lab network."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

READINESS_FILE = Path(__file__).with_name("dependency.ready")

DASHBOARD = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Lab Service Status</title>
<h1>Lab Service Status</h1>
<p id="status" role="status">Checking…</p>
<script>
async function updateStatus() {
    const status = document.getElementById("status");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);
    try {
        const response = await fetch("/ready", {
            cache: "no-store",
            signal: controller.signal
        });
        if (response.status === 200) {
            status.textContent = "Ready";
        } else if (response.status === 503) {
            status.textContent = "Not ready · HTTP 503";
        } else {
            status.textContent = "Unexpected response · HTTP " + response.status;
        }
    } catch {
        status.textContent = "Unreachable · readiness probe failed";
    } finally {
        clearTimeout(timeout);
        setTimeout(updateStatus, 3000);
    }
}
updateStatus();
</script>
"""


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.respond(200, "text/html", DASHBOARD)
        elif self.path == "/live":
            self.respond(200, "application/json", json.dumps({"live": True}))
        elif self.path == "/ready":
            ready = READINESS_FILE.is_file()
            self.respond(
                200 if ready else 503,
                "application/json",
                json.dumps({"ready": ready}),
            )
        else:
            self.respond(404, "text/plain", "Not found\n")

    def respond(self, status, content_type, body):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    with ThreadingHTTPServer(("0.0.0.0", 8080), StatusHandler) as server:
        server.serve_forever()
