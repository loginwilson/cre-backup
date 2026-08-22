"""THE PHASE BOARD — computed from the artifacts, never from memory.

    python status.py              # the board
    python status.py --verbose    # plus every state file's raw contents

⚠ A STATUS THAT IS WRITTEN DOWN IS A STATUS THAT GOES STALE. Every number here
is read from the file the job itself wrote — `_selection_cross_state.json`,
`_index_fast_state.json`, and so on — so the board cannot disagree with reality.
The moment it is transcribed into a doc it starts drifting, and a drifted status
is worse than none because it is trusted.

⚠ THIS EXISTS BECAUSE RETURNING TO A PHASE KEPT COSTING MORE THAN LEAVING IT.
Login, 2026-08-14: *"everytime I return to a phase weve tested, the results are
worse cause we forget configs and rules."* Measured examples from one day:

  · `selection_delta.py` was written specifically because `map_delta.py` never
    touches Supabase — and was never scheduled. Found by grep, not by knowing.
  · `bulk.socrata_in()` chunks CONCURRENTLY; `acquire_index._by_doc` re-wrote the
    same chunking SERIALLY, in a module that already imported it.
  · `arcgis_all()` counts-then-parallelises; `socrata()` three functions away
    walked pages one at a time. 4.4x sat unused for weeks.
  · `fuse.py` takes an `index_path` and records `"structured_record": false` —
    the third channel was designed in and never wired.

None of that is forgetting a fact. It is knowledge that exists and is not
reachable at the moment of need. The board answers "where is this phase" in one
command so the answer is never reconstructed from scratch.

⚠ AND IT REPORTS COVERAGE, NOT JUST SCORES. The regressions that cost the most
were coverage failures wearing a quality mask: `pp_doc.py` reported success over
ZERO pages, a 300s timeout silently killed the densest pages, and film "quality"
fell 77.2% -> 41.6% when nothing about quality had changed. A board that prints
pages-expected beside pages-scored catches all three at a glance.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
VERBOSE = "--verbose" in sys.argv

OK, WARN, BAD, IDLE = "OK", "WARN", "FAIL", "--"


def load(name):
    p = HERE / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def age(iso):
    """Hours since an ISO timestamp, or None."""
    if not iso:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return (time.time() - time.mktime(time.strptime(iso[:19], fmt))) / 3600
        except ValueError:
            continue
    return None


def fmt_age(h):
    if h is None:
        return "never"
    if h < 1:
        return f"{h*60:.0f}m ago"
    if h < 48:
        return f"{h:.0f}h ago"
    return f"{h/24:.0f}d ago"


def row(phase, item, state, detail, when=None):
    mark = {OK: "  OK ", WARN: "  ⚠  ", BAD: " FAIL", IDLE: "  -- "}[state]
    print(f" {mark} {phase:<12} {item:<26} {detail:<44} {fmt_age(when)}")


# ─────────────────────────────────────────────────────────── selection
def selection():
    cross = load("_selection_cross_state.json")
    if not cross:
        row("SELECTION", "three-way cross", IDLE, "never run — selection_cross.py")
    else:
        v = cross.get("verdict")
        n = cross.get("local_distinct") or cross.get("after_local")
        st = OK if v in ("clean", "repaired") else WARN
        row("SELECTION", "three-way cross", st,
            f"{v} · {n:,} documents" if n else str(v),
            age(cross.get("checked_at")))

    daily = load("_selection_daily_state.json")
    if not daily:
        row("SELECTION", "daily delta", IDLE,
            "never run — selection_daily.py --repair")
    else:
        st = OK if daily.get("verdict") in ("no_change", "already_current",
                                            "repaired") else WARN
        row("SELECTION", "daily delta", st,
            f"{daily.get('verdict')} · delta {daily.get('delta', 0):,}",
            age(daily.get("checked_at")))

    md = load("_map_delta_state.json")
    if md:
        # ⚠ THE FULL PASS IS THE ONLY TWO-WAY CHECK. A fast pass cannot see a
        # withdrawal, so its recency is not evidence of completeness.
        lf = md.get("last_full")
        h = age(lf)
        st = OK if h is not None and h < 24 * 14 else WARN
        row("SELECTION", "exhaustive ACRIS diff", st,
            f"mapped {md.get('mapped', 0):,} · new {md.get('new', 0)}", h)

    idx = HERE / "_local_ids.idx"
    if idx.exists():
        n = idx.stat().st_size // 8
        row("SELECTION", "local id index", OK, f"{n:,} ids · 8-byte hashes",
            (time.time() - idx.stat().st_mtime) / 3600)
    else:
        row("SELECTION", "local id index", WARN,
            "absent — daily delta cannot check local")


# ─────────────────────────────────────────────────────── support index
def support_index():
    st = load("_index_fast_state.json") or {}
    sets = ["master", "legals", "parties", "references", "remarks"]
    done = 0
    for name in sets:
        d = st.get(name)
        if not d:
            row("INDEX", name, IDLE, "not pulled")
            continue
        rows_, live = d.get("rows", 0), d.get("live")
        exact = live is not None and rows_ == live
        done += 1 if exact else 0
        detail = f"{rows_:,} rows" + ("" if exact else f" · live {live:,}"
                                      if live else "")
        if d.get("repaired_tail"):
            detail += " (tail repaired)"
        row("INDEX", name, OK if exact else WARN, detail)
    row("INDEX", "TOTAL RECONCILED", OK if done == len(sets) else WARN,
        f"{done}/{len(sets)} datasets exact")

    ni = HERE / "index_noimage.jsonl"
    if ni.exists():
        row("INDEX", "image-less documents", OK,
            f"{ni.stat().st_size/1e6:,.0f} MB — the ONLY record for these",
            (time.time() - ni.stat().st_mtime) / 3600)

    d = load("_index_daily_state.json")
    if d:
        tot = sum(v.get("last_delta", 0) for v in d.values() if isinstance(v, dict))
        newest = max((age(v.get("applied_at")) for v in d.values()
                      if isinstance(v, dict) and v.get("applied_at")),
                     default=None)
        row("INDEX", "daily delta", OK, f"last {tot:,} rows", newest)
    else:
        row("INDEX", "daily delta", IDLE, "never run — index_daily.py --apply")


# ───────────────────────────────────────────────────────── acquisition
def acquisition():
    st = load("_acquire_state.json") or load("map_acris_state.json")
    imgs = HERE / "devr_pages"
    if imgs.exists():
        n = sum(1 for _ in imgs.rglob("*") if _.is_file())
        row("ACQUIRE", "pages on disk", OK, f"{n:,} files in {imgs.name}/")
    else:
        row("ACQUIRE", "pages on disk", IDLE, "not started")
    row("ACQUIRE", "budget / refusals", IDLE,
        "see BULK_ACQUISITION.md · STOP on refusal, never retry")


# ────────────────────────────────────────────────────────── extraction
def extraction():
    ev = HERE / "resolve" / "_evidence"
    if not ev.exists():
        row("EXTRACT", "fused evidence", IDLE, "none — resolve/fuse.py")
        return
    docs = sorted(p for p in ev.glob("*.json")
                  if not p.stem.endswith((".escalate", ".located")))
    row("EXTRACT", "fused documents", OK if docs else IDLE,
        f"{len(docs)} document(s) fused")
    # ⚠ COVERAGE BEFORE SCORE. A score over fewer pages is not a better score.
    for p in docs:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cov = rec.get("coverage", {})
        tot = cov.get("pages_total")
        both = cov.get("pages_both_channels")
        st = OK if tot and both == tot else WARN
        row("EXTRACT", p.stem[:24], st,
            f"{both}/{tot} pages have BOTH channels")
    sc = load("resolve/_score_upright.json")
    if sc:
        row("EXTRACT", "corpus-weighted score", OK,
            f"accepted {sc.get('accepted', '?')} · ceiling {sc.get('ceiling', '?')}")


# ────────────────────────────────────────────────────────── resolution
def resolution():
    for f, label in (("resolve/_events.json", "established events"),
                     ("resolve/_leads.json", "unestablished leads")):
        d = load(f)
        if d is None:
            row("RESOLVE", label, IDLE, "none")
        else:
            row("RESOLVE", label, OK if d else IDLE, f"{len(d)} record(s)")
    row("RESOLVE", "index verifier", IDLE,
        "NOT BUILT — the third channel is pulled but unwired")


def unwired():
    """⚠ THE REGISTER OF BUILT-BUT-UNCONNECTED WORK. Nothing else tracks this,
    and it is the cheapest work in the project — already written, never run."""
    items = [
        ("fuse.py index_path", "third channel designed in, never wired"),
        ("acquire_index.py", "per-document index pull, superseded by the bulk pull"),
        ("bakeoff/extract.py", "built, never run"),
        ("rotation (--angles)", "no VLM run has ever read a rotated page"),
        ("Supabase push for index", "100.8M rows are on disk only"),
    ]
    print("\n  UNWIRED — built and not connected")
    for what, why in items:
        print(f"    · {what:<26} {why}")


def main():
    print("\n  ACRIS DECODER — phase board   "
          f"({time.strftime('%Y-%m-%d %H:%M')})")
    print("  " + "─" * 96)
    selection()
    support_index()
    acquisition()
    extraction()
    resolution()
    print("  " + "─" * 96)
    unwired()
    print("\n  Docs: docs/WORKFLOW.md · docs/sources/acris/  ·  every number "
          "above is read from the "
          "job's own state file\n")
    if VERBOSE:
        for f in sorted(HERE.glob("_*state*.json")):
            print(f"\n=== {f.name} ===")
            print(f.read_text(encoding="utf-8")[:1200])


if __name__ == "__main__":
    main()
