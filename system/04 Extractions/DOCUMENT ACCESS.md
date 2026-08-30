# DOCUMENT ACCESS — the contract for reading a document out of the db

> Hand this to anything that opens documents: extraction, a reader, an
> agent, a human. It answers ONE question — *given the db, how do I get
> the actual PDF?* — and it records the four ways that question has
> already been answered wrongly.
>
> Written 2026-08-29, after login asked for a file by name and could not
> find it. Every trap below is a real event, not a hypothetical.

## 1 · THE ONE RULE

    full path = corpus_paths.DOC_STORE / navigation.pdf

Use the resolver. Do not write that join by hand:

```python
import corpus_paths as CP

path = CP.doc_path(pdf_value)      # -> pathlib.Path, or None
```

The whole read side is one function. If you are writing anything more
than this to find a file, you are re-deriving something that is already
recorded, and §3 is about why that fails.

## 2 · WHAT `navigation.pdf` HOLDS — FIVE VALUES, ONE IS A FILE

| value | meaning | `doc_path()` |
|---|---|---|
| `By Document\...\<id>.pdf` | **the file** — relative to `DOC_STORE` | a `Path` |
| `''` | NOT YET CHECKED — the documentation floor has not reached this row. The honest todo. | `None` |
| `pending` | CHECKED — the source says the scan is not up yet; re-asked until it resolves | `None` |
| `absent` | CHECKED — determined to have no image (**richmond**) | `None` |
| `imageless` | CHECKED — aged, no image; the verdict (**acris**) | `None` |
| `NULL` | **must never appear.** If you see one, stop and report it. | `None` |

`pending` · `absent` · `imageless` are **determinations**, and they count
as *landed* on the update board — a row can be fully reproduced and still
have no file. **Landed ≠ readable.** Extraction's denominator is rows
with a real path, never the board's landed figure.

## 3 · THE FOUR TRAPS

**1 · READ THE STORED PATH. NEVER RE-DERIVE IT.**
`corpus_paths.doc_store_dir()` exists and looks like the right function.
It is not — it is the **writer's**: it decides where a file *goes* from
the recorded date, with fallbacks (the id's own date, then a plain 4+4
split). Which branch it took is not recoverable afterwards. Normalise a
recorded string or fix a bad date and the same id re-derives a
**different folder**, so a recomputing reader reports "missing" for a
file that is sitting on disk. `navigation.pdf` was written at the moment
the file landed. That is the truth.

**2 · TWO ROOTS EXIST AND ONLY ONE HOLDS THE FILES.**

    DOC_STORE   D:\CRE Decoding System\02 Acquisitions\
                Legal Instruments Acquisition            <- the files
    STORE       D:\Ignore\...\Acquisition Outputs\
                Documents                                <- deprecated

`STORE` is the more natural-sounding name, it resolves, and it exists on
disk. A hand-join against it returns a valid-looking path and fails as
*"file not found"* — which reads like missing data rather than a wrong
root. Always `CP.doc_path()`.

**3 · A STATE IS NOT A FILENAME — AND EMPTY STRING IS THE DANGEROUS ONE.**
`DOC_STORE / ''` silently yields the **store root**, which *exists*. A
naive join therefore "finds" a directory, `.exists()` returns True, and a
reader sails past it. That failure surfaces as garbage output thousands
of rows later, far from its cause. `doc_path()` returns `None` for every
state precisely so this cannot happen.

**4 · A RECORDED PATH WITH NO FILE IS AN INTEGRITY PROBLEM, NOT A MISS.**
If `doc_path()` gives a Path and it does not exist, the db and the store
disagree. Report it with the id. Do not silently skip, and do not treat
it as "no image" — that would launder a defect into a verdict.

## 4 · GETTING WORK

Rows that are actually readable right now:

```sql
SELECT id, pdf FROM navigation
 WHERE pdf LIKE '%.pdf'
 ORDER BY id            -- ⚠ always order; see §6
```

Split by source when it matters — the id namespaces are disjoint:

    richmond   id LIKE 'RC_%'      (range form: id >= 'RC_' AND id < 'RC`')
    acris      everything else     (digital 2016..., film FT_/BK_)

⚠ **`LIKE 'RC_%'` DEGRADES TO A FULL SCAN** on 24M rows — `_` is a
single-character wildcard in SQL. Use the range form for anything hot.

⚠ **COUNT YOUR OWN DENOMINATOR.** Do not take the update board's
`documentation landed` as the number of readable documents; it counts
determinations, including `pending` and `imageless`. Count `pdf LIKE
'%.pdf'` and report that figure with every rate.

## 5 · THE READ LOOP

```python
import sqlite3
import corpus_paths as CP

c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
c.execute("PRAGMA busy_timeout=30000")   # ⚠ see §6

for did, pdf in c.execute(
        "SELECT id, pdf FROM navigation WHERE pdf LIKE '%.pdf' ORDER BY id"):
    path = CP.doc_path(pdf)
    if path is None:                     # a state, not a file
        continue
    if not path.exists():                # §3 trap 4 — report, never skip quietly
        report_integrity_problem(did, path)
        continue
    read(path)
```

## 6 · OPERATING ALONGSIDE THE REPRODUCTION LANES

- **OPEN THE DB READ-ONLY** (`mode=ro`) and **set `busy_timeout`.** The
  register lane writes continuously; without a timeout a reader raises
  *"database is locked"*, which looks like a missing document and is not.
- **NEVER `$offset` / `LIMIT` WITHOUT `ORDER BY`.** Unordered paging
  silently drops and duplicates rows. Order by `id`.
- **NO FULL TABLE SCANS ON A TICK.** A 24M-row `COUNT(*)` stalls WAL
  checkpointing and starves the lanes. Measured 2026-08-29: a normally
  0.14 s richmond count took **112 s** while the register lane ran, blew
  its budget, and made the board print a **negative rate**. Count once,
  cache it, carry the denominator.
- Extraction reads files; the lanes write rows. They can run together —
  but a heavy reader and a heavy writer on the same USB volume contend,
  so measure before assuming a slow read is the source's fault.

## 7 · FINDING ONE DOCUMENT BY HAND

```bash
python document_locate.py RC_988537              # print the full path
python document_locate.py RC_988537 --open       # open the PDF
python document_locate.py RC_988537 --reveal     # Explorer, file selected
```

⚠ **Windows Search will not find these.** The store is on an external
volume, which is excluded from the search index by default, so Explorer's
search box returns nothing for a file that is present. A failed Explorer
search is **not** evidence a document is missing. Ask the tool.

## 8 · OPEN ITEM

The db does not carry its own root, so a `pdf` value read straight out of
DB Browser (`By Document\1917\03 Mar\28\RC_988537.pdf`) is not resolvable
without knowing `DOC_STORE`. The fix is one meta row holding the root —
**not** rewriting the ~4.5M relative paths to absolute ones. Relative is
deliberate: this store lives on a USB drive that has already come back
under a different letter, and absolute paths would put every row wrong on
a remount while relative needs one constant changed. Scheduled for the
boundary between registration closing and documentation starting.
