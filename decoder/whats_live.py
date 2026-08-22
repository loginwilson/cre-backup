"""WHAT IS ACTUALLY LIVE — computed from the import graph, not from memory.

    python whats_live.py            # the carry list and the archive list
    python whats_live.py --drift    # files that exist but nothing reaches

⚠ DECIDING THE CARRY LIST FROM MEMORY IS HOW THINGS GET LOST. There are 264
python files in this directory. Nobody can hold which twenty are current, and
the answer changes every week — which is exactly the complaint this file exists
to answer: *"everytime we add something new it just gets lost in the fold."*

So the list is DERIVED. Start from the entry points that are genuinely run — the
scheduled routine's commands and the phase docs' runbooks — walk their local
imports transitively, and everything reached is live. Everything else is archive
BY DEFAULT, which is the safe direction: an archived file is one `git mv` from
coming back, while a wrongly-carried file re-creates the sprawl.

⚠ AND UNREACHABLE IS NOT THE SAME AS USELESS. A script nothing imports may still
hold the only copy of a hard-won trap in its docstring. Archive means "not on the
pipeline path", never "safe to delete". Nothing here deletes anything.
"""
from __future__ import annotations

import ast
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

# ⚠ ENTRY POINTS ARE DECLARED, BECAUSE NOTHING IMPORTS THEM. They are what a
# human or a scheduler invokes. Keep this list in step with the routine
# (~/.claude/scheduled-tasks/acris-selection/SKILL.md) and the phase runbooks;
# a command that runs and is not listed here is the one drift this file cannot
# detect for itself.
ENTRY = {
    "selection":   ["selection_daily.py", "selection_cross.py",
                    "reconcile_selection.py", "pull_index_fast.py",
                    "index_daily.py", "pull_index_noimage.py",
                    "repair_tail.py", "map_delta.py", "daily_delta.py",
                    "selection_delta.py", "push_selection.py",
                    "push_maps_tail.py"],
    "acquisition": ["map_acris.py", "acquire_index.py", "fetch_pages.py",
                    "afetch.py", "amap.py"],
    "extraction":  ["bakeoff/run.py", "bakeoff/run_serial.py",
                    "bakeoff/pp_doc.py", "bakeoff/score.py"],
    "resolution":  ["resolve/fuse.py", "resolve/canonical.py",
                    "resolve/claims.py", "resolve/event.py",
                    "resolve/locate.py", "resolve/score_fused.py",
                    "resolve/export_escalation.py"],
    "ops":         ["status.py", "whats_live.py"],
}


def local_imports(path: pathlib.Path) -> set[str]:
    """Module names this file imports that resolve to a file in this tree."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def resolve(mod: str, near: pathlib.Path) -> pathlib.Path | None:
    for cand in (near.parent / f"{mod}.py", HERE / f"{mod}.py"):
        if cand.exists():
            return cand.resolve()
    return None


def discovered_entries() -> set[pathlib.Path]:
    """Entry points DERIVED, not declared: a file with a `__main__` guard that
    nothing else imports.

    ⚠ A DECLARED LIST IS ONLY AS GOOD AS WHOEVER WROTE IT, AND MINE WAS WRONG.
    The first version of this file hand-listed the ACRIS document pipeline —
    selection, acquisition, extraction, resolution — and reported 253 files as
    unreachable. That number was inflated by an entire second subsystem whose
    entry points I simply had not thought of: the parcel spine, the envelope
    ledger, entitlements, and the DOB/BSA/LPC/DCP decoders, including a
    3,738-line `claims.py` and `audit.py`, the trap-enforcement arm.

    Calling them "archive" because I forgot to list them is the same failure the
    whole exercise is meant to prevent — deciding from memory. So the graph now
    finds its own roots and the declared list below is only a safety net for
    entry points a scheduler invokes that have no main guard.
    """
    imported = set()
    mains = set()
    for p in HERE.rglob("*.py"):
        if "__pycache__" in p.parts or ".venv" in p.parts:
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "__main__" in src:
            mains.add(p.resolve())
        for mod in local_imports(p):
            q = resolve(mod, p)
            if q:
                imported.add(q)
    return {p for p in mains if p not in imported}


def walk():
    seen, queue, missing = set(), [], []
    queue.extend(discovered_entries())
    for phase, files in ENTRY.items():
        for f in files:
            p = (HERE / f)
            if p.exists():
                queue.append(p.resolve())
            else:
                missing.append(f)
    reached = {}
    while queue:
        p = queue.pop()
        if p in seen:
            continue
        seen.add(p)
        reached[p] = reached.get(p, 0)
        for mod in local_imports(p):
            q = resolve(mod, p)
            if q and q not in seen:
                queue.append(q)
                reached[q] = reached.get(q, 0) + 1
    return seen, missing


def main():
    live, missing = walk()
    allpy = {p.resolve() for p in HERE.rglob("*.py")
             if "__pycache__" not in p.parts and ".venv" not in p.parts}
    archive = sorted(allpy - live)

    def rel(p):
        return str(p.relative_to(HERE)).replace("\\", "/")

    print(f"\n  LIVE — reachable from a declared entry point   ({len(live)})")
    for p in sorted(live, key=rel):
        age = (time.time() - p.stat().st_mtime) / 86400
        print(f"    {rel(p):<44} {p.stat().st_size/1024:>7.1f} KB   "
              f"{age:>5.0f}d")

    print(f"\n  ARCHIVE — nothing reaches these   ({len(archive)})")
    print("    ⚠ Not useless — several hold the only copy of a trap in their")
    print("      docstring. Archive means 'off the pipeline path'.")
    for p in archive[:25]:
        print(f"    {rel(p)}")
    if len(archive) > 25:
        print(f"    ... and {len(archive)-25} more")

    if missing:
        print(f"\n  ⚠ DECLARED BUT ABSENT ({len(missing)}) — the entry list has "
              f"drifted from reality:")
        for m in missing:
            print(f"    {m}")

    # ⚠ THE DRIFT CHECK IS THE POINT. Everything above is a snapshot; this is
    # what stops the structure decaying again. A file written in the last two
    # weeks that NOTHING reaches is new work that landed nowhere — either it
    # needs an entry-point declaration, or it needs to be imported by something
    # that has one, or it was a one-off and belongs in scratch/.
    #
    # "It just gets lost in the fold" is precisely this state, and until now it
    # was invisible: a new file in a directory of 264 looks exactly like the 263
    # around it. Here it is a named error with a date on it.
    fresh = sorted((p for p in archive
                    if (time.time() - p.stat().st_mtime) / 86400 < 14),
                   key=lambda p: -p.stat().st_mtime)
    if fresh:
        print(f"\n  ⚠ NEW BUT UNREACHED ({len(fresh)}) — written recently, on no "
              f"path. Place these or they are lost:")
        for p in fresh:
            d = (time.time() - p.stat().st_mtime) / 86400
            print(f"    {rel(p):<44} {d:>4.0f}d old")
    else:
        print("\n  No recent file is unreachable — nothing is lost in the fold.")

    print(f"\n  {len(live)} live · {len(archive)} archive · "
          f"{100*len(live)/max(len(allpy),1):.0f}% of the tree is on the path\n")


if __name__ == "__main__":
    main()
