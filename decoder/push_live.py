"""Push the mapped delta to Supabase. ⚠ COMPLETE ROWS ONLY.

`document_map.no_image` is computed from `total_pages`, so pushing a bare id
asserts "ACRIS holds no image for this document" — a permanent claim about a
record nobody has looked at. Only documents the mapper has actually seen go up.

⚠ BATCH, DO NOT SEND ONE PAYLOAD. supabase_sync.push() 500s on ~12k rows in a
single request; 500 at a time with merge-duplicates is what works.
"""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import push_selection as PS
import supabase_sync as S


def iso(s):
    if not s:
        return None
    try:
        m, d, y = (int(x) for x in s.split()[0].split("/"))
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, IndexError):
        return None


def main():
    q = {}
    for l in (HERE / "_live_delta_queue.jsonl").open(encoding="utf-8"):
        r = json.loads(l)
        q[r["doc_id"]] = r
    rows = []
    for l in (HERE / "docmaps.jsonl").open(encoding="utf-8"):
        d = json.loads(l)
        i = d.get("doc_id")
        if i not in q:
            continue
        r = PS.row(d)
        # ⚠ amap records carry no doc_type/recorded_date; the queue does. Without
        # this they land NULL and the table silently loses two columns.
        r["doc_type"] = q[i].get("doc_type")
        r["recorded_date"] = iso(q[i].get("recorded"))
        rows.append(r)
    print(f"  upserting {len(rows):,} complete rows")
    url, key = S._env()
    H = {"apikey": key, "Authorization": "Bearer " + key,
         "Content-Type": "application/json",
         "Prefer": "resolution=merge-duplicates,return=minimal"}
    ok = 0
    for i in range(0, len(rows), 500):
        b = rows[i:i + 500]
        rq = urllib.request.Request(
            f"{url}/rest/v1/document_map?on_conflict=document_id",
            data=json.dumps(b).encode(), headers=H)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(rq, timeout=120):
                    ok += len(b)
                break
            except urllib.error.HTTPError as e:
                if attempt == 2:
                    print(f"    ⚠ batch at {i} failed HTTP {e.code}")
                else:
                    time.sleep(2)
    print(f"  upserted {ok:,}/{len(rows):,}")
    if ok != len(rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
