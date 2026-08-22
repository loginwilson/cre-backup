# ACRIS · SELECTION — THE DATA

What this phase hands to acquisition. The *how* is in [workflow.md](workflow.md).

## THE TWO PRODUCTS

### 1. The doc-id map — what acquisition walks

**Store: Supabase, `document_map`.** 17,049,742 rows, reconciled ACRIS ↔ local ↔
Supabase 2026-08-14.

| column | meaning |
|---|---|
| `document_id` | PK — **and the image endpoint itself** |
| `doc_type` | RPTT, DEED, MTGE … 95 types |
| `recorded_date` | |
| `total_pages` | how many requests this document needs |
| `cover_pages` / `instrument_from` / `instrument_to` / `supporting_from` / `tax_return_from` | page geometry: which pages are the instrument vs supporting vs the RP-5217 |
| `no_image` | **true ⇒ do not fetch.** The index is this document's whole record |

⚠ **The id IS the access point.** `GetImage?doc_id={id}&page={n}` — nothing to
store, nothing to navigate. This is why acquisition can run straight off the map.

⚠ **`total_pages` is what proves acquisition, and it cannot be discovered by
fetching.** A request past the last page returns ACRIS's placeholder as HTTP 200,
so "fetch until failure" never terminates correctly. The count must come from
here.

**Work queue:** `acquisition_pending` (a VIEW, zero storage) = `document_map`
minus `source_document`. It reads 17,047,262 today because `source_document` is
empty — nothing has been acquired as corpus yet, which is accurate. Reaching zero
is the correspondence proof.

⚠ **Nothing writes `source_document` yet.** Wire it before Monday or the queue
never shrinks, a restart re-fetches everything, and the 174,142 image-less
documents get hammered for placeholders.

### 2. The support index — extraction's third channel

**Store: on disk as gzip, `index_full/`.** 100,764,843 rows across five published
Socrata datasets. Whether master/parties/legals also land in Supabase is
[migration 002](../../../migrations/), undecided.

| dataset | rows | carries | status |
|---|---|---|---|
| master `bnx9-e6tj` | 17,065,090 | doc type, dates, `document_amt`, CRFN, reel | ✅ exact |
| legals `8h5j-fqxa` | 22,727,180 | BBLs — which property it touches | ✅ exact |
| **parties `636b-3b5g`** | 46,540,137 | **names + `party_type`** | pulling |
| references `pwkr-dpni` | 8,699,896 | document-to-document links | queued |
| remarks `9p4w-7npp` | 5,732,540 | free text | ✅ exact |

⚠ **`party_type` is the row that matters.** It is who-was-grantor from a
structured source, and it is the only check that catches a role inversion — the
failure transcription scoring structurally cannot see.

⚠ **Do NOT trust `document_amt` for money.** It is 0 for every DEVR; price comes
from the cover-page RPTT/RETT stamps, and development-rights square footage lives
in an exhibit, not in any index field. The index is authoritative for parties,
roles, BBLs, types and dates — **per field, never wholesale.**

### 2a. Image-less documents — the index IS the record

**Store: `index_noimage.jsonl`, 360 MB, on disk.** 174,142 documents.

108,817 return ACRIS's placeholder (`total_pages` 0), 65,269 are microfilm-era
(−1). Mostly RTXL, but **19,712 DEEDS and 16,440 MORTGAGES** — no image of these
will ever exist. Coverage: master 100% · parties 174,067 · legals 174,018 ·
remarks 89.6% · references 2.0%.

## LOCAL WORKING FILES

| file | size | what |
|---|---|---|
| `acris_maps.jsonl` | 3.85 GB | page geometry — **15–27 h of ACRIS calls, the most expensive artifact here** |
| `acris_ids.jsonl` | 1.79 GB | the raw id pull |
| `_remaining_sorted.jsonl` / `docmaps.jsonl` / `census_maps.jsonl` | | the other map files; all four define "local" |
| `_local_ids.idx` | 136 MB | sorted 8-byte hashes — makes the daily check a binary search |
| `_id_prefix_counts.json` | | 9,148 prefix buckets — partition bounds with zero server planning |

⚠ **19,549,196 lines collapse to 17,049,742 distinct ids.** The mappers append,
so re-runs rewrite the same id. Comparing lines to rows reports every duplicate
as a loss.

## WHAT ACQUISITION CONSUMES

1. `acquisition_pending` — the queue
2. `document_map.total_pages` — how many pages, and the proof afterwards
3. `document_map.no_image` — **skip these**, they are already acquired by index

## WHAT IS NOT HERE, AND WILL NOT BE

**Staten Island recordings.** `recorded_borough` has four values only —
Manhattan 6,213,473 · Queens 4,926,801 · Brooklyn 4,336,657 · Bronx 1,588,159.
Richmond County deeds sit with the County Clerk. LEGALS carries 207,392 rows
referencing Staten Island *properties* recorded elsewhere, so the parcels are
visible while their conveyance history is not — the shape most likely to read as
coverage. Parked for consolidation with the county clerk.

⚠ **MEASURED 2026-08-18 — the doc types prove it, and the ratio alone would not.**
Staten Island averages **2.0 documents per parcel against 16.9-27.3 for every other
borough**, and the composition is not a thin version of the others — it is a different
kind of record entirely:

| doc type | Staten Island | Brooklyn |
|---|---|---|
| RPTT + RPTT&RET | **99.7%** | — |
| DEED | **0.0%** | 10.5% |
| MTGE | **0.0%** | 32.1% |

What ACRIS holds for Staten Island is the **transfer-tax form**, not the instrument.

⚠ **AND IT WILL PASS EVERY COMPLETENESS CHECK WE HAVE.** If borough 5 enters the walk
unmarked, all 101,336 parcels acquire their 207,392 documents, every folder materialises
with no `not acquired` rows, and `coverage.py` scores Staten Island **100% ACCOUNTED** —
because the specification only knows what ACRIS published, and ACRIS did publish all of
it. The failure is invisible precisely because nothing failed.

Per `acris_scope.py` this is **NOT-RECORDED**, never **MISSING**: ACRIS is not the
authority for a Richmond County deed, so its absence is an answer, not a gap. It must be
marked as a **handoff to a second custodian at SPECIFICATION time**. Discovering it in
extraction means discovering it as a silent hole in every Staten Island title chain.

⚠ **All three sides agreeing proves the COPY is faithful, not that the SOURCE is
complete.** All three would agree just as perfectly on a hole in ACRIS.
