# -*- coding: utf-8 -*-
"""WHY DOES THE RICHMOND BROWSER LOOP STALL, AND WHICH OF THE TWO CAUSES IS IT?

The loop stalls intermittently and resumes when the login clicks the browser.
Two hypotheses were live on 2026-08-22 and BOTH had been asserted as fact by
the assistant before being measured (one was wrong; the other unproven):

  A  TAB FROZEN     Edge sleeping-tabs / efficiency mode freezes the tab, and
                    with it the Web Worker carrying the loop's clock.
  B  DOWNLOAD GATE  Chromium blocks multiple automatic downloads for the
                    origin, so the clicks fire but nothing lands.

⚠ THEY LOOK IDENTICAL FROM THE BOARD (rate 0) AND OPPOSITE FROM THE FEED:

    cause          served climbing?   ready backing up?   in-flight?
    A tab frozen         NO                 YES              0
    B dl blocked         YES                no               0

`served` only increments when the page POLLS /batch. A frozen tab cannot
poll. A blocked download does not stop the polling. That single counter
separates them, and it is already in rc_feed's /stats.

Read-only: polls the feed's own /stats and counts files in _incoming.
Touches nothing. Writes a log file (never pipe long runs through grep).

Usage:  python rc_watch.py                     # watch + classify, alert only
        python rc_watch.py --stall 90          # seconds of no progress = stall
        python rc_watch.py --kick focus        # also raise the Edge window
"""
import argparse, time, json, urllib.request, pathlib, datetime, sys

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8077)
ap.add_argument("--every", type=int, default=15, help="poll seconds")
ap.add_argument("--stall", type=int, default=90, help="no-progress seconds = stall")
ap.add_argument("--kick", choices=["none", "focus"], default="none")
ap.add_argument("--log", default="rc_watch.log")
a = ap.parse_args()

INCOMING = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                        r"\Legal Instruments Acquisition\_incoming")
LOG = pathlib.Path(a.log)


def say(msg):
    line = "%s  %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def stats():
    try:
        with urllib.request.urlopen("http://localhost:%d/stats" % a.port,
                                    timeout=5) as r:
            return json.load(r)
    except Exception as e:
        return {"err": str(e)}


def incoming():
    """(completed pdfs waiting for the lander, downloads in flight)"""
    try:
        done = inflight = 0
        for p in INCOMING.iterdir():
            s = p.suffix.lower()
            if s in (".crdownload", ".tmp"):
                inflight += 1
            elif s == ".pdf":
                done += 1
        return done, inflight
    except OSError:
        return -1, -1


def kick():
    """Raise the Edge window. A frozen/slept tab resumes on foreground; a
    download-gated one does NOT, so the kick doubles as a live experiment."""
    if a.kick != "focus":
        return "none"
    try:
        import subprocess
        ps = ("$w = Get-Process msedge -ErrorAction SilentlyContinue | "
              "Where-Object { $_.MainWindowTitle } | Select-Object -First 1; "
              "if ($w) { "
              "  Add-Type -AssemblyName Microsoft.VisualBasic; "
              "  [Microsoft.VisualBasic.Interaction]::AppActivate($w.Id); 'ok' "
              "} else { 'no-window' }")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip()[:40]
    except Exception as e:
        return "kick-failed: %s" % e


say("rc_watch up · feed :%d · stall after %ds · kick=%s" % (a.port, a.stall, a.kick))

prev = stats()
prev_served = prev.get("served", 0)
prev_done, prev_inflight = incoming()
last_progress = time.time()
stalled_since = None

while True:
    time.sleep(a.every)
    s = stats()
    if "err" in s:
        say("FEED UNREACHABLE: %s  <-- rc_feed.py is down, nothing else matters"
            % s["err"][:60])
        continue

    served = s.get("served", 0)
    ready = s.get("ready", 0)
    done, inflight = incoming()

    d_served = served - prev_served
    d_done = done - prev_done          # negative = the lander is draining, fine
    progress = d_served > 0 or d_done > 0 or inflight > 0

    if progress:
        if stalled_since:
            say("RECOVERED after %ds · served+%d done%+d inflight %d"
                % (time.time() - stalled_since, d_served, d_done, inflight))
            stalled_since = None
        last_progress = time.time()
    else:
        quiet = time.time() - last_progress
        if quiet >= a.stall and not stalled_since:
            stalled_since = time.time()
            # ---- CLASSIFY: the whole point of this file ----------------
            if d_served == 0 and ready > 0:
                cause = ("A · TAB FROZEN — the page is not polling at all "
                         "(served flat, %d ready and waiting). Edge sleeping "
                         "tabs / efficiency mode. Fix: edge://settings/system "
                         "-> never sleep richmondcountyclerk.com" % ready)
            elif d_served > 0 and inflight == 0 and d_done <= 0:
                cause = ("B · DOWNLOADS BLOCKED — the page IS polling and "
                         "being served, but nothing reaches disk. Chromium "
                         "multiple-automatic-downloads gate. Fix: allow "
                         "[*.]richmondcountyclerk.com")
            elif ready == 0:
                cause = ("C · FEED DRY — not a browser problem at all; the "
                         "miners are not minting. Check rc_feed miners/token TTL.")
            else:
                cause = ("D · UNCLASSIFIED — served+%d ready %d inflight %d "
                         "done%+d. Record this combination."
                         % (d_served, ready, inflight, d_done))
            say("STALL after %ds  ==> %s" % (quiet, cause))
            say("   kick -> %s" % kick())

    prev_served, prev_done, prev_inflight = served, done, inflight
    if not stalled_since:
        say("ok · served+%-4d ready %-5d done %-4d inflight %-3d"
            % (d_served, ready, done, inflight))
