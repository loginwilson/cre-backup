# ACRIS · ACQUISITION — THE DATA

What this phase produces and where it lives. The *how* is in
[workflow.md](workflow.md).

## ⚠ THIS PHASE'S DATA DOES NOT GO IN SUPABASE

~148,000,000 page images, **~9.3 TB**. That is not a database question. Images
are written once and read sequentially by extraction — the access pattern a
filesystem is for.

| tier | medium | holds |
|---|---|---|
| **primary** | 20 TB external drive | the complete source corpus |
| **backup** | 4 TB external SSDs | verified offline copies |
| **scratch** | NYU Torch | temporary, during extraction only |

⚠ **The original stays after processing begins.** Extraction reads a copy; it
never consumes the only version. Re-acquiring a page costs ACRIS budget and
carries refusal risk, so the corpus is treated as unrepeatable.

## WHAT GOES IN SUPABASE FROM THIS PHASE — the ledger only

`source_document` — one row per acquired document. Small, and it is what makes
`acquisition_pending` shrink.

⚠ **It is empty and nothing in the ACRIS path writes it.** That is accurate
today (everything pulled so far was calibration, not corpus) and it is the gap
to close before Monday. Without it there is no way to distinguish a document
that was fetched from one that was skipped, and a restart re-fetches everything.

Minimum it must record: `document_id` · mode (`image` | `index`) · pages
retrieved · when · where on disk. Mode matters because **174,142 documents are
already acquired by index** and must never enter the image queue.

## ON DISK TODAY — calibration material, NOT corpus

| path | files | size | what |
|---|---|---|---|
| `devr_pages/` | 42,310 | 2.1 GB | 1,180 documents, pulled to calibrate acquisition and then to test extraction |
| `sample_pages/` | 4,271 | 282 MB | sampling for the bench |
| `bakeoff/pages/` | 26 | 20 MB | the fixed bench set — **identical pixels for every engine** |

⚠ **Do not count these as acquired corpus.** They exist because acquisition and
extraction needed something to be measured against. Whether Monday's run should
skip the 1,180 documents already on disk is an open decision — skipping saves
budget, re-fetching guarantees the corpus is uniform.

## THE PROOF THAT ACQUISITION MATCHES SELECTION

Per document: files on disk vs `document_map.total_pages`.

⚠ **A byte count cannot tell a short document from a truncated one**, and
"fetch until failure" never terminates — a request past the last page returns
ACRIS's placeholder as **HTTP 200**. The page count must come from selection.

`acquisition_pending` reaching zero is the corpus-level proof; the per-document
page check is the row-level one. Neither exists yet.

## MEASURED, NOT ASSUMED

- 4 procs × concurrency 8 → **49 pages/s → ~35 days, 9.3 TB**
- The ceiling is ACRIS's image service: **20 ms connect, 6% of the link.**
  Faster internet buys nothing.
- The page-map endpoint calibrated to 128 concurrent / 292 maps/s in 2026-08.
  **That is a different endpoint** — image acquisition must measure its own
  ladder and must not inherit that number.
