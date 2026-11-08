"""A small task API used as the reference product for /rspec:verify tests.

Run from tests/fixtures/reference-app: `python3 -m app --port 8765`. State is in memory; POST /api/reset clears it
(seeds call it first). Writes need `Authorization: Bearer member`. GET /api/stats is flaky on purpose: every second
call answers 503.
"""
import argparse, json, re, threading, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
STATE = {"tasks": {}, "next": 1, "stats_calls": 0}


def reset():
    # stats_calls survives a reset: the flakiness belongs to the build, not to the seeded data
    STATE.update(tasks={}, next=1)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body=None):
        data = b"" if body is None else json.dumps(body).encode("utf-8")
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def member(self):
        return self.headers.get("Authorization", "") == "Bearer member"

    def do_GET(self):
        with LOCK:
            if self.path == "/api/tasks":
                items = list(STATE["tasks"].values())
                return self.reply(200, {"count": len(items), "items": items})
            m = re.fullmatch(r"/api/tasks/([^/]+)", self.path)
            if m:
                task = STATE["tasks"].get(m.group(1))
                return self.reply(200, task) if task else self.reply(404, {"error": "not found"})
            if self.path == "/api/stats":
                STATE["stats_calls"] += 1
                if STATE["stats_calls"] % 2 == 0:
                    return self.reply(503, {"error": "busy"})
                return self.reply(200, {"count": len(STATE["tasks"])})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self.reply(400, {"error": "not JSON"})
        with LOCK:
            if self.path == "/api/reset":
                reset()
                return self.reply(204)
            if self.path == "/api/tasks":
                if not self.member():
                    return self.reply(401, {"error": "sign in"})
                title = str(body.get("title") or "").strip()
                if not title:
                    return self.reply(422, {"error": "title required"})
                task = {"id": str(uuid.uuid4()), "key": "TSK-%d" % STATE["next"], "title": title}
                STATE["next"] += 1
                STATE["tasks"][task["id"]] = task
                return self.reply(201, task)
        self.reply(404, {"error": "not found"})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8765)
    port = p.parse_args().port
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("listening on %d" % server.server_address[1], flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
