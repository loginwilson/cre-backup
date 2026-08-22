"""READ ONE DOCUMENT ALL THE WAY THROUGH — every page, every clause, every reader.

    python full_doc.py 2006082400263003

⚠ WHY. Every accuracy number in this project is HEAD-PAGE recall: OCCUPANCY 95%,
CAPITAL 59%, the mode cues — all measured on 3 to 6 pages of documents that run
10, 30 or 200. Login, 2026-08-16: "I still worry you are missing parts of the
documents." The only way to answer that is to read one document to the last page
and count what the head would have missed.

⚠ THE DEPTH CURVE IS THE POINT. Not "how many claims" but "where in the document
did they appear". A flat curve means the head is enough. A curve that keeps
climbing means every head-page number in this project is an overstatement, and
the acquisition plan has to change before 9.3 TB lands against it.

⚠ AND UNREAD IS REPORTED AS A LIST, NOT A GAP. A function with no detector, a
quantity with no extractor, a page that OCR'd to nothing — each is named. A
document is not "fully read" because the loop finished.
"""
from __future__ import annotations

import collections, json, os, pathlib, re, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import lexicon

PAGE_DIRS = ("sample_pages", "devr_pages", "pages_out", "fp_pages", "lease_pages")


def pages_for(doc):
    for d in PAGE_DIRS:
        p = HERE / d / doc
        if p.exists():
            t = sorted(p.glob("p*.tif"))
            if t:
                return t
    return []


def ocr(tifs, procs=2, threads=4):
    import devr_sweep
    from multiprocessing import Pool
    jobs = [(t.parent.name, str(t), 0) for t in tifs]
    out = {}
    with Pool(procs, initializer=devr_sweep._init, initargs=(threads,)) as pool:
        for doc, pg, txt, err in pool.imap_unordered(devr_sweep.work, jobs,
                                                     chunksize=1):
            # ⚠ AN EMPTY READ IS A FAILURE, NOT AN EMPTY PAGE.
            out[str(pg)] = (txt or "", err)
    return out


def main():
    doc = sys.argv[1] if len(sys.argv) > 1 else "2006082400263003"
    tifs = pages_for(doc)
    if not tifs:
        print(f"  no pages on disk for {doc}")
        return 1
    print(f"{doc} — {len(tifs)} pages on disk")
    t0 = time.time()
    got = ocr(tifs)
    el = time.time() - t0
    print(f"  OCR {len(got)} pages in {el:.1f}s ({el/max(len(got),1):.2f}s/page)\n")

    order = sorted(got, key=lambda k: str(k))
    blank = [p for p in order if len((got[p][0] or "").strip()) < 40]
    if blank:
        print(f"  ⚠ {len(blank)} page(s) read to (near) nothing: {blank} — "
              f"UNREAD, not empty\n")

    # ── per page: clauses, functions, modes ──────────────────────────────
    hdr = f"  {'page':<6}{'chars':>7}{'clauses':>9}   functions fired            modes"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    first_seen = {}
    per_page = {}
    total_cl = 0
    fn_clauses = collections.Counter()
    for i, p in enumerate(order, 1):
        txt, err = got[p]
        cls = list(lexicon.clauses(txt))
        total_cl += len(cls)
        fns, modes = collections.Counter(), collections.Counter()
        for c, _off in cls:
            for f in lexicon.fire(c, "function"):
                fns[f] += 1
                fn_clauses[f] += 1
                first_seen.setdefault(f, i)
            for m in lexicon.mode(c):
                modes[m] += 1
                first_seen.setdefault(f"mode:{m}", i)
        per_page[i] = (len(txt), len(cls), dict(fns), dict(modes))
        fs = " ".join(f"{k}:{v}" for k, v in fns.most_common()) or "—"
        ms = " ".join(f"{k}:{v}" for k, v in modes.most_common()) or "—"
        print(f"  {i:<6}{len(txt):>7}{len(cls):>9}   {fs:<26} {ms}")

    print(f"\n  TOTAL {total_cl:,} clauses across {len(order)} pages")

    # ── THE DEPTH CURVE ──────────────────────────────────────────────────
    print("\nDEPTH — what a head-page read would have missed")
    for head in (1, 3, 6, len(order)):
        seen = {f for f, pg in first_seen.items() if pg <= head}
        cl = sum(per_page[i][1] for i in per_page if i <= head)
        print(f"  first {head:>2} page(s): {len(seen):>2} readers fired, "
              f"{cl:>5,} clauses  {sorted(seen)}")
    late = {f: pg for f, pg in first_seen.items() if pg > 3}
    if late:
        print(f"\n  ⚠ FIRST SEEN AFTER PAGE 3 — invisible to every head-page "
              f"measurement in this project:")
        for f, pg in sorted(late.items(), key=lambda kv: kv[1]):
            print(f"      {f:<22} first fires on page {pg}")
    else:
        print("\n  every reader that fires at all fires within the first 3 pages")

    # ── WHAT NEVER FIRED ─────────────────────────────────────────────────
    detected = set(lexicon.FUNCTIONS)
    never = sorted(detected - set(fn_clauses))
    nodetector = [f for f in lexicon.CANONICAL if f.lower() not in detected]
    print(f"\nUNREAD AND ABSENT — named, not implied")
    print(f"  detectors that ran and found nothing (ABSENT): {never or '—'}")
    print(f"  functions with NO detector at all (UNREAD)   : {nodetector}")

    json.dump({"doc": doc, "pages": len(order), "clauses": total_cl,
               "first_seen": first_seen,
               "per_page": {str(k): v for k, v in per_page.items()},
               "blank_pages": blank, "absent": never, "unread": nodetector},
              open(HERE / f"_full_{doc}.json", "w"), indent=1)
    print(f"\nwrote _full_{doc}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
