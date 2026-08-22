"""ONE ACRIS JOB AT A TIME — enforced, with a heartbeat, and it can WAIT.

⚠ WHY THIS EXISTS, ON TOP OF runlock.py. runlock was written after three
collisions where two processes wrote one ledger (787 documents arriving as
1,519 rows). It guards the WRITE side. Today's collision was different and
neither runlock nor anything else caught it:

    the map held 128 connections and had restarted ~25 times
    each restart abandoned its pool into TIME_WAIT
    1,076 sockets to :443 accumulated
    -> new SSL handshakes failed with UNEXPECTED_EOF_WHILE_READING
    -> the DEVR fetch could not connect AT ALL, while the map — already
       holding established connections — carried on at 278 maps/s

So the failure was a LOCAL RESOURCE, not ACRIS, and it was invisible from
either job's point of view. The map looked healthy. The fetch looked blocked by
the server. Neither was true.

⚠ AND IT PRESENTED AS A SERVER PROBLEM, WHICH IS THE DANGEROUS PART. The
obvious reading of "cannot connect to a836-acris.nyc.gov" is that ACRIS is
refusing — which is exactly what this project spent an hour concluding earlier
today, wrongly, about a missing cookie jar. A local socket exhaustion that
looks like a remote refusal will send you to the wrong place every time.

WHAT THIS DOES
    * one holder for the whole ACRIS host, across map and image jobs alike
    * heartbeat in a daemon thread, so a crash frees it within STALE seconds
    * WAIT rather than fail, so jobs queue instead of colliding
    * names the holder in the error, so "why is nothing happening" is answerable

⚠ IT DELIBERATELY COVERS BOTH ENDPOINTS. DocumentImageView and GetImage have
separate ACRIS budgets — proven, the map ran while images were refused — but
they share this machine's sockets. The constraint being protected here is
local, so the lock is local-wide.
"""
import os
import sys
import threading
import time

import runlock

SOURCE = "acris_http"
BEAT_EVERY = 45


class AcrisLock:
    def __init__(self, job, wait=True, timeout=None):
        self.job = job
        self.wait = wait
        self.timeout = timeout
        self.lock = runlock.Lock(SOURCE, f"{job}-{os.getpid()}")
        self._stop = threading.Event()
        self._t = None

    def __enter__(self):
        t0 = time.time()
        announced = False
        while True:
            try:
                self.lock.acquire()
                break
            except runlock.Held as e:
                if not self.wait:
                    raise
                if not announced:
                    print(f"  [{self.job}] waiting for the ACRIS lock — "
                          f"{str(e).splitlines()[0][:90]}", flush=True)
                    announced = True
                if self.timeout and time.time() - t0 > self.timeout:
                    raise
                time.sleep(10)
        # ⚠ BEAT IN A DAEMON THREAD. A lock whose holder forgets to beat looks
        # abandoned after STALE seconds and a sibling takes it — which is the
        # collision the lock was meant to prevent, arrived at politely.
        self._t = threading.Thread(target=self._beat, daemon=True)
        self._t.start()
        print(f"  [{self.job}] holds the ACRIS lock", flush=True)
        return self

    def _beat(self):
        while not self._stop.wait(BEAT_EVERY):
            try:
                self.lock.beat()
            except Exception:
                pass

    def __exit__(self, *exc):
        self._stop.set()
        self.lock.release()
        return False


def status():
    """Who holds it, and for how long."""
    s = runlock.status().get(SOURCE)
    if not s:
        return "ACRIS lock: free"
    return (f"ACRIS lock: {'HELD' if s['live'] else 'stale'} by "
            f"run {s.get('run_id')} pid {s.get('pid')} "
            f"(last beat {s['age']}s ago)")


def sockets_to_acris():
    """⚠ THE NUMBER THAT EXPLAINED TODAY'S FAILURE. Worth printing before a
    run: past ~1,000 sockets in TIME_WAIT, new TLS handshakes start failing
    and the error names the remote host, not the real cause."""
    try:
        import subprocess
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetTCPConnection -RemotePort 443 -EA SilentlyContinue "
             "| Measure-Object).Count"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return int(out or 0)
    except Exception:
        return -1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(status())
    n = sockets_to_acris()
    print(f"sockets to :443 = {n}"
          + ("   ⚠ high — new handshakes may fail" if n > 800 else ""))
