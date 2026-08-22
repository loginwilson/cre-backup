"""The corpus store — `store → query` replacing `fetch → decode → delete`.

WHY THIS EXISTS, AND WHY IT IS THE MOST VALUABLE CHANGE IN THE PROJECT

    Until now every ACRIS image was SCRAP: fetched, read, deleted. That rule was
    correct while the images were borrowed — but it carried a cost that only
    became visible on 2026-08-05, when EIGHT parser bugs were fixed in a single
    session:

        every document read BEFORE each fix stayed mis-read, forever.

    Nothing could be re-checked except the transcriptions already made, and the
    fetch ledger — doing its job — prevented ever fetching those pages again. A
    bearing misread as feet, a distance taken from a street number, a dropped
    fractional inch: all frozen into the record at the parser version that made
    them.

    With storage the arithmetic reverses. A parser fix becomes RETROACTIVE:
    "re-decode everything read by parser < v8" is a query over held bytes, not a
    re-fetch that the ledger forbids and the rate limit could never afford.

    That is why this matters far more than its size suggests. At ~25 documents a
    day, transient images make a trickle that EVAPORATES. Held images make a
    trickle that COMPOUNDS — a year is ~9,000 documents that keep improving.

DESIGN

    * **Content-addressed.** Files are keyed by SHA-256 of their bytes, so the
      same page fetched twice costs one copy and corruption is detectable.
    * **The manifest is the truth, not the directory.** A file on disk proves a
      fetch happened; its absence proves nothing. Every question — what do we
      hold, at what parser version, from where — is answered from the manifest.
    * **Nothing is deleted.** The one operation this module does not offer.
"""
import hashlib, json, os, pathlib, sys, time
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))

# Point at the external drive once there is one. A relative default keeps the
# module usable today without pretending 14 TB is available.
ROOT = pathlib.Path(os.environ.get("ACRIS_CORPUS", pathlib.Path(__file__).with_name("corpus")))
MANIFEST = ROOT / "manifest.jsonl"


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _blob_path(digest):
    # two levels of fan-out: 17M files in one directory is a filesystem problem
    return ROOT / "blobs" / digest[:2] / digest[2:4] / digest


import threading
_MANIFEST_LOCK = threading.Lock()
# ⚠ ADDED 2026-08-06 after a real failure. Four THREADS running put() produced a
# torn manifest line and a JSONDecodeError. The append-only design is safe
# across PROCESSES (each write is one small syscall), but threads in one process
# share the interpreter and can interleave between open/write/close. The blast
# radius was one unreadable line — records() skips it — so the symptom was a
# noisy traceback rather than lost data, which is exactly the kind of failure
# that gets ignored until it isn't.


def put(doc_id, page, data, content_type=None, source=None):
    """Store bytes permanently and record them. Returns the manifest record.

    Idempotent: storing the same bytes twice writes one blob and one additional
    manifest line noting the second sighting.
    """
    ROOT.mkdir(parents=True, exist_ok=True)
    dg = _digest(data)
    bp = _blob_path(dg)
    fresh = not bp.exists()
    if fresh:
        bp.parent.mkdir(parents=True, exist_ok=True)
        tmp = bp.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(bp)                     # atomic: no half-written blob
    rec = {"doc_id": doc_id, "page": str(page), "sha256": dg, "bytes": len(data),
           "content_type": content_type, "source": source, "stored_at": int(time.time()),
           "new_blob": fresh}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with _MANIFEST_LOCK:                     # threads must not interleave a line
        with open(MANIFEST, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
    return rec


def get(doc_id, page):
    """Bytes we already hold for this page, or None. Never fetches."""
    for r in reversed(records()):
        if r["doc_id"] == doc_id and r["page"] == str(page):
            bp = _blob_path(r["sha256"])
            if bp.exists():
                return bp.read_bytes()
    return None


def records():
    if not MANIFEST.exists():
        return []
    out = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue                    # torn last line after a hard kill
    return out


def held():
    """{doc_id: {pages}} — what the corpus actually contains."""
    h = {}
    for r in records():
        h.setdefault(r["doc_id"], set()).add(r["page"])
    return h


def needs_redecode(journal_path, parser_version):
    """Documents we HOLD that were last decoded by an older parser.

    THE POINT OF THE WHOLE MODULE. Impossible under fetch -> delete, because the
    bytes were gone and the fetch ledger forbade getting them again.
    """
    import batch
    jr = batch.Journal(journal_path)
    out = []
    for doc_id in held():
        r = jr._done.get(doc_id)
        if r is None or r.get("parser", 0) < parser_version:
            out.append({"doc_id": doc_id, "was": (r or {}).get("parser"),
                        "now": parser_version})
    return out


def verify(sample=None):
    """Re-hash stored blobs and report corruption. Three outcomes, never two."""
    recs = records()
    seen, ok, bad, missing = set(), 0, [], []
    for r in recs:
        dg = r["sha256"]
        if dg in seen:
            continue
        seen.add(dg)
        bp = _blob_path(dg)
        if not bp.exists():
            missing.append(r)
            continue
        if sample and len(seen) > sample:
            break
        if _digest(bp.read_bytes()) == dg:
            ok += 1
        else:
            bad.append(r)
    return {"blobs_checked": ok + len(bad), "ok": ok, "CORRUPT": bad,
            "MISSING": missing, "manifest_lines": len(recs)}


def stats():
    recs = records()
    h = held()
    blobs = {r["sha256"] for r in recs}
    total = 0
    for dg in blobs:
        bp = _blob_path(dg)
        if bp.exists():
            total += bp.stat().st_size
    return {"documents": len(h), "pages": sum(len(v) for v in h.values()),
            "unique_blobs": len(blobs), "manifest_lines": len(recs),
            "bytes": total, "root": str(ROOT)}


if __name__ == "__main__":
    if "--verify" in sys.argv:
        v = verify()
        print(json.dumps({k: (len(x) if isinstance(x, list) else x)
                          for k, x in v.items()}, indent=1))
        for r in v["CORRUPT"][:5]:
            print(f"  CORRUPT {r['doc_id']} p{r['page']} {r['sha256'][:16]}")
        sys.exit(1 if v["CORRUPT"] or v["MISSING"] else 0)
    s = stats()
    gb = s["bytes"] / 1024 ** 3
    print(f"corpus at {s['root']}")
    print(f"  {s['documents']:,} documents · {s['pages']:,} pages · "
          f"{s['unique_blobs']:,} unique blobs · {gb:,.2f} GB")
    print(f"  {s['manifest_lines']:,} manifest lines")
    if s["documents"]:
        import batch
        jp = pathlib.Path(__file__).with_name("batch_journal.jsonl")
        if jp.exists():
            n = len(needs_redecode(jp, batch.PARSER_VERSION))
            print(f"  {n:,} held documents need re-decoding at parser "
                  f"v{batch.PARSER_VERSION} — a QUERY, not a re-fetch")
    else:
        print("\n  empty. Set ACRIS_CORPUS to the external drive when it arrives:")
        print("     export ACRIS_CORPUS=/mnt/acris   (or D:\\acris on Windows)")
