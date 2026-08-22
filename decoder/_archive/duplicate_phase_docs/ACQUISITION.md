# ACRIS · PHASE 2 — ACQUISITION

**Acquire data: retrieve the specified inputs.** Status: **CONFIRMED**.

Acquisition works and is not blocked. ~8,000 pages fetched across 8 configurations,
**zero refusals**. Earlier "ACRIS is blocking us" readings were harness artifacts — that
one is on the record as wrong five times, from comparing urllib probes against an aiohttp
job.

---

## 1 · The one writer to use

| script | writes | verdict |
|---|---|---|
| **`acquire_async.py`** | `{doc}.tif` multipage (+`--pdf`) | **USE THIS** — ledger-resumable, `ACRIS_CORPUS_ROOT` |
| `store.py` / `ingest.py` | sha256 blobs + `manifest.jsonl` | a storage layer, not the fetcher |
| `devr_acquire.py`, `fetch_pages.py` | `p{n:03d}.tif` loose pages | ⚠ **these made the mess — do not use** |

The loose-page writers are why `devr_pages/` holds **42,310 files in 1,180 folders and zero
containers**. `acquire_async.py` treats loose pages as its **write-failure fallback**, not
as an output format. Convert existing ones with `to_documents.py`.

```
ACRIS_CORPUS_ROOT=E:/acris python acquire_async.py --docs 200 --conc 8
```

⚠ **ONLY 2 OF 59 SCRIPTS READ THE ENV VAR.** The other 57 hardcode `devr_pages` /
`sample_pages` / `index_full` by name. **Use a Windows junction** rather than editing 57
files: `cmd /c mklink /J devr_pages E:\acris\devr_pages`.

---

## 2 · Measured throughput

| config | pages/s | latency | citywide (148.2M pg) |
|---|---|---|---|
| 1 × conc 8 | 15.0 | 0.41 s | 114 d |
| 2 × conc 8 | 29.0 | 0.42 s | 59 d |
| **4 × conc 8** | **49–58** | **0.36–0.40 s** | **30–35 d** ← use this |
| 8 × conc 8 | 69.3 | 0.54–0.97 s | 25 d |

**The knee is between 4 and 8 processes**: throughput gains 2× → 2× → **1.4×**, while
latency **doubles**.

⚠ **THE NETWORK IS RULED OUT; THE CLIENT CPU IS NOT.** TCP connect is **20 ms**; a page
fetch is 0.26 s, so ~0.24 s is ACRIS generating the TIFF. 69 pg/s = 33 Mbps against a
574 Mbps link = **6% of capacity**. So faster internet buys nothing.
**But the knee has two possible causes and nobody isolated them** — ACRIS throttling and
the client saturating produce *identical* symptoms (rising latency, flattening throughput).
This laptop is an **8-core** Core Ultra 7 266V running **64 concurrent connections** at the
knee, so client-bound is plausible.

**OPEN — the cheapest unknown left.** Repeat 8×8 while logging CPU utilisation and the
connect/wait split:
- CPU near 100% → **client-bound**; more cores buy real throughput and a lab is worth it
- CPU idle, server response rising → **server-bound**; 69 pg/s is the ceiling anywhere

⚠ Scaling *within one client* cooperates with the limiter. **Splitting across addresses to
multiply the rate budget does not, and stays off the table** — `acquire.py` is titled
*"cooperate with the limiter instead of guessing around it."*

⚠ Two machines on one home network share one address-level budget — no gain.

---

## 3 · ⚠ Traps that return HTTP 200

**PER PAGE. There is no whole-document endpoint.** `no-page`, `allpages` and `page-0` all
return the same **13,684-byte placeholder**; the print/PDF paths return an ACRIS error
page. The viewer's Save button is Acordex VTU + jsPDF assembling client-side — one
`GetImage` call per page, same request count, plus a lossy re-encode.

⚠ **END OF DOCUMENT IS A PLACEHOLDER, NOT A 404.**

```
md5  4081a3f2004d7244a966995c02c730d0     served as HTTP 200, valid TIFF bytes
```

**"Fetch until it fails" never fails.** Match the placeholder explicitly.

---

## 4 · Storage

- **One multipage TIFF per `doc_id`**, G4 preserved, **0.99×** the loose bytes; page N opens
  in ~3 ms. **17M files, not 148M** — loose pages cost ~148 GB of NTFS metadata and would
  hit an inode quota on a parallel filesystem long before the storage quota.
  **`doc_id` IS the filename**, so nothing must be opened to know what a file is.
- ⚠ **NEVER `convert("L")` A BITONAL SCAN INTO A PDF** — measured **15.2× inflation**,
  which turns 9.3 TB into **141 TB**.
- **Do not store PDFs at all.** Each is 0.98× the TIFF, so keeping both is ~2× storage.
  Generate on demand.
- **No inline PDF during fetch**: 46 → 58 pg/s without it.
- **Total 9.3–10.2 TB** at 61–67 KB/page (film 88–122, book 66–74, digital 45–48 KB).
  **Buy 16 TB.**

---

## 5 · Safety and resumption

- **Shared AIMD gate** across all workers. A **matched refusal cancels everything and never
  retries.** On a refusal: stop. Do not rotate anything, do not work around it.
- **Ledger-resumable**, so interruption is free.
- ⚠ **UPTIME BEATS THROUGHPUT.** 49 pg/s at 24/7 = **35 days**; 69 pg/s at 8 hrs/day =
  **74 days**. The faster config run part-time is the slower plan.
  Windows: lid action → Do nothing, `powercfg /change standby-timeout-ac 0`.
- **EDS bulk transfer (~$8,500, 212-487-6300)** is the sanctioned alternative to 35 days.

---

## 6 · ⚠ Bugs that reported SUCCESS while failing

Every one of these passed its own check:

- `return_exceptions=True` hid **150 dead document tasks** behind a clean summary — the
  actual cause was a full disk.
- A page cap applied *inside* the page loop truncated an 84-page document at 28 and
  labelled it `short`.
- `_check_denied` searched raw bytes for a phrase that markup splits — so the one function
  whose job is to stop us **could not fire**.
- A page-conversion job wrote **37 files for 64 inputs** and reported success, because
  nothing compared the counts.

**Therefore: every output is verified against its input count, and every rate is reported
with its denominator.** `to_documents.py` reopens each container and compares frame count
to source page count; a mismatch is reported and the document is left off the done-list.

---

## 7 · Runbook

```
python to_documents.py --dest E:/acris --dry     # what would convert
python to_documents.py --dest E:/acris           # 1,865 docs -> containers, verified
ACRIS_CORPUS_ROOT=E:/acris python acquire_async.py --docs 200 --conc 8
```

Source pages are **never deleted** by any of this. Deleting 47,378 originals is a human
decision made after checking, not a side effect.
