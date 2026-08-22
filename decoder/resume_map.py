"""RESUME THE MAP AFTER A SUSPEND. One command, safe to run twice.

⚠ WHY A SUSPEND NEEDS THIS. The processes usually survive a laptop sleep, but
their TCP connections do not. The mapper wakes holding a pool of dead sockets,
every request fails, and — because errors are counted rather than raised — it
can sit there making no progress while still looking alive. Line count is the
only honest liveness test.

⚠ AND IT WILL NOT START A SECOND MAPPER ALONGSIDE A LIVE ONE. runlock detects
siblings by command line; two mappers appending to one file is how 787 documents
once arrived as 1,519 rows. If a healthy run is already moving, this leaves it
alone and says so.

    python resume_map.py
"""
import pathlib
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPS = pathlib.Path("acris_maps.jsonl")
LOG = pathlib.Path("_supervise.log")
TARGET = 17_021_446


def procs():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | "
             "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return {}
    found = {}
    for line in out.splitlines():
        if "|" not in line:
            continue
        pid, cmd = line.split("|", 1)
        for name in ("supervise_map.py", "map_acris.py"):
            if name in cmd:
                found.setdefault(name, []).append(int(pid.strip()))
    return found


def bytes_per_doc():
    """⚠ MEASURED FROM THE FILE, NEVER ASSUMED.

    The first version of this script hardcoded 180 bytes per document. The real
    figure is ~214, so it over-counted by 27% and printed "✅ COMPLETE" at a
    genuine 87.5% — the single worst failure this script could have, because the
    whole point of it is to tell you whether the job is done.

    A record's length varies with doc_type, the instrument range and whether
    supporting-document fields are present, so there is no constant to know.
    Sample the tail and count.
    """
    size = MAPS.stat().st_size
    with open(MAPS, "rb") as fh:
        fh.seek(max(0, size - 2_000_000))
        chunk = fh.read()
    lines = chunk.count(b"\n")
    return (len(chunk) / lines) if lines else 214.0


def count():
    # ⚠ bytes, not lines. Counting 15M lines takes ~40s and this runs twice.
    return MAPS.stat().st_size if MAPS.exists() else 0


def main():
    if not MAPS.exists():
        print("acris_maps.jsonl not found — are you in the decoder directory?")
        return

    # ── is anything actually moving? ─────────────────────────────────────
    a = count()
    print("checking whether the map is still progressing (20s)...")
    time.sleep(20)
    b = count()
    BPD = bytes_per_doc()
    gained = (b - a) / BPD
    live = procs()
    done_est = b / BPD

    print(f"\n  mapped (est) : {done_est:,.0f} / {TARGET:,}  "
          f"({done_est/TARGET*100:.1f}%)")
    print(f"  rate         : {gained/20:,.0f} docs/s")
    print(f"  supervisor   : {live.get('supervise_map.py') or 'not running'}")
    print(f"  mapper       : {live.get('map_acris.py') or 'not running'}")

    if done_est >= TARGET * 0.999:
        print("\n  ✅ COMPLETE. Nothing to resume.")
        return

    if gained / 20 > 5:
        print("\n  ✅ still running and making progress — leaving it alone.")
        return

    # ── stalled. Was it a refusal, or just dead sockets? ─────────────────
    if LOG.exists():
        tail = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-6:]
        if any("REFUSED" in t for t in tail):
            print("\n  ⚠ THE SUPERVISOR STOPPED ON AN ACRIS REFUSAL.")
            print("    Do NOT restart it. That is an answer, not a crash.")
            print("    Wait, then resume by hand at lower MAP_CONC.")
            for t in tail:
                print("      " + t)
            return

    print("\n  stalled with no refusal — almost certainly dead sockets after "
          "the suspend.")
    for name, pids in live.items():
        for p in pids:
            print(f"    stopping {name} pid {p}")
            subprocess.run(["taskkill", "/PID", str(p), "/F"],
                           capture_output=True)
    if live:
        print("    waiting 10s for sockets to drain")
        time.sleep(10)

    print("\n  restarting supervisor at MAP_CONC=32 ...")
    subprocess.Popen(
        [sys.executable, "-u", "supervise_map.py"],
        env={**__import__("os").environ, "MAP_CONC": "32"},
        stdout=open("_supervise_console.log", "a"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    time.sleep(25)
    c = count()
    print(f"  restarted. gained {(c-b)/BPD:,.0f} documents in 25s")
    print("\n  check again later with:  python resume_map.py")


if __name__ == "__main__":
    main()
