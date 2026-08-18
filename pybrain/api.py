"""api.py — HTTP-API rond de Brain (stdlib http.server, geen framework).
Server-authoritatief: alle RNG/economie draait hier. De Roblox-client (HttpService)
en test-scripts praten met dezelfde Brain-instantie.

Endpoints:
  GET  /health
  POST /join   {user, role?}
  GET  /scan?col&row
  GET  /parcel?col&row
  POST /dig    {user, col, row}
  POST /buy    {user, item}
  POST /plough {user, col, row, crop}
  POST /spray  {user, col, row, agent?, dose?}
  POST /fine   {cop, target, reason}
  GET  /state?user
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from schatveld_core import Brain, config

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
BRAIN = Brain(state_path=STATE_PATH)


def _int(qs, k, d=0):
    try:
        return int(qs.get(k, [d])[0])
    except (ValueError, TypeError):
        return d


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def log_message(self, *a):
        pass  # stil

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path == "/health":
            return self._send({"ok": True, "world": config.WORLD["name"],
                               "players": len(BRAIN.players)})
        if u.path == "/scan":
            return self._send({"blocks": BRAIN.scan(_int(qs, "col"), _int(qs, "row"))})
        if u.path == "/parcel":
            return self._send(BRAIN.parcel(_int(qs, "col"), _int(qs, "row")) or {})
        if u.path == "/state":
            return self._send(BRAIN.state(qs.get("user", ["?"])[0]))
        return self._send({"error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        d = self._body()
        try:
            if u.path == "/join":
                return self._send(BRAIN.join(d.get("user", "?"), d.get("role")))
            if u.path == "/dig":
                return self._send(BRAIN.dig(d["user"], int(d["col"]), int(d["row"])))
            if u.path == "/buy":
                return self._send(BRAIN.buy(d["user"], d["item"]))
            if u.path == "/plough":
                return self._send(BRAIN.plough(d["user"], int(d["col"]), int(d["row"]), d["crop"]))
            if u.path == "/spray":
                return self._send(BRAIN.spray(d["user"], int(d["col"]), int(d["row"]),
                                              d.get("agent", "Standaard"), int(d.get("dose", 1))))
            if u.path == "/fine":
                return self._send(BRAIN.fine(d["cop"], d["target"], d["reason"]))
        except (KeyError, ValueError) as e:
            return self._send({"error": f"bad request: {e}"}, 400)
        return self._send({"error": "not found"}, 404)


def serve(host="127.0.0.1", port=8791):
    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"[Schatveld API] http://{host}:{port}  (world {config.WORLD['name']})")
    srv.serve_forever()


if __name__ == "__main__":
    import sys
    serve(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8791)
