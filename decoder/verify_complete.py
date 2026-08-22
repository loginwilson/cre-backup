"""IS THE MAP COMPLETE — AS OF TODAY, NOT AS OF WHEN THE MAP STARTED.

Two different questions, and answering only the first is how a map reports 100%
forever while falling behind:

    1. did every id we QUEUED get mapped        -> the 2 short
    2. has ACRIS published anything since       -> today's delta

⚠ NO json.loads. The previous verifier parsed 17M JSON objects to read one
field and spent 65.8s doing it. `doc_id` is the first key on every line of
acris_maps.jsonl and `document_id` is the first key on every line of
acris_ids.jsonl, so a slice answers it — with a json.loads fallback per line so
a different key order degrades in speed instead of silently dropping documents.

⚠ ALL THREE MAP FILES. Reading only acris_maps.jsonl reported 98.64% when the
truth was 100.000%; docmaps.jsonl and census_maps.jsonl hold 73,326 documents.

    python verify_complete.py            queued-vs-mapped + today's delta
    python verify_complete.py --local     skip the network, files only
"""
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")
IDS = pathlib.Path("acris_ids.jsonl")
STATE = pathlib.Path("_map_delta_state.json")


def ids_from(path, key):
    """Every id in a jsonl file. Slice first, parse only if the slice misses."""
    head = '{"%s": "' % key
    n = len(head)
    out = set()
    bad = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(head):
                e = line.find('"', n)
                if e > n:
                    out.add(line[n:e])
                    continue
            if not line.strip():
                continue
            try:                              # ⚠ fallback, never a skip
                v = json.loads(line).get(key)
            except ValueError:
                bad += 1
                continue
            if v:
                out.add(v)
            else:
                bad += 1
    return out, bad


def main():
    t0 = time.time()

    mapped, badm = set(), 0
    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            print(f"  ⚠ {name} missing")
            continue
        s, b = ids_from(p, "doc_id")
        badm += b
        print(f"  {name:<20} {len(s):>12,} ids  ({time.time()-t0:.0f}s)", flush=True)
        mapped |= s

    queued, badq = ids_from(IDS, "document_id")
    print(f"  {'acris_ids.jsonl':<20} {len(queued):>12,} ids  ({time.time()-t0:.0f}s)\n")

    print(f"  DISTINCT MAPPED      {len(mapped):>12,}")
    print(f"  DISTINCT QUEUED      {len(queued):>12,}")
    if badm or badq:
        print(f"  ⚠ unreadable lines: maps {badm:,} · ids {badq:,}")

    missing = sorted(queued - mapped)
    extra = len(mapped - queued)
    print(f"\n  QUEUED BUT NOT MAPPED {len(missing):>11,}")
    if extra:
        print(f"  mapped but never queued {extra:>9,}  (added by other runs)")
    for d in missing[:40]:
        print(f"      {d}")
    if len(missing) > 40:
        print(f"      ... and {len(missing)-40:,} more")

    if "--local" in sys.argv:
        print(f"\n  --local: network skipped.  ({time.time()-t0:.0f}s)")
        return

    # ── has ACRIS moved since the watermark? ────────────────────────────
    import bulk
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    last = st.get("dataset_stamp")
    live = int(bulk.socrata(MASTER, select="count(1) as n",
                            paginate=False, limit=1)[0]["n"])
    now = bulk.socrata(MASTER, select="max(:updated_at) as mx",
                       paginate=False, limit=1)[0]["mx"]
    print(f"\n  LIVE IN MASTER       {live:>12,}   (rows, duplicates included)")
    print(f"  dataset refreshed    {now}")
    print(f"  watermark            {last}")

    rows = bulk.socrata(MASTER, where=f":updated_at > '{last}'",
                        select="document_id", paginate=True)
    arrived = {r["document_id"] for r in rows}
    new = sorted(arrived - mapped)
    print(f"\n  touched since watermark {len(arrived):>9,} distinct documents")
    print(f"  OF THOSE, UNMAPPED      {len(new):>9,}")
    for d in new[:40]:
        print(f"      {d}")
    if len(new) > 40:
        print(f"      ... and {len(new)-40:,} more")

    total_gap = sorted(set(missing) | set(new))
    print(f"\n  ── TOTAL WORK OUTSTANDING: {len(total_gap):,} documents ──")
    print(f"  ({time.time()-t0:.0f}s)")

    if total_gap:
        pathlib.Path("_gap.json").write_text(json.dumps(total_gap, indent=1))
        print("  written to _gap.json")


if __name__ == "__main__":
    main()
