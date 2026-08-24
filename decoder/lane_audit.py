"""LANE AUDIT — are we erroring, or do code defects silently lose docs?

    python lane_audit.py            # one read-only pass, ~a minute

login (2026-08-24): "we should build to make sure we arent erroring or there
are code defects causing us to lose out." Read-only, sampled, ZERO ACRIS
requests. Five invariants, each printed as n-checked / n-failed with ids —
a rate without a denominator is banned (CLAUDE.md rule 4).

 1 SOURCE-COUNT MATCH  sampled landed pdfs' actual page count equals the
                       rd row's own `pages` (ACRIS's stated count). Catches
                       any Short that slipped the frames==total trap.
 2 FILE EXISTS         sampled pdf paths in the column exist on disk,
                       nonzero. Catches a write that landed the column but
                       lost the file.
 3 FAILS NEVER WROTE   every id in the fail logs is either still todo
                       (honest) or has since landed WITH a valid file
                       (healed by retry). A filled column with a missing or
                       empty file = the defect this exists to catch.
 4 KEY LOCKSTEP        rd rows landed since the key_on_rd trigger (their rd
                       JSON `at` >= 2026-08-22) carry keyed_by. Catches the
                       trigger silently not firing.
 5 NO ORPHAN FILES     sampled todo rows have no file already sitting in
                       the store — a file without a column entry is a lost
                       write (work done, never recorded, re-fetched forever).
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sqlite3
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
W = CP.NAV_WORK
PAGE_RE = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
SAMPLE = 60

con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=60)
con.execute("PRAGMA busy_timeout=60000")
random.seed()
fails_total = 0


def sample_rows(pred, n=SAMPLE, bands=("2003", "2026")):
    """Point-probe sampling on the PK — the predicate runs in PYTHON.
    ⚠ Putting it in SQL turned each probe into an unbounded range scan
    wherever the predicate is sparse (a filtered `id >= probe LIMIT 1`
    walks rows until one matches — measured: the first audit run hung for
    2h+ on exactly this). An unfiltered probe is one index lookup; a probe
    that lands on a non-matching row is simply resampled."""
    out, seen = [], set()
    for _ in range(n * 20):
        if len(out) >= n:
            break
        band = random.choice(bands)
        probe = band + "%012d" % random.randrange(0, 10 ** 12)
        r = con.execute(
            "SELECT id, recorded_details, pdf, keyed_by FROM navigation"
            " WHERE id >= ? ORDER BY id LIMIT 1", (probe,)).fetchone()
        if r and r[0] not in seen and not r[0].startswith("RC_") and pred(r):
            seen.add(r[0])
            out.append(r)
    return out


def pdf_pages(path):
    try:
        return len(PAGE_RE.findall(path.read_bytes()))
    except OSError:
        return -1


def verdict(name, checked, bad):
    global fails_total
    fails_total += len(bad)
    print("%-18s %d checked · %d FAILED%s"
          % (name, checked, len(bad),
             ("  -> " + ", ".join(str(b) for b in bad[:6])) if bad else ""))


# 1+2 — landed pdfs: file exists, page count == rd's own claim
rows = sample_rows(lambda r: r[2] not in ("", "imageless"))
bad_count, bad_file, n_counted = [], [], 0
for did, rd, rel, _k in rows:
    p = STORE / rel
    if not p.exists() or p.stat().st_size == 0:
        bad_file.append(did)
        continue
    try:
        want = int(json.loads(rd).get("pages") or 0)
    except Exception:
        want = 0
    if want > 0:
        n_counted += 1
        got = pdf_pages(p)
        # ⚠ MORE pages than rd claims is CORRECT, not a defect (verified by
        # eye 2026-08-24 on 2003040100001001: the extras are the City
        # Register's own RECORDING AND ENDORSEMENT COVER PAGE — "this page
        # is part of the instrument", it carries the RPTT/RETT stamps our
        # price rule reads — plus party-continuation and endorsement pages).
        # The defect direction is only FEWER: pages the source claims that
        # we failed to hold.
        if got < want:
            bad_count.append("%s(%d<%d)" % (did, got, want))
verdict("file-exists", len(rows), bad_file)
verdict("source-count", n_counted, bad_count)

# 3 — fail logs: nothing half-written
bad, ids = [], set()
for name in ("acris_lane_fails.jsonl", "acris_lane_pdf_fails.jsonl",
             "image_walk_fails.jsonl"):
    f = W / name
    if not f.exists():
        continue
    for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ids.add(json.loads(ln)["id"])
        except Exception:
            pass
ids = random.sample(sorted(ids), min(len(ids), 400))
healed = todo = 0
for did in ids:
    r = con.execute("SELECT pdf FROM navigation WHERE id=?", (did,)).fetchone()
    if not r:
        continue
    v = r[0] or ""
    if v in ("", "imageless"):
        todo += 1
    else:
        p = STORE / v
        if p.exists() and p.stat().st_size > 0:
            healed += 1
        else:
            bad.append(did)
verdict("fails-never-wrote", len(ids), bad)
print("                   (of failed ids: %d still todo · %d healed by retry)"
      % (todo, healed))

# 4 — key lockstep on trigger-era rd landings
rows = sample_rows(lambda r: (r[1] or "") != "")
bad, n = [], 0
for did, rd, _p, kb in rows:
    try:
        at = json.loads(rd).get("at") or ""
    except Exception:
        at = ""
    if at >= "2026-08-22":
        n += 1
        if not (kb or ""):
            bad.append(did)
verdict("key-lockstep", n, bad)

# 5 — orphan files on todo rows
rows = sample_rows(lambda r: r[2] == "" and (r[1] or "") != "")
bad = []
for did, rd, _p, _k in rows:
    try:
        rec = json.loads(rd).get("recorded", "")
    except Exception:
        rec = ""
    f = CP.doc_store_dir(did, rec) / ("%s.pdf" % did)
    if f.exists():
        bad.append(did)
verdict("no-orphans", len(rows), bad)

print("AUDIT %s" % ("CLEAN — no evidence of silent loss"
                    if fails_total == 0 else
                    "FOUND %d DEFECT(S) — investigate above" % fails_total))
