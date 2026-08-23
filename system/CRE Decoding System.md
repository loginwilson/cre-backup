# CRE DECODING SYSTEM

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for the system.** It runs the phases
the way a phase md runs its sources and a source md runs its custodians —
the same five sections at every altitude, because the design is FRACTAL:
the system runs phases, a phase runs sources, a source runs custodians.
Specification flows down; data flows up; each level's CHECK gates the
handoff at its altitude.

# OVERVIEW

**The job:** decode the recorded world into the present state of every
parcel and party — completely, provably, and fresh every morning. Raw
sources (county records first, then construction filings, zoning, and
beyond) are walked through six phases that turn documents into answers:
what is true about this property TODAY, at a granularity nobody else has,
with every number traceable to a page.

**The loop:** one 04:00 routine tops the system. Sync names what is new,
navigation keys and addresses it, acquisition attaches the documents,
extraction reads them into events, resolution chains the events into
stories, derivation collapses the stories into now. Go to sleep; wake up to
a fresh decoding. **Freshness is the product** — competitors are lagged,
wrong, or varying; answers stamped "proven level this morning" are the edge.

**The ladder:** `claim -> event -> account -> inference`, on two tracks —
the DATA track (tables, chains, balances) and the WRITTEN track (event
summary -> written chain -> macro summary), with the prose always generated
from the data, never authored past it.

**Procedure and judgment:** the front half (00–02) is procedure — mechanical,
complete on day one, its quality fixed by measured parameters. The back half
(03–05) is judgment — analytical, trained not written, its quality a rising
curve banked in HANDBOOKS (the constitution/case-law split: mds hold the
rules that never change; handbooks hold the learning, cold-start-survivable,
gold-set-protected, version-stamped). The bootcamp is where all of it
converges, running DURING the acquisition backfill so no time idles.

**The unit of flow is the KEY (the parcel, today).** A finished parcel
cascades through the whole back half while the corpus is still pulling —
completion is per key, never per corpus. Keys, event grammar, and the merged
graph are SYSTEM PROPERTY, converged at the phase level (keys at 01, grammar
at 03, one graph at 04) so that every source's data can join every other's.

# 1 · OUTPUT — what products stand on

The system's output is 05's present state, and it is built to hold up a
strong product surface (cards, maps, queries, feeds):

- **Per key: the answers** — every registry question answered, partial
  (source named), or blocked (break named) — plus the metrics (stored
  formulas), the macro summary, and the labeled signals.
- **Traceability as a feature:** every number walks chain -> event -> claim
  -> page. The product never shows an orphan fact.
- **Freshness as a stamp:** every answer carries the morning it was proven
  current; provisional entries surface what recorded yesterday even before
  its scan attaches.
- **Honesty as UX:** unknowns say why (a named break, a missing source) —
  the product shows the gap, never a guess.

# 2 · METHOD — the six phases

    00 Synchronizations   is the map level? name the delta        (ids)
    01 Navigations        key · doc id · index · endpoint         (the map)
    02 Acquisitions       pull images, write addresses            (the store)
    03 Extractions        documents -> events (bootcamp/bootcamp) (the tables)
    04 Resolutions        events -> chains + accounts (converge)  (the graph)
    05 Derivations        chains -> present state                 (the product)

Each phase folder holds the phase md (the contract every source must
satisfy) and one folder per source (the md that runs it + its output + its
run log — never a loose file; the tree grows WIDE with new sources, never
deep). **Adding a source:** drop a sibling folder in each phase, write its
source md on the five-section template, pass the phase contracts (the
admission audit), converge on keys/grammar/graph. No new machinery, ever.

| source | status |
|---|---|
| Legal Instruments (ACRIS + Richmond) | **LIVE** — backfill closing; back half designed, bootcamp gated |
| Construction Filings (DOB) | future — unlocks development status, contacts traversal |
| Zoning (ZR/DCP) | future — unlocks eligibility; regulatory events by applicability |
| DOF / LPC / BSA / DEC | future — named by derivation's partial answers (the registry is the source roadmap) |

**Storage & substrates — BINDINGS, not foundation.** This tree is the
LOGICAL truth; what follows is the physical binding as of today, kept in
this one section so that swapping any of it touches one paragraph and zero
logic — substrates age; the structure does not: the corpus (documents, map,
tables) lives on the corpus drive (20 TB — sized for the largest
acquisition) through acquisition; extraction compute runs on the parallel
cluster (Torch); model candidates are named in the extraction md as
candidates. **Backup is tiered:** the working corpus on the 20 TB primary;
backups onto smaller SSDs for the irreplaceable-in-time layers (the map, the
tables, the handbooks — small next to the store); cloud storage (NYU) as the
possible off-site tier; and **Supabase is the serving database** — it holds
what we DEEM worth serving (the product-facing tables: present state,
chains, the map's serving view), never the raw store. The serving wiring is
detailed here when the product layer lands. Big
outputs appear in the tree as their access points; nothing is stored twice
WITHIN the system — and yet everything is RECOVERABLE: the front half
re-derives from the custodians, the back half re-derives from the phase
beneath it, so catastrophe costs time (a re-pull measured in weeks), never
truth.

# 3 · CHECK — the system-level audit

The system is healthy when three audits hold:

1. **Every phase's check gates its handoff** — the universal law: output
   proven against something external (a custodian's counter, the disk, the
   chain's own grammar), exact-sum identities with no silent remainder,
   breaks and unknowns named, never smoothed. A phase that cannot prove
   itself does not hand off.
2. **Every md carries TIME × COST × ACCURACY** — time in measured
   throughputs and windows (never under 15 minutes), cost in request budgets
   and model tiers, accuracy in denominators and gates. Optimization is not
   a vibe; it is a checklist this document runs against every md below it.
   Every rate has a denominator; every parameter has its measurement and its
   failure mode; every unsettled value is LABELED unsettled.
3. **The conduct laws hold everywhere:** on a REFUSAL stop dead — no retry,
   no rotation, no workaround of any bot detection; never spoof an identity;
   never repair a number to make a check pass; never make information up —
   an empty cell beats a plausible fabrication; credentials are never
   printed. These are not per-phase rules; they are the system's character.

**The system's own heartbeat:** the nightly routine ends by writing ONE
morning line — synced, landed, extracted, chained, derived, with counts —
the union of the phases' run stamps, appended to the System Run Log beside
this document (no file is homeless, this one included). **A missing morning is itself an
alarm:** silence must never look like success at the top when it is banned
everywhere below.

**Product-readiness is the final benchmark:** an answer reaches the surface
only if it traces, its stamp is current, its unknowns are named, and its
tier (fact vs signal) is labeled. The check that fails withdraws the answer
— the product is never wrong quietly.

# 4 · HANDOFF — the phase when said and done

To the products and the person: a decoded market. Open a parcel — its
documented history, its present state, its pressure. Open a party — their
holdings, their movement, their story. Every answer fresh as of this
morning's proven level, every number a click from the page that recorded
it. The registry's unanswered questions name the next source; the run
stamps show the system getting sharper against a past that never changes,
even as the corpus grows every night;
and tomorrow at 04:00 the loop runs again.

---

*The mds beneath this one carry the granular law: phase mds hold the
contracts, source mds hold the methods, handbooks hold the learning. The
numbers age; the reasons do not.*

---

## 2026-08-21 — THE SETTLED ARCHITECTURE (append-only; Claude reads this first)

**Two databases, one boundary.** Phases 00–03 build THE RECORD; 04–06 build
THE READING; 07 packages. The shape changes at the extraction boundary
(one row per document -> many rows per document), which is why the store
splits there:

    custodians ──[00 sync]──> Legal Instruments.db  (tree root - THE RECORD)
        one table `navigation`, columns in phase order:
        id | rd_url | pdf_url | recorded_details | pdf | keyed_by | key
        \__ 01 nav __________/ \__ 02 acq ______/ \__ 03 org ____/
                       |
                       v
        [04 extraction, Bootcamp-governed] ──> Legal Instruments Decoded.db
        (THE READING: events/claims/quantities; 05 resolution chains them,
         06 derivation answers "what matters today"; doc id + key = the join)
                       |
                       v
        [07 productizations]

**The four bands (the login's grammar):** sync = actively staying aligned
with the sources · nav→org = the database · ext→der = analyzing the
database · productization = packaging outputs.

**Per phase, the standing trio + watch:** routine_<phase>.py (the six-step
grammar) · a concise md (the claim, the methods, the doctrine) · the shared
db — plus a row on the Updates board (D:\CRE Decoding System\Updates\,
5-minute ticks, status COMPUTED never hand-set).

**Structural enforcement lives IN the record db** (bad states
unrepresentable, not detected): `mint_urls` trigger - no id without its two
urls; `key_rules` trigger - keys only by the three-route ladder
(parcel/reference/pdf; party is DECODING, not a key) and only with their
evidence landed.

**Completeness doctrine (proven 2026-08-21):** each custodian is closed by
its OWN enumeration - ACRIS: Socrata distinct ids + the CRFN counter census
(7,010 residues -> 6,808 void · 201 found documents landed); Richmond: the
full 1850->today window census, identity held + missed + void = range.
A zero is only believed after a known-nonzero control; an unreachable
source is a report, not a crash; never repair a number to make a check
pass.


# THE PIPELINE — sync to extraction, all python (2026-08-22)

Login: *"we need to create the pipeline and see if sync can go live"* and
*"if its all python, then shouldnt it be able to consolidate?"*

## WHAT CHANGED TODAY

**The last non-python link in the system was removed.** The richmond pdf lane
ran as a DevTools snippet pasted into an Edge tab by a human, and it died
under its own download-manager growth. It is now `rc_pdf_pull.py`. See
`docs/sources/richmond/00-source.md` §3d for the measurement.

Consequence: **every phase from sync to organization is now python**, which
is what makes a pipeline possible at all. A phase with a person in it cannot
be scheduled.

| phase | routine | lanes | status |
|---|---|---|---|
| 00 sync | `routine_synchronization.py` | `map_delta.py` · `rc_sync.py` | ✅ |
| 01 nav | `routine_navigation.py` | mints rd_url + pdf_url | ✅ 100% both |
| 02 acq | **`routine_acquisition.py`** ← NEW | `rd_walk` · `image_walk` · `rc_rd_walk` · `rc_pdf_pull` | ✅ |
| 03 org | `routine_organization.py` | `nav_key.py` | ✅ |
| 04 extraction | — | — | not built |

## THE TWO CLOCKS — and why they must not be one loop

    LIVE      ~1,650 docs/day  =  0.019 docs/s   (ACRIS ~1,550 + richmond ~102)
    BACKFILL  24.1M docs                          10-75 docs/s to finish in days

**These are ~500x apart and they are different machines, different code paths
and different pacing.** Every argument for consolidation is an argument about
CONTROL (one command, one status) and never about EXECUTION (one serial lane).
Serialising them would throw away three measured results: rd and pdf are
separate server pools (A/B settled 2026-08-21), the phases pipeline rather
than barrier, and each host has its own tolerance.

## MEASURED RATES — 2026-08-22, and every one against the 0.019/s live inflow

| stage | rate | headroom vs live |
|---|---|---|
| acq rd · acris | 75-77/s | 4,000x |
| acq pdf · richmond (fetch) | 11-19/s | 1,000x |
| acq pdf · acris | 11-12/s | 660x |
| **acq pdf · richmond (LANDED IN STORE)** | **~1.8/s** | 95x |
| extraction (this box) | 0.002 docs/s | ⚠ **50x SHORT** |

⚠ **THE FETCH RATE IS NOT THE PIPELINE RATE.** `rc_pdf_pull` reported 11.6/s
while the board reported 1.83/s, and THE BOARD WAS RIGHT — it counts files
that reached the STORE; the puller counts files it pulled into `_incoming`.
Measured backlog at 23:08: **20,731 files, 7.0 GB, 30 minutes deep.**
Always end the chain at the store, never at your own stage.

## ⚠ THE REAL CEILING DURING BACKFILL IS THE SQLITE WRITER SEAT

Not any single stage. Eight processes write the same `navigation` table —
4x rd_walk, 3x image_walk, and the lander — and SQLite has ONE writer.
Two measurements bound it, both already in the code:

  - `rc_pdf_land.py`: batching commits held the write lock across CPU-heavy
    conversions and **collapsed acris rd from 99 to 16 docs/s**. It now
    commits per file deliberately, taking a small share so it starves nobody.
  - `routine_organization.py`: **a live keyer blocked every walker.** Org
    runs as a PASS on a QUIET TABLE and its busy-guard refuses otherwise.
  - `routine_navigation.py`: an unguarded scan dropped rd 17 -> 1.5 docs/s.

**Therefore: three of the four routines require a quiet table, and the lanes
never stop during backfill. The chain cannot run AS A CHAIN until backfill
closes.** During backfill the routines are audits you run at a pause. After
backfill the table is quiet almost all the time and the constraint vanishes.

## LIVE SYNC — the design, and what actually bounds it

⚠ **NEITHER SOURCE HAS A PUSH CHANNEL.** "Live" means tight polling, not a
subscription. The good news: a ceiling check is ~1 request ("has max CRFN
moved?"), not the 25-request gallop-and-bisect `routine_4am` uses to CLOSE a
gap. Polling every few minutes is genuinely cheap.

⚠ **SYNC WRITES A QUEUE, IT NEVER FIRES A TRIGGER.** Sync appends new doc ids;
nav drains them on its own cadence. A synchronous hand-off is the pattern
that blocked every walker, and the busy-guard would refuse it anyway.

**What bounds latency is the SOURCE, not us:**

    ACRIS     400/400 imaged same-day    -> minutes-live, end to end
    RICHMOND  overnight step at ~24h     -> index in minutes, document tomorrow
              (0/15 imaged at age 0; 11/11 at age 1 day)

Richmond's lag is not a defect and must not be treated as one: record at the
event as `pending`, recheck the next morning, terminal at 7 days ->
`imageless`. Only AGE separates pending from structurally imageless — the
page prints the same words for both.

## THE GATE — what lets a phase say "I am done"

⚠ **`pdf` IS EVIDENCE; `pdf_url` IS NOT.** Measured 2026-08-22 by bounded
windows: `rd_url`/`pdf_url` are populated for all 24.1M rows (minted at nav
time, pure functions of the id). `pdf` is populated ONLY where a file landed
(rowid 5k -> 2001/2001; rowid 2M/12M/20M -> 0/2001). So the acquisition gate
counts FILES, not our own optimism:

    landed + imageless + unlanded == total        per source, per product

Report a mismatch; NEVER repair a number to make it pass. routine_4am:
*"a count computed from our own output is not evidence; every failure today
looked like success by that measure."*

## THE SHAPE THAT BEATS DOC INTAKE

Post-backfill, every stage has 600-4,000x headroom over the 0.019 docs/s
inflow, so **throughput stops being the design variable and latency becomes
it.** The steady-state daily cost of the entire system:

    rd            ~1,650 docs @ 77/s     =   21 s
    acris pdf     ~1,550 docs @ 12.6/s   =    2 min
    richmond pdf    ~102 docs @ 19/s     =    5 s
                                            --------
                                            under 3 minutes/day

**Extraction is the only phase that does not clear inflow.** At 9.7 pages/doc
(measured, n=4,001; median 4, p90 24, p99 41) and 30-60 s/page, this box does
~0.002 docs/s against 0.019 needed — **~10x short.** That is the GPU, and it
is the only hardware the live system requires. Storage is NOT a purchase:
richmond 261 KB/doc + acris 499 KB/doc projects to **11.7 TB against 19.18 TB
free**.

## OPEN — do not lose these

1. ⚠ `routine_navigation.py:133` inserts **10 values into the 12-column**
   `update_board`. That write raises; nav's board row cannot be landing.
   Deliberate fix needed, not a silent patch.
2. The acq routine's full audit **timed out mid-scan** against a busy table —
   it proves its own warning. It needs a quiet window like nav and org.
3. `_incoming` backlog is unbounded by design. Nothing is lost, but the
   lander only drains when the lanes quiet.
4. Extraction has no routine and no gate.


## ⚠ THE WRITER-SEAT LAW — one root cause, three symptoms (2026-08-22)

Login named it: *"the db lag is what is slowing down updates, the org cant run
cause of it, and the concern over sync feeding nav is the same issue."*

**MEASURED THREE TIMES THE SAME NIGHT, SAME NUMBER, DIFFERENT CODE:**

    rc_pdf_land.py     per-file commit            1.8/s
    rc_pdf_pull.py     per-file commit (new code) ~2/s
    rc_pdf_pull.py     BATCHED bare UPDATEs       keeps up with 12.5/s, queue 0

Two independently written per-row writers landed on the same ~2/s. That is the
signature of a SHARED RESOURCE CEILING, not slow code: SQLite has ONE writer
seat and eight lanes queue on it. **Making a stage faster cannot help, because
the constraint is not in any stage.**

### THE RULE, STATED CORRECTLY

rc_pdf_land.py's comment was read for a year as "never batch". Its last line
is the actual rule: **"converted OUTSIDE the transaction"**. What collapsed
acris rd from 99 to 16 docs/s was holding the lock across ~50 CPU-heavy
CONVERSIONS - the slow WORK inside the transaction, not the batch.

    ⚠ BATCHING WORK      fatal   - lock held for seconds
    ✅ BATCHING WRITES   correct - lock held for milliseconds, ONE seat
                                   acquisition instead of N

Do the slow thing (fetch, convert, compute a key) OUTSIDE, then apply the
result as a batch of bare UPDATEs.

### IT DISSOLVES ALL THREE

| symptom | mechanism | fix |
|---|---|---|
| board rates lag reality | pdf column written per-row | batched - DONE, queue 0 |
| org cannot run during backfill | keying sweep holds long transactions | compute keys outside, apply batched |
| sync feeding nav feared | assumed contention | 1,650 ids/day = ONE batch/day |

⚠ Sync was never the risk. Volume, not writing, is what starves a seat:
sync appends 0.019 rows/s; the lander wanted 12/s; the keyer swept millions.

### AND A SEPARATE BUG THE SAME NIGHT - THE BOARD WAS BLIND, NOT WRONG

`routine_update.py` reported richmond pdf at 0.20/s while the lane ran 13/s.
Two causes, both stale references to a pipeline that had changed underneath:
  - the LANE MAP named only `rc_feed.py` + `rc_pdf_land.py`, never the new
    `rc_pdf_pull.py`, so a live lane read as idle;
  - `landed` was parsed out of `rc_pdf_land.log`, and the puller writes
    straight to the store, so its work never appeared in that log at all.
**A board that reads a process list and a log file is only as true as its
map of the system.** When a lane is replaced, the board must be edited in
the same commit or it will confidently report the old world.


# PHASE 00- · THE MONITOR — a new phase ahead of sync (login 2026-08-22)

Login: *"i think we have a monitor phase ahead of sync and a new count
indicates sync to kick off"* and *"the monitor indicates the delta which the
sync gets doc id for to send to nav"*.

## WHY IT IS A PHASE AND NOT PART OF SYNC

Each phase makes ONE claim. Sync's is expensive: *every doc id the source has,
the system has.* The monitor's is smaller, cheaper, and answerable constantly:

    THE SOURCE'S COUNT IS KNOWN, AS OF SECONDS AGO.

It never touches a doc id, never writes the nav db, never mints a url. It
decides ONE thing: whether sync should run. That is why it can tick every
minute while sync — which scans, gathers ids and writes — cannot.

## MONITOR vs PROBE — the cost split that makes live affordable

    MONITOR   "has anything changed at all?"     ONE request
    PROBE     "what exactly is the edge?"        gallop+bisect, ~30 requests

Probing every minute costs ~1,800 requests/hour. Monitoring every minute
costs ~60, and only fires the probe when the answer is non-zero. **The cheap
question gates the expensive one.** At steady state the answer is almost
always zero, so almost every tick costs one request.

    monitor (1 req)  ->  delta > 0?  ->  sync (probe + gather ids)
                                            ->  nav (mint urls)
                                               ->  acq (pull rd + pdf)
                                                  ->  org (key to bbl)

## THE ONE-REQUEST QUESTION, PER SOURCE

    ACRIS      count(*) where :updated_at > watermark   (Socrata, 1 request)
               ⚠ :updated_at, NEVER recorded_datetime - that column LAGS ~11
               DAYS. Measured 2026-08-11: newest recorded_datetime in all of
               ACRIS was 2026-07-31 while 28,196 rows had actually landed.
               A monitor on the wrong field reports "nothing new" FOREVER and
               looks healthy while falling permanently behind.
               (Alternative, also 1 request: does known_edge + 1 resolve?)

    RICHMOND   today's date-range window                (1 request)
               ⚠ CORRECTION 2026-08-22: the date-range search is NOT the
               Cloudflare-protected route. The 403 finding belongs to
               /ViewVscmsDocument/ViewContent, the DOCUMENT route. rc_feed and
               rc_sync hit the search endpoints from python continuously. Two
               routes on one host with different protection - do not inherit
               one route's caution onto the other.

## CAN A CONSTANT REQUEST BE SUSTAINED? THE EVIDENCE SAYS YES

routine_4am.py, measured: *"CONCURRENCY IS THE TRIP RISK, NOT VOLUME. What
tripped the server was 12,077 documents at CONC 16 in a burst. This runs
sequential at 2.5 s - 48 KB/s, one connection."*

**Bursts trip these hosts; steady sequential requests do not.** routine_4am
already makes a request every 2.5 s against ACRIS as normal daily practice.
One request per 60 s is 24x gentler than something already running. Socrata
with an app token permits thousands/hour; 60 is noise.

## LATENCY IS SOURCE-BOUND, NOT MONITOR-BOUND

    ACRIS     400/400 imaged same-day   -> minute-live END TO END
    RICHMOND  overnight step at ~24h    -> minute-live on KNOWING,
                                           next-day on HAVING

Richmond's index arrives in a minute at any polling rate; the scan arrives
tomorrow. That is the source's clock and no monitor changes it. Record at the
event as `pending`, recheck next morning, terminal at 7 days -> `imageless`.

## WHAT THE MONITOR OWES THE BOARD

Its own phase x source rows, same as every other phase, carrying the LIVE
DENOMINATOR. Every percentage on the board is measured against `needed`, and
`needed` is otherwise frozen at whatever the last sync said. The monitor makes
the denominator true continuously - so completeness is honest even while
acquisition is at 3%.

⚠ NOT BUILT YET. sync_live.py is the placeholder and it runs the FULL routine
each tick (which scans our own rows - it timed out at 100 s against a busy
table). That is exactly the cost the monitor exists to avoid. Build the
one-request question first; everything else already exists.


# THE PHASE TREE — stated whole (login 2026-08-22)

    monitorization -> synchronization -> navigation -> acquisition ->
    organization                                    ... LIVE SOURCE DATABASE

    extraction -> resolution -> derivation           ... DECODED DATABASE

    productization                                   ... PRODUCT DESIGN

⚠ `monitorization` is NEW and completes the -ation grammar. Every phase is a
noun of process; the monitor was the only one named as a thing rather than a
doing. Its claim is the smallest in the system: THE SOURCE'S COUNT IS KNOWN,
AS OF SECONDS AGO. See PHASE 00- THE MONITOR above.

⚠ NUMBERING IS AN OPEN QUESTION, DELIBERATELY LEFT OPEN. The folders are
`00 Synchronizations` .. `07 Productizations` and every path reference in the
code depends on those numbers. Renumbering eight folders to insert a new 00
would break references throughout for a cosmetic gain. Decide it explicitly;
do not let a script decide it by accident.

## WHY THE TWO-TIER SPLIT IS LOAD-BEARING

The tiers make DIFFERENT CLAIMS, VERIFIED BY DIFFERENT AUTHORITIES, and they
FAIL IN DIFFERENT SHAPES. That is why they are two databases and not one.

| | LIVE SOURCE DATABASE | DECODED DATABASE |
|---|---|---|
| claim | completeness + freshness: we hold everything the custodian holds, right now, keyed | correctness of reading: the row says what the document says |
| authority | **EXTERNAL** - ask the source its count and compare | **THE DOCUMENT ITSELF** - nothing else can settle it |
| gate | `landed + imageless + unlanded == total` | the three tests; every claim anchored to a page |
| failure shape | **SILENT AND TOTAL** - a gate-keyed pull drops retired BBLs and the audit reads its own filter's output | **PLAUSIBLE AND LOCAL** - a fabricated section label, a face amount read as a balance |
| how it is caught | arithmetic against a number we did not invent | a second reader, a crop, a witness on another page |

**The first tier can be proven. The second can only be evidenced.** That is
the whole reason the bootcamp exists for one and the update board for the
other: an external count settles tier one; nothing external settles tier two.

⚠ The rule that guards the boundary, from routine_4am: *"a count computed
from our own output is not evidence; every failure today looked like success
by that measure."* It applies to BOTH tiers and is the only rule that does.

## STATUS 2026-08-22

    monitorization    designed, NOT BUILT - the one-request question
    synchronization   PYTHON, confirmed (map_delta.py / rc_sync.py)
    navigation        PYTHON, 100% both sources
    acquisition       PYTHON as of tonight - the browser was the last
                      non-python link in the entire system and it is gone
    organization      PYTHON - richmond complete, acris armed
    ---------------------------------------------------------------
    extraction        not built - the ONLY phase under the inflow rate
    resolution        modelled
    derivation        modelled
    productization    -

**TIER ONE IS NOW FULLY AUTOMATABLE.** Not automated - backfill still has to
finish and the monitor still has to be built - but every phase in it is code
that can be scheduled. That was not true this morning.


# ORG UNBLOCKED — the writer-seat law applied to the keyer (2026-08-23 ~00:05)

Task 1 of the overnight list. **`nav_key.py` now runs alongside the writing
lanes.** It was parked behind a busy-guard since 2026-08-21 because "a live
keyer blocked every walker."

## WHAT WAS ACTUALLY WRONG

The sweep selects a batch of up to **5,000 rows**, then for each row: parses
json, and — when there are no parcels — resolves references via `ref_bbls()`,
which runs **two queries** (one on `navigation`, one on the spec db).

The old code called `con.execute(UPDATE ...)` **inside that loop**. Python's
sqlite3 opens a write transaction on the first DML and holds it until commit,
so the EXCLUSIVE WRITE LOCK was held across up to 5,000 rows of json parsing
and thousands of reference lookups. Every walker queued behind it.

**It was never "the keyer writes too much." It was "the keyer thinks while
holding the lock."** Exactly the shape rc_pdf_land.py warned about — its rule
is the last line of its comment, "converted OUTSIDE the transaction" — and
exactly what rc_pdf_pull.py measured hours earlier: per-row commits gave ~2/s,
one executemany per 250 rows kept pace with 12.5/s.

## THE FIX

Two phases instead of one:

    PHASE A   compute every (kb, key, did) into a list.  READS ONLY.
              No transaction is open. All the json parsing, all the
              reference resolution, all the spec-db lookups happen here.
    PHASE B   one executemany + one commit.  Bare UPDATEs, nothing else.
              ONE seat acquisition instead of 5,000.

Keying logic is untouched — the same three-route ladder, the same
ref-pending `continue`, the same pdf-pass verdict.

⚠ COUNTERS MOVED TOO. They used to increment during the compute loop, which
would report keys that were never written if the batch failed to commit —
a count of our own optimism. They now increment only after `wrote = True`.

## MEASURED — the whole point

    rd acris BEFORE the keyer           68.97/s
    rd acris DURING the keying pass     61-66/s, dipping to 41/s
    keying throughput                   2,000 rows in 19.1s  (~105/s)
    org acris landed                    3,243,479 -> 3,450,824

**A 10-40% dip, against the old shape's 90% collapse** (measured then:
17 -> 1.5 docs/s, and 99 -> 16 docs/s). The keyer is no longer a lane-killer.
It is now merely expensive, which is a scheduling question rather than a
prohibition.

⚠ TUNING LEFT ON THE TABLE: the executemany batch inherits the SELECT batch
of up to 5,000. rc_pdf_pull measured its sweet spot at 250. A 5,000-row
executemany holds the lock longer than it needs to, and the 41/s dip is
probably that. Try 500-1,000 before running the keyer continuously.

## CONSEQUENCE FOR THE PIPELINE

`routine_organization.py`'s busy-guard ("RUNS AS A PASS ON A QUIET TABLE -
never alongside writing lanes") was correct for the OLD keyer and is now
over-strict. Org route 1 (parcel, inline with rd) already ran during backfill;
routes 2-3 can now run too. **Org no longer has to wait for backfill to end**,
which was the single biggest reason the chain could not flow.


## BATCH SIZE MEASURED — the keyer is now FREE (2026-08-23 00:07)

The two-phase fix removed the collapse; the BATCH dial removed the rest.
Same code, same lanes, one variable:

| BATCH | rd acris during the keying pass | cost vs ~69-73/s baseline |
|---|---|---|
| 5,000 | 35 - 41/s | **~45%** |
| **500** | **68.7 - 74.5/s** | **none measurable** |

⚠ AND A CORRECTION MADE IN FLIGHT. When rd first slid to 35/s I attributed it
to the keyer and said so. Then rd stayed at 35/s for a full minute AFTER the
keyer was stopped — so the attribution was unproven at the moment it was made.
Sampling with the keyer off showed a genuine recovery (35 -> 41 -> 48.7 ->
72.8), which is what actually established the keyer as the cause. **A number
moving while X runs is not evidence that X moved it; the control is the run
without X.** Same defect class as every other one today, caught this time
before it was banked.

**CONSEQUENCE: `routine_organization.py`'s busy-guard is now obsolete.** It
refuses to run while lanes write, which was right for the old keyer and is now
strictly worse than running. Org can key continuously during backfill at
BATCH=500. That removes the last reason the chain could not flow.


# THE BOARD WAS MEASURING ITSELF — tasks 3 & 4 (2026-08-23 ~00:35)

Two separate defects, one consequence: **no phase's own measurement was reaching
the board.** The board was reporting numbers it had derived from log lines, and
the phases that could have contradicted it were failing silently.

## DEFECT A — the phase routines could not write a row at all

`routine_navigation.py:133` and `routine_organization.py:95` both did

    INSERT OR REPLACE INTO update_board VALUES (?,?,?,?,?,?,?,?,?,?)

**TEN values into a TWELVE column table.** sqlite rejects it outright —
*"table update_board has 12 columns but 10 values were supplied"* (reproduced,
not assumed). So both routines raised at the end of their run, after printing a
clean CHECK, and neither ever wrote its row.

⚠ **AND THE BOARD LOOKED FINE ANYWAY**, which is why this survived: those rows
were being filled by `routine_update.py`, which has its own correct 12-value
writer. The board showed `navigation acris 100.0% COMPLETE` from log arithmetic
while the phase that actually verifies that claim was crashing.

Had sqlite accepted the short row it would have been worse than a crash: every
value lands one column early, so `landed` receives `needed`, and `pct_of_total`
— a REAL column — receives the **status string**. A row that reads as data and
is noise.

**THE DEFECT IS POSITIONAL INSERT, NOT THE MISCOUNT.** `update_board` has
already grown three columns (`rate_now`, `pct_increase`, `eta`), and every
growth silently breaks every positional writer. Both are now written with
NAMED COLUMNS, which cannot shift. Two files broke the same way for the same
reason — that makes it a shape, and shapes get structure, not a note.

## DEFECT B — `landed` came from logs, and logs are not evidence

The acquisition rows were `baseline + delta scraped from lane logs`. That is
**counter arithmetic**, and counter arithmetic only ever drifts one way: a lane
restart double-counts, a consumed baseline under-counts, and the row sails past
100% looking healthy. It already happened once (richmond rd pinned at 100.17%,
2026-08-21) and the standing rule from that day is *">100% board = counter
arithmetic, re-baseline from true count."*

**`board_truth.py` IS that true count.** A row is landed because there is a path
in the `pdf` column — not because a log line said so.

    pdf = ''            unlanded
    pdf = 'imageless'   resolved, no image — COUNTS AS DONE, nothing to fetch
    pdf = '<path>'      landed          e.g. By Document\2003\01 Jan\06\....pdf
    pdf IS NULL         never minted — the assumption-breaker, counted separately

### ⚠ IT ANCHORS THE TICK, IT DOES NOT REPLACE IT

Counting `pdf != ''` directly is a **16.5 GB table scan** — measured **64.8 s per
200,000 rows under lane load, ~2.2 hours a pass**, all of it competing with the
walkers for the same disk. The board refreshes every 60 s. So truth re-anchors on
a slow cadence and the fast tick carries only the delta since the anchor. The
logs stop being the authority and become what they always were: an estimate.

### THE COUNTS ARE INDEX-ONLY — no table reads

    ix_nav_pdf_todo  ON navigation(id) WHERE pdf = ''    partial — the todo set
    PK autoindex     ON navigation(id)                   totals

and ⚠ **the source split is a PREFIX**: richmond ids are `RC_2113781`, acris ids
are `2026081700306001`. `'R' > '9'`, so the two sources are CONTIGUOUS RANGES in
the id index and both counts become range scans on an index that already exists
— never a `LIKE` over 16.5 GB.

    landed = total - todo         per source, both index-only

⚠ **THE SUBTRACTION HAS ONE ASSUMPTION: every row is either todo or done.**
`pdf IS NULL` is in neither set and would silently inflate `landed`. It is
counted separately and reported, never absorbed. *Never repair a number to make
a check pass.*


# THE CHAIN RAN END TO END — and what it found (2026-08-23 ~01:00)

Task 5. `phase_chain.py` runs the five phases in order, each gated by its own
assertion. ⚠ Searched first (rule 1): `chain.py` is the FINANCING chain,
`pipeline.py` is the workflow on ONE DOCUMENT, `routine_4am.py` is the daily
ACRIS routine. None of them ran the phases in order.

**THE POINT IS THE GATES, NOT THE SEQUENCE.** Five scripts back to back is a
batch file. What makes it a chain is that each phase makes ONE claim and a phase
that cannot prove its claim does not hand work to the next.

⚠ **A PHASE THAT DECLINES IS NOT A PHASE THAT FAILED.** `routine_acquisition.py`
refuses to scan while the walkers write. With the fleet running that is the
CORRECT answer. The chain reports DECLINED separately from NOT LEVEL — folding
them together teaches us to ignore real failures.

## ⚠ THE GRADER MUST SPEAK THE PHASE'S LANGUAGE

First run scored a perfectly healthy monitor as **NO VERDICT**. The routines say
`LEVEL` / `NOT LEVEL`; the monitor says `quiet` / `NEW` / `reporting NOTHING`
and never says LEVEL at all. A grader that does not speak the phase's vocabulary
**reports the GRADER's gap as the PHASE's failure** — the same disease as
reading an error as a zero, one level up. `verdict()` is now per-phase.

And note what the monitor's claim actually is: *the edge is KNOWN*, not
*something arrived*. **`quiet` is a PASS.** The failure is the monitor declining
to answer.

## ⚠ THE PHASES WERE COMPETING FOR THE SAME SCAN

Running the chain revealed it: `routine_synchronization` STEP 1 computes system
totals by scanning 24.1M rows, and `board_truth` was computing the same number
at the same moment, while `nav_key` wrote the very index one of them was
scanning (`ix_nav_key`). Three processes, one index, all slow.

**MEASURED, AND THE ASYMMETRY IS THE LESSON:**

    ix_nav_pdf_todo   23,097,031 entries    30 s     ~770,000/s   HOT
    PK autoindex       2,501,589 entries   168 s      ~15,000/s   COLD

Same machine, same minute, 50x apart. The partial todo index is hot because the
walkers query `pdf=''` constantly; the PK's `RC_` range is touched by nobody.
**Index choice is not a detail here — it is the whole cost.** A count is cheap
or catastrophic depending on whether the fleet already keeps that index warm.

## THE MEASURED GAP — logs vs the pdf column

    richmond pdf   board  102,241     TRUE  152,237     board is 49% LOW
    acris pdf      board  860,283     TRUE  ~868,066    board is ~1% low

⚠ **AND THE CAUSE WAS NOT DRIFT.** `routine_update.py` gained a branch to count
`rc_pull.log` on 2026-08-22 — pointed at `NAV_WORK`, while `rc_pdf_pull.py`
writes the log into its own cwd. `pp.exists()` was False on every pass, so the
branch did nothing and 45,986 landed pdfs were omitted. That is **92% of the
49,996 gap**, and it is a fix that failed the same night it was written.

**A FIX THAT DOES NOT FIRE IS INDISTINGUISHABLE FROM THE BUG IT FIXED.** In code
the tell is a guard whose negative branch is SILENT — `if p.exists()`, a regex
that matches nothing, a count that returns 0. Three defects tonight share it:
this path, the richmond row regex, and the richmond page-1 edge. Every one
returned a clean, healthy-looking, wrong answer.

The durable answer is not a better log parser. It is that **`landed` is counted
from the `pdf` column**, which no path assumption can hide.


# BOARD TRUTH IS LIVE — `landed` now comes from the column (2026-08-23 01:05)

Task 3 closed and verified end to end. `board_truth.py --loop --every 1800` runs
beside the fleet; `routine_update.py` prefers its anchor over the logs.

    ROW                     BEFORE (logs)      AFTER (pdf column)
    acquisition pdf acris        860,283              871,297
    acquisition pdf richmond     102,241              156,677     +53%

## THE DESIGN CHANGED ONCE, BECAUSE THE FIRST ONE WAS TOO SLOW TO RUN

v1 counted everything itself and **ran 28 minutes without finishing**. The
measurement that killed it, taken on the same machine in the same minute:

    ix_nav_pdf_todo   23,097,031 entries    30 s   ~770,000/s   HOT
    PK autoindex       2,501,589 entries   168 s    ~15,000/s   COLD

**50x, from index choice alone.** The walkers query `pdf=''` constantly so that
index is always warm; the PK's `RC_` range is touched by nobody. Worse, a plain
`count(*)` picks `ix_nav_key` — the index `nav_key.py` is actively WRITING — and
a long read against a hot index in WAL mode degrades as it accumulates frames.

**v2: COUNT THE TODO SET, READ THE TOTAL.**

    todo   counted off ix_nav_pdf_todo        hot, ~25 s
    total  read from the SYNC LEDGER          free
    landed = total - todo

**131 seconds a pass**, down from >28 minutes and unfinished.

⚠ **VALIDATED, NOT ASSUMED.** The chain's `routine_synchronization` STEP 1
finished its own independent full scan minutes later and returned
**acris 21,615,745 · richmond 2,501,589** — exactly the ledger figures v2
substituted. The shortcut was checked against the long way before being trusted.

## ⚠ IT COMPOSES ANOTHER PHASE'S ASSERTION AND SAYS SO

`landed = total - todo` is only true if our table holds a row per source
document. **That is navigation's claim, not this file's** — so the anchor records
which sync run it leaned on (`ledger_run`) and declares `depends_on: navigation
LEVEL`. Composing assertions across phases is exactly what the chain is for;
hiding that you composed them is how a number becomes unfalsifiable.

The denominator now comes from OUTSIDE our own database, which is the point: a
total taken from our own table can only ever tell us we are consistent with
ourselves.

## ⚠ A STALE ANCHOR MUST NOT WIN

An anchor older than 2 hours cannot see the last hour of landings, which makes it
*worse* than the live log estimate. `routine_update` ignores it past TRUTH_FRESH
and falls back. **Never silently prefer an old truth to a live estimate.**

## ⚠ AND THE GUARD I WROTE COULD NOT HAVE FAILED

`nullprobe` checks for rows inserted but never minted (`pdf IS NULL`), which
would silently inflate `landed`. v1 probed `rowid <= 200000` — **the OLDEST rows,
minted years ago and long since landed.** It could only ever return 0. That is
not a passing check, it is an absent one (rule 4: *a counter sitting at zero is a
claim to verify, not a result*). Now probes the TAIL, where sync actually
inserts. Current reading: **0 of the last 200,000** — and now that means
something.


# ⚠ THE PRODUCTION HALF BLOCKS THE VERIFICATION HALF (2026-08-23 ~01:20)

The chain's first end-to-end run answered a question nobody had asked directly:
**three of the five phases cannot prove their claim while the fleet is running.**

    monitor   LEVEL              cheap by design - a few requests
    sync      LEVEL both sources delta 0 / delta 0
    nav       DECLINED           busy-guard; tail probe clean
    acq       DECLINED           busy-guard
    org       DECLINED           busy-guard

Every DECLINE has the same cause: **that phase's audit is a full TABLE scan**,
and the fleet never stops. Measured 64.8 s per 200,000 rows under lane load —
~2.2 hours for the corpus, and the scan is what dropped rd from 17 to 1.5 docs/s
the day the guards were written. The guards are correct. The AUDITS are wrong.

    nav   reads rd_url, pdf_url          -> table scan
    acq   reads recorded_details, pdf    -> table scan
    org   groups by keyed_by             -> table scan

## THE FIX ALREADY EXISTS IN THIS SYSTEM AND WAS PROVEN TONIGHT

`board_truth.py` had exactly this problem and solved it: it stopped scanning the
table and counted a **partial index on the todo condition** instead.

    ix_nav_pdf_todo  ON navigation(id) WHERE pdf = ''

    table scan          200,000 rows      64.8 s      ~3,000/s
    partial index    23,097,031 rows        30 s    ~770,000/s

The index is fast *because the walkers keep it hot* — they query `pdf=''`
constantly. **The audit rides on the fleet's own working set instead of fighting
it.** That is the whole trick, and it generalises: give every phase's claim a
partial "todo" index and each audit becomes ~30 s instead of ~2.2 hours.

    ix_nav_url_todo    WHERE COALESCE(rd_url,'')='' OR COALESCE(pdf_url,'')=''
    ix_nav_rd_todo     WHERE COALESCE(recorded_details,'')=''
    ix_nav_keyed_todo  WHERE keyed_by IS NULL

⚠ **NOT TONIGHT, AND NOT WHILE ELEVEN LANES WRITE.** Building an index on a
24.1M-row / 16.5 GB table is one long WRITE transaction — it would take the
writer seat and hold it, which is the writer-seat law violated as hard as it can
be violated. **This needs a quiet window, and it is a schema change, so it is
login's call.** Recorded here as the identified next move, not done unilaterally.

## THE INTERIM POSITION IS HONEST, NOT LEVEL

Until then: `nav` runs a bounded TAIL probe when it cannot afford the full scan
(~65 s, last 200,000 rows, currently **0 missing urls**), and reports
`DECLINED (tail ok)` — strictly more than "declined", strictly less than LEVEL.
`board_truth` states `depends_on: navigation LEVEL` rather than pretending its
subtraction is self-evident.

**A phase that cannot be checked is not a phase that passed**, and the board now
distinguishes those three states instead of two.

## ⚠ AND A GUARD WITH AN EXEMPTION FOR THE DEFAULT MODE IS NOT A GUARD

`routine_acquisition.py` read `if alive and not (a.dry or a.anyway)` and its own
message said *"run --dry for a safe read"*. But `--dry` skips the WRITE, and the
write was never the expensive part — steps 1-2 scan 16.5 GB either way. So
`phase_chain.py --dry` walked straight past the guard and started precisely the
unguarded scan the file exists to prevent. Caught only because running the chain
made it visible.

**`--dry` is a promise about WRITES. It can never be a promise about COST.**
Only `--anyway` overrides now.


# ✅ THE CHAIN RAN END TO END — first time (2026-08-23 01:00)

Task 5. `phase_chain.py --dry`, all five phases, one command:

    PHASE     VERDICT              SECONDS
    monitor   LEVEL                     56
    sync      LEVEL                    464     acris delta 0 · richmond delta 0
    nav       DECLINED (tail ok)       182     last 200,000 rows · 0 missing urls
    acq       DECLINED                   1     busy-guard, correctly
    org       DECLINED                   1     busy-guard, correctly

    CHAIN CLEAN · 2 of 5 phases PROVEN (monitor, sync) · 3 unproven

⚠ **THE HEADLINE CARRIES ITS DENOMINATOR NOW.** The first version printed a bare
`CHAIN LEVEL` with three of five phases declined — the exact conflation this
file's own docstring warns against, committed by the file itself. **A phase that
could not be checked is not a phase that passed.** Nothing here is a rate
without a denominator.

⚠ Sync ran **464 s, not the 28 minutes** of the earlier attempt. Same scan, same
data — the difference was that three other processes had stopped scanning the
same index. **Contention, not throughput.**

## WHAT RUNNING IT ACTUALLY BOUGHT — four defects nothing else would have found

Running the chain is what surfaced these. None was visible from reading code.

1. **`routine_acquisition`'s busy-guard exempted `--dry`.** `if alive and not
   (a.dry or a.anyway)`, with its own message advising *"run --dry for a safe
   read"*. But `--dry` skips the WRITE, and the write was never the cost —
   steps 1-2 scan 16.5 GB either way. The chain's dry run walked straight past
   the guard and started exactly the scan the file exists to prevent.
   **`--dry` is a promise about WRITES, never about COST.**

2. **The grader did not speak the monitor's language** — scored a healthy run as
   NO VERDICT because the monitor says `quiet`, never `LEVEL`.

3. **`sync_fast.py` inserted rows the lanes can never see.** It wrote only
   `(id, rd_url, pdf_url)`, leaving `recorded_details`, `pdf` and `keyed_by`
   NULL — while `nav_append.py:216` states the invariant outright: *"rd_walk
   sees recorded_details='', image_walk sees pdf='', nav_key sees
   keyed_by=''"*. **NULL is not ''**, so every document landed by the fast path
   would have been skipped by every downstream lane FOREVER, while looking
   perfectly healthy — id present, count right, url audit passing. It would
   also sit outside `ix_nav_pdf_todo`, so board_truth would report it as
   **LANDED: a document with no pdf, counted as acquired.**
   ⚠ Verified not yet triggered: **0 NULLs in the last 400,000 rows** — the
   delta has been 0 all weekend. It would have bitten on the first busy morning,
   in the path login most wants to rely on (*"i want live not a batch"*).

4. **The monitor's gate fired the WRONG sync.** `fire_sync` called
   `routine_synchronization.py`, whose STEP 1 counts 24.1M rows (~27 min) before
   it looks at the source at all — fired on a ONE-MINUTE cadence. `sync_fast.py`
   exists precisely for this and its docstring already drew the line:

       routine_synchronization.py   proves levelness   minutes   periodic
       sync_fast.py                 lands the delta    seconds   every minute

   **Nothing was wired to it.** The design was written and never connected —
   the same "rule that does not fire" shape as the other three.

## ⚠ THE PATTERN ACROSS ALL OF TONIGHT

Seven defects, one shape: **a check that ran, found nothing, and could not tell
"nothing" from "clean."** A dead regex. A page-1 edge. A path that did not
exist. A guard with an exemption. A NULL that is not ''. A verdict function that
did not know the vocabulary. A design never wired up.

Every one produced a confident, healthy-looking, wrong answer. **Make the
negative branch loud, or verify against something outside the check.**


# ✅ THE GATE FIRED — monitor -> sync proven live (2026-08-23 01:05)

`phase_monitor.py --gate --every 60` is running as a service. The gate had never
fired, and waiting for Monday to find out whether it works is not a test — so it
was tested deliberately: drop the known edge by 5, watch the whole chain react.

    01:05:08  acris edge ...860 · control ok · probed +1..+8 (2 req) · NEW at ...861
    01:05:10  --> firing sync_fast.py for acris
              our top CRFN ...860 · control resolves - probe OK
              walked +13 (14 requests) · found 5 new
                ...861  2026081800762002  ASSIGNMENT OF LEASES AND REN  8/21 7:56:33 PM
                ...862  2026081800762003  INITIAL UCC1                  8/21 7:56:34 PM
                ...863  2026081800762004  MORTGAGE                      8/21 7:56:35 PM
                ...864  2026081800762005  ASSIGNMENT OF LEASES AND REN  8/21 7:56:36 PM
                ...865  2026081800762006  INITIAL UCC1                  8/21 7:56:37 PM
              landed 0 ids into navigation
              edge advanced ...860 -> ...865  (after the commit, never before)
    01:07:39  acris edge ...865 · quiet

**Everything it claimed, it did.** It resolved five real documents, INSERT OR
IGNORE correctly no-opped because we already hold them, the watermark advanced
only after the commit, and the next tick went quiet. **The edge restored itself
to the true value** — the backup was never needed.

⚠ **NOTE THE COST ASYMMETRY, WHICH IS THE DESIGN.** A QUIET minute costs 9
requests (probe the whole span, find nothing). A BUSY minute cost **2** — it
stops at the first hit and hands the rest to sync. The monitor gets cheaper
exactly when there is more to do.

## AND RICHMOND NOW HAS THE SAME PATH — `rc_sync_fast.py`

It had none, so the gate had nothing to fire but the full routine (STEP 1 alone
counts 24.1M rows). ⚠ **Richmond needs no gallop**: ACRIS walks the CRFN counter
because its edge is a boundary to be FOUND; Richmond's window RETURNS THE
DOCUMENTS, so the delta is one PK lookup per row.

    measured: 3-day window · 103 documents · 7 pages · 22 s · held 103 · NEW 0

# ⚠ I BROKE THE RATE BY FIXING THE COUNT (same night, caught same night)

Anchoring `landed` to `board_truth` made the LEVEL right and the DERIVATIVE
nonsense. Both rates are computed by differencing `landed` over a window — so
differencing a counter that re-measures every 30 MINUTES measures **the anchor's
step, not the lane**:

    acris pdf     board 1.37/s     lanes actually 11.06/s     eta 175.48 days
    richmond pdf  board 1.91/s     lane log says  10.81/s     eta  14.16 days
    rate_now      0.0 on both      - which reads as STALLED

`1600 / (20*60) = 1.33`. That is the anchor's step divided by the window, and it
is exactly what the board printed. **The most misleading cell on the board is a
zero rate next to a healthy lane.**

⚠ This is the SAME ALIASING DISEASE as the morning of 2026-08-22 (60-second
samples of 60-second lumps reading 0.0, then 175.4/s, then 13.3/s) arriving by a
new route — **and I introduced it by making the number more accurate.** An
improvement to a level is not automatically an improvement to what is derived
from it.

**THE RULE, ALREADY WRITTEN IN THIS FILE AND NOT APPLIED TO THE NEW CASE:**
*a lane already measured its own rate — READ IT, do not re-derive it.*
Anchored rows now take the lane's published figure outright, and richmond's pdf
lane got the LANE_RATE entry it never had.

    AFTER:  acris pdf    11.06/s   eta 21.71 days   (was 175.48)
            richmond pdf 10.71/s   eta  2.53 days

⚠ **AN ANCHORED COUNTER IS AUTHORITATIVE ABOUT THE LEVEL AND USELESS AS A
DERIVATIVE.** Never difference one to get a rate.


# THE PIPELINE — WHERE IT STANDS, 2026-08-23 01:30  (plain terms)

Everything below is running right now, unattended.

## THE FIVE STEPS, AND WHO DOES THEM

    00  MONITOR    "has anything new been filed?"          phase_monitor.py --gate
    01  SYNC       "get me the ids of whatever is new"     sync_fast.py / rc_sync_fast.py
    02  NAVIGATE   "put every id in the table with a url"  routine_navigation.py
    03  ACQUIRE    "attach the actual pdf"                 rd_walk / image_walk / rc_pdf_pull
    04  ORGANIZE   "key each document to what it is about" nav_key.py

The monitor asks the cheap question once a minute. When the answer is yes it
fires the FAST sync, which lands only the new ids. The lanes then pick those rows
up **with no restart**, because a new row is written with its work columns empty
and each lane selects on exactly that.

## WHAT IS ACTUALLY RUNNING (11 python processes)

    4 x rd_walk.py      --workers 28    the recorded-detail walk
    3 x image_walk.py   --workers 28    the acris pdf lanes
    1 x rc_pdf_pull.py  --workers 16    richmond pdfs, pure python
    1 x rc_pdf_land.py                  drains the old richmond backlog
    1 x rc_feed.py                      richmond feed
    1 x org_backfill_arm.py             the keyer
    +   phase_monitor (gated) · board_truth (30 min) · routine_update (60 s)

## THE NUMBERS, FROM THE COLUMN NOT THE LOGS

    acquisition rd   acris      9,667,266 / 21,612,715   44.7%   ~66/s   eta 2.1 d
    acquisition rd   richmond   2,501,589 / 2,501,589    100%    COMPLETE
    acquisition pdf  acris        872,897 / 21,612,715    4.0%  11.06/s  eta 21.7 d
    acquisition pdf  richmond     158,916 /  2,501,589    6.4%  10.71/s  eta  2.5 d
    organization     acris      3,747,509 /  9,656,707   38.8%

## WHAT IS PROVEN AND WHAT IS NOT — read this part

    monitor   PROVEN     edge known, and the gate FIRED live (tested, not assumed)
    sync      PROVEN     acris delta 0 · richmond delta 0
    nav       UNPROVEN   tail probe clean (last 200,000 rows, 0 missing urls)
    acq       UNPROVEN   busy-guard: cannot scan while the fleet writes
    org       UNPROVEN   busy-guard: same

⚠ **2 of 5. A phase that could not be checked is NOT a phase that passed**, and
the board says so rather than printing a comfortable "LEVEL".

**THE ONE THING BLOCKING THE OTHER THREE** is that their audits are full table
scans (~2.2 hours) and the fleet never pauses. The fix is measured and prepared
in `migrate_audit_indexes.py` — partial "todo" indexes, the same trick that took
board_truth from 28 minutes-and-unfinished to 131 seconds. ⚠ **It needs a
deliberate pause of the fleet and it is login's call**, because CREATE INDEX
takes the writer seat for the whole build. Nothing was run.

## THE SEPARATE QUESTION NOBODY HAS ANSWERED: rd IS AT HALF ITS CEILING

The fleet is at the proven operating point (rd 4x28) but running **~56-84/s
against a measured aggregate ceiling of ~138/s**. It has been ~69/s all night,
including with the keyer stopped. That is 2 days vs 1 day for the rd backfill.

⚠ **NOT INVESTIGATED, DELIBERATELY.** Settling it needs controlled A/B, which
means stopping lanes — against the standing instruction to keep everything
running. And the prior lesson applies: *a single-lane bump reads linear by
borrowing the controls' headroom; only the full-fleet reading settles it.*
Flagged for a waking decision rather than guessed at overnight.
