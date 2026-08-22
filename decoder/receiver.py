"""LOCAL RECEIVER — the browser pulls, this writes.

    python receiver.py                 # listens on 127.0.0.1:877

WHY THIS EXISTS

    api-v6 refuses a headless client outright — 403 on the FIRST request, from
    Python, with a browser User-Agent. Not rate limiting: a bare client is not
    served at all. So the pull has to run inside the logged-in tab, and the tab
    has to get ~2.9M records out (41,817 buildings x ~69 listings each).

    Three ways out of a browser, and two are wrong here:

      hold it in memory, download once  ~2.9M records will not fit, and one
                                        crash costs the entire run
      POST straight to Supabase         needs the service_role key inside
                                        StreetEasy's page context, where any
                                        script on their page can read it. That
                                        key bypasses RLS on every table.
      POST to localhost  <- this        the key stays on this machine, nothing
                                        accumulates in the tab, and a crash
                                        costs one batch

⚠ IT WRITES TO DISK, NOT STRAIGHT TO SUPABASE. A batch that arrives is banked as
    a JSONL line before anything else can go wrong. Loading into Postgres is a
    separate, re-runnable step over a file that already exists — so a network
    hiccup at hour two costs a retry, not the harvest.

⚠ AND IT COUNTS. Every response states how many records have landed in total, so
    the browser side can print a running denominator instead of a number that
    only goes up.
"""
import json, os, pathlib, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OUT = pathlib.Path(__file__).with_name("leases_raw")
OUT.mkdir(parents=True, exist_ok=True)
PORT = int(os.environ.get("RECEIVER_PORT", "877"))

_lock = threading.Lock()
STATE = {"batches": 0, "records": 0, "buildings": 0, "started": time.time(),
         "errors": 0, "file": None}


def _path():
    if STATE["file"] is None:
        STATE["file"] = OUT / f"leases_{int(STATE['started'])}.jsonl"
    return STATE["file"]


class H(BaseHTTPRequestHandler):
    def _cors(self):
        # the page origin is streeteasy.com; this endpoint only ever accepts
        # from localhost so the allow-list is deliberately wide but the socket
        # is bound to 127.0.0.1
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # /slugs serves the worklist so the browser fetches it from here rather
        # than having 41,403 slugs injected through the debugger — and so a tab
        # crash costs nothing: re-open, re-fetch, resume from `done`.
        if self.path.startswith("/slugs"):
            keys = json.loads((pathlib.Path(__file__).with_name("buildings")
                               / "streeteasy-parcel-keys.json").read_text(encoding="utf-8"))
            # ⚠ RESUME IS AUTOMATIC, because the tab WILL die. Anything already
            # banked in leases_raw is excluded from the worklist, so re-opening
            # the tab and re-running picks up where it stopped instead of
            # re-pulling hours of history.
            done = set()
            for f in OUT.glob("leases_*.jsonl"):
                try:
                    with open(f, encoding="utf-8") as fh:
                        for line in fh:
                            i = line.find('"slug":"')
                            if i >= 0:
                                done.add(line[i + 8:line.find('"', i + 8)])
                except Exception:
                    pass
            work = [{"slug": r["slug"], "bbl": r["bbl"], "name": r.get("name")}
                    for r in keys if r.get("bbl") and r.get("slug")
                    and r["slug"] not in done]
            # ★ PRIORITY FIRST. api-v6 windows are scarce and cumulative, so the
            # order the worklist is served in decides what actually gets pulled
            # today. `priority.json` holds the BBLs that matter now; everything
            # else keeps its place behind them rather than being dropped.
            pri = pathlib.Path(__file__).with_name("buildings") / "priority.json"
            if pri.exists():
                want = set(json.loads(pri.read_text(encoding="utf-8")))
                work.sort(key=lambda w: 0 if w["bbl"] in want else 1)
                STATE["priority_pending"] = sum(1 for w in work if w["bbl"] in want)
            STATE["remaining"] = len(work)
            STATE["already_done"] = len(done)
            body = json.dumps(work).encode()
        else:
            body = json.dumps(STATE, default=str).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(n)
        try:
            body = json.loads(raw)
            rows = body.get("rows") or []
            with _lock:
                with open(_path(), "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps(r, separators=(",", ":")) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                STATE["batches"] += 1
                STATE["records"] += len(rows)
                STATE["buildings"] += int(body.get("buildings") or 0)
            ok = True
            msg = None
        except Exception as e:
            with _lock:
                STATE["errors"] += 1
            ok = False
            msg = f"{type(e).__name__}: {e}"
        self.send_response(200 if ok else 500)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        # the browser prints these, so it can show a denominator rather than a
        # number that only ever goes up
        self.wfile.write(json.dumps({"ok": ok, "error": msg,
                                     "records": STATE["records"],
                                     "buildings": STATE["buildings"],
                                     "batches": STATE["batches"]}).encode())

    def log_message(self, *a):
        pass          # one line per batch would drown the console


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"receiver on http://127.0.0.1:{PORT}  ->  {OUT}")
    print("  POST {buildings:n, rows:[...]}   ·   GET / for state")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print(f"\nstopped · {STATE['batches']:,} batches · {STATE['records']:,} records "
              f"· {STATE['buildings']:,} buildings -> {STATE['file']}")
