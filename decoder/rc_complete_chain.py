"""WAIT FOR THE RICHMOND PULL, THEN PROVE COMPLETENESS AND LAND IT.

    ACRIS_CORPUS_ROOT=D:/acris python rc_complete_chain.py --check   test the wait only
    ACRIS_CORPUS_ROOT=D:/acris python rc_complete_chain.py --arm

⚠ WHY THIS IS PYTHON AND NOT A SHELL CHAIN. The shell version used `pgrep -f`,
which does not see Win32 processes from Git Bash - so the wait loop matched
nothing, the chain fired IMMEDIATELY, and the verifier ran alongside the pull,
re-fetching the same 2.39M documents and doubling load on a county server. The
rewrite with a PowerShell one-liner returned an empty string because of shell
escaping, which would have failed the same way. A WAIT CONDITION THAT SILENTLY
EVALUATES FALSE IS WORSE THAN NO WAIT AT ALL.

So: the process check is a function that returns True/False/None, `--check`
exercises it before anything is armed, and an indeterminate result REFUSES to
proceed rather than assuming the coast is clear.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = HERE / "_rc_complete.log"
PY = sys.executable
TARGET = "rc_detail_pull"


def pull_running():
    """True / False / None(indeterminate). Never guesses."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return TARGET in (out.stdout or "")


def stage(label, args, log):
    log.write(f"\n=== {label} · {time.strftime('%Y-%m-%d %H:%M')} ===\n")
    log.flush()
    rc = subprocess.call([PY, "-u"] + args, stdout=log, stderr=subprocess.STDOUT,
                         cwd=str(HERE))
    log.write(f"--- {label} rc={rc}\n")
    log.flush()
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--arm", action="store_true")
    a = ap.parse_args()

    r = pull_running()
    print(f"  process check -> {r!r}  "
          f"({'pull is running' if r is True else 'pull NOT running' if r is False else 'INDETERMINATE'})")
    if a.check or not a.arm:
        print("  --check only; nothing armed.")
        return
    if r is None:
        sys.exit("  process check is INDETERMINATE - refusing to arm. "
                 "A broken wait fires immediately and doubles the load.")

    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"\n\n##### armed {time.strftime('%Y-%m-%d %H:%M')} "
                  f"(pull running: {r}) #####\n")
        while True:
            s = pull_running()
            if s is None:
                log.write("  process check went indeterminate - waiting, not proceeding\n")
                log.flush()
                time.sleep(120)
                continue
            if s is False:
                break
            time.sleep(120)
        log.write(f"\n  pull exited {time.strftime('%Y-%m-%d %H:%M')}\n")
        stage("completeness pass", ["rc_detail_verify.py", "--fix", "--rounds", "8"], log)
        stage("land details", ["rc_detail_land.py", "--apply"], log)
        stage("final proof", ["rc_detail_verify.py"], log)


if __name__ == "__main__":
    main()
