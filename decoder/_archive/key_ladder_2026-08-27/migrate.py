"""APPLY PASSES 1/2/3 + THE LOT LEDGER TO Legal Instruments.db.

Staged and RESUMABLE: every stage records itself in `migration_state`, so a
kill, a crash or a pulled drive costs one stage, not the run.

⚠ ORDER IS LOAD-BEARING. The go-forward TRIGGERS are created LAST, on purpose.
A trigger that fires per-row is right for a landing lane and catastrophic for a
backfill: `key_on_ref_insert` would fire on each of ~10M ref inserts, resolving
one row at a time. The backfill instead bulk-loads the edges and resolves the
whole population in set operations, then installs the triggers to keep FUTURE
landings keyed. Same end state, orders of magnitude apart.

⚠ key_rules must be replaced BEFORE anything writes keyed_by='party', or the
old rule ABORTs every pass-3 row ("party is DECODING, not a key").

Run:  python migrate.py            (all pending stages)
      python migrate.py --status   (what has run)
      python migrate.py --stage N  (one stage)
"""
import sqlite3, sys, io, time, os

import sys as _s
DB = (_s.argv[_s.argv.index("--db")+1] if "--db" in _s.argv
      else "D:/CRE Decoding System/Legal Instruments.db")
BATCH = 200000


def con():
    c = sqlite3.connect(DB, timeout=600)
    c.execute("PRAGMA recursive_triggers = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = NORMAL")
    c.execute("PRAGMA cache_size = -400000")      # ~400MB, this is a bulk job
    return c


def state_init(db):
    db.execute("CREATE TABLE IF NOT EXISTS migration_state ("
               "stage INTEGER PRIMARY KEY, name TEXT, done_at TEXT, note TEXT)")
    db.commit()


def done(db, n):
    return db.execute("SELECT 1 FROM migration_state WHERE stage=?", (n,)).fetchone()


def mark(db, n, name, note=""):
    db.execute("INSERT OR REPLACE INTO migration_state(stage,name,done_at,note) "
               "VALUES (?,?,datetime('now'),?)", (n, name, note))
    db.commit()


def log(m):
    print("  %s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def id_batches(db):
    """walk the PK in ranges - ids are TEXT and span two namespaces"""
    lo = db.execute("SELECT MIN(id) FROM navigation").fetchone()[0]
    while True:
        hi = db.execute("SELECT id FROM navigation WHERE id > ? "
                        "ORDER BY id LIMIT 1 OFFSET ?", (lo, BATCH)).fetchone()
        if not hi:
            yield lo, None
            return
        yield lo, hi[0]
        lo = hi[0]


# ─────────────────────────────────────────────────────────── stages ──
def split_sql(sql):
    """Split into statements, treating CREATE TRIGGER..END; as ONE unit.

    !! A NAIVE split(';') OR split(';\\n') SILENTLY SHREDS TRIGGERS. A trigger
    body contains its own statement terminators, so a naive split yields the
    CREATE TRIGGER line and then its body lines as SEPARATE fragments. Filtering
    "chunks that start with CREATE TRIGGER" then drops the head and leaves the
    body to execute as free-standing SQL. Found 2026-08-27 on the scratch run -
    it surfaced as "cannot commit - no transaction is active", which points
    nowhere near the actual cause.
    """
    import re as _re
    out, buf, in_trg, depth = [], [], False, 0
    for line in sql.splitlines(True):
        st = line.strip().upper()
        if not in_trg and st.startswith("CREATE TRIGGER"):
            in_trg, depth = True, 0
        buf.append(line)
        if in_trg:
            # !! "ENDS AT THE FIRST END;" IS WRONG. key_rules is a
            # `SELECT CASE ... END;` inside `BEGIN ... END;` - the CASE's END
            # closes the block first and truncates the statement ("incomplete
            # input"). BEGIN and CASE both OPEN a level; END closes one. The
            # trigger ends only when the outermost BEGIN is closed.
            for tok in _re.findall(r"\b(BEGIN|CASE|END)\b",
                                   _re.sub(r"--.*", "", st)):
                depth += 1 if tok in ("BEGIN", "CASE") else -1
            if depth == 0 and st.endswith(";") and "BEGIN" in "".join(buf).upper():
                out.append(("trigger", "".join(buf))); buf = []; in_trg = False
        elif line.rstrip().endswith(";"):
            body = "".join(buf).strip()
            # !! JUDGE THE CODE, NOT THE BUFFER. buf carries every comment line
            # that preceded the statement, so testing body.startswith("--")
            # discards EVERY documented statement - which here is all of them.
            # Found 2026-08-27: it surfaced as "no such table: main.refs",
            # i.e. the index survived and its CREATE TABLE had been dropped.
            code = "\n".join(l for l in body.splitlines()
                             if l.strip() and not l.strip().startswith("--")).strip()
            if code:
                kind = ("drop_trigger" if code.upper().startswith("DROP TRIGGER")
                        else "plain")
                out.append((kind, body))          # comments kept: sqlite is fine with them
            buf = []
    if "".join(buf).strip():
        out.append(("plain", "".join(buf)))
    return out


def stage1_schema(db):
    """tables, indexes, views - NO triggers yet (stage 9 installs those)"""
    for f in ("pass2_migration.sql", "lot_ledger.sql", "pass3_migration.sql"):
        n = 0
        for kind, stmt in split_sql(io.open(f, encoding="utf-8").read()):
            if kind != "plain":
                continue
            # !! ix_nav_crfn IS DEFERRED TO THE LAST STAGE, DELIBERATELY.
            # It is the single most expensive object here: json_extract over
            # 24.8GB on the external drive, measured at 3.26 MB/s = ~2 HOURS,
            # holding a write lock the whole time. Built first (as it was on
            # the 10:37 run) it teaches us nothing for two hours while the
            # lanes sit paused. The doc_id reference route needs only the
            # PRIMARY KEY and yields a bbl 76.6% of the time, so nearly all
            # of the answer is reachable in minutes without this index. It
            # only widens the crfn half of the reference route.
            if "ix_nav_crfn" in stmt:
                continue
            db.execute(stmt)
            n += 1
        db.commit()
        log("schema from %-22s %d statements" % (f, n))


def stage2_keyrules(db):
    """replace key_rules so 'party' is a legal route"""
    sql = io.open("pass3_migration.sql", encoding="utf-8").read()
    i = sql.index("DROP TRIGGER IF EXISTS key_rules")
    j = sql.index("-- ── the board")
    for kind, stmt in split_sql(sql[i:j]):
        db.execute(stmt)
    db.commit()
    log("key_rules replaced - 'party' now legal, and may never carry a lot")


def stage3_refs(db):
    """Harvest reference edges out of the landed rd - ONE table scan per batch.

    !! THE FIRST VERSION READ EVERY ROW THREE TIMES. It ran a separate
    INSERT..SELECT per kind (doc_id / crfn / file_nbr), and each one re-scanned
    the same id range and re-ran json_each over the same JSON. On a 24.8GB
    table on the external drive that measured ~90s per 200k batch = ~3 HOURS.
    One MATERIALIZED pass over the edges, extracted three ways, is the same
    result for a third of the reads.

    RESUMABLE: the last finished id is committed with each batch, so a kill
    costs one batch, not the stage. The earlier version restarted at MIN(id)
    every time - which for a 3-hour stage means a kill near the end throws
    away everything.
    """
    db.execute("CREATE TABLE IF NOT EXISTS migration_cursor ("
               "stage INTEGER PRIMARY KEY, last_id TEXT)")
    db.commit()
    row = db.execute("SELECT last_id FROM migration_cursor WHERE stage=3").fetchone()
    cursor = row[0] if row else None
    if cursor:
        log("resuming refs backfill from id > %s" % cursor)

    n, t0 = 0, time.time()
    while True:
        lo = cursor if cursor else db.execute(
            "SELECT MIN(id) FROM navigation").fetchone()[0]
        nxt = db.execute("SELECT id FROM navigation WHERE id > ? ORDER BY id "
                         "LIMIT 1 OFFSET ?", (lo, BATCH)).fetchone()
        hi = nxt[0] if nxt else None
        # !! ALWAYS INCLUSIVE AT THE BOTTOM. `hi` is the FIRST ROW OF THE NEXT
        # batch and the batch range is [lo, hi) - so the cursor already points
        # at the first UNPROCESSED row. Resuming with `>` skips it, dropping
        # exactly one document per batch boundary, silently. Caught on the
        # scratch run with BATCH=3: 3 ref edges instead of 5, and the
        # reference route claimed 1 row instead of 3. At BATCH=200000 it would
        # have lost ~120 documents across the corpus and looked like nothing.
        if hi:
            where, rng = "n.id >= ? AND n.id < ?", (lo, hi)
        else:
            where, rng = "n.id >= ?", (lo,)
        db.execute("""
            INSERT OR IGNORE INTO refs(from_id, kind, value)
            WITH e AS MATERIALIZED (
              SELECT n.id AS id, j.value AS v
                FROM navigation n,
                     json_each(n.recorded_details,'$.references') j
               WHERE %s AND n.recorded_details != ''
                 AND json_extract(n.recorded_details,'$.references') IS NOT NULL)
            SELECT id,'doc_id',  json_extract(v,'$.doc_id')
              FROM e WHERE json_extract(v,'$.doc_id')   IS NOT NULL
            UNION ALL
            SELECT id,'crfn',    json_extract(v,'$.crfn')
              FROM e WHERE json_extract(v,'$.crfn')     IS NOT NULL
            UNION ALL
            SELECT id,'file_nbr',json_extract(v,'$.file_nbr')
              FROM e WHERE json_extract(v,'$.file_nbr') IS NOT NULL""" % where, rng)
        last = hi if hi else db.execute("SELECT MAX(id) FROM navigation").fetchone()[0]
        db.execute("INSERT OR REPLACE INTO migration_cursor(stage,last_id) VALUES (3,?)",
                   (last,))
        db.commit()
        n += 1
        cursor = hi
        if n % 5 == 0:
            c = db.execute("SELECT COUNT(*) FROM refs").fetchone()[0]
            log("refs batch %d  %s edges  %.0fs/batch  at %s"
                % (n, format(c, ","), (time.time() - t0) / n, last))
        if hi is None:
            break
    c = db.execute("SELECT COUNT(*) FROM refs").fetchone()[0]
    log("refs COMPLETE: %s edges" % format(c, ","))
    return "%d edges" % c


def stage4_subjects(db):
    """person-subject documents -> doc_subject"""
    db.execute(
        "INSERT OR IGNORE INTO doc_subject(doc_id,kind,value,role) "
        "SELECT n.id,'person',upper(trim(json_extract(j.value,'$.name'))),"
        "       json_extract(j.value,'$.panel') "
        "  FROM navigation n "
        "  JOIN subject_rule sr ON sr.kind='person' "
        "       AND sr.type = upper(json_extract(n.recorded_details,'$.type')) "
        "  , json_each(n.recorded_details,'$.parties') j "
        " WHERE n.recorded_details != '' AND COALESCE(n.key,'')='' "
        "   AND json_extract(n.recorded_details,'$.parties') IS NOT NULL "
        "   AND COALESCE(trim(json_extract(j.value,'$.name')),'') != ''")
    db.commit()
    c = db.execute("SELECT COUNT(*) FROM doc_subject").fetchone()[0]
    log("doc_subject: %s subject rows" % format(c, ","))
    return "%d subjects" % c


def stage5_party(db):
    """promote those rows to the 'party' route (key stays empty)"""
    cur = db.execute(
        "UPDATE navigation SET keyed_by='party' "
        " WHERE keyed_by='pdf-pass' "
        "   AND EXISTS (SELECT 1 FROM doc_subject WHERE doc_id = navigation.id)")
    db.commit()
    log("pass 3: %s rows keyed to a PERSON" % format(cur.rowcount, ","))
    return "%d party rows" % cur.rowcount


def stage6_crfnindex(db):
    log("building ix_nav_crfn over 21.6M rows - this is the long one")
    db.execute("CREATE INDEX IF NOT EXISTS ix_nav_crfn "
               "ON navigation(json_extract(recorded_details,'$.crfn')) "
               "WHERE recorded_details != ''")
    db.commit()
    log("ix_nav_crfn built")


def stage7_reference(db):
    """resolve pass 2 in SET operations, repeating until chains stop yielding"""
    total = 0
    for rnd in range(1, 12):
        cur = db.execute("""
            UPDATE navigation SET keyed_by='reference',
                   key=(SELECT key FROM v_reference_key WHERE id = navigation.id)
             WHERE keyed_by='pdf-pass'
               AND COALESCE((SELECT key FROM v_reference_key
                              WHERE id = navigation.id),'') != ''""")
        db.commit()
        log("pass 2 round %d: %s newly keyed" % (rnd, format(cur.rowcount, ",")))
        total += cur.rowcount
        if cur.rowcount == 0:
            break
    return "%d reference rows" % total


def stage8_ledger(db):
    """project every key into (bbl, doc) pairs"""
    n = 0
    for lo, hi in id_batches(db):
        rng = (lo, hi) if hi else (lo,)
        w = "id >= ? AND id < ?" if hi else "id >= ?"
        db.execute("""
          INSERT INTO doc_lot(bbl, doc_id, route, collective)
          WITH RECURSIVE src AS (SELECT id, key, keyed_by FROM navigation
                                  WHERE %s AND COALESCE(key,'') != ''),
          split(id, route, coll, bbl, rest) AS (
              SELECT id, keyed_by, CASE WHEN instr(key,';')>0 THEN 1 ELSE 0 END,
                     '', key || ';' FROM src
              UNION ALL
              SELECT id, route, coll,
                     substr(rest,1,instr(rest,';')-1),
                     substr(rest,instr(rest,';')+1)
                FROM split WHERE rest != '')
          SELECT bbl, id, route, coll FROM split WHERE bbl != ''
          ON CONFLICT(bbl,doc_id) DO NOTHING""" % w, rng)
        db.commit()
        n += 1
        if n % 10 == 0:
            c = db.execute("SELECT COUNT(*) FROM doc_lot").fetchone()[0]
            log("ledger batch %d ... %s pairs" % (n, format(c, ",")))
        if hi is None:
            break
    c = db.execute("SELECT COUNT(*) FROM doc_lot").fetchone()[0]
    log("doc_lot COMPLETE: %s (bbl,doc) pairs" % format(c, ","))
    return "%d pairs" % c


def stage9_triggers(db):
    """NOW install the go-forward triggers, for FUTURE landings only.

    key_rules is skipped here - stage 2 already replaced it, and re-running
    its DROP/CREATE would be a no-op at best and a window with no ladder
    enforcement at worst.
    """
    for f in ("pass2_migration.sql", "lot_ledger.sql", "pass3_migration.sql"):
        n = 0
        for kind, stmt in split_sql(io.open(f, encoding="utf-8").read()):
            if kind != "trigger" or " key_rules " in stmt.split("\n")[0] + " ":
                continue
            db.execute(stmt)
            n += 1
        db.commit()
        log("%d triggers from %s" % (n, f))


# ⚠ ORDER = CHEAPEST-INFORMATIVE FIRST, MOST EXPENSIVE LAST.
# Everything up to and including stage 9 runs on the primary key and on the
# json already in each row, so the whole keying picture appears in minutes.
# ix_nav_crfn (stage 10) is a ~2-hour full-table build that only WIDENS the
# reference route via crfn; the routes and the ledger are already correct
# without it, and it re-runs the reference resolver afterwards to pick up
# whatever the crfn edges add. Deferring it means the lanes can be judged,
# and restarted, long before it finishes.
STAGES = [(1, "schema", stage1_schema), (2, "key_rules", stage2_keyrules),
          (3, "refs backfill", stage3_refs), (4, "doc_subject", stage4_subjects),
          (5, "party route", stage5_party),
          (7, "reference route", stage7_reference), (8, "lot ledger", stage8_ledger),
          (9, "go-forward triggers", stage9_triggers),
          (6, "ix_nav_crfn (SLOW)", stage6_crfnindex),
          (10, "reference route again (crfn edges)", stage7_reference)]

if __name__ == "__main__":
    db = con(); state_init(db)
    if "--status" in sys.argv:
        for n, nm, _ in STAGES:
            r = db.execute("SELECT done_at,note FROM migration_state WHERE stage=?",
                           (n,)).fetchone()
            print("  %d %-22s %s" % (n, nm, ("DONE %s %s" % r) if r else "pending"))
        sys.exit()
    only = int(sys.argv[sys.argv.index("--stage") + 1]) if "--stage" in sys.argv else None
    for n, nm, fn in STAGES:
        if only and n != only:
            continue
        if done(db, n):
            log("stage %d %s - already done, skipping" % (n, nm)); continue
        log("STAGE %d - %s" % (n, nm))
        t0 = time.time()
        note = fn(db) or ""
        mark(db, n, nm, "%s (%.0fs)" % (note, time.time() - t0))
        log("stage %d done in %.0fs" % (n, time.time() - t0))
    db.close()
    print("\nMIGRATION COMPLETE")
