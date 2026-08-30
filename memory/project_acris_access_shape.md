---
name: project-acris-access-shape
description: "Why acris reached 75% fast without tripping - it is the SHAPE of departures (paced metronome, one access point, ramped) not the rate; rd_walk is structurally bursty"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5d1473bc-bb54-490c-8d66-326f7b72067b
  modified: 2026-08-29T16:54:59.448Z
---

**IT IS NOT THE RATE. IT IS THE BURST.** login asked the right question
2026-08-26 23:00: *"understand how we got to 75% in the first place... most was
in a massive continuous process, whereas what we do now is super fragmented."*

    PACED   acris_lane.py   104.6 req/s   one departure every 9.6 ms, EVENLY
    BURSTY  rd_walk.py       12 workers   up to 12 in flight at once
                             28 workers   up to 28   <- 503'd in 6 min, 08-26
                             80 workers   up to 80
                           4x28 arms      up to 112  <- REFUSED twice

**THE FASTER CONFIG WAS THE SAFER ONE.** 104.6/s paced sustained fine; ~48/s
in clumps of 28 got 503'd. ACRIS meters CLUMPS, not volume.

The mechanism, from acris_lane's pacer: *"Reserving a slot makes spacing a
PROPERTY OF THE SCHEDULE rather than a side effect of how busy the wire
happened to be. Burst capacity is exactly 1, at any latency, after any idle."*

## THE THREE THINGS rd_walk STRUCTURALLY LACKS

1 **A PACER.** N workers each loop as fast as they can, so burst capacity IS
  N and they re-synchronise whenever latency dips.
2 **A RAMP.** acris_lane staggers rd workers 0.5s apart and climbs pdf width
  from a floor. rd_walk does `for t in threads: t.start()` - every TLS
  handshake in the same instant. ⚠ login's header: ACRIS served its Bandwidth
  Notice ONE SECOND after exactly such a relaunch (trip #3), after absorbing a
  governor's gentle climb to width 52 all morning without complaint.
3 **WARM RESUME.** The governor banks its earned tempo (lane_tempo.json) and
  resumes at 60%, because re-climbing costs 2+ hours. login: *"a loss in
  connection would kill a ton of progress on ramp up speed."* The file itself
  says this is *"what made 'just restart it' an unaffordable answer to any
  problem."*

## ⚠ AND ONE ACCESS POINT, NOT SEVERAL

login's theory, in acris_lane's header: *"ACRIS tripped its Bandwidth Notice
twice while the edge-prober and the doc-walkers ran as SEPARATE python
processes - two behaviors under one IP. ACRIS tolerates ONE access point that
maximizes workers, not multiple access points."*

## ⚠⚠ I COLD-LAUNCHED rd_walk FOUR TIMES ON 2026-08-26 (80, 80, 28, 12)

Each one a stampede of simultaneous handshakes; the 22:07 503 came 6 minutes
after the 28-worker cold launch. **I treated restarts as free while the design
notes call them the most expensive event in the system.** Before restarting an
acris lane, ask what the START costs, not just what the RATE will be.

## OPEN, FOR TOMORROW

⚠ lane_tempo.json reads `{"rps":104.6,"best":104.6,"clean":true,
"refused":true}` - clean AND refused both true, which should be impossible.
Warm resume keys off `clean`, so a restart could resume HOT into a server that
pushed back. Resolve before bringing acris_lane back.

acris_lane is PAUSED in fleet.py (PAUSED={"acris_lane"}). The tool that earned
75% is idle while the bursty one runs. See
[[project-acris-consolidated-lane]], [[project-acris-measured-ceiling]].

## ⚠⚠ THE ACTUAL DEFECT: A COLD TLS HANDSHAKE PER DOCUMENT (found 2026-08-27 06:05)

login asked the question that found it: *"how did we do acris earlier on and
how is our probe doing it? it should be using the minted links to just one
time load the page, get, then next"* and *"theres something we are doing
different since we got to 80% but earlier days were fast without tripping."*

    rd_walk.py     urllib.request.urlopen(req) PER DOCUMENT  -> NO POOLING.
                   A brand new TCP + TLS handshake for EVERY document.
    acris_lane.py  requests.Session() + HTTPAdapter(pool_maxsize=N,
                   pool_block=True)  -> pooled, keep-alive, REUSED.

    acris_lane @ 104.6 req/s  ->  ~20 handshakes total, then ~0/s   SUSTAINED
    rd_walk    @  24.3 docs/s ->  24.3 HANDSHAKES PER SECOND        notice @2h
    rd_walk    @  11.8 docs/s ->  11.8 handshakes/s                 survived 4.9h

**rd_walk at 24 docs/s opened MORE new connections per second than acris_lane
did at FOUR TIMES the request rate.** acris_lane's own note states the rule:
*"Concurrency is now a WARM-CONNECTION COUNT, NOT A HANDSHAKE RATE - which is
what makes raising it safe."*

⚠ **SO MY LEAKY-BUCKET MODEL NAMED THE WRONG VARIABLE.** I fitted refill=12.5
docs/s, bucket=89,208 docs from two trip events. It fit the symptom because
handshakes and documents were 1:1 in every run I measured - the confound was
invisible precisely because it was perfect. **A model fitted only over runs
that share a hidden defect will describe the defect, not the system.** The one
run that should have falsified it (80w surviving 78 min when it predicted 59)
I explained away as diagnostic interference instead of doubting the variable.

FIXED in rd_walk.py: `_new_session()` + `_get()` mirroring acris_lane -
pool_connections=1, pool_maxsize=workers+8, pool_block=True (a HARD ceiling),
max_retries=0. Two contracts preserved deliberately:
  - **RAISES urllib.error.HTTPError on 4xx/5xx.** requests returns those as
    ordinary responses; every refusal detector here catches HTTPError, so a
    503 as a normal response would parse as a blank page and the workers
    would hammer on.
  - **r.close() in a finally on EVERY path** - the CLOSE_WAIT deadlock of
    08-24, where unclosed shed responses held pool slots until the pool was
    100% dead and pool_block made every worker wait forever.

PROVED LOCALLY before touching acris (localhost server, counted distinct
client ports): 30 requests over 6 threads -> **24 sockets unpooled vs 6
pooled**, one per worker, reused. At real scale a 2-hour 24/s run goes from
~172,800 handshakes to ~20.

NEXT: 28 workers pooled, as a controlled A/B against the 28-worker UNPOOLED
run that took a notice at 126 min. Same width, only the transport differs.

## THE FETCH-HOOK AUDIT - WHO POOLS AND WHO DOES NOT (2026-08-27 06:35)

    rc_lane.py     POOLED   pool_connections=4, pool_maxsize=max(8,workers)
    acris_lane.py  POOLED   pool_maxsize=max_inflight+8, pool_block=True
    rd_walk.py     POOLED   (fixed 2026-08-27)
    image_walk.py  COLD     its own urlopen() at line 155
    acris_pdf.py   HOOK     `FETCH = None` - pooled ONLY when acris_lane sets it
    acris_edge.py  HOOK     `FETCH = None` - same
    fetch_pages.py COLD     urlopen()
    live_delta.py  COLD     urlopen()

⚠⚠ **acris_pdf AND acris_edge ARE POOLED ONLY WHEN DRIVEN BY acris_lane**,
which injects `one_at_a_time` into their FETCH hook (`AP.FETCH = ...`,
`AE.FETCH = ...`). Standalone via image_walk.py they open a connection per
request. **AND pdf IS ~12 REQUESTS PER DOCUMENT:**

    image_walk @ 8 docs/s   ->  ~96 HANDSHAKES/SECOND
    rd_walk    @ 24 docs/s  ->   24 handshakes/s   = notice in 2 hours

So the pdf campaign must run through **acris_lane, NEVER image_walk** - that
is a transport decision, not a worker-count decision. Picking a "safe" width
for image_walk cannot fix a 4x handshake rate.

## ⚠ RICHMOND IS THE CONTROL THAT CORROBORATES ALL OF IT

rc_lane POOLS, and richmond reached 100% without ever tripping - acris_lane's
own comment records "proven 160 concurrent connections" there. **The one
source we ran at very high concurrency without trouble is the one that reuses
connections.** Independent of the acris evidence, and it points the same way:

    rc_lane    pooled    160 concurrent     never tripped
    acris_lane pooled    104.6 req/s        sustained
    rd_walk    UNPOOLED   24 handshakes/s   notice at 2 hrs

## THE POOLED A/B - PAUSED MID-TEST 2026-08-27 07:33, RESUME AT THE OFFICE

    UNPOOLED 28 workers   23.5 -> 25.3 docs/s   NOTICE at 126 min
    POOLED   28 workers   41.0 -> 35.8 docs/s   0 refusals at 26 min (PAUSED)

**Pooling is ~50% FASTER at the identical width** - the handshake cost was
showing up as latency, not just as a trip risk. Verified in production by
socket count: over 60s and ~1,500 documents the process used **58 distinct
sockets** (28 established, steady) where unpooled would need ~1,500.
CLOSE_WAIT was 0, so the finally: r.close() holds.

⚠ THE TEST IS UNFINISHED AND IT IS A DISCRIMINATING ONE. Two live theories
predict OPPOSITE outcomes - resume at 28 workers and let it run:

    BYTES/RATE theory   the notice is about volume (it IS a "Bandwidth"
                        Notice). Pooled runs 37 docs/s vs unpooled 24,
                        so it should trip SOONER: 126 x (24/37) = ~83 min.
    HANDSHAKE theory    the metered thing is new connections, cut ~96%,
                        so it should run FAR PAST 126 min.

⚠ **DO NOT RAISE WORKERS UNTIL THIS RESOLVES.** If we bump to 40/64 now and it
survives, we cannot tell whether pooling or the width bought it. Raise workers
as the NEXT single-variable step - and note acris_lane's tempo file records
`refused: true` at 104.6 req/s, so pooling is not immunity, only headroom.

STATE AT PAUSE: rd 17,310,267 / 21,617,307 = **80.08%**. ACRIS recovery
measured twice: 81 min (05:45->07:06) and ~84 min (08-24 03:45->05:09).
Restore with C:\dev\cre_lanes_restore.cmd - updated 08-27 to rd 28 pooled with
BOTH image_walk arms removed (standalone image_walk is the cold path).

## ⚠⚠ RESOLVED 2026-08-29: A DOOR IS A *PROCESS*, AND SHARDING MAKES MORE

The A/B above is settled, and by an expensive route. To beat the GIL I split
registration into four PROCESSES over disjoint id ranges (reg_a..reg_d). It
was fast - **61 docs/s aggregate, zero fails**. But each process opens its own
pooled session, so the approved THREE-door design silently became SIX, and
five were live when ACRIS served the notice at 12:23 (three shards took it
independently, at three different ids, within 0.9 min of entry).

    4 shards x 28w  =  61 docs/s   REFUSED 2026-08-29 12:23
    1 door  x 40w   =  32 docs/s   clean, no refusal   <- the approved shape

login: *"the shards are what killed it."* **Pooling made concurrency a warm-
connection count; it did NOT make PROCESSES free.** One session per floor is
the whole contract - splitting a floor for throughput spends the exact
currency ACRIS meters. If both are ever wanted, the shape is ONE session in a
parent process fanning raw HTML to child processes for PARSING, never more
sessions.

⚠ **AND MY ~11 docs/s "GIL CEILING" WAS WRONG - measured on the wrong band.**
I told login one process could not exceed ~11/s and to expect that. It does
**32/s**. The 11 came from DIGITAL-era pages (~118 KB); film-band records are
compact and parse far cheaper. *A ceiling measured on one band is not a
ceiling on another.* One door never cost us speed - four doors cost us access.

⚠ **STOP-ON-REFUSAL STOPS PROCESSES; NOTHING STOPS THE RESPAWNER.** CRE Fleet
Guard (schtask, every 5 min, `fleet.py start all`) restarted the shards INTO
the live notice at 12:24, 12:29, 12:34. The restart loop IS a retry, and the
notice names "automated scripts" as a trigger. A refusal hold is not complete
until the guard AND the scheduled tasks are handled - `ACRIS-MapDelta-Daily`
was still armed for 04:00 and had to be disabled too. See
[[feedback-guarded-roster-edit-order]].

⚠ **WHEN A HOLD IS ON, THE SOURCE'S STATE IS LOGIN'S TO CHECK, NOT OURS TO
SAMPLE.** Do not probe to test whether a ban lifted. Today's resume came from
login looking directly ("acris is open right now") - that is the pattern.
