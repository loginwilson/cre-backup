"""THE SCHEDULED WRAPPER. Task Scheduler runs this; you never see it.

    Registered as   ACRIS-MapDelta-Daily   (see setup_schedule.ps1)
    Log             _delta_daily.log       (rotates at 5 MB)
    Summary         _delta_daily_status.tsv   one line per run, greppable

⚠ IT ALWAYS EXITS 0. A refusal is not a failure of this job — ACRIS declines,
map_delta holds the watermark, and tomorrow's run picks up exactly the same
work. Exiting non-zero would paint the task red in Task Scheduler and train you
to ignore it, which is worse than silence. The TSV is where you look instead:
a run that mapped nothing writes PARTIAL, and two PARTIALs in a row is the
signal that something is actually wrong.

⚠ NO CONSOLE WINDOW, DELIBERATELY. The task this replaces opened a python
console at 04:00 every morning and its last exit code was 0xC000013A —
control-C — because the window was being closed by hand. A scheduled job that
demands attention every morning gets killed every morning. This one runs under
pythonw with stdout redirected to the log before anything can print.
"""
import datetime
import os
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
os.chdir(HERE)                      # ⚠ every path in map_delta is relative
sys.path.insert(0, str(HERE))

LOG = HERE / "_delta_daily.log"
TSV = HERE / "_delta_daily_status.tsv"

# ⚠ ROTATE BEFORE OPENING. A year of daily runs is a large file, and the one
# time you need to read it will be the time it has grown too big to open.
if LOG.exists() and LOG.stat().st_size > 5_000_000:
    LOG.replace(HERE / "_delta_daily.log.1")

# ⚠ REDIRECT FIRST, IMPORT SECOND. Under pythonw sys.stdout is None, so any
# print before this line — including map_delta's module-level
# sys.stdout.reconfigure — raises and the job dies silently with no log.
# ⚠ BOM ON CREATION ONLY — NOT ON EVERY APPEND.
#
# The log is full of ✅ and ⚠ and ·, and without a leading BOM every Windows
# tool that opens it (Get-Content under PowerShell 5.1, Notepad, the Task
# Scheduler pane) decodes it as the ANSI codepage and renders mojibake.
#
# But opening in "a" mode with utf-8-sig writes the BOM EVERY TIME, because the
# encoder emits it at the start of each handle's output, not each file's. That
# plants a stray BOM before every day's header and fixes nothing, since the
# decoder only honours one at byte zero. Pick the encoding from whether the
# file is about to be created.
new = not LOG.exists() or LOG.stat().st_size == 0
fh = open(LOG, "a", encoding="utf-8-sig" if new else "utf-8", errors="replace")
sys.stdout = sys.stderr = fh

t0 = datetime.datetime.now()
print(f"\n{'='*72}\n{t0:%Y-%m-%d %H:%M:%S}  ACRIS map delta\n{'='*72}", flush=True)

status, note = "ERROR", ""
try:
    import map_delta
    map_delta.main()
    st = {}
    if map_delta.STATE.exists():
        import json
        st = json.loads(map_delta.STATE.read_text())
    new = st.get("new", 0)
    mode = st.get("mode", "?")
    # ⚠ THE WATERMARK IS THE TRUTH, NOT THE PRINTED TEXT. map_delta writes
    # mode 'fast-partial' precisely when it declined to advance, so this reads
    # the same fact the next run will read rather than re-deriving it.
    if mode.endswith("partial"):
        status, note = "PARTIAL", f"{new} outstanding, watermark held"
    else:
        status = "OK"
        note = f"{new} mapped" if new else "nothing new"
except SystemExit:
    status, note = "OK", "exited early"
except Exception:
    note = "exception — see log"
    traceback.print_exc()

el = (datetime.datetime.now() - t0).total_seconds()
print(f"\n{status}  {note}  ({el:.0f}s)", flush=True)

if not TSV.exists():
    TSV.write_text("when\tstatus\tseconds\tnote\n", encoding="utf-8")
with open(TSV, "a", encoding="utf-8") as t:
    t.write(f"{t0:%Y-%m-%d %H:%M}\t{status}\t{el:.0f}\t{note}\n")

fh.close()
sys.exit(0)                         # ⚠ always. See the note at the top.
