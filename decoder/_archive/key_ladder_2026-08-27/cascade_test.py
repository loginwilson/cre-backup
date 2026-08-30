"""HOW DO WE MAKE A REFERENCE CHAIN DEEPER THAN ONE HOP RESOLVE?

pass2_test.py case 7 failed: R lands and keys Q, but Q becoming keyed does not
re-fire the dependents trigger for P, because recursive_triggers defaults OFF -
SQLite will not re-enter a trigger from that trigger's own action.

Two candidate fixes, run against the same scenarios:

  A  PRAGMA recursive_triggers = ON       one line, but it is a PER-CONNECTION
                                          pragma: every writer must set it or
                                          chains silently stop resolving there.
  B  transitive closure in SQL            self-contained in the schema, works
                                          on any connection, costs a recursive
                                          CTE per fire.

Reported side by side, including the cycle case, which is what would punish a
transitive walk if the guard is wrong.
"""
import sqlite3, os, sys, json

LIVE = "D:/CRE Decoding System/Legal Instruments.db"


def live_sql():
    db = sqlite3.connect("file:" + LIVE.replace(" ", "%20") + "?mode=ro",
                         uri=True, timeout=10)
    out = [r[0] for r in db.execute(
        "SELECT sql FROM sqlite_master WHERE tbl_name='navigation' AND sql IS NOT NULL "
        "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END")]
    db.close()
    return out


BASE = """
CREATE TABLE refs (
  from_id TEXT NOT NULL, kind TEXT NOT NULL, value TEXT NOT NULL,
  PRIMARY KEY (from_id, kind, value)) WITHOUT ROWID;
CREATE INDEX ix_refs_target ON refs(kind, value);
CREATE INDEX ix_nav_crfn ON navigation(json_extract(recorded_details,'$.crfn'))
  WHERE recorded_details != '';

CREATE VIEW v_reference_key AS
SELECT r.from_id AS id,
       (SELECT group_concat(k, ';') FROM (
          SELECT DISTINCT t.key AS k FROM refs r2 JOIN navigation t
            ON (r2.kind='doc_id' AND t.id = r2.value)
            OR (r2.kind='crfn' AND json_extract(t.recorded_details,'$.crfn') = r2.value)
           WHERE r2.from_id = r.from_id AND COALESCE(t.key,'') != ''
           ORDER BY t.key)) AS key
  FROM refs r GROUP BY r.from_id;

CREATE TRIGGER key_on_reference AFTER UPDATE OF keyed_by ON navigation
WHEN NEW.keyed_by = 'pdf-pass'
 AND COALESCE((SELECT key FROM v_reference_key WHERE id = NEW.id),'') != ''
BEGIN
  UPDATE navigation SET keyed_by='reference',
    key=(SELECT key FROM v_reference_key WHERE id=NEW.id) WHERE id=NEW.id;
END;
"""

# A: direct dependents only, but the pragma lets the trigger re-enter itself
DEP_DIRECT = """
CREATE TRIGGER key_dependents_on_key AFTER UPDATE OF key ON navigation
WHEN COALESCE(NEW.key,'') != '' AND COALESCE(OLD.key,'') = ''
BEGIN
  UPDATE navigation SET keyed_by='reference',
     key=(SELECT key FROM v_reference_key WHERE id=navigation.id)
   WHERE keyed_by='pdf-pass'
     AND id IN (SELECT from_id FROM refs
                 WHERE (kind='doc_id' AND value=NEW.id)
                    OR (kind='crfn' AND value=json_extract(NEW.recorded_details,'$.crfn')))
     AND COALESCE((SELECT key FROM v_reference_key WHERE id=navigation.id),'') != '';
END;
"""

# B: walk the reverse reference graph in one statement, no pragma needed.
# UNION (not UNION ALL) terminates a cycle: a node already in the working set
# is not re-added, so A->B->A closes instead of spinning.
DEP_CLOSURE = """
CREATE TRIGGER key_dependents_on_key AFTER UPDATE OF key ON navigation
WHEN COALESCE(NEW.key,'') != '' AND COALESCE(OLD.key,'') = ''
BEGIN
  UPDATE navigation SET keyed_by='reference',
     key=(SELECT key FROM v_reference_key WHERE id=navigation.id)
   WHERE keyed_by='pdf-pass'
     AND id IN (
       WITH RECURSIVE up(n) AS (
         SELECT from_id FROM refs
          WHERE (kind='doc_id' AND value=NEW.id)
             OR (kind='crfn' AND value=json_extract(NEW.recorded_details,'$.crfn'))
         UNION
         SELECT r.from_id FROM refs r JOIN up ON r.value = up.n AND r.kind='doc_id'
       ) SELECT n FROM up)
     AND COALESCE((SELECT key FROM v_reference_key WHERE id=navigation.id),'') != '';
END;
"""


def build(dep_sql, recursive):
    path = "cascade_%s.db" % ("A" if recursive else "B")
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    if recursive:
        db.execute("PRAGMA recursive_triggers = ON")
    for s in live_sql():
        db.executescript(s + ";")
    db.executescript(BASE)
    db.executescript(dep_sql)
    db.commit()
    return db


def rd(crfn, *bbls):
    return json.dumps({"crfn": crfn, "parcels": [{"bbl": b} for b in bbls]})


def shell(db, i):
    db.execute("INSERT OR IGNORE INTO navigation"
               "(id,recorded_details,rd_url,pdf,pdf_url,keyed_by,key)"
               " VALUES (?,'','','','','','')", (i,))


def land(db, i, crfn, *bbls):
    shell(db, i)
    db.execute("UPDATE navigation SET recorded_details=? WHERE id=?", (rd(crfn, *bbls), i))


def ref(db, f, k, v):
    db.execute("INSERT OR IGNORE INTO refs(from_id,kind,value) VALUES (?,?,?)", (f, k, v))


def st(db, i):
    r = db.execute("SELECT keyed_by,key FROM navigation WHERE id=?", (i,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def scenarios(db, label):
    res = {}

    # depth 1 - the case that already worked
    land(db, "T1", "C-T1", "1000010001")
    shell(db, "S1"); ref(db, "S1", "doc_id", "T1"); land(db, "S1", "C-S1")
    res["depth-1"] = st(db, "S1") == ("reference", "1000010001")

    # depth 2 - P -> Q -> R, landed leaf-last
    shell(db, "P2"); shell(db, "Q2")
    ref(db, "P2", "doc_id", "Q2"); ref(db, "Q2", "doc_id", "R2")
    land(db, "P2", "C-P2"); land(db, "Q2", "C-Q2")
    land(db, "R2", "C-R2", "2000020002")
    res["depth-2"] = st(db, "P2") == ("reference", "2000020002")

    # depth 3
    shell(db, "A3"); shell(db, "B3"); shell(db, "C3")
    ref(db, "A3", "doc_id", "B3"); ref(db, "B3", "doc_id", "C3")
    ref(db, "C3", "doc_id", "D3")
    land(db, "A3", "C-A3"); land(db, "B3", "C-B3"); land(db, "C3", "C-C3")
    land(db, "D3", "C-D3", "3000030003")
    res["depth-3"] = st(db, "A3") == ("reference", "3000030003")

    # cycle with NO key anywhere - must not spin
    shell(db, "X"); shell(db, "Y")
    ref(db, "X", "doc_id", "Y"); ref(db, "Y", "doc_id", "X")
    try:
        land(db, "X", "C-X"); land(db, "Y", "C-Y")
        res["cycle-unkeyed"] = st(db, "X") == ("pdf-pass", "")
    except sqlite3.Error as e:
        res["cycle-unkeyed"] = "ERR " + str(e)[:40]

    # cycle that TOUCHES a keyed row - the nasty one
    shell(db, "M"); shell(db, "N")
    ref(db, "M", "doc_id", "N"); ref(db, "N", "doc_id", "M")
    ref(db, "N", "doc_id", "K9")
    land(db, "M", "C-M"); land(db, "N", "C-N")
    try:
        land(db, "K9", "C-K9", "4000040004")
        res["cycle-keyed"] = st(db, "N")[0] == "reference"
    except sqlite3.Error as e:
        res["cycle-keyed"] = "ERR " + str(e)[:40]

    # ladder integrity
    bad = db.execute("""SELECT COUNT(*) FROM navigation WHERE
          (keyed_by='pdf-pass' AND COALESCE(key,'')!='')
       OR (keyed_by IN ('parcel','reference') AND COALESCE(key,'')='')
       OR (COALESCE(keyed_by,'')='' AND COALESCE(key,'')!='')""").fetchone()[0]
    res["ladder-clean"] = (bad == 0)
    db.commit()
    return res


print("A = PRAGMA recursive_triggers ON  ·  B = transitive closure in SQL")
print()
ra = scenarios(build(DEP_DIRECT, True), "A")
rb = scenarios(build(DEP_CLOSURE, False), "B")

print("  %-18s %-22s %s" % ("scenario", "A (pragma)", "B (closure)"))
print("  " + "-" * 58)
for k in ["depth-1", "depth-2", "depth-3", "cycle-unkeyed", "cycle-keyed", "ladder-clean"]:
    def f(v):
        return "PASS" if v is True else ("FAIL" if v is False else str(v))
    print("  %-18s %-22s %s" % (k, f(ra[k]), f(rb[k])))
print()
awin = all(v is True for v in ra.values())
bwin = all(v is True for v in rb.values())
print("A all-pass: %s   B all-pass: %s" % (awin, bwin))
