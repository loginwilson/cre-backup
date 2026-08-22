"""ACQUIRE THE DEVELOPMENT RIGHTS CORPUS — all 1,201, paced, resumable.

⚠ WHAT CHANGED, AND IT INVALIDATES MOST OF TODAY'S ACQUISITION ANALYSIS.

    old fetcher, NO COOKIES, 25s apart (0.04 req/s)  -> refused at request 5
    browser, real session, 1.62 req/s               -> 38/38, no refusal
    session_fetch, ONE cookie, 1 req/s              -> 8/8,  no refusal

It was never a rate limit. It was a client that asked for images without ever
visiting the page they belong to. Everything built earlier today on the
"address-level throttle" reading — the AIMD governor, the 600/day cap, the
burn-the-day-on-refusal policy — was aimed at the wrong target.

⚠ WHAT IS KEPT ANYWAY, AND WHY.

    the permanent LEDGER       a page is never fetched twice, across sessions,
                               forever. Still correct, and now the main saving.
    the HARD ABORT on refusal  still correct. If ACRIS ever does say no, this
                               stops and does not retry. The detector stays.
    deliberate PACING          at 1.0 req/s this is SLOWER than the browser
                               managed (1.62). Fetching here blocked Login's
                               own browser earlier today; being measurably
                               gentler than a person clicking Save is the floor,
                               not a formality.

⚠ WHAT IS DROPPED. The 600/page daily cap, which was calibrated in August
against a misdiagnosis. Removing a limit silently would be exactly the kind of
change that bites later, so: it is replaced by a per-run page budget that must
be passed in explicitly, and the run reports what it actually spent.

STORAGE — fetch, extract, sweep. The TIFFs are transient by design:
    44,947 pages as TIFF   ~2.5 GB   transient
    after extraction        ~0.3 GB   OCR text + proof crops, kept forever
"""
import json
import pathlib
import sys
import time

import fetch_budget
import fetch_pages
import session_fetch

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("devr_pages")
STATE = pathlib.Path("devr_acquire_state.json")


def load_maps():
    m = {}
    p = pathlib.Path("docmaps.jsonl")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("hid_TotalPages"):
                    m[r["doc_id"]] = r
    return m


def run(limit_pages, pace=1.0, max_docs=None):
    wl = json.load(open("worklist_DEVR.json"))
    maps = load_maps()
    print(f"work list {len(wl):,} documents · {len(maps):,} mapped")

    # ⚠ ONLY MAPPED DOCUMENTS. Fetching a document whose page count is unknown
    # means probing until a placeholder comes back — which is the range scan
    # that caused the August block. If it is not mapped, it waits.
    todo = [r for r in wl if r["document_id"] in maps]
    if max_docs:
        todo = todo[:max_docs]

    s = session_fetch.Session()
    spent = 0
    t0 = time.time()
    docs_done = 0
    for r in todo:
        doc = r["document_id"]
        mp = maps[doc]
        lo, hi = mp.get("instrument", [1, mp["hid_TotalPages"]])
        pages = [p for p in range(lo, hi + 1)
                 if not fetch_budget.already_have(doc, p)]
        if not pages:
            continue
        d = OUT / doc
        d.mkdir(parents=True, exist_ok=True)
        print(f"\n[{docs_done+1}] {doc}  pages {lo}-{hi} "
              f"({len(pages)} needed)  bbl {r['legals'][0]['bbl_raw'] if r['legals'] else '?'}")
        for p in pages:
            if spent >= limit_pages:
                print(f"  page budget reached ({limit_pages})")
                _report(spent, t0, docs_done)
                return
            try:
                data, ct, ln = s.page(doc, p)
            except fetch_pages.AccessDenied as e:
                # ⚠ STOP. Do not retry, do not work around it.
                print(f"\n⚠ REFUSED after {spent} pages this run. {str(e)[:120]}")
                _report(spent, t0, docs_done)
                return
            except Exception as e:
                print(f"  p{p}: {type(e).__name__} {str(e)[:70]}")
                continue
            if data is None:
                print(f"  p{p}: not an image ({ct}, {ln}b)")
                continue
            (d / f"p{p:03d}.tif").write_bytes(data)
            fetch_budget.note_fetch(doc, p)
            spent += 1
            if spent % 25 == 0:
                el = time.time() - t0
                print(f"    ... {spent} pages, {spent/el:.2f} req/s")
            time.sleep(pace)
        docs_done += 1
    _report(spent, t0, docs_done)


def _report(spent, t0, docs):
    el = max(time.time() - t0, 0.001)
    rate = spent / el
    print(f"\n{'='*64}")
    print(f"  {spent:,} pages · {docs} documents · {el/60:.1f} min · "
          f"{rate:.2f} req/s")
    if rate > 0:
        print(f"  -> all 1,201 DEVRs (~44,947 pages) at this rate: "
              f"{44947/rate/3600:.1f} hours")
    sz = sum(f.stat().st_size for f in OUT.rglob('*.tif')) if OUT.exists() else 0
    print(f"  on disk: {sz/1e6:,.1f} MB (transient — swept after extraction)")


if __name__ == "__main__":
    run(limit_pages=int(sys.argv[1]) if len(sys.argv) > 1 else 120,
        pace=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0,
        max_docs=int(sys.argv[3]) if len(sys.argv) > 3 else None)
