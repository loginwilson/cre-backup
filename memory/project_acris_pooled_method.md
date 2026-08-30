---
name: project-acris-pooled-method
description: "POOLED transport is the settled acris method (145min/28w/0 refusals vs unpooled notice at 126min); plus the two tests queued - worker ceiling, and ONE batch in then each worker to its own floor/job"
metadata: 
  node_type: memory
  type: project
  originSessionId: 36a502fe-953e-4ab9-ab0c-cd3194ce697c
  modified: 2026-08-27T16:21:26.598Z
---

## THE SETTLED METHOD: POOL THE CONNECTIONS

**Concurrency is a WARM-CONNECTION COUNT, not a handshake rate.** The wall we
kept hitting was cold TLS handshakes, not volume. `urllib.request.urlopen()`
does NOT pool; `requests.Session()` + `HTTPAdapter(pool_block=True)` does.

**PROVEN 2026-08-27** — same 28 workers, same corpus, only the transport
changed:

| run | outcome |
|---|---|
| UNPOOLED 28w | **Bandwidth Notice at 126 min** |
| POOLED 28w | **145 min, 183,489 docs, 21.2-21.7 docs/s, 83 fails, ZERO refusals, `.err` file never created** |

Verified earlier: 58 sockets vs ~1,500 for the same work, ~50% faster.
Ramp law still applies - stagger worker starts (0.5s), never cold-launch.

⚠ Modules still on the COLD path (unpooled) as of 2026-08-27:
`image_walk.py`, `fetch_pages.py`, `live_delta.py`. `acris_pdf.py` /
`acris_edge.py` need no change (they pool under `acris_lane`). Full writeup:
`decoder/docs/sources/acris/02-acquisition/transport.md`.

## TEST 1 — THE WORKER CEILING (queued, login's call)

*"max amount we can get through security in 1 batch"*

Prior measurement: at 60 workers throughput sat FLAT at ~42 docs/s while
LATENCY scaled with worker count (0.87s → 1.91s) = server-side concurrency
limit, extra workers just queue. Today's 28w ran 21.4/s - about half - and
per-worker rates match (1.3 vs 1.43 s/doc), so it likely scales ~linearly to
~60 workers then flattens.

**The falsifiable prediction worth testing: refusal tracks CONNECTION COUNT,
not volume.** If the notice fires on handshakes, pooled workers can go far
higher than unpooled before tripping anything, because steady-state handshake
rate is ~zero regardless of worker count.

Method: rungs 28 → 40 → 52 → 64, staggered start, 20 min per rung, **stop
where OUTPUT stops improving, never at a typed number** (see
[[project-acris-measured-ceiling]]).

## TEST 2 — ONE BATCH IN, THEN EACH TO ITS OWN FLOOR

*login: "can we enter 1 batch with various workers doing different tasks
(monitor, synchronization, rd, pdf)" ... "how to batch to get in and then each
go to their floor (job)"*

The building metaphor is the design: **ONE entry (one warm pool, one ramp, one
pacer), then each worker rides to its own floor** - monitor / sync / rd / pdf -
instead of four separate processes each opening its own front door.

Hypothesis: if acris meters CONNECTIONS, one shared pool across all job types
beats N_rd + N_pdf separate pools, because the total connection count is what
is counted. This is [[project-acris-access-shape]]'s "ONE access point" taken
to its conclusion.

⚠ **The countervailing force to design around: a pdf is a LARGE body, an rd is
a small one.** In a shared pool a slow multi-MB transfer occupies a connection
an rd fetch could have turned over ten times. So mixed pooling could RAISE the
refusal ceiling while LOWERING rd throughput. **Those are separable outcomes -
measure both, not just "did it get blocked".**

⚠ Also possible it buys nothing on the metering side: prior note says rd and
pdf hit SEPARATE server pools. That assumption is what the current two-process
design rests on, so testing it is worthwhile either way.

Both tests need the db settled first - schema changes cannot happen with lanes
in flight. See [[project-acris-consolidated-lane]], [[project-acris-ua-and-deadlock]].
