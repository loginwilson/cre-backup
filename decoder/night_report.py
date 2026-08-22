"""WHAT THE NIGHT ACTUALLY PRODUCED — computed from the artifacts, never from memory.

    ACRIS_CORPUS_ROOT=D:/acris python night_report.py

⚠ SAME RULE AS status.py: every number is read from the file the job itself wrote — the
ledger, the spec index, the folders on disk. A report transcribed from what I remember
doing starts drifting the moment it is written, and a drifted report is worse than none
because it is trusted. If a number here is wrong, the artifact is wrong.

⚠ IT REPORTS SHORTFALL, NOT JUST OUTPUT. A run that fetched a great deal and left every
parcel half-built is a bad night, and a summary that leads with the page count would
hide that. Completeness comes first.
"""
from __future__ import annotations

import os, pathlib, re, sqlite3, sys, datetime, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
ROOT = CP.ROOT
SPEC = CP.SPEC_DB
LED = CP.LEDGER
BYP = CP.BYPARCEL
STORE = CP.STORE


def main():
    print(f"  ACRIS OVERNIGHT WALK — {datetime.datetime.now():%Y-%m-%d %H:%M}\n")

    # ── the ledger: what was fetched
    if LED.exists():
        c = sqlite3.connect(f"file:{LED}?mode=ro", uri=True)
        st = dict(c.execute("SELECT status, COUNT(*) FROM doc GROUP BY status"))
        ok, pg, by = c.execute(
            "SELECT COUNT(*), COALESCE(SUM(got),0), COALESCE(SUM(bytes),0) "
            "FROM doc WHERE status='ok'").fetchone()
        cls = list(c.execute("SELECT cls, COUNT(*), COALESCE(SUM(got),0) FROM doc "
                             "WHERE status='ok' GROUP BY cls ORDER BY 3 DESC"))
        c.close()
        print(f"  DOCUMENTS  {ok:,} complete · {pg:,} pages · {by/1e9:.1f} GB fetched")
        for k, n, p in cls:
            print(f"      {k:<9} {n:>8,} docs  {p:>10,} pages")
        # ⚠ `empty` is a FINDING, not a failure: the document has no image and the index
        # row is its whole record. It belongs in the report as a discovery.
        print(f"      image-less discovered (absent from noimage_index): "
              f"{st.get('empty',0):,}")
        if st.get("short"):
            print(f"      ⚠ short (fewer pages than expected): {st['short']:,}")
    else:
        print("  no ledger — nothing was fetched")
        return

    # ── the folders: what is readable
    comp = part = 0
    spec_docs = linked = 0
    worst = []
    for f in BYP.rglob("_INDEX.md"):
        t = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*(\d+) documents\*\*", t)
        if not m:
            continue
        tot = int(m.group(1)); spec_docs += tot
        na = t.count("| not acquired |")
        linked += len(list(f.parent.glob("*.pdf")))
        if na:
            part += 1; worst.append((na, tot, f.parent))
        else:
            comp += 1
    tot_p = comp + part
    print(f"\n  PARCELS    {tot_p:,} folders · {comp:,} COMPLETE · {part:,} partial")
    if tot_p:
        print(f"      {100*comp/tot_p:.0f}% of folders are a whole record, in order")
    print(f"      {spec_docs:,} documents named across them · {linked:,} PDFs linked in")
    if worst:
        print("      largest shortfalls:")
        for na, tot, d in sorted(worst, reverse=True)[:5]:
            print(f"        {na:>4} of {tot:>4} missing   {d.parent.name}/{d.name}")

    # ── lineage
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        import lineage
        lineage._load()
        n_ed = len(lineage._META)
        con = sqlite3.connect(SPEC)
        acris = {r[0] for r in con.execute("SELECT bbl FROM parcel")}
        con.close()
        retired = len(acris & set(lineage._FWD))
        print(f"\n  LINEAGE    {n_ed:,} published DOF edges")
        print(f"      {len(acris):,} BBLs named · {retired:,} retired · "
              f"{len(acris)-retired:,} lineage-aware parcels")
    except Exception as e:
        print(f"\n  LINEAGE    unavailable ({e})")

    # ── the run itself
    log = CP.log("overnight")
    if log.exists():
        lines = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
                 if "pg/s avg" in l]
        if lines:
            print(f"\n  RATE       last: {lines[-1].strip()}")
    stop = CP.STOP
    print(f"\n  REFUSALS   {'⚠ STOPPED — ' + stop.read_text(encoding='utf-8') if stop.exists() else 'none — ACRIS never refused'}")
    print(f"  DISK       {sum(f.stat().st_size for f in STORE.rglob('*.pdf'))/1e9:.1f} GB in the store"
          if STORE.exists() else "")


if __name__ == "__main__":
    main()
