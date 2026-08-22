"""LABEL THE WHOLE DEVR CORPUS ON THREE PAGES EACH — not another sample.

    python devr_head.py                # all 1,180, resumable
    python devr_head.py --limit 100
    python devr_head.py --report       # classify from what is already read

⚠ NOTHING NEEDS FETCHING. 1,180 of the 1,215 DEVR documents are ALREADY on disk
— 42,310 pages, 2.1 GB, acquired earlier and never read. Only 25 were ever
OCR'd, which is why "the sample" was 25: it was a sample of what had been READ,
and it was mistaken for a sample of what had been ACQUIRED. Before pulling any
sample, look at what is already there.

⚠ AND A FULL READ IS NOT NEEDED TO PICK A SAMPLE. Deciding whether a document is
a genuine rights instrument takes exactly two things:

    filed_as   Document Type, printed on the cover page          (page 1)
    is_a       the instrument's own title, on its first body page (page 2-3)

Three pages per document labels the ENTIRE POPULATION for ~3,540 pages of OCR,
against 42,310 for a full read. The remaining 92% is only worth spending on
documents already known to be worth reading.

⚠⚠ AND THIS IS THE ONLY WAY THE FREE SCREEN GETS TESTED. `same entity on both
party types` separated the labelled 25 perfectly — 0/13 genuine, 12/12 mis-filed
— but all 12 mis-filed were ONE filing by ONE presenter, so that is one
draftsman's habit measured twelve times, not a validated rule. It flags 12.0% of
the full population across every year, which is plausible and proves nothing.
n=1 is not a rate. This pass produces the ground truth that either confirms the
screen at n=1,180 or kills it.

⚠ THE SAMPLE WAS ALSO 2003-ONLY. All 25 read documents were recorded in 2003 —
the first year of the electronic era, 45 of 1,215. Every coverage number so far
was measured on one year's drafting conventions.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
SRC = HERE / "devr_pages"
OUT = HERE / "devr_head"

# ⚠ THREE, AND THE THIRD IS NOT PADDING. The ACRIS cover runs to 2+ pages
# whenever the party or property list overflows — coverpage.py documents a
# 4-page cover on a multi-party assignment — so page 2 is often still the
# wrapper. Reading only pages 1-2 would return the cover twice and no title.
HEAD_PAGES = 3

TITLE_WORDS = (r"DECLARATION|AGREEMENT|DEED|EASEMENT|COVENANT|RESTRICTIONS?|"
               r"CERTIFICATE|WAIVER|LEASE|ASSIGNMENT|SATISFACTION|MODIFICATION|"
               r"CONSENT|SUBORDINATION|AMENDMENT|MEMORANDUM")
TITLE = re.compile(r"((?:[A-Z][A-Za-z]{2,}\s*){0,5}(?:" + TITLE_WORDS + r")"
                   r"(?:\s*(?:OF|AND|FOR)\s*(?:[A-Z][A-Za-z]*\s*){1,5})?)", re.I)
COVER = re.compile(r"RECORDING\s*AND\s*ENDORSEMENT|NYC\s*DEPARTMENT\s*OF\s*FINANCE",
                   re.I)
DOCTYPE = re.compile(r"Document\s*Type\s*:?\s*([A-Z][A-Z /&\-]{4,44}?)\s*"
                     r"(?=Document|PRESENTER|RETURN|PROPERTY|PARTIES|$)", re.I)

# What counts as a genuine development-rights instrument, by its own title.
RIGHTS = ("ZONINGLOT", "DEVELOPMENTRIGHTS", "DEVELOPMENTAGREEMENT",
          "AIRRIGHTS", "TRANSFERABLEDEVELOPMENT")


def sweep(limit=None, procs=2, threads=4):
    OUT.mkdir(exist_ok=True)
    docs = sorted(d for d in SRC.iterdir() if d.is_dir())
    todo = [d for d in docs if not (OUT / f"{d.name}.json").exists()]
    if limit:
        todo = todo[:limit]
    jobs = [(d.name, str(p), 0) for d in todo
            for p in sorted(d.glob("p*.tif"))[:HEAD_PAGES]]
    if not jobs:
        print("  nothing to read — every document already has a head")
        return
    print(f"  {len(todo)} documents · {len(jobs)} pages "
          f"(<= {HEAD_PAGES}/doc) · PP-OCRv4/OpenVINO", flush=True)

    import devr_sweep
    from multiprocessing import Pool
    pages, errs, t0 = collections.defaultdict(dict), 0, time.time()
    blank, done = {}, 0
    # ⚠ REBUILD THE POOL EVERY BATCH. A worker whose inference session has
    # degraded returns empty text forever after and raises nothing, so ONE bad
    # worker silently blanks every document routed to it for the remainder of
    # the run. That is exactly the shape observed: 502 documents wholly empty,
    # 663 wholly fine, 15 partial — bimodal, which is a worker signature, not a
    # page one. A bounded pool lifetime caps the blast radius.
    BATCH = 300
    for b0 in range(0, len(jobs), BATCH):
      with Pool(procs, initializer=devr_sweep._init, initargs=(threads,)) as pool:
        for i, (doc, pg, txt, err) in enumerate(
                pool.imap_unordered(devr_sweep.work, jobs[b0:b0 + BATCH],
                                    chunksize=2), done + 1):
            done = i
            pages[doc][pg] = txt
            errs += bool(err)
            if i % 50 == 0:
                el = time.time() - t0
                print(f"    {i}/{len(jobs)}  {el/i:.2f}s/pg  "
                      f"eta {(len(jobs)-i)*el/i/60:.0f}m  errs {errs}", flush=True)
            # ⚠ WRITE AS SOON AS A DOCUMENT IS COMPLETE. A two-hour run that
            # holds everything in memory loses everything to one crash, and the
            # resume then re-reads pages it had already paid for.
            want = min(HEAD_PAGES, len(list((SRC / doc).glob("p*.tif"))))
            if len(pages[doc]) >= want:
                got = pages.pop(doc)
                # ⚠⚠ AN EMPTY READ IS NOT A READ. The first full run wrote 502
                # documents whose every head page came back with ZERO characters
                # — while reporting "errs 0", because no exception was raised.
                # Re-running one of those pages alone produced 1,819 characters
                # immediately: the pages were fine, the run had degraded (it was
                # killed part-way, consistent with memory exhaustion quietly
                # breaking inference). Because the empty string was written as a
                # successful result, the classifier then read it back and called
                # the DOCUMENT unreadable — 49.6% of the corpus — attributing a
                # harness failure to the source material. Same defect class as
                # "HTTP 200 with empty content is a FAILURE". Refuse to write,
                # and the resume retries it.
                if not any((v or "").strip() for v in got.values()):
                    blank[doc] = True
                    continue
                (OUT / f"{doc}.json").write_text(json.dumps(
                    {"doc_id": doc, "engine": "PP-OCRv4/openvino",
                     "pages": [{"page": k, "accepted_text": v}
                               for k, v in sorted(got.items())]},
                    indent=1), encoding="utf-8")
    el = time.time() - t0
    print(f"\n  DONE {len(jobs)} pages in {el/60:.1f}m ({el/len(jobs):.2f}s/pg) "
          f"· {errs} errors · {len(blank)} documents REFUSED "
          f"(every head page blank — not written, resume will retry)",
          flush=True)


def classify(rec):
    """(filed_as, is_a, verdict) from a head record."""
    pgs = rec.get("pages") or []
    filed = is_a = None
    for p in pgs:
        t = " ".join((p.get("accepted_text") or "").split())
        if COVER.search(t[:200]):
            if not filed:
                m = DOCTYPE.search(t)
                filed = " ".join(m.group(1).split()).upper() if m else None
            continue
        if not is_a:
            m = TITLE.search(t[:700])
            if m:
                v = " ".join(m.group(1).split()).upper().strip(" ,.")
                is_a = v if len(v) > 6 else None
    key = re.sub(r"[^A-Z]", "", is_a or "")
    if not key:
        verdict = "unreadable"
    elif any(w in key for w in RIGHTS):
        verdict = "genuine"
    else:
        verdict = "misfiled"
    return filed, is_a, verdict


def report():
    recs = sorted(OUT.glob("*.json"))
    if not recs:
        print("  no heads read yet")
        return
    feat = {f["doc"]: f for f in
            json.loads((HERE / "_devr_feat.json").read_text(encoding="utf-8"))}
    rows, ver = {}, collections.Counter()
    for f in recs:
        rec = json.loads(f.read_text(encoding="utf-8"))
        filed, is_a, v = classify(rec)
        rows[rec["doc_id"]] = {"filed_as": filed, "is_a": is_a, "verdict": v,
                               "year": feat.get(rec["doc_id"], {}).get("year"),
                               "same": feat.get(rec["doc_id"], {}).get("same")}
        ver[v] += 1
    n = len(rows)
    print(f"\nDEVR HEAD CLASSIFICATION — {n} documents read of 1,180\n")
    for k, c in ver.most_common():
        print(f"    {k:<12}{c:>6}  {c/n:>6.1%}")

    # ⚠ THE SCREEN IS SCORED HERE, AGAINST READ TEXT, OR IT IS NOT SCORED.
    got = [r for r in rows.values() if r["verdict"] in ("genuine", "misfiled")
           and r["same"] is not None]
    if got:
        tp = sum(1 for r in got if r["same"] and r["verdict"] == "misfiled")
        fp = sum(1 for r in got if r["same"] and r["verdict"] == "genuine")
        fn = sum(1 for r in got if not r["same"] and r["verdict"] == "misfiled")
        tn = sum(1 for r in got if not r["same"] and r["verdict"] == "genuine")
        print(f"\n  FREE SCREEN 'same entity both party types' vs read text "
              f"(n={len(got)})")
        print(f"    flagged & really mis-filed   {tp:>5}")
        print(f"    flagged & actually GENUINE   {fp:>5}  ⚠ false positives")
        print(f"    not flagged but MIS-FILED    {fn:>5}  ⚠ false negatives")
        print(f"    not flagged & genuine        {tn:>5}")
        if tp + fp:
            print(f"    precision {tp/(tp+fp):.1%} · recall "
                  f"{tp/max(tp+fn,1):.1%}")
        print("    ⚠ the screen was fitted on 12 mis-filed documents that were "
              "ONE filing.\n      These numbers, not those, decide whether it "
              "can be used.")

    top = collections.Counter(r["is_a"] for r in rows.values()
                              if r["verdict"] == "misfiled")
    print(f"\n  WHAT THE MIS-FILED ONES ACTUALLY ARE")
    for k, c in top.most_common(10):
        print(f"    {c:>4}  {str(k)[:64]}")

    byyr = collections.defaultdict(collections.Counter)
    for r in rows.values():
        byyr[r["year"]][r["verdict"]] += 1
    print(f"\n  BY YEAR   (genuine / misfiled / unreadable)")
    for y in sorted(byyr):
        c = byyr[y]
        print(f"    {y}   {c['genuine']:>4} / {c['misfiled']:>3} / "
              f"{c['unreadable']:>3}")

    out = HERE / "_devr_labels.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\n  -> {out.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--procs", type=int, default=2)
    a = ap.parse_args()
    if not a.report:
        sweep(a.limit or None, a.procs)
    report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
