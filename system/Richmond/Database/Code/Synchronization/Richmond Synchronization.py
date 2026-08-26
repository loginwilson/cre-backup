"""RICHMOND SYNCHRONIZATION — the only thing that writes to Richmond Database.

    import importlib.util as _u                       # the filename has spaces
    SYNC = _u.module_from_spec(_u.spec_from_file_location("sync", <path>))

    SYNC.fresh(ids)     -> the subset we do NOT already hold
    SYNC.land(ids)      -> write them; returns how many were new
    SYNC.newest()       -> highest id held, as a number
    SYNC.total()        -> rows

    python "Richmond Synchronization.py"                    report only
    python "Richmond Synchronization.py" --file ids.txt --apply
    cat ids.txt | python "Richmond Synchronization.py" --stdin --apply

ONE WRITER, TWO CALLERS. Enumeration (all history, occasional) and
Monitorization (the trailing window, every 60 s) both DISCOVER ids and hand
them here. Neither writes. That is the entire point: the NULL rule, the
INSERT OR IGNORE and the Source constant live in exactly one file, so they
cannot drift apart. Two writers is how `rd_walk` and `rc_source` ended up
disagreeing about whether an image existed, one restart away from marking
scanned documents unscanned forever.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE = "richmond"
CHUNK = 500                # ids per IN (...) — well under any variable cap


def _find_db(name="Richmond Database.db"):
    """Walk UP from this file until the database turns up.

    ⚠ NOT A FIXED NUMBER OF LEVELS. A hardcoded depth broke the moment this
    tree was restructured. ⚠ Each level is checked bare AND under a
    `Database/` subfolder, because the db is a SIBLING of this folder
    (Code/Synchronization -> ../../Database/) — walking up alone sails past
    it. ⚠ A miss is FATAL, never silent: sqlite3.connect() on a wrong path
    CREATES an empty file, and every id then lands somewhere nobody reads
    while the log says LANDED and looks perfectly healthy."""
    for d in [HERE] + list(HERE.parents):
        for c in (d / name, d / "Database" / name, d / "database" / name):
            if c.exists():
                return c
    raise SystemExit("cannot find %s above %s" % (name, HERE))


DB = _find_db()


def _con(write=False):
    c = sqlite3.connect(DB, timeout=600) if write else \
        sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=600)
    c.execute("PRAGMA busy_timeout=300000")
    return c


# ── reads ────────────────────────────────────────────────────────────────
def total():
    c = _con()
    n, = c.execute("SELECT COUNT(*) FROM synchronization").fetchone()
    c.close()
    return n


def newest():
    """Highest id held, AS A NUMBER.

    ⚠⚠ THE CAST IS NOT OPTIONAL AND ITS ABSENCE IS INVISIBLE. `ID` is TEXT,
    so SQLite sorts it lexically and MAX(ID) returns a real id that is simply
    the wrong one. MEASURED on this table 2026-08-25:

        MAX(ID)                   ->     999999
        MAX(CAST(ID AS INTEGER))  ->  2,826,705

    Both are ids that exist, so nothing looks broken — you just get an answer
    off by a factor of three. Anything asking "where did we get to" must
    cast."""
    c = _con()
    n, = c.execute("SELECT MAX(CAST(ID AS INTEGER))"
                   " FROM synchronization").fetchone()
    c.close()
    return n or 0


def fresh(ids):
    """The subset of `ids` this database does not already hold, order kept."""
    want = [str(i).strip() for i in ids if str(i).strip()]
    if not want:
        return []
    have, c = set(), _con()
    for i in range(0, len(want), CHUNK):
        part = want[i:i + CHUNK]
        have.update(r[0] for r in c.execute(
            "SELECT ID FROM synchronization WHERE ID IN (%s)"
            % ",".join("?" * len(part)), part))
    c.close()
    seen = set()
    return [i for i in want
            if i not in have and not (i in seen or seen.add(i))]


# ── the one write ────────────────────────────────────────────────────────
def land(ids):
    """Record SOURCE and ID. Returns how many rows were actually new.

    ⚠ THIS WRITES THE ID AND NOTHING ELSE — not the urls, even though both
    are a pure function of the id (login 2026-08-25: "your code autofilled
    the urls. that was not asked of you"). Minting belongs to whatever fills
    those columns, not to the step that notices a document exists.

    ⚠⚠ EVERY UNFILLED COLUMN IS LEFT NULL, NEVER ''. They are not the same
    value and do not answer the same query: `= ''` never matches NULL, and
    neither does `!= ''`. MEASURED on this table while it held both — a lane
    asking `WHERE "Document" = ''` found FOURTEEN rows and reported itself
    finished while 2,501,709 documents sat invisible to it. NULL is also the
    honest state: "not yet acquired" is unknown, not known-to-be-empty.
    Readers ask `IS NULL`.

    ⚠ The PRIMARY KEY is `ID` ALONE, not (Source, ID). Correct while this
    file holds one source — but if these tables are ever merged, a colliding
    id from another source is DISCARDED SILENTLY by the OR IGNORE. Change the
    key before merging, not after."""
    rows = [(SOURCE, str(i).strip()) for i in ids if str(i).strip()]
    if not rows:
        return 0
    con = _con(write=True)
    before = con.total_changes
    for _try in range(120):                 # the monitor may hold the lock
        try:
            con.executemany(
                'INSERT OR IGNORE INTO synchronization ("Source","ID")'
                " VALUES (?,?)", rows)
            con.commit()
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    else:
        con.close()
        raise RuntimeError("could not acquire the write lock in 10 minutes")
    n = con.total_changes - before
    con.close()
    return n


# ── cli ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="a file of ids, one per line")
    ap.add_argument("--stdin", action="store_true", help="read ids from stdin")
    ap.add_argument("--apply", action="store_true",
                    help="write; without it nothing is written")
    a = ap.parse_args()

    print("db      %s" % DB)
    print("rows    {:,}".format(total()))
    print("newest  {:,}".format(newest()))

    src = []
    if a.file:
        src = pathlib.Path(a.file).read_text(encoding="utf-8").split()
    elif a.stdin:
        src = sys.stdin.read().split()
    if not src:
        raise SystemExit(0)

    new = fresh(src)
    print()
    print("offered {:,}   already held {:,}   NEW {:,}"
          .format(len(src), len(src) - len(new), len(new)))
    if not a.apply:
        print(">> report only, nothing written (pass --apply to land them)")
        raise SystemExit(0)
    n = land(new)
    print("landed  {:,}".format(n))
    print("rows    {:,}".format(total()))
    # ⚠ A COUNTER SITTING AT ZERO IS A CLAIM, NOT A RESULT.
    if n != len(new):
        print(">> %d of %d did not land — investigate, do not re-run blindly"
              % (len(new) - n, len(new)))
