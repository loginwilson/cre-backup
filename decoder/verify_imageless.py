"""IS A pdf='imageless' VERDICT TRUE? — re-ask the source, one doc at a time.

    python verify_imageless.py --sample 300          # measure the false rate
    python verify_imageless.py --sample 300 --apply  # ...and repair what it finds
    python verify_imageless.py --all --apply         # full repair sweep (resumable)

WHY THIS EXISTS. A refusal is HTTP 200 WITH NO TotalPages, so `page_count`
read the Bandwidth Notice as "this document has no image" and the pdf lanes
wrote pdf='imageless' - a PERMANENT verdict manufactured from a TEMPORARY
refusal (found 2026-08-24; both acris_pdf and image_walk patched). Every
refusal window with pdf workers running is a suspect period, and the old
image_walk fleet had NO detector on the map response at all, so it would
have marked doc after doc for a whole block.

⚠ A FALSE imageless IS WORSE THAN A GAP. The row counts as READY on the
board AND tells extraction there is nothing to read, so the document is
silently never decoded. Same family as a Short passing for a whole pdf.

⚠ PIANO DISCIPLINE. One connection, one request at a time - and NOTHING
ELSE MAY TOUCH ACRIS WHILE THIS RUNS (stop the lane first). A refusal stops
this pass at once; it never retries and never rotates.

⚠ REPAIR MEANS CLEARING THE VERDICT, NOT WRITING A NEW ONE. A false row is
set back to pdf='' so the lane re-fetches it through the normal path. This
script never writes a pdf path and never writes 'imageless'."""
from __future__ import annotations

import argparse
import pathlib
import random
import sqlite3
import sys
import threading
import time
import urllib.error

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import acris_pdf as AP                                          # noqa: E402
import corpus_paths as CP                                       # noqa: E402
import fetch_pages                                              # noqa: E402
import live_delta as LD                                         # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--sample", type=int, default=300)
ap.add_argument("--all", action="store_true")
ap.add_argument("--apply", action="store_true")
ap.add_argument("--pace", type=float, default=0.15)
a = ap.parse_args()

REFUSALS = (fetch_pages.AccessDenied, LD.Refused)
LOG = CP.NAV_WORK / "verify_imageless.jsonl"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": fetch_pages.UA})
SESSION.mount("https://", requests.adapters.HTTPAdapter(
    pool_connections=1, pool_maxsize=1, max_retries=0))
_wire = threading.Lock()


def one_at_a_time(url, referer, timeout=90):
    with _wire:
        r = SESSION.get(url, headers={"Referer": referer}, timeout=timeout)
    if r.status_code >= 400:
        raise urllib.error.HTTPError(url, r.status_code, r.reason,
                                     r.headers, None)
    time.sleep(a.pace)
    return r.content, r.headers.get("Content-Type", "")


AP.FETCH = one_at_a_time


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


ro = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
ro.execute("PRAGMA busy_timeout=120000")

if a.all:
    say("collecting every imageless row (a scan - minutes)")
    ids = [r[0] for r in ro.execute(
        "SELECT id FROM navigation WHERE pdf='imageless'"
        " AND id NOT LIKE 'RC_%' ORDER BY id")]
    say("%s rows to verify" % "{:,}".format(len(ids)))
else:
    # unbiased rate estimate: point probes across the id space, each landing
    # on the next imageless row at or after a random id
    say("sampling %d imageless rows by point probe" % a.sample)
    seen, ids = set(), []
    for _ in range(a.sample * 40):
        if len(ids) >= a.sample:
            break
        band = random.choice(("2003", "2005", "2008", "2012", "2016",
                              "2020", "2024", "2026", "BK_", "FT_"))
        probe = band + "%012d" % random.randrange(0, 10 ** 12)
        r = ro.execute("SELECT id, pdf FROM navigation WHERE id >= ?"
                       " ORDER BY id LIMIT 1", (probe,)).fetchone()
        if r and r[1] == "imageless" and r[0] not in seen:
            seen.add(r[0])
            ids.append(r[0])
    say("%d sampled" % len(ids))

wcon = None
if a.apply:
    wcon = sqlite3.connect(CP.NAV_DB, timeout=600)
    wcon.execute("PRAGMA busy_timeout=300000")

true_v = false_v = err = 0
t0 = time.time()
for i, did in enumerate(ids, 1):
    try:
        total = AP.page_count(did)
    except REFUSALS as e:
        say("REFUSED at %s - STOPPING THE PASS: %.80s" % (did, e))
        break
    except Exception as e:
        err += 1
        continue
    if total > 0:
        false_v += 1
        say("  FALSE VERDICT %s - source reports %d pages" % (did, total))
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write('{"id": "%s", "pages": %d, "at": "%s"}\n'
                     % (did, total, time.strftime("%Y-%m-%dT%H:%M:%S")))
        if a.apply:
            for _try in range(60):
                try:
                    wcon.execute("UPDATE navigation SET pdf='' WHERE id=?"
                                 " AND pdf='imageless'", (did,))
                    wcon.commit()
                    break
                except sqlite3.OperationalError:
                    time.sleep(5)
    else:
        true_v += 1
    if i % 50 == 0:
        el = time.time() - t0
        say("  %d/%d checked · %d confirmed · %d FALSE (%.1f%%) · %d err ·"
            " %.2f req/s" % (i, len(ids), true_v, false_v,
                             100.0 * false_v / max(true_v + false_v, 1),
                             err, i / el if el else 0))

n = true_v + false_v
say("DONE  %d checked · %d confirmed imageless · %d FALSE (%.2f%%) · %d err"
    % (n, true_v, false_v, 100.0 * false_v / max(n, 1), err))
if false_v and not a.apply:
    say("(report-only - rerun with --apply to clear those verdicts)")
