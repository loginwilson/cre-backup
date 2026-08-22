"""WHAT IS THE DENOMINATOR FOR "HOW MUCH OF ACRIS DO WE HAVE?" — measured once, cached.

    ACRIS_CORPUS_ROOT=D:/acris python denominators.py --build
    ACRIS_CORPUS_ROOT=D:/acris python denominators.py            # show the cache

⚠ WHY THIS EXISTS. Progress was being reported against three different numbers on the
same day — 17,049,742 (the real-property map), 21,611,511 (every ACRIS row in the spec),
and 19,856,842 (the rows a parcel walk can actually reach). The same 329,386 documents
read as 1.93%, 1.52% or 1.66% depending on which one you picked, and nothing in the code
said which was correct. A rate without its denominator is not a measurement.

⚠ THE ACQUISITION DENOMINATOR IS THE PARCEL-KEYED COUNT, NOT THE SPEC COUNT. Acquisition
walks BY PARCEL: it starts from a BBL and asks the spec what documents that BBL holds. A
document with no row in `parcel_document` can never be reached that way, however present
it is in the specification. Measured 2026-08-19: 1,754,669 ACRIS documents (8.1%) are
unkeyed, and 1,339,151 of those are microfilm-era `FT_`. Counting them in the denominator
makes the walk look permanently incomplete; leaving them out silently redefines the corpus.
Report BOTH, always.

⚠ THIS IS EXPENSIVE ON PURPOSE AND MUST NOT RUN INSIDE `--status`. The keyed count is a
full pass over ix_pd_doc (29.2M entries, ~394 s on the One Touch). A status command that
costs six minutes of USB I/O is one nobody runs, and worse, it contends with the walk it
is measuring — that contention alone dragged a healthy 87 pg/s run down to a reported 23.
Compute here, cache to JSON, read there.

⚠ THREE ACRIS ID CLASSES, NOT TWO. `FT_` film and `BK_` book are both microfilm-era and
they behave differently: BK_ is keyed 1,721,171 of 1,721,172 while FT_ is only 83.9%.
Folding BK_ into the CRFN bucket hides that entirely — it did, until 2026-08-19.
"""
from __future__ import annotations

import argparse, datetime, json, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

CACHE = CP.STATE / "denominators.json"

# ⚠ AN ESTIMATE, AND LABELLED AS ONE. Page totals come from page_counts.db where known;
# this is the projection used for the drive sizing (148.2M pages / 9.3-10.2 TB). Never
# print it without saying it is an estimate — a hard-looking number invites a false %.
PAGES_ESTIMATE = 148_200_000

CLS = ("case when substr(document_id,1,3)='RC_' then 'RC_' "
       "when substr(document_id,1,3)='FT_' then 'FT_' "
       "when substr(document_id,1,3)='BK_' then 'BK_' "
       "when document_id is null then '(NULL)' else 'CRFN' end")


def build():
    if not CP.SPEC_DB.exists():
        sys.exit(f"  no spec db at {CP.SPEC_DB}")
    c = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    out = {"measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "spec_db": str(CP.SPEC_DB), "pages_estimate": PAGES_ESTIMATE}
    t0 = time.time()

    print("  [1/4] spec documents by id class ...", flush=True)
    t = time.time()
    out["spec_by_class"] = {k: n for k, n in
                            c.execute(f"select {CLS}, count(*) from document group by 1")}
    # ⚠ COUNT(*) SEPARATELY AND COMPARE. A row whose id matches no prefix vanishes from
    # every bucket without raising anything: substr(NULL,1,3)='RC_' is NULL, not false,
    # so it fails every WHEN and lands nowhere. Found exactly one such row 2026-08-19 —
    # the class buckets summed to 24,037,915 while count(*) said 24,037,916.
    out["spec_total_rows"] = c.execute("select count(*) from document").fetchone()[0]
    out["spec_class_sum"] = sum(out["spec_by_class"].values())
    out["spec_unclassed"] = out["spec_total_rows"] - out["spec_class_sum"]
    print(f"        {out['spec_total_rows']:,} rows, {time.time()-t:.0f}s "
          f"(unclassed: {out['spec_unclassed']})", flush=True)

    print("  [2/4] distinct documents keyed to a parcel ...", flush=True)
    t = time.time()
    out["keyed_by_class"] = {k: n for k, n in c.execute(
        f"select {CLS}, count(distinct document_id) from parcel_document group by 1")}
    print(f"        {sum(out['keyed_by_class'].values()):,} keyed, {time.time()-t:.0f}s",
          flush=True)

    print("  [3/4] parcels ...", flush=True)
    t = time.time()
    out["parcels_in_spec"] = c.execute("select count(*) from parcel").fetchone()[0]
    # ⚠ THE PARCEL DENOMINATOR IS NOT `count(*) FROM parcel`. Acquisition can only ever
    # complete a parcel that holds at least one ACRIS document; a Richmond-only parcel is
    # not incomplete work for this job, it is another job's work. Counting all 1,346,101
    # would make the ACRIS walk permanently unfinishable by construction.
    out["parcels_with_acris"] = c.execute(
        "select count(distinct bbl) from parcel_document "
        "where substr(document_id,1,3) <> 'RC_'").fetchone()[0]
    print(f"        {out['parcels_in_spec']:,} in spec · "
          f"{out['parcels_with_acris']:,} hold >=1 ACRIS doc, {time.time()-t:.0f}s",
          flush=True)

    print("  [4/4] derived ...", flush=True)
    acris = ("CRFN", "FT_", "BK_")
    out["acris_spec"] = sum(out["spec_by_class"].get(k, 0) for k in acris)
    out["acris_keyed"] = sum(out["keyed_by_class"].get(k, 0) for k in acris)
    out["acris_unkeyed"] = out["acris_spec"] - out["acris_keyed"]
    out["richmond_spec"] = out["spec_by_class"].get("RC_", 0)
    out["richmond_keyed"] = out["keyed_by_class"].get("RC_", 0)
    out["build_secs"] = round(time.time() - t0, 1)
    c.close()

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  -> {CACHE}  ({out['build_secs']}s)")
    return out


def load():
    if not CACHE.exists():
        return None
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except ValueError:
        return None


def show(d=None):
    d = d or load()
    if not d:
        sys.exit("  no cache — run: python denominators.py --build")
    print(f"  measured {d['measured_at']}  ({d.get('build_secs','?')}s)")
    print()
    print("  class      spec rows   parcel-keyed      unkeyed   coverage")
    for k in ("CRFN", "FT_", "BK_", "RC_"):
        s = d["spec_by_class"].get(k, 0)
        kk = d["keyed_by_class"].get(k, 0)
        print(f"  {k:<8} {s:11,} {kk:14,} {s-kk:12,}   {100.0*kk/s if s else 0:6.2f}%")
    print(f"  {'TOTAL':<8} {d['spec_class_sum']:11,} "
          f"{sum(d['keyed_by_class'].values()):14,} "
          f"{d['spec_class_sum']-sum(d['keyed_by_class'].values()):12,}")
    if d.get("spec_unclassed"):
        print(f"  ⚠ {d['spec_unclassed']} row(s) match NO id class — not in any bucket above")
    print()
    print(f"  ACRIS spec              {d['acris_spec']:,}")
    print(f"  ACRIS parcel-keyed      {d['acris_keyed']:,}   <- ACQUISITION DENOMINATOR")
    print(f"  ACRIS unkeyed           {d['acris_unkeyed']:,}   <- unreachable by a parcel walk")
    print(f"  parcels with ACRIS doc  {d['parcels_with_acris']:,}   <- PARCEL DENOMINATOR")
    print(f"  pages (ESTIMATE)        {d['pages_estimate']:,}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    CP.ensure()
    show(build() if a.build else None)
