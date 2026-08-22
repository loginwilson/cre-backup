# LEGAL INSTRUMENTS — NAVIGATION

**The phase's one claim: every id in the Legal Instruments db is TABLED with
its two endpoints minted.** Sync (00) proves the ids are all there;
navigation proves each has a row ready for acquisition (02) to fill.

**The db:** `D:\CRE Decoding System\Legal Instruments.db` — THE one table,
shared by phases 01–03, columns in phase order (reading a row left-to-right
is the phase walk):

    id | rd_url | pdf_url | recorded_details | pdf | keyed_by | key
    \____ 01 navigation ____/\__ 02 acquisition __/\_ 03 organization _/

**The feed:** sync's step 5 calls `nav_append.py` — the ONE inserter.
INSERT OR IGNORE, never upsert (an upsert would blank a `recorded_details`
we spent a request on). A new row carries only id + the two urls; **an empty
cell IS the work list** — rd_walk selects `WHERE recorded_details=''`,
image_walk `WHERE pdf=''`, the keyer `WHERE keyed_by=''`. An appended row is
picked up by running lanes with no signal, no scheduling, no restart.

**The urls are pure functions of the id** — nothing is fetched to mint them:

    ACRIS     rd  .../DocumentSearch/DocumentDetail?doc_id={id}
              pdf .../DocumentSearch/DocumentImageView?doc_id={id}
    RICHMOND  rd  .../Search/viewDocumentInfo/{internal}
              pdf .../ViewVscmsDocument/ViewContent?p_endorsementId={internal}

⚠ **The Richmond rd is the one exception to a straight GET**: the address is
minted like any other, but the page behind it renders only in a browser
after a search grant (per-result-set, measured 2026-08-21). The MINT is
still nav's job; the special ACCESS is acquisition's Chrome lane.

## MINT REGARDLESS — the image states belong to ACQUISITION

Nav mints both urls for EVERY id, unconditionally. Every document has an rd;
a small number never get an image — but a pdf url that leads nowhere does
NOT mean imageless, and nav must not try to know the difference. Acquisition
distinguishes, using the measured lag:

    pdf url dead + id young  -> PENDING  (re-probe each run while <= 7 days)
    pdf url dead + id aged   -> IMAGELESS (decaying tail re-probe, never
                                 abandoned - 174,142 known on ACRIS)

    lag, measured: ACRIS scans attach SAME-DAY (400/400) ·
                   RICHMOND overnight, a step at ~24 h (age 0: 0/15, age 1: 11/11)

This phase completes when every single id has its urls. What the urls
resolve to is the next phase's claim.

## HOW MINTING HAPPENS — structural first, routine second

**Layer 1 — STRUCTURAL (the `mint_urls` trigger in the db itself).** Fires
on every insert, branching on the id's namespace (`GLOB 'RC_*'` → the
Richmond pair from the internal number; anything else → the ACRIS pair): a
row landing without its urls gets them in the same transaction, whoever the
inserter is — sync, a census landing, any future path. A bare row is
UNREPRESENTABLE, not detected later. Minting is not a routine that runs;
it is a property the table has. (Proven 2026-08-21 on known-bare inserts in
both namespaces — and the first version was caught by its own control:
`LIKE 'RC.%'` never matches, `GLOB 'RC_*'` does.)

**Layer 2 — THE ROUTINE (`routine_navigation.py`), the phase audit.** The
trigger enforces; the audit PROVES — daily at 4:20 AM, after sync. Six
steps:
count per source → count rows missing urls → mint the missing → write the
`navigation` rows to the update board → CHECK: missing = 0 AND table total
= sync ledger total (report a mismatch, never repair it). First run
2026-08-21: **NAVIGATION LEVEL** — acris 21,615,110 · richmond 2,426,803,
both equal to the ledger, zero missing urls.

## DOCTRINE

- ⚠ **The ACRIS watermark is `MAX(id) WHERE id < '3'`**, never `< 'RC_'` —
  ids sort `2026… < BK_ < FT_ < RC_`, so an unbounded MAX returns microfilm
  and silently skips every new recording.
- ⚠ **Point probes, never scans, while lanes write** (measured: one
  unguarded scan dropped rd from 17 to 1.5 docs/s). The routine's full
  count runs only behind its busy-guard; the 5-minute board reads
  denominators, never the table.
- The `pdf` column is a computed path, not evidence — acquisition's gate
  proves the file, not this table.

## THE RUNNING SYSTEM — nav is the trigger, not a stage (LOCKED 2026-08-22)

Navigation is COMPLETE for the closed corpus (both sources 100%) and stays
complete by construction: the `mint_urls` trigger mints every new id's
urls inside sync's own insert transaction, so the acquisition lanes' empty
cells appear already-addressed. The 4:20 AM audit only proves the claim;
it never performs the work. Lane configuration: see the LOCKED
CONFIGURATION block in the acquisition md.
