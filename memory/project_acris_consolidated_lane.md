---
name: project-acris-consolidated-lane
description: acris_lane.py = ALL of acris in one process (edge+rd+pdf+key); ready=needed−pdf_todo; freshness clause; scaling plan for <30-day target
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T18:50:57.584Z
---

**THE TWO ACCESS RULES (login's naming, 2026-08-24):** every source gets an
access constitution read from its measured behavior. **PIANO RULE** (acris):
one player — a single access point carefully sequencing organs (10s edge
reservation, pools as fingers) because the source trips on multiple
presences. **DRUMROLL RULE** (richmond): maximum independent hits, no
coordination needed (proven 160 concurrent connections clean) — the only
law is don't drop the sticks (stop-on-refusal). Both still ONE LANE (one
process, one governor, one ready row, one refusal tripwire); the rule sets
the time signature, not the shape.

**THE CONSOLIDATED ACRIS LANE (cut over 2026-08-24 ~10:12).** `acris_lane.py`
(decoder dir) is the ONLY process allowed to touch ACRIS — login's piano rule:
"one access at a time... a super concise machine playing piano." Four organs,
one process: edge probe (10s reservation, walk-on-hit, rd arrives IN the probe
request) · rd backfill (28 workers, ix_nav_rd_todo) · pdf pool (20 workers,
trailing feeder + HOT LIST — sync landings jump the queue; new filing fully
ready in ~1 min, proven 10:08) · keying (key_on_rd trigger, no process).
Launch: `python fleet.py start sync` or
`python acris_lane.py --apply --workers 28 --pdf-workers 20`, stdout →
NAV_WORK\acris_lane.log. Retired: acris_live, rd_walk×4, image_walk×3 —
starting any beside the lane recreates the tripping condition.

**⚠⚠ THE FLAG LESSON (trips #3-#4, 13:03-13:50 — login's read, correct):**
a notice CLEARING is not the flag clearing. After 13:03's cold-start notice,
service resumed at HALF SPEED (rd 12.8/s vs 25-30 at unchanged width, both
endpoints, zero errors, CPU idle) — that IS the tripped state still live,
and running traffic through it keeps the flag warm; every relaunch (even
ramped) re-knocks a flagged IP with fresh handshakes and re-aggravates.
Result: notice #4 against width-8 traffic. ⚠ CORRECTED 14:10 (login was right: "they only block and serve"): the
"half-service flag" was DISPROVEN — the real cause was the CONNECTION'S
LATENCY at 228ms (vs ~20 normal; measured Cloudflare ping + speedtest,
identical on two wifi networks, bandwidth healthy at 50Mbps parallel).
At 228ms RTT, 28 rd workers arithmetically = 12.8/s — no throttle
involved. ACRIS has exactly two states: SERVE and BLOCK (Bandwidth
Notice). Diagnostic law: measure PING before theorizing server behavior —
single-stream speed & per-worker rates are latency-priced, and width
FIGHTS latency (more in-flight covers travel time). **RESUME PROTOCOL: notice →
FULL SILENCE (kill the lane, probe included, hours not minutes) → single
probe → if clean, tiny test pool 10 min reading PER-WORKER rd rate (~1.0
doc/s/worker = clear · ~0.5 = still flagged → silence again, longer) →
only then the ramp.** Never run half-speed traffic thinking it's warm-up,
and never diagnose "slow" without a neutral-host pipe test first — 13:49's
1.2MB/s pipe turned out to be OneDrive.Sync churning on the decoder folder
(Downloads IS synced; rc logs write there constantly — move logs off
synced paths; same lesson as bkrea's C:\dev move).

**⚠⚠ THE SETTLED DIAGNOSIS — CONVERGENCE, NOT VOLUME (login, after trip #5,
2026-08-24):** "acris trips when multiple requests come in simultaneously so
it needs to sequentially orchestrate... its not the number of requests, its
the overlap when they converge that tells them to block." The rd pool, the
pdf pool and the edge walk must NEVER touch the wire at the same instant.
This resolves the day's paradox: width 52 ran clean for 4 morning hours but
width 32 tripped in 18 min at 14:39 — because the VPN's 228ms latency had
been SPACING our arrivals; at 8ms the same workers cycled ~3x faster and
arrivals bunched into near-simultaneous clusters. Fewer workers, sharper
convergence, faster trip. A "clean climb" on a slow line proves nothing
about a fast one.
**THE BUILD:** acris_lane holds ONE requests.Session with pool_maxsize=1 and
a semaphore of `--max-inflight` (default 1); `one_at_a_time()` is the single
voice and acris_pdf.FETCH is injected with it, so rd + pdf maps + pdf pages
+ probe all take strict turns down one kept-alive connection (no per-request
TLS handshake either). Workers stay parallel for LOCAL work only (parse,
img2pdf, db). `--max-rps` (Tempo token bucket) states pace directly since
worker count stopped controlling rate. Richmond EXEMPT — drumroll rule.
⚠ acris_edge's probe still uses its own connection (passes the gate, so
never converges) — unify if zero exceptions are wanted.

**⚠⚠ THE RAMP LAW (trip #3, 13:03):** NEVER cold-launch — a restart firing
~80 workers at once = 80 cold TLS opens in one second = Bandwidth Notice
ONE SECOND after launch, after the governor's gentle climb to 52 ran clean
ALL DAY. The lane now self-ramps unavoidably (pdf width 8 +4/30s to
target; rd staggered 0.5s) — never add a bypass, and RESTARTS THEMSELVES
ARE LOAD EVENTS: minimize them (tuning belongs to the governor). Sustained
width was never the tripper — the stampede was. Also: governor announces
each width's settled avg at every step (--step-minutes 10 windows, login's
call); measured that day: w48 ~5.4/s · w50 ~6.2/s (peak 7.5).

**FRESHNESS CLAUSE:** TotalPages≤0 on a doc recorded within --fresh-days (30)
= DEFERRED (pdf stays '', feeder wrap retries), never `imageless` — scan lag
is not a verdict. Only aged docs earn `imageless`.

**READY = needed − pdf_todo** (exact: pdf only ever follows rd;
ix_nav_pdf_todo index-only). Board sync acris row = (ready, ledger total);
rate keys off the lane's "PDF PROGRESS N pdfs · M imageless" line (ready-docs,
one subtraction for rate+increase). rd detail = "N total" line + hidden acq rd
row. ONE refusal tripwire stills BOTH pools; probe continues as resume
detector; resume = login's call.

**THE GOVERNOR (built 10:26):** pdf width is SELF-TUNED against the server's
shed signal (Short/timeout = load-shedding, distinct from blocks): shedding
minute (≥3) → width ×0.75, hold 10 min; 5 clean minutes → +2 up to
--pdf-max 48; rd feeder draining → +8 immediately (rd's budget reallocated —
login: "the intelligence needs to know once rd finishes it can allocate more
to pdf and live sync"). Workers idle above pdf_width[0]; refusal still
stills everything. Per-worker rate ≈ fleet parity (0.15/s); 6-8/s needs
~40-55 workers — governor finds what the server bears, day vs night.

**LANDED=READY VERIFIED BY SAMPLE (10:29):** 314/314 pdf-done rows carry
their pass-1 key (covered 2003 band + hot band) — 0% unkeyed, and by
construction new rows key before pdf (trigger fires on rd, pdf follows rd).
FT_ film band: 0 pdfs yet — film completes ~3.6x docs/page (tilt lever,
front-loads doc-count without moving the page-bound 100% date).

**<30-day target** (login): ~19.9M pdfs left needs ≥7.7 ready/s sustained;
measured image-backend ceiling ~6-8/s aggregate (worker-independent). Plan:
governor climbs (CPU was 43% of one core), rd closes (~2 days) → +budget,
ProcessPool-offload img2pdf/md5 if GIL pins first. Next: rc_lane for
richmond AFTER its pdf trio levels (~1.5 days; login 10:28 — no urgency,
richmond never tripped) → pure 2-row board. See
[[project-decoder-updates-board]], [[project-decoder-fleet-restore]],
[[project-acris-refusal-20260824]].

**THE PASS MODEL — SYNC CARRIES ACRIS THROUGH PASS 2 (login 2026-08-24):**
"doc id, urls, rd, pass 1, pdf, repeat until 100%, pass 2, reach 100%, now
extraction" · "acris synchronization takes care of everything from sync all
the way up through pass 2 basically" · "the percentage now is based on
achieving pass 1."

    pass 1  the parcel key an rd row assigns BY ITSELF (key_on_rd trigger,
            free, inside rd's transaction). ⚠ THE SYNC PERCENTAGE COUNTS
            THIS — READY = id + urls + rd + pass-1 key + pdf|imageless.
    pass 2  the docs pass 1 could NOT give a BBL, keyed from REFERENCES
            that tie a bbl to a doc. Local work off rd data, zero ACRIS
            requests — but gated on sync 100%, because a reference into a
            doc that has not landed yet resolves to nothing.
    pass 3  extraction.

⚠ **DO NOT RE-GATE PASS 2 ON rd ALONE.** 2026-08-24 the arm read "acris rd
8.10%" against ~75% actual rd and I started patching it to measure rd
directly — reasoning that reference keying needs no images so it shouldn't
wait on them. Sound reasoning, wrong premise: **pass 2 waits on ROW
COMPLETION, not on its own input being available.** org_backfill_arm.py now
gates on the board's `synchronization|acris` row and says so in its
docstring.

**⚠ THE VERIFY SWEEP FREEZES THE GOVERNOR (measured 15:37–15:45).** The
governor climbs on `shed == 0 and landed > 0`, where landed = pdfs +
imageless. Re-confirmations book to a separate `verified` counter (added so
the ready rate stays honest) — so a verify-only workload makes landed 0
EVERY minute, the clean-minute streak resets every minute, and the tempo can
never step. Symptom: 2,645 verified / 52 pdfs / 0.1 ready/s, pinned at the
12/s launch cap with zero sheds. The sweep is resumable (`_verify_cursor.txt`),
so it yields the wire and resumes later. **An honest counter that a control
loop does not read is a control loop that cannot see its own progress.**

**REQUESTS PER READY ROW = ~8.2, MEASURED.** 6.18 pages/doc (400 pdfs sampled
across 80 year-dirs) + 1 map + 1 rd. So the <30-day target's 8 ready/s needs
**~66 req/s sustained** — under the 80 rps ceiling, and well under the old
sharded fleet's measured ~140/s aggregate, but ~8x the 8.5/s the piano lane
was holding. That is the number the ceiling hunt is hunting.

**⚠⚠ WHAT ACTUALLY BROKE PIANO (found 2026-08-24, two defects, both fixed).**
login: "I thought the piano approach fixed it and it had worked a very long
time and then something happened that broke it." It did work — and then two
things silently turned the piano back into a drum:

**1 · Tempo was a BUCKET, not a pacer.** `tokens = min(self.rps, ...)` banked
a FULL SECOND of beats. After any idle stretch (img2pdf on a long doc, a
batch of db writes) every worker's saved-up token was playable at once.
MEASURED, no network: after 1.2 s idle at 20/s, the old bucket let **16 of 16
threads fire instantly with zero spacing**; the pacer holds every gap at
48.6–50.6 ms against a 50 ms target, 0 bursts. Average rate identical — the
rate is what we were watching, and the rate looked clean.
⚠ THIS IS ALSO WHY IT WORKED FOR SO LONG: the 228 ms VPN kept the wire
permanently busy so tokens never banked. Faster line → workers idle during
local work → tokens bank → chords. Same settings, same req/s, new failure.
FIX: reserve the next departure slot (`next_at = due + 1/rps`) and sleep to
it. Burst capacity is exactly 1 at any latency, after any idle.

**2 · `pool_maxsize=1` + `--max-inflight 16` = A COLD-HANDSHAKE GENERATOR.**
urllib3's `block` defaults to **False**: one request takes the pooled
connection, the other 15 call `_new_conn()` (fresh TLS each) and are
DISCARDED on release because the pool is full. Continuously. The lane's own
docstring claim — "one kept-alive connection, what a browser looks like" —
was only true at `--max-inflight 1`; every metered config since was minting
and burning ~15 cold connections per cycle, which is precisely the stampede
signature that trips this server ("160 cold TLS opens in one instant").
FIX: `pool_maxsize=a.max_inflight, pool_block=True` — the pool is a HARD
ceiling and concurrency becomes a WARM-CONNECTION COUNT, not a handshake
rate. Combined with the pacer, connections are also born evenly spaced
(83 ms apart at 12/s), so the pool warms instead of stampeding — which is
the ramp law satisfied by construction, not by a warmup thread.

**⚠ THE GENERAL LAW:** the dial we watch (req/s) cannot see the property that
trips the server (arrival spacing), and the config that names our intent
(`pool_maxsize=1`, "one connection") is not the same as the behavior the
library delivers. **Verify the mechanism, not the setting.** Both defects
were invisible in every rate reading and both were provable in seconds
offline.
