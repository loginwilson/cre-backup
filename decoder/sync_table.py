"""THE DATED SYNC TABLE — the artifact §1 of the Synchronization md requires.

    python sync_table.py                 re-read live state, write the table
    python sync_table.py --no-probe      use the last recorded reads (offline)

⚠ THIS ARTIFACT DID NOT EXIST UNTIL 2026-08-20. The md has specified it since it
was written - "One dated table per run", named for the gap it closed, carrying
both balances and the delta ids - and nothing ever produced one. The folder held
the md and nothing else. Every run's delta lived only as text in a rotating log,
so there was no morning report, no audit trail, and no dated proof the map was
ever level.

WHAT IT IS AND IS NOT (md §1, settled 2026-08-19):
    the HANDOFF is the specification DATABASE - nav_build reads that.
    this TABLE is the MORNING REPORT and the audit trail. It is not parsed.
Writing it does not move data; it records what a run measured.

THE TWO BALANCES:
    ids    - MEASURED here. This phase's own check. Must read 0 to finalize.
    images - READ from the map. Tomorrow's expected flips, not outstanding work.
             Only a number that GROWS across runs is a finding.

⚠ SCOPE DIFFERS PER CUSTODIAN, DELIBERATELY. ACRIS has a dense counter so its
row is corpus-wide. Richmond has no counter, so its row is WINDOW-scoped and its
corpus-wide level is implied by induction - every window since the backfill has
zeroed. Do not "fix" Richmond's row to look like ACRIS's; the asymmetry is the
honest shape of two different custodians.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

OUT_DIR = pathlib.Path("D:/CRE Decoding System/00 Synchronizations"
                       "/Legal Instruments Synchronization")
RUN_LOG = OUT_DIR / "_run_stamps.tsv"
RC_DELTA = CP.INDEX / "rc_delta.jsonl"
CEILING = HERE / "_socrata_ceiling.json"
EDGE = HERE / "_crfn_edge.json"


def _run(script, args=()):
    """Run a probe and return its stdout. Never raises - a probe that fails
    leaves the field unknown, and 'unknown' must be visible in the table rather
    than silently rendered as a number."""
    try:
        p = subprocess.run([sys.executable, "-u", str(HERE / script), *args],
                           capture_output=True, text=True, timeout=900,
                           encoding="utf-8", errors="replace")
        return (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return f"PROBE FAILED: {type(e).__name__}: {e}"


def _num(text, pattern):
    m = re.search(pattern, text)
    return int(m.group(1).replace(",", "")) if m else None


def acris_row(probe):
    """Corpus-wide. live state is the CRFN counter; current specification is
    counted from the map."""
    out = _run("crfn_monitor.py") if probe else ""
    held = _num(out, r"highest landed crfn\s+([\d,]+)")
    edge = _num(out, r"live edge crfn\s+([\d,]+)")
    span = _num(out, r"span outstanding\s+([\d,]+)")
    if held is None and EDGE.exists():
        edge = json.loads(EDGE.read_text(encoding="utf-8")).get("edge")
    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    # ⚠ ACRIS IS THREE ID FAMILIES, NOT ONE. Modern numeric ids are only
    # 11.6M of it; FT_ (microfilm) and BK_ (book/page) are ACRIS too. Counting
    # GLOB '[0-9]*' reported 11,576,139 as "current specification" and put it
    # beside a CRFN as "live state" - a document count against a recording
    # number, which is not a comparison at all. ACRIS = everything that is not
    # Richmond.
    spec = con.execute("SELECT COUNT(*) FROM document "
                       "WHERE document_id NOT LIKE 'RC_%'").fetchone()[0]
    con.close()
    return {"custodian": "ACRIS", "scope": "corpus", "spec": spec,
            "live": None, "edge": edge, "held": held, "delta": span, "raw": out}


def richmond_row(probe):
    """WINDOW-scoped, and its completeness is proven by ARITHMETIC (instrument
    density), not by trusting the server's row count."""
    out = _run("rc_daily.py") if probe else ""
    win = _num(out, r"window returned ([\d,]+) documents")
    held = _num(out, r"already held ([\d,]+)")
    new = _num(out, r"NEW ([\d,]+)")
    missing = _num(out, r"missing (\d+)")
    m = re.search(r"window ([\d-]+) \.\. ([\d-]+)", out)
    return {"custodian": "RICHMOND", "scope": "window", "spec": held,
            "live": win, "delta": new, "density_missing": missing,
            "window": (m.group(1), m.group(2)) if m else None, "raw": out}


ROUTINE_LOG = HERE / "_routine_4am_run.log"


def run_deltas():
    """⚠ THE `delta` COLUMN IS WHAT THE RUN STAGED; THE `ids` BALANCE IS THE
    FINAL RE-READ. The md's own example shows both at once - delta 1,588 in the
    column, `balances: ids 0` underneath - because a run that fetched 1,588
    documents and then proved itself level is the thing worth recording. The
    first version of this file re-read live state and wrote the resulting ZERO
    into the delta column, which erased the run's entire work and made every
    table look like a day nothing was filed.

    So the column is parsed from the run the routine just finished."""
    if not ROUTINE_LOG.exists():
        return None, None
    txt = ROUTINE_LOG.read_text(encoding="utf-8", errors="replace")
    block = txt.rsplit("DAILY ROUTINE", 1)[-1]
    a = re.search(r"DONE ([\d,]+) documents", block)
    r = re.search(r"fetched ([\d,]+) \u00b7 \d+ errors", block)
    if r is None:
        r = re.search(r"fetched ([\d,]+)", block)
    return (int(a.group(1).replace(",", "")) if a else None,
            int(r.group(1).replace(",", "")) if r else None)


def images_balance():
    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    d = dict(con.execute("SELECT image_state, COUNT(*) FROM document "
                         "WHERE image_state IS NOT NULL GROUP BY image_state"))
    con.close()
    return d


def acris_delta_ids(baseline, edge):
    """⚠ THE CRFN SPAN, STATED AS A SPAN. The walk enumerates
    (baseline, edge] minus what it already holds. Writing 1,204 individual
    numbers that are simply consecutive would be noise pretending to be
    evidence, so the block states the range and its count - and says plainly
    that holes BELOW the baseline are NOT covered by it."""
    if baseline is None or edge is None:
        return None, None
    return (baseline + 1, edge), edge - baseline


def richmond_delta_ids(window):
    """internal_ids recorded inside the window, from the delta jsonl."""
    if not RC_DELTA.exists() or not window:
        return []
    lo, hi = window
    ids = []
    for line in RC_DELTA.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        rec = (r.get("recorded") or "").strip()
        try:
            mm, dd, yy = rec.split("/")
            iso = f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
        except Exception:
            continue
        if lo <= iso <= hi and r.get("internal_id"):
            ids.append(f"RC_{r['internal_id']}")
    return sorted(set(ids))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-probe", action="store_true")
    ap.add_argument("--last-level", help="ISO date the map was last level")
    a = ap.parse_args()
    probe = not a.no_probe

    print("re-reading live state (md §3: the custodian keeps recording "
          "while we walk)...")
    ac = acris_row(probe)
    rc = richmond_row(probe)
    img = images_balance()
    ac_run, rc_run = run_deltas()

    base = json.loads(CEILING.read_text(encoding="utf-8")).get("ceiling") \
        if CEILING.exists() else None
    # the baseline the run STARTED from is one span below the current ceiling
    # ⚠ the run's span, reconstructed: the ceiling has ALREADY been advanced
    # to the edge by the time this runs, so (ceiling - run_delta, ceiling] is
    # the span the walk actually covered. Using the current ceiling as the
    # baseline produced "2026000235037 .. 2026000235036 (0 numbers)" - a range
    # that runs backwards, printed without complaint.
    _edge = ac.get("edge")
    span_ids, span_n = acris_delta_ids(
        (_edge - ac_run) if (_edge is not None and ac_run) else None, _edge)
    rc_ids = richmond_delta_ids(rc.get("window"))

    ids_balance = (ac.get("delta") or 0) + (rc.get("delta") or 0)
    finalized = ids_balance == 0 and ac.get("delta") is not None \
        and rc.get("delta") is not None
    today = dt.date.today().isoformat()
    last = a.last_level or "2026-08-19"
    name = f"{last} to {today}.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / name

    L = []
    L.append(f"# SYNCHRONIZATION — {last} to {today}")
    L.append("")
    L.append(f"**{'FINALIZED' if finalized else '⚠ STAGED — NOT HANDED OFF'}** · "
             f"written {dt.datetime.now():%Y-%m-%d %H:%M}")
    L.append("")
    L.append("    custodian | current specification | live state | delta | delta doc ids")
    L.append("    ----------|----------------------|------------|-------|--------------")
    # current specification = what the map holds NOW (after this run landed).
    # live state = what the custodian had when the run read it = spec, since the
    # re-read proved span 0. delta = what THIS RUN staged and landed.
    ac_before = ac['spec'] - (ac_run or 0)
    L.append(f"    ACRIS     | {ac_before:>20,} | {ac['spec']:>10,} "
             f"| {ac_run if ac_run is not None else '?':>5} | see id block")
    rcs = f"{(rc['spec'] or 0) - (rc_run or 0):,} (in window)"
    rcl = f"{rc['live']:,} (window)" if rc['live'] is not None else "?"
    L.append(f"    RICHMOND  | {rcs:>20} | {rcl:>10} "
             f"| {rc_run if rc_run is not None else '?':>5} | see id block")
    L.append("")
    # TOTAL row (login 2026-08-20): the custodian deltas summed, for the
    # one-glance read. ONLY the delta column totals - spec/live scopes differ
    # (ACRIS corpus-wide vs Richmond window); summing them would compare a
    # census to a keyhole. First insertion of this row matched the WRONG
    # 'balances' - the docstring's example - and sat invisibly inside a string
    # literal printing nothing: anchor on code, never on prose that quotes it.
    _tot = (ac_run or 0) + (rc_run or 0)
    L.append(f"    TOTAL     | {'':>21} | {'':>10} | {_tot:>5} | new doc ids this run")
    L.append("")
    L.append(f"    balances: ids {ids_balance} (the gate)")
    L.append(f"              images {img.get('pending', 0):,} pending "
             f"({img.get('present', 0):,} present · "
             f"{img.get('imageless', 0):,} imageless)")
    L.append("")
    L.append("**ACRIS is corpus-wide** (it has a counter). **Richmond is "
             "window-scoped** (it has none); its corpus-wide level is implied by "
             "induction — every window since the backfill has zeroed.")
    L.append("")
    if rc.get("density_missing") is not None:
        L.append(f"Richmond completeness is proven by ARITHMETIC: instrument "
                 f"density missing **{rc['density_missing']}**. A zero-row "
                 f"window is never believed without re-asking a 1-day range.")
        L.append("")
    L.append("## Delta doc ids")
    L.append("")
    L.append("⚠ AUDIT ONLY. The handoff is the specification database "
             "(md §1, settled 2026-08-19); `nav_build.py` reads it directly. "
             "These blocks are for a human to spot-check.")
    L.append("")
    L.append("```acris-delta")
    if span_ids and span_n and span_n > 0:
        L.append(f"crfn {span_ids[0]} .. {span_ids[1]}   ({span_n:,} numbers)")
        L.append("# stated as a SPAN: the walk enumerates (baseline, edge] minus")
        L.append("# what it holds. Listing consecutive numbers individually would")
        L.append("# be noise pretending to be evidence.")
    else:
        L.append("# baseline or edge unavailable — span not stated")
    L.append("```")
    L.append("")
    L.append("```richmond-delta")
    L.append(f"# {len(rc_ids):,} ids recorded in the window")
    # ⚠ THE CAP AND ITS DECLARATION MUST LIVE IN ONE PLACE. This was
    # rc_ids[:200], with the notice ("... N more") written by a SEPARATE
    # `if len(rc_ids) > 200` several lines below and outside the branch. The
    # cap was therefore honestly declared - but the 200 was written twice, so
    # raising one and not the other on 2026-08-20 printed all 315 ids under a
    # line insisting 115 were missing. A number duplicated across two
    # statements is a lie waiting for the first person who edits one of them.
    # The bound is now a single name, and only the branch that truncates says
    # anything about truncation.
    RC_LIST_CAP = 2000
    if not rc_ids:
        L.append("# none new in window")
    else:
        L.extend(rc_ids[:RC_LIST_CAP])
        if len(rc_ids) > RC_LIST_CAP:
            L.append(f"# ... {len(rc_ids) - RC_LIST_CAP:,} FURTHER IDS NOT LISTED "
                     f"(of {len(rc_ids):,} total).")
            L.append("# This block is bounded for readability. The COMPLETE set")
            L.append("# is the specification database, which is the actual")
            L.append("# handoff; nothing downstream reads this block.")

    L.append("```")
    L.append("")
    L.append("## ⚠ WHAT THIS TABLE DOES NOT PROVE")
    L.append("")
    L.append("`span outstanding 0` is measured ABOVE the baseline. The gap is "
             "computed as `range(baseline+1, edge+1)`, so **holes BELOW the "
             "baseline are never examined** — and `document` stores no CRFN, so "
             "the map cannot answer which recording numbers it holds.")
    L.append("")
    L.append("Measured 2026-08-20: 2026 issued **235,036** CRFNs; the map holds "
             "**234,972** ACRIS documents recorded in 2026 — a difference of "
             "**64**, an upper bound (some issued numbers never resolve).")
    L.append("")
    L.append("Closing it needs `crfn` on `document`, then `held` computed from "
             "the map instead of `_live_delta_queue.jsonl` (which carries one "
             "month, not the year).")
    L.append("")

    p.write_text("\n".join(L), encoding="utf-8")

    stamp = (f"{dt.datetime.now():%Y-%m-%d %H:%M}\t"
             f"acris_run={ac_run}\trichmond_run={rc_run}\t"
             f"ids={ids_balance}\timages_pending={img.get('pending', 0)}\t"
             f"{'FINALIZED' if finalized else 'STAGED'}\n")
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(stamp)

    print(f"\nwrote {p}")
    print(f"  {'FINALIZED' if finalized else 'STAGED (not handed off)'}"
          f" · ids {ids_balance} · images {img.get('pending', 0):,} pending")
    return 0 if finalized else 1


if __name__ == "__main__":
    sys.exit(main())
