"""THE DOCUMENT MAP — how many pages, and which ones are the instrument.

One HTML load of DocumentImageView returns hidden fields that lay out the whole
document before a single image is fetched:

    hid_TotalPages   everything GetImage will serve
    hid_Sup          supporting documents start at this page (0 = none)
    hid_Tax          tax return / RP-5217 starts here     (0 = none)

⚠ THIS IS THE FIX FOR THE TECHNIQUE THAT GOT THIS PROJECT BLOCKED. On
2026-08-05 a range scan spent ~83 requests fetching 15-page windows to LOCATE
an exhibit, and that is what tripped the limiter. The location was free the
whole time, from this page, with no images at all.

⚠ IT ALSO FINDS THE RP-5217 — the deed agent's declared THIRD price witness,
which this project has never once fetched because nothing knew where it lived.
Every price derived so far rests on two witnesses (RPTT ÷ 2.625% and
RETT ÷ 0.400%) with a third sitting at a page number this call would have named.

⚠ AND hid_Tax = 0 IS A FINDING, NOT A MISS. A conveyance with no tax return
filed is evidence — on the Domino deed it sits alongside $0/$0 stamps and
identical grantor and grantee. ABSENT is an answer.

⚠ WHETHER THIS ENDPOINT IS THROTTLED LIKE GetImage IS UNKNOWN AND IS EXACTLY
WHAT probe() MEASURES. It matters enormously: if HTML is cheap, an entire
document type can be MAPPED before any acquisition is planned, and the page
budget spent only on instrument pages. If it is throttled the same, mapping
costs as much as fetching and the plan changes.

Same manners as every other call here: browser UA, Referer, paced, and it stops
dead on a refusal.
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CACHE = pathlib.Path("docmaps.jsonl")

FIELDS = ("hid_Cov", "hid_Sup", "hid_Tax", "hid_DocID")

# ⚠ hid_TotalPages IS NOT A FORM FIELD. It lives ONLY inside the frame's src,
# URL-encoded, as part of a JSON blob:
#
#   <frame src="...DocumentImageVtu?searchCriteriaStringValue=%7B...
#               %22hid_TotalPages%22%3A138%2C...">
#
# The first parser looked for it as a hidden input, found nothing, and returned
# `total None` for every document — while correctly reading hid_Sup=137 from
# the same page. A map saying "supporting starts at 137, total unknown" is
# worse than no map: it looks populated. Decode the frame src instead.


def _field(html, field):
    m = (re.search(rf'name="{field}"[^>]*value="([^"]*)"', html) or
         re.search(rf'value="([^"]*)"[^>]*name="{field}"', html))
    if not m:
        return None
    v = m.group(1).strip()
    return int(v) if v.isdigit() else (v or None)


def _frame_json(html):
    """The frame src carries the viewer's whole state. Decode it."""
    m = re.search(r'searchCriteriaStringValue=([^"&\']+)', html)
    if not m:
        return {}
    try:
        return json.loads(urllib.parse.unquote(m.group(1)))
    except Exception:
        # ⚠ FALL BACK, BUT SAY SO. A silent {} here reintroduces the exact bug
        # this function was written to fix.
        m2 = re.search(r'TotalPages%22%3A(\d+)', html)
        return {"hid_TotalPages": int(m2.group(1))} if m2 else {"_parse_failed": True}


def fetch_map(doc_id, pause=6.0):
    """-> dict, or raises AccessDenied. One HTML request."""
    req = urllib.request.Request(
        f"{BASE}?doc_id={doc_id}",
        headers={"User-Agent": UA,
                 "Referer": "https://a836-acris.nyc.gov/DS/DocumentSearch/"
                            f"DocumentDetail?doc_id={doc_id}"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as f:
        status, hdrs = f.status, dict(f.headers)
        data = f.read()
    el = time.time() - t0
    # ⚠ THE SAME REFUSAL DETECTOR. A block on this endpoint must abort as loudly
    # as one on GetImage — a silently-empty map would be recorded as "document
    # has no supporting pages", which is a wrong claim, not a missing one.
    try:
        fetch_pages._check_denied(data, hdrs.get("Content-Type", ""))
    except fetch_pages.AccessDenied:
        fetch_pages._log_refusal(doc_id, "MAP", status, hdrs, el, len(data))
        raise
    html = data.decode("utf-8", "ignore")
    m = {"doc_id": doc_id, "elapsed_s": round(el, 2), "bytes": len(data)}
    for fld in FIELDS:
        m[fld] = _field(html, fld)
    fj = _frame_json(html)
    m["hid_TotalPages"] = fj.get("hid_TotalPages")
    if fj.get("_parse_failed"):
        m["warning"] = "frame JSON unparsable — total page count UNKNOWN"

    tot = m["hid_TotalPages"]
    sup, tax, cov = m["hid_Sup"] or 0, m["hid_Tax"] or 0, m["hid_Cov"] or 0
    if tot:
        # sections start at hid_Sup / hid_Tax; the instrument runs to whichever
        # comes first. ⚠ hid_Cov is the COVER count, so the instrument does not
        # start at page 1 — it starts after the cover.
        after = [x for x in (sup, tax) if x]
        m["instrument"] = [cov + 1, (min(after) - 1) if after else tot]
        m["supporting"] = [sup, tot] if sup else None
        m["tax_return"] = [tax, (sup - 1 if sup and sup > tax else tot)] if tax else None
        m["instrument_pages"] = m["instrument"][1] - m["instrument"][0] + 1
    time.sleep(pause)
    return m


def probe(doc_ids, pause=6.0):
    """⚠ MEASURES WHETHER HTML IS THROTTLED. Stops the moment it is refused."""
    out, refused_at = [], None
    for i, d in enumerate(doc_ids, 1):
        try:
            m = fetch_map(d, pause)
        except fetch_pages.AccessDenied:
            refused_at = i
            print(f"  ⚠ HTML REFUSED at load {i} — this endpoint IS throttled")
            break
        except Exception as e:
            print(f"  {d}: {type(e).__name__} {str(e)[:70]}")
            continue
        out.append(m)
        # ⚠ APPEND NOW, NOT AT THE END. The first version accumulated every map
        # in memory and wrote the cache only after the loop finished, so a
        # 1,161-document run that was interrupted at document 1,160 would
        # persist NOTHING — two hours of polite requests thrown away, and worse,
        # the ledger would not know they had been made. Anything that runs for
        # hours must checkpoint as it goes.
        try:
            with open(CACHE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(m) + "\n")
        except Exception as e:
            print(f"  ⚠ could not persist map for {d}: {type(e).__name__}")
        print(f"  {i:>3} {d}  total {m['hid_TotalPages']}  "
              f"cov {m['hid_Cov']}  instrument {m.get('instrument')}"
              f"={m.get('instrument_pages')}pp  "
              f"sup {m['hid_Sup']}  tax {m['hid_Tax']}  "
              f"({m['bytes']/1000:.0f}kb {m['elapsed_s']}s)")
    # (maps are persisted per-document above; nothing to flush here)
    print(f"\n  {len(out)} maps fetched"
          + (f", refused at {refused_at}" if refused_at
             else " — NO REFUSAL. HTML appears cheaper than images."))
    return out, refused_at


if __name__ == "__main__":
    wl = json.loads(pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                                 else "worklist_DEVR.json").read_text())
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    probe([r["document_id"] for r in wl[:n]])
