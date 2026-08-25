"""SWEEP the browser lane's downloads into the store + table - CONVERTING
on the way (login: "itll be fatal if you just download rc pdf as the format
theyre in... save and convert into pdf of tiffs that compress it").
Measured: the VSCMS viewer serves COLOR JPEG pages (~640KB each, 3.65MB for
a 7-page deed); re-encoded to 1-bit G4 TIFF the same deed is ~10x smaller,
and it lands in the SAME format the ACRIS image lane stores. A file that is
not a real pdf (0 pages, wrong magic) is left in place and reported.

Usage:  python rc_pdf_land.py [--loop]
"""
import argparse
import io
import pathlib
import re
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import fitz
import img2pdf
from PIL import Image

STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
# ONE-TOUCH (login): a browser's download location points at _incoming on
# D: - the raw file lands ONCE on the big drive and C: never stages it.
# ⚠ SWEEP EVERY PLAUSIBLE DROP FOLDER. Each browser PROFILE has its own
# download setting: a second session pointed at the STORE ROOT stranded 98
# files there (2026-08-22) - un-chronologized AND never marked in the
# table, so those docs read as unacquired forever. The store root is now
# swept like any other drop folder; the sweep re-files them correctly.
DOWNS = (STORE / "_incoming", pathlib.Path(r"C:\Users\smile\Downloads"),
         STORE / "By Document")

ap = argparse.ArgumentParser()
ap.add_argument("--loop", action="store_true",
                help="run as the RC pdf landing daemon (sweep every 60s)")
ap.add_argument("--raw", action="store_true",
                help="LAND WITHOUT CONVERTING (validity-check only, ~10/s):"
                " acquisition = having the doc; rc_convert.py compresses"
                " in place later. Split 2026-08-21: the inline G4 convert"
                " ran ~0.4 docs/s and became the whole lane's bottleneck"
                " (Chrome pulled 1.1/s, backlog 1,600+).")
a = ap.parse_args()

# THE BOARD READS _working/rc_pdf_land.log ("landed N pdfs" lines) - when
# this runs as a task, stdout goes to the task file and the board goes
# blind (2026-08-21: board froze at 2,531 while the daemon landed
# thousands). The daemon writes its OWN feed line - no bridge needed.
BOARD_LOG = CP.NAV_WORK / "rc_pdf_land.log"


def say(msg):
    print(msg, flush=True)
    if "landed" in msg:
        with BOARD_LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")

con = sqlite3.connect(CP.NAV_DB, timeout=600)
con.execute("PRAGMA busy_timeout=300000")


# ⚠ A DEAD PARTIAL DOWNLOAD HOLDS A CHROME DOWNLOAD SLOT FOREVER.
# Measured 2026-08-22: 32 in-flight files in _incoming, newest 97 s old,
# AVERAGE 49 min, OLDEST 89,831 s - twenty-five hours. A .crdownload that
# has not been written to in 25 hours is not downloading, it is a corpse.
# Chrome caps concurrent downloads, so corpses fill the slots and live
# fetches queue behind them until something times out and a burst rushes
# through. That is the whole "saves rapidly, backs up, freezes, then jumps
# massively and clears" cycle the login described - the lander was never
# the cause, and no amount of landing faster would have fixed it.
# Age is judged by mtime, so a SLOW-but-live download is never killed: an
# active transfer touches its file continuously. Only genuinely abandoned
# ones go, and their ids return to the feed's work list because the table
# is the work list - an unlanded id is still unlanded.
STALE_PARTIAL = 15 * 60


def reap_partials():
    """delete abandoned .crdownload/.tmp so live downloads get their slots"""
    gone = 0
    for d in DOWNS:
        for pat in ("*.crdownload", "*.tmp"):
            for p in d.glob(pat):
                try:
                    if time.time() - p.stat().st_mtime > STALE_PARTIAL:
                        p.unlink()
                        gone += 1
                except OSError:
                    pass          # locked = Chrome still owns it; leave it
    if gone:
        say(f"reaped {gone} dead partial download(s)")
    return gone


def sweep():
    n = bad = 0
    reported = [0]                   # how many already announced this sweep
    reap_partials()
    queue = [p for d in DOWNS for p in sorted(d.glob("RC_*.pdf"))]
    if queue:
        print(f"sweep start: {len(queue)} waiting", flush=True)
    for src in queue:
        # ⚠ REPORT DURING THE SWEEP, NOT ONLY AT ITS END. A silent daemon
        # working through 800 files looks identical to a stalled one - it
        # cost a wrong "it's blocked" diagnosis on 2026-08-21.
        # ⚠ COMMIT AND REPORT IN CHUNKS, not once per sweep. A sweep of 1,000
        # files ran ~40 min silent, so the dashboard (which sums "landed N
        # pdfs") showed ZERO while the lane was working fine - and that read
        # as a stall. Chunking makes progress visible AND durable.
        if n and n % 50 == 0:
            say(f"landed {n - reported[0]} pdfs "
                f"({len(queue)-n} left in sweep)")
            reported[0] = n
        # ⚠ CHROME DUPLICATE NAMES: a re-download saves "RC_123 (1).pdf" -
        # the raw stem is NOT the id (it built "By Document\RC_1\001 \..."
        # whose trailing-space dir Windows strips at mkdir but not at write:
        # FileNotFoundError, lander dead, 2026-08-21). Normalize first; if
        # the id already landed, the dup is trash, not work.
        did = re.sub(r" \(\d+\)$", "", src.stem)
        try:
            # a file Chrome is still writing opens truncated - skip while hot
            if time.time() - src.stat().st_mtime < 3:
                continue
            already = con.execute(
                "SELECT pdf FROM navigation WHERE id=?", (did,)).fetchone()
            if already is None:
                print(f"  {did}: no navigation row - left in place",
                      flush=True)
                bad += 1
                continue
            if already[0]:
                src.unlink()          # landed earlier; this is a re-download
                continue
            d = fitz.open(str(src))
            if d.page_count <= 0:
                raise ValueError("0 pages")
            if a.raw:
                d.close()
                out = src.read_bytes()      # validity proven; convert later
            else:
                frames = []
                for page in d:
                    pix = page.get_pixmap(dpi=200)
                    im = Image.frombytes("RGB", (pix.width, pix.height),
                                         pix.samples)
                    buf = io.BytesIO()
                    im.convert("1").save(buf, format="TIFF",
                                         compression="group4")
                    frames.append(buf.getvalue())
                raw = src.stat().st_size
                d.close()
                out = img2pdf.convert(frames)
                # KEEP WHICHEVER IS SMALLER (color-JPEG scans shrink 7.8x
                # under G4; already-compressed docs would INFLATE ~25%)
                if len(out) >= raw:
                    out = src.read_bytes()
        except Exception as e:
            print(f"  {did}: NOT convertible ({e}) - left in place",
                  flush=True)
            bad += 1
            continue
        rec = con.execute(
            "SELECT json_extract(recorded_details, '$.recorded')"
            " FROM navigation WHERE id=?", (did,)).fetchone()
        dest = CP.doc_store_dir(did, (rec[0] if rec else "") or "")
        dest.mkdir(parents=True, exist_ok=True)
        dst = dest / f"{did}.pdf"
        dst.write_bytes(out)
        src.unlink()
        # ⚠ COMMIT PER FILE. The UPDATE opens an implicit write transaction;
        # committing every 50 held the nav db's ONE write lock across ~50
        # CPU-heavy conversions (30-60 s) while all eight lanes queued on
        # busy_timeout - acris rd collapsed 99 -> 16 docs/s the moment this
        # daemon started (board 9:24-9:34, 2026-08-21). Milliseconds of lock
        # per file, converted OUTSIDE the transaction, is the rule.
        con.execute("UPDATE navigation SET pdf=? WHERE id=?",
                    (str(dst.relative_to(STORE)), did))
        con.commit()
        n += 1
    con.commit()
    n -= reported[0]                 # only the tail not already announced
    if n or bad:
        say(f"landed {n} pdfs"
            + (f" · {bad} invalid left behind" if bad else ""))


while True:
    sweep()
    if not a.loop:
        break
    time.sleep(60)
