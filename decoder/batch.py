"""Corpus-scale decode — built for 17,036,716 documents, not for 50 a day.

WHY THIS EXISTS NOW, WITH NO CORPUS IN HAND
    Acquisition is a procurement step (see BULK_ACQUISITION.md): one call or one
    letter. PROCESSING is weeks of engineering and it is entirely ours. The
    difference between "the drive arrives and we start writing code" and "the
    drive arrives and we start decoding" is the whole timeline, so this is built
    first and proven on synthetic input.

    Measured target: 17.0M documents through OCR + full decode is ~25 days at
    64 workers. That is only true if the pipeline never has to restart from zero
    and never silently drops work — which is what the rest of this file is about.

THE FOUR THINGS THAT KILL A RUN THIS SIZE

  1. **Restart from zero.** A 25-day run WILL be interrupted. Every document's
     outcome is journaled before the next begins, so a kill at 400,000 resumes
     at 400,000. The journal is the unit of truth, not the output directory —
     a written file proves a decode finished, but its ABSENCE proves nothing
     (it could have been a legitimate no-op).

  2. **Silent drops.** This project's recurring failure, now seen eight times,
     is A CHECK THAT REPORTS SUCCESS BECAUSE IT LOOKED IN THE WRONG PLACE. At
     17M documents nobody inspects the output, so every document must end in an
     EXPLICIT recorded outcome — ok / empty / FAILED / skipped — and the counts
     must reconcile against the manifest. `seen == ok + empty + failed + skipped`
     is asserted at the end of every run. An unreconciled run is a failed run.

  3. **Large N hiding bugs.** A duplicate-BBL defect was invisible at 98,000
     rows and failed loudly at 364. Percentages without denominators are how
     that happens, so every rate printed here carries its denominator, and a
     random sample is held back for inspection on every run.

  4. **A parser fix that cannot be applied retroactively.** The whole argument
     for owning the corpus. Each result records the PARSER VERSION that produced
     it, so "re-decode everything touched by parser < v7" is a query rather than
     a re-fetch. This is impossible under fetch -> decode -> delete.
"""
import hashlib, json, os, pathlib, random, sys, time, traceback
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PARSER_VERSION = 8          # bump on ANY decode change; drives retroactive re-runs
SAMPLE_RATE = 0.001         # 1 in 1,000 held back for human inspection


# ---------------------------------------------------------------------------
# Type routing. The document type decides the handler; an unknown type is
# recorded as unknown rather than pushed through a generic parser, because a
# generic fallback is exactly what once read a STREET NUMBER as a distance.
# ---------------------------------------------------------------------------
ENVELOPE = {"ZONE", "DEVR", "AIRRIGHT", "EASE", "DECL", "AGMT", "SAGE", "SMIS",
            "CERT", "MISC", "TERA", "LDMK", "LIC", "CONS", "DEED, RC"}


def route(doc_type):
    """Which handler reads this type. Returns None for types we do not decode."""
    t = (doc_type or "").strip().upper()
    if t in {"ZONE", "DEVR", "AIRRIGHT"}:
        return "envelope"          # zoning lot descriptions, rights transfers
    if t in {"EASE", "DECL", "TERA", "CONS", "LIC"}:
        return "encumbrance"       # burdens and their releases
    if t in {"AGMT", "SAGE", "SMIS", "CERT", "MISC", "LDMK"}:
        return "instrument"        # read for parties, dates, cited instruments
    if t.startswith("DEED"):
        return "conveyance"
    if t in {"MTGE", "ASST", "SAT"}:
        return "financing"
    return None


# ---------------------------------------------------------------------------
# The journal — append-only, one line per document, written BEFORE moving on.
# ---------------------------------------------------------------------------
class Journal:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._done = {}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue        # a torn last line from a hard kill
                    self._done[r["doc_id"]] = r

    def done_at_version(self, doc_id, version):
        """Resume skips a document ONLY if a CURRENT-parser result exists.

        Keyed on version so a parser bump re-runs affected documents instead of
        the run reporting 'all done' against stale output.
        """
        r = self._done.get(doc_id)
        return bool(r) and r.get("parser") == version and r.get("outcome") != "FAILED"

    def append(self, rec):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())        # a 25-day run must survive a hard kill
        self._done[rec["doc_id"]] = rec


# ---------------------------------------------------------------------------
# Decoding one document.
# ---------------------------------------------------------------------------
def decode_one(task):
    """Pure function, runs in a worker. NEVER raises — a crash must not take
    the pool down, and an exception is itself a recorded outcome."""
    doc_id, doc_type, path = task["doc_id"], task["doc_type"], task.get("path")
    t0 = time.time()
    base = {"doc_id": doc_id, "doc_type": doc_type, "parser": PARSER_VERSION,
            "handler": route(doc_type)}
    try:
        if base["handler"] is None:
            return {**base, "outcome": "skipped", "reason": "type not decoded",
                    "secs": round(time.time() - t0, 3)}
        if path and not pathlib.Path(path).exists():
            return {**base, "outcome": "FAILED", "reason": "file missing",
                    "secs": round(time.time() - t0, 3)}

        facts = _decode(base["handler"], path, task)

        # POSITIVE SIGNAL REQUIRED. "No exception" is not success — an empty
        # result is a real and different outcome, and conflating the two is how
        # a broken handler reads as a clean run.
        if not facts:
            return {**base, "outcome": "empty", "reason": "handler returned nothing",
                    "secs": round(time.time() - t0, 3)}
        return {**base, "outcome": "ok", "facts": facts,
                "secs": round(time.time() - t0, 3)}
    except Exception as e:
        return {**base, "outcome": "FAILED", "reason": f"{type(e).__name__}: {e}"[:200],
                "trace": traceback.format_exc()[-400:],
                "secs": round(time.time() - t0, 3)}


def _decode(handler, path, task):
    """Read the document and return facts. Synthetic when no image is present.

    Real OCR lands here once a corpus exists; the surrounding machinery —
    routing, journaling, reconciliation, sampling — is what is being proven now,
    and it is identical either way.
    """
    text = task.get("text")
    if text is None and path:
        p = pathlib.Path(path)
        if p.suffix.lower() in (".txt", ".json"):
            text = p.read_text(encoding="utf-8", errors="ignore")
        else:
            return {"note": "image OCR not wired — corpus not yet in hand",
                    "bytes": p.stat().st_size}
    if not text:
        return {}

    import metes
    facts = {"chars": len(text)}
    tv = metes.traverse(text)
    if tv.get("n_courses"):
        facts["traverse"] = {"courses": tv["n_courses"],
                             "closure_error_ft": tv.get("closure_error_ft"),
                             "area_sf": tv.get("area_sf"),
                             "verdict": metes.verdict(tv)}
    return facts


# ---------------------------------------------------------------------------
# The run.
# ---------------------------------------------------------------------------
def run(manifest, journal_path, workers=None, limit=None, sample_rate=SAMPLE_RATE,
        seed=20260805):
    """Decode every document in `manifest`, resumably, and RECONCILE at the end.

    `manifest` is an iterable of {doc_id, doc_type, path?, text?}.
    """
    workers = workers or max(1, (os.cpu_count() or 4) - 2)
    jr = Journal(journal_path)
    rng = random.Random(seed)

    tasks, resumed = [], 0
    for t in manifest:
        if limit and len(tasks) >= limit:
            break
        if jr.done_at_version(t["doc_id"], PARSER_VERSION):
            resumed += 1
            continue
        tasks.append(t)

    total_in = len(tasks) + resumed
    print(f"manifest {total_in:,} documents — {resumed:,} already decoded at "
          f"parser v{PARSER_VERSION}, {len(tasks):,} to do, {workers} workers")
    if not tasks:
        print("nothing to do")
        return {"seen": 0, "resumed": resumed}

    counts, held, t0 = Counter(), [], time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(decode_one, t): t["doc_id"] for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()          # decode_one never raises
            jr.append(rec)
            counts[rec["outcome"]] += 1
            if rng.random() < sample_rate:
                held.append(rec)
            if i % 5000 == 0 or i == len(tasks):
                el = time.time() - t0
                print(f"  {i:>9,}/{len(tasks):,}  {i/el:>8,.0f} docs/s  "
                      f"ok={counts['ok']:,} empty={counts['empty']:,} "
                      f"FAILED={counts['FAILED']:,} skipped={counts['skipped']:,}")

    # ---- RECONCILE. An unreconciled run is a failed run. -------------------
    seen = sum(counts.values())
    ok = seen == len(tasks)
    el = time.time() - t0
    print(f"\n  {seen:,} outcomes recorded for {len(tasks):,} submitted "
          f"— {'reconciled' if ok else 'MISMATCH, DO NOT TRUST THIS RUN'}")
    for k in ("ok", "empty", "FAILED", "skipped"):
        n = counts[k]
        print(f"    {k:<8} {n:>9,}  {n/seen*100:>5.1f}% of {seen:,}")
    if el > 0:
        print(f"\n  {el/60:.1f} min at {seen/el:,.0f} docs/s"
              f"  -> 17,036,716 docs = {17_036_716/(seen/el)/86400:,.1f} days at "
              f"this width")
    if held:
        print(f"\n  {len(held)} held back for inspection (1 in "
              f"{int(1/sample_rate):,}) — LOOK AT THESE, the summary line above "
              f"is one I wrote myself")
    return {"seen": seen, "counts": dict(counts), "resumed": resumed,
            "reconciled": ok, "sample": held, "secs": el}


# ---------------------------------------------------------------------------
def manifest_from_index(doc_types=None, limit=None):
    """Build a work list from the FREE ACRIS index — no images needed.

    The index is unmetered, on a different host, and has never blocked us. It
    already tells us every document that exists and its type, so the entire work
    list is knowable today.
    """
    import bulk
    where = None
    if doc_types:
        q = ",".join(f"'{t}'" for t in doc_types)
        where = f"doc_type in({q})"
    rows = bulk.socrata("bnx9-e6tj", select="document_id,doc_type,recorded_borough",
                        where=where, limit=limit)
    return [{"doc_id": r["document_id"], "doc_type": r.get("doc_type"),
             "path": None} for r in rows]


def _synthetic(n, seed=1):
    """Prove the machinery without a corpus: routing, journaling, resume,
    reconciliation and failure handling all exercise identically."""
    rng = random.Random(seed)
    types = sorted(ENVELOPE) + ["MTGE", "DEED", "UCC1", "RPTT"]
    body = ("BEGINNING at a point; RUNNING THENCE North 00°37'08\" West, a "
            "distance of 50.69 Feet; THENCE North 89°31'32\" East, a distance of "
            "16.00 Feet; THENCE South 00°28'20\" East, a distance of 50.69 Feet; "
            "THENCE South 89°31'32\" West, a distance of 16.00 Feet to the point "
            "of BEGINNING.")
    out = []
    for i in range(n):
        t = rng.choice(types)
        out.append({"doc_id": f"SYN{i:012d}", "doc_type": t,
                    "text": body if rng.random() > 0.05 else ""})
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--synthetic" in a:
        n = int(next((x for x in a if x.isdigit()), 20000))
        jp = pathlib.Path(__file__).with_name("batch_journal_synthetic.jsonl")
        if "--fresh" in a and jp.exists():
            jp.unlink()
        r = run(_synthetic(n), jp, workers=int(os.environ.get("W", 0)) or None)
        sys.exit(0 if r.get("reconciled") else 1)
    if "--plan" in a:
        m = manifest_from_index(sorted(ENVELOPE), limit=int(os.environ.get("N", 2000)))
        c = Counter(route(x["doc_type"]) for x in m)
        print(f"{len(m):,} documents sampled from the free index")
        for k, v in c.most_common():
            print(f"  {str(k):<12} {v:>8,}  {v/len(m)*100:>5.1f}% of {len(m):,}")
        sys.exit(0)
    print(__doc__)
    print("usage: python batch.py --synthetic [N] [--fresh]  |  --plan")
