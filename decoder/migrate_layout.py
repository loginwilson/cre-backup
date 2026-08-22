"""RENAME THE CORPUS TO WHAT IT ACTUALLY IS — acris -> legal-instruments.

    python migrate_layout.py            report what it WOULD do, touch nothing
    python migrate_layout.py --apply    do it

⚠ RUN THIS ONLY WITH EVERY WRITER STOPPED. It refuses to start otherwise: a
folder rename with live handles either fails or corrupts, and the detail pull
holds `index/rc_detail.jsonl` open for append continuously.

WHY. The drive is named for ONE custodian and holds TWO. Richmond is 2,426,404 of
the 24,037,915 document ids — a tenth of the corpus and the only source of Staten
Island deeds. "acris" stopped being the name of this thing when the second
custodian landed, and a name that misdescribes its contents is how the next person
concludes Richmond does not belong here.

    D:/acris/                      D:/legal-instruments/
      01-specification/     ->       Specification/     README + the mapping
      02-acquisition/       ->       Acquisition/       README + by-parcel/
      00-run/               ->       _run/              disposable ops state
      _legacy-pages/        ->       _legacy-pages/     unchanged

⚠ TWO FOLDERS ARE THE PRODUCT, THE UNDERSCORED ONES ARE NOT. `_run` keeps its
leading underscore precisely so it never reads as a third phase — it is logs,
PIDs, worklists and the ledger, and it is REBUILDABLE. That boundary was the whole
point of the old 00/01/02 numbering and it survives the rename.

⚠ COMPATIBILITY JUNCTIONS ARE CREATED, NOT SKIPPED. ~6 scripts hardcode
`D:/acris/...` and the Windows scheduled task bakes `ACRIS_CORPUS_ROOT=D:/acris`
into its command line. The junctions mean nothing breaks at 4 AM while those are
migrated one at a time, instead of a big-bang edit of 97 references.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLD_ROOT = pathlib.Path("D:/acris")
NEW_ROOT = pathlib.Path("D:/legal-instruments")

RENAMES = [("01-specification", "Specification"),
           ("02-acquisition", "Acquisition"),
           ("00-run", "_run")]


def writers_running():
    """Any live process that holds the corpus open. A rename must not race them."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" "
             "| Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        return [f"could not enumerate processes ({type(e).__name__}) — refusing"]
    watch = ("rc_detail_pull", "rc_detail_land", "rc_daily", "routine_4am",
             "live_land", "overnight", "push_", "rc_land")
    return [l.strip() for l in out.splitlines()
            if l.strip() and any(w in l for w in watch)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("CORPUS LAYOUT MIGRATION")
    print(f"  {OLD_ROOT}  ->  {NEW_ROOT}")

    # ── refuse if anything is writing ────────────────────────────────────
    busy = writers_running()
    if busy:
        print("\n  ⚠ REFUSING — these are still running:")
        for b in busy:
            print(f"      {b[:110]}")
        print("  Stop them first. A rename with live handles fails or corrupts.")
        sys.exit(1)
    print("  no corpus writers running ✓")

    # ── the junction created 2026-08-19 must go before the real rename ───
    if NEW_ROOT.exists() and NEW_ROOT.is_symlink() or (
            NEW_ROOT.exists() and not (NEW_ROOT / "Specification").exists()
            and not (NEW_ROOT / "01-specification").exists()):
        print(f"  {NEW_ROOT} exists as a JUNCTION (the interim alias) — it is "
              f"removed first so the real folder can take the name")
        if a.apply:
            subprocess.run(["cmd", "/c", "rmdir", str(NEW_ROOT)], check=True)

    plan = [f"rename  {OLD_ROOT}  ->  {NEW_ROOT}"]
    for old, new in RENAMES:
        plan.append(f"rename  {new_name(old)}  ->  {new}")
    plan.append(f"junction {OLD_ROOT} -> {NEW_ROOT}   (compat for hardcoded paths)")
    for old, new in RENAMES:
        plan.append(f"junction {NEW_ROOT/old} -> {NEW_ROOT/new}   (compat)")

    print("\n  PLAN")
    for p in plan:
        print(f"    {p}")

    if not a.apply:
        print("\n  --apply not given; nothing touched.")
        print("  AFTER applying, these still need doing BY HAND:")
        print("    1. scheduled task 'ACRIS Live Sync 4AM': ACRIS_CORPUS_ROOT=D:/legal-instruments")
        print("    2. corpus_paths.py: SPEC/ACQ/RUN folder names")
        print("    3. the ~6 hardcoded D:/acris paths (rc_detail_land.py SRC, "
              "land_index_rest.py, land_personal.py, pull_index_fast.py, "
              "fix_reference_key.py)")
        print("    4. re-point the READMEs' example commands")
        return

    # ── do it ────────────────────────────────────────────────────────────
    OLD_ROOT.rename(NEW_ROOT)
    print(f"\n  renamed root -> {NEW_ROOT}")
    for old, new in RENAMES:
        src, dst = NEW_ROOT / old, NEW_ROOT / new
        if src.exists():
            src.rename(dst)
            print(f"  renamed {old} -> {new}")
    # compat junctions so nothing breaks before the references are migrated
    subprocess.run(["cmd", "/c", "mklink", "/J", str(OLD_ROOT), str(NEW_ROOT)])
    for old, new in RENAMES:
        subprocess.run(["cmd", "/c", "mklink", "/J",
                        str(NEW_ROOT / old), str(NEW_ROOT / new)])
    print("\n  compat junctions created — old paths keep working.")
    print("  NOW do the 4 by-hand items listed by the dry run.")


def new_name(old):
    return NEW_ROOT / old


if __name__ == "__main__":
    main()
