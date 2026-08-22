"""THE DOCUMENT-TYPE CENSUS — one profile per type, built from three pages each.

    python census.py                  # read heads for every type we hold images for
    python census.py --report         # profile from what is already read
    python census.py --limit 200

⚠ WHY A PROFILE PER TYPE AND NOT ONE LEXICON FOR ALL. Login, 2026-08-16: "we need
to know how each document overlaps on functions by understanding the documents
first." That is the correction to how this was built. A FUNCTION's vocabulary is
TYPE-SPECIFIC — "encumbrance" in a deed is the single clause "subject to
covenants running with the land", while in a ZLDA it is a numbered section built
out of defined terms. One global pattern set therefore fires on the deed and goes
silent on the ZLDA while both genuinely encumber. Knowing WHICH function changed
tells you nothing about HOW that type writes it down, and the writing is what has
to be read.

⚠ THE PROFILE FIELDS ARE NOT A GUESS AT WHAT MIGHT MATTER. Every one is
something that broke something this week:

    filed_as vs is_a   11% of DEVRs are not DEVRs — 12 of the first 25 were
                       PARTY WALL declarations, and their "no quantity" refusal
                       was CORRECT. Building an extractor for them would have
                       produced nothing, or worse, noise tuned until it produced
                       something.
    cover_pages        the ACRIS wrapper runs 1 page or 4+. Assuming 3 put the
                       body out of reach on 41 documents and reported them
                       "unreadable".
    exhibits           a real block, not the word appearing in a recital — 23/25
                       vs lexicon's 13/25 on the same documents.
    functions          measured per type, so overlap becomes a table rather than
                       a theory.
    direction          free from ACRIS's own code table for 86.5% of documents;
                       must be read for the rest.

⚠ AN EMPTY READ IS REFUSED, NEVER WRITTEN. Carried over from devr_head.py, where
a degraded worker returned zero characters, raised nothing, and 502 documents
were saved as successful blank reads — then reported as "49.6% of the corpus is
unreadable", which was a statement about my harness dressed as a statement about
ACRIS.

⚠ AND THE SAMPLE PER TYPE IS PRINTED NEXT TO EVERY RATE. A mis-file rate from 12
documents is not a rate; 12 documents from one filing by one presenter is not
even 12. Nothing here is quotable without its n.
"""
from __future__ import annotations

import argparse
import collections
import os
import json
import pathlib
import re
import statistics
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
OUT = HERE / "census_head"
PAGE_DIRS = ("devr_pages", "sample_pages", "pages_out", "fp_pages",
             "lease_pages")
# ⚠ OVERRIDABLE. 3 covers a cover page plus the opening of the instrument for
# most types. A LEASE spends 1-2 pages on the ACRIS wrapper and then a page of
# recitals before the demise clause, so OCCUPY needs 6 or it reads only
# boilerplate. Documents already in census_head/ are skipped, so raising this
# only affects the newly held type.
HEAD_PAGES = int(os.environ.get("HEAD_PAGES", 3))

import lexicon

COVER = re.compile(r"RECORDING\s*AND\s*ENDORSEMENT|NYC\s*DEPARTMENT\s*OF\s*FINANCE",
                   re.I)
DOCTYPE = re.compile(r"Document\s*Type\s*:?\s*([A-Z][A-Z0-9 /&\-,\.]{3,44}?)\s*"
                     r"(?=Document|PRESENTER|RETURN|PROPERTY|PARTIES|$)", re.I)
PAGEOF = re.compile(r"PAGE\s*(\d+)\s*[O0]F\s*(\d+)", re.I)
PAGECOUNT = re.compile(r"Document\s*Page\s*Count\s*:?\s*(\d{1,4})", re.I)
TITLE_WORDS = (r"DECLARATION|AGREEMENT|DEED|EASEMENT|COVENANT|RESTRICTIONS?|"
               r"CERTIFICATE|WAIVER|LEASE|ASSIGNMENT|SATISFACTION|MODIFICATION|"
               r"CONSENT|SUBORDINATION|AMENDMENT|MEMORANDUM|MORTGAGE|RELEASE|"
               r"POWER\s+OF\s+ATTORNEY|AFFIDAVIT|CONTRACT|NOTICE|LIEN")
# ⚠ see title_read.py — the nested-quantifier form of this pattern backtracks
# catastrophically on glued OCR text (3.64s/call measured). Flat and bounded.
TITLE = re.compile(r"([A-Za-z][A-Za-z ]{0,48}?(?:" + TITLE_WORDS + r")"
                   r"(?:\s{0,2}(?:OF|AND|FOR)\s{0,2}[A-Za-z ]{0,34}?)?)", re.I)
# ⚠ ANCHORED TO THE HEAD OF THE PAGE. Unanchored it matches "annexed hereto as
# Exhibit A" inside a recital and calls the recital an exhibit.
EXH_HEAD = re.compile(r"^\W{0,40}(EXHIBIT|SCHEDULE|ANNEX|APPENDIX)\s*"
                      r"[\"'“‘]?\s*([A-Z0-9]{1,3})\b", re.I)


def doc_dirs():
    seen = {}
    for d in PAGE_DIRS:
        p = HERE / d
        if not p.exists():
            continue
        for x in p.iterdir():
            if x.is_dir() and list(x.glob("p*.tif")):
                seen.setdefault(x.name, x)
    return seen


def sweep(limit=None, procs=2, threads=4):
    OUT.mkdir(exist_ok=True)
    dirs = doc_dirs()
    # devr_head/ already holds 1,180 of these — never pay for a page twice
    prior = {p.stem for p in (HERE / "devr_head").glob("*.json")} \
        if (HERE / "devr_head").exists() else set()
    todo = [v for k, v in sorted(dirs.items())
            if not (OUT / f"{k}.json").exists() and k not in prior]
    if limit:
        todo = todo[:limit]
    jobs = [(d.name, str(p), 0) for d in todo
            for p in sorted(d.glob("p*.tif"))[:HEAD_PAGES]]
    if not jobs:
        print("  every held document already has a head read")
        return
    print(f"  {len(todo)} documents · {len(jobs)} pages "
          f"({len(prior)} already read in devr_head/)", flush=True)

    import devr_sweep
    from multiprocessing import Pool
    pages, blank, errs, done, t0 = collections.defaultdict(dict), {}, 0, 0, time.time()
    BATCH = 300     # rebuild the pool so one wedged worker cannot poison the run
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
                      f"eta {(len(jobs)-i)*el/i/60:.0f}m", flush=True)
            want = min(HEAD_PAGES, len(list(dirs[doc].glob("p*.tif"))))
            if len(pages[doc]) >= want:
                got = pages.pop(doc)
                if not any((v or "").strip() for v in got.values()):
                    blank[doc] = True     # an empty read is not a read
                    continue
                (OUT / f"{doc}.json").write_text(json.dumps(
                    {"doc_id": doc, "pages": [{"page": k, "accepted_text": v}
                                              for k, v in sorted(got.items())]},
                    indent=1), encoding="utf-8")
    el = time.time() - t0
    print(f"\n  DONE {len(jobs)} pages in {el/60:.1f}m · {errs} errors · "
          f"{len(blank)} REFUSED as blank (not written, retried on resume)",
          flush=True)


def profile_one(rec):
    """Everything three pages can say about one document."""
    pgs = rec.get("pages") or []
    filed = is_a = None
    n_cover = 0
    total = count = None
    exhibits, fns, regions = set(), set(), set()
    for p in pgs:
        t = " ".join((p.get("accepted_text") or "").split())
        if not t:
            continue
        fns |= set(lexicon.fire(t, "function"))
        regions |= set(lexicon.fire(t, "region"))
        if COVER.search(t[:200]):
            n_cover += 1
            if not filed:
                m = DOCTYPE.search(t)
                filed = " ".join(m.group(1).split()).upper() if m else None
            m, k = PAGEOF.search(t), PAGECOUNT.search(t)
            if m and k and total is None:
                total, count = int(m.group(2)), int(k.group(1))
            continue
        m = EXH_HEAD.match(t)
        if m:
            exhibits.add(f"{m.group(1).upper()} {m.group(2).upper()}")
        if not is_a:
            m2 = TITLE.search(t[:700])
            if m2:
                v = " ".join(m2.group(1).split()).upper().strip(" ,.")
                if len(v) > 6:
                    is_a = v
    return {"filed_as": filed, "is_a": is_a,
            # cover length is PRINTED, not guessed: total pages minus body pages
            "cover_pages": (total - count) if (total and count) else None,
            "total_pages": total, "body_pages": count,
            "exhibits": sorted(exhibits), "functions": sorted(fns),
            "regions": sorted(regions)}


def report():
    import bulk
    recs = {}
    for d in ("census_head", "devr_head"):
        p = HERE / d
        if p.exists():
            for f in p.glob("*.json"):
                recs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    if not recs:
        print("  nothing read yet")
        return
    ids = sorted(recs)
    ty = {}
    for r in bulk.socrata_in("bnx9-e6tj", "document_id", ids,
                             select="document_id,doc_type"):
        ty[r["document_id"]] = (r.get("doc_type") or "").strip()
    codes = json.loads((HERE / "_doctype_codes.json").read_text(encoding="utf-8"))
    UNDEF = {"PARTY 1", "PARTY ONE", "PARTY1"}

    by = collections.defaultdict(list)
    for d, rec in recs.items():
        by[ty.get(d, "?")].append(profile_one(rec))

    print(f"DOCUMENT-TYPE CENSUS — {len(recs):,} documents · "
          f"{len(by)} of 126 types held\n")
    hdr = (f"  {'TYPE':<9}{'n':>5}{'cover':>7}{'pages':>7}{'exh%':>6}"
           f"{'mis%':>6}  {'dir':<10}{'functions seen'}")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    out = {}
    for t in sorted(by, key=lambda k: -len(by[k])):
        v = by[t]
        cov = [x["cover_pages"] for x in v if x["cover_pages"] is not None]
        tp = [x["total_pages"] for x in v if x["total_pages"]]
        exh = sum(1 for x in v if x["exhibits"])
        # mis-filed = the instrument names itself something unrelated to its code
        desc = re.sub(r"[^A-Z]", "", (codes.get(t, {}).get(
            "doc__type_description") or "").upper())
        mis = 0
        named = 0
        for x in v:
            k = re.sub(r"[^A-Z]", "", (x["is_a"] or "").upper())
            if not k:
                continue
            named += 1
            if not any(w and w in k for w in (desc[:9], desc[:6])):
                mis += 1
        p1 = (codes.get(t, {}).get("party1_type") or "").strip()
        d = "published" if p1 and p1 not in UNDEF else "UNDEFINED"
        fns = collections.Counter(f for x in v for f in x["functions"])
        fstr = " ".join(f"{k}:{100*n//len(v)}%" for k, n in fns.most_common(4))
        print(f"  {t:<9}{len(v):>5}"
              f"{(statistics.median(cov) if cov else 0):>7.0f}"
              f"{(statistics.median(tp) if tp else 0):>7.0f}"
              f"{100*exh//max(len(v),1):>5}%"
              f"{(100*mis//named if named else 0):>5}%"
              f"  {d:<10}{fstr}")
        out[t] = {"n": len(v), "cover_pages_median": (statistics.median(cov) if cov else None),
                  "total_pages_median": (statistics.median(tp) if tp else None),
                  "pct_with_exhibits": 100*exh//max(len(v), 1),
                  "pct_misfiled": (100*mis//named if named else None),
                  "n_titled": named, "direction": d,
                  "functions": dict(fns),
                  "titles": collections.Counter(
                      x["is_a"] for x in v if x["is_a"]).most_common(4)}
    (HERE / "_census.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    print("\n  FUNCTION OVERLAP — which types touch which function")
    allf = sorted({f for t in out for f in out[t]["functions"]})
    print(f"    {'':<9}" + "".join(f"{f[:9]:>11}" for f in allf))
    for t in sorted(out, key=lambda k: -out[k]["n"]):
        row = "".join(
            f"{(str(100*out[t]['functions'].get(f,0)//out[t]['n'])+'%'):>11}"
            for f in allf)
        print(f"    {t:<9}{row}")

    print("\n  ⚠ every rate above is on the n in column two. A mis-file rate "
          "from 12\n    documents of one filing is not a rate. -> _census.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if not a.report:
        sweep(a.limit or None)
    report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
