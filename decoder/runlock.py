"""One decoder per source at a time. Enforced, not remembered.

⚠ THIS HAS NOW BITTEN THREE TIMES AND COST REAL WORK EACH TIME.

    DCP, twice: a corrected run started while the previous one was still alive,
    both appending to dcp_documents.jsonl. 787 distinct documents arrived as
    1,519 rows and I spent a round diagnosing it as an API defect before
    checking `run_id` and finding two writers.

    BSA, once: the previous SESSION's process survived the session ending. I
    deleted the ledgers and started a fresh run; the old process was still
    writing. Result — two run_ids in one ledger (2,213 rows + 10,779), 12,550
    decode records for 10,802 calendar numbers, and one torn line where two
    large appends interleaved.

    Every time, the symptom looked like a data problem. Every time it was two
    processes. The append-only sink survives concurrency BETWEEN sources by
    design; it was never meant to absorb two writers on the SAME source.

WHY A HEARTBEAT LOCK AND NOT A PID CHECK

    `os.kill(pid, 0)` is not a reliable liveness test on Windows, which is where
    this runs. A lock that cannot tell "alive" from "crashed" is worse than none
    — the first crash leaves a file that blocks every future run and gets
    deleted by hand, which trains you to delete it.

    So the lock carries a TIMESTAMP the holder refreshes as it works. A lock
    whose beat is older than STALE seconds is abandoned and may be taken. It
    self-heals after a crash, and it refuses a live sibling.
"""
import json, os, pathlib, time

DIR = pathlib.Path(os.environ.get("DECODER_SINK",
                                  pathlib.Path(__file__).with_name("sink"))) / "locks"
STALE = 180          # a run that has not beaten in 3 minutes is gone


class Held(Exception):
    """Another process owns this source right now."""


class Lock:
    def __init__(self, source, run_id):
        self.path = DIR / f"{source}.lock"
        self.source, self.run_id = source, run_id

    def _read(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def siblings(self, script):
        """Other live processes already running the same script.

        ⚠ THE LOCK CANNOT EVICT WHAT PREDATES IT. A DCP process started the day
        before the lock existed kept writing straight through two of my "single
        writer" runs — 40,700 ledger rows for a 32,931 queue and 59 torn lines
        before anyone noticed, because the lock only refuses NEW acquirers.

        A lock protects against the runs you start. This protects against the
        one you forgot was already going.
        """
        try:
            import subprocess
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                 "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=30).stdout
            rows = json.loads(out or "[]")
            if isinstance(rows, dict):
                rows = [rows]
            return [r["ProcessId"] for r in rows
                    if script in (r.get("CommandLine") or "")
                    and r["ProcessId"] != os.getpid()]
        except Exception:
            return []                      # never block a run on the check itself

    def acquire(self, force=False, script=None):
        if script:
            others = self.siblings(script)
            if others and not force:
                raise Held(
                    f"{script} is ALREADY RUNNING as pid(s) {others}. That "
                    f"process may predate this lock and will keep writing "
                    f"regardless of it — stop it before starting another, or "
                    f"you get two writers, duplicate ledger rows and torn "
                    f"lines. Pass force=True only if you know it is dead.")
        DIR.mkdir(parents=True, exist_ok=True)
        cur = self._read()
        if cur and not force:
            age = time.time() - (cur.get("beat") or 0)
            if age < STALE:
                raise Held(
                    f"{self.source} is already being decoded by pid "
                    f"{cur.get('pid')} run {cur.get('run_id')} "
                    f"(last beat {age:.0f}s ago). Two writers on one source is "
                    f"how 787 documents became 1,519 rows. Stop that run first, "
                    f"or wait {STALE - age:.0f}s for the lock to go stale.")
        self.beat()
        return self

    def beat(self):
        DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"source": self.source, "run_id": self.run_id, "pid": os.getpid(),
             "beat": time.time()}), encoding="utf-8")

    def release(self):
        try:
            cur = self._read()
            if cur and cur.get("pid") == os.getpid():
                self.path.unlink()
        except Exception:
            pass

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False


def status():
    if not DIR.exists():
        return {}
    out = {}
    for p in DIR.glob("*.lock"):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        r["age"] = round(time.time() - (r.get("beat") or 0))
        r["live"] = r["age"] < STALE
        out[p.stem] = r
    return out


if __name__ == "__main__":
    for src, r in sorted(status().items()):
        print(f"  {src:<6} {'LIVE ' if r['live'] else 'stale'} "
              f"pid {r.get('pid'):<8} run {r.get('run_id'):<20} "
              f"beat {r['age']}s ago")
    if not status():
        print("  no decoder holds a lock")
