# Access discipline — binding on the judge, every extractor, and every script

**Extraction never accesses a source. It reads a db, and it opens the documents
that db points to. That is the whole of it.**

This binds the orchestrator first, because the orchestrator is who broke it.

## The only permitted shape

1. read the **doc id**
2. read its **registered details** and `pdf` value from `navigation` — opened
   `mode=ro`, with `busy_timeout`, never written
3. resolve with `corpus_paths.doc_path(pdf_value)` — the **stored** path. It returns
   a `Path`, or `None` when the row holds a state (`''`, `pending`, `absent`,
   `imageless`) rather than a file
4. open **that file on the drive**

`docpkg.py` implements exactly this and is the only sanctioned path. The full
contract is `04 Extractions/DOCUMENT ACCESS.md`; this file does not restate it.

## Forbidden, no exceptions, no "just once to check"

- **any network call, to any source.** The corpus is on disk — ~2.04M PDFs. A
  document that is not there is a finding to report, never a thing to fetch.
- **running `acris_reproduction.py`, `fleet.py`, `rc_lane.py`, or any acquisition
  or reproduction script.** A second process against a registry is the ban
  condition. Reading is not acquiring; extraction never acquires.
- **`corpus_paths.doc_store_dir()`**, or joining a root by hand. That is the
  *writer's* function; it re-derives a location from a date and will point at a
  different folder than the one the file actually landed in.
- **walking the acquisition store** — `rglob`, `find`, recursive `Get-ChildItem`,
  any directory scan under `02 Acquisitions`. The db already knows where the file
  is.
- **writing to, or holding a long transaction on, the navigation db.**

## Why the directory walk is on that list

It looks harmless — local reads, no network, nothing acquired. It is not.

> The store is on a **USB volume the register lane writes to continuously.** A heavy
> reader and a heavy writer on that volume contend. `DOCUMENT ACCESS.md` §6 measured
> it: a richmond count that normally takes **0.14 s took 112 s** while the lane ran,
> blew its budget, and made the board print a negative rate.
>
> On 2026-08-30 the orchestrator ran a corpus-wide `rglob` over the acquisition
> store for **three and a half hours**, plus a second recursive scan of the whole
> `D:\CRE Decoding System` tree, while a live registration pull was running. The
> pull's throughput went to zero.
>
> Nothing was fetched. Nothing was acquired. The damage was entirely disk
> contention, from code that looked read-only and safe.

**"It's only reading" is not a defence.** Scope is the constraint, not intent.

## Structural state, verified 2026-08-30

- `loop/bin/*.py` — **zero** network imports
- `corpus_paths.py` — imports `os`, `pathlib`, `re`, `sqlite3`, `time`; no network
- `docpkg.py` — `mode=ro` + `busy_timeout`, resolves via `doc_path()`, never
  `doc_store_dir()`, and treats a recorded path with no file as an integrity problem
  rather than a miss

The sanctioned path was already correct every time this went wrong. **The failure
was never the tool. It was improvising around it.**

If a tool you need does not exist: **say so and stop.**
