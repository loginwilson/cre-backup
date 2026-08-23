---
name: project-acris-decoder
description: "ACRIS document-level decoder — DEVR GRADUATED (12/12 validated incl. blind condo test, 0 code changes), Supabase live w/ balanced postings; decode by function family not code; images transient, facts permanent; next type = user's call"
metadata: 
  node_type: memory
  type: project
  originSessionId: 176544e8-656c-4540-a15c-f710beced15e
  modified: 2026-08-05T20:44:16.552Z
---

Document-level ACRIS decoder (started 2026-08-05; prompt + files in
`Downloads\Source Folder (Real Estate Data)\ACRIS\`). User directs type order;
loop = anatomy → targets → validator FIRST → parser → 3-outcome proof run →
graduate on an unseen doc. End state: parcel × 126-doc-types timeline database,
true zoning-lot map + air-rights price tape ($/SF per trade), then daily delta
monitoring. A new dedicated Supabase is offered by the user for the fact store.

**Pull (perfected):** Socrata bnx9-e6tj master + 8h5j-fqxa legals →
`GetImage?doc_id=&page=N` (TIFF 300dpi) needs browser UA+Referer; past last page
endpoint serves constant placeholder forever — stop at md5
4081a3f2004d7244a966995c02c730d0; cover "PAGE 1 OF N" cross-check. Images are
SCRAP: fetch → decode → validate → delete (~1000:1 image:fact ratio); ACRIS
re-fetchable = archive; provenance = doc_id+page, never stored images.

**DEVR proof run n=11 (2004–2026, boros 1/3/4, 17–111pp): 11 validated, 0
unparseable.** Six species under one code: 2-party ZLDA, multi-party ZLDA,
ZLDA+easements, airspace vertical split (self-to-self, future 900x lot),
deed-style conveyance of excess rights, amendment-to-DRA (Greenpoint: City
conveyed 501,227 SF for $0 + 431 affordable units). Deals record as batch
constellations (same 13-digit doc-id prefix): DEVR+DECL+ZONE+CERT+SAGE/SMIS+PAT;
"[Attached]" exhibits = sibling documents. **Decode by ENVELOPE+ENCUMBER
function family, not by code** — a Declaration was recorded as SAGE, the $24M
easement-as-ZLDA as EASE; classify from inside.

**Validators (built, `ACRIS/decoder/devr_validate.py`):** conservation
(Σareas, area×FAR, retained+excess=generated, Σafter=Σgenerated, pro-rata),
taxes (RPTT 1.425%/2.625%, RETT ⌈c/500⌉×$2 — one-directional), metes-and-bounds
geometry. Caught real recorded-original defects: wrong multiplier, 18'11" lot
gap, schedule-letter swaps, wrong-LLC signature block, missing acknowledgment.
**Consideration is almost never in the instrument** — triangulate index amt ↔
cover taxes; index $0 can hide $5M (Extell 2010: prepaid tax refs both
back-solve to exactly $5,000,000, ~$93/SF). Watch for: appended unexecuted form
copies (2/3 of a doc), ACRIS image sets missing pages vs stated count,
rights owner ≠ fee owner (Memorandum of Retainage), use-specific rights
(community facility), rezone-contingent quantities, index under-reporting
zoning-lot rosters (4 actual vs 2 indexed).

**Built:** `ACRIS/decoder/` schema.sql (document/effect/lifecycle_link/consent +
parcel_type_timeline view), load_facts.py, acris_facts.db (11 docs, 63 parcels,
53 links, 13 absent-consent findings); DEVR-anatomy-draft.md (full anatomy);
fetch_doc.py in session scratchpad (re-create if needed). Price tape so far:
$12.27 ('04 Wburg) $154.54 ('05 UES) $93.32 ('10 Chelsea) $216.77 ('14 FiDi)
$91.71 ('14 Wburg) $63.14 ('21 Harlem CF) $30.65 ('25 Jamaica) $125 ('26 Wburg).
Decode engine = vision pass w/ fixed JSON contract (page provenance mandatory,
never repair numbers) → deterministic validation in code. NEXT: graduation test
on a fresh unseen DEVR; then widen to family. Related: [[project_bkrea_lot_lineage]],
[[project_bkrea_change_tracking]], [[project_bkrea_debt_throughline]].

**Supabase LIVE (2026-08-05):** dedicated NEW project (host trljek…, separate
from app project); creds in `C:\dev\acris-decoder.env` (ACRIS_SUPABASE_URL /
ACRIS_SUPABASE_SERVICE_KEY, sb_secret format). Schema = `decoder/supabase_schema.sql`,
all objects `acris_`-prefixed: facts (acris_document) → timeline (acris_posting,
double-entry: signed quantity_sf, counter_bbls, Σ=0 per doc enforced by
acris_v_envelope_balance_check) → app-facing views (acris_v_envelope_adjustment
= net SF per BBL the app applies to its buildable calc; acris_v_parcel_timeline,
acris_v_price_tape, acris_v_active_restrictions, acris_v_zoning_lot_membership).
Migrated: 11 docs / 83 postings / 53 links / 15 consents; 10/10 transfers
balance. Loader = `decoder/migrate_to_supabase.py` (dedupe within-payload before
POST or PostgREST 500s; upsert via Prefer: resolution=merge-duplicates).
Collective grants (rights to multi-lot premises with no per-lot split) post to a
lead lot with counter_bbls carrying the roster — never invent a split. App must
read VIEWS only, never tables.

**BBL SPINE + BASELINES (2026-08-05, `decoder/build_spine.py`, `spine_archive.py`,
`baselines.json`):** rule = **post to what the DOCUMENT names, resolve at READ
time**. Current PLUTO (Socrata 64uk-42ks) gives lot area, zoning, residFAR/
commFAR/facilFAR, `appbbl` (predecessor lot) and `condono` (condo billing lot).
**Condominium unit lots are NOT in PLUTO** — PLUTO carries ONE billing lot per
condo (e.g. MN 1446 lot 7502 = condo 950, appbbl 1014460149) — so unit lots
resolve by chaining the document's own "f/k/a Lot 149" recital to PLUTO's
appbbl. That closed the condo fall: 82/82 unit lots → 2 canonical parcels.
Match the f/k/a phrase case-insensitively (`f/k/a|formerly` + optional "lot").

**PLUTO archive = C:\dev\bkrea-v2\.pluto-archive, 52 zips p02a…p26v1 (2002→).**
⚠ Traps learned the hard way: (1) **presence is NOT monotonic — lots are BORN as
well as retired**, so a binary search assuming "present in the oldest vintage"
reports every later-created lot as predating PLUTO (it silently mislabelled all
3 test lots); (2) newer vintages are ONE citywide CSV (~860k rows) while older
are per-borough .txt — filtering by borough re-reads the citywide file once per
borough and turns a 20s scan into 10min; (3) the right primitive is
`parcel_at(bbl, filing_date)` — start at the vintage nearest the DOCUMENT'S date
and expand outward, so validating a 2004 instrument uses the 2004 lot area/FAR,
not today's.
**TWO FINDINGS THAT PROVE BASELINES MUST BE TEMPORAL (2026-08-05):**
(1) *Derived lineage* — Williamsburg B2722: the 2004 ZLDA states lot 10 = 7,500
SF and lot 34 = 5,000 SF; today lot 10 is 12,500 SF and lot 34 is gone. PLUTO
recorded NO appbbl link, so the merger is recoverable ONLY by reconciling the
document's own areas against the current map. New spine source
`derived_area_reconciliation` (marked inferred, never authoritative) — documents
+ arithmetic are a lineage source where DOF's link is missing.
(2) *Rezoning invalidates today's yardstick* — Chelsea B800 lot 49: the 2010
Extell chart uses FAR 10 and a 15,639 SF lot; today PLUTO says M1-8A/R11, FAR 12,
8,527 SF (rezoned AND subdivided since). Validating a 2010 transfer against
today's PLUTO would fail for the right reason and the wrong cause. **Baseline is
a function of time: envelope(t) = baseline(t) + Σ postings ≤ t**, and the
baseline must come from the vintage at the filing date. Overall on the pilot:
13/15 document-stated lot areas match current PLUTO within 2% — the 2 that don't
are exactly these two, i.e. every divergence was explained, none were errors.

**⚠ PLUTO IS NOT THE PARCEL AUTHORITY — it is a DERIVED file and it LAGS.**
Proved in-pilot: Jamaica lot 78 was subdivided in Jan 2017 (ownership statement
CRFN 2017000021137); the May 2017 instrument uses the post-subdivision 5,271 SF
while PLUTO p17v1 still carried the pre-subdivision 29,568 SF. **The document
was ahead of the tax map.** Resolve stack, in authority order:
 1. **the recorded DOCUMENTS** — metes and bounds define the land in ANY era;
    "f/k/a" recitals are lineage records. Authoritative, and the decoder already
    reads them.
 2. **DOF Digital Tax Map** — the legal tax map / lot numbering, geometry-first,
    a different parcelling model from PLUTO. NOT yet wired in; it is the
    reconciliation source when DTM and PLUTO disagree.
 3. **ACRIS legals = a PARCEL CENSUS back to the 1960s** (`acris_lot_census.py`).
    Every instrument records a block+lot, so the filings naming a lot bracket
    its life. Pilot result: 69 parcels censused, **41 reach before 2002**,
    earliest evidence **1966-01-03**. Lot 149 (Knickerbocker predecessor) filed
    1968→2001 — it died just before PLUTO began, which is exactly why the spine
    needed the document's f/k/a recital. Caveat: "no recent filings" ≠ retired
    (lot 1014290025 last filed 2009 but still exists) — label them CANDIDATE
    retirements and corroborate.
 4. **PLUTO** — richest attributes (area, zoning, FAR), but derived, 2002+, lagging.
 5. Sanborn / Bromley atlases — pre-digital geometry, last resort.
**Answer to "can we reconcile back to the first ACRIS filing?"** EXISTENCE: yes,
to ~1966 via legals. GEOMETRY/AREA pre-2002: only where a document states metes
and bounds — which is precisely what we decode, so it is available for the
parcels we care about, and absent citywide. Always state where evidence starts.
FUTURE CHALLENGE (user-flagged): mid-1900s ACRIS scans will be hard to read.

**TIE LINES PLACE PARCELS → ZR 12-10 CONTIGUITY IS CHECKABLE.** "BEGINNING …
distant 72 feet westerly from the corner formed by …" locates a parcel in a
block frame; place every member and adjacency falls out. This OVERTURNED a
recorded failure: the 2005 UES decode flagged an 18'11" contiguity gap, but
placement shows all four parcels touch lot 128 (25↔128 28.00 ft horizontal,
27↔128 18.92 ft vertical, 28↔128 19.92 ft vertical) — the zoning lot IS
contiguous **through lot 128's depth, not along the avenue frontage**, and the
two 18'11" runs are simply non-member lots. ⚠ LESSON: a zoning lot need not be
contiguous along its street frontage; never infer a defect from frontage gaps.
A prior FAIL can itself be wrong — re-check failures, not just passes.

**PARCEL DOSSIER (`decoder/parcel_dossier.py`)** — the systemization: coverage
FIRST (e.g. MN1446 L151 = 2 of 24 recorded documents = 8%, labelled "a SAMPLE,
not a history"), then identity/lineage, timeline, envelope position, live
restrictions, parties, absent consents. **It prefers the SURVEY over the tax
map**: using the instrument's 1,021.8 SF instead of PLUTO's 1,040 makes the
computed residual 10,218 − 6,554 = **3,664 SF, exactly the retained figure the
instrument states** — PLUTO's area would have been 182 SF wrong. Never report a
dossier without its coverage denominator.

**METES AND BOUNDS ARE THE LEGAL SOURCE (`decoder/metes.py`, 2026-08-05).** A
deed conveys the land DESCRIBED, not "tax lot 34" — tax lots are DOF's
administrative overlay, DTM is the official geometry for that overlay, PLUTO is
quarterly packaging. The survey courses are available for ANY era, so they close
the pre-2002 geometry gap no parcel file can reach. Engine walks the traverse,
shoelace area + CLOSURE ERROR (area is only trustworthy when the courses return
to the point of beginning). Validated: MN1446 L151 party-wall jog → 1,022.0 vs
stated 1,021.8 (0.02%); MN1446 L1 → 2,037.5 exact; QN9793 L78 → 5,271.1 exact;
all closing to 0.0 ft. The KNOWN-DEFECTIVE Ten Eyck L19 description returns
**unparseable** instead of a fabricated area — refusal is the correct output.
⚠ Three parser traps, all found by measurement: (1) descriptions say "BEGINNING"
at BOTH ends — split once on the first, or you take the empty tail; (2) the
clause before the first "thence" is a TIE LINE locating the point of beginning,
not a boundary course — counting it throws closure by exactly the tie distance
(54.417 ft in the test case); (3) **NYC street names contain compass words** —
"thence westerly along East 71st Street" matches "east" before "westerly" and
flips the course 180°, so match the -ly adverbs FIRST and guard bare cardinals
against a following street name.
⚠ **CONTRACT GAP:** the pilot decodes SUMMARIZED legal descriptions ("25 x 100")
instead of transcribing the courses verbatim, so only 4 of 14 documents carry any
dimension text and none is a usable course list. The extraction contract must
require **verbatim course transcription** for every legal description — that is
the one field that makes the survey usable as the primary geometry source.

**DIVERGENCE IS NOT ONE THING — classify it** (`map_divergences.json`, audit
check 6b). Four kinds: `agree` · `partial` (document describes p/o a lot — test
doc ≤ map, never equality) · `map_lag` (the document's figure appears in a LATER
vintage) · `survey_vs_taxmap` (persistent across vintages; report, never repair).
Anything else is `unexplained` → FAIL. Pilot: **41/41 explained** = 36 agree +
1 partial + 2 lag + 2 survey.
 · LAG PROVEN: Jamaica lot 78 doc 5,271 → p18v1 = 5,271 (PLUTO caught up ~1yr
   after the Jan-2017 subdivision); Greenpoint lot 6 doc 9,011 → p21v4 = 9,000.
 · GENUINE: Extell lot 49 doc 15,639 vs PLUTO 16,745 held constant across
   p11v1/p11v2/p12v1/p13v1 (6.6%); Greenpoint lot 3 doc 2,703 vs 2,814 across
   p21v3/v4/p22v1 (4%). Never converge ⇒ survey-vs-tax-map, not decode error.
⚠ REGRESSION I CAUSED AND CAUGHT: the ACRIS census writes a SECOND spine row per
BBL (different valid_from), and a last-wins `{r["bbl"]: r for r in ...}` dropped
the row holding the successor link — silently breaking lineage for 2 lots. Merge
spine rows per BBL (union successors/predecessors), never last-wins.

## ▶ PICK UP HERE (current state + next actions, 2026-08-05)

**Where everything lives** (nothing important is only in a chat):
`Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder\` (MOVED here 2026-08-05; was `...\ACRIS\decoder\`) — ARCHITECTURE.md
(ledger design), EXTRACTION_CONTRACT.md (what a decode must return),
SOURCE_MAP_DOB.md (DOB+BSA+DCP+**LPC+HPD+the Zoning Resolution** → accounts),
plus the working code: audit.py · reduce.py · migrate_to_supabase.py ·
resolve_citations.py · build_spine.py · spine_archive.py ·
build_historical_baselines.py · acris_lot_census.py · metes.py ·
parcel_dossier.py · devr_validate.py · **zr_feed.py** (live Zoning Resolution)
· **split_zones.py** (tax-lot ∩ zoning-district geometry) ·
**close_split_far.py** · dump_zoning_reference.mjs, and the data files
baselines.json · baselines_historical.json · map_divergences.json ·
split_zone_shares.json · zoning_reference.json · zr_cache/.
Decoded facts JSON lives in the session scratchpad `devr/decoded/` — **fragile,
re-derivable from Supabase `decoder_document.raw_facts`**. Supabase = project
"Data Decoder", creds `C:\devcris-decoder.env`.
Run order after any decode: `migrate_to_supabase.py <decoded_dir>` →
`reduce.py <decoded_dir>` → `resolve_citations.py` → `audit.py`.

**Audit: 15 checks, 0 FAIL, 10 PASS, 5 INFO.** The split-district FAIL is CLOSED
(see the geometry + ZR sections below). Remaining INFO: 44 of 83 citations
unresolved (30 reference-less "of even date", 4 reel/page, 5 CRFN); 1 document
conveys rights with no SF stated anywhere (Knickerbocker 2026012000388003 — try
DCP 1961 zoning layer + the ZD1 for DOB job M01361353); roster-vs-index
divergences all explained.

**Next actions, in order:** (1) re-decode legal descriptions to
`courses_verbatim` for the 13 documents that still carry summaries, so metes.py
+ contiguity run at scale; (2) then either widen ACRIS to
ZONE/AIRRIGHT/EASE/DECL/CERT/SAGE, or build the sweep runner. **Do NOT scale the
sweep until (1) is done.** Later, on the user's roadmap: comparables decoded
from listing services (a separate source family), and monitoring/update as a
first-class concern alongside population.

**STATE 2026-08-05 end of session:** 14 documents / 215 postings / 83 citations
(31 resolved) / 323 baselines / 213 spine rows. Audit = **12 checks, 0 FAIL,
7 PASS, 5 INFO**. Both original falls closed (condo unit lots → canonical
parcels; 151/151 BBLs resolve today or at filing date).
**WEAK CHECKS FIXED (same session) — the fix was ARCHITECTURAL, not a patch:**
both failed because they parsed PROSE. Cure = store the fact structurally and
check the field. Added to every decode: `consideration.zero_verified` (how the
prepaid-tax trap was ruled out, with the cover re-read) and `lot_areas_by_bbl`
(bbl → SF + provenance, so no fuzzy "applies_to_lot" matching). Also: the audit
must SELECT `raw_facts` or every structured check silently sees None and reports
a false FAIL. Result: $0 check 0/4 fake → **4/4 real PASS**; lot-area check
0/0 fake → **42 real comparisons**. ⚠ GENERAL RULE: *a check that evaluates
nothing reports as clean* — always print the denominator, and treat 0/0 as a
defect in the check, never as a pass. Fixing a fake PASS into a real FAIL is
progress.

**SELF-AUDIT HARNESS (`decoder/audit.py`)** — every learned trap encoded as a
check that re-runs over the whole store forever, with denominators. First three
rounds: 3 FAIL → 2 FAIL → 1 FAIL (remaining = the known condo/lineage fall).
Caught, in its first run: (a) **silent membership loss** — roster entries arrive
as `{bbl}` OR `{borough,block,lot}` and the loader filtered to the first shape,
dropping every zoning-lot membership posting for documents written the other way,
no error raised; (b) dead hand-typed ENVELOPE_POSTINGS still in the loader,
duplicating reduce.py and shadowing the `bbl()` helper; (c) **two bugs in my own
checks** — a BBL slice at [5:] instead of [6:] (lot starts at index 6) that
flagged 12 documents instead of the true 2, and a provenance-length floor that
mis-scored. LESSON: a check that fires on everything hides the real signal; audit
the auditors. Also: page number alone is NOT provenance — carry page + what is on it.

⚠ **SWEEP-DESIGN FINDING (2026-08-05, from the Knickerbocker DECL):** the MTA
owns lot 51 (2010 condemnation) and conditioned its consent on *nothing being
recorded against lot 51* — so the Declaration binds lot 51 into the zoning lot
while being **deliberately omitted from that lot's index legals**. A parcel-keyed
ACRIS pull on lot 51 can never surface it. Phase-2 parcel lifespans are therefore
incomplete by construction if built from index legals alone; completeness
requires the document-extracted ROSTER as a second index (decode → roster →
back-fill parcel↔document edges).

**MULTI-SOURCE (2026-08-05).** Supabase project renamed **Data Decoder**; tables
renamed `acris_*` → **`decoder_*`** + explicit `source` column ('acris'|'dob_now')
via `migration_002_data_decoder.sql`. All 4 user workbooks (ACRIS, DOB BIS, DOB
NOW, BSA, DCP) share the SAME 15-function legend ⇒ **function is the join
language**; the account chart absorbs every source with 3 additions: `asbuilt`
(CO/TCO — what legally EXISTS, ACRIS has no equivalent), `envelope_claimed`
(ZD1/PW1B/approved plans — a CLAIM, never `envelope_transferable`), `entitlement`
(BSA/DCP grants). RULE: **a recorded instrument changes what MAY be built; a
permit only describes what IS being built** — `decoder_v_envelope_adjustment`
filters `source='acris'`. ⚠ **Source-specific checks MUST be scoped to their
source**: the first DOB row instantly failed the ACRIS prepaid-tax check because
a permit has no consideration. Map = `decoder/SOURCE_MAP_DOB.md`.

⚠ **PLUTO's single zoning field is WRONG for ~38% of parcels.** DCP
**`fdkv-4t4z` NYC Zoning Tax Lot Database** is the authoritative per-BBL zoning
assignment. Measured on 323 pilot baselines: **123 carry a commercial overlay or
special district `zonedist1` drops; 22 are SPLIT between districts where a single
FAR is simply wrong** (audit now FAILS on those rather than using one FAR). The
Knickerbocker zoning lot is entirely in Special District **TA** (Transit Land
Use, 2nd Ave Subway) with a C1-5 overlay — invisible in PLUTO.
Other DCP layers that answer open questions: **1961 Zoning Districts** (non-
conforming rights descend from it — likely explains buildings exceeding today's
FAR, e.g. Knickerbocker's 149,436.84 SF on ~100,300 as-of-right); **Special TDR
Regulations** (the regime governing every DEVR); MIH; E-Designations; POPS;
ZAP-BBL `2iga-a6mk` (parcel-addressable ENTITLE).
**BSA reaches to the 1930s–40s and those grants are STILL BINDING** (calendar
no. = sequence-year-type). The RESOLUTION binds, not the fact of a grant — same
premise as this project. SOC = amend/extend/waive a prior grant (lifecycle).
Extension of Term: when a fixed term lapses **the use becomes illegal** — an
encumbrance with an expiry. BZY/ZR 11-331 vested rights explain FAR exceeding
the current district. GCL 35/36 (mapped street bed / no frontage) = viability.

**TWO-PHASE ROADMAP (user's strategy, 2026-08-05):**
*Phase 1 — learn by FUNCTION* (now): decode type-by-type within a function
family so correlated instruments teach each other (ENVELOPE+ENCUMBER first,
then TITLE+CAPITAL). Output = per-type playbooks: variants, where the numbers
live, validators, reducer semantics.
*Phase 2 — sweep by PARCEL* (once the families are understood): the unit of work
becomes a BBL, not a document. Pull every ACRIS instrument touching that parcel,
decode **oldest → newest**, each document briefed with the parcel's
already-decoded timeline. Chronological order is not cosmetic — state folds
forward, lifecycle links (satisfactions, terminations, amendments) resolve
naturally against instruments already in hand, and context only helps if it is
history rather than future. One context per parcel instead of per document, so
it is also the cheapest mode. Then "run an ACRIS lifespan" is one command.
PREREQUISITE: the BBL spine defines when a parcel is *born* (subdivision,
merger, condo conversion), so lifespan mode cannot start before gap 4 is built.
BOUNDARY to state honestly: ACRIS's own digital horizon (~1966, older via
reel/page) is the earliest "birth" recoverable — a lifespan starts at the
earlier of lot creation and ACRIS coverage, and must say which.

**BRANCHING + CITATION RESOLUTION (2026-08-05, `decoder/resolve_citations.py`):**
governing principle from the user — *if a document you need is logically
referenced, branch and decode it; envelope and encumbrance instruments support
each other, and as long as you hold the reference number you can always return
to the occurrence.* Goal: once the whole ENVELOPE+ENCUMBER family is decoded,
timeline context fills the NULLs (join keys — parcel assignment, and DOB job
number on the permit side — are what make that possible).
Resolution routes: crfn / doc_id (regex out of the citation) → Socrata master;
**batch_sibling** (13-digit prefix) for reference-less "of even date /
simultaneously herewith" citations, accepted only when exactly one sibling
matches the cited KIND (ambiguity stays a finding). ⚠ MODELING FIX: a citation
is WHAT is cited + HOW it is identified — `acris_lifecycle_link.target_ref` must
store `"{what} :: {identifier}"`; storing the identifier alone made
reference-less citations unresolvable (found and fixed same day).
Confirms "titles lie": Knickerbocker's Zoning Lot Certification was recorded as
**SMIS**, its Declaration as DECL, and a 2016 Declaration elsewhere as SAGE —
only the constellation finds them. Constellations are big: Greenpoint batch = 34
siblings (DEEDs, MTGEs, EASEs, CERTs), Jamaica = 19 incl. 7 MTGEs — i.e. the
CAPITAL family arrives free alongside ENVELOPE when sweeping by batch.

**REDUCER AUTOMATED (2026-08-05, `decoder/reduce.py`):** declarative transfer
spec → deterministic postings; no hand-typing. TRANSFER-GROUP model: every lot
on BOTH sides gets a row tagged {transfer_group, side, group_quantity_sf,
allocation, basis}; per-lot quantity ONLY when the document states it, else NULL
+ group total (never invent a split, never lead-lot-only). Balance checked at
group level. validate_row() gate rejects bad bbl/date/quantity before insert.
Result: 25 hand-typed → 123 generated postings, 0 rejects, all fully-allocated
groups balanced, Greenpoint cross-group 211,898+289,329=501,227 exact.
⚠ **`acris_v_envelope_adjustment.net_adjustment_sf` is NULL (not 0) when a
transfer touches a lot with no per-lot SF stated — the app MUST treat null ≠
zero.**

⚠ **OPEN FALL — condo/lineage inconsistency (found 2026-08-05 by the backward
re-check):** Knickerbocker posted to 81 condo UNIT lots (index's view) while
Greenpoint posted to RETIRED base lots 2472/60, 65, 2494/1 (document's view).
Both cannot be right; 99 of 118 "affected parcels" are an artifact of the condo
expansion. Correct rule = post to what the DOCUMENT names, resolve to current
BBLs at READ time — which requires the BBL spine (gap 4). Do not scale the
sweep until this is settled, or every condo deal inflates parcel counts.

**GRADUATION PASSED (2026-08-05):** blind draw 2026012000388003 (Knickerbocker
Condominium → Torkian, B1446) decoded+validated with ZERO code changes — decoder
untangled the condo trap unaided (81 unit lots = grantor's own land f/k/a 149;
receiving base lots 1/2/3), caught index duplicating lot 1102, mapped 13
cross-instruments back to 1995 reels, taxes exact vs $549,305.48. Revealed 7th
variant: **quantity-unstated ZLDA** ("all excess" conveyed, SF never stated —
only retained 149,436.84 SF given); posted with quantity_sf NULL + note, per-SF
refused, resolve via FAR baseline later. Store: 12 docs / 92 postings / 60
links / 17 consents. MEMORY.md line may still say 11 — 12 is current. ARCHITECTURE.md in decoder/ = ledger design
(accounts: title, envelope_transferable/membership/form, use_restriction,
occupancy, capital, distress, standing, party_observation). User will upgrade
Supabase plan later; free-tier egress overage was the APP org's, decoder org is
separate and egress-light by design.

## Zoning + geometry: the two sources that outrank what I had been using

**The Zoning Resolution is a LIVE FEED, not a workbook** (`zr_feed.py`).
`zr.planning.nyc.gov` is fetchable, text-based, section-addressable, and the
section number IS the address: first digit = Article, second = Chapter, so
`23-22` -> `/article-ii/chapter-3/23-22`. Parse the HTML tables, keep the
`<sup>` markers, cache the PARSED FACTS not the page, and keep `LAST AMENDED`
so a re-run detects an amendment. User's instruction 2026-08-05: live-feed the
ZR for anything relying on exact zoning. No Excel needed for it.

**FAR is not a number per district — it is a number per (district, condition),
and only the Resolution publishes both.** ZR 23-22 lists R6 at 2.20 in its own
row AND as "R6¹" in the 3.00 row, footnote 1 = "For zoning lots, or portions
thereof, located within 100 feet of a wide street". Checked live against the
app's hand-transcribed table: **26 of 27 districts agreed, and the one that did
not was exactly the one whose rule lived in a footnote** — `lib/zoningReference.ts`
had "corrected" R6 to a flat 2.20 on 2026-07-27, deleting a real wide-street
3.00. Transcription cannot carry a footnote. (Also note "or portions thereof":
wide-street FAR is a SECOND axis of splitting, within 100 ft of the street —
not yet computed; both figures carried, frontage stated as un-established.)

**Split-district lots: ZR 77-22 is the rule.** "Each such floor area ratio shall
be multiplied by the percentage of the zoning lot to which such floor area ratio
applies. The sum of the products thus obtained shall be the adjusted maximum
floor area ratio." Area-weighted — not max, not first. PLUTO publishes the
PRIMARY district's FAR and it is wrong on split lots (MN 1014290103: PLUTO 10.0
vs adjusted 8.41). DCP `fdkv-4t4z` names both districts but publishes no
percentage, so the percentage must be MEASURED: tax-lot polygon ∩ DCP `nyzd`,
both requested at `outSR=2263` (state-plane US survey feet) so shapely areas
come back in ft² with no reprojection of our own to get wrong. 22 pilot lots:
21 resolved, 1 single-district-plus-unzoned.

**UNZONED land is not FAR-zero, it is not in the zoning lot at all.** Mapped
parkland (nyzd `PARK`) carries no district. Blending it in at 0 understates FAR
while overstating lot area and the two errors do NOT cancel — remove it from the
weighting and shrink the lot area instead.

**A blank in a FAR table is two different facts.** An R district really does
permit no commercial floor area; R10A's blank community-facility cell is a hole
in a transcribed chart. Same null, opposite meanings. Name the legal zeros
explicitly and leave everything else unresolved. And a commercial OVERLAY (nyco,
separate layer) puts commercial floor area back on an R portion — so "R = no
commercial" only holds where DCP shows no overlay.

## ⚠ TRAP: MapPLUTO polygons can be FRAGMENTS (found 2026-08-05)

Using MapPLUTO's outline as a proxy for the tax-lot polygon returned a **1,625 sf
two-ring fragment for BBL 3025200100 whose own LotArea attribute said 65,000**;
DOF's Digital Tax Map returns 74,925. Four of 22 pilot lots were affected
(-97.5%, -58.7%, -42.6%, -26.5%).

**The shares computed on those fragments looked flawless** — 100% coverage, two
tidy districts, no error raised — because a RATIO cannot tell you it was taken
over the wrong footprint. Only cross-checking polygon area against the stated
lot area caught it. Same shape as the scale-failure lesson: the output validated
itself.

Cure: **DOF Digital Tax Map is the geometry source**, MapPLUTO only as fallback,
and every lot records which one it came from.
`https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/Digital_Tax_Map_VIEW/FeatureServer/5`
(BBL is a STRING there; flags worth carrying: CONDO_FLAG, AIR_LOT_FLAG,
EASEMENT_FLAG, SUB_LOT_FLAG, BILL_BBL_FLAG, LOT_NOTE). Gate is one-sided: a
polygon much SMALLER than the stated area is a fragment; LARGER is the normal
few-percent generosity and still covers the whole lot. After the switch, median
divergence 5.5% -> 3.6%.

## LPC + HPD (workbooks supplied 2026-08-05) — what they add that ACRIS cannot

- **LPC decides the envelope that zoning cannot see.** Whether a rooftop
  enlargement is visible, and therefore permissible, is decided at LPC, not in
  the FAR calculation. A site can hold unused rights the Commission will never
  let anyone build. Landmark rights are TRANSFERABLE (ZR 74-79 / special-district
  TDR), so designation detaches an envelope rather than destroying it — that
  makes LPC a DEVR subtype, inside the envelope ledger, not beside it.
  **Calendared ≠ designated**: constrained in practice with no recorded
  instrument behind it (`ncre-qhxs`). Per-BBL join = `gpmc-yuvp`.
- **HPD Shareholder role closes a real ACRIS blind spot.** A co-op transfers
  SHARES, records no deed, so ACRIS is silent on every co-op ownership change —
  an ACRIS-only lifespan shows the building as never having traded.
  `feu5-w2e2`. Registration is ANNUAL (calendar-driven, not event-driven), so
  it is a MONITORING source, not an event source.
- **CONH `bzxi-2tsw` blocks DOB permits** until HPD certifies no harassment — a
  hard per-parcel development gate appearing in no recorded instrument.
- No new accounts needed: `use_restriction`, `standing`, `entitlement`,
  `distress`, `occupancy`, `party_observation`, `envelope_claimed` absorb both.

## Reported area vs digitized geometry — two different quantities (2026-08-05)

Three-way test over 38 parcels whose lot area is stated in a recorded document:
**document vs PLUTO = median 0.00%. Document vs DOF tax-map polygon = median
6.39%.** PLUTO's `lotarea` is DOF's REPORTED figure from the tax roll — the same
administrative number the surveys recite — while the DTM polygon is a
CARTOGRAPHIC DIGITIZATION of the shape.

So: **use the reported area for QUANTITIES** (lot area × FAR = envelope) and
**the polygon for SHAPES** (which districts a lot spans, adjacency, contiguity),
where a few percent of digitizing error cancels because shares are ratios. The
polygon-vs-reported comparison is a FRAGMENT DETECTOR, not an accuracy score —
do not "improve" it toward 0%, that would be chasing the wrong number. (Large
outliers in that test — +302%, +200%, -45% — are LINEAGE cases: the document
describes the lot as it was. Compare against the contemporaneous vintage.)

## FAR sourcing: every use now comes from the section that governs it

`close_split_far.py` resolves each use from the live ZR, transcribed reference
only as fallback, and every value records which:
  residential R6-R12          **23-22** (keeps BOTH street-width figures)
  community facility in R     **24-11**  (fills R10A = 10.0, blank in the reference)
  commercial in C1-C8         **33-122**
  community facility in C     **33-123**
  commercial under a C1/C2 OVERLAY on an R district  **33-121 Column A**, keyed by
      the UNDERLYING residence district, × the MEASURED overlay coverage of that
      district's portion (nyco ∩ nyzd ∩ lot) — an overlay is drawn ~100-200 ft
      deep so it routinely covers only part of a lot
  manufacturing in M          **43-12**
  A-suffix M1 (City of Yes)   **43-132**, verbatim "the maximum floor area ratio
      for ALL PERMITTED USES" — one figure serves manufacturing, commercial AND
      community facility, which is why an MX pair like M1-8A/R11 resolves at all
Contextual variants fall back to the parent district (R10A -> R10) and SAY they did.
Result: 22/22 split lots, all three uses, **zero unresolved FAR cells**.

⚠ Regression I caught in myself the same session: when unifying the lookups I
collapsed R6's conditional FAR back to a single number — the exact error the ZR
feed exists to prevent. Residential must stay {narrow, wide}; the caller picks.

## Parcel lifecycle model — CAPTURED, NOT BUILT

`decoder/PARCEL_LIFECYCLE.md` records Login's model (2026-08-05): pre-development
-> construction -> temporary operation -> operation -> unit-level comparables ->
signals while operating -> back to pre-development, restarting **with or without
a sale**. Two points he made that the old stage model missed:
- an owner can restart the cycle with no conveyance at all, so a model waiting
  for a deed misses every owner-driven restart;
- the sale at the turn is TWO instruments under one name — land ($/BSF) if
  underbuilt/vacant, operating (cap rate) if the asset is the income, and which
  one it is depends on the ENVELOPE, i.e. on this decoder.
**The least-covered stage is activity DURING operation** (ULURP, BSA, LPC
designation/calendaring, ground lease, CONH, E-designation, liens, rezoning
landing, ACP5) — signals that restrict, motivate, or merely mark. Rule for
filling a gap: name the stage, name the transition, name the document that
proves it, THEN build.
Explicitly deferred by Login: soft/hard COST decoders, GROUND LEASE, listing-
service comparables, and a **party-context decoder** ("who each player in the
game is") — that last one is a decoder over party observations we are ALREADY
capturing (ACRIS grantor/grantee + borrower SPE, DOB PW1 §26, LPC applicant AND
owner, HPD agent/officer/shareholder), not a new pull.

## ⚠ THREE BUGS IN metes.py, all found the moment descriptions went VERBATIM

Summarised descriptions ("25 x 100") had hidden every one of these. Fixed
2026-08-05; the 2005 UES traverse now reproduces the recorded area EXACTLY
(2,146.7 vs 2,147 stated, closure 0.00 ft) — external proof, not self-report.

1. **Bearing took the first direction in MY LIST, not the first in the TEXT.**
   A course routinely names a second direction as a REFERENCE — "westerly
   parallel with Leonard Street 100 feet to the **Southerly** side of Ten Eyck
   Street" travels WEST and merely mentions a street's south side. Scanning
   (northerly, southerly, easterly, westerly) in list order returned SOUTH: a
   90-degree error, silent, on any description citing a street side — which is
   most of them. Fix: leftmost match BY POSITION.
   **This bug was created by the fix above it** (the guard against street names
   containing compass words). A guard can create the thing it guards against.
2. **"76 feet, 8 inches" parsed as 76.0** — the comma broke the inches capture.
3. **Generic fallback grabbed the STREET NUMBER.** "westerly parallel with 75th
   Street, 28th feet" → **75 feet**, because the "28th feet" typo defeated the
   pattern and the fallback took the first number in the clause.
   **Rule adopted: prefer an UNPARSEABLE course to a silently wrong one.** A
   missing course is visible the moment you look at the traverse; a wrong
   distance is invisible and poisons the area. The fallback is deleted.

**Reverse lesson:** before the fix the 2005 description looked DEFECTIVE (area
5,700, closure 47 ft). It was fine — the parser was broken. False-positive
defects are as damaging as missed ones, and only an external check (does the
traverse reproduce the recorded area?) can tell them apart.

## Verbatim re-decode — progress

Coverage check corrected: `courses_verbatim` lives INSIDE `legal_descriptions[]`,
not at top level. My first check looked at the top level, found nothing, and
reported "0/15" — a check aimed at the wrong field returns an empty result that
reads exactly like a real finding. Now enforced by an audit check that counts
BOTH failure modes separately: summarised vs **no description block at all**.
True state: 4 descriptions verbatim, 8 summarised (3 docs), **9 documents carry
NO legal_descriptions block** (decoded before the contract required one).

`fetch_pages.py` pulls ONLY the pages a decode already recorded — a re-read
never needs the whole document. Images still scrap: fetch → read → delete.

**DONE: 2026061500475003** (Williamsburg ZLDA, lots 19+20). BOTH exhibits are
DEFECTIVE AS RECORDED — Ex A is missing its first boundary course, contradicts
itself ("westerly parallel with Leonard Street"), and duplicates an easterly
course; Ex B is missing its northerly return (closure error 100.00 ft). Neither
traverse closes. **But the TIE LINES prove contiguity**: lot 20 sits 100-125 ft
west of Leonard, lot 19 sits 125-150 ft west, sharing the boundary at 125 ft —
which is what a zoning lot merger requires. Contiguity provable even where the
traverse is not. Nothing repaired.

## ⚠ KEY-FORMAT TRAPS — now ENFORCED in `decoder/keys.py`, not remembered

Every source keys a parcel differently, and the failures do NOT look like
failures:

    ACRIS legals      borough / block / lot as SEPARATE integer columns
    Socrata PLUTO     block zero-padded to 5   '01446'
    DOB BIS / NOW     block NOT padded         '1446'   <- padded => ZERO rows,
                                                           reads as "no filing"
    MapPLUTO ArcGIS   BBL NUMERIC              BBL IN (1014460001)
    DOF DTM ArcGIS    BBL STRING               BBL IN ('1014460001')
    DCP fdkv-4t4z     bbl string

**BLOCK+LOT IS NOT A PARCEL KEY.** Querying `BLOCK=1540 AND LOT=3` on the tax map
with no borough returned BROOKLYN's block 1540 lot 3 — a real parcel, wrong
borough, no error raised. `keys.boro()` now RAISES on a missing borough rather
than defaulting. `keys.py` self-tests 12/12.

## ⚠ metes.py — FOUR bugs, every one surfaced by going VERBATIM

Summarised descriptions ("25 x 100") hid all four. Fixed 2026-08-05; both
external checks now pass: 2005 UES = **2,146.7 vs 2,147 recorded, closure 0.00
ft**; 2012 airspace = **2,504.2 vs 2,504.17 recorded, closure 0.00 ft**.
`parse_distance` unit tests 11/11.

1. **Bearing took the first direction in MY LIST, not in the TEXT.** A course
   names a second direction as a REFERENCE — "westerly parallel with Leonard
   Street ... to the **Southerly** side of Ten Eyck Street" travels WEST.
   Scanning (northerly, southerly, easterly, westerly) in list order returned
   SOUTH: a silent 90-degree error on any description citing a street side,
   which is most of them. Fix: leftmost match BY POSITION.
   **This bug was CREATED by the fix directly above it** (the guard against
   street names containing compass words). A guard can create what it guards against.
2. **"76 feet, 8 inches" -> 76.0** — the comma broke the inches capture.
3. **Generic fallback grabbed the STREET NUMBER**: "westerly parallel with 75th
   Street, 28th feet" -> **75 feet**. Fallback DELETED.
   **Rule adopted: prefer an UNPARSEABLE course to a silently wrong one.** A
   missing course is visible in the traverse; a wrong distance is not.
4. **Bare fractional inches dropped**: "25 feet 1/2 inch" -> 25.0, because the
   pattern demanded a whole number before the fraction. Turned a lot recorded at
   25'0-1/2" x 100' = 2,504.17 sf into a tidy, wrong 2,500.

**Reverse lesson:** before these fixes the 2005 description looked DEFECTIVE
(area 5,700, closure 47 ft). It was fine — the parser was broken. A
false-positive defect is as damaging as a missed one, and only an EXTERNAL check
(does the traverse reproduce the recorded area?) distinguishes them.

## ⚠ CORRECTED: absence from today's map ≠ never created

**What I claimed on 2026-08-05 and got WRONG:** doc 2012120600575002 Exhibit B
said "currently designated as part of Block 1540, Lot 3 (**to be Lot 9003**)";
neither lot appears on today's tax map, and I concluded the air lot "was never
minted". **False.** DOF's alteration book shows:
  * **2012-12-21** lot 9003 created — authority: *"Zelda Recorded on 12/10/2012
    Zelda CRFN # 2012000483179 Survey by: Earl B. Lovell- S.P. Belcher Inc
    Survey Date: 11/30/2012 PW 1 # 121354550"*. ("Zelda" is DOF's own spelling of
    ZLDA.) That CRFN **is** the decoded document — the prediction was fulfilled.
  * **2017-10-26** "Air rights lot 9003 was merged back into lot 3 as requested
    by the owner - 95 and Third LLC"
  * **2017-10-26** lot 3 itself Dropped in a Lot Merger, authority two deeds
    (CRFN 2014000430833, CRFN 2015000377043)

**The real lesson: a CURRENT-STATE query cannot distinguish "never existed" from
"existed and was retired".** Only the alteration book can. The original trap
still holds — a "to be Lot ___" recital is a CLAIM to be resolved against the map,
never posted as an identity — but resolve it against the HISTORY, not today.

## Verbatim re-decode — running progress

`fetch_pages.py` pulls ONLY the pages a decode already recorded (a re-read never
needs the whole document); images stay scrap: fetch -> read -> delete.
Audit check now counts BOTH failure modes: summarised vs **no description block
at all**. State after this pass: 6 verbatim / 12, **2 of 4 summarised docs done**,
9 documents still carry NO description block.

- **2026061500475003 DONE** (Williamsburg, lots 19+20). BOTH exhibits DEFECTIVE
  AS RECORDED — Ex A missing its first course, self-contradictory, duplicates an
  easterly course; Ex B missing its northerly return (closure 100.00 ft). Neither
  closes. **But the TIE LINES prove contiguity**: lot 20 sits 100-125 ft west of
  Leonard, lot 19 sits 125-150 ft — sharing the boundary at 125 ft, which is what
  a zoning lot merger requires. Contiguity provable where the traverse is not.
- **2012120600575002 DONE** (airspace vertical split, MN 1540 lot 3). Both
  parcels close at 2,504.2. Two facts the summary had destroyed: the plane is 120
  ft above the **Manhattan Topographic Bureau datum, which is 2.75 ft above USCGS
  mean sea level** (so 122.75 ft MSL — any cross-check against DOB height data is
  wrong by 2.75 ft without it); and the footprints are IDENTICAL, so their areas
  are **NOT additive** — the same 2,504.17 sf of ground is described twice, once
  below the plane and once above.

## Self-assessment 2026-08-05 (Login asked directly)

Reasoning is holding; **mechanical source-handling is where the errors cluster**.
This session's mistakes were ALL wrong-key / wrong-field / wrong-argument-order /
wrong-list-order — never a wrong conclusion, and the conclusions were externally
validated. But the count rose with the number of sources in play. Cure is the
project's own rule applied to myself: ENFORCE, don't remember (`keys.py`, audit
checks), and end every chain with an external check rather than a summary I wrote.

## Verbatim re-decode — ALL SUMMARIES CLEARED (13/13 verbatim, 0 summarised)

Remaining gap: **9 documents carry NO legal_descriptions block at all** —
2004110301042003, 2010102601040006, 2014070300770002, 2014091201052002,
2017053000419005, 2021020901358005, 2021070601644010, 2025102901095004,
2026012000388002. Their description pages are NOT yet known (the earlier decodes
recorded no page), so each needs its exhibit located before a targeted fetch.

**A THIRD description shape exists: INCORPORATION BY REFERENCE.** ZLDA Exhibit D
of 2026012000388004 reads in full: "ALL that volume of space ... from and above
the Lower Limiting Plane, which is located one hundred twelve (112) feet above
Datum Level within the boundaries of the Owner Premises described in Exhibit A of
this Agreement." It has NO COURSES because the instrument gave it none —
complete as recorded, NOT a summary. The audit check now accepts
`incorporates_by_reference` + `description_verbatim` as complete; counting it as a
gap would send someone back to re-read a page that is already whole.
⚠ Its "**Datum Level**" is a defined term used WITHOUT its definition on the
page. Contrast doc 2012120600575002, which spelled out the Topographic Bureau
datum and its 2.75 ft offset from mean sea level. Resolve the definition from the
body before comparing a 112 ft plane to any DOB height.

**2026012000388003 (Knickerbocker) DONE** — 3 descriptions, all close at 0.00 ft:
Condominium Land 10,029.8 sf (12 courses, irregular), Developer Land Lot 1
2,037.5 sf, Lots 2+3 3,750.0 sf (described as ONE parcel, no per-lot split).
CONTIGUITY from the tie lines again: lot 1 runs 27'2" north from the Second Ave /
E 71st corner and lots 2+3 BEGIN 27'2" north of that same corner — they abut
exactly. On a 12-course irregular shape, closure is a real check on the
TRANSCRIPTION: one misread digit and it would not close.

**2026012000388004 DONE** — lot 151 closes at **1,022.0 sf against the 1,021.8 sf
the instrument's own §1.17 arithmetic uses** (0.24 sf, 0.02%). Not repaired. Two
lot areas are in play: the one the courses describe and the one the computation
relies on. Either way **the survey beats the tax map** — PLUTO's 1,040 would miss
the stated 6,554 sf transfer by 182 sf, while 1,021.8 x 10 - 3,664 = 6,554 exactly.
Its Exhibit B is **word-for-word identical** to sibling doc ...003's — two
separately recorded instruments describing the same land the same way, which is a
free cross-document check.

## Knickerbocker unstated quantity — CANDIDATE, NOT an answer

Measured Condominium Land 10,029.8 sf x FAR 10 = 100,298 sf as-of-right against
**149,436.84 sf built — over-built by 49,138.84 sf**. By as-of-right arithmetic
there is NOTHING to convey, yet $549,305.48 was paid for "ALL Excess Development
Rights". Batch back-solve: sibling doc ...004 states 6,554 sf for $1,650,000 =
$251.7547/sf; $549,305.48 at that rate implies **2,181.9 sf** — but misses by
**$23.17**, and the two transfers had DIFFERENT transferors with no stated common
rate. Recorded as a candidate WITH its residual, not accepted. The over-build
almost certainly means non-conforming rights predating 1961 — a different SOURCE
(DCP 1961 Zoning Districts layer), not a different calculation.

## ⚠ SPECIAL DISTRICTS SUPERSEDE the citywide FAR tables (found 2026-08-05)

Login asked whether UAP/MIH and special districts were being handled. Honest
answer at the time: **MIH was being FETCHED and not USED, special districts
RECORDED and not APPLIED** — and that second gap was a live error.

**Confirmed error:** BBL 4097930089 is C4-4D 70.9% / C6-3 29.1% inside the
Special Downtown Jamaica District. **ZR 115-21** (last amended 10/29/2025):
"the maximum floor area ratio permitted for commercial uses shall be **8.0 in
C6-3 Districts** and 12.0 in C6-4 Districts". The citywide table says 6.0, so the
adjusted commercial FAR came out **4.156 against a correct 4.739 — understated
14%, with nothing null and no error raised anywhere.** This is the failure mode
where every lookup SUCCEEDS and the answer is still superseded.

**ZR Appendix B is the resolver**: `/appendix-b-index-special-purpose-districts`
indexes **101** special-district symbols to section numbers, so DCP's per-lot
symbol resolves to real regulatory text instead of to a memory of the
abbreviation. Confirmed: **MSX = Midtown South Mixed Use (121-00), TA = Transit
Land Use (95-00), DJ = Downtown Jamaica (115-00)** — none of which I would have
reliably expanded from the code alone. Cached in `decoder/zr_special_districts.json`.

`decoder/special_districts.py` applies an override ONLY from text that has been
read, with the citation. **Absence from the table means "not yet checked", never
"no effect"** — `status()` returns `unverified` and the lot is flagged. A regex
that found no floor-area section in MSX/TA is a WEAK NEGATIVE: it means the
search failed, not that the district is silent. MSX and TA remain unverified.

4 of the 22 pilot split lots sit in a special district: 1008000033 + 1008000074
(MSX), 1014460005 (TA), 4097930089 (DJ).

**Still open on this axis:** MIH/UAP. ZR 23-22's second column ("Qualifying
affordable housing or qualifying senior housing") IS parsed by `zr_feed` — R6
3.90, R8 7.20/8.64 narrow/wide, R11 15.0 — but `close_split_far` consumes only
the Standard-residences column, so the affordable figures are captured and
unused. MIH areas are a separate DCP layer (`bw8v-wzdr`), mapped in
SOURCE_MAP_DOB.md, not built. Note ZR 115-05 "Applicability of the Mandatory
Inclusionary Housing Program" — special districts also govern where MIH applies.

## THE ZONING RESOLUTION IS INDEXED — 4,051 sections (`decoder/zr_index.py`)

Login 2026-08-05: *"you should digest the entire zoning resolution assure you
dont miss this ... you need to understand that context if you are to attempt
verifying sf across various sites that are changing."* Right, and the method
matters: do NOT read it into context, HARVEST ITS STRUCTURE and consult it.

`zr_index.json` = every section number, title, article, chapter, URL, plus tags
for what it can modify. **4,051 sections / 101 chapters. 1,490 envelope-relevant:
bulk 454, geometry 384, supersession 346, floor_area 227, bonus 116, transfer 38,
grandfathering 37, affordability 34, density 31.**
**227 sections can change floor area. I had been consulting NINE.** Every modifier
found so far (street width, special district, uniform-FAR) was found by tripping
over it; the index turns that into a lookup. It is an index of WHERE TO LOOK, not
a store of rules — rules still come from reading the section, so a stale index
costs a missed section, never a wrong number.
Floor-area sections by article: ix 36, viii 32, ii 25, iii 22, xi 22, xiii 18,
xiv 17, vi 15, x 12, xii 12, iv 10, vii 5, i 1 — i.e. the SPECIAL PURPOSE
DISTRICT articles (VIII-XIV) hold more floor-area rules than the citywide ones.

## ⚠ SECTION-NUMBER -> URL: the prefix is 2 OR 3 digits

`23-22` -> Article 2 Ch 3, but `115-21` -> Article **11** Ch **5**, `121-00` ->
Article **12** Ch **1**. Reading the first two characters as (article, chapter)
sent 115-21 to Article I Chapter 1 and 404'd. **Every special purpose district
lives in Articles VIII-XIV and therefore has a three-digit prefix**, so that bug
made most of the supersession surface unreachable. Caught by the monitor, not by
me.

## HISTORICAL ZR: LAST AMENDED is the guard; the archive only reaches 2024-03

`/zr-downloads` publishes dated full-ZR PDFs but only **8 vintages, 2024-03
onward** — it CANNOT say what a rule said in 2004. What it can do is bound the
question, via `zr_feed.applies_at(section, date)`:
    last amended <= document date -> today's text IS what applied
    last amended >  document date -> it is NOT; the figure for that date is NOT
                                     ESTABLISHED (stated gap, never a silent
                                     substitution)
Verifying a 2004 instrument's floor area against the 2026 Resolution measures how
much the rules changed, not whether the decode is right — same error as comparing
lot areas to today's tax map instead of the contemporaneous vintage.
**OPEN SOURCING QUESTION for Login: pre-2024 ZR text.** DCP may publish older
editions elsewhere; this is a gap he could fill.

## MONITORING IS DESIGNED IN, NOT BOLTED ON (`decoder/monitor.py`)

Login: *"populating is one thing, monitoring and updating is another ... if the
zoning resolution changes thats huge, if the count on acris for development
rights changes, those are new sites."* Three fingerprints, all cheap, producing a
WORKLIST that the decoders then run against — keeping detection separate from
decoding is what makes a daily cadence affordable:
  * **RULE CHANGED** — a watched section's LAST AMENDED moves. Free, because
    zr_feed already stores it as part of the fact. Baselines captured 2026-08-05:
    23-22 / 24-11 / 33-121 / 33-122 / 33-123 / 77-22 = 12/5/2024; 43-12 + 43-132
    = 6/6/2024; **115-21 = 10/29/2025**.
  * **UNIVERSE GREW** — the COUNT of a doc type in ACRIS moves. One count query,
    no document fetched. **DEVR baseline = 1,201 documents** (the figure earlier
    in this project was 1,189 — the universe has ALREADY grown by 12).
    A count that FALLS is not normal and must be read before either number is
    trusted.
  * **PARCEL MOVED** — zoning district, lot area, or the lot ceasing to exist.
A check that could not run is reported as `check_failed`, never as clean.

## Population progress reporting — DEFERRED, deliberately (Login 2026-08-05)

*"we cant populate parcel and track progress until the system is 100% refined.
this means 100% accuracy and every aspect of the lifecycle of a parcel. then we
can consider enrichments."* So the metric that matters NOW is refinement (audit
falls at zero, every lifecycle stage having named evidence), not coverage. Build
population progress reporting when parcel-by-parcel starts, not before — a
coverage percentage computed over an unrefined system is the same self-validating
summary as [[feedback_bkrea_scale_failure]].

## MSX and TA resolved — and the FAR answer was the LEAST useful part

Both checked against the FULL section list of their chapter, not just what a
keyword search tagged. **A title index cannot prove absence**, so a negative
claim gets read in full or it is not made.

**MSX (Midtown South Mixed Use, Art XII Ch 1, 22 sections): does NOT change base
FAR.** Its only floor-area section is 121-31, a PUBLIC SCHOOL exemption; 121-30
"SPECIAL BULK REGULATIONS" covers yards, height/setback and street walls. So the
citywide figures for 1008000033 and 1008000074 stand. **But**:
  * **121-341 Transfer of development rights from LANDMARKS** and **121-342 from
    the THEATER SUBDISTRICT** — MSX changes the envelope through TRANSFER, which
    is exactly this decoder's subject. A DEVR in MSX may draw on either.
  * **121-05 Applicability of Article XII Chapter 3** — incorporates the Special
    Mixed Use (MX) regulations BY REFERENCE. Chain still to follow.
  * **121-04** MIH applies here.

**TA (Transit Land Use, Art IX Ch 5, 24 sections): ZERO floor-area sections.**
Does not change FAR at all. **But 95-11 is RECORDATION** — a transit easement is
RECORDED, so it lands in ACRIS as an ENCUMBER (with 95-12 Termination and 95-13
Previous Transit Easement Agreements). And **95-04 Certification of Transit
Easement VOLUME**: the easement is a volume bounded by a limiting plane, the same
shape as the airspace parcels already decoded. Lot 1014460005 sits in TA on
Second Avenue (Second Avenue Subway) — expect a recorded transit easement there.

**The lesson: asking "does this district change FAR" is the narrow question.** The
useful answer was what each district GENERATES — transfers in MSX, recorded
easement volumes in TA. That is the "context" Login meant: a district explains
how a site got its rights, not just what its FAR is today.

## ZONING OVER TIME — the answer is the MAP history, not the text history

Login asked what reference gives zoning as it applied at a past date.
**DCP `nyzma` (Zoning Map Amendments, ArcGIS, same org as nyzd): 1,414 features,
1,237 with EFFECTIVE dates spanning 1977-01-20 .. 2026-05-20, plus 29 STATUS
!= 'Adopted' still in the pipeline.** Fields: EFFECTIVE, STATUS, ULURPNO,
PROJECT_NAME + geometry. That is the "which district applied to this lot on this
date" layer, and it is also a FORWARD signal (certified-but-not-adopted
rezonings = sites about to change).

Layer the sources by what each answers:
  * **which district applied when** -> `nyzma` 1977-2026 (+ the 1961 base map for
    pre-1977 and for non-conforming rights). THE useful one.
  * **what the rule text said** -> zr.planning.nyc.gov, but the full-ZR archive
    only reaches **2024-03**; use `zr_feed.applies_at()` to say when today's text
    is NOT safe for a past date rather than substituting it silently.
  * **when a special district began** -> ZR Appendix B carries CPC ADOPTION and
    BOE/COUNCIL ADOPTION dates per district (e.g. Battery Park City 11/14/73 then
    10/19/81). A dated history already in hand.
Remaining gap: ZR TEXT 1961-2024, and map coverage 1961-1977.

## DOF — consulted for GEOMETRY ONLY; the rest is untouched (workbook 2026-08-05)

Honest state when Login asked: the decoder uses DOF's Digital Tax Map for
polygons and PLUTO (which derives from DOF's RPAD) for lot area. **No assessment,
no exemptions, no arrears, no sales, no income.**

Two datasets in the workbook SUPERSEDE inference already being done:
  * **`smk3-tmxj` Digital Tax Map** — "creation, merger, apportionment and
    retirement … the authority on lot lineage". The spine has been INFERRING
    lineage from PLUTO vintages. (Socrata metadata returns no column list; needs
    a live probe.)
  * **`eguu-7ie3` Digital Tax Map: Condominium Units** — unit lot -> parent,
    published. **Verified: MN 1446 lots 1101-1181 = 81 units -> base 1014460149,
    condo 950** — exactly what was inferred from the document's "f/k/a Lot 149"
    recital + PLUTO appbbl. Inference CONFIRMED, but note **block 1446 holds
    THREE condos** (514/lot 35/36 units, 1521/lot 41/13 units, 950/lot 149/81
    units): a block-wide resolution would have swept in 49 unrelated unit lots.
    Right answer, fragile method — now sourced.
  * **`ag5u-vnw2` Subterranean Lots** — only **81 citywide**; below-grade lots
    (rail, utility, vault). The counterpart to the airspace parcels already
    decoded: parent_bbl -> sub_lot_bbl.

High-value DOF sources still unconsulted, by function:
  VALUE     rgy2-tti8 assessment roll · a5nd-6mit assessment CHANGE ("a large
            jump often follows a completed alteration or a lost exemption" — a
            lifecycle signal) · w2pb-icbu annualized sales (2016+) · aht6-vxai
            Article 7 certiorari petitions (owner suing over the assessment)
  ⚠ CO-OPS  9ck6-2jew condo + **myei-c3fa co-op comparable rental income — "the
            only public per-building income figure for a property type that
            records no deeds"**. Second route into the co-op blind spot alongside
            HPD's Shareholder role.
  DISTRESS  9rz4-mjek tax lien sale lists · scjx-j6np property charges balance
  VALUE/DEV muvi-b6kx exemption detail (421-a, ICAP) · rgyu-ii48 abatements
            (J-51) — directly development-relevant
  OCCUPY    92iy-9c3n storefronts reported vacant (Local Law 157)
  TITLE     fn4k-qyk2 COLP city-owned property · sv7x-dduq ACRIS Personal
            Property Master (UCC — **security in COOPERATIVE SHARES**, the co-op
            financing route ACRIS real-property records cannot show)

## DOF LOT LINEAGE IS PUBLISHED — stop inferring it (`decoder/dof_lineage.py`)

Socrata `smk3-tmxj` is a BLOB download, not an API. The queryable copy is DOF's
own ArcGIS **`DTM_ETL_DAILY_view`** (a DAILY ETL, which also suits monitoring):
  layers  0 TAX_LOT_POLYGON, 1 TAX_BLOCK_POLYGON
  tables  2 AIR_LOT, 3 CONDO, 4 CONDO_UNIT, 5 REUC_LOT, 6 SUB_LOT,
          **9 DAB_BOOK_HEADER, 15 DAB_LOT** (+ DAB_AIR/BLOCK/CONDO/SUB, PTS_*)

**The Digital Alteration Book is the lineage authority**: DAB_LOT gives BBL +
Lot_Action (Dropped / Affected / Added) + TRANS_NUM; DAB_BOOK_HEADER gives
Change_Date, Change_Type, **Auth_for_Change**, and the NEW block/lot.
**77,904 entries, 2008-05-20 .. 2026-08-04.** Before 2008 the spine's PLUTO-vintage
inference is still the only route.

**⭐ `Auth_for_Change` CITES THE INSTRUMENT** — CRFNs, deed dates, surveyor name
and survey date, DOB/PW1 job numbers. That is a TWO-WAY JOIN between parcel
lineage and the documents this decoder reads: `history(bbl)` for what changed and
why, `by_instrument(crfn)` for which lots a recorded document moved. Verified
live on CRFN 2012000483179 -> BBL 1015400003. (It is free text, so a LIKE scan:
matches are evidence, a non-match is not proof.)

**CONDO_UNIT replaces the appbbl chain.** Verified: base 1014460149 -> 81 units.
⚠ Never resolve unit lots BLOCK-WIDE: MN 1446 carries THREE condos
(514/lot 35/36 units, 1521/lot 41/13 units, 950/lot 149/81 units) — a block-wide
query sweeps in 49 unrelated unit lots. Key on base BBL or unit BBL.

**AIR_LOT and SUB_LOT** give the vertical carve-offs (parent_bbl -> air/sub lot),
the map's record of the airspace parcels ZLDAs create. Only 81 subterranean lots
citywide.

## PARTIES: observation -> entity -> timeline (`decoder/entities.py`)

Login 2026-08-05: *"keep the names with the entity and then we find contacts
later. It is important to also indicate their role and when. not just who it is
and party since that makes time hard to see linearly."*

**⚠ First, a gap I had been asserting away:** `party_observation` had **ZERO
rows**. The account existed in the chart, `parties` sat in every decode's
raw_facts, and the reducer never emitted them — so every name decoded was
invisible to any query, while I was describing party capture as if it worked.
Fixed in `migrate_to_supabase.reduce_doc`: **54 observations, 47 entities**.

**The three layers, same shape as the ledger:**
  * **observation** — immutable and STAMPED: name, ROLE, lot, document, DATE.
  * **entity** — the actor behind name variants. A JOIN, never an edit; the
    observation keeps the name exactly as the document wrote it.
  * **timeline** — fold observations by entity or by parcel, in date order.
    This is what makes time linear, which a flat contact list destroys.
A CONTACT is a further fold ("who do I call today") and is deliberately NOT built:
**contacts age, observations do not.** Build it once the stage model populates,
because a contact's worth depends on the stage — a managing agent matters in
operation, a PW1 §26 owner-with-phone matters in pre-development.

**Normalisation is deliberately conservative**: a FALSE MERGE invents a
relationship between sites and is invisible afterwards. Only case/punctuation
folding and suffix normalisation (L.L.C. -> LLC, kept not dropped). Address- or
officer-based merging is an INFERENCE and belongs in a reviewable enrichment step.

**⚠ A trailing parenthetical is not one thing.** "(Torkian Group)" is a SPONSOR
behind an SPE — the SPE is disposable, the sponsor is what tracks across sites.
"(70%)" is an OWNERSHIP SHARE. Read as an alias it invented two entities named
"70%" and "30%". Split by shape: digits/punctuation/percent = share, anything
with a letter = name. Both are kept.

**What the timelines already show at n=14 documents:**
  * **301 EAST 71 INVESTORS LLC** (sponsor: Torkian Group) — receives rights
    2025-12-18, declares the zoning lot 2026-01-09, receives more the same day.
    A developer ASSEMBLING, legible in one view.
  * **1683 THIRD AVENUE ASSOCIATES LLC** — grantor AND recipient on the same
    instrument: the self-to-self airspace split, correctly surfacing as
    role-changed rather than as two parties.
  * **NEW YORK COMMUNITY BANK** — consenting mortgagee on two sites 11 years
    apart. A multi-site lender, which is a different kind of actor from a
    counterparty.
  * **BOARD OF MANAGERS OF THE KNICKERBOCKER CONDOMINIUM** — declarant AND
    grantor of rights: the condo board is the one selling the air rights.
`role_changed` and `multi_site` are the flags worth watching — an actor on BOTH
sides of the market is the interesting case.

## ⭐ ACRIS DOCUMENTS CARRY A NOTICES BLOCK — the richest contact source, and I was skipping it

Found 2026-08-05 while hunting for a legal description in doc 2004110301042003
(p17). The **Notices** section of a ZLDA prints a full contact block per party:

    To Owner:      Marie Vittiburga, 59 Richardson Street, Brooklyn NY 11222,
                   Tel (718) 387-0732          <- a NATURAL PERSON owner with a phone
    with a copy to Ernest Thifault, Esq., 154 Norman Avenue, tel + fax
    To Developer:  Bayard House, LLC, 62 Bayard Street, **Att'n: Mr. Witold Brend**,
                   tel + fax
    and            Sabin Enterprises, Inc., **SAME address, SAME Att'n**
    with a copy to Sheldon Lobel, P.C., Att'n: Jordan Most, Esq.

Three things this gives that nothing else does:
  1. **A named HUMAN behind an SPE** ("Att'n: Mr. Witold Brend") with phone and
     fax — the ACRIS equivalent of DOB PW1 §26, and available from 2004.
  2. **Entity linkage STATED, not inferred**: Bayard House LLC and Sabin
     Enterprises Inc share an address AND a principal, printed in one block. That
     is exactly the "same address, same officer" merge I said belongs in a
     reviewable enrichment step — here the DOCUMENT asserts it, so it is a fact.
  3. **Counsel on both sides** — repeat zoning counsel is itself a network signal.
Cross-check that it is real contact data: the owner's notice address (59
Richardson Street) is ON the Owner Land, which fronts Richardson Street.

**⚠ GAP IN THE EXTRACTION CONTRACT: there is no `notices[]` block.** Every decode
so far has read past this page. Add it — name, role, street address, phone, fax,
attention-party, and which party it serves — and re-read it for the documents
already decoded.

## Finding exhibits CHEAPLY: page BYTE SIZE ranks the reads

Reading pages blind to locate a legal description is the expensive step (an image
costs far more to read than to fetch). The two page kinds differ in the bytes:

    body prose        dense, justified, full margins    48-82 KB
    exhibit / legal   title + a paragraph + whitespace   8-33 KB

Measured: 2026061500475003 p18/19 = 16.5/14.8 KB · 2012120600575002 p15/16 =
23.8/25.8 KB · 2026012000388003 p36/37 = 33.0/17.6 KB · 2026012000388004 p40 =
7.9 KB — against 48-82 KB body pages in the same documents.
`fetch_pages.py --scan <doc> <dir> <lo> <hi>` fetches a range, ranks lightest
first, and stops at the placeholder (so it also finds the page COUNT).
**Verified first try:** scanning 2004110301042003 pages 19-34 found the document
ends at 28, flagged p20-21 and p23-28 as light, and p23 was Exhibit A.
It is a HEURISTIC for ORDERING reads, never a classification — a 13-course metes
description is dense; nothing is discarded, only deprioritised.

**2004110301042003 Exhibit A DONE** — Owner Land, Lot 36 (BBL 3027220036):
4 courses, **2,500.0 sf, closure 0.00 ft**, and PLUTO agrees exactly at 2,500.
Note the shape of the deal: **4,075 sf of rights conveyed from a 2,500 sf lot** —
rights are not bounded by lot area, they are bounded by lot area x FAR minus what
is built, which is why the envelope ledger cannot be checked against lot size.

## ⭐ CONTIGUITY IS PROVABLE FROM THE EXHIBITS ALONE — no map needed

Doc 2004110301042003 (Greenpoint, 2004), four exhibits read via the byte-size
scan. Every description is a TIE LINE from the same corner (Lorimer Street), so
the parcels can be laid out on one axis without any geometry source:

    Richardson Street, north side  (feet EAST of Lorimer)
       lot 36    75-100   25 ft wide x 100 deep =  2,500 sf   <- Owner Land
       lot 34   100-150   50 ft wide x 100 deep =  5,000 sf
       lot 33   150-175   25 ft wide x 100 deep =  2,500 sf
    Bayard Street, south side
       lot 10   125-200   75 ft wide x 100 deep =  7,500 sf

  * Richardson frontage 75 -> 100 -> 150 -> 175 with **NO GAPS** — contiguous.
  * Richardson lots run 100 ft NORTH, Bayard lots 100 ft SOUTH, so **the
    descriptions themselves imply a 200 ft block depth** and lot 10 backs onto
    lots 34 and 33 across the rear.
  -> the merged zoning lot is contiguous, proved from four recorded exhibits.

**This is the third document where the TIE LINE carried the merger-critical fact**
(after 2026061500475003 and 2026012000388003). The pattern is now firm: **a tie
line locates a parcel absolutely against a street corner, so parcels sharing a
corner reference can be compared WITHOUT a survey traverse and without a map.**
Contiguity is provable even where a traverse does not close (as in
2026061500475003, where neither exhibit closed).

Deal shape worth remembering: four exhibits total **17,500 sf of LAND** and the
instrument conveyed **4,075 sf of RIGHTS** — rights are bounded by lot area x FAR
minus what is built, never by lot area, so an envelope posting can never be
sanity-checked against parcel size.

Lot 8 (Exhibit B-1 continues on p27) is still unread; the chain above already
holds without it, and an additional parcel can only extend an assemblage, not
break it.

## A FOURTH description shape: the PERIMETER of several lots

Doc 2021020901358005 (Harlem 2021), p14: **"Block 1908, Lots 4 and 60
(Perimeter)"** — ONE 8-course L-shaped description bounding TWO lots together,
not one description per lot. Closes at **14,388.6 sf, closure 0.00 ft**.

**Triple reconciliation, three independent sources:**
    perimeter traverse            14,388.6 sf   (this decode)
    PLUTO lot 4                    4,297   sf
    document-stated lot 60        10,092   sf   (PLUTO has lot 60 ABSENT)
    4,297 + 10,092 =              14,389   sf   -> agrees to 0.4 sf
A parcel PLUTO can only half-see, closed out by the instrument itself.

Description shapes now seen — the contract must handle all four:
  1. per-lot metes and bounds
  2. INCORPORATION BY REFERENCE (Exhibit D of 2026012000388004: a plane over
     another exhibit's footprint, no courses of its own)
  3. VERTICAL parcels (above/below a limiting plane, footprint identical to the
     lower parcel so areas are NOT additive)
  4. **PERIMETER of several lots** — area is the SUM of the constituents, so it
     must never be posted against a single BBL

## More party observations hiding in plain sight

Doc 2021020901358005 p19 is an ARCHITECT'S CERTIFICATION, signed and sealed:
**John H. Rodenbeck, AIA, NCARB, LEED AP, EDAC, Partner — NY registered architect
licence 037995-1.** A licence number joins straight to DOB's licence register.
Together with the NOTICES block (owner/developer/counsel with phones) and DOF's
`Auth_for_Change` (surveyor name + survey date), ACRIS documents are naming FOUR
professional roles the decoder has not been capturing: owner contact, counsel,
architect (with licence), surveyor.
(Minor tell of care: that letter's footer still reads the unfilled template
placeholder "Client Name, Project, Date".)

## CONTRACT REVISED 2026-08-05 — three additions, all enforced by the audit

`EXTRACTION_CONTRACT.md` now requires:

1. **`shape` on every legal description** — `per_lot | perimeter | vertical |
   incorporation_by_reference`. Required because **the shapes disagree about
   whether areas ADD UP**, and getting it wrong is silent in opposite directions:
     * `perimeter` is ADDITIVE (one bound, several lots) — posted against a single
       BBL it TREBLES that parcel (MN 1908 lots 4+60: 14,388.6 sf against lot 4's
       own 4,297)
     * `vertical` is NOT additive — the same ground described twice, above and
       below a plane (2012120600575002: sum them and 2,504.17 sf is double-counted)
   A `perimeter` must carry `covers_bbls`; a `vertical` must carry
   `vertical_extent` INCLUDING whether the datum is defined on the page.
2. **`notices[]`** — serves_party, role (party/counsel/attention_individual),
   name, **attention** (the human behind an SPE), address, phone, fax, email.
3. **`certifications[]`** — kind (architect/surveyor/engineer), name,
   credentials, **licence_number** (joins DOB's licence register), what it
   certifies.

Audit checks added: shape declared (+ shape-specific required fields), and a
contacts INFO check that NAMES the documents not yet read — so the backfill
cannot quietly stall.

**Backfill state after the first pass:** 18/18 descriptions verbatim (was 13),
**18/18 shapes declared**, 7/14 documents complete. Notices captured for 1
document (5 contacts), certifications for 1. **13 documents still need their
notices page read** — that is page-read work, not a code change.

Newly recorded this pass: 2004110301042003 all four exhibits (lots 36/10/33/34,
every one closing at 0.00 ft) and 2021020901358005's perimeter.

## ⚠ PATH MOVED 2026-08-05 — decoder is now under `Decoder Prompt\decoder\`

Mid-session the source folder was reorganised: `Source Folder (Real Estate
Data)\ACRIS\decoder\` is GONE; everything lives at **`Source Folder (Real
Estate Data)\Decoder Prompt\decoder\`**. All 39 files intact and everything
runs unchanged — the modules resolve their own data with
`pathlib.Path(__file__).parent`, so relocation cost nothing. Two absolute paths
still point outside and are unaffected: `C:/dev/acris-decoder.env` (credentials)
and `C:/dev/bkrea-territory-intelligence-app` (the zoning-reference dump).
If a path fails, SEARCH before concluding anything is lost.

## A FIFTH contact-bearing block: `acknowledgments[]`

Found on doc 2014091201052002 p20. The jurat gives what nothing else does:
  * **the HUMAN who signed for the entity** — "David Mathew Owens **a/k/a**
    David M. Owens". The a/k/a is a name variant STATED by the document, which
    is exactly what entity resolution must otherwise guess at.
  * **the notary, identified**: Donna S. Weisman, No. 01WE6025982, Queens
    County, commission expiring 2015-06-07.
  * **⚠ A DEFECT SURFACE.** The page carries TWO acknowledgment blocks and the
    second is wholly UNEXECUTED — blank name, date, signature and notary, in a
    RECORDED original. Recorded as `executed: false`, never as absent-and-fine.
    (Matches the earlier pilot finding of a missing acknowledgment; this is the
    second instance, so it is a pattern, not a one-off.)

Notices, certifications and acknowledgments are three views of one question —
**who touched this document, in what capacity** — kept separate because the
capacity IS the point. Audit now reports unexecuted jurats as their own INFO line
so a defect is never read as missing data.

**Audit: 19 checks, 1 FAIL** (7 documents still carrying no description block).

## ⚠ metes.py bug FIVE: distances SPELLED OUT IN WORDS

Doc 2014091201052002 Exhibit A writes every distance as words: *"distant ONE
HUNDRED AND SEVENTY-TWO FEET easterly ... RUNNING THENCE northerly parallel with
Graham Avenue, ONE HUNDRED FEET; THENCE easterly ... TWENTY-TWO FEET"*. A
digits-only parser returns None for all of them.

Credit where due to the earlier rule — **"prefer an UNPARSEABLE course to a
silently wrong one"** meant this surfaced as a dropped traverse rather than as a
wrong area. The rule paid for itself.

Fix: `words_to_number()` + word forms in `parse_distance`, tried ONLY after the
numeric forms (a digit always wins) and ANCHORED TO THE UNIT WORD, so a stray
"one" in prose ("part of the way through a party wall") can never become a
distance — that exact case is now a unit test. **13/13 parse_distance tests pass.**
Handles "twenty-two feet", "one hundred feet", "one hundred and seventy-two feet",
"seventy-six feet eight inches".

Result: Block 2765 Lot 35 (173 Devoe Street) closes at **2,200.0 sf, closure
0.00 ft**, and PLUTO agrees exactly at 2,200.

Also worth capturing per description: **the exhibit often states its own BBL and
street address** ("Also known as 173 Devoe Street ... Block 2765, Lot 35") —
recorded as `stated_bbl_in_exhibit` / `street_address_in_exhibit`. That is the
document naming its own parcel, which beats any inference from the index.

**Audit: 19 checks, 1 FAIL. Descriptions 19/19 verbatim, 19/19 shaped,
8/14 documents complete; 6 still carry no description block.**

## ⭐ NEW VALIDATOR: a notary's commission must be LIVE on the jurat date

Doc 2025102901095004 p33: the stamp reads **"JACOB GROSS, Notary Public State of
New York, No. 02-GR6183574, Qualified in Kings County, Commission Expires March
17, 2023"** — against a jurat dated **October 2025**. **The commission had lapsed
by more than two years when the acknowledgment was taken.** An acknowledgment
taken by a notary whose commission has expired is defective on its face. The
month was also altered by hand on the recorded original ("August" struck,
"October" written above).

The check is cheap and universal (compare `commission_expires` to the jurat
`date`) and it catches something nobody reads for. Now permanent in `audit.py`.

## ⚠ SEVERITY DISCIPLINE — caught myself grading a DOCUMENT defect as OUR failure

The new check first shipped as **FAIL**, which was wrong. **A FAIL means OUR
STORE is unsafe to use. A lapsed commission is a defect in the RECORDED
ORIGINAL that the decoder captured correctly** — the pipeline is working exactly
as designed when it fires. Same reasoning already applied to the
unexecuted-jurat check. Corrected to INFO with the tag "DOCUMENT DEFECT, not a
decode gap".

**The general rule, now explicit: grade by WHOSE problem it is.**
  * FAIL  — our data is wrong, missing, or unsafe to use
  * INFO  — a finding about the world, correctly captured
Grading findings about the world as failures of our own data trains everyone to
ignore FAILs, which is how a real fall gets missed.

**Audit: 20 checks, 1 FAIL (the description backfill), 11 PASS, 8 INFO.**
Two document defects now standing on the record: one unexecuted acknowledgment
block (2014091201052002) and one expired notary commission (2025102901095004).

## ⚠ CORRECTED: the expired-notary "defect" was OVERSTATED (Login's question)

Login asked "if it expired, does that mean a new filing is in place?" — and the
question exposed that I had over-claimed. **Two errors in one finding:**

1. **A STAMP IS NOT THE COMMISSION.** NY notary terms run four years and notaries
   routinely keep using an old stamp after renewing. What was observed is a
   STALE STAMP; whether the commission was live is a different, checkable fact.
   The **NY DOS notary register** would settle it — not consulted. The field is
   now labelled `commission_expires_source: "stamp impression — NOT verified"`.
2. **NY Executive Law 142-a CURES IT.** The statute validates a notary's acts
   notwithstanding an **expired term** (subd. 2). Protection is withheld where
   the defect is *"apparent on the face of the certificate"* — a visibly stale
   stamp IS — **but that limitation itself lapses SIX MONTHS after the act**
   (subd. 3). Jurat 2025-10-12 -> window closed **2026-04-12**. Today (2026-08-05)
   the acknowledgment is cured. Verified against the statute text, not recalled.

**Answer to the question: no new filing was needed and none exists.** Checked
every ACRIS document indexed against QN 12099 lots 50/32/38 — no corrective or
re-recorded instrument. The check is now worded as **a lead, not a verdict**.

**Lesson: a defect on the face of a document is not the same as a defect in law.**
Recording the observation is right; concluding invalidity is not ours to do. Where
a curative statute exists, cite it and DATE the cure.

## The Jamaica parcel's post-transfer filings — the lifecycle, visible

Same parcel, everything recorded after the DEVR (a good worked example of
[[PARCEL_LIFECYCLE]] and of the debt throughline):
    2025-10-30  DEVR $1,685,980 + DECL + SMIS + ZONE      <- envelope assembled
    2025-11-21  DEED, MTGE $22,243,580, MTGE $20,484,420,
                AGMT $12,272,000, MLEA, ASST, TL&R, PREL x2   <- ~$42.7M financed
    2026-01-09  DEED, MTGE $9,000,000, AGMT $28,084,130.63,
                AL&R, MLEA, ASST, ASSTO                       <- further ~$37M
Rights transferred, then financed three weeks later. **MLEA (Memorandum of
Lease) appears in BOTH rounds** — the ground-lease thread Login flagged as a
future decoder, showing up inside a deal already in the store.

## ⚠ metes.py bugs SIX and SEVEN — both exposed by the FIRST surveyed description

Doc 2025102901095004 p26 (QN 12099 lot 38) is the pilot's first description using
**quadrant bearings** ("North 00°37'08" West, a distance of 50.69 Feet") rather
than "parallel with X Street" recitals. It broke the engine in two ways at once,
and the traverse came back with an area of 531 sf against a real 21,564.

6. **Bearings SPELLED OUT were not matched.** The pattern wanted `N ... E`; a
   survey writes `North ... West`. Every such course fell through to the cardinal
   fallback, which returned a COMPASS DIRECTION (270°) in place of the surveyed
   angle (359.3811°). Silent — a plausible azimuth, wrong by half a degree to
   ninety. Fix: `BEARING_RE` accepts abbreviated OR spelled-out quadrant letters.

7. **⭐ A BEARING'S MINUTES AND SECONDS WERE READ AS FEET AND INCHES.** In a
   bearing `37'08"` means 37 MINUTES 8 SECONDS; in a distance the identical
   string means 37 FEET 8 INCHES. Reading "North 00°37'08" West, a distance of
   50.69 Feet" for a distance returned **37.67 ft** — the bearing's own minutes
   and seconds — and ignored the 50.69 the document states.
   **Fix: parse the bearing FIRST, delete its matched span, then read the
   distance from what remains.** Same notation, opposite meaning, nothing about
   the result looks wrong — the worst kind of bug.

**External proof after the fix:** closure **0.009 ft over a 770 ft perimeter =
1:90,909 (surveyor grade)**, area **21,561.8 sf against PLUTO's 21,564.0 — 0.01%**.
Before the fix: 531.5 sf, closure 43.9 ft.

Also: one of my own bearing test EXPECTATIONS was wrong (S 89°31'37" W is
269.5269°, not 269.4736° — my arithmetic). The code was right. Worth remembering
that a failing test can be the test's fault, and that checking which is which
takes ten seconds.

**Descriptions now 20/20 verbatim, 20/20 shaped, 9/14 documents complete.**
Five documents still carry no description block: 2010102601040006,
2014070300770002, 2017053000419005, 2021070601644010, 2026012000388002.

## ⚠ SIGNATURE PAGES ARE EVIDENCE — a decoded party fact was WRONG

Doc 2017053000419005 p42. The decode recorded the First Presbyterian Church in
Jamaica as **"NOT a signatory; transfers via separate Lot 86 ZLDA"**. The
signature page shows **"Trustees of the First Presbyterian Church in Jamaica"
executing the instrument, signed by the Clerk of Session.** The Church IS a
signatory. Corrected, and its `normalized_role` flagged for review — a party
recorded as `other_zoning_lot_member` on the assumption it did not sign may
actually be a GRANTOR, which would change the envelope posting for 4/9793/86.

**Found only because the exhibit hunt happened to land on the signature page.**
The first pass skipped straight past it. Signature blocks are now their own
capture (`signature_blocks[]`): entity, signatory as written, TITLE, page.

**The TITLE is often more reliable than the name.** Both names here are
handwritten and only partly legible, and are recorded WITH a legibility caveat
rather than a confident transcription. But the titles are printed-clear:
**Vice-Chairman** (a CDC) and **Clerk of Session** — the latter being the correct
Presbyterian congregational officer to execute for a board of trustees, which
corroborates that the execution is regular even where the name is not readable.
Rule: transcribe a legible title with confidence, an illegible name with a caveat,
and never let the caveat on one contaminate the other.

Corroborates [[project_bkrea_viability]]: religious institutions DO transact
development rights — here a Presbyterian church is a party to a rights transfer.

## MESSY SIGNATURES: the method (`decoder/SIGNATURE_LADDER.md` + `entities.resolve_signatories`)

Login: deeds are handwritten, other documents PRINT the same names, and later
rungs carry full contact — so entity -> name -> contact -> profile.

**The governing rule: a signature is the WEAKEST evidence of a NAME and the
STRONGEST evidence of an ACT.** Split them and record them at different
confidences:
    certain    someone executed this, in this TITLE (printed), on this date,
               for this entity
    uncertain  who they are
Recording both at one confidence is the error.

**The join key is (entity + title + date), never the name** — all three are
readable when the signature is a scrawl.

**The ladder of PRINTED rungs:** 0 signature (act) → 1 jurat (typed signatory +
notary) → 2 Notices block (name, ATTENTION-party, address, phone, fax) → 3 ACRIS
party index `636b-3b5g` (entity names + ADDRESSES, typed) → 4 DOB PW1 §26 (owner,
title, business, PHONE + EMAIL; PDF only) → 5 HPD contacts `feu5-w2e2` (head
officer, managing agent, shareholder; refreshed ANNUALLY) → 6 LPC `dpm2-m9mq`
(applicant AND owner) → 7 **NYS DOS corporate filings** (officers — the rung that
turns an SPE into people) → 8 sealed certifications + DOF `Auth_for_Change`
(architect with LICENCE NUMBER, surveyor, survey date).
Each rung is a DIFFERENT DOCUMENT TYPE, which is why the ladder only works once
several types are decoded for the same parcel.

**⚠ The index will not save you:** the ACRIS party index for 2017053000419005
lists three entities and **omits the First Presbyterian Church, which signed the
instrument**. The signature page is sometimes the ONLY place a party appears.
(It did give addresses though: FJCUDC and the HDFC share 89-60 164th Street —
typed entity-to-address linkage.)

**Confidence is UPGRADED, never overwritten.** `signature_blocks[]` carries
`signatory_as_written` + `name_confidence` (illegible | handwritten_uncertain |
typed | legible_print); a resolution lands BESIDE it as `resolved_name` +
`resolved_from`. A wrong resolution stays visible and reversible — same rule as
entity normalisation, same reason.

`entities.resolve_signatories()` returns CANDIDATES with a status
(resolved / ambiguous / no printed instance yet) and never edits anything. Run
2026-08-05: both 2017 signatories return **"no printed instance yet"** — correct,
because that document's jurat pages have not been read and it has no notices
block captured. The resolver names what is missing instead of guessing.

## IDENTIFICATION STRENGTH IS A PROPERTY OF THE DOCUMENT **TYPE** (`decoder/id_strength.py`)

Login's observation: across types you meet no signature, then a signature, then
PRINT, then full contact — and that difference belongs to the TYPE. Written down,
it converts hunting page-by-page into REACHING for the right document.

Five levels, strictly ordered:
    none → signature (mark + printed TITLE; proves the ACT) → printed_name
    → addressed (name + street address) → full_contact (+ PHONE, sometimes email)

**⚠ The level is a CEILING for the type, not a guarantee for the instance.**
DEVR/ZLDA rates `full_contact` because 2004110301042003 carries a Notices block
with phones — but 2014091201052002 has a jurat and NO notices. Per-document it
varies; the registry says where it is WORTH LOOKING.

**⚠ `observed` vs `EXPECTED` is the honest column.** Only levels seen on a page
actually read here are `observed: True`. Everything else comes from the source
workbooks and must never be quoted as measured.

**The finding that matters: exactly ONE confirmed full_contact source exists —
the DEVR/ZLDA itself.** The type already being decoded is the strongest CONFIRMED
route to a named human with a phone. DOB PW1 §26 is expected to equal it and is
unbuilt. Everything else confirmed tops out at `addressed` (ACRIS party index,
entities only) or `printed_name` (DOF surveyor firms).

Confirmed today: DEVR/ZLDA full_contact · ACRIS party index addressed · DOF
Auth_for_Change printed_name · DECL signature.
Expected, unverified: DOB PW1 §26 full_contact · HPD contacts, LPC permit, MTGE,
MLEA, NYS DOS addressed · DEED printed_name.

## ENRICHMENT / PROFILING — designed, DEFERRED by Login (`decoder/ENRICHMENT.md`)

Login: once we have parcel → document → role → entity → name → real company →
real role → phone/email/mailing, profile the person from internet sources. Then:
**"not yet, but after we finish a parcel lifecycle we could probably understand
every single person who played a role in its past — and future."**

**The rule: a DECODED fact cites a document; an ENRICHED fact cites a source AND
a match.** Separate tables. Enrichment carries `source`, `match_keys`,
`match_confidence`, `matched_to`. Require **two independent corroborating keys**
(entity, address, title, date-range) before `strong`; one key is `weak` and
`weak` never propagates into a contact. This is the false-merge problem again,
but worse — it attaches a LIVING PERSON to someone else's transaction.

**⚠ NO LinkedIn scraping.** Terms prohibit it and it enforces actively; a source
that fights the collector breaks SILENTLY, and a silent break is
indistinguishable from a real absence — the exact failure this decoder exists to
prevent. Same standing rule as ACRIS images and [[project_bkrea_crexi_derivation]].
Scope stays BUSINESS CAPACITY: who acted, in what role, on which deal.

**Better sources, authoritative first:** NYS DOS corporate filings (officers +
address for service — turns an SPE into people) · **SEC EDGAR Form D** (real
estate syndications file constantly and the form NAMES executive officers and
promoters — structured, free, unread in brokerage) · licence registers (a licence
number IS a verified individual; certifications already give us those) · NYC CFB
+ City Clerk lobbyist registry · NY e-courts · company sites last.

**Build only when** `resolve_signatories()` returns `resolved` rather than
`no printed instance yet` — a profile hung on a misread signature is worse than
no profile.

## ⭐ A parcel's cast is PAST, PRESENT **and FUTURE** — the future is already named

Login's addition, and it is the sharp part. Future participants appear in records
that have not matured:
    nyzma 29 CERTIFIED-not-adopted   applicant, project, ULURP no. — a district
                                     about to change
    BSA calendared / SOC pending     applicant + counsel, variance in flight
    LPC CALENDARED (not designated)  a constraint about to bind
    DOB job filed, no permit         owner (PW1 §26), architect, expediter
    CONH required, not certified     a permit gate not yet cleared
    MLEA + MTGE just recorded        lender and ground lessee — who NOW has a say
Worked example, QN 12099: the October DEVR named the transferors, but November's
**$42.7M of mortgages and an MLEA named the parties who will actually shape what
gets built** — a lender and a ground lessee absent from the record six weeks
earlier.
So: past participants (decoded) · present holders (folded to current) ·
**forecast participants (named in PENDING filings)** — and the third is a
MONITORING output, which is why `monitor.py` watches counts and pipeline status.

## COUNTERPARTY PROFILES — the buyer/seller substrate (`entities.counterparty_profiles`)

Login: knowing patterns, history and "ins" on who people are is what makes this
work for finding BUYERS AND SELLERS. Built — and it needs no new source, because
it folds party observations against envelope postings.

Per entity: sides taken (sold / bought / lent_to / declared), parcels, documents,
counterparties, active date range, **$/sf range**, and flags `both_sides` and
multi-site. Every field DERIVED from stamped observations, so any line walks back
to a document and a page. Nothing is inferred about a PERSON — it is a record of
what their ENTITIES did.

At n=14 documents it already surfaces the right shapes:
  * **New York Community Bank** — lender on 2 sites 11 years apart, 7
    counterparties. A RELATIONSHIP, not a name.
  * **1683 Third Avenue Associates LLC** — `both_sides`: grantor AND recipient on
    one instrument (the self-to-self airspace split). A distinct play, visible on
    sight.
  * **301 East 71 Investors LLC** (Torkian Group) — bought twice in 3 weeks at
    **$251.75/sf**, 9 counterparties. A live assembler with a known price point.
  * **129 Front Hotel LLC → 110 Wall Street L.P. (Rudin) at $216.77/sf** — a comp
    where BOTH PARTIES ARE NAMED, from one instrument. That is the shape of the
    whole product: not an anonymous $/sf, a counterparty pair with a price.

`both_sides` and multi-site are the flags worth trading on — an actor on both
sides of the market is the interesting one.

**⚠ SCALE CAVEAT, to be repeated rather than forgotten:** n=14 documents. DEVR
alone is **1,201** and that is one type of one source. The patterns worth trading
on (repeat sellers, district assemblers, which lender follows which sponsor) need
the SWEEP, not the pilot — see [[feedback_bkrea_scale_failure]].

## ROLE REGISTRY — controlled vocabulary, built EARLY on purpose (`decoder/roles.py`)

Login: the role list will get wide (mortgagee, mortgagor, architect, engineer,
developer, owner, buyer, seller, attorney...). Then: *"we wont worry about it
until its sweeping. we still need to assure each decode of a document type is
perfect."* Agreed — this is SCAFFOLDING, not a build. It cost one file and
prevents one specific failure: the same attorney arriving as "counsel", "atty"
and "Esq." from three document types and splitting into three people.

**29 roles / 5 capacities — 16 OBSERVED, 13 EXPECTED (marked).**
Each role carries: `capacity` (principal | financial | professional |
governmental | fiduciary), `counterpart` (roles come in PAIRS — one observation
implies a second party to look for), `sources` (which doc type + block states it,
so a missing role says which document to PULL), and `reach` (how strongly it
identifies a human).

**`reach` is the useful axis:** `licensed_individual` (architect, engineer,
notary — a LICENCE NUMBER is the strongest identification in the system) >
`individual` (owner, developer, attorney, officer, managing agent) > `firm`
(surveyor) > `entity` > `agency`.

`ALIASES` maps what documents actually print onto canonical keys
(transferor→grantor_of_rights, counsel→attorney, Clerk of Session→officer,
lender→mortgagee). **Role is a property of the OBSERVATION, never of the
entity** — an entity holds many roles over time, which is the whole point.

## Login's ordering, to hold to

*"we still need to assure each decode of a document type is perfect, but when it
all pieces together it will be extremely efficient."* So: **per-type decode
correctness FIRST, cross-type folding second.** The registries (roles,
id_strength) and the design docs (SIGNATURE_LADDER, ENRICHMENT, PARCEL_LIFECYCLE)
are deliberately cheap scaffolding that make the fold cheap later — they are NOT
permission to start folding now.

## metes.py bug EIGHT + a THIRD bearing form (doc 2014070300770002, FiDi)

8. **⚠ UNICODE VULGAR FRACTIONS were DROPPED SILENTLY.** "117 feet ¼ inch"
   returned **117.0**. The typed "1/4" parsed; the single-character "¼" did not.
   Worst kind of miss — the number still looks reasonable. Fixed by normalising
   ¼ ½ ¾ ⅓ ⅔ ⅛ ⅜ ⅝ ⅞ before any pattern runs.

**A THIRD bearing form: the DEFLECTION ANGLE.** "THENCE southerly on a line which
forms an angle of 89 degrees 45 minutes 50 seconds on its westerly side with the
southerly side of Pine Street" — stated against the PREVIOUS line, not against
north. Now detected and marked `azimuth_basis="deflection_angle_approximated"`,
so a traverse is never read as precise when the cardinal fallback has rounded
89°45'50" to a flat 90°. Three forms now seen: cardinal words · quadrant bearings
· deflection angles.

**⭐ WHY THIS ONE DOES NOT CLOSE — and why that is the right answer.**
6.08 ft over a 310 ft perimeter. **FiDi's street grid is SKEWED**: Front Street
does not run true north, so "northerly along the easterly side of Front Street"
is the DOCUMENT'S OWN approximation. A cardinal-word description in a rotated
grid CANNOT close without the true street bearings. This is not a defect in the
instrument and not a bug in the parser — it is a limit of the description form,
and it is now stated on the record (`traverse_caveat`) rather than left as an
unexplained failure. Area 4,806.5 sf vs PLUTO 4,685 (+2.6%); NEITHER is trusted
for this lot.

**Consequence for the sweep:** rectilinear-grid boroughs traverse cleanly;
skewed-grid areas (FiDi, parts of Brooklyn/Queens laid to old road lines) will
systematically not close on cardinal-word descriptions. Expect it, flag it, and
do not chase it — the fix is true street bearings, not a better parser.

**Descriptions 21/21 verbatim, 10/14 documents complete.** Four remain:
2010102601040006, 2017053000419005, 2021070601644010, 2026012000388002.

## ⛔ ACRIS ACCESS DENIED 2026-08-05 — bandwidth notice hit. STOP, do not work around.

The image endpoint stopped serving TIFFs and began returning a **200 with an HTML
page, byte-identical (25,103 b) for every document and page**:

  *"NOTICE — Further access to ACRIS is denied. This can be due to multiple
   reasons such as detection of automated scripts/robots that are capturing data
   from the website or having exceeded the bandwidth limits we have established
   to ensure that all users of the ACRIS system experience high performance."*

**Stopped immediately. Did not retry, rotate, or work around it** — the standing
constraint on this project, and correct regardless.

**⚠ IT LOOKED LIKE SUCCESS.** `scan()` skipped any non-TIFF response without a
word, so a refusal was indistinguishable from "this document has no more pages" —
two scans returned an empty list and I read them as short documents. A block that
reads as a completed scan is exactly the self-validating failure this project
keeps meeting. `fetch_pages.py` now raises `AccessDenied` on the notice text and
prints NOT AN IMAGE for any other non-TIFF instead of skipping.

**⭐ THE TRADE-OFF I GOT WRONG.** The byte-size `--scan` heuristic optimises MY
reading cost (fetch a range cheaply, read only the light pages) — but it
MULTIPLIES the REQUEST cost, ~15 fetches to find one exhibit. ACRIS charges for
requests, not for my reading. So the technique that made the last four documents
cheap in context is what tripped the limit. **Next time: use the page numbers the
decode already recorded, fetch ONLY those, and accept a slower search rather than
a range scan.** Targeted fetching was the original design and it was right.

**Where it stopped:** 21/21 descriptions verbatim, **10/14 documents complete**.
Four still lack a description block — 2010102601040006, 2017053000419005,
2021070601644010, 2026012000388002 — and they need ACRIS images, so that work is
BLOCKED until access returns. Everything not needing images (Supabase, ZR, DCP,
DOF, DOB, Socrata) is unaffected.

## BACKWARD RE-CHECK RUN — every stored traverse re-walked (`recheck_traverses.py`)

Eight metes.py bugs were fixed during this session, so every area recorded
earlier was a claim made by an engine that no longer exists. Re-walked all 20
verbatim descriptions through the CURRENT parser:

**19 unchanged · 0 CHANGED · 4 traverse blocks backfilled.**

Zero movement, and the reason is worth knowing rather than assuming: each bug was
found AT THE MOMENT the affected description was transcribed, so every stored
value already had the fix. The re-check CONFIRMS that instead of trusting it —
which is the whole point, because "no change" is only meaningful when something
actually looked.

Backfilled 4 blocks transcribed before traverse blocks were stored at all:
2005101400455004 (2,146.7 and 1,362.0, both closing at 0.00) and
2026061500475003 (one unparseable, one non-closing at 100.0 ft — both correct,
the descriptions are defective as recorded).

**Made permanent:** `recheck_traverses.py` (run after ANY metes.py change — it
repairs nothing, it reports) and a new audit check "verbatim descriptions carry
a walked traverse" — because a description without a traverse has been
transcribed but never CHECKED, and the traverse is the only external test of the
transcription (a misread digit stops it closing).

⚠ And one more instance of the recurring shape: the re-check's own first version
tested for an AREA rather than for a traverse BLOCK, so a legitimately
unparseable description was reported as unchecked. A check that mis-defines its
own subject invents a gap. Fixed.

**Audit now 21 checks: 1 FAIL, 12 PASS, 8 INFO.** 20/20 walked — 17 close, 3 do
not, each with a stated reason.

## MIH IS A MAPPED, DATED, PARTIAL AREA — `nycmih` (279 areas), wired 2026-08-05

Not a flag on a lot. `services5.arcgis.com/.../nycmih/FeatureServer/0` — **279
areas**, each with **MIH_Option** (1 / 2 / 3, combinations), **DateAdopte**,
ZR_ULURPno, ProjectNam, Status, CD, and geometry. Three consequences:
  * **geometric** — a lot can be PARTLY in (1015400005 is 19.8% covered while
    its neighbour 1015400111 is 100%);
  * the **OPTION** sets the affordability required, hence which ZR 23-22 column
    applies — the affordable figures `zr_feed` already parses;
  * **DATED** — whether MIH applied to a 2014 instrument is a different question
    from whether it applies today.
`split_zones.mih_for_lot()` returns coverage fraction + option + adoption date.
**5 of the 22 pilot split lots are in a mapped MIH area.**
Confirms ZR 121-04: the two MSX lots sit in the Midtown South Mixed-Use Plan MIH
area (adopted 2025-08-14, Options 1/2/3).

## ⭐ A REZONING-CONTINGENT RECORDING, proved by dates (QN 12099, doc 2025102901095004)

    2025-10-12  acknowledgment taken (jurat, p33)
    2025-10-14  document date
    2025-10-29  Jamaica Neighborhood Plan MIH area ADOPTED
    2025-10-29  ZR 115-21 (Special Downtown Jamaica FAR) LAST AMENDED
    2025-10-30  DEVR RECORDED, \$1,685,980 for 55,000 sf
    2025-11-21  ~\$42.7M of mortgages recorded
**Executed BEFORE the rezoning, held, and recorded the DAY AFTER it landed.** The
parties were waiting for the adoption — the transfer is rezoning-contingent, and
the DATES prove it without reading a word of the contract. (Memory already
flagged "rezone-contingent quantities" as a watch item; this is the mechanism
visible from three sources at once: ACRIS dates, DCP adoption date, ZR amendment
date.)

**Method that generalises:** compare an instrument's execution date, its
recording date, and the adoption dates of any zoning change touching its lots.
A gap between EXECUTION and RECORDING that straddles an adoption is a strong
signal of a contingent deal — cheap to compute, and it needs no document text.

## SPECIAL DISTRICTS NOW APPLIED, not just recorded (2026-08-05)

⚠ The gap: `special_districts.py` existed for hours, correctly identified the
DJ override, and **was never wired into `close_split_far`** — so the baselines
still carried the un-superseded figure. A module that is right and unused is
worth exactly nothing, and nothing in the audit caught it because the audit
checked that a FAR existed, not WHICH TABLE it came from.

Now wired, and the supersession runs BEFORE any citywide lookup:
    **4097930089 commfar 4.1563 -> 4.7377** (C6-3 lifted 6.0 -> 8.0 by ZR 115-21,
    Special Downtown Jamaica) — the 14% understatement is corrected on the record.
    1008000033 / 1008000074 (MSX) and 1014460005 (TA) unchanged — correct, both
    verified against their FULL chapters as not modifying FAR.

Every baseline now carries `special_district`, `special_district_name` and
`special_district_status`. A district with `status == "unverified"` makes
`district_far` REFUSE rather than return a citywide figure — so an unchecked
special district can never silently supply a wrong number.

**The general lesson, which has now bitten twice this session** (party
observations sat unreduced; special districts sat unapplied): *a component that
is CORRECT but UNWIRED produces exactly the same output as one that does not
exist.* The audit must check the PATH, not just the presence of a value.

## ⭐ DOF's ALTERATION BOOK IS AN INDEPENDENT INDEX OF INSTRUMENTS (2026-08-05)

Ran `dof_lineage.history_batch()` over all **151 posted BBLs in 6 requests**
(one-at-a-time would have been ~300 — batching matters, learned the hard way).

**52/151 lots have a recorded alteration since 2008-05-20.** Change types: 52 Lot
Apportionment · 16 Merger · 15 Boundary Line · 14 REUC · 10 Condominium · 10
Reconfiguration · 2 Air-and-Subterranean. Lot actions: 95 Affected · **32 NEW** ·
8 Dropped · 4 renumbered. **32 lots in our own posting set were CREATED after
2008** — anything keyed on today's BBLs was silently missing them.

**46 distinct CRFNs cited by DOF as the authority — 46/46 resolve to an ACRIS
document, and ALL 46 are instruments our decodes never cited.** DEED 23 · MAPS 9 ·
CDEC 8 · CORRD 2 · ADEC 1 · DEVR 1 · LTPA 1 · DEEDO 1. So the alteration book is a
SECOND INDEX of paper affecting a parcel — the same lesson as the MTA/lot-51 case,
from the other direction: a parcel-keyed ACRIS pull does not see everything.

**Constellation rule: CDEC and MAPS ALWAYS come as a pair** — consecutive document
ids (…001 / …002), same recording day, DOF processing the condominium one day
later. Nine condominium events across our parcels, each with its pair, none in
the store. The one DEVR DOF cites IS already decoded (a clean consistency check).

**✅ CLOSED: why PLUTO has no row for MN 1908 lot 60.** DOF: Condominium recorded
2024-04-08 (CRFN 2024000086716/7). `eguu-7ie3`: **condo 3194, base 1019080060,
13 unit lots**. The lot became a CONDOMINIUM, so its value moved to the unit lots
and PLUTO carries no billing row. That is exactly why the Harlem PERIMETER
description (14,388.6 sf) reconciled as PLUTO lot 4 (4,297) + the DOCUMENT's lot
60 (10,092): only the instrument still states lot 60 as a whole parcel. Three
sources agree.

## ACRIS AT SCALE: INDEX vs IMAGES (the distinction that governs everything)

  * **INDEX — free, unlimited, no throttling.** `bnx9-e6tj` holds **17,036,716
    documents**; plus legals, parties, references, remarks. Type, date, parties,
    parcels, amount. NOT the constraint.
  * **IMAGES — the constrained resource.** Everything the index cannot give
    (legal descriptions, notices, signatures, jurats, certifications, operative
    clauses) needs a page image, and that endpoint is what blocked.

**Subscription (from the notice, verbatim): "contact the City Register (Ph:
212-487-6300) to learn about our subscription data services."** NOT VERIFIED:
price, whether images are included, format, licence, cadence — nyc.gov returned
403. **Questions for the call:** images or index only? delivery (bulk / SFTP /
raised API limit)? incremental feed for monitoring? commercial licence? cost.

**Scaling rules adopted:** index-first triage (decide WHICH documents deserve an
image) · targeted pages only, never range scans · never fetch a page twice · a
hard daily request budget so the limit is never approached · subscription for the
sweep, because 126 types × ~860k lots × ~30 pages is the wrong channel by three
orders of magnitude.

## ⭐ THE FREE INDEX ALONE GIVES A CITYWIDE DEVR MARKET MAP (2026-08-05)

Login flagged ACRIS bulk data as likely expensive. Measured what the FREE index
yields for the whole DEVR universe — **no images fetched**:

    1,201 documents, 2003-2026 (peak 87 in 2007; trough 16 in 2010; 68 in 2025)
    9,068 legal rows — MN 6,204 · BK 1,591 · QN 996 · BX 277
    **\$2,680,219,953** stated consideration across 596 priced documents
    median \$1,475,000 · max \$208,364,375
    605 (50%) record \$0 — and the Extell case proved \$0 can hide a real price

**What images add is ONE COLUMN: the QUANTITY in square feet.** Prices without sf
are not a \$/sf tape, and \$/sf is the comparable that gets traded on.

**⭐ THE COST ANSWER: that is ~1,500 pages, not millions.** 596 priced documents
× 2-3 pages each (the chart page + the definition page, both already known page
positions in a decoded document). At a polite rate with a daily cap that is a few
days of background work. **So the subscription is OPTIONAL for DEVR and only
becomes NECESSARY when widening to all 126 types citywide.** The single
highest-value dataset here — a real \$/sf air-rights price tape with named
counterparties — is reachable inside the free tier IF fetching is disciplined.

## What the free ACRIS index does and does NOT replace (measured, not assumed)

  * **`pwkr-dpni` References (8.7M rows) — the citation graph, PUBLISHED.** Only
    6 outbound + 4 INBOUND for our 14 documents, so it is SPARSE. But the 6
    outbound are all same-batch siblings, which **independently confirms the
    batch-constellation model**, and INBOUND references (documents citing OURS)
    are a view no amount of reading our own pages can produce. It carries
    formally-indexed references only — NOT prose citations like "Declaration of
    even date", which are 30 of our 44 unresolved.
  * **`8h5j-fqxa` Legals (22.7M) carries `air_rights`, `easement`, `partial_lot`,
    `subterranean_rights`.** Measured: air_rights on 3/245 of our rows, the other
    three flags ZERO. **Useful as a POSITIVE signal, worthless as a negative
    one** — never infer "no easement" from an empty flag.
  * **`9p4w-7npp` Remarks (5.7M): ZERO rows for all 14 of our documents.** Not a
    substitute for images.
  * **`636b-3b5g` Parties (46.5M): names + ADDRESSES**, typed. Entities only.

**Doctrine: index-first triage.** Let the free index decide WHICH documents earn
an image, then fetch only the pages a decode already located.

## ⛔ ACRIS SUBSCRIPTION PRICING — seen 2026-08-05, and the verdict is DON'T PAY

Login supplied DOF's "Index and Image Electronic Data Services" schedule.

    REAL PROPERTY **IMAGES**, all boroughs:  30d **\$8,670** · 90d \$26,010 ·
                                             180d \$52,020 · 365d **\$93,640**
    Manhattan images only:                   30d **\$1,820** · 365d \$19,660
    REAL PROPERTY **INDEX**, all boroughs:   30d \$2,110 · 365d **\$22,800**

**⚠ The INDEX tier sells data that is FREE.** `bnx9-e6tj` + legals + parties +
references + remarks are on NYC Open Data with a full API — 17,036,716 documents,
pulled all session at no cost. Login: *"I am not paying for free data."* Correct.
**Never buy the index tier.**

**Images are the only real product**, and \$93,640/yr is not defensible here.
The interesting line is the **30-day** tier, because what this project needs is a
ONE-TIME HARVEST, not a subscription — and Manhattan alone (\$1,820) covers
**6,204 of the 9,068 DEVR legal rows (68%)**.

**⭐ THE QUESTION THAT DECIDES IT, ahead of price: what does the subscription
DELIVER?** Bulk transfer / feed → \$1,820–\$8,670 once is cheap for a permanent
image archive. **Just credentials to the same rate-limited viewer → worth
nothing**, you would be paying to be throttled more politely. Ask that first on
212-487-6300.

**Measured alternative:** ~1,490 pages for the \$/sf tape, ~3,002 for every DEVR
document. At 400/day that is **3.7 and 7.5 days, \$0**. Recommendation: don't pay;
fetch politely over a week.

## `fetch_budget.py` — politeness ENFORCED, not intended

Built after the block. Hard daily ceiling (400), persisted across restarts ·
minimum interval · **a permanent (doc_id, page) ledger so a page is NEVER fetched
twice, across sessions, forever** · and a refusal BURNS the rest of the day's
budget, because retrying into a block is how a short limit becomes a long one.

`fetch_pages.py` is now budget-aware, and **`scan()` REFUSES to run unless
explicitly told `i_know_this_is_expensive=True`** — it is the range-fetch that
caused the block, ~15 requests to find one exhibit when the decode already
records the page. Kept only for documents decoded before pages were recorded.

The ledger is the quiet win: it makes an incremental day-by-day harvest practical
instead of one heroic run that gets cut off halfway.

## HOW TO FETCH ACRIS WITHOUT GETTING BLOCKED (settled 2026-08-05)

**What is known, not guessed:** ~100-150 image requests in ~2 hours, **in BURSTS
OF 13-19 AT ONE-SECOND INTERVALS**, produced the block. The threshold itself is
unknown and CANNOT be learned without tripping it, so assume it is low.

**The PATTERN is the likely tell, more than the volume.** Someone researching a
document opens it, reads with pauses, moves on. Fifteen requests a second apart
is a script and looks like one.

**Settings now enforced in `fetch_budget.py`:**
    DAILY_CAP = 100      MIN_INTERVAL_S = 25.0
    -> ~42 minutes of requests spread over a day
    -> 596 priced DEVR docs (~1,490 pages) ≈ 15 days
    -> all 1,201 DEVR docs (~3,002 pages)  ≈ 30 days
    -> the 4 currently blocked descriptions ≈ 10 pages, one afternoon
Raise ONLY after a clear week with no refusal, and RECORD the date it was raised
so a later block can be attributed to the change.

**`harvest.py`** makes it boring and repeatable: probe once → if refused, burn
the day and exit cleanly → else build the queue INDEX-FIRST (priced documents
first, because they are what turns a price list into a \$/sf tape) → fetch only
pages the ledger has not seen → stop at the cap. Re-running the same day is
harmless.

⚠ **Bug caught the moment it was built:** `access_ok()` reported "access ok
(text/html)" — it tested for the ABSENCE of one known refusal phrase instead of
for the PRESENCE of an image. A refusal page we had not seen before would have
read as success and the whole harvest would have run into a wall. **Require the
positive signal, never the absence of a negative one.** That is the same shape as
the silent-skip, the empty-scan and the wrong-field checks — four instances in
one session, and it is now the single most repeated failure mode in this project.

**Standing position on evasion, asked three times and answered the same way:**
no rotation, no proxying, no spoofing, no retry-into-block. Waiting for the reset
IS legitimate and `harvest.py` probes once per run to catch it. Evading the
detector is not — it is Login's own project rule, and a source that must be
tricked breaks silently, which is the exact failure this decoder exists to catch.

## SPINE REBUILT ON DOF'S PUBLISHED LINEAGE (2026-08-05)

The inferred spine was materially incomplete where DOF publishes the answer:
**4 of 8 dropped lots had NO successor; 12 of 31 created lots had no predecessor.**

Method: the DAB does not hand you a successor. **The TRANSACTION does** — within
one TRANS_NUM, what was Dropped and what was New/Affected are the two sides of
one map change. Querying by transaction rather than by our own BBLs returned
**186 lot-rows against 139**: 47 lot involvements were invisible when asking only
about our parcels. Second-index lesson again.

**22 dropped lots now have a PUBLISHED successor**, 35 spine rows upserted,
spine 243 -> 256 BBLs. Every link carries `valid_from` = **the date the map
actually changed**, so it resolves BY DATE, not merely "this became that".
  * **1014460002, 1014460003 -> 1014460001** (2026-05-15) — the Knickerbocker
    Developer Land consolidated; our postings name lots 1/2/3 as of Dec 2025 /
    Jan 2026, correctly, and now resolve forward.
  * **✅ 1015400003 -> 1015400002** (2017-10-26) — THE OPEN THREAD CLOSED: MN 1540
    lot 3 merged into lot 2 with lots 4, 45, 46, 47, 48, 49.
  * **1014290025 absorbed 6 lots** (21, 22, 23, 24, 121, 122) in ONE event — one
    row with six predecessors, because the merge was a single event, not six.
  * **3027220034 -> 3027220010** — independently CONFIRMS the earlier
    area-reconciliation inference (2004 doc lot10 7,500 + lot34 5,000 = today's
    lot10 12,500). DOF: "Deeds submitted 7/15/2008 to merge lots 10 & 34."

⚠ Schema notes for next time: `decoder_bbl_spine` PK is **(bbl, valid_from)**,
`valid_from` is NOT NULL, and there is no unique constraint on (bbl, source) — so
upsert on `bbl,valid_from` and GROUP predecessors into one row per event.

## SCALING SOURCES — the reframe (Login: "find creative ways not to get blocked")

**Lever 1 — requests per DOCUMENT, not requests per day.** One page per request
means a 30-page document costs 30 requests. If ACRIS exposes a whole-document
endpoint (multi-page TIFF, or the viewer's PDF/print export), that is **1 request
instead of 30** — same data, 30x fewer requests, and LESS load on them. Untested
(blocked); **first thing to probe when access returns.** If it works, 3,002 pages
becomes ~1,200 requests: **2 days at the conservative cap instead of 30.**

**Lever 2 — OFF-PEAK.** Their stated reason for limits is "to ensure all users of
the ACRIS system experience high performance". Running 2-5am directly serves that
reason and is likely to meet a higher effective ceiling. Politeness aligned with
their own justification, not against it.

**⭐ Lever 3 — STOP TREATING THIS AS AN ACRIS SCALING PROBLEM.** ACRIS images are
ONE bottleneck among ten sources; the other nine have no meaningful limits, and
**five are mapped but NOT BUILT**: DOB BIS+NOW, HPD, LPC, BSA, DOF
assessment/exemptions/sales. Proof: with images blocked all afternoon we still
produced the citywide DEVR market map, lineage for 151 lots, 46 resolved CRFNs,
MIH wiring, and the special-district correction.
**Run the nine in parallel and let ACRIS images trickle at 100/day.** That is a
faster path to a populated database than any image throughput would be.

## BULK PULLING — settings MEASURED, not assumed (`decoder/bulk.py`, 2026-08-05)

Login: *"see if we can increase batch and speed."* Benchmarked rather than guessed:

    SOCRATA \$limit    was 1,000  ->  **50,000 honoured**   (50x fewer requests)
                      the whole 1,201-row DEVR universe in ONE request, 0.5s
    SOCRATA in()      was 200 ids -> **500**                (2.5x)
                      1,000 ids = 25,133-char URL = **HTTP 414**
    CONCURRENCY       1 worker 27.2s -> **4 workers 4.4s (6.2x)**
                      8 workers 3.7s — diminishing, so 5 is the setting
    ARCGIS            maxRecordCount **1,000**, supportsPagination true ->
                      compute offsets from a count query, fetch pages CONCURRENTLY
    CROSS-SOURCE      Socrata + two ArcGIS orgs concurrently in 0.7s — independent
                      limits, so different SOURCES parallelise for free

Result: **entire DEVR universe + all 9,008 of its legals = 4 requests, 2.6s**
(was 9 sequential requests). ⚠ **NONE of this applies to ACRIS IMAGES** — that
endpoint is rate-limited by policy and is deliberately excluded. **Fast on the
open data, slow on the images.**

## ⭐ THE AIR-RIGHTS UNIVERSE, discovered from an INDEX FLAG (2026-08-05)

`8h5j-fqxa` has an `air_rights` column. Filtered across 22.7M rows **in 2.3s**:

    23,675 legal rows · **10,422 distinct parcels** · 12,479 documents
    span **1973..2026** (DEVR coverage only starts 2003)
    4,103 priced documents, median \$500,000, **total \$66,236,159,945**
    boroughs: MN 12,043 · QN 5,404 · BK 5,127 · BX 1,088 · SI 13

**The reframe: the flag sits mostly on FINANCING documents, not transfers.**
SAT 3,038 · MTGE 1,925 · ASST 1,702 · AGMT 1,034 · DEED 697 · TL&R 623 ·
**DEVR only 398** · SAGE 374 · SMIS 323 · AL&R 283.
Air rights are MORTGAGED, SATISFIED and ASSIGNED far more often than conveyed —
which is the debt throughline applied to the envelope, and it reaches back three
decades earlier than DEVR does.

⚠ **FLOOR, NOT A CENSUS.** The same flag appeared on only **3 of 245** of our own
legal rows, so it is inconsistently applied. Positive signal only — never infer
absence, and never quote 23,675 as complete.

## DOB BUILT (`decoder/dob.py`) — four datasets, 100% stage-mapped

Pulled CONCURRENTLY in **8.9s** for our 151 posted BBLs:
    BIS jobs `ic3t-wcy2`  1,237 rows · NOW jobs `w9ak-ipjd` 574 ·
    permits `ipu4-2q9a` 1,765 · CO `bs8b-p36w` 87
Stages: **operation 1,016 · pre_development 433 · construction 341 · abandoned 15
· cleared 6 — 1,811/1,811 (100%) mapped.**

## ⚠⚠ CORRECTION TO MEMORY: the DOB key format is PER DATASET, not per agency

The old note said "DOB does NOT pad the block ('1446' not '01446')". **Wrong for
three of four datasets.** Measured:
    ic3t-wcy2 BIS jobs  borough 'QUEENS'    block '01446' PADDED  lot '00009'
    w9ak-ipjd NOW jobs  borough 'Manhattan' block '441' UNPADDED  lot '16'
    ipu4-2q9a permits   borough 'BROOKLYN'  block '06861' PADDED  lot '00067'
    bs8b-p36w CO        borough 'Bronx'     block '05141' PADDED  lot '00035'
`block='1446'` returns ZERO against BIS; `'01446'` returns five. Four datasets,
THREE conventions, and borough is a NAME in upper OR title case.
**Never generalise a key format from one table to an agency.** `dob.SPEC` holds
the per-dataset spelling; `dob.keyparts(bbl, dataset)` builds it.

## ⭐ A CONTROL MUST TEST THE QUERY SHAPE, NOT A PARTICULAR PARCEL

First control used a fixed block (MN 1446) and reported **FAIL for the CO
dataset** — but that only meant "no CO on that block", not "wrong format". A
control keyed to a specific parcel MANUFACTURES failures exactly where it is
meant to prevent them. Now **self-calibrating**: sample a real row FROM THAT
DATASET, rebuild its key with our own SPEC, prove we find it again, and assert
the SPEC reproduces the spelling. All four PASS.

## ⭐ THREE-SOURCE CONFIRMATIONS from the DOB pull

  * **DOB job 121354550, type SI, MN 1540 lot 3, COMPLETED** — that is the EXACT
    PW1 number DOF's `Auth_for_Change` cited as authority for the 2012 airspace
    subdivision. DOF named the DOB job; DOB has it. Two agencies, one event.
  * **Two SC jobs on MN 1908 lot 60** — the Harlem condominium, now confirmed
    from a THIRD source (instrument perimeter → DOF alteration book → DOB SC).
  * **31 SI/SC filings** on our parcels — the DOB side of lot lineage, exactly as
    SOURCE_MAP_DOB predicted.

## ⭐ `cleared` IS A DISTINCT LIFECYCLE STAGE (found while mapping statuses)

"FULL DEMOLITION SIGNED-OFF" contains "SIGNED-OFF" and would have bucketed as
**operation** — making a demolished site look occupied. The work finished, but
what finished was REMOVAL: the improvement is gone and the site is LAND again.
In Login's lifecycle that is **the loop CLOSING** — an operating building
returning to pre-development — not a site entering operation. Matched FIRST,
before the generic "SIGNED OFF" rule. Stage vocabulary is now:
pre_development · construction · operation · **cleared** · abandoned.

## CONTACTS: DOB NOW names a LICENSED individual on 574/574 filings (100%)

`applicant_first_name` / `applicant_last_name` / `applicant_professional_title`
(PE, RA) / **`applicant_license`**. E.g. "DOUGLAS ACKERMAN — PE lic 071409".
A licence number is a VERIFIED individual — the strongest identification in the
system per `id_strength.py` — and this rung needs **no images at all**. It is the
cheapest route to the contact layer currently available.

## HPD BUILT (`decoder/hpd.py`) — and the CONTACT LADDER completed end to end

Pulled for our 151 posted BBLs in 18s: registrations 29 · **contacts 124** ·
violations 599 · CONH 0 · AEP 0. (The two zeros are TRUSTWORTHY absences — the
self-calibrating control passed first, so "no rows" means no rows.)

**⚠ THE JOIN GRAPH MATTERS MORE THAN THE PARCEL KEY.** Two datasets carry NO
borough/block/lot at all:
    BBL -> registrations (tesw-yqqr) --registrationid--> contacts (feu5-w2e2)
                    \--buildingid--> LL44 unit rents (9ay9-xkek)
Contacts are reachable ONLY through the registration. A parcel with no current
registration has no reachable contact — a fact about the BUILDING (under 3 units,
or non-compliant), not a gap in the pull.

**Key formats, again PER DATASET:** registrations + violations `boro` UPPER with
block/lot UNPADDED; CONH `borough` UPPER **plus a real `bbl` column**; **AEP has
NO block/lot columns at all**, only `bbl`. `hpd.SPEC` holds each.

**⭐ The control caught its own assumption.** v1 demanded a `block` column and
failed AEP — which has none. **A control must branch on what the dataset ACTUALLY
HAS**, or it tests its own assumption and manufactures a failure exactly where it
is meant to prevent one. (Third variant of this lesson today: fixed-parcel
control, absent-column control, and absence-of-a-negative-signal.)

## ⭐⭐ THE LADDER, COMPLETED — SPE to named human, two sources, ZERO images

    ACRIS   "301 East 71 Investors LLC (Torkian Group)"  recipient of rights,
            MN 1446 lots 1/2/3, docs 2026012000388003/4
    HPD     CorporateOwner  301 EAST 71 INVESTORS LLC     <- CONFIRMS THE JOIN
            HeadOfficer     **HERSEL TORKIAN**            1650 Broadway
            Agent           **HERSEL TORKIAN**            1650 Broadway
            **Shareholder** **HERSEL TORKIAN**            1650 Broadway
            Officer         **BEHROOZ TORKIAN**           1650 Broadway
            SiteManager     ANNIE XIAO

Not a fuzzy name match — **HPD's CorporateOwner field carries the IDENTICAL entity
name ACRIS recorded**, so the two sources agree on the entity and HPD supplies the
humans behind it: two named principals, a site manager, and a mailing address.

**parcel -> document -> role -> entity -> name -> real role -> mailing address**,
every link citing a public source, **no document images at all**. The only rung
still missing is PHONE/EMAIL = DOB PW1 §26 (unbuilt, reachable).

And the role is **Shareholder** — a CO-OP, the structure ACRIS records no deed
for. These people are invisible from ACRIS alone. This is the blind spot closing.

Contacts on our parcels: CorporateOwner 26 · Agent 26 · HeadOfficer 26 ·
SiteManager 24 · Officer 12 · **Shareholder 10**. 98/124 name an individual;
100/124 carry a business address.

## LPC BUILT (`decoder/lpc.py`) — and a TRUE absence, proved

Result on our 151 posted BBLs: **0 designated · 0 calendared · 0 LPC permits ·
0 violations · 0 complaints.** None of the pilot parcels is landmark-regulated.
That is a TRUSTWORTHY absence: all five self-calibrating controls passed first,
and each dataset returns rows for other parcels.

⚠ **A FIFTH borough spelling appears here** — `gpmc-yuvp` uses TWO-LETTER codes
(`'BK'`), which no other agency in this project uses. Five LPC datasets, four
conventions:
    gpmc-yuvp buildings   borough **'BK'** two-letter   + real `bbl` column
    ncre-qhxs desig/cal   `boroughid` numeric           + real `bbl` column
    dpm2-m9mq permits     borough 'Brooklyn' title      no bbl
    wycc-5aqt violations  **boro** 'BROOKLYN' upper     no bbl
    ck4n-5h6x complaints  borough 'Brooklyn' title      no bbl

**⭐ NEW FIRST RULE FOR ADDING A SOURCE: prefer the `bbl` column wherever it
exists.** It is unambiguous and skips the borough-spelling problem entirely.
Across DOB/HPD/LPC there are now **five** borough spellings (UPPER, Title,
numeric, two-letter, and a `bbl` column) and both padded and unpadded blocks.

## ⚠ A NO-OP FILTER — caught only by an INVARIANT, not by a check

`rows_for` ended `... in wanted or True`, which makes the whole condition a
no-op: **block-level rows were returned as if they were lot-level.** It surfaced
as a CONTRADICTION — 0 designated buildings but 35 LPC permits — and LPC permits
cannot exist without a designation, so the invariant exposed it.

**On a dataset with no such invariant it would simply have been wrong, silently.**
Strict/loose now measured side by side: permits 0 on our LOTS vs 35 on our
BLOCKS; violations 0 vs 1; complaints 0 vs 1.

**The lesson worth keeping: a filter that always passes looks identical to a
filter that works.** Test filters by asserting the strict result is a SUBSET of
the loose one and that the two differ — an equal count means the filter did
nothing.

## ⚠⚠ SEVENTH INSTANCE: a \$limit that SILENTLY TRUNCATED (`bulk.py`, same day)

`bulk.socrata()` defaulted to `\$limit=50000` and returned **exactly 50,000 rows
for a dataset holding 62,306**. A result whose length EQUALS the limit is
indistinguishable from a complete one — and this was in the module built
specifically to make bulk pulling safe.

Fixed by AUTO-PAGINATION, not a bigger number: `socrata()` now walks `\$offset`
until a page comes back short, so **no caller can under-read by forgetting a
limit**. An explicit `limit` is still honoured but sets `socrata.truncated`, so a
deliberate sample can never be mistaken for a census. Verified: declared 62,306,
returned 62,306.

**The seven instances of ONE failure shape, all found 2026-08-05:**
  1. scanner skipped non-image responses silently
  2. coverage check read the wrong nesting level -> "0 of 15"
  3. re-check tested for an AREA instead of a traverse BLOCK
  4. `access_ok()` tested for the ABSENCE of a refusal phrase, not the PRESENCE
     of an image
  5. DOB control keyed to a FIXED PARCEL -> manufactured a failure
  6. HPD/LPC control demanded a column the dataset does not have
  7. `\$limit` equal to the row count -> truncation that looks like completeness
**Require the POSITIVE signal. Never infer success from the absence of a known
negative, and never trust a count that equals your own cap.**

## BSA — the dirtiest parcel keys met so far (`f72e-3i4c`, 62,306 rows)

Datasets: `yvxd-uipr` applications status (10,805) · `f72e-3i4c` action portal
(62,306, BBL+BIN) · `855v-w7mc` pre-application meetings (75, has `applicant`)
· `99rv-74dm` decisions map (0 columns — a blob asset, not queryable).

**Measured quality on the full 62,306:**
    bbl    57% well-formed · **43% missing/placeholder (including literal '0')**
    block  80% single · 18% missing/'NONE' · **1.2% LISTS** ('00344,00347',
           '00203#00208') · 0.3% ranges
    lot    62% single · 18% missing · **15% LISTS** · 3.5% RANGES ('16-20,42,43')
    of rows with BOTH a well-formed bbl and a numeric block, **93% agree** (7% do not)

**⚠ CORRECTION to my own earlier statement:** a 1,000-row sample suggested 41%
disagreement; measured across all 62,306 it is **7%**. The small sample compared
the bbl's LOT against a lot LIST, which is not the same test. Sample-scale claims
about data quality must be re-measured at full scale before they are recorded.

**⚠ AND A CORRECTION TO THE LPC RULE ("prefer the bbl column"):** here the bbl
column is missing 43% of the time and disagrees with block/lot 7% of the time.
**Revised rule: prefer the bbl column, but VERIFY it against block/lot before
trusting it, and treat a lot/block value as a possible LIST OR RANGE, never as a
scalar.** A BSA grant routinely covers many lots — keying by bbl alone silently
drops the rest of the grant.

## DOF VALUE AXIS BUILT (`decoder/dof_value.py`) — the last mapped source

All five controls PASS. On our 151 BBLs in 1.2s: **assessment change 5,535 ·
exemptions 250 · abatements 240 · sales 32 · tax-lien-sale 19.**

**`parid` IS A BBL** — verified 799/800 sampled rows of `muvi-b6kx` decode to the
same boro/block/lot the row carries separately. That is the **SIXTH parcel-key
form**: BBL string · boro/block/lot (FIVE borough spellings) · registrationid ·
buildingid · BIN · parid.
Keys: `a5nd-6mit`/`muvi-b6kx`/`rgyu-ii48` parid · `w2pb-icbu` bbl · `9rz4-mjek`
borough NUMERIC + block/lot · **`rgy2-tti8` assessment roll returns HTTP 403** —
not openly queryable, needs another route.

## ⭐⭐ CAPSTONE: A COMPLETE PARCEL LIFESPAN, 96 EVENTS, FIVE SOURCES

MN block 1446 lots 1/2/3/151 — assembled from ACRIS + DOF sales + DOF alteration
book + DOB + HPD, and it reads as one story:

    2001-2019   routine A2/A3 alterations                  OPERATION
    2024-09-10  **\$25,000,000** — lots 1, 2, 3 bought together
    2025-01-13  Full Demolition filed
    2025-03-13  Full Demolition signed off                 **CLEARED**
    2025-06-03  **\$4,525,000** — adjacent lot 151 acquired
    2025-12-18  ACRIS: DBMJ + SZ 1390.5 Second Ave grant rights to
                301 East 71 Investors (Torkian Group)      6,554 sf / \$1,650,000
    2026-01-09  Declaration creates the zoning lot; **East West Bank consents as
                mortgagee**; second rights transfer (quantity never stated)
    2026-03..06 **New Building job M01361353**, filings S1-S9  PRE-DEVELOPMENT
    2026-05-15  DOF merges lots 2 and 3 into lot 1
    current     HPD: HERSEL TORKIAN, BEHROOZ TORKIAN, ANNIE XIAO

**operation -> sale -> demolition -> cleared -> assemblage -> air rights ->
zoning lot -> financing -> new building -> lot merger.** Every stage of
[[PARCEL_LIFECYCLE]], evidenced and dated, each line citing its source.

It validates three of today's own additions: the **`cleared`** stage exists in the
wild; the **lot merger** DOF published is the one the ACRIS postings needed; and
**job M01361353** is the ZD1 identified hours earlier as holding the Knickerbocker
floor area.

## ⚠ A SEVENTH FORMAT TRAP — DATES, and it corrupts TIMELINES not joins

DOB BIS returns **"01/03/2020" (MM/DD/YYYY)**; DOB NOW, DOF and ACRIS return ISO;
ArcGIS returns **epoch milliseconds**. String-sorting a mixed list interleaves
them wrongly — "01/03/2020" sorts BEFORE "2024-09-10" because "0" < "2" — so a
parcel history reads out of order while every individual row is correct. My own
capstone timeline printed wrong on the first run.
`keys.iso_date()` now normalises ISO / MM-DD-YYYY / epoch-ms / datetimes, and
returns **None rather than guessing** so an unparseable date sorts as unknown
instead of year zero.

## ALL NINE SOURCES WIRED INTO THE AUDIT (`decoder/sources.py`, 2026-08-05)

"Pullable" is not "verified". **Twice this session a component was CORRECT and
UNWIRED and produced exactly the same output as one that did not exist** — party
observations sat in raw_facts unreduced; the special-district override sat
computed but unapplied while baselines carried the wrong figure. Neither was
caught, because the audit checked that a VALUE existed, not that the PATH ran.

`sources.check_all()` re-runs **19 self-calibrating controls** every audit:
DOB ×4 · HPD ×4 · LPC ×4 · DOF value ×5 · DOF alteration book · Zoning Resolution.
**19/19 reachable.** Wired into `audit.py` as its own check.

**Three outcomes, never two — and the middle one is the point:**
    reachable   the control passed; the query shape works TODAY
    empty       the query works and returns nothing FOR OUR PARCELS. A finding
                about the parcels (LPC is legitimately empty — none of the pilot
                lots is landmark-regulated), not about the pull.
    BROKEN      schema drift, renamed column, withdrawn dataset. **A broken
                source looks EXACTLY like an empty one**, so it is reported
                separately and can never pass as "no data for our parcels".
The check also guards itself: if `sources.check_all()` raises, the audit reports
FAIL naming the exception rather than skipping the check.

**AUDIT NOW: 22 checks — 1 FAIL · 13 PASS · 8 INFO.** The single FAIL remains the
four ACRIS-image-blocked descriptions (2010102601040006, 2017053000419005,
2021070601644010, 2026012000388002) — ~10 pages, one afternoon at 100/day
whenever access returns.

## OVERNIGHT AUTOMATION SET UP 2026-08-05 (Login asleep, reads at 5am)

Two scheduled tasks, stored under `C:\Users\smile\.claude\scheduled-tasks\`:

  * **`acris-image-harvest`** — daily 07:32. Probes ACRIS ONCE via `harvest.py`;
    if refused, burns the day's budget and stops (never retries, never evades).
    If access IS back, targeted-fetches the four blocked documents
    (2010102601040006, 2017053000419005, 2021070601644010, 2026012000388002),
    transcribes verbatim per the contract, deletes the images.
  * **`decoder-overnight-practice`** — hourly 23:17 through 04:17. Orient on
    memory -> prove the floor (`selftest.py` 44/44, `audit.py`) -> pick ONE item
    (adversarial testing, cross-source contradictions, unresolved citations, MIH,
    the Knickerbocker quantity) -> record findings INCLUDING mistakes.

! Scheduled tasks only fire while the app is OPEN. If closed they run on next
launch. Recurring cron tasks also expire after 7 days.

! What actually persists between runs is MEMORY AND CODE, not "training". Each
run starts with no recollection of any conversation. The ratchet is: read memory
-> do work -> write findings back. That is why this file is written traps-first,
with what each one guards.

## `selftest.py` — 44 assertions, the FLOOR (2026-08-05)

Every trap this project has met is now an assertion, each recording WHAT IT
GUARDS (a test whose purpose is forgotten is the first one deleted). Groups:
keys 13 - dates 7 - parse_distance 14 - parse_bearing 6 - traverse 4.
Needs no ACRIS images, runs in seconds. Run it after ANY change.

## ! BUG FOUND BY THE BATTERY: overlapping LOT-KIND ranges

`is_unit_lot` used `lot >= 1001` to mean "condominium unit lot" — but DOF's
numbering puts several kinds above 1000:
    1-999 ground - 1001-6999 CONDO UNIT - 7501-7599 condo BILLING -
    8000-8999 REUC - 9000-9999 AIR / subterranean
So an AIR LOT satisfied `is_unit_lot` and would have been collapsed to a
condominium's billing lot — a wrong parent, silently. `keys.lot_kind()` now
separates all five and `audit.py` uses it instead of its own inline `>= 1001`.
Harmless TODAY (82 = 82, no air lot posted yet) but a decoded document already
names 1015409003 — a landmine, not a non-issue.

## MISSION RESTATED BY LOGIN 2026-08-05 (and I had drifted)

*"The idea is to understand the ENCUMBRANCES and ENVELOPE related documents from
ACRIS. However, other sources support and resolve the narrative more than just
development rights alone. It is all about moving through the documents to
understand how they work and interact and build the parcel from BIRTH TO PRESENT."*

So: the subject is the ACRIS **ENVELOPE + ENCUMBER FAMILIES**, not DEVR alone.
DEVR was the entry point. The other nine sources RESOLVE THE NARRATIVE — date a
map change, name the instrument behind it, supply a stage, identify a party —
they are not the subject. I had drifted toward breadth (nine sources) when the
work is DEPTH across the document families. Overnight task re-pointed.

## `timeline.py` — the product, made repeatable

`python timeline.py <bbl>` assembles one parcel from ACRIS + DOF map + DOF sales
+ DOB (+ HPD), every row citing its source and document. It FOLLOWS LINEAGE
(successors/predecessors, so a history does not stop where a BBL stops),
NORMALISES DATES BEFORE SORTING via `keys.iso_date` (the ad-hoc first version
printed out of order because BIS is MM/DD/YYYY and ArcGIS is epoch-ms), and runs
a `contradictions()` pass that reports SUSPICIONS not verdicts.

## ! THE CONSTELLATION GAP — I decoded 2 of 4 documents and thought the deal was understood

Pulled EVERY ACRIS document for MN 1446 lot 151 from the free index:
**24 instruments spanning 1972..2026.** Types: MTGE 5, DEED 3, SAT 3, ASST 3,
AGMT 2, ZONE 1, SMIS 1, DECL 1, DEVR 1, EASE 1, AL&R 1, RPTT&RET 1, PAT 1.

    2026-01-20 batch = FOUR documents recorded together:
        SMIS 2026012000388001   NOT DECODED
        DECL 2026012000388002   decoded
        DEVR 2026012000388004   decoded   $1,650,000
        EASE 2026012000388005   NOT DECODED
    2026-05-12  ZONE 2026050401026001     NOT DECODED

An EASE in an envelope batch is precisely the shape already flagged in this
project (a $24m easement ACTING as a ZLDA, recorded as EASE). The ZONE four
months later is the zoning-lot certification. **Decoding the DEVR and calling the
deal understood was wrong** — the family is the unit of analysis, not the type.

PRIORITY QUEUE when ACRIS images return: 2026012000388001 (SMIS),
2026012000388005 (EASE), 2026050401026001 (ZONE) — same parcel, same deal.

Also visible only from the full history: **2025-06-25 DEED $4,525,000 + MTGE
$2,585,000 + AL&R** — a 57% LTV acquisition three weeks before the alteration
filings began. And the record reaches **1972** (pre-2003 `FT_`-prefixed reel/page
document ids) — 30 years earlier than PLUTO, which is the real answer to "birth".

## THE SHAPE OF THE WHOLE JOB (measured citywide 2026-08-05) — and the triage that cracks it

ACRIS = **17,036,716 documents across 95 types**. The ENVELOPE + ENCUMBER family:

    AGMT      920,875   72.0%   CATCH-ALL
    SAGE      133,727   10.5%   CATCH-ALL
    SMIS       59,282    4.6%   CATCH-ALL
    CERT       55,648    4.4%
    ZONE       46,079    3.6%
    EASE       20,862    1.6%
    DECL       19,155    1.5%   CATCH-ALL
    MISC       13,470    1.1%   CATCH-ALL
    TERA 4,462 - CONS 1,577 - LDMK 1,226 - DEVR 1,201 - DEED,RC 474 - LIC 140 - AIRRIGHT 64
    ------------------------------------------------------------------
    family total 1,278,242 (7.5% of ACRIS) - of which CATCH-ALL 1,146,509 (90%)
    **DEVR is 1,201 = 0.1% of the family.** AGMT is 767x larger.

So the job was never "decode DEVR". **90% of the subject is types whose CODE TELLS
YOU NOTHING** — only the instrument says what it does. And 1.15m documents cannot
be opened at any fetch rate.

## ⭐⭐ THE TRIAGE: BATCH CO-OCCURRENCE CUTS THE CATCH-ALLS BY 99.5%

Unambiguous envelope ANCHORS (ZONE / DEVR / AIRRIGHT) = **47,344 documents in
43,581 recording batches**. Catch-alls sharing a batch with an anchor (same
13-digit doc-id prefix):

    SMIS 2,203 - SAGE 1,776 - AGMT 1,073 - DECL 857 - MISC 27  =  **5,936**
    5,936 of 1,146,509  =  **0.52%  ->  a 99.5% reduction**

**That is the scalability answer.** You cannot open 1,146,509 documents; you can
open 5,936. And the FREE INDEX does the triage before a single image is fetched —
which is also why the image rate limit stops being the binding constraint.

Corollary for the work queue: anchored catch-alls first, then anchored CERT/EASE,
then the long tail of unanchored catch-alls (which need a different signal —
document_amt, party, parcel, or `pwkr-dpni` references).

## ⚠ AND THE MISTAKE THIS EXPOSED

I decoded 14 DEVR documents and had been treating that as "the subject". DEVR is
**0.1%** of the family. Worse, on MN 1446 lot 151 I decoded 2 of the 4 documents
in a single recording batch (DEVR + DECL) and left the SMIS and EASE unread —
the EASE being exactly the shape this project already flagged (a $24m easement
ACTING as a ZLDA). **The recording batch is the unit of analysis, not the type.**

## ⚠⚠ LOGIN'S CORRECTION: "You can't do index. We are all about the DOCUMENT."

I drifted. After finding the 99.5% batch triage I started treating index-side
work as the answer. It is not. **The INDEX says a document exists; only the
DOCUMENT says what it does** — the founding principle of this project. Triage
decides WHAT to open. It never replaces opening.

## THE HONEST ARITHMETIC OF "EVERY DOCUMENT" (2026-08-05)

Observed page counts in this pilot: 19-98 per document, ~30 for a ZLDA, assume
~15 for a catch-all.

    DEVR only              1,201 docs =     36,030 pages
    anchored catch-alls    5,936 docs =     89,040 pages
    ALL envelope+encumber  1,278,242  = **19,173,630 pages**

    at 1,000 pages/day:  DEVR 36 days - anchored catch-alls 89 days -
                         **ALL: 19,174 days = 52 YEARS**

**Opening every envelope/encumbrance document through the per-page viewer
endpoint is NOT ACHIEVABLE.** Not with a higher rate, not with scheduling, not
with politeness. Say so plainly rather than implying otherwise.

**The only two real levers, and neither is scheduling:**

  1. **A WHOLE-DOCUMENT ENDPOINT.** If ACRIS serves a multi-page TIFF or a PDF
     export in ONE request instead of 15-30, the unit changes from PAGES to
     DOCUMENTS — a ~15x cut (all-family drops from 52 years to 3.5; anchored
     catch-alls from 89 days to 6). **UNTESTED because we are blocked. It is the
     single highest-value experiment available and must be tried ONCE the moment
     access returns.**
  2. **BULK DELIVERY.** This is what the City Register call is actually about —
     not the \$8,670, but whether the subscription is a FEED or merely credentials
     to the same throttled viewer. With bulk, 1.28m documents stops being a
     FETCHING problem and becomes a PROCESSING problem, which is solvable.

Achievable meanwhile: DEVR in weeks, anchored catch-alls in months. Real
progress, and enough to learn each type's ins and outs — but it is not "every
document", and Login should hear that now rather than in three months.

## Overnight task restructured accordingly

Step 0 is now: CAN WE OPEN DOCUMENTS RIGHT NOW? If yes, that IS the run — test
the whole-document lever once, then open documents in priority order (the four
blocked descriptions; then the UNREAD SIBLINGS of an already-decoded batch —
SMIS 2026012000388001, EASE 2026012000388005, ZONE 2026050401026001; then a
fresh instance of a type never opened, writing `docs/TYPE_<CODE>.md`).
If blocked: reroute to preparation that makes the next open-access run faster —
build the queue WITH PAGE NUMBERS so no request is wasted rediscovering them —
and say plainly in the notes that this was fallback work.

## WHERE THE EXTRACTION PROBLEM ACTUALLY IS (measured 2026-08-05)

**Ten of eleven source families are already extracted at full scale, free:**
ACRIS INDEX (17,036,716 docs, Socrata) - DOF tax map + alteration book (ArcGIS) -
DOF value/sales/exemptions (Socrata) - DCP zoning/MIH/nyzma (ArcGIS) - Zoning
Resolution (4,051 sections, parsed) - DOB structured (7.4M rows / 4 datasets) -
HPD - LPC - BSA.

**The problem is ACRIS DOCUMENT IMAGES**, ~1.28m envelope/encumbrance documents
behind a per-page, rate-limited viewer, plus a smaller DOB-PDF tail (PW1 s26).
So "decode all of ACRIS and every other source" has ONE bottleneck, not many.

## STORAGE IS NOT THE CONSTRAINT — measured from 71 real ACRIS TIFF pages

mean 36,113 b - median 27,216 b - min 1,582 - max 112,900.

    DEVR only            1,201 docs  ~30pp =    1.3 GB
    anchored catch-alls  5,936 docs  ~15pp =    3.2 GB
    envelope+encumber    1,278,242         =  0.3-1.4 TB
    ALL of ACRIS         17,036,716        =  2.3-18.5 TB

Hosting the SUBJECT is roughly **\$70-300/year** (B2 ~\$70/TB/yr, R2 ~\$180,
S3 ~\$280, Glacier Deep Archive ~\$12 — approximate, verify before committing).
**The cost is ACQUISITION, never storage.**

## \u2b50 FOIL — the legitimate bulk route, drafted 2026-08-05

`decoder/FOIL_REQUEST_DRAFT.md` (DRAFT, nothing sent). NY Public Officers Law
Art. 6; **\u00a787(1)(b)(iii) caps the fee for ELECTRONIC records at the ACTUAL COST OF
REPRODUCTION**, not a commercial licence price — against DOF's published \$8,670
(30-day) / \$93,640 (annual) image subscription. Request is scoped to the 15
envelope/encumbrance classes (~1.28m docs, 7.5% of ACRIS) with three pre-agreed
narrower fallbacks, asks for native TIFF in bulk plus a manifest mapping images
to document ids, and offers to supply media. Expect the agency to argue the
records are "available in another form" — worth testing anyway; it costs a letter.

Call 212-487-6300 in parallel with ONE question ahead of price: **bulk transfer,
or credentials to the same viewer?** Viewer-only is worthless at this scale.

## \u26a0 IF BULK ARRIVES, CHANGE THE ARCHITECTURE: store, do not delete

fetch \u2192 read \u2192 DELETE was correct while images were rate-limited and precious.
It becomes actively harmful once the corpus is owned. **This session fixed EIGHT
parser bugs** (leftmost-direction, bearing-minutes-as-feet, spelled-out numbers,
unicode fractions, street-number-as-distance, ...). With transient images only the
transcriptions already made could be re-checked — anything mis-read BEFORE a fix
stayed mis-read. With a stored corpus every parser improvement re-runs against
everything. That is the difference between a decoder that improves and one that
only improves going forward.

## ⭐ THE MEASURED TRIP POINT — reconstructed exactly (Login's observation)

Login: *"We were fine, but as soon as you tried bulk it blocked."* Correct, and
the sequence proves it:

    targeted  2026061500475003 p18,19              2   cum   2
    targeted  2012120600575002 p15,16              2         4
    targeted  2026012000388003 p36,37              2         6
    targeted  2026012000388004 p36,37,40           3         9
    targeted  2004110301042003 p14-18              5        14   <- all fine
    SCAN      2004110301042003 19-34              11        25
    SCAN      2021020901358005 13-30               8        33
    SCAN      2014091201052002 12-30              14        47
    SCAN      2025102901095004 25-42              18        65
    SCAN      2025102901095004 43-58               1        66
    SCAN      2017053000419005 36-54              12        78
    SCAN      2014070300770002 14-32              19        97
    SCAN      2026012000388002 33-48         -> **BLOCKED at ~98**

**14 targeted requests: no problem. 83 scan requests: block.
~97 total in ~90 minutes.**

**Consequence: DAILY_CAP was 100 — sitting EXACTLY on the number that got us
blocked. Lowered to 50** at 25s spacing (~21 min of activity per day). That is
1.9x under the observed trip point and spread across a window ~69x longer.
We do NOT know whether the limit is per-session, per-hour or per-day, and cannot
learn it without tripping it again, so assume the tightest reading. Raise only
after a clear week with no refusal, and RECORD the date of any change so a later
block can be attributed rather than guessed at.

**What this reprices:** the 4 blocked descriptions ~0.2 days, the lot-151 batch
siblings (SMIS + EASE + ZONE) ~0.9 days — both trivial. But the DEVR universe
becomes **721 days** at 50/day. Per-page trickling can finish the PILOT and never
the corpus, which is exactly why FOIL + the bulk question are the real path.

## 2026-08-13 scheduled run — THREE OF THE FOUR BLOCKED DESCRIPTIONS ARE CLOSED

Audit went **22 checks / 1 FAIL → 23 checks / 1 FAIL**, but the FAIL shrank from
four documents to one: **21 → 31 verbatim descriptions, 10/14 → 13/14 documents
complete.**

**⚠ THE TASK FILE IS STALE IN TWO PLACES AND BOTH MATTERED.**
 1. `python harvest.py 5` is no longer an access probe — `harvest.py` is now an
    image-SWEEPER (plan / --crop / --sweep) and prints a GC report. It cannot
    tell you whether ACRIS is serving. The standing "if it says ACCESS NOT
    AVAILABLE, stop" rule is therefore unreachable via that command.
 2. `harvest.known_pages(doc_id)` does not exist. Page numbers come from
    `docmaps.jsonl` / `acris_maps.jsonl` (via `amap`), not from harvest.
**Access is fine** ([[project_acris_bulk_acquisition]], 2026-08-12: ~8,000 pages,
zero refusals) and this run fetched 15 pages with no refusal.

**AND THREE OF THE FOUR "BLOCKED" DOCUMENTS WERE ALREADY ON DISK.**
`pages_out/2010102601040006` (110 png), `devr_pages/2017053000419005` (46 tif),
`devr_pages/2021070601644010` (52 tif). The audit had been reporting them as
image-blocked for a week while the images sat in the repo. **Check the disk
before the budget.** Only 2026012000388002 needed fetching (15 pages, targeted,
pp.33-47; images read then deleted).

Method that made it cheap: **Tesseract over every page first (208 pages in ~2
min, 10 procs, `OMP_THREAD_LIMIT=1`), grep for "BEGINNING at|thence", then READ
only the hit pages as images and transcribe.** OCR locates; it never transcribes
— the OCR of these very pages says "SQ feet" for 50 feet and "Lot 1!" for Lot 11.

### ⚠⚠ BUG #10 IN metes.py — AN ANGLE'S MINUTES AND SECONDS WEAR THE SAME MARKS AS FEET AND INCHES

    "...forms an interior angle of 89 degrees 40' 40" with the last
     mentioned courses 154.36 feet"
       -> parse_distance returned 43.333 ft   (40 feet 40 inches)
    "N 76 deg 19'05" E 100.00 feet"
       -> 19.417 ft                            (19 feet 5 inches)

The DMS group comes FIRST in the clause, so it won the search and the real
distance was never reached. Closure on the Jamaica Schedule A missed by **111
feet** — which is the only reason it was caught. **CLOSURE IS THE PARSER TEST,
again.** Nine earlier bug hunts missed this because every description in the
store until now spelled the angle out ("31 minutes 20 seconds"), which never
tripped it.
Fix: strip the DMS group (anchored on the degrees token, so a bare `27'2"` is
untouched) before any distance is read. **The fix re-created the bug once**:
`deg\.?|degrees?` is leftmost-first, so "89 degrees" matched only "89 deg" and
left "rees 40' 40"" for the feet pattern to eat. Longest alternative first.
`selftest.py` **51 → 56 assertions**, 5 of them this trap and its guards.
**Backfill over all 20 stored descriptions: 0 changed** — real, and stated as a
denominator rather than as reassurance.

### What each document gave up

**2010102601040006** (Extell/Chelsea ZLDA, MN 800) — 4 descriptions, pp.29-31.
Lot 49 walks to **15,639.2 sf against the 15,639 the 2010 chart itself uses**
(closure 0.06 ft) — the courses independently reproduce the document's own
figure, and that is the divergence PLUTO's 16,745 was flagged against.
Lots 53+55+56 = 4,066.7 + 2,468.8 + 2,468.8 = **9,004.3 vs the sealed survey's
9,015** (0.12%). The same four descriptions appear THREE times in the 110-page
bundle (pp.29-31, 33-34, 44-46, 80-83, 86-87) — a bundle repeats its exhibits
once per instrument inside it.

**2017053000419005** (Jamaica ZLDA, QN 9793) — 4 descriptions, pp.29-30, 44-45.
 * ⭐ **TWO DESCRIPTIONS IN ONE DOCUMENT ARE BOTH HEADED "LOT 78" AND THEY ARE
   DIFFERENT LAND.** Exhibit A p29 = 104.96 x 50.22 → **5,271.1 sf** (chart:
   5,271). Schedule A p44 = 192.65 x 154.36 → **29,600.1 sf**, which is lot 78 +
   lot 79 (5,271 + 24,397 = 29,668, 0.23%). The title-report schedule was never
   updated after the January 2017 subdivision. **Keying on the heading alone
   posts the parent's geometry to the child lot** — and this is the same lot 78
   whose subdivision already proved PLUTO lags. The document lags too, in a
   different exhibit of itself.
 * ⚠ **Schedule B (Lot 86, p45) is TRUNCATED AS RECORDED** — three courses, then
   it stops at "69 feet to a point;" with no return to the point of beginning.
   Rest of page blank, next page is Exhibit F. Transcribed as printed, closure
   192.74 ft = the whole missing course. Nothing reconstructed.
 * Exhibit F chart: lot 78 = 5,271 · lot 79 = 24,397 · lot 86 = 14,332 ·
   **total 44,000 at FAR 5 = 220,000 sf**.
 * ⚠ **CONTRACT TENSION worth settling:** EXTRACTION_CONTRACT says a truncated
   description gets `courses_verbatim: null`. But the audit counts a null as
   *summarised*, i.e. a decode failure, when the defect is in the RECORD. Kept
   the text (it IS verbatim — everything printed) + `truncated_as_recorded:
   true`, matching how the Williamsburg defective exhibits were already handled.

**2026012000388002** (Knickerbocker DECL, MN 1446) — Exhibit A p38, Exhibit C p47.
 * ⭐ **CROSS-DOCUMENT PROOF: Exhibit A walks to 10,029.8 sf at 0.00 ft closure —
   the identical figure sibling 2026012000388003 produced on a different day
   from a different page** (12 irregular courses). Two instruments, two
   independent transcriptions, one area.
 * Exhibit C (the whole expanded zoning lot) = **22,987.5 sf**, closure 0.00.
   Known members 10,029.8 + 2,037.5 + 3,750.0 + 1,022.0 = 16,839.3, leaving
   **6,148.2 sf for MTA lot 51 and any remainder** — recorded as arithmetic to
   check, not as an answer.
 * ⭐ **THE MTA/LOT 51 SWEEP FINDING IS CONFIRMED FROM THE PAGE.** pp.33-35 are
   the Authority's Acknowledgment and Consent: it consents to the 2026 merger
   *and* stipulates that none of the expansion documents will be recorded
   against the Lot 51 Land. So lot 51 is bound into the zoning lot and invisible
   to any parcel-keyed pull on lot 51 — **but it IS described**, as Parcel E of
   the title certification at p42, with state-plane coordinates
   (N 219,306.7406 E 995,802.4483).

**2021070601644010** (Greenpoint Landing, BK 2472/2494) — **NOT DONE, and that
is the remaining FAIL.** All 52 pages are already on disk and OCR-scanned; the
description block is pp.23-52 in six exhibits, inventoried page-exact in
`pending_descriptions`. ⚠ Exhibit A uses CURVES ("on a curve deflecting to the
right, with a radius of 5.00 feet"), so per the contract it transcribes in full
and the traverse reports `has_curve_unhandled` — **this document cannot produce
a closing area until curve handling exists.** Stated, not worked around.

### ⚠ NEW AUDIT CHECK: "descriptions located but not transcribed"

**The verbatim check can only see what the decode listed.** A decoder that
transcribes two of four descriptions and lists only those two scores 100%
complete — the check has no way to know about a description it was never told
about. Found while closing 2026012000388002, whose own exhibits are A and C but
whose Exhibit B carries a certification with further parcel descriptions.
So a decode that LOCATES a description it did not transcribe must record it
under `pending_descriptions` (what / which pages / why), and the new check
counts them. INFO, not FAIL — queued with page numbers is the opposite of lost —
but it can never read as clean. Currently 7 queued across 2 documents.

### SELECTION / MAPPING — the delta, and why the cheap monitor said "0 new"

Login's instruction this run: *"run the daily delta between what the selection
is and the current acris system ... a 20,000 document change requires you to
fetch and populate the new 20,000 document id endpoints into the selection
mapping"*, and *"it will take you forever to go over every single recorded doc
id — the important thing is identifying the delta between the live and recorded
mapping, then selecting the unrecorded ids to populate into the map"*.

    mapped locally (union of all 3 map files)   17,049,742
    live master rows                            17,065,090
    `map_delta.py --check` (FAST pass)          **0 new**

**The fast pass is keyed on `:updated_at > watermark`, and the watermark IS the
dataset's current max `:updated_at` (2026-08-10T13:35:44.257Z — Socrata has not
republished since).** So the cheap query answers "nothing arrived" while the
row count sits 15,348 above what is mapped. This is the exact failure the file's
own header warns about, one field over: a monitor that can only see forward
inherits every gap it already has and reports clean.
⚠ Some or all of that 15,348 may be DUPLICATE document_ids — MASTER carries
them, and `count(distinct document_id)` TIMES OUT on Socrata. **Only the
exhaustive set difference can say.** `map_delta.py --full` was launched
(`_map_full_20260813.log`); it pulls ids per doc_type and diffs against the
mapped union, then maps only the difference — which is precisely "diff, then
populate the unrecorded", not a walk over 17M recorded ids. It reached 80/95
types / 763,199 ids in ~30 min and the remaining 15 types are the giants (DEED
3.6M, MTGE 4.2M, SAT+ASST 4.8M), so it prints nothing more until it finishes.
Separately: `_map_todo.json` still holds **1,161 ids that were queued and never
mapped**, and three of this run's four target documents were in it.

### ⚠ AND A NUMBER I ALMOST RECORDED WRONG

`acris_maps.jsonl` has 17,001,755 lines against a claimed 17,049,742 mapped, and
I started to write that up as a 48k shortfall. It is not: `mapped_ids()` reads
**all three** map files and the other two hold the rest. The file's own docstring
says so. **A denominator from one file where the code unions three is the same
class of error as the ones this project keeps catching — check what the code
counts before reporting what the file holds.**

## ⭐ SELECTION LIVES IN SUPABASE — the daily job re-pointed (Login, 2026-08-13)

*"the selection map should be in supabase and the daily master row check + delta
determines what needs to update to the selection map in the database"* — so
`document_map` is the AUTHORITY and the local jsonl files are a working copy.
That re-points the daily routine, and it exposed three things `map_delta.py`
cannot do:

 1. **It diffs against LOCAL FILES.** `mapped_ids()` unions three jsonl files on
    disk and answers "is my laptop current". Measured 2026-08-13: **local
    17,049,742 mapped, `document_map` holding 4,563,156.** The file was
    complete-ish and the table was 12.5 million rows behind, and nothing in the
    daily run could see it.
 2. **Its fast pass keys on `:updated_at > watermark` and the watermark IS the
    dataset's current maximum**, so it reported **0 new** while live rows sat
    15,348 above what was mapped. **THE COUNT IS THE INDEPENDENT WITNESS** — it
    does not care when a row landed.
 3. **It writes to a local file.** New maps land in `docmaps.jsonl`, which
    `push_selection.py` does not even read (it reads `acris_maps.jsonl`), so a
    delta run could "succeed" and never reach the database at all.

**`decoder/selection_delta.py` (new)** — `python selection_delta.py [--map]`.
Live ACRIS vs `document_map`, per doc_type, then id-diff only where the counts
disagree, map the missing, upsert. End-to-end proven on AIRRIGHT the same hour:
**live 63 distinct · in map 0 · missing 63 → mapped → document_map 0 → 63.**

⚠ **62 of those 63 were ALREADY MAPPED LOCALLY.** The gap was a *database* gap,
not a mapping gap — which is exactly the distinction the old routine could not
draw, and exactly why the authority has to be the thing you measure.

⚠ **SUPABASE REFUSES POSTGREST AGGREGATES**: `select=doc_type,document_id.count()`
returns **400 PGRST123 "Use of aggregate functions is not allowed"**, so there is
no GROUP BY over this API. Per-type counts are 95 filtered `Prefer: count=exact`
HEAD-style requests instead — 0.27s each, ~25s for the lot, and each returns a
header not a result set. That is what makes count-localisation cheap enough to
run daily: a day with 20,000 new documents touches a handful of types, so only
those types get their ids pulled.

⚠ **A COUNT IS A DETECTOR, NOT A PROOF.** ACRIS master carries duplicate
document_ids (live rows 17,065,090 > distinct ids), so a small positive gap can
be pure duplication — AIRRIGHT is **64 rows / 63 distinct ids**, and the "64" in
this project's own document inventory is the row count. Types whose counts agree
are printed as *"no evidence of a gap"*, never as equal; `--full-ids` forces the
stronger statement. A count the map declines to return is `check_failed`, kept as
None, and id-diffed — never read as zero, which would manufacture a gap the size
of the whole type.

**Running 2026-08-13:** `push_selection.py` resumed (29% of the 3.85 GB file,
~1,390 rows/s, document_map 4.56M → climbing, ~2.5 h to go) and
`map_delta.py --full`. ⚠ **When the push finishes it will still be short**:
`push_selection` reads only `acris_maps.jsonl`, while the mapped union spans
three files — `docmaps.jsonl` + `census_maps.jsonl` hold ~48k documents that
must be pushed separately (`ACRIS_MAPS=docmaps.jsonl`, with the byte-offset
state file moved aside first, since the state is keyed to a single source).

### DELTA RESULT 2026-08-13 — THE LOCAL MAP IS CURRENT, AND THE 15,348 WAS ALL DUPLICATES

`map_delta.py --full` finished in **4,873 s (81 min)**:

    live master ROWS       17,065,090
    live DISTINCT ids      17,049,742   <- the exhaustive per-type pull
    mapped locally         17,049,742
    NEW TO MAP                      0   "map is current"

So the apparent 15,348-document gap was **100% duplicate document_ids in ACRIS
master** — the count-vs-distinct caution written into `selection_delta.py` an
hour earlier was the correct call, and the fast pass's "0 new" was right for the
wrong reason (it could not have seen a real gap either way).
**Keep both readings: the COUNT detects, the DISTINCT-ID DIFF decides.**
Cost of the honest answer: 81 minutes, once. Cost of the count check: 2 seconds.
That is exactly why the daily job counts first and only id-diffs where counts
disagree.

⚠ The gap that IS real is the DATABASE, not the map: `document_map` was at
4.56M against 17,049,742. That is a push backlog, not a mapping backlog, and no
amount of delta running would have found it — only measuring the authority does.

### `push_maps_tail.py` (new) — the other two map files

`push_selection.py` reads ONE source and resumes on a byte offset in one state
file, so it cannot be pointed at a second file while running. docmaps.jsonl
(69,729) + census_maps.jsonl (3,600) = **72,149 distinct ids**, pushed by a
separate driver.

⚠ **AN UPSERT CAN ERASE.** `amap` writes page geometry only — 68,549 of those
rows carry no `doc_type` and no `recorded`. `push_selection.row()` turns a
missing key into an explicit null and PostgREST `merge-duplicates` writes every
column in the payload, so pushing them over a document already loaded from
acris_maps.jsonl would **blank its doc_type**. A backfill that deletes
information looks exactly like a clean run. Rows are therefore grouped by which
fields they actually have and each group sent with only its own columns.

⚠ **AND A NULL doc_type IS NOT MERELY MISSING — IT IS UNCOUNTABLE.**
`selection_delta.py` reconciles per doc_type, so a null-typed row counts under
no type, never reads as present, and gets re-diffed every day forever. Worse
than a missing row, which at least gets fixed. Cured by filling the type from
`acris_ids.jsonl` in one offline pass: **68,445 filled, 104 still unknown**
(those push without the column, keeping whatever the table holds).

### ⚠⚠ THE VERIFIER KILLED THE RUN IT WAS VERIFYING (2026-08-13)

`push_maps_tail.py` died on **HTTP 500 — and the 500 was on the COUNT, not the
write.** 26,000 rows had already landed successfully; the run reported a
traceback and nothing else.

Cause: `supabase_sync.push()` takes an exact `count=exact` of the WHOLE TABLE
before and after its batches. That is fine for 360k fact rows. I then called
`push()` once per 1,000-row chunk, so **every chunk triggered a full-table
count** — and at ~5.5M rows and climbing (with `push_selection.py` writing
concurrently) Supabase began returning 500 on the count itself.

Three things worth keeping:
 * **A partial success that reports as a total failure is the same defect as a
   partial failure that reports as success** — already written into
   `_post`'s docstring in this very module, one function away, about a different
   failure. The rule was known and the shape still got through.
 * **Batch OUTSIDE a function that verifies INSIDE and you multiply the
   verification, not the work.** Count twice, not 17,000 times.
 * A count that cannot be taken is **UNKNOWN**, never 0, and never an exception
   that propagates. `safe_count()` now reports `check_failed` in words.
Also: the `held` figures printed during that run were rising ~5,000 per batch
from the CONCURRENT push_selection job — so the before/after subtraction was
never going to be a clean measure of what this job added. Two writers on one
table means the delta is not attributable; say so rather than printing it.
⚠ EXPECT `S.count()` TO GET WORSE, NOT BETTER, AS document_map GROWS TOWARD
17M. Anything that needs a row count at that scale should ask for one filtered
count per doc_type (0.27s each) rather than one exact count of everything.

### ⭐ WHY THE PUSH IS SLOW — MEASURED, AND THE FIX (2026-08-13)

Login asked whether ~3.5 h was the pull or Supabase. **It is Supabase ingest, and
it is per-REQUEST latency, not bandwidth.** Measured against the live table:

    serial batch  1,000    799 ms/req    1,251 rows/s   <- the old default
    serial batch  2,500  1,050 ms/req    2,381 rows/s
    serial batch  5,000  2,683 ms/req    1,864 rows/s   <- past the knee
    batch        10,000  HTTP 500                       <- refused outright
    conc 4 x batch 2,500                 3,193 rows/s   <- best observed
    conc 6 x batch 2,500                 2,067 rows/s   <- index contention

~85% of wall time was round-trip, so the levers are rows-per-request and
requests-in-flight, and BOTH have a knee. Defaults changed 1,000 serial ->
**2,500 x 4 concurrent**. For contrast the ACRIS side is not the problem at all:
Socrata served 17M ids in 81 minutes because it returns 50k rows per request,
while Supabase takes 2,500 per write against a growing ON CONFLICT index.
⚠ The rate is NOT constant: a region of the file whose documents are already in
the table runs ~6,000 rows/s (pure merges) and genuinely new rows settle near
1,800–3,200. Quote a range, and never extrapolate an ETA from the first minute.

### ⭐ PAUSE, DO NOT FAIL — and it was tested by accident within the hour

Login: *"i will lose connection so it should pause not fail"*. The old `send()`
tried 5 times over 31 seconds and then raised, which killed the process; a closed
lid or a router blip would have ended a 3-hour job.
Now: **unbounded retry on 5xx and transport errors**, backoff capped at a 60 s
poll, one log line per minute while waiting — and **a 4xx still stops instantly**,
because that is a schema/data bug that will fail identically forever and
retrying it turns a bug into a silent infinite loop.
**Proved the same hour**: the laptop slept, four in-flight writes died with
`URLError: EOF occurred in violation of protocol`, all four printed PAUSED and
then `...link back, chunk accepted after 1 retries`. The job never stopped.

⚠ **AND THE CHECKPOINT HAD TO CHANGE WITH THE CONCURRENCY.** With N writes in
flight they confirm out of order, so `f.tell()` runs ahead of the earliest
UNconfirmed chunk — checkpointing there would resume PAST rows that never
landed, which is the one way a resumable job silently loses data. Fixed by
sending in WAVES: every chunk in a wave must confirm before the offset advances,
making it a true low-water mark. Re-doing a wave costs nothing (idempotent
upsert); skipping one costs data you never learn about.

### ⚠⚠ A TUNED CONSTANT IS A MEASUREMENT OF ONE MOMENT (2026-08-13)

2,500 x 4 was **measured**, not guessed, and it was still wrong an hour later.
At ~5.7M rows it was the fastest configuration. At ~7M all four concurrent
writes began returning

    HTTP 500 {"code":"57014","message":"canceling statement due to statement timeout"}

because the ON CONFLICT merge against a bigger index no longer fits inside
Supabase's statement timeout. **The ceiling MOVES as the job does its own work.**
The pause-not-fail retry handled it (8 stalls, 8 recoveries) — but retrying the
SAME oversized statement is patience without learning, at ~30 s a stall, with the
frequency only going one way.

`push_selection.Gate` — AIMD on BATCH SIZE. A statement timeout halves the batch
(floor 250) and drops concurrency to 2; eight clean waves grow it back by 25%
(ceiling 2,500). Same shape as the ACRIS fetch gate, except this one is reacting
to work it is itself making heavier.

⚠ **57014 IS NOT A NETWORK ERROR AND MUST NOT BE TREATED AS ONE.** A dropped SSL
connection means *try again unchanged*; a statement timeout means *you asked for
too much*. **Identical HTTP 500 to the caller, opposite remedy** — and the only
way to tell them apart is to read the error body, which the old handler threw
away. The run summary now prints the timeout count and the final gate position,
with the note that a gate which never moved means the ceiling was never reached,
not that there isn't one.

### ⚠ AND I MISREAD MY OWN GATE'S THROUGHPUT (same session)

A 120-second sample taken **while the gate was climbing back from 312** read
**388 rows/s** and projected **6.9 hours**. A 180-second sample taken once it had
recovered to the 2,500 ceiling read **1,937 rows/s -> 1.3 hours**. Same job,
same minute-scale window, **5x apart**.

**A rate measured during recovery is not the rate.** An AIMD gate spends its life
oscillating; sampling it anywhere on the climb reports the climb, not the
steady state. This is the mirror of the earlier error in the same session
(quoting 6,000 rows/s from the first minute after a restart, when the file
region was all cheap merges). **Both directions of the same mistake, one hour
apart: never take a throughput reading from a transient, and always say which
part of the cycle a number came from.**
Settled behaviour: 12 statement-timeout stalls, 12 recoveries, no failures,
~1,900 rows/s average with the gate riding its 2,500 ceiling.

### ⚠⚠ THE CHECKPOINT WAS DESTROYED BY THE EVENT IT EXISTED TO SURVIVE (2026-08-13)

The Claude Code session restarted; the push process died with it — fine, that is
what the checkpoint is for. But `_push_selection_state.json` was left as
**39 BYTES OF NUL**. `STATE.write_text(...)` truncates, then writes, and the kill
landed between the two. Not empty, not obviously corrupt — just unreadable.
**A 3-hour job's entire resume point, gone, while the log still read 50.0%.**

Three fixes, all in `push_selection.py`:
 * `save_state()` — temp file, flush, **fsync**, `os.replace`. Atomic on NTFS and
   POSIX. A kill now leaves the OLD state or the NEW one, never a hole.
 * `load_state()` — an unreadable checkpoint **raises and says so**. Reading it as
   `{}` would silently restart 17M rows from zero and look like normal operation.
   That is the same "absence read as a value" shape as the 2026-08-05 seven.
 * The byte offset is now printed in the LOG on every checkpoint (`@1909628732`).
   When the state file died, the log's rounded "50.0%" was the only surviving
   clue — worth ±1.9 MB of ambiguity. Printing a number in two places is free.

**Recovery rule, and it has a direction:** resume DELIBERATELY EARLY. Re-sending
is an idempotent merge that costs seconds; skipping is data loss you never learn
about. Resumed at 49.5% against a log reading 50.0% — ~85,000 rows redone, and
that is the cheap side of the trade every time.

⚠ ALSO: launch long jobs with PowerShell `Start-Process ... -WindowStyle Hidden`,
not `nohup ... &` from the Bash tool — the latter dies with the session. But the
real protection is the checkpoint, not the launcher: any future session resumes
the push with plain `python push_selection.py`.

### ⭐ HOW TO LAUNCH A JOB THAT OUTLIVES THE AGENT (2026-08-13, learned by losing it 3x)

The selection push was killed **three times** by Claude Code session/turn
teardown. Two launchers do NOT escape the agent's process tree:
    nohup python x.py &                      (Bash tool)      -> dies
    Start-Process -WindowStyle Hidden        (PowerShell)     -> dies (~10 min)
What works: a **Windows Scheduled Task**, which runs under the Task Scheduler
service, outside that tree entirely.

⚠ `schtasks /Create /TR "<path>"` FAILED with Last Result **-2147024894
(0x80070002, "cannot find the file")** because the path contains spaces AND
parentheses ("Source Folder (Real Estate Data)") and /TR does not survive it.
Use the PowerShell cmdlets instead — they quote correctly and take a working
directory:
    $a = New-ScheduledTaskAction -Execute "cmd.exe" `
         -Argument "/c `"$dirun_push_selection.cmd`"" -WorkingDirectory $dir
    $s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
         -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) `
         -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval 1min
    Register-ScheduledTask -TaskName "acris-push-selection" -Action $a -Settings $s -Force
    Start-ScheduledTask -TaskName "acris-push-selection"
⚠ `-ExecutionTimeLimit ([TimeSpan]::Zero)` = no limit. The DEFAULT IS 3 DAYS and
would silently kill a long job — another cap that looks like a completion.

`decoder/run_push_selection.cmd` wraps it in a retry loop: the script resumes
from its atomic checkpoint, so the right answer to any death is simply to start
it again, and it exits 0 only when the file is fully read.

**Verified working:** resumed from `{"offset": 2226018273}` and carried on from
58.0% under the scheduler's own PID. This is the pattern for every long job in
this project — acquisition included, where the run is 35 days.

### ⚠⚠ THE PUSH HIT A REAL WALL AT ~14.3M ROWS — IT IS THE INSTANCE, NOT THE CLIENT

Stopped at **84.02% of the file (~14.3M of 17,049,742 rows)**. Not a tuning
problem any more:
  * the AIMD gate walked all the way DOWN to its floor (**batch 250 x conc 2**)
    and was **still** getting `57014 statement timeout` on every wave
  * no wave completed for ~5 minutes; the offset did not move
  * with ALL WRITES STOPPED for 2 minutes: a full-table exact count still fails
    after **70.9 s**, and an INDEXED count (`doc_type=eq.DEVR`) that ran in
    **0.27 s earlier in the day now takes 23.5 s** — an 87x degradation
So the instance is saturated (small compute tier + index maintenance/autovacuum
after ~10M inserts), and hammering it with retries makes recovery slower. Task
stopped deliberately; the atomic checkpoint holds at
`{"offset": 3237726662, "sent": 4448840}` and `python push_selection.py` resumes.

**PostgREST upsert is the wrong tool for a 17M-row bulk load and this is where
that becomes undeniable.** Per-statement `ON CONFLICT` against a growing index
gets slower exactly as the job gets closer to done — the failure arrives late,
when the sunk cost is highest. Three remedies, all on the DB side:
 1. **`COPY` into a staging table + one `INSERT ... ON CONFLICT`** — minutes,
    not hours. Needs the direct Postgres connection string (Supabase dashboard
    -> Settings -> Database); the env file holds only the REST service key, and
    `psql` is not on PATH.
 2. **Raise `statement_timeout`** on the role PostgREST uses. A config change to
    Login's database — ask first.
 3. **Larger compute tier.** Costs money; Login's call.
⚠ Whatever is chosen, the DAILY job is unaffected: `selection_delta.py --map`
writes only the day's new filings (thousands, not millions) and never needs a
full-table count — it uses per-doc_type filtered counts.

### ⚠ AND I FAILED MY OWN BACKWARD RE-CHECK, WITH A MEASURABLE COST

`count_rows()` in `push_selection.py` raised on failure and was called at
STARTUP. At ~14M rows it began timing out, so the exception escaped `main()`
before a single row was pushed — and the wrapper dutifully restarted the process
into the same crash. **Five restarts, zero progress, offset frozen at 84.0%.**
The retry loop meant to make the job unkillable instead made it loop forever on
a fatal startup check.

**I had already found and fixed this exact defect in `push_maps_tail.py` earlier
the same day, and written the note "a verifier that aborts the run it is
verifying".** [[feedback_confidence_backcheck]] says: when a new trap is found,
re-run it over every earlier entry. I wrote the lesson and skipped the sweep, and
it cost the run.
**A count is a DIAGNOSTIC. It must never be able to stop the work it describes —
and it degrades precisely as the table it counts grows, so it fails late.**

### ★ "DID SUPABASE REJECT THE REST?" — NO. NOTHING WAS EVER REJECTED.

Worth separating carefully, because the two look identical from the client:
  * **Rejection** = 4xx. The row is bad, it will fail forever, stop.
  * **`57014 canceling statement due to statement timeout`** = 500. The row is
    FINE; the instance ran out of TIME BUDGET under sustained load.
Proof, not inference: the very rows sitting just past the stall point were
posted by hand after a ~15 minute pause — **10, 50 and 250 rows all HTTP 200 in
0.3–0.7 s**, and verified present afterwards. Same rows, same key, same table.
The data was never the problem.

**The 84% is verified safe, positively.** 36 documents sampled from nine points
across the whole pushed region (0.1% to 99.95% of it) against the source file:
**36/36 present, 0 missing, 0 with mismatched page geometry.** And no partial
rows are possible — one POST is one `INSERT ... ON CONFLICT`, so a timed-out
statement rolls back whole; the wave checkpoint only advances on confirmation.

⚠ **A FULL `count=exact` NOW FAILS PERMANENTLY AND THAT IS NOT IL L HEALTH.**
Post-recovery: indexed count `doc_type=eq.DEVR` **0.4 s** (was 23.5 s while
saturated, 0.27 s originally) while the full-table count still 500s — but in
8.7 s rather than 70.9 s, i.e. it hits the timeout fast. A COUNT(*) over 14M+
rows simply exceeds the statement timeout and always will. Do not read that as
the instance being unwell; read the INDEXED count instead. This is exactly why
`selection_delta.py` reconciles per doc_type.

### ⚠ THE GATE COULD DEEPEN THE PROBLEM IT WAS SENSING

At the floor (250 x 2) halving does nothing, so the gate just kept retrying
every 2 s — **adding load to the instance that was already the bottleneck.**
Fixed: after 3 consecutive floor-level timeouts it **COOLS DOWN 5 minutes**.
Justified by measurement, not taste: 15 idle minutes took an indexed count from
23.5 s to 0.4 s and 250-row upserts from timing out to 0.7 s. THE INSTANCE
RECOVERS ON ITS OWN IF YOU LET IT.
Resumed 84.02% -> 84.16% at ~112 rows/s — real progress, but ~7 h for the last
2.7M rows. Sustained writes at this table size are simply beyond this tier, so
the honest recommendation stands: `COPY` + one `INSERT ... ON CONFLICT` via the
direct Postgres connection, or more compute.

### ⭐⭐ ROOT CAUSE NAMED BY SUPABASE ITSELF: **DISK IO BUDGET EXHAUSTION**

Supabase emailed Login mid-run: *"Your project is depleting its Disk IO
Budget... your project is utilizing more Disk IO than what your compute add-on
can effectively manage."* That is the mechanism behind **every** symptom measured
today, and it explains the one thing that looked strange — recovery while idle.

Smaller compute add-ons have a BASELINE disk throughput plus a **burst budget
that accrues while under baseline and drains while over it.** Drain it and you
are hard-capped at baseline. Map that onto the day:

    3,193 rows/s early                     bursting on a full budget
    ~1,900 rows/s mid-run                   budget draining
    250-row upserts timing out              budget EXHAUSTED, baseline only
    indexed count 0.27s -> 23.5s            same cause, read side
    15 min idle -> 0.4s, 250 rows in 0.7s   budget partially REFILLED
    resume -> degraded again in minutes     refill spent immediately
    ~112 rows/s sustained                   THIS IS BASELINE

⚠ **SO "WAIT AND RESUME" IS NOT A FIX** — it buys one short burst per idle
period and the remaining 2.7M rows will drain it again. I had ranked it as a
viable option; it is not. The instance was never unhealthy and the rows were
never rejected: **we were spending an IO allowance we did not know existed.**

**The levers, cheapest first — all reduce IO PER ROW rather than asking for
patience:**
 1. **DROP THE SECONDARY INDEXES FOR THE LOAD, REBUILD AFTER.** Every upsert
    currently maintains the primary key AND `document_map_type` AND the partial
    `document_map_noimg`. Three index writes per row across ~17M rows is a large
    share of the disk IO, and one rebuild at the end is far cheaper than
    incremental maintenance. Free and reversible.
 2. **`COPY` + one `INSERT ... ON CONFLICT`** via the direct Postgres connection.
    Bulk load, one statement, vastly less per-row overhead than 17M REST upserts.
 3. **Bigger compute add-on** — raises the baseline itself. Costs money.

⚠ AND THE GENERAL LESSON, which outlives this table: **a hosted database has a
throughput ALLOWANCE, not just a rate.** Everything I measured early
(2,500 x 4 = 3,193 rows/s) was measured ON BORROWED BURST and was never the
sustainable rate. **A benchmark taken while a budget is full is a measurement of
the budget, not of the system.** Same shape as the two throughput misreadings
earlier the same day — three instances now of quoting a transient as steady
state.
⚠ Push PAUSED deliberately at **84.16%** (`offset 3243080095`) so it stops
consuming the budget while Login decides. Nothing lost; `python
push_selection.py` resumes.

### ⚠ A SILENT LOG READ AS A DEAD JOB — IT WAS PYTHON'S STDOUT BUFFER

The push ran for 8 minutes without writing one line to its log while the atomic
checkpoint advanced the whole time. **Python BLOCK-buffers stdout when it is
redirected to a file**, so the startup lines and every `print` without
`flush=True` sat unwritten. I nearly restarted a working job because its log had
not been touched since before it started.
Fixes: `python -u` in the wrapper, and the standing rule —
**READ `_push_selection_state.json`, NOT THE LOG, to answer "is it alive".**
The checkpoint is written atomically per wave and cannot lie about progress; the
log can be minutes stale by construction.

### ⚠⚠ THE WRAPPER REPORTED "push completed cleanly" AT 84.2%

`if errorlevel 1` in cmd. A Ctrl+C kill exits **0xC000013A**, which cmd compares
as a NEGATIVE number, so `errorlevel 1` was FALSE and a KILLED process printed
**"[wrapper] push completed cleanly"** with 2.7M rows still unsent.
Replaced with a POSITIVE marker: `push_selection.py` writes
`_push_selection_DONE` **only** after its read loop reaches EOF (and never under
`--limit`, which also exits the loop). The wrapper tests for that file.
This is the project's oldest failure shape — success inferred from the absence of
a known negative — reappearing in three lines of batch script.

### ⚠ AND THE JOB KEPT BEING Ctrl+C'd BY MY OWN TOOL CALLS

Task Scheduler reported `LastTaskResult 3221225786 = 0xC000013A =
STATUS_CONTROL_C_EXIT` — not a crash, not teardown: the job shared a CONSOLE with
the agent shell, so every time a tool call ended the control event reached it.
Ladder of attempts: `nohup &` dies · `Start-Process -WindowStyle Hidden` dies ·
interactive Scheduled Task gets Ctrl+C · `-LogonType S4U` needs elevation
("Access is denied", and -Force DELETED the task on the way).
**What works with no admin rights: `decoder/spawn_push.py`** — `subprocess.Popen`
with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`. No console
exists, so no control event can arrive.
⚠ And do NOT pass the log file handle to Popen when the .cmd already redirects to
it — two writers, and Windows refuses the second ("being used by another
process") so the wrapper spins forever having pushed nothing.

### ★ "WHY NOT JUST MOVE AT THE PACE WE HAD BEFORE" — THE PACE WAS BORROWED

Login's question, and it deserves the blunt answer: **3,193 rows/s was never a
rate we had. It was a balance we spent.** Disk IO burst budget accrues over days
of idleness and drains under load; the early speed was withdrawal, not income.
Once drained, the sustainable rate is the REFILL rate.

Measured twice, independently, ~30 minutes apart: **~17,000 rows land, then the
instance stalls ~5 minutes, repeat — about 170,000 rows/hour ≈ 46 rows/s.**
2.66M rows remaining ⇒ **~16 hours**. That is income, not the borrowed number.

⚠ AND A GATE CEILING SET ABOVE WHAT THE SYSTEM ACCEPTS IS A METRONOME FOR
FAILURE. MAX was 2,500 while inserts measured:
    250 new rows 0.41s OK · 500 new 0.72s OK · 1,000 new TIMEOUT · 2,000 TIMEOUT
so the x1.25 ratchet climbed 500 -> 625 -> 782 -> timeout -> halve -> cool down
-> climb again, living in the failure zone. Capped MAX at the measured 500.
⚠ BUT CAPPING DID NOT FIX THE RATE — still ~47 rows/s. **The binding constraint
is the IO budget, not the statement size**, and my 500-row probe had itself been
taken in a moment when budget happened to be available. *A probe against a
budgeted resource measures the budget's current level, not the system.* Third
time today I read a transient as a steady state.

### ⚠⚠ I DESTROYED THE WRAPPER AND MY PATCH REPORTED SUCCESS

`pathlib.write_text()` OPENS (truncating) and THEN encodes. A unicode char in a
cp1252 default encoding raised UnicodeEncodeError *after* the truncate, leaving
`run_push_selection.cmd` at **0 bytes**. My next patch read the empty file,
found nothing to replace, wrote the empty string back, and **printed "wrapper
patched"**. Two spawns then did nothing at all and I hunted the wrong cause.
**Verify the ARTIFACT, not the print** — `wc -c` and a `grep` for the line you
believe you wrote. And keep .cmd/.bat files ASCII-only on Windows.

### ⭐⭐⭐ THE ACTUAL BUG: **THE ROWS WERE IN THE WRONG ORDER**. Login was right.

Login pushed back twice — *"before you had an api or endpoint... and moved super
quick"* and *"figure out what's wrong with your pull"* — against my answer that
the instance was simply out of IO. **The instance was a symptom. The cause was
insert order, and it was mine.**

A/B on the SAME endpoint, SAME instance, SAME depleted IO budget, minutes apart:

    SCATTERED key order   **0 of 2,000 rows landed** — every batch timed out
    SORTED key order      2,000/2,000, and then:
                            500 sorted rows  0.23s  =  2,169 rows/s
                          1,000 sorted rows  0.32s  =  3,091 rows/s
                          2,500 sorted rows  0.70s  =  3,555 rows/s
                          5,000 sorted rows  TIMEOUT (the real ceiling)

`acris_maps.jsonl` is in ACRIS's arbitrary order, so **every insert landed on a
random B-tree page** — random disk IO, page splits, buffer thrash. That is what
drained the Disk IO budget, and the timeouts, the AIMD gate flailing, the
cooldowns and the "16 hours" were all downstream of it. Sorted by `document_id`,
inserts append near-sequentially and the same index pages stay in cache.
**Sorting 2.47M rows took 18 seconds.** Result: 0 gate moves, 0 timeouts, 0
cooldowns — versus 47 rows/s and constant stalling.

⚠ **AND MY DIAGNOSIS WAS CONFIDENTLY WRONG IN A WAY THAT LOOKED RIGOROUS.** I
had measurements, an A/B (merge 1.00s vs insert 8.62s), a vendor email naming
Disk IO, and a coherent story — and I concluded "this tier cannot do it,
here are three things you must buy or change." Every measurement was real. The
*inference* skipped the one variable I controlled. **When a system says you are
using too much of a resource, ask what you are making it do, not only how much
it will allow.** The merge-vs-insert test was even pointing straight at index
maintenance; I read it as "inserts are expensive" instead of "why is this index
insert expensive".

⚠ The user's instinct — *17M maps and a 148M-page count came back fast, so speed
IS available* — was better than my model. (Worth noting what those actually
were: 17M x 13 KB HTML GETs at 128 concurrency, and the 148,659,387 pages was
ARITHMETIC over `hid_TotalPages`, never a fetch.) Different subsystem, but the
inference "something is wrong with how you are asking" was correct.

**STANDING RULE FOR EVERY BULK LOAD IN THIS PROJECT: SORT BY THE PRIMARY KEY
FIRST.** It is seconds of local work and it is the difference between 3,555
rows/s and not completing at all. Applies to the spine, the ledger, geometry,
and to acquisition's writes later — which are far larger than this.

### ⚠⚠⚠ CORRECTION TO THE ENTRY ABOVE — AND THE REAL STATE OF THIS RUN

Two things I got wrong, both of the SAME shape I had already named twice today.

**1. TWO PUSHES WERE RUNNING AGAINST THE SAME TABLE FOR 83 MINUTES.**
`taskkill /IM python.exe` killed the unsorted push's python — but not its
WRAPPER, which dutifully restarted it 30 s later. So the sorted run (pid 19540)
and the old UNSORTED run (pid 3760) both wrote to `document_map` from 15:27 to
16:50, the unsorted one scattering random inserts through the index the sorted
one was trying to fill in order. **Worse, both wrote the SAME
`_push_selection_state.json`**, so every progress number I read and reported in
that window was two counters interleaved and is worthless.
⇒ KILL THE WRAPPER BEFORE THE WORKER, and give every concurrent job its own
state file. A retry loop is a resurrection loop when you are trying to stop.

**2. THE 3,555 rows/s WAS ANOTHER TRANSIENT.** With the competitor killed and
the sorted file restarted from offset 0, **2,500-row sorted batches time out
again** and the gate walks straight back down. Sorting is still real — the
back-to-back A/B (0/2,000 scattered vs 2,000/2,000 sorted) was clean and
dramatic — but **sorting cannot conjure disk IO.** The probe simply landed in a
window where burst credit had accrued.
**That is the FOURTH time today I quoted a transient as a steady state**
(6,000 rows/s after a restart · 388 rows/s during a gate climb · 3,555 rows/s
sorted · and 500-row inserts "OK" minutes before they were not). The pattern is
now unmistakable: **on a budgeted resource, every short probe measures the
budget's current level. A rate is only real if it survives ten minutes.**

**HONEST STATE:** the instance's IO budget is deeply depleted — by us, over a
full day of pushing, latterly by two writers at once. All processes STOPPED
2026-08-13 ~16:55 so it can recover. `document_map` holds roughly 14.9M of
17,049,742; `_remaining_sorted.jsonl` (2,474,112 rows, sorted, 564 MB) is on
disk and is the correct input for the finish. Re-sending anything already loaded
is a cheap merge, so restarting the sorted file from zero is safe.
**Plan: let it rest, then run the sorted file once, alone.** The genuine fixes
remain the ones that cut IO rather than wait for it — drop the two secondary
indexes for the load, or `COPY` via a direct Postgres connection.


## 2026-08-14 scheduled run — THE LAST BLOCKED DESCRIPTION IS CLOSED. AUDIT 0 FAIL.

**2021070601644010 (Greenpoint Landing DEVR, BK 2472/2494/2502/2510/2520) DONE.**
Audit went **23 checks / 1 FAIL → 23 checks / 0 FAIL**: 31 → **62 verbatim
descriptions, 13/14 → 14/14 documents complete, 0 summarised, 0 with no
description block.** The four-document backlog opened on 2026-08-05 is now empty.

**No ACRIS request was made.** All 52 pages were already on disk
(`devr_pages/2021070601644010`), exactly as the 2026-08-13 entry recorded.
**Check the disk before the budget** — twice now.

⚠ **THE TASK FILE IS STILL STALE IN THE SAME TWO PLACES** (`python harvest.py 5`
is not an access probe; `harvest.known_pages()` does not exist), and it still
names four target documents of which three were closed the day before. A
scheduled task file is a cached plan and it goes stale like any other cache —
read the memory first and treat the task file as a hint.

### What the document turned out to be: 31 descriptions across SIX exhibits

    A  pp.23-37  Developer Conveyed Properties  16 parcels (B2472 lots 2,3,10,21,45,
                 50,60,65,80,90,100,200,475; B2494 lots 1,5; B2502 lot 2)
    C  p39       Lot 6 Land                      9,011 sf
    D  pp.40-43  City Land                       5 parcels (2472/20, 25, 35, p/o 75; 2494/3)
    E  pp.44-49  GLA Land                        7 parcels (2472/30, 55; 2494/10, 20;
                                                 2502/1; 2510/1; 2520/57)
    F  p50       Parcel H1H2 Land               44,599 sf — named by PARCEL, no tax lot
    H  p52       Block 2494 Lot 3                2,703 sf

Also read specifically to prove the inventory complete, and neither carries
courses: **p38 = Exhibit B**, a list of seven Subparcel Development and Easement
Agreements (already in cross_instruments), and **p51 = Exhibit G**, the
development-rights allocation chart. `pending_descriptions` for this document is
now EMPTY *and says which pages were checked and found descriptionless* — an
empty queue that cannot be mistaken for an unexamined one.

⭐ **THE SAME LAND IS DESCRIBED TWICE INSIDE ONE INSTRUMENT.** Block 2494 Lot 3
appears **word for word** in Exhibit D (p43, as City Land) and Exhibit H (p52).
Both walk to **2,702.9 sf at 0.00 ft closure against the stated 2,703** — a free
cross-check needing no second document, the same shape as the 388003/388004
Exhibit B match.

⭐ **AND IT EXPLAINS A DIVERGENCE ALREADY ON FILE.** That lot runs **to the mapped
CENTERLINE of West Street** — the description *includes half the mapped street
bed*. So does D lot 20, and so does E block 2502 lot 1 along Freeman Street. That
is the mechanism behind the recorded `survey_vs_taxmap` finding "doc 2,703 vs
PLUTO 2,814, held across p21v3/v4/p22v1": not digitizing spread, **a different
boundary**. Read the courses before classifying a divergence — the answer can be
in the description's own words.
⭐ E block 2510 lot 1 states its divergence *itself*, in the tie line:
**"distant 230.28 feet (230 feet Tax Map)"**.

### ⚠⚠ 23 OF 31 DESCRIPTIONS YIELD NO AREA — AND THE CAUSE IS MY PARSER, NOT THE SURVEY

    8 close   (closure 0.00–2.62 ft) — 6 reproduce the instrument's OWN stated area
              within 0.5%: 9,011 · 2,853 · 2,703 (twice, two exhibits) · 20,829,
              exact to ≤0.5 sf; plus 317,688 vs a walked 318,342.6 (+0.21%)
    23 do not — every one of them for the SAME two constructs

This surveyor writes a course as an **INTERCARDINAL adverb** ("northwesterly",
"southeasterly") plus a **stated INTERIOR ANGLE with the previous course**
("forming an interior angle of 151° 33' 26" with said northerly side of
Commercial Street"). `metes.py` resolves only the four cardinal `-ly` adverbs and
reads no relative angle, so `NORTHWESTERLY` matches nothing at all — `\bwesterly\b`
cannot fire inside it — and the course is dropped.
**Every parcel that closed is rectilinear-and-cardinal; every parcel that failed
is not.** The split is that clean, which is what identifies the cause.

⚠ **AND THE TEMPTING FIX IS THE WRONG ONE.** Adding `northwesterly=315°` to
CARDINAL would make Exhibit F walk a 45° parallelogram out of a rectangle the
document explicitly calls 90° at every corner — a **silently wrong area** where
there is now an honest refusal. In these descriptions the compass word is
APPROXIMATE and the interior angle is EXACT. The real capability is a
**relative-angle traverse**: take the first course's azimuth from its adverb, turn
by (180° − interior angle) at each vertex, and use the adverb only to *check* the
result. Deferred deliberately rather than half-built at the end of an unattended
run — a fix that creates the bug it guards against is this file's most repeated
story.
**It arrives with its own test set already in hand**: 18 of the 23 failures state
their area, so the fix is externally checkable the moment it exists (2,879 ·
63,405 · 226,481 · 58,974 · 72,032 · 11,890 · 20,025 · 262,808 · 150,980 · 44,599
· 42,958 · 50,281 …). Curves stay unhandled and stay `has_curve_unhandled`.

### Defects in the recorded original — transcribed as printed, none repaired

 * **D lot 25**: the closing course reads *"an exterior angle of 241° 33' 26"
   **feet**"* — the word *feet* attached to an ANGLE. Bug #10's trap wearing its
   other face, and exactly why the DMS strip in `parse_distance` is anchored on
   the degrees token.
 * **E block 2494 lot 20**: the CLOSING course is printed *"Thence **westerly** …
   along said southerly side of Dupont Street"* where it must run EASTERLY to
   return to the point of beginning. ⚠ The walked area still comes out at exactly
   the stated 20,025 sf while closure misses by 400.4 ft — **an area that matches
   is not proof the courses are right.** Only closure caught it.
 * **E block 2510 lot 1**: one course ends *"to a point on the United States
   **Pierhead** Line"* and the next travels *"along said United States **Bulkhead**
   Line"*. Two distinct lines, named inconsistently at one vertex.
 * Unit omitted: A block 2494 lot 1 *"a distance of 4.91 to a point"*; E block
   2494 lot 10 *"80.67 to a point"*. "a distance of" omitted entirely: A lot 45
   *"interior angle of 103°52'37" 69.78 feet"*. Typos: *"forming **and** interior
   angle"* (D lot 20), *"a **distant** 1529.18 feet"* (D lot 35), *"or 3.466
   **ACRES acres**"* (E lot 57).
 * E block 2520 lot 57: 1160.00 × 130.16 = 150,985.6 against a stated 150,980
   (5.6 sf). Reported.

### Exhibit A is the one exhibit that mostly does NOT state its areas

3 of 16 parcels carry "Encompassing an area of" (lots 65 = 20,829, 100 = 42,958,
200 = 50,281); the other 13 state none. Exhibits C/D/E/F/H state one for every
parcel. So on the DEVELOPER side of this deal the areas must come from the
traverse — which is precisely the side the parser cannot yet walk. That is the
practical cost of the gap above, stated as a denominator rather than as a plan.

### Store state after this run

15 documents / 270 postings / 83 citations. **23 checks | 0 FAIL | 14 PASS |
9 INFO.** 62/62 descriptions verbatim, 62/62 declare a shape, 61/61 walked
(34 close, 27 do not, each with a stated reason). `selftest.py` **56/56**.
The "located but not transcribed" queue is down from 7 items across 2 documents
to **1 item**: 2026012000388002 pp.41–44, the Zoning Lot Exhibit II title
certification.

**NEXT, in order:** (1) the relative-angle traverse in `metes.py`, validated
against the 18 stated areas above, then curves; (2) the last queued
certification description; (3) the ENVELOPE+ENCUMBER widening / sweep runner.
