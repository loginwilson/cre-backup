"""ACRIS LIVE — one request per document: detect, mint, AND land the rd.

    python acris_live.py                    # report only, writes nothing
    python acris_live.py --apply            # the real thing
    python acris_live.py --apply --every 10

Login 2026-08-23: *"highest crfn you run 1 request every 10 seconds of our
highest crfn + 1. if it hits, you fill in the doc id, mint the rd and pdf url,
then since you are already on rd you can pull all in one and then acris pdf can
follow. its kind of like the synchronization automates navigation and the rd
pull all in one."*

That is exactly what this does, and the saving is real. The four phases used to
be four fetches of the SAME PAGE:

    monitor    GET DocumentDetail -> "something is there", discards 131 KB
    sync       GET it again       -> takes the doc id
    navigation                    -> mints two urls (pure string work, free)
    rd_walk    GET it again       -> parses recorded_details

Now: ONE GET lands a row that is already id + rd_url + pdf_url + recorded_details.
Only the pdf is left, and the pdf lane picks it up with no restart because the
row lands with pdf=''.

⚠ WHY CRFN AND NOT THE DOC ID. Measured 2026-08-23, and the doc id LOOKS like a
counter (YYYYMMDD+NNNNN+SSS) which is exactly the trap:

    20260821 seq 00876..00885 x suffix 001..006  ->  ONLY 00880/001 exists
    20260822 and 20260823 at seq 1,2,5,50,200    ->  nothing at any suffix

The doc id is stamped at SUBMISSION and is sparse - 4 of 5 probed sequences do
not exist at all, across every suffix. CRFN is issued at RECORDING, densely and
in order (11 holes in all of July, all verified unissued). So edge+1 is a true
frontier on CRFN and is not one on the doc id.

⚠ THE CRFN IS NEVER STORED. It is the odometer, not the data - it lives in
_crfn_edge.json and never enters the table. What the row needs is the doc id,
because both urls are pure functions of it.

⚠ CONTROL, BUT NOT EVERY TICK. A blank is ambiguous (absent crfn / malformed
request / changed route / 503 all look alike) so it must be proven. But at a
10-second cadence, controlling every blank doubles the request count forever to
re-answer a question that cannot change in 10 seconds. So the control runs at
most once per --control-every seconds, and a blank is only believed if a
control has passed inside that window. A LIVE answer is its own control and
needs none.

⚠ AN ERROR IS NOT AN ABSENCE and a refusal is never retried. 401/403/429 raise
immediately (acris_edge); 5xx backs off. On any failure this writes nothing and
does NOT advance the edge, so the next tick re-asks.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import acris_edge as AE                                        # noqa: E402
import corpus_paths as CP                                      # noqa: E402
import rd_parse as RD                                          # noqa: E402

EDGE_STATE = HERE / "_crfn_edge.json"
LOG = HERE / "acris_live.log"
ACRIS_URL = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
CONFIRM_BLANKS = 8

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="write; default reports")
ap.add_argument("--every", type=int, default=10,
                help="seconds between ticks when the edge did not move")
ap.add_argument("--control-every", type=int, default=60,
                help="seconds between control requests (a live hit is its own)")
ap.add_argument("--deep-every", type=int, default=300,
                help="seconds between DEEP walks. A shallow tick stops at the "
                     "first blank (1 request); only a deep walk can step over "
                     "a permanently unissued crfn, so this bounds how long a "
                     "hole can stall the edge.")
ap.add_argument("--max", type=int, default=500,
                help="walk bound per tick; past this, escalate to the routine")
ap.add_argument("--pdf", action="store_true",
                help="also pull the pdf for landed rows, ONE per idle cycle "
                     "(sync always goes first)")
ap.add_argument("--pdf-lo", default="20260815",
                help="only pull pdfs for ids above this - the LIVE frontier. "
                     "The 20.3M-row history is the backfill fleet's job and a "
                     "sequential lane would need 6.4 years for it.")
ap.add_argument("--once", action="store_true")
a = ap.parse_args()


def say(m):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def urls(did):
    """Pure function of the id — the SAME mint as routine_navigation.urls.
    (nav_append is a SCRIPT: importing it would run it.)"""
    return (ACRIS_URL + "DocumentDetail?doc_id=" + did,
            ACRIS_URL + "DocumentImageView?doc_id=" + did)


def read_edge():
    return int(json.loads(EDGE_STATE.read_text(encoding="utf-8"))["edge"])


def write_edge(n):
    """⚠ AFTER THE COMMIT, NEVER ON A LOOK. index_daily.py: "state saved before
    the work meant a report-only run moved the cutoff and the next real run
    found nothing, with 28,196 documents permanently behind it while it printed
    success.\""""
    st = json.loads(EDGE_STATE.read_text(encoding="utf-8"))
    st["edge"] = n
    st["watermark"] = n
    EDGE_STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def land(rows):
    """One transaction. THE WRITER-SEAT LAW: batch the WRITES, never the work.

    ⚠ EVERY WORK COLUMN IS '' AND NEVER NULL. nav_append.py:216 states the
    invariant: rd_walk sees recorded_details='', image_walk sees pdf='',
    nav_key sees keyed_by=''. Those lanes select on `= ''` and NULL is not '',
    so a NULL row is invisible to every lane forever while looking healthy.
    Here recorded_details lands FILLED, which is what makes rd_walk skip it -
    that is the point, not an omission."""
    con = sqlite3.connect(CP.NAV_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    # ⚠ INSERT EMPTY, THEN UPDATE THE RD — IN THAT ORDER, IN ONE TRANSACTION.
    #
    # This looks like a pointless extra statement and is not. `key_on_rd` is
    # `AFTER UPDATE OF recorded_details`, so a row that ARRIVES with the rd
    # already filled never triggers it. Measured 2026-08-23 against a scratch
    # copy of the real schema:
    #
    #     INSERT empty, then UPDATE rd   -> key_on_rd fires, bbl keyed
    #     INSERT with rd already filled  -> keyed_by stays '' , NO key
    #
    # The first version of this file did the second, so every document it
    # landed would have been UNKEYED - and invisible, because the row is
    # complete in every other column and no lane selects for "rd but no key"
    # except the backfill keyer, which is deliberately held until acris rd
    # reaches 99.95% (org_backfill_arm.py). New documents would have sat
    # unkeyed for days while every board read 100%.
    #
    # mint_urls is `AFTER INSERT` and fires either way, so the urls below are
    # belt-and-braces: the db mints the same two strings from the id itself.
    ins = [(did, "", urls(did)[0], "", urls(did)[1], "", "")
           for _crfn, did, _rd in rows]
    upd = [(rd, did) for _crfn, did, rd in rows if rd]
    for _try in range(120):              # never die on a lock
        try:
            con.executemany(
                "INSERT OR IGNORE INTO navigation"
                " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by, key)"
                " VALUES (?,?,?,?,?,?,?)", ins)
            con.executemany(
                "UPDATE navigation SET recorded_details=?"
                " WHERE id=? AND recorded_details=''", upd)
            con.commit()
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    else:
        con.close()
        raise RuntimeError("could not acquire the write lock in 10 minutes")
    n = con.total_changes
    con.close()
    return n


_last_control = [0.0]


def control_ok(edge):
    """True if the probe is proven. A live hit proves itself; this is only for
    believing a BLANK. Rate-limited: re-proving every 10s is pure cost."""
    if time.time() - _last_control[0] < a.control_every:
        return True                      # proven recently enough
    state, did = AE.quick_crfn(edge)
    if state == "live":
        _last_control[0] = time.time()
        return True
    return False


_last_deep = [0.0]


def tick():
    """Returns (ok, landed). ok=False means WE LEARNED NOTHING - not level.

    ⚠ A QUIET TICK COSTS 1 REQUEST, NOT 9. The first version walked the full
    CONFIRM_BLANKS(8) every tick, so a quiet tick was 9 requests - at a
    10-second cadence, 54 requests a minute to re-learn a number that had not
    moved. Login asked for *"1 request every 10 seconds"* and meant it.

    ⚠ BUT THE 8-BLANK WALK CANNOT SIMPLY BE DROPPED. The counter has genuine
    unissued holes. If one sits at edge+1, a probe that stops at the first blank
    NEVER ADVANCES - it re-asks the same dead number every 10 seconds forever
    while documents pile up above it. That is a silent permanent stall, the
    worst failure shape this system has.

    So: shallow every tick, DEEP periodically.

        shallow   probe edge+1 only                    1 request
        deep      walk until 8 consecutive blanks      up to 9, every
                  - the only thing that can step        --deep-every seconds
                    over a permanent hole

    A hole therefore costs at most --deep-every of delay, not forever, and the
    steady-state cost is ~6 requests/min at a 10s tick plus one deep walk."""
    edge = read_edge()
    deep = (time.time() - _last_deep[0]) >= a.deep_every
    limit = CONFIRM_BLANKS if deep else 1
    if deep:
        _last_deep[0] = time.time()
    found, blanks, n = [], 0, edge
    try:
        while blanks < limit and (n - edge) < a.max:
            n += 1
            state, did, html = AE.fetch(n)
            if state != "live":
                blanks += 1
                continue
            blanks = 0
            # ⚠ PARSE FROM THE BODY WE ALREADY HAVE. Refetching here would
            # rebuild the exact duplication this file exists to remove.
            try:
                rec = json.dumps(RD.parse_acris(html), separators=(",", ":"))
            except Exception as e:
                # ⚠ A PARSE FAILURE IS NOT A REASON TO DROP THE DOCUMENT. Land
                # it with recorded_details='' so rd_walk retries it properly;
                # never let a parser bug silently lose a doc id.
                say("  ⚠ rd parse failed for %s (%s) - landing with rd='' so "
                    "rd_walk retries it" % (did, type(e).__name__))
                rec = ""
            found.append((n, did, rec))
    except Exception as e:
        code = getattr(e, "code", None)
        say("  PROBE UNPROVEN (%s%s: %.90s) - nothing written, edge NOT "
            "advanced" % (type(e).__name__, " %d" % code if code else "", e))
        return False, 0

    if (n - edge) >= a.max:
        say("  ⚠ walked %d without %d consecutive blanks - delta too big for a "
            "linear walk. Run routine_synchronization.py (gallop+bisect). "
            "Nothing written." % (a.max, CONFIRM_BLANKS))
        return False, 0

    if not found:
        # ⚠ PROVE THE BLANK BEFORE BELIEVING IT.
        try:
            if not control_ok(edge):
                say("  CONTROL %d did not resolve - probe unproven, reporting "
                    "NOTHING (not 'level')" % edge)
                return False, 0
        except Exception as e:
            say("  CONTROL errored (%s) - reporting NOTHING" % type(e).__name__)
            return False, 0
        # ⚠ SAY IT. A quiet tick used to return here in silence, which is the
        # one thing this system keeps re-learning not to do: a lane that goes
        # quiet reads exactly like a lane that died. "Nothing new" is a RESULT
        # and the most common one.
        say("  level at crfn %d · %s walk, %d blank(s), control ok · %d req"
            % (edge, "DEEP" if deep else "shallow", blanks, n - edge))
        return True, 0

    if not a.apply:
        for crfn, did, rec in found[:5]:
            say("  would land crfn %d -> %s  rd %s"
                % (crfn, did, "parsed" if rec else "EMPTY"))
        say("  --apply not given: NOTHING WRITTEN, edge NOT advanced")
        return True, 0

    landed = land(found)
    write_edge(found[-1][0])             # after the commit, never before
    # ⚠ THE LEDGER MOVES THE GOALPOSTS (login 2026-08-24: "if files are
    # coming in the needed would move with the landed"). rc_live has written
    # its landings to the synchronization ledger since day one; acris never
    # did, so the board's `needed` sat at Friday's total while Monday's
    # inflow landed - both needed AND landed lagged by exactly the inflow.
    # Accounted, not measured - previous total + what we landed;
    # routine_synchronization re-anchors it. A ledger failure never stops
    # sync: the rows ARE landed.
    try:
        _lg = sqlite3.connect(r"D:\CRE Decoding System\00 Synchronizations"
                              r"\Legal Instruments Synchronization"
                              r"\Legal Instruments Synchronization.db",
                              timeout=60)
        try:
            _prev = _lg.execute(
                "SELECT system_total FROM synchronization"
                " WHERE source='acris' AND system_total > 0"
                " ORDER BY run_at DESC LIMIT 1").fetchone()
            _sys = (_prev[0] if _prev else 0) + len(found)
            _lg.execute("INSERT OR REPLACE INTO synchronization"
                        " (run_at, source, system_total, source_total,"
                        " delta, doc_ids) VALUES (?,?,?,?,?,?)",
                        (time.strftime("%Y-%m-%d %H:%M"), "acris", _sys,
                         _sys, 0, ";".join(d for _c, d, _r in found)))
            _lg.commit()
        finally:
            _lg.close()
    except Exception as e:
        say("  ⚠ ledger write failed (%s) - rows ARE landed" % type(e).__name__)
    # ⚠ HAND THE NEW IDS TO THE PDF STEP DIRECTLY. This is the only thing that
    # makes a fresh document's pdf arrive in seconds instead of behind the
    # backlog - see the note in pdf_step about the submission-date ordering.
    _pdf_hot.extend(did for _crfn, did, _rd in found)
    withrd = sum(1 for _c, _d, r in found if r)
    say("  landed %d · rd filled on %d/%d in the SAME request · edge %d -> %d"
        % (landed, withrd, len(found), edge, found[-1][0]))
    for crfn, did, rec in found[:5]:
        say("      crfn %d  ->  %s" % (crfn, did))
    return True, landed


_pdf_skip = set()          # ids that came back SHORT - do not loop on them
_pdf_cooldown = [0.0]      # set on a refusal; sync keeps running regardless
_pdf_hot = []              # JUST-LANDED ids, pdf'd before any backlog row


def pdf_step():
    """ONE document's pdf. Returns a short status string, or None if idle.

    ⚠ SYNC IS THE INTERRUPT, PDF IS THE BACKGROUND TASK. This is only ever
    called on a cycle where the edge did NOT move, and it does exactly one
    document before returning so the next edge probe is at most one document
    away. Measured 8.8-23.5s per document, so a cycle is ~10-25s when there is
    pdf work and ~1s when there is not.

    ⚠ A PDF REFUSAL MUST NOT STOP SYNC. image_walk's rule is "refusal anywhere
    stops ALL workers", which is right for a 28-worker image fleet and wrong
    here: rd and pdf are SEPARATE SERVER POOLS (A/B settled 2026-08-21), so an
    image refusal says nothing about the detail route. Losing the freshness
    guarantee over an image problem would be the expensive mistake. So a refusal
    parks the PDF half on a cooldown and leaves sync ticking.

    ⚠ SHORT IS NOT A PDF. acris_pdf raises rather than converting the frames it
    did get - "a 1-of-8 read looks exactly like success". The row stays pdf=''
    so the backfill fleet retries it properly; we just stop re-picking it here,
    or the same document blocks the live lane forever."""
    if time.time() < _pdf_cooldown[0]:
        return None
    try:
        import acris_pdf as AP
    except Exception as e:
        say("  pdf disabled: %s" % e)
        _pdf_cooldown[0] = time.time() + 3600
        return None

    # ⚠ JUST-LANDED ROWS JUMP THE QUEUE, AND THE ORDERING BELOW CANNOT DO IT.
    # `ORDER BY id DESC` sorts by DOC ID, and the doc id carries the SUBMISSION
    # date, not the recording date - measured gaps of 2 to 17 days. So a
    # document recorded 60 seconds ago can have an id from two weeks back and
    # sort BELOW ~2,000 backlog rows. Login 2026-08-23: *"shouldnt it be instant
    # though if a doc is recorded and we have constant monitoring."* It should,
    # and only an explicit hot queue makes it so - the id ordering never will.
    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    row = None
    while _pdf_hot and row is None:
        did = _pdf_hot.pop(0)
        if did in _pdf_skip:
            continue
        r = con.execute("SELECT id, recorded_details FROM navigation"
                        " WHERE id=? AND pdf=''", (did,)).fetchone()
        if r:
            row = r
            say("  pdf  HOT (just landed, jumping %d backlog row(s))"
                % len(_pdf_hot))
    if row is None:
        for did, rd in con.execute(
                "SELECT id, recorded_details FROM navigation"
                " WHERE pdf='' AND recorded_details!='' AND id > ? AND id < '3'"
                " AND id NOT LIKE 'RC!_%' ESCAPE '!' ORDER BY id DESC LIMIT 40",
                (a.pdf_lo,)):
            if did not in _pdf_skip:
                row = (did, rd)
                break
    con.close()
    if not row:
        return None
    did, rd = row
    try:
        rec = json.loads(rd).get("recorded", "") if rd else ""
    except Exception:
        rec = ""

    t = time.time()
    try:
        state, value = AP.fetch_pdf(did, rec)
    except AP.AccessDenied as e:
        # ⚠ DO NOT RETRY, DO NOT ROTATE. Park and keep syncing.
        _pdf_cooldown[0] = time.time() + 900
        say("  ⚠ pdf REFUSED on %s (%.60s) - pdf parked 15 min, SYNC CONTINUES"
            % (did, e))
        return None
    except AP.Short as e:
        _pdf_skip.add(did)
        say("  pdf SHORT on %s (%.70s) - left pdf='' for the backfill, skipping"
            % (did, e))
        return None
    except Exception as e:
        say("  pdf error on %s (%s: %.60s)" % (did, type(e).__name__, e))
        return None

    if not a.apply:
        return "%s would be %s (%.1fs)" % (did, state, time.time() - t)

    w = sqlite3.connect(CP.NAV_DB, timeout=600)
    w.execute("PRAGMA busy_timeout=300000")
    for _try in range(120):
        try:
            w.execute("UPDATE navigation SET pdf=? WHERE id=? AND pdf=''",
                      (value, did))
            w.commit()
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    w.close()
    return "%s -> %s (%.1fs)" % (did, state, time.time() - t)


def main():
    say("acris_live up · tick %ds · control every %ds · pdf=%s · apply=%s"
        % (a.every, a.control_every, a.pdf, a.apply))
    if not a.apply:
        say("  ⚠ --apply NOT given: reporting only, nothing will be written")
    fails = 0
    while True:
        ok, landed = tick()
        if not ok:
            fails += 1
            wait = min(a.every * (2 ** fails), 900)
            say("  held after %d failure(s) - next attempt in %ds "
                "(unreachable is NOT 'level')" % (fails, wait))
        elif landed:
            # ⚠ SYNC FIRST, ALWAYS. New documents exist, so chase them and do
            # NO pdf work this cycle - falling behind the edge to fetch an
            # image would trade the one guarantee this lane exists to make.
            fails, wait = 0, 0
        else:
            fails, wait = 0, a.every
            if a.pdf:
                # the edge did not move, so spend the idle time on one pdf
                r = pdf_step()
                if r:
                    say("  pdf  %s" % r)
                    wait = 0             # more pdf work waiting; keep going
        if a.once:
            return 0 if ok else 1
        if wait:
            time.sleep(wait)


if __name__ == "__main__":
    sys.exit(main() or 0)
