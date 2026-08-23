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
