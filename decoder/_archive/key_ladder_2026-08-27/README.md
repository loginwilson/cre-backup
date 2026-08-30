# THE KEY LADDER — built, proven, and retired the same day (2026-08-27)

`navigation.key` and `navigation.keyed_by` are **removed**. This directory
holds the whole design, working and tested, so it can be put back if the
reasoning below ever stops holding.

Nothing here is broken. It was retired because it turned out to be a
**denormalized cache of a table that answers the same question better**, not
because it failed.

---

## What it did

Four routes, assigned by trigger the moment a row's evidence landed — never a
batch job:

| route | meaning | tier |
|---|---|---|
| `parcel` | the rd names the document's own lots | READ |
| `reference` | a document it cites names them | DERIVED |
| `party` | subject is a PERSON — no lot claimed | — |
| `pdf-pass` | landed, unresolvable from the rd | unresolved |

`key` held `;`-joined BBLs; `keyed_by` held the route; `key_rules` enforced
the ladder (`PRE_MIGRATION_SCHEMA.sql` has the original text).

## Why it was retired

**1 · `key` was a cache, not a source.** For 93.6% of rows the lot is already
structured JSON in the rd (`parcels[].bbl`). Keying never *read* anything — it
copied a field ACRIS had already given us. And `doc_lot` can be built straight
from that JSON with no intermediate column:

```sql
INSERT INTO doc_lot(bbl, doc_id, route)
SELECT json_extract(j.value,'$.bbl'), n.id, 'parcel'
  FROM navigation n, json_each(n.recorded_details,'$.parcels') j
```

**2 · `keyed_by` was derivable.** The one job that looked irreplaceable —
telling `party` (correctly lot-less) apart from `pdf-pass` (unknown) — is just
which table holds a row:

| condition | meaning |
|---|---|
| has `doc_lot` rows | keyed to lots (route lives on the pair) |
| has `doc_subject` rows | subject is a person, correctly no lot |
| neither, rd landed | unresolved |
| rd not landed | not reached yet |

**3 · Extraction reads rd AND image anyway**, so the `reference` and `party`
routes resolve, before extraction, rows that extraction would resolve regardless.
Their only UNIQUE value is the **174,142 imageless documents** that can never
be extracted and would otherwise be permanently lot-less — 0.87% of the corpus.
⚠ That number was never weighed against the build cost until after the build.

## What SURVIVED and why

- **`doc_lot`** — kept. Not as keying, as an **INDEX**. `json_extract` across
  21.6M rows is a ~2-hour full scan (measured, external drive at ~3.4 MB/s); a
  `(bbl, doc_id)` table is a seek. It is the extraction WORK LIST, and the
  arithmetic that justifies it is: **25M documents at an optimistic 10s each is
  7.9 years single-threaded, ~9.5 months at 10x.** Broad-sweep extraction is
  unreachable, so extraction must be lot-targeted, so lot→doc must be fast.
- **`refs`** — kept, and it is the load-bearing table. Three jobs, found one at
  a time: inherit a lot (keying, now retired), **link an event to its prior**
  (the chain), and **say WHICH concurrent instance a release closes** (a lot can
  carry three live mortgages; without the edge you know an encumbrance ended but
  not which). The last two are needed by extraction regardless.
- **`doc_subject`** — kept. Person-subject documents (federal liens: 99.8%
  parcel-less because they are filed against a taxpayer, not a parcel).

## Put it back when…

- lot→doc has to carry a **confidence tier per attachment** — e.g. extraction
  starts finding lots the rd never named, so one document reaches different lots
  by different routes. `doc_lot.route` already has the column; the ladder is the
  vocabulary for it.
- the 174k imageless documents need lots badly enough to justify the machinery.
- someone wants `key`'s O(1) "is this row keyed" check back instead of an
  EXISTS against `doc_lot`.

## Proof that it worked

- `passes_test.py` — 22 checks, all routes end-to-end on rd_walk's write alone
- `pass2_e2e.py` — 20 checks, triggers only, nothing inserted by hand
- `cascade_test.py` — why `PRAGMA recursive_triggers` is **required**: it
  defaults OFF, so chains deeper than one hop silently do not resolve, and a
  SQL transitive closure CANNOT substitute (one UPDATE cannot observe its own
  effects). Per-connection — assert at lane startup, never trust it.
- `migrate.py` — the staged, resumable backfill runner.

⚠ Traps the scratch harness caught that reasoning did not: a naive `;` split
shreds trigger bodies; a comment check judging the accumulated buffer drops
every documented statement; `key_rules` is `SELECT CASE..END;` inside
`BEGIN..END;` so "ends at the first END;" truncates it; and a batch cursor set
to the next batch's first row must be resumed with `>=`, not `>`, or one
document per boundary vanishes silently.

---

## RETIRED 2026-08-27 — and the routes are a QUERY, not a lost capability

`reference` and `party` were dropped along with the columns. The reasoning that
made that safe:

- **`party` is fully covered by extraction.** Reading a federal lien yields a
  taxpayer name, not a lot — the same answer the route produced.
- **`reference` is covered EXCEPT for imageless AND parcel-less rows.** A
  parcel-less document WITH an image gets placed by extraction; one without an
  image has only its rd, which is parcel-less by definition. ⚠ That intersection
  was never measured — rough arithmetic (174k imageless x ~6.4% parcel-less)
  says order-10k rows, but it assumes independence and imageless correlates
  with microfilm, which may correlate with thin parcel data. **Measure it before
  relying on the estimate.**

**`refs` survives, so the reference route is one query:**

```sql
SELECT r.from_id, dl.bbl
  FROM refs r JOIN doc_lot dl ON dl.doc_id = r.value
 WHERE NOT EXISTS (SELECT 1 FROM doc_lot WHERE doc_id = r.from_id)
```

What was deleted is the TRIGGER MACHINERY that ran this eagerly at landing
time — not the ability. Running it after extraction is arguably better: it
resolves against a much fuller `doc_lot` than exists today.
