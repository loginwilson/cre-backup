# ACRIS acquisition — THE TRANSPORT

*Written 2026-08-27 after a night of Bandwidth Notices. This file exists
because the thing that decides whether ACRIS serves us is **not** the worker
count, and every tuning session that assumed otherwise reached a wrong answer.*

---

## THE RULE

> **Concurrency is a WARM-CONNECTION COUNT, not a HANDSHAKE RATE.**
> — `acris_lane.py`, and it is the whole finding.

A pooled client holding 28 warm sockets and a client opening 28 new TLS
connections per second look nothing alike to this server, even when they
fetch identical documents at an identical rate.

## HOW IT WAS FOUND

login, 2026-08-27 06:00, after four Bandwidth Notices in twelve hours:

> *"how did we do acris earlier on and how is our probe doing it? it should be
> using the minted links to just one time load the page, get, then next"*
> *"theres something we are doing different since we got to 80% but earlier
> days were fast without tripping"*

There was. The lane that reached ~75% (`acris_lane.py`) used a pooled
`requests.Session`. The lane running afterwards (`rd_walk.py`) used
`urllib.request.urlopen()` — **which does not pool** — so it opened a fresh
TCP + TLS connection for **every single document**.

    acris_lane @ 104.6 req/s  ->  ~20 handshakes total, then ~0/s   SUSTAINED
    rd_walk    @  24.3 docs/s ->  24.3 HANDSHAKES PER SECOND        notice @ 126 min
    rd_walk    @  11.8 docs/s ->  11.8 handshakes/s                 survived 4.9 h

**rd_walk at 24 documents/second opened more new connections per second than
acris_lane did at four times the request rate.**

## THE CONTROL

Richmond (`rc_lane.py`) pools — `pool_connections=4, pool_maxsize=max(8,
workers)` — reached **100%**, and `acris_lane`'s own notes record "proven 160
concurrent connections" there. The one source ever run at very high
concurrency without trouble is the one that reuses connections. Independent of
the ACRIS evidence, pointing the same way.

## WHO POOLS (audit 2026-08-27)

| module | transport |
|---|---|
| `rc_lane.py` | POOLED |
| `acris_lane.py` | POOLED (`pool_block=True`, hard ceiling) |
| `rd_walk.py` | POOLED — fixed 2026-08-27 |
| `acris_pdf.py` | **HOOK** — `FETCH = None`; pooled ONLY under `acris_lane` |
| `acris_edge.py` | **HOOK** — same |
| `image_walk.py` | COLD — its own `urlopen()` |
| `fetch_pages.py` | COLD |
| `live_delta.py` | COLD |

### ⚠ THE pdf CONSEQUENCE

`acris_pdf` and `acris_edge` are pooled **only when `acris_lane` injects
`one_at_a_time` into their `FETCH` hook**. Run standalone through
`image_walk.py` they open a connection per request — and **pdf costs ~12
requests per document**:

    image_walk @ 8 docs/s  ->  ~96 HANDSHAKES/SECOND
    rd_walk    @ 24 docs/s ->   24 handshakes/s  = a Bandwidth Notice in 2 hours

**So the pdf campaign runs through `acris_lane`, never through `image_walk`.**
That is a transport decision, not a worker-count decision — no "safe width"
fixes a 4x handshake rate. `C:\dev\cre_lanes_restore.py` had both
`image_walk` arms removed on 2026-08-27 for this reason.

## TWO CONTRACTS THE FIX MUST PRESERVE

Copied deliberately from `acris_lane.one_at_a_time`; both were paid for:

1. **RAISE `urllib.error.HTTPError` ON 4xx/5xx.** `urllib` raises; `requests`
   returns them as ordinary responses. Every refusal detector in this repo
   catches `HTTPError`, so a 503 arriving as a normal response parses as a
   blank page and the workers keep hammering a server that just refused us.
2. **`r.close()` in a `finally`, on EVERY path.** The CLOSE_WAIT deadlock of
   2026-08-24: ACRIS shed with 503s and closed its side; responses raised
   without closing left each socket in CLOSE_WAIT holding a pool slot until
   the pool was 100% dead connections, and `pool_block=True` then made every
   worker wait forever. *The failure was ours, not ACRIS's.*

## MEASURED, NOT ASSUMED

Local proof (localhost server, distinct client ports counted):
30 requests over 6 threads → **24 sockets unpooled vs 6 pooled**.

Production proof (live ACRIS, 60 s, ~1,500 documents):

    distinct sockets used : 58        (unpooled would need ~1,500)
    established, steady   : 28        = exactly the worker count
    CLOSE_WAIT            : 0

And it is **~50% faster at the same width** — 36–41 docs/s pooled against
23.5–25.3 unpooled. The handshake cost was showing up as latency all along.

## ⚠ UNRESOLVED — THE TEST WAS PAUSED AT 26 MINUTES

Pooled 28 workers ran 26 min with **0 refusals** before being paused for
travel. The baseline to beat is **126 minutes** (same width, unpooled). Two
theories still make opposite predictions:

- **BYTES/RATE** — the notice is about volume (it *is* called a Bandwidth
  Notice). Pooled runs faster, so it should trip **sooner**: ~83 min.
- **HANDSHAKE** — the metered thing is connections, cut ~96%, so it should run
  **far past** 126 min.

**Do not raise workers until this resolves.** If width and transport change
together, neither is measured. And pooling is not immunity: `lane_tempo.json`
records `refused: true` at 104.6 req/s — it buys headroom, not exemption.

## ⚠ A METHOD NOTE WORTH MORE THAN THE FINDING

Before this was found, a leaky-bucket model was fitted to two trip events
(refill 12.5 docs/s, bucket 89,208 docs) and used to recommend a worker count.
It fit well — because handshakes and documents were 1:1 in **every run
measured**. The confound was invisible precisely because it was perfect.

**A model fitted only over runs that share a hidden defect will describe the
defect, not the system.** The one run that should have falsified it (80
workers surviving 78 min against a predicted 59) was explained away as
measurement interference instead of prompting doubt about the variable itself.
