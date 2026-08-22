"""PERSONAL PROPERTY — pull ALL FIVE index components from Socrata.

    ACRIS_CORPUS_ROOT=D:/acris python pp_pull_all.py

⚠ THIS IS 21% OF THE REGISTER AND WE HELD NONE OF IT. Real property is 17.06M of
a 21.61M register; the other 4.55M is here. Socrata publishes all five components,
so this is a DOWNLOAD, not a crawl — no ACRIS contact, no trip risk.

⚠ COUNT FIRST, ASSERT AFTER. A short pull looks identical to a complete one on
disk. Every dataset's count(1) is recorded BEFORE the pull and the landed row
count must match it. Socrata's own count is the only denominator that is not
derived from our own output.

⚠ $offset WITHOUT $order SILENTLY DROPS AND DUPLICATES ROWS while COUNT stays
correct. pull_index_fast handles this ($order=document_id across partitions,
$order=:id within one document). Do not reimplement paging here.

⚠ 62.4% of these documents carry a REAL bbl (2,837,150 of 4,547,264) and will
attach to parcels we ALREADY HOLD. That changes parcel.n_docs, which acquisition
FILTERS AND RANKS ON — so landing this reopens parcels that currently look
complete. It is a specification-wide change, not an append.
"""
from __future__ import annotations
import json, pathlib, sys, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pull_index_fast as P

P.STATE = HERE / "_pp_all_state.json"

SETS = [("personal_master",     "sv7x-dduq"),
        ("personal_legals",     "uqqa-hym2"),
        ("personal_parties",    "nbbg-wtuz"),
        ("personal_references", "6y3e-jcrc"),
        ("personal_remarks",    "fuzi-5ks9")]


def live_count(ds):
    u = (f"https://data.cityofnewyork.us/resource/{ds}.json?"
         + urllib.parse.urlencode({"$select": "count(1)"}))
    return int(list(json.load(urllib.request.urlopen(u, timeout=180))[0].values())[0])


def main():
    if not P.STATE.exists():
        P.STATE.write_text("{}", encoding="utf-8")
    print("ACRIS PERSONAL PROPERTY — all five components\n")
    expect = {}
    for name, ds in SETS:
        expect[name] = live_count(ds)
        print(f"  {name:<22} {ds}  expect {expect[name]:>12,}")
    (HERE / "_pp_expected.json").write_text(json.dumps(expect, indent=1),
                                            encoding="utf-8")
    print()
    t0 = time.time()
    for name, ds in SETS:
        st = json.loads(P.STATE.read_text(encoding="utf-8"))
        print(f"\n=== {name} ({ds}) — expect {expect[name]:,} ===")
        s = time.time()
        try:
            P.pull(name, ds, st)
        except Exception as e:
            print(f"  ⚠ {name} FAILED: {type(e).__name__}: {e}")
            continue
        print(f"  {name} done in {(time.time()-s)/60:.1f}m")
    print(f"\n  ALL PULLS {(time.time()-t0)/60:.1f} minutes")
    print("\n  ── ACCEPTANCE: landed vs Socrata's own count ──")
    import gzip
    bad = 0
    for name, _ in SETS:
        f = P.OUTDIR / f"{name}.jsonl.gz"
        if not f.exists():
            print(f"  {name:<22} MISSING"); bad += 1; continue
        n = sum(1 for _ in gzip.open(f, "rt", encoding="utf-8"))
        ok = n == expect[name]
        if not ok:
            bad += 1
        print(f"  {name:<22} {n:>12,} / {expect[name]:>12,}  "
              f"{'PASS' if ok else f'FAIL ({n-expect[name]:+,})'}")
    print(f"\n  {'ALL FIVE COMPLETE' if not bad else f'⚠ {bad} INCOMPLETE'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
