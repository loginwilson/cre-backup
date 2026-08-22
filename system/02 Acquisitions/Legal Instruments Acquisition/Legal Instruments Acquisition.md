# LEGAL INSTRUMENTS — ACQUISITION

**The phase's one claim: every id's row carries its two payloads —
`recorded_details` filled and `pdf` attached as a REAL FILE — or is honestly
classified `pending` / `imageless`.** Nav minted the addresses; acquisition
fills what they resolve to. Closing identity, per source per payload:

    filled + pending + imageless = total

**The feed is AUTOMATIC, not scheduled: an empty cell IS the work list.**
Lanes select `WHERE recorded_details=''` / `WHERE pdf=''` continuously, so
the moment sync lands an id (and the db trigger mints its urls) a running
lane picks it up — no signal, no restart. The routine is only the AUDIT;
a supervisor keeps lanes alive across reboots.

---

## THE LOCKED CONFIGURATION (settled 2026-08-22 ~00:15, experiment-priced)

**MEASURED STABLE, 2026-08-22 11:30 (10-min clean window, single browser
session): acris rd 97.5 · richmond pdf 2.37 · acris pdf ~5 docs/s.**
That is the target shape (100 / 8 / 2) with one caveat: acris pdf's
doc-rate is NOT a throttle — both arms run at ~43 pg/s, the server's
page ceiling; docs/s = pages ÷ page-density, and density varies by
corpus region (film ~3.7 pg/doc vs digital ~13.4). The lever, unused so
far: point BOTH arms at film ranges → ~9-11 docs/s at the same page
ceiling (same total time, completed docs far sooner).

**The sequence, not a static fleet:** acris rd is the priority until it
closes (~2.3 days), then the machine flips to the pdf campaigns.

    NOW (overnight standing):
      acris rd    4 × 28                      ~100 docs/s   ≈ 2.3 days
      acris pdf   2 × 28 (digital + film)     ~8 docs/s     the long pole
      richmond rd CLOSED - walker = daily follower
      richmond pdf feed(32 miners, ahead 300) → ONE visible browser
                  (2 pullers ~1.5-2 docs/s) → raw lander; converter PARKED
                  — the session lives in CHROME (Edge is the user's daily
                  browser; the download stream must not ride in it). A
                  fully-covered or minimized window counts as HIDDEN to
                  Chrome's occlusion deter - keep the window on screen.
    AFTER acris rd closes:
      everything to the pdfs - richmond goes TWO-BROWSER (Edge+Chrome,
      3.1 docs/s measured) + converter resumes + acris pdf ladder re-runs
      on the freed cores/connections (old campaign hit 75-90 pg/s).

**Why one browser now — the experiments that priced it (2026-08-21/22):**
- PAUSE TEST: both browser loops stopped → acris rd 55 → **101 docs/s**
  within minutes. The browsers are a real machine tax, not a launch spike
  (a 14-min sustained watch confirmed NO warm-back under load).
- TWO-BROWSER TEST: Edge+Chrome served 3.09 docs/s combined (the iapps
  wall is PER-CLIENT ~2/s — a second real browser adds its own pool; a
  second TAB in the same browser adds nothing) — but acris held at ~55/s.
- THE PRICE: two-browsers-now buys richmond pdf ~1 day and costs acris rd
  ~2 days and acris pdf ~19 (8 → 5 docs/s). The SEQUENCE dominates every
  line. ⚠ The browser tab must stay VISIBLE (hidden ⇒ throttled ~1/s).

**The daily process, sync-kicked, structural end to end:** sync lands new
ids → the db trigger mints both urls in the same transaction → running
lanes select empty cells continuously (no signal, no restart) → the
Richmond walker follows rd, the feed/browser/lander chain follows pdf →
organization runs its pass when acquisition hands it context. The board
watches; nothing is remembered by hand.

## THE FOUR LANES

**ACRIS rd** — DocumentDetail pulls over the proven session shape.
**MEASURED 2026-08-21 evening, single-lane-first protocol (one lane bumped,
three as live controls, disjoint table-slice measurement):**

    4×20 =  80 conn:  ~99 docs/s   (24.7/lane)
    4×28 = 112 conn: ~138 docs/s   (34.5/lane) - controls flat
    1×36 + 3×28:      lane read 44.3 - LOOKED linear...
    4×36 = 144 conn: ~139 docs/s   (34-35/lane) - NO GAIN

⚠ **THE CEILING IS AGGREGATE: ~140 docs/s from the server, however you
slice it.** The single-lane 36 test read linear only because that lane
borrowed headroom the 28-worker controls weren't using — the moment all
four ran 36, they split the same total. A single-lane test PASSES ≠ the
rollout gains; only the full-fleet reading settles it. **OPERATING POINT:
4×28** (the lowest config that reaches the ceiling; fewer connections,
same throughput). Fails at background (~0.007%), zero refusals throughout.
Rate read from TABLE-SLICE GROWTH
(disjoint id bands, 2-min windows), not the lanes' own printers — ⚠ a
restarted lane's stdout reporter can go mute while the lane lands fine
(measured: 3 mute lanes all landing at full rate; diagnose from the table,
never from silence). ⚠ Slices must be DISJOINT with lane ranges - an
overlapping slice double-counted a neighbor lane and read 103.7 docs/s
where the truth was 44.3.

**ACRIS pdf** — DocumentImageView page-chain.
⚠ end-of-document is a PLACEHOLDER served as HTTP 200 — the chain's stop
condition is content, not status.
**WE MEASURE DOC/S** — pages are a lane-internal load gauge, never the
reported number. **PDF CEILING FOUND 2026-08-21 evening: ~6-8 docs/s
AGGREGATE** (≈40 pg/s internally; night runs looser than rush hour).
Proven twice at constant-total workers: 2 procs × 28 = 40.2 · 3 procs ×
~60 workers = 40.1 — rearranging changes nothing. One process knees at ~26
(the GIL); two collect the pool; a third adds only RAM use. Hint of two
~20 pg/s sub-pools (digital / film). **OPERATING POINT: 2×28** (digital arm
+ film arm). Film completes ~3× the docs per page (≈3.7 pg/doc vs ≈13.4) —
tilt toward film when completed-document count matters first.

**A/B SETTLED 2026-08-21: SPLIT RUNNING WINS — the pools are independent.**
rd held 135 docs/s under a 20-worker pdf arm (138 alone — noise) while the
arm added 20.2 pg/s with zero fails: the details pages and the images are
served from separate capacity. Sequential would idle the image backend for
the whole rd campaign. pdf scales its own ladder (old campaign reached
75-90 pg/s at 4×20) by WORKERS-PER-PROCESS first — the 16 GB RAM ceiling
(~4-5 processes) binds before the server does. Measure ≥15-minute windows:
the ledger commits once per process and short windows lie (29 vs 110 pg/s
measured on the same healthy run).

**RICHMOND rd — CLOSED 2026-08-21 ~11:55 PM: 2,501,589 / 2,501,589,
table-counted, empty 0.** The walker stays on as the DAILY follower.
⚠ The closure's lesson: the last 339 docs sat in two DEEP recovery
windows (hundreds of listing pages) where the walker's restart-from-
page-1 design meant one mid-walk timeout aborted the window every sweep.
**The retry unit must never be bigger than the failure unit** — get()
now retries PER PAGE (4 attempts, backoff); that change landed all 339
in a single pass after two full sweeps had failed.

**RICHMOND rd — CODED, on the new site too (re-cracked 2026-08-21 night).**
The redesign's grant rule, measured: a detail unlocks after the session
fetches THE LISTING PAGE the id appears on (not the whole search, not
nothing — an id whose page was never fetched gets the 4,212-byte shell;
same id right after its page: full detail). `rc_rd_walk.py` owns it:
window → pages → targets' details, one keep-alive session per worker, the
census db supplying every id's window. Lands the CORPUS SCHEMA: doc_type ·
book/page · recorded · amount · status · **image_state** (rc_mint's pdf
selector) · **parcels as BBLs** (borough 5 — route-1 keyable on arrival) ·
parties with the person/company column kept.

⚠ CONCURRENCY HISTORY, so nobody under-runs this county again: the OLD
site served rc_detail_pull at **conc 80 × 2 concurrent sweeps = 160
connections**, 2,498,810 details in ~26 h (~27 docs/s sustained, Aug
18-19). The NEW site took the same 160 (2 shards × 80 workers, night of
Aug 21, ZERO fails) — but ⚠ ONLY RAMPED: 160 first TLS handshakes in the
same instant = SSLError across the board while a lone request succeeds
(the cold-burst trip; keep-alive removes every handshake EXCEPT the first,
so rc_rd_walk staggers session birth 0.4 s/worker). Our GIL pins a process
near one core (~10 docs/s/process); scale = process SHARDS (--shard i/n),
~19-20 docs/s at 2×80. The walker is also the DAILY follower: sync lands a
new RC id with empty rd → the walk fills it coded. Chrome's only remaining
Richmond job is PDFs.

⚠ **ONE DB, ONE WRITE LOCK — COMMIT PER ROW IN EVERY DAEMON.** The pdf
lander's UPDATE opened an implicit transaction that stayed open across ~50
CPU-heavy conversions (commit-every-50): the nav db's single write lock
was held 30-60 s at a stretch and EVERY lane queued behind busy_timeout —
acris rd collapsed 99 → 16 docs/s the moment the daemon started
(2026-08-21 9:24-9:34 board). Convert OUTSIDE the transaction, hold the
lock milliseconds. A slow lane after a new daemon starts = suspect a held
lock BEFORE suspecting CPU or the server.

⚠ **RICHMOND HAS TWO NUMBER NAMESPACES — verify by BOOK/PAGE or the
instrument field, NEVER by filename-vs-Document-Number-search.** Our
RC_{n} is the INTERNAL id (the ViewDocumentInfo route key, unique, what
the census walked). The clerk's "Document Number" search queries the
INSTRUMENT number — a separate sequence that numerically overlaps.
Measured 2026-08-21: internal 1008528 = instrument #9566, Book 847/Page
195, 1942 (pdf stamp "Vol 847 PG 195" matches) while instrument #1008528
belongs to internal 2815386 (a 2026 deed) — searching our id as a Document
Number finds a DIFFERENT, equally-real doc and reads like a mismatch.
Old-era check: pdf's Vol/PG stamp = row's book/page. Modern check: LAND
DOC # stamp = row's `instrument` (it will NOT equal the filename - that
is correct). Mint is id-faithful (granted vs feed-style A/B: identical
document handles).

**RICHMOND pdf — THE SETTLED METHOD (locked 2026-08-21 night; the login:
"very important you keep the acquisition method stored so we never
forget"). Four links, each with its measured rate and its trap:**

    rc_feed.py --miners 32 --ahead 300      (~2-3 mints/s)
      → N visible browser sessions, 2-3 pullers each (~1.1/s per puller)
      → rc_pdf_land.py --loop --raw         (~10/s, validity-check only)
      → rc_convert.py --loop                (deferred G4, next-week job)

1 · THE FEED mints ViewContent 302-Location tokens - headless work touches
ONLY richmondcountyclerk.com; the iapps host is the browser's alone.
⚠ WHY PYTHON CANNOT DO THIS LANE (settled 2026-08-22, so nobody re-asks):
python requesting the FINAL image url with a VALID FRESH token and a
completely normal request (real Chrome User-Agent, proper Referer, correct
Accept) gets **HTTP 403 Forbidden** - while the browser is served that
same token seconds later. The host fingerprints below the header layer
(TLS/handshake), which python's stack cannot present without actively
impersonating a browser fingerprint = working around bot detection = the
line we DO NOT cross. So the asymmetry is STRUCTURAL and measured, not a
missing trick: 3 of 4 lanes are pure python (acris rd, acris pdf, richmond
rd); richmond pdf ALONE needs a real browser, and that is the host's
design. (The in-app browser pane also got the bot interstitial - only a
real user-driven browser with the extension works.) Mint is
ID-FAITHFUL (granted vs cold A/B: identical handles). Keep --ahead ≈300:
tokens EXPIRE, and a deep buffer serves near-dead tokens.
2 · THE BROWSER LOOP is a WEB WORKER (v7, settled 2026-08-22 morning):
the worker polls /batch?n=25 and runs TWO concurrent fetch runners at
250 ms pace; the page's only job is the download click, which is
event-driven. ⚠ WHY A WORKER: page-timer loops are throttled when the
window is hidden/covered/screen-locked (~0.5-1 doc/s, and overnight the
crawl let every queued token expire → a false refusal trip at 00:30).
Worker timers are exempt: **measured 1.85 docs/s WITH THE WINDOW
HIDDEN** (368/3.3 min, 0 errors) ≈ the per-client wall. The lane is now
CONTINUOUS - covered, minimized, screen-locked, full pace; only machine
sleep stops it. The id travels WITH the url so the download name is the
internal id.
Guard: an expired token's 401 is NOT a refusal - drop it; at 5
consecutive failures PURGE THE QUEUE ONCE and test FRESH tokens; only ~3
more fresh failures = a real block, STOP ALL. (⚠ Overnight 2026-08-22
taught why the purge step exists: the screen LOCKED → Chrome marked the
window hidden → the loop throttled → every queued token expired → a
plain 5-streak guard read its own staleness as a refusal and stopped at
~00:30. The lane is a SCREEN-ON lane until the multi-browser era; it
pauses with the lock and that is acceptable - it is the lowest-priority
lane while acris rd runs.) Multiple sessions need no sharding: the
feed's queue hands each token out exactly once.

⚠ **THE WALL IS PER-IP ~2 docs/s — MORE SESSIONS DO NOT HELP. SETTLED
2026-08-22 with honest counters; do not rebuild browser topology.**

    1 session  : 1.85-2.16 docs/s · acris rd ~100/s
    2 sessions : 1.95-2.05 docs/s · acris rd  ~65/s
    3 sessions : 1.73 docs/s      · acris rd  ~47/s   (WORSE, both ways)

⚠ THE EARLIER "3.09 docs/s on Edge+Chrome" WAS A MEASUREMENT ARTIFACT:
that feed had no token TTL, so EXPIRED tokens still counted as "served"
while the browser failed them. Once the feed discarded stale tokens
before serving, the same topology measured ~2. **A counter of handoffs
is not a counter of work** — measure landed files or the consumer's own
success count. Extra sessions only split the same allowance and spend
RAM, which is what drags acris (RAM binds, never CPU: the census showed
5 of 8 cores idle, every lane remote-bound). OPERATING POINT: **ONE
browser session, 2 worker runners.** The ~14-day Richmond pdf backlog is
the county's own pace, not something to engineer around.
3 · THE RAW LANDER strips Chrome's " (N)" dup suffix (a raw stem built a
trailing-space dir that killed the daemon), deletes re-downloads of
landed ids, validity-checks (%PDF + pages), stores on RECORDED date,
lands the row, COMMITS PER FILE (the held-lock rule above).
4 · THE CONVERTER is OPTIONAL, never a dependency (settled 2026-08-22:
"we dont even have to convert"). The RAW file IS the acquired document -
it passes the gate and extraction renders it identically. Conversion
only buys resting size (~870 GB raw vs ~350 GB converted, against 18 TB
free) and faster corpus copies. Raw files self-identify forever
(DCTDecode pages = raw · CCITTFax = converted · keep-smaller rules), so
rc_convert.py can run at any idle time, or never, with no bookkeeping.

The pdf cell's save path (`By Document\YYYY\MM Mon\DD\{id}.pdf`) is a
CLAIM the gate must prove. Verify IDENTITY by the two-namespace rule
above, never by the filename against a Document-Number search.

---

## THE STATES — pending / imageless (the lag is built in)

A pdf url that leads nowhere does NOT mean imageless:

    id <= 7 days old  -> PENDING   re-probed each run
    older             -> IMAGELESS decaying tail re-probe, never abandoned

    lag, measured: ACRIS scans attach SAME-DAY (400/400) ·
                   RICHMOND overnight, a step at ~24 h (age 0: 0/15 · age 1: 11/11)

⚠ 174,142 ACRIS documents are KNOWN image-less and must never be fetched.

---

## STORAGE — recorded chronology (the login's rule, 2026-08-21)

Documents store on RECORDED date: `By Document\YYYY\MM Mon\DD\{id}.pdf` —
the store reads as the county's own chronology. Nothing else is organized
here; keying to BBL is the NEXT phase (03), which fires as a pass once
acquisition's payloads give it full context.

## THE GATE — live-vs-disk, the check this phase was missing

Nav's `pdf` column is a computed path, NOT evidence. The audit ends on disk:
the file EXISTS, is non-zero, and opens as a PDF (`%PDF` header + page
count); rd parses as the details it claims. Sampled continuously, full sweep
at audit. Rates on the board carry their denominators, windows ≥15 min.
