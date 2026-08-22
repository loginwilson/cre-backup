"""WORKFLOW -> SUPABASE. The pipeline's own memory, made queryable.

    python push_workflow.py              # upsert workflow.json into Supabase
    python push_workflow.py --show       # print what would be pushed

⚠ RUN workflow_ddl.sql IN THE SUPABASE SQL EDITOR FIRST. PostgREST cannot create
tables, so this script cannot bootstrap itself. If the tables are missing it says
so plainly rather than reporting a successful push of nothing.

⚠ WHY THIS EXISTS. Several rules in workflow.json were learned TWICE because the
first learning lived only in a chat log - the trust gate's real recall, the
per-page escalation bill, the difference between a page an engine never produced
and a page it scored zero on. A rule that is not queryable is a rule that will be
rediscovered at full price.

⚠ IDEMPOTENT ON (stage, kind, title). Re-running merges over itself. The local
workflow.json stays the source of truth and Supabase is the read surface - same
split as the JSONL sink and decoder_facts.
"""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import supabase_sync as S

HERE = pathlib.Path(__file__).parent
SRC = HERE / "workflow.json"


def post(url, key, table, rows, conflict):
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{table}?on_conflict={conflict}",
        data=json.dumps(rows).encode(), method="POST",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates,return=minimal"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode("utf-8", "replace")


def count(url, key, table):
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{table}?limit=1",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Prefer": "count=exact", "Range": "0-0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return int(r.headers.get("Content-Range", "0/0").split("/")[-1])
    except urllib.error.HTTPError as e:
        return -1 if e.code == 404 else -2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    doc = json.loads(SRC.read_text(encoding="utf-8"))
    stages = doc["stages"]
    # ⚠ EVERY OBJECT IN A BULK INSERT MUST CARRY IDENTICAL KEYS. PostgREST
    # rejects the whole batch with PGRST102 "All object keys must match" if one
    # entry omits an optional field - and most entries have no `numbers`. Fill
    # the full column set explicitly rather than letting presence vary; a
    # missing key is not the same as a null and only one of them posts.
    COLS = ("stage", "kind", "title", "body", "numbers", "measured_on",
            "status", "supersedes", "seq")
    entries = [{c: e.get(c, "active" if c == "status" else None) for c in COLS}
               for e in doc["entries"]]

    print(f"  {len(stages)} stages · {len(entries)} workflow entries")
    by = {}
    for e in entries:
        by[e["stage"]] = by.get(e["stage"], 0) + 1
    for s in stages:
        print(f"    {s['seq']}. {s['stage']:<12} {by.get(s['stage'],0):>2} entries   "
              f"[{s['state']}]")
    print(f"    {'global':<15} {by.get('global',0):>2} entries")
    if a.show:
        return

    url, key = S._env()
    for t in ("decoder_stage", "decoder_workflow"):
        if count(url, key, t) == -1:
            print(f"\n  ⚠ TABLE {t} DOES NOT EXIST.")
            print(f"  Run workflow_ddl.sql in the Supabase SQL editor first:")
            print(f"    {HERE / 'workflow_ddl.sql'}")
            print(f"  Nothing was pushed.")
            return

    st, err = post(url, key, "decoder_stage", stages, "stage")
    print(f"\n  decoder_stage    HTTP {st} {err}")
    st, err = post(url, key, "decoder_workflow", entries, "stage,kind,title")
    print(f"  decoder_workflow HTTP {st} {err}")

    print(f"\n  decoder_stage    now holds {count(url,key,'decoder_stage'):,} rows")
    print(f"  decoder_workflow now holds {count(url,key,'decoder_workflow'):,} rows")


if __name__ == "__main__":
    main()
