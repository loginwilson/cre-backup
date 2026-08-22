"""Push the OTHER two map files into document_map.

    python push_maps_tail.py [--verify]

`push_selection.py` reads ONE source (`acris_maps.jsonl`) and resumes on a byte
offset held in a single state file, so it cannot be pointed at a second file
while it is running. These two are small enough not to need any of that:
docmaps.jsonl 69,729 lines + census_maps.jsonl 3,600 lines.

⚠ THE REASON THIS IS NOT JUST "RUN THE PUSHER TWICE": AN UPSERT CAN ERASE.
`docmaps.jsonl` is written by `amap`, and some of its rows carry no `doc_type`
and no `recorded` — the ones recovered from a log have only the page geometry.
`push_selection.row()` turns a missing key into an explicit null, and PostgREST
`resolution=merge-duplicates` writes every column in the payload, so pushing
those rows over a document already loaded correctly from acris_maps.jsonl would
BLANK ITS doc_type. A backfill that deletes information is worse than no
backfill, and it would look like a clean run.

So rows are split by which fields they actually have, and each group is sent
with only its own columns. A row that does not know a document's type simply
does not mention the column, and whatever is already in the table survives.

⚠ AND THE FILES OVERLAP EACH OTHER. Deduped by document_id before sending,
preferring the RICHEST record (one that knows the type and has a page count)
rather than the last one read — last-wins would let a bare log-recovered row
beat a complete one.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import push_selection
import supabase_sync as S

FILES = ("docmaps.jsonl", "census_maps.jsonl")
TABLE = "document_map"
BATCH = 1000


def fmt(n):
    return f"{n:,}" if n is not None else "UNKNOWN (count did not evaluate)"


def safe_count():
    """Row count that REPORTS ITS OWN FAILURE instead of killing the run.

    ⚠ THIS IS WHAT BROKE THE FIRST ATTEMPT, AND IT BROKE IT FROM THE WRONG SIDE.
    `supabase_sync.push()` takes an exact `count=exact` of the whole table before
    and after its batches — fine for 360k fact rows, and I then called it once
    per 1,000-row chunk, so every chunk triggered a full-table count. At ~5.5M
    rows (and climbing, with push_selection.py writing concurrently) Supabase
    started returning **HTTP 500** on the count, the exception propagated, and
    the run died — **after 26,000 rows had already been written successfully.**

    A verifier that aborts the run it is verifying turns a partial success into
    a reported total failure, which this project has already named as the same
    defect as the reverse. So: count twice, not 17,000 times; and when the count
    cannot be taken, say `UNKNOWN` — never 0, and never a raised exception.
    """
    try:
        return S.count(TABLE)
    except Exception as e:
        print(f"  ⚠ count unavailable ({type(e).__name__}: {e}) — reported as "
              "UNKNOWN, not as zero")
        return None


def richness(d):
    """How much this record knows. Higher wins on a document_id collision."""
    return ((1 if d.get("doc_type") else 0)
            + (1 if d.get("recorded") else 0)
            + (1 if d.get("hid_TotalPages") is not None else 0)
            + (1 if d.get("instrument") else 0))


def main():
    verify = "--verify" in sys.argv
    best, read, bad = {}, 0, 0
    for name in FILES:
        p = pathlib.Path(__file__).with_name(name)
        if not p.exists():
            print(f"  MISSING {name} — skipped (reported, not assumed empty)")
            continue
        n = 0
        for line in open(p, encoding="utf-8", errors="replace"):
            read += 1
            n += 1
            try:
                d = json.loads(line)
            except ValueError:
                bad += 1
                continue
            k = d.get("doc_id")
            if not k:
                bad += 1
                continue
            if k not in best or richness(d) > richness(best[k]):
                best[k] = d
        print(f"  {name:<20} {n:>8,} lines")
    print(f"\n  lines read       {read:,}")
    print(f"  malformed/keyless{bad:>8,}")
    print(f"  distinct doc_ids {len(best):,}")

    # ⚠ A NULL doc_type IS NOT HARMLESS — IT IS INVISIBLE TO THE DAILY DELTA.
    # `amap` writes page geometry only, so 68,549 of these rows know no type.
    # Preserving the table's existing value covers documents already loaded from
    # acris_maps.jsonl, but a document that arrives here FIRST would land with
    # doc_type null — and `selection_delta.py` reconciles per doc_type, so a
    # null-typed row counts under nothing, is never seen as present, and gets
    # re-diffed every single day forever. A row that is silently uncountable is
    # worse than a missing row, because the missing one at least gets fixed.
    # So the type is filled from the id ledger first — an offline pass over a
    # file we already hold, not 686 more requests at ACRIS.
    LEDGER = pathlib.Path(__file__).with_name("acris_ids.jsonl")
    need = {k for k, d in best.items() if not d.get("doc_type")}
    if need and LEDGER.exists():
        print(f"\n  {len(need):,} rows carry no doc_type — filling from "
              f"{LEDGER.name} ...", flush=True)
        found = 0
        with open(LEDGER, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                # cheap prefilter: the id is the first value on the line
                a = line.find('"document_id": "')
                if a < 0:
                    continue
                a += 16
                b = line.find('"', a)
                k = line[a:b]
                if k not in need:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                best[k]["doc_type"] = r.get("doc_type")
                rec = r.get("recorded_datetime")
                if rec and not best[k].get("recorded"):
                    best[k]["recorded"] = rec[:10]
                need.discard(k)
                found += 1
                if not need:
                    break
        print(f"  filled {found:,} · still unknown {len(need):,}"
              + ("  (these push without the column, keeping whatever the table "
                 "holds)" if need else ""))
    elif need:
        print(f"\n  ⚠ {len(need):,} rows carry no doc_type and {LEDGER.name} is "
              "absent — they will be uncountable by the daily per-type delta")

    # ⚠ SPLIT BY KNOWN FIELDS so an upsert can never null out a good value.
    groups = {}
    for d in best.values():
        r = push_selection.row(d)
        drop = [c for c in ("doc_type", "recorded_date") if r.get(c) is None]
        for c in drop:
            r.pop(c)
        groups.setdefault(tuple(sorted(r)), []).append(r)
    for cols, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        missing = {"doc_type", "recorded_date"} - set(cols)
        print(f"  group of {len(rows):>7,} rows"
              + (f"  — omits {sorted(missing)} so the table keeps what it has"
                 if missing else "  — full payload"))

    if verify:
        print("\n  --verify: nothing sent.")
        return 0

    before = safe_count()
    print(f"\n  {TABLE} before {fmt(before)}")
    sent = 0
    for cols, rows in groups.items():
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i + BATCH]
            S._post(TABLE, chunk, "document_id")     # idempotent upsert, retries
            sent += len(chunk)
            if sent % 10000 == 0:
                print(f"    {sent:>8,} sent", flush=True)
    after = safe_count()
    print(f"\n  rows sent        {sent:,}")
    print(f"  {TABLE} after  {fmt(after)}")
    if before is not None and after is not None:
        print(f"  net new          {after - before:,}   (the rest merged onto "
              "document_ids already present — expected, these files overlap "
              "acris_maps.jsonl, and a concurrent push_selection run is adding "
              "rows at the same time, so this is NOT a clean subtraction)")
    else:
        print("  ⚠ net new UNKNOWN — the count did not evaluate. The upserts "
              "landed (they are idempotent and retried); the verification did "
              "not. Re-run --verify later rather than assuming either way.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
