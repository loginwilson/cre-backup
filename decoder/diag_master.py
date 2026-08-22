"""Which master rows did the partitioned pull miss, and do they share a shape?

⚠ A SHORTFALL WITH NO PATTERN IS A DIFFERENT BUG FROM ONE WITH A PATTERN. If the
missing ids cluster at partition boundaries the tiling is wrong; if they cluster
by era the range comparison is wrong; if they are scattered the loss is
transport, not logic. Reporting "23,016 short" without which 23,016 is a number,
not a finding.
"""
import collections, gzip, json, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent

got = collections.Counter()
with gzip.open(HERE / "index_full" / "master.jsonl.gz", "rb") as f:
    for line in f:
        try:
            got[json.loads(line)["document_id"]] += 1
        except Exception:
            pass
print(f"  pulled file: {sum(got.values()):,} rows · {len(got):,} distinct ids")
dupes = sum(v - 1 for v in got.values() if v > 1)
print(f"  duplicate rows inside the file: {dupes:,}")

have = set()
with open(HERE / "acris_ids.jsonl", encoding="utf-8", errors="replace") as f:
    for line in f:
        i = line.find('"document_id":')
        if i < 0:
            continue
        j = line.find('"', i + 14); k = line.find('"', j + 1)
        if j > 0 and k > 0:
            have.add(line[j + 1:k])
print(f"  local id list: {len(have):,} ids")

missing = have - set(got)
extra = set(got) - have
print(f"\n  in local list, NOT in pulled file: {len(missing):,}")
print(f"  in pulled file, not in local list: {len(extra):,}")
if missing:
    by_era = collections.Counter(d[:4] for d in missing)
    print(f"  missing by era prefix (top 12): {dict(by_era.most_common(12))}")
    print(f"  examples: {sorted(missing)[:6]}")
    (HERE / "_master_missing.txt").write_text("\n".join(sorted(missing)),
                                              encoding="utf-8")
    print(f"  -> _master_missing.txt")
