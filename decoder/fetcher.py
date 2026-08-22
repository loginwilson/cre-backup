"""A fetch pool that lets the HOST set the rate, instead of a constant guessed
in advance.

THE MEASUREMENT THAT PROMPTED THIS

    s-media.nyc.gov serves an LPC permit in a median 0.26 s, 69 KB. The decoder
    slept 1.5 s between fetches, so it spent 83% of a 53-hour sweep asleep. The
    1.5 s was not measured — it was picked because the host publishes no crawl
    policy and slow felt safer than sorry.

    Slow is not the same as considerate. A fixed sleep is deferential to a
    number I invented and completely deaf to the server: it keeps hammering at
    exactly the same rate while the host is failing, and it keeps crawling at
    exactly the same rate while the host is idle. The polite thing and the fast
    thing are the same thing — WATCH THE HOST AND REACT.

HOW THIS BEHAVES

    A token bucket sets a target rate shared by N workers, and the rate moves
    the way TCP moves: additive increase, multiplicative decrease.

        every clean response      rate += a little, up to a stated ceiling
        429 / 503 / any 5xx       rate HALVED, immediately, and the request
                                  is retried after a backoff
        latency drifts upward     rate halved — a host that is slowing down is
                                  telling you something before it starts
                                  refusing
        repeated refusals         the pool STOPS. It does not grind on.

    So the ceiling is a permission, not a target. On a host that is happy the
    sweep converges to it; on a host under strain it retreats without anyone
    watching, which a fixed sleep can never do.

⚠ NOT FOR ACRIS. That endpoint is rate-limited by policy and is deliberately
  excluded — going faster there is how this project got blocked once already.
"""
import queue, threading, time, urllib.error, urllib.request


class Governor:
    """Shared, self-adjusting rate limit. Thread-safe."""

    def __init__(self, start=1.0, ceiling=3.0, floor=0.2):
        self.rate = float(start)          # requests per second
        self.ceiling, self.floor = float(ceiling), float(floor)
        self._lock = threading.Lock()
        self._next = time.monotonic()
        self._base_latency = None
        self.refusals = 0
        self.stopped = False

    def wait(self):
        """Block until this caller may issue its request."""
        while True:
            with self._lock:
                now = time.monotonic()
                gap = 1.0 / max(self.rate, 1e-6)
                if now >= self._next:
                    self._next = max(now, self._next) + gap
                    return
                sleep_for = self._next - now
            time.sleep(min(sleep_for, 0.5))

    def ok(self, latency):
        with self._lock:
            if self._base_latency is None:
                self._base_latency = latency
            else:
                self._base_latency = 0.9 * self._base_latency + 0.1 * latency
            # a host that is slowing is asking for room before it starts saying no
            if latency > max(3 * self._base_latency, 2.0):
                self.rate = max(self.floor, self.rate / 2)
            else:
                self.rate = min(self.ceiling, self.rate + 0.05)
            self.refusals = 0

    def refused(self, code=None):
        with self._lock:
            self.rate = max(self.floor, self.rate / 2)
            self.refusals += 1
            if self.refusals >= 8:
                self.stopped = True
        return self.stopped


RETRYABLE = {429, 500, 502, 503, 504}


def fetch_many(items, url_of, on_result, ua, workers=3, governor=None,
               attempts=4, timeout=90, skip=None):
    """Fetch `items` concurrently under one governor.

    `on_result(item, body, status)` is called from a worker thread with exactly
    one of: bytes, or None plus a status string. It must be cheap and
    thread-safe — do the parsing in it only if the parse is fast, otherwise
    queue the bytes.
    """
    gov = governor or Governor()
    q = queue.Queue()
    for it in items:
        q.put(it)
    lock = threading.Lock()
    counts = {"ok": 0, "skipped": 0, "failed": 0, "retried": 0}

    def worker():
        while not gov.stopped:
            try:
                it = q.get_nowait()
            except queue.Empty:
                return
            try:
                if skip and skip(it):
                    with lock:
                        counts["skipped"] += 1
                    on_result(it, None, "cached")
                    continue
                url = url_of(it)
                body, status = None, "FAILED"
                for n in range(attempts):
                    if gov.stopped:
                        break
                    gov.wait()
                    t0 = time.monotonic()
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": ua})
                        with urllib.request.urlopen(req, timeout=timeout) as r:
                            body = r.read()
                        gov.ok(time.monotonic() - t0)
                        status = "fetched"
                        break
                    except urllib.error.HTTPError as e:
                        if e.code in RETRYABLE:
                            gov.refused(e.code)
                            with lock:
                                counts["retried"] += 1
                            time.sleep(min(2 ** n, 30))
                            continue
                        status = f"HTTP {e.code}"     # 404/403 is an answer
                        break
                    except Exception as e:
                        gov.refused()
                        with lock:
                            counts["retried"] += 1
                        status = f"{type(e).__name__}"
                        time.sleep(min(2 ** n, 30))
                with lock:
                    counts["ok" if body else "failed"] += 1
                on_result(it, body, status)
            finally:
                q.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    counts["final_rate"] = round(gov.rate, 2)
    counts["stopped_by_refusals"] = gov.stopped
    return counts
