"""SELECTION -> SUPABASE. The 17M-document work-list, off one local disk.

    python push_selection.py --limit 5000      # measure rate and row size first
    python push_selection.py                   # full run, resumable
    python push_selection.py --verify          # count only, push nothing

⚠ THIS IS THE STAGE THAT ONLY EXISTS IN ONE PLACE. `acris_maps.jsonl` is 3.85 GB
holding 17,049,740 mapped documents - every document_id in ACRIS with its page
count and its instrument / supporting / tax-return page ranges. Supabase's
`document_map` was created for exactly this and holds ZERO rows. The mapping run
that produced it took hours against ACRIS and pinned concurrency at 128; losing
that file means asking ACRIS for all of it again.

Selection is the stage every later stage is keyed on: acquisition fetches
document_id + page range, extraction reads what acquisition wrote, resolution
walks the lineage across document_ids. If the work-list is unreproducible then
nothing downstream can be re-derived, only re-guessed.

⚠ IDEMPOTENT ON document_id. The mapper APPENDS - re-runs and delta runs write
the same doc_id again, and `_map_verified.json` counts 17,049,740 "mapped"
against a file with more lines than that. An INSERT would multiply documents and
inflate every page-count projection built on top. Every write here is an upsert
that merges over itself, so re-running is always safe and always converges.

⚠ IT RESUMES ON BYTE OFFSET, NOT ROW NUMBER. A 3.85 GB stream will be
interrupted - by the laptop sleeping, by a transient SSL drop at row ~250k
(measured, in supabase_sync), by the user closing the lid. Re-reading 3.85 GB to
find where it stopped costs more than the push. The offset is written after each
confirmed batch, so a kill loses at most one batch and that batch is idempotent.

⚠ AND IT PRINTS DENOMINATORS. "pushed 17M rows" is unverifiable and this project
has been burned by exactly that shape three times. Lines read, rows sent, rows
Supabase actually holds, and whether those reconcile.
"""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import supabase_sync as S

HERE = pathlib.Path(__file__).parent
SRC = pathlib.Path(os.environ.get("ACRIS_MAPS", HERE / "acris_maps.jsonl"))
STATE = HERE / "_push_selection_state.json"
TABLE = "document_map"
# ⚠ MEASURED 2026-08-13 AGAINST THE LIVE TABLE, not chosen. Per-request latency
# is ~85% of wall time, so the lever is rows-per-request and requests-in-flight:
#     serial batch  1,000   799 ms/req    1,251 rows/s   <- the old default
#     serial batch  2,500  1,050 ms/req   2,381 rows/s
#     serial batch  5,000  2,683 ms/req   1,864 rows/s   <- past the knee
#     batch        10,000  HTTP 500                      <- refused outright
#     conc 4 x batch 2,500                3,193 rows/s   <- best observed
#     conc 6 x batch 2,500                2,067 rows/s   <- contention
# So 2,500 x 4. Bigger batches lose to per-statement cost on a growing ON
# CONFLICT index; more concurrency loses to contention on the same index.
BATCH = 2500
CONC = 4


class Gate:
    """AIMD on BATCH SIZE, because the ceiling MOVES as the table grows.

    ⚠ MEASURED THE HARD WAY 2026-08-13. 2,500 x 4 was measured as optimal at
    ~5.7M rows. At ~7M the same statement started returning
        HTTP 500 {"code":"57014","message":"canceling statement due to
                  statement timeout"}
    on all four concurrent writes at once — the ON CONFLICT merge against a
    bigger index simply takes longer than Supabase's statement timeout allows.
    Retrying the SAME oversized statement is patience without learning: it did
    recover (8 stalls, 8 recoveries) but each cost ~30 s, and the frequency only
    goes one way from here. **A tuned constant is a measurement of one moment.**

    So: a statement timeout HALVES the batch and drops concurrency to 2; a run
    of clean waves grows the batch back by 25%. Same shape as the ACRIS fetch
    gate that already governs image acquisition — the difference is that this
    one is reacting to work it is itself making heavier.

    ⚠ 57014 IS NOT A NETWORK ERROR AND MUST NOT BE TREATED AS ONE. A dropped
    SSL connection means "try again unchanged". A statement timeout means "you
    asked for too much" — identical HTTP 500 to the caller, opposite remedy.
    Telling them apart is the whole point of reading the error body.
    """
    # ⚠ MAX WAS 2,500 AND THAT IS WHY THE JOB CRAWLED. Measured 2026-08-13
    # against the depleted instance, on GENUINELY NEW rows (inserts, which is
    # what the push does — merges are far cheaper and measuring those flattered
    # every earlier number):
    #      250 new rows  0.41s   610 rows/s   OK
    #      500 new rows  0.72s   694 rows/s   OK
    #    1,000 new rows  8.62s   statement timeout
    #    2,000 new rows  9.59s   statement timeout
    # The ceiling for an INSERT statement is between 500 and 1,000. But the
    # gate's own ratchet (x1.25 after 8 clean waves, up to MAX) kept CLIMBING
    # INTO that wall: 500 -> 625 -> 782 -> timeout -> halve to 250 -> cool down
    # 5 min -> climb again. It spent its life in the failure zone and its
    # recovery, and delivered **46 rows/s end-to-end while a working statement
    # runs at ~690**. The gate was not protecting throughput, it was consuming
    # it.
    # ⇒ Cap MAX at the MEASURED safe size. An AIMD ceiling set above what the
    # system accepts is not a ceiling, it is a metronome for failure.
    MIN, MAX = 250, 500
    COOLDOWN = 300                      # 5 min, measured: recovery took ~15

    def __init__(self, batch=BATCH, conc=CONC):
        self.batch, self.conc = batch, conc
        self.clean = 0
        self.timeouts = 0
        self.at_floor = 0

    def too_heavy(self):
        self.timeouts += 1
        self.clean = 0
        old = self.batch
        self.batch = max(self.MIN, self.batch // 2)
        self.conc = 2
        if self.batch != old:
            print(f"    GATE: statement timeout -> batch {old} -> {self.batch}, "
                  f"conc {self.conc}", flush=True)
            self.at_floor = 0
            return
        # ⚠ AT THE FLOOR, HALVING DOES NOTHING AND RETRYING MAKES IT WORSE.
        # 2026-08-13: the gate reached batch 250 x conc 2 and kept timing out;
        # every 2-second retry added load to an instance that was ALREADY the
        # bottleneck, so the thing meant to relieve pressure was applying it.
        # Measured after stopping for ~15 minutes: an indexed count went
        # 23.5s -> 0.4s and 250-row upserts went from timing out to 0.7s.
        # THE INSTANCE RECOVERS ON ITS OWN IF YOU LET IT. So once the smallest
        # batch we have still fails, the only useful move is to stop asking.
        self.at_floor = getattr(self, "at_floor", 0) + 1
        if self.at_floor >= 3:
            self.at_floor = 0
            print(f"    GATE: still timing out at the {self.MIN}-row floor — "
                  f"COOLING DOWN {self.COOLDOWN // 60} min. The database is the "
                  "bottleneck; retrying harder is what deepened it last time.",
                  flush=True)
            time.sleep(self.COOLDOWN)

    def ok(self):
        self.clean += 1
        if self.clean >= 8 and self.batch < self.MAX:
            old = self.batch
            self.batch = min(self.MAX, int(self.batch * 1.25) + 1)
            self.clean = 0
            print(f"    GATE: {old} -> {self.batch} after 8 clean waves",
                  flush=True)


GATE = Gate()


def row(d):
    """One JSONL map record -> one document_map row.

    ⚠ A MISSING RANGE IS null, NEVER 0. `supporting: null` means the document has
    no supporting pages; `supporting_from: 0` would read as "starts at page 0"
    and acquisition would fetch a page that does not exist. Page numbers in this
    corpus are 1-based.
    """
    ins = d.get("instrument") or [None, None]
    sup = d.get("supporting") or [None, None]
    tax = d.get("tax_return") or [None, None]
    tot = d.get("hid_TotalPages")
    return {
        "document_id": d["doc_id"],
        "doc_type": d.get("doc_type"),
        "recorded_date": d.get("recorded") or None,
        "total_pages": tot,
        "cover_pages": d.get("hid_Cov"),
        "instrument_from": ins[0],
        "instrument_to": ins[1],
        "supporting_from": sup[0],
        "tax_return_from": tax[0],
        # ⚠ no_image IS NOT "the fetch failed". It is the mapper's finding that
        # ACRIS holds no image for this document at all - a real and permanent
        # property of the record, and the reason acquisition must not treat a
        # zero-page document as a bug to retry forever.
        "no_image": (not tot) or tot == 0,
    }


def save_state(off, sent):
    """Checkpoint ATOMICALLY. The plain write destroyed the resume point.

    ⚠ FOUND 2026-08-13 THE ONLY WAY IT CAN BE FOUND — by losing one.
    `STATE.write_text(...)` truncates the file, then writes. The process was
    killed between those two steps and the checkpoint was left as **39 bytes of
    NUL** — not corrupt-looking, not empty, just unreadable. The 3-hour job's
    entire resume point, gone, while the log still showed it had reached 50%.
    A checkpoint that can be destroyed by the very event it exists to survive is
    not a checkpoint.

    Write to a sibling temp file, flush, fsync, then os.replace — which is
    atomic on NTFS and POSIX alike. A kill now leaves EITHER the old state or
    the new one, never a hole.
    """
    tmp = STATE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"offset": off, "sent": sent}, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, STATE)


def load_state():
    """Read the checkpoint, TREATING UNREADABLE AS UNKNOWN rather than as zero.

    A corrupt state file silently read as {} restarts a 17M-row push from the
    beginning — hours of work, and it would look like normal operation.
    """
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text())
    except Exception as e:
        print(f"  ⚠ CHECKPOINT UNREADABLE ({type(e).__name__}) — "
              f"{STATE.name} holds {STATE.stat().st_size} bytes that are not "
              "JSON. NOT treating that as 'start from zero'. Pass --offset N "
              "(the log's last percentage x file size, rounded DOWN — re-sending "
              "is free, skipping is not), or --restart to mean it.")
        raise SystemExit(2)


def count_rows(url, key):
    """Exact row count, or None. NEVER RAISES.

    ⚠ THIS EXACT DEFECT WAS FOUND AND FIXED IN push_maps_tail.py EARLIER THE
    SAME DAY, AND I DID NOT CARRY IT BACK HERE. The cost: at ~14M rows the
    startup count began timing out —
        HTTP 500 {"code":"57014","message":"canceling statement due to
                  statement timeout"}
    — the exception escaped `main()` before a single row was pushed, the
    wrapper restarted the process, and it crashed in the same place again.
    **Five restarts, zero progress, offset frozen at 84.0%.** The retry loop
    that was supposed to make the job unkillable instead made it loop forever
    on a fatal startup check.

    A COUNT IS A DIAGNOSTIC. It must never be able to stop the work it is
    describing, and it gets slower precisely as the table it counts gets
    bigger — so this is a defect that arrives late, when the run is nearly
    done and the loss is largest.

    (The project's own rule, written after 2026-08-05: when a new trap is
    found, re-run it over every earlier entry. I wrote the note and skipped
    the sweep.)
    """
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{TABLE}?select=document_id&limit=1",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Prefer": "count=exact", "Range": "0-0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return int(r.headers.get("Content-Range", "0/0").split("/")[-1])
    except Exception as e:
        print(f"  ⚠ row count unavailable ({type(e).__name__}) — reported as "
              "UNKNOWN, not as zero, and NOT allowed to stop the push")
        return None


def send(url, key, rows, attempts=0):
    """Upsert one chunk. WAITS OUT A DEAD LINK; never gives up on one.

    ⚠ THE OLD POLICY WAS 5 TRIES OVER 31 SECONDS AND THEN DIE. Login works on a
    laptop that loses its connection — closing the lid, changing networks, a
    router blip — and a 31-second patience budget turns any of those into a
    dead 3-hour job. The write is an IDEMPOTENT upsert and the byte offset is
    checkpointed, so there is never a reason to abandon a chunk: the correct
    behaviour under a lost connection is to WAIT, say so, and carry on when the
    link returns.

    `attempts=0` means unbounded. Backoff climbs to a 60-second poll and stays
    there, so an overnight outage costs one line of log per minute and nothing
    else. Pass a number for a bounded measurement run.

    ⚠ A 4xx STILL STOPS IMMEDIATELY. That is a schema or data problem, it will
    fail identically forever, and retrying it is how you turn a bug into a
    silent infinite loop. Only 5xx and transport errors are treated as "the
    network, not us".
    """
    body = json.dumps(rows).encode()
    i = 0
    while True:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/rest/v1/{TABLE}?on_conflict=document_id",
            data=body, method="POST",
            headers={"apikey": key, "Authorization": "Bearer " + key,
                     "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates,return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                if i:
                    print(f"    ...link back, chunk accepted after {i} retries",
                          flush=True)
                return len(rows), r.status
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", "replace")
            # ⚠ ONE 4xx IS TRANSIENT, AND IT IS A 401.
            #     HTTP 401 {"code":"PGRST303","message":"JWT issued at future"}
            # Hit 2026-08-13 at 84% of the push. It is CLOCK SKEW between
            # Supabase's own services — the local clock was checked against a
            # third party at the time and was 1.3 s out, so it is not ours and
            # not something a retry can make worse. It clears by itself.
            # The blanket "4xx is our bug, fail forever" rule was right about
            # every other 4xx and wrong about this one, and being wrong cost a
            # process death and an in-flight wave each time it fired.
            # ⚠ DO NOT WIDEN THIS TO ALL 401s. A revoked or malformed key also
            # returns 401 — with PGRST301 / "Invalid API key" — and retrying
            # THAT forever is exactly the silent infinite loop the rule exists
            # to prevent. Match the transient code, not the status.
            transient_401 = ("PGRST303" in detail
                             or "issued at future" in detail
                             or "JWT expired" in detail)
            if 400 <= e.code < 500 and not transient_401:
                raise RuntimeError(f"HTTP {e.code}: {detail}")
            why = f"HTTP {e.code}: {detail[:120]}"
            if "57014" in detail or "statement timeout" in detail:
                GATE.too_heavy()
        except Exception as e:
            why = f"{type(e).__name__}: {e}"
        i += 1
        if attempts and i >= attempts:
            raise RuntimeError(f"{why}  (after {attempts} attempts)")
        wait = min(2 ** min(i, 6), 60)
        if i == 1 or i % 5 == 0:
            print(f"    PAUSED — {why}; retry {i} in {wait}s "
                  f"(offset is checkpointed; nothing is lost)", flush=True)
        time.sleep(wait)


def flush_wave(url, key, wave, conc):
    """Send a wave of chunks concurrently and return rows accepted.

    Every chunk in the wave must confirm before the caller checkpoints, so a
    kill mid-wave resumes at the START of the wave rather than past it.
    """
    import concurrent.futures as cf
    if len(wave) == 1:
        n, _ = send(url, key, wave[0])
        wave.clear()
        return n
    with cf.ThreadPoolExecutor(min(conc, len(wave))) as ex:
        futs = [ex.submit(send, url, key, c) for c in wave]
        total = sum(f.result()[0] for f in futs)   # raises if any chunk 4xx'd
    wave.clear()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N rows (measurement run)")
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--conc", type=int, default=CONC,
                    help="concurrent upserts per wave")
    ap.add_argument("--restart", action="store_true", help="ignore saved offset")
    ap.add_argument("--offset", type=int, default=0,
                    help="resume from this byte offset (recovery when the "
                         "checkpoint is lost; re-sending rows is idempotent)")
    ap.add_argument("--verify", action="store_true", help="count only")
    a = ap.parse_args()

    GATE.batch, GATE.conc = a.batch, a.conc
    url, key = S._env()
    if not SRC.exists():
        print(f"  MISSING {SRC}"); return
    before = count_rows(url, key)
    gb = SRC.stat().st_size / 1e9
    print(f"  source  {SRC.name}  {gb:.2f} GB")
    print(f"  target  {TABLE}  holds "
          f"{f'{before:,}' if before is not None else 'UNKNOWN'} rows before this run")
    if a.verify:
        return

    st = {} if a.restart else load_state()
    off = a.offset if a.offset else st.get("offset", 0)
    if off:
        print(f"  resuming at byte {off:,} ({off/SRC.stat().st_size*100:.1f}%)")

    # ⚠ DEDUPE WITHIN THE BATCH OR POSTGRES REFUSES THE WHOLE COMMAND.
    # Measured: HTTP 500, code 21000, "ON CONFLICT DO UPDATE command cannot
    # affect row a second time". The mapper APPENDS - re-runs and delta runs
    # write the same doc_id again - so a 1000-line window can hold the same
    # document twice. Upsert handles duplicates ACROSS commands; it cannot
    # handle two rows with one key INSIDE one command. Last occurrence wins,
    # which is the newest mapping of that document.
    sent = read = bad = dup_in_batch = 0
    reached_eof = False
    buf, wave, t0 = {}, [], time.time()
    with open(SRC, "r", encoding="utf-8", errors="replace") as f:
        f.seek(off)
        while True:
            line = f.readline()
            if not line:
                reached_eof = True
                break
            read += 1
            try:
                r = row(json.loads(line))
                if r["document_id"] in buf:
                    dup_in_batch += 1
                buf[r["document_id"]] = r
            except Exception:
                # ⚠ COUNTED, NOT SWALLOWED. A malformed line is a finding about
                # the mapper; silently skipping it makes the totals disagree
                # with no explanation.
                bad += 1
            if len(buf) >= GATE.batch:
                wave.append(list(buf.values()))
                buf = {}
                if len(wave) >= GATE.conc:
                    sent += flush_wave(url, key, wave, GATE.conc)
                    GATE.ok()
                    # ⚠ CHECKPOINT ONLY AFTER THE WHOLE WAVE CONFIRMS.
                    # With N writes in flight they finish out of order, so
                    # f.tell() is ahead of the earliest UNconfirmed chunk. A
                    # crash mid-wave would then resume PAST rows that never
                    # landed — the one way a resumable job can silently lose
                    # data. Waiting for the wave makes the offset a true
                    # low-water mark; re-doing a wave costs nothing because
                    # every write is an idempotent upsert.
                    save_state(f.tell(), sent)
                    el = time.time() - t0
                    # ⚠ THE OFFSET GOES IN THE LOG TOO. When the state file was
                    # lost, the log's rounded "50.0%" was the only surviving
                    # clue and it is worth ~1.9 MB of ambiguity. A number
                    # printed twice in two places costs nothing.
                    print(f"    {sent:>10,} sent  {sent/max(el,1):>6.0f} rows/s  "
                          f"{f.tell()/SRC.stat().st_size*100:5.1f}%  "
                          f"{el/60:.1f} min  @{f.tell()}", flush=True)
            if a.limit and read >= a.limit:
                break            # a sample, NOT the end of the file
        if buf:
            wave.append(list(buf.values()))
        if wave:
            sent += flush_wave(url, key, wave, GATE.conc)
            save_state(f.tell(), sent)
        off_final = f.tell()

    # ⚠ POSITIVE COMPLETION MARKER. The wrapper used to decide "done" from
    # `if errorlevel 1`, and a Ctrl+C kill exits with 0xC000013A — which cmd
    # compares as a NEGATIVE number, so `errorlevel 1` was FALSE and a KILLED
    # process was reported as **"[wrapper] push completed cleanly"** while the
    # offset sat at 84.2%. Exactly this project's oldest failure shape: success
    # inferred from the absence of a known negative.
    # Reaching here means the read loop ran to EOF. That is the only thing that
    # may ever be called completion, and the wrapper now tests for THIS FILE.
    # ⚠ AND ONLY ON A REAL EOF. `--limit` is a measurement sample that also
    # falls out of the loop; writing the marker there would tell the wrapper a
    # 5,000-row probe had finished a 17M-row push.
    DONE = HERE / "_push_selection_DONE"
    if reached_eof and not a.limit:
        DONE.write_text(json.dumps({"offset": off_final, "sent": sent,
                                    "src_bytes": SRC.stat().st_size}),
                        encoding="utf-8")
        print(f"  COMPLETION MARKER written: read to EOF at byte {off_final:,}")
    else:
        print("  no completion marker — the file was NOT read to the end "
              f"({'--limit sample' if a.limit else 'stopped early'})")
    el = time.time() - t0
    after = count_rows(url, key)
    print(f"\n  lines read      {read:,}")
    print(f"  malformed       {bad:,}")
    print(f"  dup within batch{dup_in_batch:,}   (collapsed before sending)")
    print(f"  rows sent       {sent:,}")
    print(f"  table before    {before if before is None else f'{before:,}'}")
    print(f"  table after     {after if after is None else f'{after:,}'}"
          + (f"   (+{after-before:,})" if None not in (before, after) else
             "   (delta UNKNOWN — a count did not evaluate)"))
    print(f"  elapsed         {el/60:.1f} min   {sent/max(el,1):.0f} rows/s")
    print(f"  statement timeouts {GATE.timeouts:,}   final batch {GATE.batch} "
          f"x {GATE.conc}   (a gate that never moved means the ceiling was "
          f"never reached, not that there isn't one)")
    # ⚠ THE RECONCILIATION IS THE POINT. after-before < sent means duplicate
    # doc_ids in the source, which is EXPECTED (the mapper appends on re-runs)
    # and is the number that tells you how many.
    dup = sent - (after - before) if None not in (before, after) else None
    if dup is None:
        print("  reconciliation NOT EVALUATED — a row count did not return. "
              "Re-run --verify when the table is quiet; do not read this as "
              "'reconciled'.")
    elif dup > 0:
        print(f"  {dup:,} sent rows merged onto existing document_ids "
              f"(duplicates in source - expected, upsert converged)")
    if a.limit:
        # ⚠ bytes CONSUMED, not the whole file. Dividing total size by lines
        # read reported "770,658 bytes/line" and "0.0 hours" for a 3.85 GB push
        # - a projection that says the job is free.
        consumed = st.get("offset", 0)
        consumed = (json.loads(STATE.read_text())["offset"] - off) if STATE.exists() else 0
        per = consumed / max(read, 1)
        total = SRC.stat().st_size / max(per, 1)
        rate = sent / max(el, 1)
        print(f"\n  PROJECTION for the full file:")
        print(f"    {per:.0f} bytes/line -> ~{total:,.0f} lines total")
        print(f"    ~{total/max(rate,1)/3600:.1f} hours at {rate:.0f} rows/s")


if __name__ == "__main__":
    main()
