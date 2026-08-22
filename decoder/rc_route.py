"""DISCOVER THE RICHMOND DATE-RANGE ROUTE — the live-sync path.

    ACRIS_CORPUS_ROOT=D:/acris python rc_route.py

WHY THIS AND NOT GALLOPING INTERNAL IDS. The block ledger is the HISTORICAL
access path (whole block, no paging). For the DAILY delta it is wrong twice: it
cannot tell you what is new without re-reading 3,789 blocks, and a brand-new
document may sit on a block we would not think to re-ask. DATE RANGE asks the
question we actually have - "what recorded since <watermark>?" - the way ACRIS's
CRFN edge does, but published directly instead of probed.

WARNING - POST NEEDS THE ANTI-FORGERY TOKEN *AND* THE COOKIE FROM THE SAME
SESSION. 400 without. The menu page mints both; we walk GET menu -> POST button
-> read the form the server hands back, exactly as a click does. No guessing at
routes: every path here came off the page.
"""
from __future__ import annotations
import json, pathlib, re, sys, urllib.parse, urllib.request
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rc_source as RC

def token(html):
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None

def post(s, path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(RC.BASE + path, data=body, method="POST")
    req.add_header("User-Agent", RC.UA)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Referer", RC.BASE + "/Search/SearchIndex")
    import time; time.sleep(RC.PACE)
    with s.op.open(req, timeout=60) as r:
        h = r.read().decode("utf-8", "replace"); url = r.geturl()
    RC.check_refused(h)
    return url, h

def forms(html):
    out = []
    for m in re.finditer(r'<form[^>]*action="([^"]*)"[^>]*>(.*?)</form>', html, re.S | re.I):
        fields = [(a, b) for a, b in re.findall(r'<input[^>]*name="([^"]+)"[^>]*?(?:value="([^"]*)")?', m.group(2))]
        out.append((m.group(1), fields))
    return out

def discover():
    s = RC.Session()
    menu = s.get("/Search/SearchIndex")
    tok = token(menu)
    print(f"  menu ok · token {'present' if tok else 'MISSING'}")
    url, page = post(s, "/Search/SearchIndex",
                     {"button": "DateRangeSearch", "hbutton": "DateRangeSearch",
                      "htoken": "", "__RequestVerificationToken": tok})
    print(f"  -> {url}  ({len(page):,} b)")
    for a, fs in forms(page):
        print(f"  FORM action={a}")
        for n, v in fs:
            if n != "__RequestVerificationToken":
                print(f"      {n} = {v!r}")
    (HERE / "_rc_daterange_page.html").write_text(page, encoding="utf-8")
    print("  saved -> _rc_daterange_page.html")


if __name__ == "__main__":
    discover()
