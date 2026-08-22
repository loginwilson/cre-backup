"""Shared fact sink — many decoders writing at once, one timeline reading out.

LOGIN'S ARCHITECTURE, 2026-08-06:

    "multiple decoders running at once and then an all in one decoder that can
     timeline it all together and summarize ... one chat running acris, one
     running dob, one decoding comps from streeteasy"

That works, and the reason it works is that `facts.Fact` already carries
`source` + `document_id` + `page`. A fact is self-locating, so it does not
matter which process produced it or in what order they arrive.

WHY APPEND-ONLY JSONL AND NOT A SHARED TABLE

    Concurrent writers need either a database that arbitrates them or a format
    where arbitration is unnecessary. Append-only lines are the latter: on every
    platform this project runs on, a write smaller than the pipe buffer lands
    whole, so two decoders appending never interleave a single line. No locks,
    no server, no coordination — and a torn final line from a hard kill costs
    one fact, not the file.

    Supabase remains the query surface. This is the WRITE path, because a
    decoder mid-document should never be blocked by a network round trip.

⚠ THE FAILURE THIS DESIGN IS BUILT AGAINST

    Running four decoders quadruples throughput AND quadruples the ways a silent
    gap can appear. If the ACRIS decoder dies at document 40 of 200 while DOB
    finishes cleanly, a pooled timeline looks complete and is missing a third of
    the record — the exact failure this project has met eight times.

    So every decoder writes a HEARTBEAT with its denominator, and `coverage()`
    reports per source. A source that never wrote a heartbeat is reported as
    UNKNOWN, never as zero, because "no facts" and "never ran" look identical
    in the data and mean opposite things.
"""
import json, os, pathlib, sys, time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ROOT = pathlib.Path(os.environ.get("DECODER_SINK",
                                   pathlib.Path(__file__).with_name("sink")))
FACTS = ROOT / "facts.jsonl"
RUNS = ROOT / "runs.jsonl"
LEDGER = ROOT / "documents.jsonl"


def _append(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, separators=(",", ":")) + "\n"
    # one write, one line — the whole basis for lock-free concurrency
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def emit(fact, run_id=None):
    """One decoder writes one fact. Safe to call from any number of processes."""
    rec = dict(fact)
    rec["run_id"] = run_id
    rec["emitted_at"] = int(time.time())
    _append(FACTS, rec)
    return rec


def ledger(source, source_doc_id, *, bbls=None, doc_type=None, happened=None,
           recorded=None, decode_status="unread", pages_total=None, pages_read=0,
           run_id=None, **extra):
    """Record that a DOCUMENT EXISTS — before, and independently of, reading it.

    THIS IS TABLE 2 OF LEDGER_SCHEMA, and RULE_DOCUMENTS_NOT_INDEXES is why it
    has to exist separately from `facts`:

        an index row tells you a document exists. Only the document tells you
        what it says.

    So an index pull writes HERE, never to `facts`. Both are legitimate work and
    they are not the same work. Without this file, "no facts from DOS" and
    "20,832,961 DOS filings exist and none has been opened" are indistinguishable
    — and the second is a plan, while the first is a dead end.

    `decode_status` is the whole point: unread | queued | decoding | decoded |
    FAILED | unreadable. A ledger row with pages_read=0 is not a gap in the
    record; it is the record of a gap, which is the only kind you can act on.
    """
    _append(LEDGER, {"source": source, "source_doc_id": str(source_doc_id),
                     "bbls": [str(b) for b in (bbls or [])], "doc_type": doc_type,
                     "happened": happened, "recorded": recorded,
                     "decode_status": decode_status, "pages_total": pages_total,
                     "pages_read": pages_read, "run_id": run_id,
                     "at": int(time.time()), **extra})


PARTIES = ROOT / "parties.jsonl"


def party(source, name, *, bbls=None, entity_id=None, contact_name=None,
          address=None, status=None, run_id=None, **extra):
    """WHO a party is and WHERE to reach them. A THIRD kind of row, and it
    exists because it is neither of the other two.

    ⚠ WHY NOT A FACT. `facts.Fact` refuses to exist without document_id + page,
    and it is right to: a fact is an assertion read off a page. A
    service-of-process address is none of that — it is the register's CURRENT
    STATE, has no document behind it, no page, and no date on which it was
    "said". Forcing it into a Fact would mean inventing a page number, which is
    the precise dishonesty RULE_DOCUMENTS_NOT_INDEXES exists to stop.

    ⚠ WHY NOT A DOCUMENT LEDGER ROW EITHER. Nothing here is a document. The
    ledger answers "what exists, and have we read it". This answers "who signed,
    and how do we reach them".

    So it gets its own file, and its provenance is explicit in `basis`:
        register  — read off an agency's current-state record (no document)
        document  — read off a filed instrument (then it should be a Fact too)

    This is the decoder's actual deliverable for REACH. It is current-state and
    it OVERWRITES conceptually rather than accumulating: an address is true now,
    not true on a date, so a reader must take the latest row and never build a
    history out of these.
    """
    _append(PARTIES, {"source": source, "name": name,
                      "bbls": [str(b) for b in (bbls or [])],
                      "entity_id": entity_id, "contact_name": contact_name,
                      "address": address, "status": status, "basis": "register",
                      "run_id": run_id, "at": int(time.time()), **extra})


def parties(source=None, bbl=None):
    rows = _read(PARTIES)
    if source:
        rows = [r for r in rows if r.get("source") == source]
    if bbl:
        rows = [r for r in rows if bbl in (r.get("bbls") or [])]
    return rows


def documents(source=None, decode_status=None):
    rows = _read(LEDGER)
    if source:
        rows = [r for r in rows if r.get("source") == source]
    if decode_status:
        rows = [r for r in rows if r.get("decode_status") == decode_status]
    return rows


def heartbeat(source, run_id, *, done, total, status="running", note=""):
    """Declare progress AND ITS DENOMINATOR.

    `done` alone is a number that cannot be wrong and cannot be useful. `total`
    is what makes 40 either "finished" or "a fifth of the way, and it stopped".
    """
    _append(RUNS, {"source": source, "run_id": run_id, "done": done,
                   "total": total, "status": status, "note": note,
                   "at": int(time.time())})


def _read(path):
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                continue                # torn last line after a hard kill
    return out


RETRACTIONS = ROOT / "retractions.jsonl"


def retract(source, *, field, values, reason, run_id=None):
    """Withdraw already-written facts. ADDITIVE — nothing is deleted.

    ⚠ WHY THIS EXISTS, added 2026-08-06 by the BSA/LPC/DCP decoder.

        The sink is append-only, so a batch written by a parser later found to
        be wrong cannot be removed. Until now the remedy was a heartbeat NOTE
        saying "bsa/1 is superseded" — and a note in `runs.jsonl` is invisible
        to anyone reading `facts.jsonl`, which is everyone. 8,891 facts written
        from a bad parser, and a retraction nobody would ever see.

        That is the failure this project keeps meeting in new clothes: the
        record looks complete, and the thing that would tell you otherwise is
        somewhere you had no reason to look.

    A retraction names a source and a field/value set — `bsa_parser` in
    ("bsa/1","bsa/2","bsa/3") — and `facts()` applies it BY DEFAULT. A caller
    who wants the raw file asks for it explicitly.
    """
    _append(RETRACTIONS, {"source": source, "field": field,
                          "values": list(values), "reason": reason,
                          "run_id": run_id, "at": int(time.time())})


def retractions():
    return _read(RETRACTIONS)


def is_retracted(fact, rules=None):
    for r in (retractions() if rules is None else rules):
        if r.get("source") and fact.get("source") != r["source"]:
            continue
        if fact.get(r["field"]) in r["values"]:
            return True
    return False


def facts(source=None, bbl=None, include_retracted=False):
    rows = _read(FACTS)
    if not include_retracted:
        rules = retractions()
        if rules:
            rows = [r for r in rows if not is_retracted(r, rules)]
    if source:
        rows = [r for r in rows if r.get("source") == source]
    if bbl:
        rows = [r for r in rows if bbl in (r.get("bbls") or [])]
    return rows


def coverage():
    """Per-source progress. THREE states, and the third is the important one.

        complete   a run reported status=complete
        PARTIAL    a run started and its last heartbeat is short of total
        UNKNOWN    no heartbeat at all — the decoder may never have started,
                   and this is NOT the same as "found nothing"
    """
    runs = _read(RUNS)
    latest = {}
    for r in runs:
        k = (r["source"], r["run_id"])
        if k not in latest or r["at"] >= latest[k]["at"]:
            latest[k] = r
    per = defaultdict(lambda: {"done": 0, "total": 0, "status": "UNKNOWN"})
    for (src, _), r in latest.items():
        p = per[src]
        p["done"] += r.get("done") or 0
        p["total"] += r.get("total") or 0
        if r.get("status") == "complete" and p["status"] != "PARTIAL":
            p["status"] = "complete"
        elif r.get("status") != "complete":
            p["status"] = "PARTIAL"
    counts = defaultdict(int)
    for f in _read(FACTS):
        counts[f.get("source") or "?"] += 1
    for src in counts:
        per[src]["facts"] = counts[src]
    for src in per:
        per[src].setdefault("facts", 0)
    return dict(per)


def report():
    cov = coverage()
    if not cov:
        print("sink is empty — no decoder has written yet")
        print(f"  set DECODER_SINK to share one sink across chats "
              f"(currently {ROOT})")
        return
    print(f"SINK — {ROOT}\n")
    print(f"  {'source':<14}{'facts':>8}{'done':>8}{'total':>8}  status")
    for src, p in sorted(cov.items()):
        note = {"complete": "",
                "UNKNOWN": "  <- NEVER RAN (not the same as 'found nothing')"}.get(
                    p["status"], "")
        if p["status"] == "PARTIAL":
            # ⚠ two different situations were being shown identically:
            #   done < total   -> the run genuinely stopped short
            #   done == total  -> it processed everything but never declared
            #                     complete, so we cannot tell a finished run
            #                     from one that died on its last step.
            # Both are "not confirmed complete", but they are not the same
            # doubt, and reading them as one under-reports finished work.
            note = ("  <- STOPPED SHORT" if p["done"] < p["total"]
                    else "  <- reached total but never declared complete")
        print(f"  {src:<14}{p['facts']:>8,}{p['done']:>8,}{p['total']:>8,}"
              f"  {p['status']}{note}")
    led = _read(LEDGER)
    if led:
        per = defaultdict(lambda: {"n": 0, "read": 0})
        for r in led:
            p = per[r.get("source") or "?"]
            p["n"] += 1
            p["read"] += 1 if r.get("decode_status") == "decoded" else 0
        print(f"\n  DOCUMENT LEDGER — what is known to EXIST, and how much of it "
              f"has been opened")
        print(f"  {'source':<14}{'documents':>11}{'decoded':>9}")
        for src, p in sorted(per.items()):
            flag = "  <- catalogued, NONE read" if p["read"] == 0 else ""
            print(f"  {src:<14}{p['n']:>11,}{p['read']:>9,}{flag}")

    partial = [s for s, p in cov.items() if p["status"] != "complete"]
    if partial:
        print(f"\n  ⚠ {len(partial)} source(s) not complete: {', '.join(partial)}")
        print(f"    A pooled timeline built now WILL look finished and will not be.")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        import facts as F
        rid = "demo-1"
        heartbeat("ACRIS", rid, done=0, total=41)
        emit(F.Fact("consideration_paid", document_id="2010102601040006", page=1,
                    bbls=["1008000053"], happened="2010-10-14", value=5_000_000,
                    unit="USD", confidence="derived",
                    derivation="RPTT $131,250/0.02625 = RETT $20,000/0.004"), rid)
        emit(F.Fact("declaration_recorded", document_id="FT_1670008616267", page=1,
                    bbls=["1008000053"], happened="1979-11-14", source="ACRIS",
                    verbatim="IN REM TAX FORECLOSURE ACTION NO. 29 ... VACATE ORDER",
                    note="City tax foreclosure vacated — indexed as MISC"), rid)
        heartbeat("ACRIS", rid, done=2, total=41)
        heartbeat("DOB", "demo-2", done=12, total=12, status="complete")
    report()
