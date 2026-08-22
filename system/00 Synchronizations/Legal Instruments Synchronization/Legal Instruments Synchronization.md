# LEGAL INSTRUMENTS — SYNCHRONIZATION

**The phase's one claim: every document id both custodians hold is named in the
Legal Instruments db.** Sync counts, names the delta, lands it, and proves
delta = 0. It never writes anything else.

**The routine:** `routine_synchronization.py` (decoder root). Scheduled daily
4 AM ('ACRIS Live Sync 4AM') and runnable on demand. Six steps per source:

1. **System total** — count the source's ids in the Legal Instruments db
2. **Source total** — read the custodian's own count, live
3. **Delta** = 2 − 1
4. **Gather the delta's doc ids** — landed into the sync db LIVE, along the walk
5. **Send the ids to the Legal Instruments db** (`nav_append.py` — the one inserter)
6. **Confirm delta = 0 — if not, kick off again** (bounded 3 rounds)

The loop converges because each round's delta is only what recorded during the
previous round (~4–5 docs/min): proven live 2026-08-21, 2,146 → 230 → 19 → 0.

**The db:** `Legal Instruments Synchronization.db`, one table:

    synchronization: date | source | system_total | source_total | delta | doc_ids

One row per source per day; a same-day re-run MERGES (union of ids), never
replaces. TOTAL row always bottom, derived from every source's latest row.
The board (`D:\CRE Decoding System\Updates\`) reads this db every 5 minutes.

---

## ACRIS — the CRFN edge walk

CRFN = YYYY + a dense per-year serial, so the live edge is found by counting.
`crfn_monitor.py` owns it: open a real session (cookies + browser UA — measured
2026-08-09: cookie-less died by request 5; a real session at 40× the rate had
zero refusals), then **control → gallop → bisect → confirm 8 blanks**, 2.5 s
pace. The control is the map's own highest CRFN: it must resolve or the run
stops — a malformed probe classifies every real document as absent.
CRFN → doc id via the doc-id endpoint; never subtract CRFNs across a year
boundary (2026000233436 → 2027000000001).

⚠ The sequence has HOLES (2009: a gallop from seq 1 stopped at 122 with
430,881 held). Any edge probe seeds at the held count and confirms with a
spread, not consecutive blanks (`acris_census.py` has the fixed probe).

## RICHMOND — the date-range window

The county redesigned the site 2026-08-21; `rc_window.py` owns the new one:

    GET /Search/DateRangeSearch?StartSearchDate=YYYY-MM-DD&EndSearchDate=YYYY-MM-DD
        &SelectedDocumentIdentifier=0&pageNumber=N

Rows carry recorded date · type · **internal id** (in the ViewDocumentInfo
href) · instrument. 17 rows/page fixed; 'Page N of M' carries the count;
windows ≤ 30 days (longer returns a SILENT zero). Sync asks
[watermark − 3-day lookback .. today] and deltas against the db.
⚠ Detail pages are a browser-only shell with a per-result-set grant —
acquisition's Chrome lane, never sync's. Two id namespaces (instrument,
internal id) with no derivable relation; never compute one from the other.

---

## DOCTRINE

- **A zero is only verified by a KNOWN-NONZERO control.** `rc_window.control()`
  parses a window that provably holds 315 docs and raises ProbeBroken rather
  than return empty. (The redesign made the old parser read 0 everywhere; the
  false LEVEL stood ~6 h and hid 215 documents.)
- **An unreachable source is a REPORT, not a crash.** DNS blips (the VPN) kill
  requests, never the routine's state.
- **On a refusal: stop dead.** No retry, no rotation, wait for a person.
- **Never repair a number to make a check pass** — report the failure.

## COMPLETENESS — how "no id missing, ever" is proven (2026-08-21)

The daily sync proves levelness at the EDGE. Whole-inventory coverage is
proven per custodian by the custodian's own enumeration:

- **ACRIS** = Socrata master indexes (100% to their refresh, ~weekly;
  count DISTINCT ids — the masters carry duplicate rows) + the CRFN walk for
  the tail since refresh. Verified 2026-08-21: every year band 2003–2024
  matched to the document; 2026's gap = the refresh lag the walk had already
  covered. Microfilm (FT_/BK_, no counter) matches the index it came from.
  `acris_census.py` independently bounds each year issued-vs-held.
- **RICHMOND** (no bulk index exists) = `rc_census.py` sweeps every date
  window 1850 → today and collects every internal id the county has ever
  listed. Identity: **held + missed + void = range**. Missed ids land through
  sync; voids go to the VOID LEDGER, never the Legal Instruments db.
  (Records actually begin ~1914; an early-2020 band burned ~200k ids in two
  weeks — system migration, resolved as void by the census.)

## THE RUNNING SYSTEM — sync is the kick-off (LOCKED 2026-08-22)

Both custodians are CLOSED (acris 21,615,734 · richmond 2,501,589, each by
its own enumeration, richmond rd table-counted 100%). From here sync is the
ONLY entry point for new work, and every downstream step is structural:
sync lands a new id → the db's `mint_urls` trigger mints both urls in the
same transaction → the acquisition lanes select empty cells continuously
(no signal, no restart — the Richmond rd walker and the pdf feed chain are
standing followers) → organization keys when acquisition hands it context.
The 4:00 AM run IS the daily adjustment; nothing else needs starting.
The full lane configuration and its experiment-measured prices live in
`02 Acquisitions/…/Legal Instruments Acquisition.md` — THE LOCKED
CONFIGURATION block.

## THE LEDGER — end-of-run semantics (reformed 2026-08-22)

Every measured run writes its row — A MEASURED ZERO IS A ROW (a level run
that writes nothing is indistinguishable from a run that never happened;
that ambiguity cost a false "richmond didn't run" on 2026-08-22). Columns
are END-OF-RUN STATE: `system_total` = our count AFTER the run's landing
recount · `delta` = STILL OUTSTANDING (0 = level — the zeroing visible
per source per day) · `doc_ids` = the day's catch (same-day runs union
it; state columns always carry the latest run's truth). TOTAL therefore
adds up in both columns whatever dates it mixes: our-now vs their-now.
Rows before 2026-08-22 carry the old run-start semantics.

⚠ THE MATURATION LAG: a doc landed the day it was recorded freezes a
premature rd — instrument BLANK (the county publishes "Document No." ~a
day late; and the label carries a PERIOD on modern pages — the parser
must accept `Document No\.?`) and image_state 'absent' (the scan lag).
`rc_rd_refresh.py` (runs inside the sync routine daily) re-walks young
premature docs until they mature — this is what fills the
internal-id ↔ instrument bridge the audits read, and what flips
image_state so rc_mint ever selects their pdfs.
