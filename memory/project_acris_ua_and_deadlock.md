---
name: project-acris-ua-and-deadlock
description: "2026-08-24 — the acris 503 wall was our User-Agent string, not a ban or a rate limit; and a CLOSE_WAIT connection leak deadlocked the lane at high throughput"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T22:52:16.177Z
---

**TWO SEPARATE FAULTS HIT AT 18:26 AND LOOKED LIKE ONE "ACRIS TRIPPED US".**
Neither was a trip. Both were ours. login diagnosed the second one from the
outside: *"why did it just fail, that shouldnt happen. it tells me its code
since acris is fully serving."*

## 1 · THE 503 WALL WAS THE USER-AGENT

MEASURED same IP, same second, one variable changed, on
`DocumentDetail?doc_id=2002122000001001`:

    ...Chrome/126.0.0.0 Safari/537.36   -> HTTP 503, 4,309 bytes, 3/3 attempts
    ...Chrome/126.0     Safari/537.36   -> HTTP 200, 118,445 bytes

Referer present or absent made **no difference**. 4-second spacing made **no
difference** — so it is NOT a rate limit and NOT an IP ban. acris's edge
discriminates on the version string itself. The lane had run ~166,000 requests
on the long form earlier the SAME DAY, so the rule appeared mid-day.

⚠ **I CALLED THIS A SERVER-WIDE REFUSAL AND STOPPED THE LANE. WRONG.** The
tell was in the data the whole time: **a refused client still SENDS.** Our
request counter was frozen at ~2/min (the probe alone). A ban produces fast
failures and a climbing counter; a frozen counter is a local deadlock. Read
the counter before naming the cause.

Fixed in `fetch_pages.py` (`UA`), which the acris lane's session uses.
⚠ Other files still define their own UA: `afetch.py`, `amap.py`, `docmap.py`,
`live_delta.py`, `ramp.py`, `ramp2.py`, `session_fetch.py` — **unfixed, and
they will 503 if run.** `acris_edge.py` uses an honest `acris-decoder/1.0`.

## 2 · THE CLOSE_WAIT POOL DEADLOCK (the real high-throughput bug)

`one_at_a_time` raised `HTTPError` on status >= 400 **without closing the
response.** Every 503 left its socket in CLOSE_WAIT still holding a pool slot.
netstat showed **exactly 24 CLOSE_WAIT against `--max-inflight 24`** — a pool
of 100% dead connections. `pool_block=True` then blocked every worker forever
on a connection that could never return, and because those 24 threads each
held an `inflight` permit, **no request could start either.**

⚠ **`TRANSPORT RECYCLED` CANNOT CLEAR THIS** — the blocked threads are waiting
on the OLD pool. Only a process restart recovers. That is why it recycled
twice and stayed frozen.

Three fixes, all in `acris_lane.py`:
1. `try: return _read(r, url) finally: r.close()` — closed on EVERY path,
   including the body-will-not-read path (55 fail rows had empty bodies —
   that was the leak running).
2. `err.acris_shed = r.status_code in (429,500,502,503,504)`, read at both
   fail sites. **503 used to be classed with 400 as an ordinary per-doc
   fail**, which is why the governor stepped 96.6 -> 100.6/s *while* acris
   was 503ing and the ready rate had already collapsed 6.57 -> 3.91/s.
3. `last_ok` stamped only on a REAL success. It used to be stamped before the
   status check, so a stream of 503s refreshed the liveness clock exactly
   like success — each failing probe retry (20s, 40s, 80s) reset the
   watchdog. **A socket that answers is not a server that serves.**
4. `pool_maxsize = max_inflight + 8` so a future leak degrades instead of
   deadlocking. ⚠ `pool_block` STAYS `True` — it is what prevents the cold-
   handshake stampede that tripped this server before.

Verified offline against fabricated 200/400/503/unreadable-503 responses — 12
guards, all fire — then live: the governor now COLLAPSES on a shed
(55.6 -> 22.2/s, hold 10 min) where before it climbed.

## ⚠ THE FALSE HIGH-WATER

`lane_tempo.json` held `{"rps":100.6,"best":100.6,"clean":true}` — 100.6 was
recorded CLEAN because the shed test could not see 503. A warm restart would
have resumed there and climbed straight back into it. **When a detector is
blind, every record it wrote while blind is suspect.** Corrected to
`best: 92.6` (the last rung that actually sustained, at the run's best ready
rate 6.57/s).

⚠ `WARM_MAX_AGE` is 6h and it checks the `at` field: writing `"at": 0` makes
the file read as ancient and the lane **cold-starts silently**. Stamp
`time.time()`.

See [[project-acris-consolidated-lane]], [[project-decoder-updates-board]].
