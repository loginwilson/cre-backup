# ACRIS · PHASE 2 — ACQUISITION

**Status: begins 2026-08-17 (drive arriving).** Selection is complete and
reconciled, so the inventory this phase must match is settled.

## GOAL

Get the documents onto disk, and be able to prove that what landed **matches the
inventory selection defined**. Accuracy in this phase is not transcription
accuracy — it is correspondence to the selection map.

## WHAT WE ARE FETCHING

| | |
|---|---|
| documents | **17,049,742** (reconciled ACRIS ↔ local ↔ Supabase) |
| pages | ~148,000,000 |
| image-less | **174,142** — never fetch these; the index is their record |
| endpoint | `https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={id}&page={n}` |

⚠ **No navigation and no URL storage.** The endpoint is a pure function of the
doc id, which is why acquisition can run straight off the selection map. The page
count per document is already in `document_map` (`total_pages`, `instrument_from`,
`instrument_to`), so we know exactly how many requests each document needs before
asking for the first one.

## ⚠ THE RULES THAT ARE NOT NEGOTIABLE

**1. Do not build a bulk image scraper and do not work around bot detection.**

**2. STOP DEAD ON A REFUSAL.** No retry, no backoff-and-continue, no rotating
anything, no routing around it. Report it and stop that line of work.

⚠ This has already been violated by a *scoping* bug, not a decision.
`map_acris._batch()` created its own `stop = asyncio.Event()` **inside** the
retry loop, so a refusal halted that batch, printed "REFUSED — stopping. No
retry." — and the next batch built a fresh Event and went straight back at it.
Six refusals were logged while the map carried on gaining documents. The lesson
is not "move the flag": **a stop signal scoped inside the loop it is meant to
stop cannot stop it, and the log will print the word "stopping" every time it
fails to.** Refusal state is run-scoped (`_REFUSED`, module level).

**3. One refusal became three on 2026-08-05 and cost the image endpoint for an
hour.** Treat the first as the last warning it is.

**4. Preserve the original.** Source data stays on disk after processing begins.
Processing copies are scratch.

## STORAGE (from the charter)

| tier | what |
|---|---|
| primary | 20 TB external drive — the complete source corpus |
| backup | multiple 4 TB external SSDs, verified offline copies |
| scratch | NYU Torch, temporary, during extraction only |

## STEPS WE FOLLOW — to be confirmed before Monday

The mapper's own approach is the precedent worth reusing, because it already
solved the pacing problem empirically:

```
python map_acris.py          # the precedent: calibrates concurrency, then commits
```

⚠ **It measures the live link at start-up instead of trusting a constant, and
re-measures if throughput drifts.** Every fixed pacing number in this project has
been wrong: a 6-second pause invented before anything was measured (1,200x too
slow), a "ceiling at 16 connections" that was a cold-start artefact (the real one
is ~128), and a "rate limit" that turned out to be a missing cookie jar.

Its measured ladder, 2026-08-09:

| concurrency | throughput | latency |
|---|---|---|
| 32 | 3.7 maps/s | 1.00x |
| 64 | 263.1 maps/s | 1.72x |
| **128** | **291.6 maps/s** | 3.03x → stop |

Settled at 128 concurrent / ~292 maps/s. **That is the page-map endpoint, not the
image endpoint** — image acquisition must calibrate its own ladder and must not
inherit this number.

## CALIBRATIONS — to be measured Monday, not assumed

| setting | status | how it gets set |
|---|---|---|
| image concurrency | **unmeasured** | calibrate on the live link; stop when latency multiplies faster than throughput |
| per-request timeout | **unmeasured** | must exceed the slowest legitimate page, or slow pages read as missing |
| checkpoint interval | per document | nothing may be held in memory that has not been written |
| retry policy | **none on refusal** | transient network ≠ refusal; the two must be distinguishable in the log |
| daily budget | **undecided** | needs a number before starting, not after |

⚠ **A prior mapper accumulated results in memory and wrote once at the end**:
762 maps were in flight and 321 on disk when it was interrupted, and the rest had
to be recovered by re-parsing a log. Checkpoint per document.

## HOW WE PROVE ACQUISITION MATCHES SELECTION

**The work queue already exists and is correct** — `acquisition_pending` is a
VIEW, not a table (verified 2026-08-14; I had wrongly flagged it as a 17M-row
duplicate of the map):

```sql
create view acquisition_pending as
select m.document_id, m.doc_type, m.total_pages, m.no_image,
       m.instrument_from, m.instrument_to
from document_map m
left join source_document s on s.document_id = m.document_id
where s.document_id is null;
```

Zero storage. It is the selection map minus whatever has been acquired, so it
shrinks as work lands and reaching zero *is* the correspondence proof.

⚠ **BUT `source_document` IS EMPTY AND NOTHING IN THE ACRIS PATH WRITES TO IT.**
Only `dcp.py` and `to_supabase.py` reference it. So today the queue reads
17,047,262 — correct, but it will keep reading that forever while the drive
fills, because acquisition has no ledger. **This is the gap to close before
Monday:** every acquired document must be recorded, or there is no way to tell a
document that was fetched from one that was skipped, and a restart re-fetches
everything.

⚠ **AND THE 174,142 IMAGE-LESS DOCUMENTS ARE ALREADY ACQUIRED — BY INDEX.** The
view's own comment says so: *"An image-less document belongs here too until its
INDEX acquisition has run: skipping it loses the event."* `index_noimage.jsonl`
holds them, and none are recorded in `source_document`. Until they are, the queue
will keep offering documents that have no image to fetch, and a naive run will
hammer the endpoint for placeholders 174,142 times.

Per-document verification must compare files on disk against
`document_map.total_pages`. A byte count cannot tell a short document from a
truncated one.

⚠ **End-of-document is a PLACEHOLDER served as HTTP 200.** A request past the
last page does not error — it returns ACRIS's placeholder image. Page-count
verification cannot rely on "fetch until failure"; it has to compare against the
count selection already recorded.

## BUILT / UNWIRED / UNBUILT

- **Built:** `map_acris.py` (the page-map precedent, with live calibration) ·
  `fetch_pages.py` · `afetch.py` · `acquire_async.py` · `acquire_run.py`
- **Unbuilt:** the acquisition↔selection correspondence check · the budget policy
- **Measured, not blocked:** 4 procs × conc 8 → 49 pg/s → ~35 days / 9.3 TB. The
  ceiling is ACRIS's image service (20 ms connect, 6% of link), **so faster
  internet buys nothing.**

## PROMOTED DOCS

None re-read yet. `ACQUISITION_PLAN.md`, `BULK_ACQUISITION.md`,
`ACRIS_NAVIGATION.md`, `BLOCK_DIAGNOSIS.md` are the candidates — **read them
against current behaviour before Monday**, since this is the phase where a stale
rule is most expensive.

Memory: `project_acris_bulk_acquisition.md`

---

## ADDED 2026-08-17 — measured while preparing for the drive

### ⚠ THREE SCRIPTS WRITE DOCUMENTS AND ONLY ONE IS CORRECT

| script | writes | verdict |
|---|---|---|
| **`acquire_async.py`** | `{doc}.tif` multipage (+`--pdf`) | **USE THIS** |
| `store.py` / `ingest.py` | sha256 blobs + `manifest.jsonl` | a storage layer, not the fetcher |
| `devr_acquire.py`, `fetch_pages.py` | `p{n:03d}.tif` loose pages | ⚠ **these made the mess** |

The loose-page writers are why `devr_pages/` holds **42,310 files in 1,180 folders and zero
containers**, and why nothing downstream could address a document as a unit.
`acquire_async.py` treats loose pages as its **write-failure fallback**, not an output
format. Login, 2026-08-17: *"not pages. do the doc."*
⚠ And `corpus/` on disk is the BLOB store — so what is on the laptop was **not** written by
the script its own docstring describes. Check what wrote a folder before trusting its layout.

**Convert what already exists:** `python to_documents.py --dest E:/acris --dry` then without
`--dry`. It reopens every container and compares frame count to source page count; a
mismatch is reported and the document is left off the done-list. **Source is never deleted.**
1,865 docs / 47,378 pages → 1,865 containers.

### ⚠ ONLY 2 OF 59 SCRIPTS CAN BE POINTED AT THE DRIVE

`acquire_async.py` and `acquire_run.py` read `ACRIS_CORPUS_ROOT`; **57 others hardcode
`devr_pages` / `sample_pages` / `index_full` by name.** Editing 57 files risks silent
breakage. **Use a Windows junction** — every hardcoded path keeps working:

```
cmd /c mklink /J devr_pages E:\acris\devr_pages
```

### ⚠ END OF DOCUMENT IS A PLACEHOLDER SERVED AS HTTP 200

```
md5  4081a3f2004d7244a966995c02c730d0     HTTP 200, valid TIFF bytes, NOT a 404
```

**"Fetch until it fails" never fails.** Match the placeholder explicitly. Same shape:
`no-page`, `allpages` and `page-0` all return the same 13,684-byte placeholder — there is
no whole-document endpoint.

### ⚠ NEVER `convert("L")` A BITONAL SCAN INTO A PDF

Measured **15.2× inflation** — it would turn 9.3 TB into **141 TB**. Do not store PDFs at
all (0.98× the TIFF each, so keeping both is ~2× storage); generate on demand. No inline
PDF during fetch: 46 → 58 pg/s without it.

### ⚠ OPEN — IS THE CONCURRENCY KNEE US OR THEM?

| config | pages/s | latency |
|---|---|---|
| 1 × conc 8 | 15.0 | 0.41 s |
| 2 × conc 8 | 29.0 | 0.42 s |
| 4 × conc 8 | 49–58 | 0.36–0.40 s |
| 8 × conc 8 | 69.3 | **0.54–0.97 s** |

Gains run 2× → 2× → **1.4×** while latency **doubles**. The NETWORK is ruled out (20 ms TCP
connect; 69 pg/s = 33 Mbps = **6% of a 574 Mbps link**). **But client saturation and ACRIS
throttling produce IDENTICAL symptoms and were never separated.** This laptop is 8-core
running **64 concurrent connections** at the knee, so client-bound is plausible.

**The test:** repeat 8×8 logging CPU utilisation and the connect/wait split.
CPU ~100% → client-bound, more cores buy throughput, a lab is worth it.
CPU idle with rising server response → 69 pg/s is the ceiling anywhere.
⚠ Scaling within one client cooperates with the limiter. **Splitting across addresses to
multiply the rate budget does not, and stays off the table.**

---

## 2026-08-17 · THE NIGHT THE WALK STARTED — measured, on the 20 TB drive

### ⚠ ANSWERED: THE CONCURRENCY KNEE IS NEITHER US NOR THEM — IT WAS THE SELECTOR

The test above was run. **8 × conc 8 → 40.6 pg/s at 30.8% mean CPU (p90 36.1%, max
93.5%).** Neither branch of the prediction held: CPU was not ~100% (not client-bound)
and the gate never backed off once — `delay settled 0.000s` in **every** configuration
tested tonight, so ACRIS never throttled us either.

The real cost was `pick()`. It scans `acris_maps.jsonl` — **3.85 GB** — **once per
process**, so an 8-way run reads ~31 GB before fetching a single page, inside the timed
window. Selecting from the spec index instead removed it:

| config | selector | pages/s |
|---|---|---|
| 1 × conc 24 | acris_maps scan | 32.0 |
| 1 × conc 48 | acris_maps scan | **20.5** ← *slower than 24* |
| 8 × conc 8 | acris_maps scan | 40.6 |
| **6 × conc 12** | **spec index** | **53.8–56.6** |

⚠ **CONCURRENCY INSIDE ONE PROCESS IS NOT A LEVER.** 48 was 36% SLOWER than 24 with
latency up (0.48s → 0.60s). Scale processes; each one's pages are sequential by design.

### ⚠ PIL'S PDF WRITER EMITS MALFORMED G4 — USE img2pdf

`Image.save(format="PDF")` **re-encodes** CCITT G4 and produces a stream both pypdf and
MuPDF reject (`invalid code in 2d faxd`). **0 of 5 pages survived a round-trip.** It
passed every cheap check — `/CCITTFaxDecode`, `bpc=1`, exact dimensions — which is why
the filter tag is NOT evidence. `img2pdf` copies the stream: **156/156 pages
pixel-identical** across 6 documents, and file sizes land within ~3 KB of the same
documents saved from the browser.
⚠ **Verify pixels through a decoder, never a header.**

### ⚠ THREE SILENT-FAILURE BUGS, ALL OF THE SAME SHAPE

1. `pick_parcel()` returns `expect=0` for "page count unknown"; the fetch loop was
   `range(1, expect + 1)` — and **`range(1,1)` is empty**. Parcel-driven acquisition
   fetched **zero pages, always**, and raised nothing.
2. Status was `"ok" if len(frames) == expect` — with `expect=0` every COMPLETE document
   was marked `short` (**46/46** on BBL 4000110001). The resume set is `status='ok'`, so
   an overnight run would have re-fetched the same parcels until morning.
3. The driver read child output with `subprocess(text=True)`, which decodes with the
   Windows locale codec and mangles the banner's box characters — it reported **0 pages
   for batches that fetched 900**. ⚠ The **refusal check reads the same string**, so the
   one signal that must never be missed was being parsed out of mangled text.

**Count the thing, not the claim about the thing.** Progress now comes from the ledger.

### ⚠ BUILD THE SPEC INDEX ON THE NVMe, NEVER ON THE CORPUS DRIVE

Direct to USB: ~1 MB/s read, **0 B/s written**, no temp files — 40 minutes in,
`CREATE INDEX` had not started. Every insert into a keyed table is a random B-tree
write. Same build on NVMe: **17,065,090 master rows → 17,049,742 documents in 97s**,
whole index **554s**. Then move the file; it is only ever read sequentially afterwards.

### ⚠ LINEAGE IS NOT OPTIONAL, AND IT IS ALREADY PUBLISHED

DOF's Digital Alteration Book (`spine/dab_edges.json`, pulled by `dof_lineage.py`)
carries **48,157 edges** — 26,415 `merged_into`, 19,278 `apportioned_to`, 2,464
`replaced_by`. Against the spec index:

- ACRIS has named **1,250,935** BBLs; **24,416 are identities DOF has superseded**
- **lineage-aware distinct parcels: 1,226,519**
- ⚠ **545,345 documents sit under a retired name** — invisible to any walk keyed on the
  current BBL alone
- fan-out is real: `1010381002` absorbs **121** lots; `1002481004` becomes **816**

⚠ **THE GAIN DEPENDS ON THE LINEAGE TYPE, AND THE BIG NUMBER IS THE MISLEADING ONE.**
`1010381002` has 121 predecessors and gains only **+6** documents — condo *unit* lots
barely transact. `4000110001` has **3** predecessors and gains **+14 (46 → 60)**,
including a **$260,714,020 mortgage** filed under lot 4000110003. Ordinary lot mergers
matter far more than condo fan-out.

**Rule implemented:** *POST to what the document names, RESOLVE at read time.*
`lineage.family(bbl)` = the lot plus every predecessor, never successors (a later,
different parcel). Both `parcel_folder.py` and `pick_parcel()` read through it, so the
folder cannot list a document acquisition will never fetch.

### ⚠ THE 69 pg/s "CEILING" WAS A ROUND BARRIER — MEASURED 80+ WITHOUT IT

The open question above asked whether the knee was the client or ACRIS. It was neither:
it was the **driver's own barrier**, and the same laptop and the same 8×conc pool that
reported 40.6 pg/s now sustains **76–84.5 pg/s** with no change to the client at all.

Two independent barriers were costing roughly half the wall clock:

1. **Selection.** `pick()` scans `acris_maps.jsonl` (3.85 GB) ONCE PER PROCESS —
   ~31 GB of contending reads before the first page is fetched, inside the timed
   window. Selecting from the spec index removed it.
2. **Round synchronisation.** The driver submitted N parcels and waited for ALL of them
   before starting the next N. Across a 8–300 document band, seven workers idled while
   the largest parcel finished — *every round*. Wall clock was "slowest parcel per
   round" instead of "total work ÷ workers".

| shape | pages/s |
|---|---|
| 8 × conc 8, acris_maps scan, round barrier | 40.6 |
| 8 × conc 8, spec index, round barrier | 52.8–54.7 |
| **8 × conc 10, spec index, continuous pool** | **76–84.5** |

⚠ **THE GATE NEVER BACKED OFF IN ANY OF THESE.** `delay settled 0.000s` throughout, no
refusal at any point. Every gain came from removing our own waiting, not from asking
ACRIS for more. **Measure the harness before blaming the server.**

⚠ Corollary for the corpus estimate: at 80 pg/s the 148.2M pages is **~21 days**, not
the 35 on record — and the "16 days" figure OCR_STRATEGY.md flags as *never
reproducible* now looks like it needed ~107 pg/s, which remains unreached.

### ⚠ NEVER FETCH AN IMAGE-LESS DOCUMENT — 26 HAD ALREADY LEAKED

`noimage_index` holds **138,970** document ids whose index row IS the record. Selection
had no membership test, so 26 reached the fetcher, returned the placeholder, and were
written as `empty` — indistinguishable from a defect. `pick_parcel()` now filters
against the set (loaded once per process).
⚠ **The phase doc says 174,142 image-less documents; the file on disk has 138,970 —
35,172 apart. One of those numbers is wrong and it has not been resolved.**

### ⚠ AT 80 pg/s THE BINDING CONSTRAINT IS RAM — NOT ACRIS, CPU, OR THE LINK

Measured during the sustained run (8 procs × conc 10, 80 connections):

| resource | usage | headroom |
|---|---|---|
| CPU | 38.1% mean, p90 50.1% | yes |
| network | 91 Mbps recv | yes — **16% of the 574 Mbps link** |
| disk write | 8.0 MB/s | yes |
| **RAM** | **84% used, 2.7 GB free** | **NO** |

Each worker holds a whole document's pages in memory before assembly, so process count
scales memory linearly. On this laptop — 16 GB with **8 GB carved for the Arc iGPU** —
2.7 GB free is the wall. ⚠ **More cores would not help; more RAM would.** That is the
lab question worth costing, and it replaces the earlier "is it us or them" framing:
it is us, and specifically it is memory.

### ⚠ THE PARCEL-COMPLETENESS BUGS — three caps, none of them the one being tuned

A folder that reads "not acquired" forever is worse than an empty one: it looks like
work outstanding when it is finished. Three separate causes, found in order:

1. **`--max-pages` defaults to 1800 and the driver never passed it.** For a parcel pick
   the page count is unknown, so the cap charges an ESTIMATED 12 pg/doc — biting at
   **1800/12 = 150 documents** no matter how deep the parcel. BBL 4071170051 has 234
   documents; selection returned all 234; the ledger had never *attempted* 49 of them.
   ⚠ **Selection was correct the whole time.** The cause was a stopping rule nobody set.
2. **`--docs-cap` split across `--batch`.** With batch=3/cap=400 over an 8–300 band,
   only **6 of 55** parcels finished. The driver never revisits, so "later" meant never.
   Guard added: `docs_cap` is raised to `batch × hi × 2` if it would truncate.
3. **`empty` was reported as "not acquired".** `noimage_index` holds 138,970 ids; the
   phase doc claims 174,142. The gap is real: FT_1610008670761 (1966 DEED, reel
   40152/263) is **absent from the index**, returned the placeholder in 0.51 s, and was
   written `empty`. ⚠ **An `empty` result is not a failure — it is the DISCOVERY that a
   document has no image**, and the index row is its whole record. The folder now reads
   the ledger and counts those as image-less, so a parcel can actually reach complete.

After 1 and 2: parcels written in a 30-minute window went from ~0 complete to
**140 complete / 100 partial**, and the partials were missing exactly **1** document —
which was cause 3.

### ⚠ RESTARTING BY HAND BRED DUPLICATES — 6 DRIVERS, 4 WATCHDOGS

Every manual relaunch left the previous driver alive, and because a watchdog restarts a
driver it believes is missing, the copies **breed** rather than accumulate. Each one
drew on the same address-level limiter while believing it was the only client.
`only_one()` now refuses to start a second copy (PID file + a liveness AND cmdline
check, because a killed process leaves its PID file behind).

⚠ **AND THE WATCHDOG'S OWN PROBE WAS BLIND.** It shelled out to `wmic`, which is
deprecated and **absent from this machine's PATH**; the call raised, the except branch
returned "assume alive", and it would have guarded nothing all night. It uses psutil now.
⚠ A guard whose probe can only answer "fine" is not a guard — test the probe, not just
the guarded thing.

### ⚠ A PARCEL-COMPLETE WALK IS 60% TRANSFER-TAX RETURNS

Measured over the first 111,505 documents of the 2026-08-17 overnight walk:

| doc_type | count | share |
|---|---|---|
| **RPTT&RET** | 66,387 | **59.5%** |
| ASST | 9,693 | 8.7% |
| MTGE | 6,601 | 5.9% |
| AGMT | 6,011 | 5.4% |
| RPTT | 4,847 | 4.3% |
| DEED | 4,730 | 4.2% |

⚠ **NOT A DEFECT — A CONSEQUENCE OF THE UNIT OF WORK.** Walking whole parcels means
taking every instrument on them, and tax returns outnumber conveyances several to one.
They also EARN their place: the index reports `document_amt=0` and the price lives on
the RPTT/RETT stamps.

But it is the number to know before choosing a selection axis. **Parcel-complete and
type-targeted are different corpora**: 4,730 deeds cost 111,505 documents here, and a
type-first pull would have bought them in a fraction of the requests — at the cost of
never holding one parcel's story end to end. Pick the axis from the question being
asked, and do not let a walk chosen for chronology be judged as if it were a sample.

### ⚠ EVERY RESTART PAYS A FAST-FORWARD TOLL — DO NOT TUNE A RUNNING WALK

The pool is `ORDER BY n_docs DESC`, deterministic and always from the top. On restart the
driver re-walks every parcel it already finished; the ledger's `done` filter means it
fetches nothing, but it still spawns a process per group and reads the spec for each.
Measured 2026-08-17: after a restart at 608 parcels, the run logged **0 pages for 14
minutes** while it cleared the completed head at ~51 parcels/min.

⚠ **The rate line reads 0.0 pg/s during this and looks exactly like a dead run.** It is
not — check the ledger delta and the parcel counter, which keep moving.

Three restarts were spent chasing throughput (conc 8→10, batch 1→3, a cap fix). The cap
fix was worth it — parcels were coming out truncated. The tuning was not: each toll was
~14 minutes against a batching gain of maybe 9%. **Tune on a short pool, then start the
long run once.** A walk that is producing complete parcels should be left alone.

### ⚠ A MANIFEST IS A SNAPSHOT, AND IT GOES STALE BEHIND YOUR BACK

Six parcels read "not acquired" across four consecutive checkpoints and looked like a
hard failure. They were not: the ledger said `ok`, the PDFs were on disk at the exact
expected path, and **0 of 145,914 `ok` documents lacked a file**. The `_INDEX.md` had
simply been written BEFORE those documents landed, and nothing rewrote it — the driver
only materialises parcels IT processed in THAT run, so a parcel topped up by a later run
keeps an old manifest forever.

⚠ **The stale artifact was the measurement, not the corpus.** Every completeness figure
reported during the night was computed from those files, so the run looked worse than it
was. Refresh all manifests before reporting, and treat "the folder says X" as a claim
about the folder, not about the store.

⚠ The cheap cross-check that settles it in one query: for every ledger row with
`status='ok'`, assert the PDF exists at `documents/{id[:2]}/{id}.pdf`. If that holds, the
corpus is intact regardless of what any manifest says.

## ⚠ ANSWERED FOR GOOD: THE CONCURRENCY KNEE IS ACRIS, NOT US

The doc has asked since the drive arrived whether the knee was client saturation or
server throttling, noting the two "produce IDENTICAL symptoms and were never separated."
Separated 2026-08-18 on truly-fresh parcels (no document of the parcel in the ledger),
with the indexed selector so no 3.85 GB scan pollutes the window:

| connections | shape | pages/s | mean latency | max |
|---|---|---|---|---|
| 20 | 1 × conc 20 | 58.3 | 0.28 s | 5.4 s |
| **80** | **1 × conc 80** | **89.3** | 0.68 s | 8.4 s |
| 140 | 1 × conc 140 | 59.9 | 1.43 s | 31.7 s |
| 140 | **2 × conc 70** | **61.0** | 1.85 / 0.97 s | 22.6 s |

⚠ **THE LAST TWO ROWS ARE THE ANSWER.** Same 140 connections, split across two
processes instead of one: 61.0 vs 59.9 pg/s. If the ceiling were client saturation —
one Python process minding 140 sockets — splitting it would have helped. It did not.
**The far end sets the limit, and past ~80 connections latency rises faster than
throughput, so more concurrency returns LESS.**

⚠ **AND PROCESSES WERE NEVER THE LEVER.** 1 × conc 80 = 89.3 pg/s matches what 8 × conc
10 achieved. The earlier "scale processes, not threads" conclusion was an artefact of
`pick()` scanning acris_maps.jsonl once per process; with an indexed selector the
process count only changes memory. **Prefer FEW processes at high concurrency**: 2 × 40
holds ~80 connections for ~360 MB instead of ~1.4 GB across eight.

⚠ **COROLLARY — MORE MACHINE WILL NOT BUY SPEED.** At the 80-connection optimum: CPU
38%, network 91 Mbps of a 574 Mbps link (16%), disk 8 MB/s. Nothing local is saturated.
The earlier "more RAM would help" note is superseded: RAM limits how many PROCESSES fit,
and processes were never what produced throughput. **~90 pg/s is the corpus rate**, so
148.2M pages is ~19 days of continuous running, and the only remaining levers are
fetching FEWER pages or a different endpoint — not asking harder.

### ⚠ AT A FIXED 80 CONNECTIONS, THE SHAPE STILL MATTERS — PIPELINE FILL, NOT LOAD

Having established that ~80 connections is ACRIS's optimum, the remaining variance is
ours. Measured 2026-08-18, every arm holding **exactly 80 connections**:

| shape | pages/s |
|---|---|
| 2 × conc 40 | 79.0 |
| 1 × conc 80 | 89.3 |
| 8 × conc 10 | ~90 |
| **4 × conc 20** | **93.8** |

⚠ **Identical load on ACRIS, 19% spread in throughput.** The driver hands each process a
batch of parcels; when a batch ends, that process must respawn (~1.5 s: interpreter,
PIL, aiohttp, the 138,867-id image-less set, the lineage edges) before it fetches again.
With 2 processes a handover idles HALF the connection pool; with 4 it idles a quarter.
Below that, per-process fixed memory starts to dominate again.

**Rule: pick the process count from handover cost, and the concurrency from
80 ÷ processes.** 4 × 20 is the measured sweet spot on this machine — ~720 MB resident,
93.8 pg/s, and ~18.3 days for the 148.2M-page corpus.

⚠ Do not read this as "more processes is better" — that was the error the acris_maps
scan induced. Total connections is what ACRIS sees and what caps throughput; process
count only decides how much of that budget sits idle during a handover.

---

## 2026-08-18 · THE STANDING RUN — what supervises acquisition, and why each piece exists

Login's instruction, 2026-08-18: *"if the drive is plugged in and the wifi is on then this
needs to be running essentially unless I say otherwise."* Four processes hold that up.

| process | question it answers | stops when |
|---|---|---|
| `overnight.py` | walk parcels, fetch their documents | `--until`, or `_STOP` |
| `watchdog.py` | did the driver die mid-run? | `--until`, or `_STOP` |
| **`supervisor.py`** | **should anything be running at all right now?** | a refusal, or `--max-starts` |
| **`checkpoint_loop.py`** | how is it going, every 10 min | `_STOP` |

```
ACRIS_CORPUS_ROOT=D:/acris nohup python supervisor.py --until 23:59 &
ACRIS_CORPUS_ROOT=D:/acris nohup python checkpoint_loop.py &      # -> logs/checkpoints.log
```

### ⚠ THE SUPERVISOR EXISTS BECAUSE FOUR DIFFERENT SILENCES LOOK IDENTICAL

A driver that is not running gives no clue which of these happened, and they need opposite
responses:

```
drive absent           -> WAIT.  Login moved locations with the drive. Not a stop.
link down              -> WAIT.  Not a stop.
_STOP "paused by hand" -> WAIT for Login. This IS "unless I say otherwise".
_STOP "refused"        -> ⚠ NEVER RESTART. Report and exit.
```

So the flag is **read**, not merely tested for existence. The two writers produce
distinguishable text — `overnight.py:268` writes `refused`, `pull.py:107` writes
`paused by hand <when> — <why>` — and both strings were tested against the guard before it
was trusted. Auto-restarting a refusal would cost Login their own ACRIS access while
they are away; the limiter is address-level.

### ⚠ THE SELF-COUNT BUG, THREE TIMES IN ONE DAY

Every process-enumerating guard here got this wrong at least once:

| guard | what it did | effect |
|---|---|---|
| `watchdog.driver_alive` | probed with `wmic`, absent from PATH | always "alive" — would never restart |
| `watch10.procs` | substring-matched whole command lines | reported `driver 4` with ONE driver running |
| `supervisor.running` | counted its own PID as an existing supervisor | singleton guard guaranteed **zero** instances |

**Match the script the interpreter is running (`argv[1]`, skipping `-u`), exclude your own
PID, and require `name` to start with `python`.** A monitor that cries wolf about duplicate
drivers is worse than no monitor, because duplicates breeding is a real failure here.

### ⚠ THE MONITOR MUST BE CHEAPER THAN WHAT IT MEASURES

Measured 2026-08-18: a `reopen.py` full sweep plus a stray-process backlog, run while the
walk was going, dropped the rate **from ~85 to 54.7 pg/s** — the monitoring was briefly the
single largest drag on the thing it monitored. The checkpoint therefore does two ledger
reads and one directory enumeration (0.3 s for 7,400 parcels) and **never** reads a
manifest or queries the spec DB. Save manifest walks for a pause.

### ⚠ THE STORE'S 3-WAY SHARD IS UGLY AND MEASURABLY FINE

`documents/{doc_id[:2]}/` yields only three shards, because ACRIS ids have three prefixes:
`20…` 69.7% · `FT_` 26.8% · `BK_` 3.5%. At full corpus that is ~11.9M files in one
directory. **Measured before assuming it was a problem:** `os.scandir` reads 214,030
entries in 0.1 s (1.5M/s), projecting to ~8 s for 11.9M; a lookup by name is 11 ms, which
is USB latency and not directory size. NTFS indexes directories as a B-tree. **Do not
restructure 17M files over this.**

### NAMING — settled, and why

```
by-parcel/{boro}/{block}/{lot}/          3/00247/0009
    {date}__{doc_id}__{type}__{reel}-{pg}.pdf
    1974-01-07__BK_7430068201487__DEED__682-1487.pdf
documents/{doc_id[:2]}/{doc_id}.pdf      the bytes, once; by-parcel hardlinks to them
```

- **BBL** is the join key for every other NYC source (PLUTO, DOB, DOF, HPD, DCP). Anything
  else needs translating at every boundary. Zero-padded so lexical sort = numeric sort, and
  split three levels so no directory holds 1.25M entries.
- **date first** is what makes a parcel readable oldest-to-newest in any file browser with
  no tooling at all. That is the whole point of the layout.
- **doc_id** is ACRIS's own key and the image URL is a pure function of it — a filename is
  enough to re-fetch the document.
- ⚠ **A BBL IS A CURRENT LABEL, NOT A PERMANENT IDENTITY.** 24,416 named BBLs are already
  retired and 545,345 documents sit under superseded names. `parcel_folder.rows()` resolves
  the lineage family at read time, so a folder shows its predecessors' documents — but
  nothing downstream should treat a path as an identifier.

## 2026-08-19 · ⚠ THE IMAGE LAG WINDOW REACHES INTO ACQUISITION, AND IT WAS RETIRING DOCUMENTS FOR GOOD

**The policy already existed and acquisition could not see it.** `image_policy.py` is the
one image policy for both sources — `pending` → probed each daily run while
≤ `TERMINAL_DAYS`=7 old → `imageless`. It is a *specification* rule. Acquisition never
imported it, so the rule was a config sitting one directory away from the code that
needed it. (The recurring shape: the fix exists and is unaddressable, not missing.)

### The loss, and why every count read clean while it happened

```
document recorded 3 days ago, scan not yet attached
  -> fetch returns the END-OF-DOC PLACEHOLDER (HTTP 200)
  -> ledger row written `empty`
  -> parcel_folder.empty_ids() folded it into the image-less set
  -> _INDEX.md rendered it "**no image** — index is the record"
  -> the manifest now has NO outstanding row
  -> overnight.py tests for "| not acquired |" -> parcel marked COMPLETE
  -> the parcel is never queued again. The scan attaches on day 4. Nothing asks.
```

Every number along that path is correct and the outcome is a permanent false claim:
*"this document has no image, the index is its whole record"* — asserted about a record
nobody finished looking at. **`pending` and `imageless` are INDISTINGUISHABLE on any
single read; only AGE separates them.** A placeholder proves nothing until the window
closes.

### The fix — three files, and the second one is the half that is easy to miss

- `parcel_folder.empty_ids()` now returns **(terminal, pending)**, splitting the ledger's
  `empty` rows on `image_policy.is_terminal()`. Clock = the spec's `recorded_date`,
  falling back to the ledger's `at` (when we asked), exactly as image_policy does, so a
  dateless record is never immortal. ⚠ The clock must come from the SPECIFICATION — the
  ledger only knows when *we* asked, and the window is measured from RECORDING.
- `_INDEX.md` gained a third state, `pending scan`, counted as **outstanding**.
- ⚠ `overnight.py` had to change too. It decides completeness by string-matching the
  manifest, so a new state that it does not know about is invisible: the parcel would
  still have read complete and the fix would have done nothing. It now tests
  `("| not acquired |", "| pending scan |")`. Old manifests predate the marker and are
  unaffected, so it is safe over what is already on disk.
  **A new state is not wired until every reader of that state knows it.**

### Verified on real data, not on a counter sitting at zero

1,893 ledger `empty` rows split **1,888 terminal / 5 pending**. The five are not noise —
they are a **DEED and two MORTGAGES from one closing** (`2026072800456001/002/003`, one
submission, sub-indices 001-003) plus two RPTT&RET, recorded 2026-08-12/13 and asked
2026-08-18. All five were being written off permanently. None of their three parcels had
a manifest on disk yet, so nothing needed repairing — the exposure was entirely forward.

⚠ **THIS CONTRADICTS THE "ACRIS HAS NO LAG" CALIBRATION** (`LIVE_SYNC.md`: *ACRIS 400/400
imaged same-day, so its pending set drains on the first probe*). Back-check of every
`empty` row by ask-minus-record interval:

| asked after recording | empty rows |
|---|---|
| same day | 0 |
| 1–3 d | 0 |
| 4–7 d | **6** |
| 8–30 d | 4 |
| 1–12 mo | 38 |
| > 1 yr | 1,845 |

35 of them were recorded in 2026 (RPTT&RET 13 · MTGE 5 · ASST 5 · DEED 2 · …). The
same-day claim was measured on a 400-document sample that evidently did not include the
slow types. **The 7-day window is not Richmond-only. Do not narrow it to one source.**

### The standing rule for every phase after this

**A document already recorded in the specification can still acquire its image later.**
So: acquisition may never treat a placeholder as terminal inside the window, a parcel may
never be marked complete while it holds one, and anything that lands late must re-enter
the pipeline — **a newly acquired image is new input to extraction, not just a file on
disk.** Acquisition's job does not end at the byte.

> ⚠ **READ [transport.md](transport.md) BEFORE TUNING ANY WIDTH.**
> Whether ACRIS serves us is decided by the TRANSPORT, not the worker
> count: a pooled client holding N warm sockets and a client opening N
> cold TLS connections per second are different animals at the same
> document rate. `image_walk.py` standalone is the cold path and must
> not run — pdf goes through `acris_lane`. (2026-08-27)
