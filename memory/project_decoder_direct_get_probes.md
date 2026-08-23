---
name: project_decoder_direct_get_probes
description: "Both custodians' edge probes are plain GETs (no session/token); ACRIS has no usable date window and Socrata is 23 days stale"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-23T20:53:39.163Z
---

Settled 2026-08-23. **Both monitor lanes are single plain GETs — no session, no
token, no pacing sleep.** A full tick across both custodians is 3 requests, ~2s.

    richmond  GET /Search/DateRangeSearch?StartSearchDate=..&EndSearchDate=..
              &SelectedDocumentIdentifier=0            0.6-0.7s  (login found it)
    acris     GET /DS/DocumentSearch/DocumentDetail
              ?hid_CRFN=<n>&SearchType=DocID           0.5-0.9s

`hid_CRFN` works as a QUERY PARAMETER. The old path (`live_crfn.detail_html`)
POSTed it with `__RequestVerificationToken` + session + `LD.PACE` — none of that
is checked on this route. Measured: live CRFN = 131,544 bytes with a doc_id;
absent = 10,182-byte stub with none. 13x gap, but **the parse is the test, not
the size**. Helper: `acris_edge.quick_crfn()` → `(state, doc_id)`.

⚠ **THE PROBE RETURNS THE DOC_ID, SO THE PROBE *IS* SYNC.** The 131KB detail
page is the record. The monitor used to read the doc id, discard it, and fire
sync to re-fetch the identical page. Login caught it: *"if monitor can get new
doc id without sync... this should become the new sync."* Now `sync_fast.py`
walks the edge itself; the monitor's remaining job is a LEVELNESS AUDIT
(system/source/delta per source, 0 = level) that is **not part of the pipeline**.

⚠ **ACRIS HAS NO USABLE DATE WINDOW — three dead ends, do not re-explore:**
- ID/CRFN search: no date field at all (confirmed on the options page).
- Document **TYPE** search: HAS `cmb_date` = `7` (Last 7 days) / `31` / `DR`
  (range) — but **requires a doc type**, so "everything today" is ~60 searches.
  And it refuses GET: every parameter set returns the same **21,724-byte
  search-options menu**. The tokened POST bounced back to the form too (47KB).
- Socrata `bnx9-e6tj`: has `recorded_datetime` and **stops at 2026-07-31**. Top
  CRFN 2026000216051 vs our edge 2026000237865 — **21,814 documents / 23 days
  behind us.** A date monitor there reports calm through three weeks of filings.

So ACRIS must COUNT (dense CRFN counter) where Richmond can DATE. Login's
date-delta reasoning was right — a re-read window makes delta a set difference,
self-healing, no watermark — the source just won't sell it. See
[[project_acris_selection_job]], [[project_rc_rd_coded]].

**CRFN IS STORED — inside `recorded_details`, not as a column.** (Corrects an
earlier note here that called it a blocker.) `navigation` is id|rd_url|pdf_url|
recorded_details|pdf|keyed_by|key, but `rd_parse.parse_acris` captures `crfn`
into the rd JSON, so the levelness audit needs no schema change — only a column
if the scan proves too slow. ⚠ The parsed value carries a trailing HTML entity
(`"2026000237863 &nbsp;"`), which will silently break any exact-match join.

⚠ **PIPELINE RESTRUCTURED 2026-08-23 (login's design).** TWO SYNCHRONIZATION
SERVICES, both 10s, both 1 request on a quiet tick. Synchronization owns
everything up to the pdf; a separate pdf lane runs alongside; **org is the
natural close of both and costs ZERO requests** — `nav_key.py` reads
`recorded_details` from the db and never touches the network.

    acris_live.py --apply --every 10   crfn+1      -> id + rd_url + pdf_url + rd
    rc_live.py    --apply --every 10   date window -> id + rd_url + pdf_url

ACRIS's probe URL IS its rd_url, so rd arrives inside the detection request:
**2 requests take a document from nonexistent to fully keyed to a BBL.**
Richmond's rd is guarded and stays a separate in-session POST, so its rows land
with `recorded_details=''` and the rd lane picks them up. `phase_monitor` is
retired — both halves now live in their own service.

⚠ **RICHMOND'S NEW ROWS ARE ON THE *LAST* PAGE.** The day sorts ASCENDING by
instrument at 17/page, so `quick_day(day)` (page 1) watches the part of the day
that never changes again. `rc_live` caches today's last page in
`_rc_live_page.json`, fetches THAT page each tick (1 request — quick_day takes a
`page=` argument and returns the total page count), follows overflow when the
count increments, and resets the page at midnight. A full-day sweep every 900s
covers the one blind spot (a row inserted into an earlier page) — but is
SUPPRESSED when a cold start already walked 1..pages, which otherwise re-read
every page and reported **205 rows on a 103-document day**.

⚠ **A QUIET TICK MUST COST 1 REQUEST, BUT THE 8-BLANK WALK CANNOT BE DROPPED.**
Walking CONFIRM_BLANKS every tick = 9 requests = 54/min at a 10s cadence. But
stopping at the first blank forever stalls on a permanently unissued crfn —
re-asking one dead number while documents pile above it. Fix is shallow-every-
tick + DEEP every `--deep-every` (300s), so a hole costs 5 minutes, not forever.

⚠ **NAVIGATION AND ORGANIZATION ARE DATABASE TRIGGERS, NOT PHASES THAT RUN.**
Three triggers on `navigation`: `mint_urls` (AFTER INSERT — mints both urls from
the id, dispatching on the `RC_*` prefix), `key_rules` (BEFORE UPDATE — restricts
keyed_by to parcel/reference/pdf-pass/pdf, making bad states unrepresentable),
and `key_on_rd` (AFTER UPDATE OF recorded_details — keys the BBL in the SAME
transaction, since the rd carries it for ~99.7% of the corpus).

⚠⚠ **`key_on_rd` IS `AFTER UPDATE`, SO A ROW THAT ARRIVES WITH THE RD ALREADY
FILLED IS NEVER KEYED.** The first `acris_live.py` INSERTed recorded_details
directly and every document it landed would have been UNKEYED — invisible,
because the row is complete in every other column and the only lane that selects
"rd but no key" is the backfill keyer, which `org_backfill_arm.py` deliberately
holds until acris rd hits 99.95%. **Fix: INSERT with `recorded_details=''`, then
UPDATE it, in one transaction** — the way rd_walk writes. Verified against a
scratch copy of the real schema; never assume a trigger fires on insert.

⚠ **ORGANIZATION IS DISSOLVED AS A PHASE (login 2026-08-23): keying is "part of
the natural progression of rd under pass 1."** Three passes: pass 1 = key_on_rd
trigger keys parcel/pdf-pass IN THE SAME COMMIT as every rd landing (keyed count
≡ rd-landed count, zero lag by construction); pass 2 = at rd 100%, reference
keyer over the pdf-pass pool (cites are doc_id→id direct PK hits, or crfn→id
matched against the target's own rd); pass 3 = at pdf 100%, pdf-read keyer; the
residue genuinely has no BBL and stays pdf-pass ("party is DECODING, not a key").
The 2026-08-23 backfill (org_key_cursor.py) keyed 4,487,749 in 44 min (94.9%
parcel / 5.1% pdf-pass) after DROPPING ix_nav_key — the index made key writes
1,482x slower (94/s vs 138,774/s; every key = a random insert into a 24M-entry
b-tree) — then rebuilt it once in 27 min. ⚠ pdf-pass, NEVER blank, for
"rd read, no bbl": blank must mean only "never examined" or completion becomes
unprovable. ⚠ The board's 5.9M backlog estimate overshot the real 4.49M because
TRIGGER-KEYED ROWS WRITE NO LOG LINES and the board counted org from nav_key
logs. org_backfill_arm is now redundant — repurpose as the pass-2 arm.

⚠ **ORG SHOWING 0.00/s IS CORRECT, NOT A STALL.** `org_backfill_arm` measured it:
backfill now → org 26h / rd 56h; backfill after → rd 45h / org 49h = **7h sooner**.
Keying is a follower with nothing downstream (extraction is not running), so
early keys cost 30-40% of the fleet and buy nothing. Board status `TRIGGER` means
the trigger handles new landings; the ~6.0M unkeyed are pre-trigger rows, which
a trigger cannot reach — "a trigger has no past tense".

⚠ **RICHMOND CANNOT DO crfn-STYLE +1, FOR TWO INDEPENDENT REASONS.** Measured
08/21: `instrument` is perfectly dense (1017248..1017350, 0 gaps) but
`internal_id` — the number the URLs take — DECREASES 36 times as instrument
ascends, spanning 6,077 values for 103 documents (**58 blanks per hit**). And no
route accepts an instrument number (candidates 404). On top of that,
`/Search/viewDocumentInfo/<id>` cold returns HTTP 200 + "INVALID REQUEST:
UNAUTHORIZED SEARCH ACCESS" — the rd needs a live search in the same session,
re-POSTing the results form with `ViewDetailsButton=<internal_id>`
(`rc_source.py:45`, which already documented this before I re-probed it).
Richmond keeps the date window: 17 rows per request beats +1 anyway.

⚠ **A 403 MUST NEVER BE RETRIED AND `check_refused` CANNOT SEE ONE** — it runs
only after a body is read, so an HTTPError bypasses it. `quick_crfn` now raises
immediately on 401/403/429 and retries only 5xx/307.

⚠ **503 SITE-WIDE IS NOT A REFUSAL AND NOT OUR DOING.** 2026-08-23 11:04
a836-acris.nyc.gov returned 503 on every route *including the bare root* — the
root is the control that proves it's the host, not us and not one route. Report
NOTHING, never "quiet", and never a traceback: an unreachable host must read as
one line saying we learned nothing. See [[feedback_confidence_backcheck]].

⚠ **A CRFN IS AN IDENTIFIER, NOT A QUANTITY.** `f"{edge:,}"` rendered
2026000237865 as "2,026,000,237,865" — reads as two trillion and invents a third
number namespace out of pure formatting. Never comma-group an id.
