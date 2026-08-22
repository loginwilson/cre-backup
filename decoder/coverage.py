"""IS ANYTHING BEING MISSED? — scored against the SPECIFICATION, never against the walk.

    ACRIS_CORPUS_ROOT=D:/acris python coverage.py

⚠ THE TRAP THIS EXISTS TO CLOSE. `_track.py` counts `_INDEX.md` folders and reports
"parcels complete". Every folder it reads was created by the walk, so a parcel the walk
never SELECTED cannot appear in its denominator — it would report 100% complete while
28.6% of parcels had never been looked at. An audit that reads the filter's own output
can only ever confirm the filter.

⚠ SO THE DENOMINATOR IS `parcel_spec.db`, which was built from the ACRIS index and knows
about every parcel and every document whether or not we ever chose to walk it.

⚠ AND EXCLUSION IS REPORTED AS A NUMBER, NOT AS A SETTING. `--lo 8 --hi 300` is invisible
in a log line; "357,749 parcels can never be reached under the current config" is not.
A band that is out of scope on purpose still has to be COUNTED, or "we'll get to it later"
quietly becomes "we never did".

Three verdicts, borrowed from acris_scope.py because the distinction is the same one:
    ACCOUNTED    fetched, or proven image-less (the index row IS the record)
    OUTSTANDING  in scope, simply not reached yet — time closes this
    UNREACHABLE  in the corpus, excluded by the current config — ONLY A DECISION closes this
"""
from __future__ import annotations

import os, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

# the band the walk is currently configured for — keep in step with pull.py DEFAULT
LO, HI = 1, 300


def main(orphans=False):
    spec = sqlite3.connect(f"file:{CP.SPEC/'parcel_spec.db'}?mode=ro", uri=True)
    led = sqlite3.connect(f"file:{CP.LEDGER}?mode=ro", uri=True)

    docs = spec.execute("SELECT COUNT(*) FROM document").fetchone()[0]
    parcels = spec.execute("SELECT COUNT(*) FROM parcel").fetchone()[0]
    st = dict(led.execute("SELECT status, COUNT(*) FROM doc GROUP BY status"))
    ok, empty = st.get("ok", 0), st.get("empty", 0)
    accounted = ok + empty

    print(f"\n  SPECIFICATION   {parcels:,} parcels · {docs:,} documents  <- the denominator\n")
    print(f"  ACCOUNTED       {accounted:,}  ({100*accounted/docs:.2f}%)")
    print(f"      fetched     {ok:,}")
    print(f"      image-less  {empty:,}   (index row is the whole record — not a gap)")
    print(f"  NOT YET HELD    {docs-accounted:,}  ({100*(docs-accounted)/docs:.2f}%)\n")

    # ⚠ ORPHANS ARE NOT BACKLOG — SEPARATE THEM OR THEY HIDE FOREVER.
    # Acquisition reaches a document ONLY via parcel -> parcel_document -> document.
    # A document with no parcel link cannot be fetched by any amount of running, yet it
    # sits in NOT YET HELD looking exactly like work not started. Counting it is the
    # difference between "we are 3% done" and "3% done, and 0.2% is unreachable".
    # ⚠ EXACT, NOT SAMPLED. Sampling gave 0/1,199 at random but 6/3,000 in the early
    # rows on 2026-08-18 — orphans CLUSTER, so no sample can bound them.
    if orphans:
        n = spec.execute("SELECT COUNT(*) FROM document d WHERE NOT EXISTS "
                         "(SELECT 1 FROM parcel_document pd "
                         "WHERE pd.document_id = d.document_id)").fetchone()[0]
        print(f"  * ORPHANS       {n:,}  ({100*n/docs:.3f}%) — no parcel link, "
              "UNREACHABLE by the walk")
        print("      these never close by running longer")
        print()

    # ── where the un-held documents live, so exclusion is a number and not a setting
    bands = [("index-only", 0, 0), (f"1-{LO-1}  BELOW lo", 1, LO-1),
             (f"{LO}-{HI}  IN BAND", LO, HI), (f"{HI+1}+  ABOVE hi", HI+1, 10**9)]
    print(f"  {'band':<20}{'parcels':>12}{'doc-links':>14}{'% links':>10}  verdict")
    tl = spec.execute("SELECT COALESCE(SUM(n_docs),0) FROM parcel").fetchone()[0]
    unreach_p = unreach_l = 0
    for lab, lo, hi in bands:
        n, d = spec.execute(
            "SELECT COUNT(*), COALESCE(SUM(n_docs),0) FROM parcel WHERE n_docs BETWEEN ? AND ?",
            (lo, hi)).fetchone()
        if n == 0:
            continue
        inscope = (lo >= LO and hi <= HI)
        verdict = "OUTSTANDING (time)" if inscope else "⚠ UNREACHABLE (decision)"
        if not inscope:
            unreach_p += n; unreach_l += d
        print(f"  {lab:<20}{n:>12,}{d:>14,}{100*d/tl:>9.1f}%  {verdict}")

    print(f"\n  ⚠ UNREACHABLE UNDER CURRENT CONFIG (--lo {LO} --hi {HI}):")
    print(f"      {unreach_p:,} parcels ({100*unreach_p/parcels:.1f}% of all parcels)")
    print(f"      {unreach_l:,} doc-links ({100*unreach_l/tl:.1f}% of all links)")
    print("      These do NOT close by running longer. They close by widening the band.")
    print("\n  ⚠ doc-links double-count documents shared by several parcels "
          f"({tl:,} links over {docs:,} documents).\n")


if __name__ == "__main__":
    # * --orphans is a FULL 17M-row NOT EXISTS scan. Run it against a
    # paused walk; it competes with the workers for the same USB drive.
    main(orphans="--orphans" in sys.argv)
