"""Run the BSA decoder over a queue, and leave behind proof of what it touched.

THE THING THIS FILE IS ACTUALLY FOR

    Not throughput. The decoder already works on one document. What a run has to
    guarantee is that afterwards you can tell these four apart:

        decoded      read, facts written
        empty        read, and it genuinely says nothing about the envelope
        unreadable   image-only scan — the text is there, we cannot see it
        FAILED       fetch or parse blew up

    Collapsing any two of those is how a source reports 100% coverage while a
    fifth of it was never opened. So every calendar number in the queue gets a
    ledger row whatever happens to it, and the ledger is written BEFORE the run
    reports anything about itself.

Usage
    python bsa_run.py --where "application='BZ' and section='72-21'" --limit 40
    python bsa_run.py --all
    python bsa_run.py --report
"""
import argparse, json, os, pathlib, sys, time, traceback

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bsa
import runlock
import sink

LEDGER = pathlib.Path(os.environ.get(
    "BSA_LEDGER", pathlib.Path(__file__).with_name("bsa_ledger.jsonl")))
DECODES = pathlib.Path(os.environ.get(
    "BSA_DECODES", pathlib.Path(__file__).with_name("bsa_decodes.jsonl")))


def _append(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":"), default=str) + "\n")
        f.flush()


def done_already():
    if not LEDGER.exists():
        return {}
    out = {}
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            out[r["calendar"]] = r["decode_status"]
    return out


def run(rows, run_id=None, resume=True, emit=True, beat_every=10):
    run_id = run_id or f"bsa-{int(time.time())}"
    # ⚠ ONE WRITER PER SOURCE. Three separate corruptions came from two
    # processes appending to the same ledger; see runlock.py.
    _lock = runlock.Lock(bsa.SOURCE, run_id).acquire(script="bsa_run.py")
    total = len(rows)
    seen = done_already() if resume else {}
    sink.heartbeat(bsa.SOURCE, run_id, done=0, total=total,
                   note=f"{len(seen)} already in ledger")
    counts = {"decoded": 0, "empty": 0, "unreadable": 0, "FAILED": 0,
              "skipped": 0, "facts": 0}
    checks = {"PASS": 0, "FAIL": 0}
    fails = []
    for i, r in enumerate(rows, 1):
        cal = r.get("calendar") or f"row{i}"
        if resume and seen.get(cal) in ("decoded", "empty", "unreadable"):
            counts["skipped"] += 1
            continue
        rec = {"source": bsa.SOURCE, "calendar": cal, "run_id": run_id,
               "url": r.get("decisions_url"), "at": int(time.time())}
        try:
            p, how = bsa.fetch(r["decisions_url"], cal)
            if p is None:
                rec.update(decode_status="FAILED", note=how)
                counts["FAILED"] += 1
                fails.append((cal, how))
                _append(LEDGER, rec)
                continue
            d = bsa.decode(cal, p, r)
            rec["pages_total"] = d.get("pages")
            rec["fetch"] = how
            if d["status"] == "unreadable":
                rec.update(decode_status="unreadable", note=d.get("note"))
                counts["unreadable"] += 1
                _append(LEDGER, rec)
                _append(DECODES, d)
                continue
            ck = bsa.selfcheck(d)
            d["checks"] = ck
            for c in ck:
                checks[c["verdict"]] = checks.get(c["verdict"], 0) + 1
            fs = bsa.to_facts(d, run_id=run_id, emit=emit)
            env = d.get("envelope") or {}
            bs, bbl_prov = bsa.bbls(d)
            rec.update(decode_status="decoded" if fs else "empty",
                       facts=len(fs), pages_read=d.get("pages_read"),
                       bbls=bs, bbl_provenance=bbl_prov,
                       relief_kind=d.get("relief_kind"),
                       outcome=bsa.outcome_from_document(d)[0],
                       has_permitted=bool(env.get("permitted")),
                       has_granted=bool(env.get("granted")),
                       conditions=len(d.get("conditions") or []),
                       checks_failed=[c["check"] for c in ck
                                      if c["verdict"] == "FAIL"])
            counts["decoded" if fs else "empty"] += 1
            counts["facts"] += len(fs)
            _append(LEDGER, rec)
            _append(DECODES, d)
        except Exception as e:
            rec.update(decode_status="FAILED",
                       note=f"{type(e).__name__}: {e}",
                       trace=traceback.format_exc()[-800:])
            counts["FAILED"] += 1
            fails.append((cal, f"{type(e).__name__}: {e}"))
            _append(LEDGER, rec)
        if i % beat_every == 0:
            _lock.beat()
            sink.heartbeat(bsa.SOURCE, run_id, done=i, total=total,
                           note=json.dumps(counts))
    status = "complete" if counts["FAILED"] == 0 else "PARTIAL"
    sink.heartbeat(bsa.SOURCE, run_id, done=total, total=total, status=status,
                   note=json.dumps(counts))
    _lock.release()
    return {"run_id": run_id, "total": total, "counts": counts,
            "checks": checks, "failures": fails[:20]}


def report():
    rows = []
    if LEDGER.exists():
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    latest = {}
    for r in rows:
        latest[r["calendar"]] = r
    from collections import Counter
    st = Counter(r["decode_status"] for r in latest.values())
    print(f"BSA LEDGER — {len(latest):,} calendar numbers touched")
    for k, v in st.most_common():
        print(f"    {k:<12} {v:>7,}")
    dec = [r for r in latest.values() if r["decode_status"] == "decoded"]
    if dec:
        g = sum(1 for r in dec if r.get("has_granted"))
        p = sum(1 for r in dec if r.get("has_permitted"))
        c = sum(1 for r in dec if (r.get("conditions") or 0) > 0)
        bad = [r for r in dec if r.get("checks_failed")]
        print(f"\n  of {len(dec):,} decoded:")
        print(f"    granted envelope found   {g:>7,}  {g/len(dec)*100:5.1f}%")
        print(f"    permitted baseline found {p:>7,}  {p/len(dec)*100:5.1f}%")
        print(f"    at least one condition   {c:>7,}  {c/len(dec)*100:5.1f}%")
        print(f"    a self-check FAILED      {len(bad):>7,}  {len(bad)/len(dec)*100:5.1f}%")
        cf = Counter(x for r in dec for x in (r.get("checks_failed") or []))
        for k, v in cf.most_common():
            print(f"        {v:>6,}  {k}")
    print()
    sink.report()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--where")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--no-emit", action="store_true")
    ap.add_argument("--no-resume", action="store_true")
    a = ap.parse_args()
    if a.report:
        report()
        sys.exit()
    rows = bsa.index(where=a.where)
    rows.sort(key=lambda r: (r.get("filed") or ""), reverse=True)
    if a.limit:
        rows = rows[:a.limit]
    print(f"queue: {len(rows):,} decisions"
          f"{' (LIMITED — this is a sample, not the universe)' if a.limit else ''}")
    out = run(rows, emit=not a.no_emit, resume=not a.no_resume)
    print(json.dumps(out, indent=1, default=str))
