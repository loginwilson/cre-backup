"""MINT RICHMOND IMAGE URLS for the browser pdf lane (login: the RC pdf is
browser-assisted - "use the url in chrome"; conc comes from batching many
urls into one in-page fetch).

Headless work here touches ONLY richmondcountyclerk.com: the ViewContent
route answers 302 with the tokenized iapps viewer url in Location. The
redirect is NOT followed - the image host is never contacted headless (it
refuses headless clients, and a refusal we deliberately elicit is still a
refusal). Chrome does the fetching.

Picks the next N RC rows in id order whose rd is landed, whose pdf cell is
empty, and whose rd says the image is PRESENT (a pending image mints a
dead viewer). Writes JSON lines {id, url} to _working/rc_pdf_batch.jsonl.

Usage:  python rc_mint.py --limit 12
"""
import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import pathlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import rc_source as RC
import rc_sync as RS

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=12)
ap.add_argument("--workers", type=int, default=6,
                help="concurrent mint sessions (the mint must stay ahead of"
                     " the browser loop's ~1 doc/s; 6 sessions give ~4-6/s)")
a = ap.parse_args()

OUT = CP.NAV_WORK / "rc_pdf_batch.jsonl"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=120,
                      check_same_thread=False)
con.execute("PRAGMA busy_timeout=60000")
rows = con.execute(
    "SELECT id FROM navigation WHERE id LIKE 'RC_%'"
    " AND recorded_details != '' AND pdf = ''"
    " AND json_extract(recorded_details, '$.image_state') = 'present'"
    " ORDER BY id LIMIT ?", (a.limit,)).fetchall()

import threading
from concurrent.futures import ThreadPoolExecutor

tl = threading.local()
lock = threading.Lock()
minted, skipped = [], [0]


def mint(did):
    iid = did[3:]
    try:
        if not hasattr(tl, "op"):
            w = RS.Window("08/17/2026", "08/17/2026")
            tl.op = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(w.s.jar), _NoRedirect())
            tl.op.addheaders = [("User-Agent", RC.UA)]
        time.sleep(RC.PACE)
        req = urllib.request.Request(
            RC.BASE + f"/ViewVscmsDocument/ViewContent?p_endorsementId={iid}")
        req.add_header("Referer", RC.BASE + f"/Search/ViewDocumentInfo/{iid}")
        try:
            with tl.op.open(req, timeout=60):
                loc = None
        except urllib.error.HTTPError as e:
            loc = (e.headers.get("Location")
                   if e.code in (301, 302, 303) else None)
        with lock:
            if loc:
                minted.append({"id": did, "url": loc})
            else:
                skipped[0] += 1
    except Exception:
        with lock:
            skipped[0] += 1


with ThreadPoolExecutor(max_workers=a.workers) as ex:
    list(ex.map(mint, [r[0] for r in rows]))

with OUT.open("w", encoding="utf-8") as f:
    for m in minted:
        f.write(json.dumps(m) + "\n")
print(f"minted {len(minted)}/{len(rows)} (skipped {skipped[0]}) -> {OUT}")
