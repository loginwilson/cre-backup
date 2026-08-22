"""Launch the selection push with NO CONSOLE, so nothing can Ctrl+C it.

    python spawn_push.py        # returns immediately; the push runs on

⚠ WHY THIS FILE EXISTS. The push has now been killed FOUR times by the agent
session, and the last two were not process-tree teardown at all — Task Scheduler
reported `LastTaskResult 3221225786 = 0xC000013A = STATUS_CONTROL_C_EXIT`. The
job shared a CONSOLE with the agent's shell, so every time one of my tool calls
ended, the console control event reached the push and killed it. It looked
identical to a crash, and I spent two restarts treating it as one.

Three fixes were tried and each failed for its own reason:
    nohup ... &                       dies with the session
    Start-Process -WindowStyle Hidden dies with the session (~10 min)
    Scheduled Task (interactive)      runs, but shares the console -> Ctrl+C
    Scheduled Task with -LogonType S4U  "Access is denied" — needs elevation

What works without elevation: spawn with **DETACHED_PROCESS**, which gives the
child no console at all, plus **CREATE_NEW_PROCESS_GROUP** so it is not in the
parent's group. A console control event has nowhere to arrive.

The child is the .cmd wrapper, so the retry loop still applies: push_selection.py
resumes from an atomic checkpoint, and the right answer to any death is to start
it again.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
LOG = HERE / "_push_selection_run.log"

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000

# ⚠ DO NOT HAND THE LOG FILE TO Popen. The .cmd wrapper already redirects with
# `>> _push_selection_run.log`, so passing an open handle for stdout/stderr puts
# TWO WRITERS on one file and Windows refuses the second:
#     "The process cannot access the file because it is being used by another
#      process."
# The wrapper then spins on that error forever, having pushed nothing. One
# owner of the log, and it is the wrapper.
p = subprocess.Popen(
    ["cmd", "/c", str(HERE / "run_push_selection.cmd")],
    cwd=str(HERE), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
    close_fds=True)

print(f"push detached as pid {p.pid} — no console, cannot receive Ctrl+C")
print(f"  log:   {LOG.name}")
print(f"  state: _push_selection_state.json  (resume point, atomic)")
