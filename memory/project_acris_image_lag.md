---
name: project_acris_image_lag
description: "The 7-day image lag window reaches into ACQUISITION, not just the daily spec routine — a placeholder inside the window was retiring documents permanently, and the parcel was marked complete so nothing ever came back"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-19T13:46:35.512Z
  originSessionId: 08c6ae7d-15c6-47eb-a318-3f175a82786b
---

**A document already recorded in the specification can still acquire its image later.**
`image_policy.py` is the one image policy for both sources — land `pending` → probe each
daily run while ≤ `TERMINAL_DAYS`=7 old → `imageless`. It was a *specification* rule that
**acquisition never imported**, so it sat one directory from the code that needed it.
(The recurring shape: the fix exists and is unaddressable, not missing.)

## ⚠ THE SILENT PERMANENT LOSS — every number along the path read correct

```
recorded 3 days ago, scan not yet attached
 -> fetch returns the END-OF-DOC PLACEHOLDER (HTTP 200)
 -> ledger row `empty`
 -> parcel_folder.empty_ids() folded it into the image-less set
 -> _INDEX.md rendered "**no image** — index is the record"
 -> manifest now has NO outstanding row
 -> overnight.py tests for "| not acquired |" -> parcel marked COMPLETE
 -> never queued again. The scan attaches on day 4. Nothing asks. Ever.
```

The output is a **permanent false claim** — *"this document has no image, the index is
its whole record"* — asserted about a record nobody finished looking at.
**`pending` and `imageless` are INDISTINGUISHABLE on any single read; only AGE separates
them.** A placeholder proves nothing until the window closes.

## The fix — THREE files, and the third is the one that is easy to miss

- `parcel_folder.empty_ids()` returns **(terminal, pending)**, splitting ledger `empty`
  rows on `image_policy.is_terminal()`. ⚠ Clock = the spec's `recorded_date`, falling
  back to the ledger's `at` — **the window is measured from RECORDING**; the ledger only
  knows when *we* asked.
- `_INDEX.md` gained a third state `pending scan`, counted as OUTSTANDING.
- ⚠ `overnight.py` decides completeness by STRING-MATCHING the manifest, so a new state
  it does not know is invisible — the parcel would still read complete and the fix would
  have done nothing. Now tests `("| not acquired |", "| pending scan |")`. Old manifests
  predate the marker so it is safe over what is on disk.
  **A new state is not wired until every reader of that state knows it.**

Verified on real data, not a counter at zero: 1,893 `empty` rows split **1,888 terminal /
5 pending** — a **DEED + two MORTGAGES from one closing** (2026072800456001/002/003, one
submission, sub-indices 001–003) plus two RPTT&RET, recorded 08-12/13, asked 08-18. All
five were being written off permanently. None of their 3 parcels had a manifest yet, so
the exposure was entirely forward.

## ⚠ THIS REFUTES THE "ACRIS HAS NO LAG" CALIBRATION

`LIVE_SYNC.md` records *ACRIS 400/400 imaged same-day, so its pending set drains on the
first probe*. Back-check of every `empty` row by ask-minus-record interval:
same-day **0** · 1–3 d **0** · 4–7 d **6** · 8–30 d **4** · 1–12 mo **38** · >1 yr **1,845**.
35 were recorded in 2026 (RPTT&RET 13 · MTGE 5 · ASST 5 · DEED 2 …). The same-day claim
came from a 400-doc sample that did not include the slow types.
**The 7-day window is NOT Richmond-only — do not narrow it to one source.**

## The standing rule for every phase after this

Acquisition may never treat a placeholder as terminal inside the window; a parcel may
never be marked complete while it holds one; and **anything that lands late must re-enter
the pipeline — a newly acquired image is new input to extraction, not just a file on
disk.** Acquisition's job does not end at the byte.

See [[project_acris_bulk_acquisition]], [[project_acris_selection_job]],
[[feedback_confidence_backcheck]].
