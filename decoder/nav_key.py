"""THE KEYING PASS - the follower process (login runtime design,
2026-08-20 evening: "two processes simultaneously... the keying will follow
up the doc id row after the land to determine its key type and key. if it
cant be keyed it is saved for second pass with pdf url").

Sweeps the one table for rows with recorded_details but no key and writes
the conclusion per the evidence ladder:

  parcel     details.parcels carry BBL(s)      key = all of them (";"-joined;
             multi-parcel = the involved lots, login)
  reference  the doc's evidence is a REFERENCE to another document. The key
             is filled when that target already resolves (via this table's
             own keyed rows or the spec's parcel_document - one hop, v1);
             it is left EMPTY when the target has not been pulled yet, and
             an empty key IS the pass-2 worklist. ⚠ Same type either way -
             the TYPE is the evidence class, the KEY is the answer.
  pdf-pass   neither parcels nor references - the pdf url keys it (document
             rung / federal-lien residence / terminal party). This is the
             PASS 3 worklist. ⚠ Stored as "pdf-pass" for continuity with
             rows already written; it IS login's "pdf" type.

⚠ THE THREE PASSES READ THESE STATES (login 2026-08-24):
    pass 1  keyed_by='parcel'                     -> BBL straight from the rd
    pass 2  keyed_by='reference' AND key=''       -> cross the crfn/doc id
            once the pull is complete and every target exists
    pass 3  keyed_by='pdf-pass'                   -> the pdf is all that is left
⚠ Pass 2 must select on THAT predicate, not on the unkeyed one
(`keyed_by IS NULL OR keyed_by=''`) - a marked row will never match it.

--loop makes it a daemon that trails the walker; one sweep otherwise.
Keys are written ONLY from custodian-asserted evidence - same bulletproof
stack as the walker (the details landed id-echoed; references are the
register's own edges).
"""
import argparse
import json
import pathlib
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

ap = argparse.ArgumentParser()
ap.add_argument("--loop", action="store_true",
                help="run as the follower daemon (sweep, sleep 30s, repeat)")
ap.add_argument("--limit", type=int, default=0,
                help="key at most N rows this run (the login's graduated"
                     " approval: 1 -> 10 -> 50 -> 100 -> free rein)")
ap.add_argument("--show", action="store_true",
                help="print each decision with its evidence")
ap.add_argument("--rescan", action="store_true",
                help="restart the cursor at the top to collect rows skipped"
                     " as ref-pending - the deliberate end-of-pull pass, NOT"
                     " something to run in a 30s loop (it walks all 24M rows)")
ap.add_argument("--sleep", type=int, default=30,
                help="seconds between sweeps when looping")
ap.add_argument("--lo", default="", help="key ids > this")
ap.add_argument("--hi", default="￿", help="key ids < this")
ap.add_argument("--src", choices=["acris", "rc", "all"], default="all",
                help="follow one source's completions (login 2026-08-20:"
                     " one keyer behind acris, one behind rc)")
a = ap.parse_args()
SRC_FILTER = {"acris": " AND id NOT LIKE 'RC_%'",
              "rc": " AND id LIKE 'RC_%'",
              "all": ""}[a.src]

con = sqlite3.connect(f"file:{CP.NAV_DB}", uri=True, timeout=600)
# 5 min: a store migration's single commit measured LONGER than 60s and
# killed the rc keyer mid-sweep (2026-08-20) - the follower must outwait
# any one writer's transaction, never die to it
con.execute("PRAGMA busy_timeout=300000")

# ⚠ BATCH SIZE IS A LANE-IMPACT DIAL, MEASURED 2026-08-23. The sweep's SELECT
# size is also the executemany size, so it decides how long the write lock is
# held per acquisition. At 5,000 the keyer ran happily (~105 rows/s) but rd
# acris slid 69 -> 41 -> 35/s while it worked. rc_pdf_pull measured its own
# sweet spot at 250 for the same reason. Smaller = more seat acquisitions but
# each one brief; larger = fewer but longer, and the walkers wait behind each.
# Raise it only while watching `acquisition rd` on the board.
BATCH = 500
# second connection, read-only - the proven pattern every script here uses
# (ATTACH chokes on this path's spaces/colon across encodings; two
# connections do the same job with zero URI ceremony)
spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True, timeout=120)


def ref_bbls(ref):
    """one hop: the referenced doc's parcels, from our own table first,
    then the spec's register capture"""
    row = con.execute("SELECT keyed_by, key FROM navigation WHERE id=?",
                      (ref,)).fetchone()
    if row and row[0] == "parcel" and row[1]:
        return row[1].split(";")
    rows = spec.execute("SELECT DISTINCT bbl FROM parcel_document"
                        " WHERE document_id=? AND TRIM(COALESCE(bbl,''))!=''",
                        (ref,)).fetchall()
    return [r[0] for r in rows]


# ⚠ ONE CURSOR PER ID RANGE, MATCHING THE WALKERS. A single shared cursor
# was WRONG: there are TWO rd lanes (digital from '0', film from 'A'), and
# the one cursor raced to the end of the film range (FT_1000004272600) and
# left every row the DIGITAL lane landed stranded behind it - the keyer
# posted +0 for four straight ticks while rd kept landing rows. A cursor may
# only ride a frontier it is the sole follower of.
CURSOR_F = CP.NAV_WORK / f"nav_key_{a.src}_{a.lo or 'start'}.cursor"


def load_cursor():
    try:
        return CURSOR_F.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def sweep():
    # ⚠ THE CURSOR PERSISTS ACROSS SWEEPS. It used to reset to '' every pass,
    # and because neither recorded_details nor keyed_by is indexed, each pass
    # WALKED ALL 24M ROWS just to prove there was no more work - then slept
    # 30s and did it again. Two keyers doing that pinned the USB drive at
    # 3.3% idle and starved every pull lane (measured 2026-08-21: stopping
    # them took D: to 92.7% idle and rd from 2.6 to 12.9+ docs/s).
    # rd lands top-to-bottom in id order, so the keyer just follows the
    # frontier; new rows always arrive BEYOND the cursor.
    # ⚠ Rows skipped as ref-pending are left behind by this. That is correct
    # for now: an unresolved reference is a CRFN whose document has not been
    # pulled yet, so it cannot resolve until the pull completes anyway
    # (nav_key's own standing note). --rescan restarts from '' to collect
    # them, and that is a deliberate end-of-pull pass, not a 30s loop.
    sweep.cursor = a.lo if a.rescan else (load_cursor() or a.lo)
    n = {"parcel": 0, "reference": 0, "pdf-pass": 0}
    while True:
        room = (a.limit - sum(n.values())) if a.limit else 5000
        if room <= 0:
            break
        # MAX SPEED (login settled 2026-08-20 after weighing the strict
        # rd->pdf->key relay): the bbl evidence is ENTIRELY in the rd, so
        # keys fire on rd completion and never wait out the pdf campaign.
        # The rows that truly need a pdf (no parcels, no refs) wait anyway
        # - the keyer marks them pdf-pass and phase 2 owns them.
        batch = con.execute(
            "SELECT id, recorded_details FROM navigation"
            " WHERE recorded_details != '' AND (keyed_by IS NULL OR keyed_by='')"
            " AND id > ? AND id < ?" + SRC_FILTER + " ORDER BY ID LIMIT ?",
            (sweep.cursor, a.hi, min(room, BATCH))).fetchall()
        if not batch:
            # ⚠ WRAP, DO NOT PARK. Reaching the end means "nothing left ahead
            # of me", NOT "nothing left". There are two rd lanes filling two
            # id ranges (digital from '0', film from 'A'), so a cursor that
            # stops at the far end strands every row the OTHER lane lands
            # behind it - measured 2026-08-21: the keyer parked at
            # FT_1000004272600 and posted +0 for four straight ticks while rd
            # kept landing rows. Wrapping costs one index walk per sweep when
            # caught up, which is why --sleep must stay generous.
            sweep.cursor = a.lo
            break
        sweep.cursor = batch[-1][0]   # advance past skipped (ref-pending) rows
        # ⚠ THE WRITER-SEAT LAW (measured 2026-08-22). This loop used to call
        # con.execute(UPDATE) PER ROW, which opens a write transaction on the
        # FIRST row and holds the exclusive lock until the commit ~5,000 rows
        # later - while every remaining row parses json and runs TWO MORE
        # QUERIES for reference resolution (ref_bbls hits `con` AND `spec`).
        # Thousands of lookups performed while holding the write lock: that is
        # why "a live keyer blocked every walker" and why this phase was
        # parked behind a busy-guard.
        #
        # rc_pdf_land.py had the rule right all along - "converted OUTSIDE the
        # transaction" - and rc_pdf_pull.py measured the payoff: per-row
        # commits gave ~2/s, ONE executemany per 250 rows kept pace with 12.5/s.
        # The work was never the problem; holding the lock during it was.
        #
        # So: COMPUTE EVERY KEY FIRST (reads only, no txn open), then apply
        # once. The lock is held for milliseconds instead of minutes, and the
        # keying logic below is untouched.
        updates, tally = [], {}
        for did, det in batch:
            try:
                d = json.loads(det)
            except ValueError:
                continue
            pcls = d.get("parcels") or []
            bbls = []
            for p in pcls:
                b = p.get("bbl") if isinstance(p, dict) else p
                if b:
                    bbls.append(str(b))
            if bbls:
                kb, key = "parcel", ";".join(dict.fromkeys(bbls))
            else:
                inherited = []
                for ref in (d.get("references") or []):
                    # structured refs (rd_parse: {doc_id/crfn/file_nbr...})
                    # and legacy string refs both resolve on their doc id;
                    # crfn-only refs wait for the map that completes with
                    # the pull (login: "reference converges at the end")
                    target = (ref.get("doc_id") if isinstance(ref, dict)
                              else ref if isinstance(ref, str) else None)
                    if target and (target[:1].isdigit()
                                   or target[:3] in ("FT_", "BK_")):
                        inherited += ref_bbls(target)
                if inherited:
                    kb, key = "reference", ";".join(dict.fromkeys(inherited))
                elif d.get("references"):
                    # refs exist but don't resolve YET (a CRFN whose doc
                    # lands later; the map completes when the pull does -
                    # login 2026-08-20). NEVER a premature pdf-pass verdict.
                    #
                    # ⚠⚠ MARK IT, DON'T SKIP IT (login 2026-08-24: "if its
                    # pass2 shouldnt it be marked pending for that... that
                    # would make pass2 and 3 much easier and shouldnt cost a
                    # ton given that only a small amount are going to be
                    # pass2 and 3"). Leaving the row unkeyed made
                    # PENDING and NEVER-LOOKED-AT the same state, so the only
                    # way to find this population later was --rescan, which
                    # WALKS ALL 24M ROWS. Naming the state turns pass 2 into
                    # a lookup over its own small worklist.
                    #
                    # ⚠ THIS TAKES THE ROW OUT OF THE NORMAL SWEEP - the
                    # sweep selects `keyed_by IS NULL OR keyed_by=''`, so a
                    # marked row is no longer retried automatically. That is
                    # correct and deliberate: an unresolved reference is a
                    # CRFN whose document has not been pulled yet, so it
                    # CANNOT resolve until the pull completes. It is pass-2
                    # work by definition. ⚠ But it does mean pass 2 must
                    # actually run - org_backfill_arm releases it at sync
                    # 99.95%, and pass 2 must select keyed_by='ref-pending'
                    # (NOT the unkeyed predicate, which will never match).
                    #
                    # ⚠ THE TYPE IS THE EVIDENCE CLASS; THE KEY IS THE ANSWER
                    # (login 2026-08-24: "in the type it would be parcel,
                    # reference, pdf. pass 1 can give every bbl. pass 2 once
                    # everything is done can do bbl through the reference
                    # since it can cross crfn or doc id in the rd. Then, pdf
                    # is the final way of keying when its all thats left").
                    #
                    # So there is no separate "pending" TYPE. A doc whose
                    # evidence is a reference is `reference` whether or not it
                    # resolves yet - what differs is the KEY:
                    #     reference + key  -> resolved (its target was already
                    #                         pulled; keyed at pass 1)
                    #     reference + ''   -> PASS 2 WORKLIST
                    # An earlier draft invented a fourth state for this and it
                    # was wrong: it split one population across two names for
                    # a difference that the key column already expresses.
                    #
                    # key stays EMPTY: a pending row has no parcel yet, and
                    # writing anything there would be a fabricated verdict.
                    kb, key = "reference", ""
                else:
                    # NO parcels, NO references - genuinely rd-unkeyable:
                    # saved for the second pass, the pdf url keys it
                    kb, key = "pdf-pass", ""
            # NO WRITE HERE - collect it. The transaction opens once, below.
            updates.append((kb, key, did))
            tally[kb] = tally.get(kb, 0) + 1
            if a.show:
                ev = (f"parcels panel -> {key}" if kb == "parcel" else
                      f"references {d.get('references')} -> {key}"
                      if kb == "reference" else
                      f"no parcels, refs={d.get('references', [])!r},"
                      f" slid={d.get('slid', '-')} -> saved for pdf pass")
                print(f"  {did}  {d.get('type', '?'):<10} {kb:<9} {ev}",
                      flush=True)
        # ⚠ ONE TRANSACTION, ONE SEAT ACQUISITION. All the thinking is done;
        # this is a batch of bare UPDATEs and nothing else. NEVER DIE ON A
        # LOCK (measured twice: an index build and a bulk UPDATE each held an
        # exclusive txn long enough to kill the keyer mid-sweep) - retry, and
        # if it still will not go, write NOTHING and let a later sweep re-find
        # the rows. The table is the work list.
        wrote = False
        for _try in range(120):
            try:
                if updates:
                    con.executemany("UPDATE navigation SET keyed_by=?, key=?"
                                    " WHERE id=?", updates)
                con.commit()
                wrote = True
                break
            except sqlite3.OperationalError:
                time.sleep(5)
        if wrote:
            # ⚠ COUNT ONLY WHAT COMMITTED. Incrementing during the compute
            # loop would report keys that were never written if the batch
            # failed - a count of our own optimism, not of rows.
            for k, v in tally.items():
                n[k] += v
        else:
            print("  ⚠ batch did not commit after 120 tries - 0 keys written,"
                  " rows left for a later sweep", flush=True)
            continue
        # persist AFTER the commit, never before: a cursor ahead of the
        # committed keys would silently skip rows on the next start
        try:
            CURSOR_F.write_text(sweep.cursor, encoding="utf-8")
        except Exception:
            pass
    # persist AFTER the loop as well, so a WRAP is saved. Without this a
    # restart resumes at the old far-end cursor and strands rows again.
    try:
        CURSOR_F.write_text(sweep.cursor, encoding="utf-8")
    except Exception:
        pass
    return n


while True:
    t0 = time.time()
    n = sweep()
    total = sum(n.values())
    if total:
        msg = (f"keyed {total:,} in {time.time()-t0:.1f}s · "
               f"parcel {n['parcel']:,} · reference {n['reference']:,} · "
               f"pdf-pass {n['pdf-pass']:,}")
        print(msg, flush=True)
        # THE BOARD FEED (login 2026-08-22: organization must show live,
        # per source, like every other phase). One log per --src so the
        # board can carry an acris row and a richmond row separately;
        # routine_update glob-sums "keyed N" newer than the baseline.
        with (CP.NAV_WORK / f"nav_key_{a.src}.log").open(
                "a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    if not a.loop:
        break
    time.sleep(a.sleep)
