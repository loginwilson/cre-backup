"""END-TO-END: DOES PASS 2 WORK WHEN ONLY rd_walk'S OWN WRITE HAPPENS?

pass2_test.py inserted `refs` rows by hand, which is not how production works.
Here NOTHING is inserted by hand: a document lands exactly the way rd_walk
lands it - one UPDATE of recorded_details carrying parcels/references/crfn -
and every edge, key and route must be produced by triggers alone.

That difference matters because refs_on_rd and key_on_rd fire on the SAME
event (UPDATE OF recorded_details) and SQLite does not document an order
between them. If keying wins the race, the row is parked before its edges
exist. key_on_ref_insert is the belt-and-braces that makes the order stop
mattering; this file is what proves it.

Live schema + live triggers are read out of Legal Instruments.db and the
migration is applied on top, so what is tested is what would ship.
"""
import sqlite3, os, sys, json, io

LIVE = "D:/CRE Decoding System/Legal Instruments.db"
SCRATCH = "pass2_e2e.db"
MIGRATION = "pass2_migration.sql"


def live_sql():
    db = sqlite3.connect("file:" + LIVE.replace(" ", "%20") + "?mode=ro",
                         uri=True, timeout=10)
    out = [r[0] for r in db.execute(
        "SELECT sql FROM sqlite_master WHERE tbl_name='navigation' AND sql IS NOT NULL "
        "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END")]
    db.close()
    return out


def build():
    if os.path.exists(SCRATCH):
        os.remove(SCRATCH)
    db = sqlite3.connect(SCRATCH)
    db.execute("PRAGMA recursive_triggers = ON")
    for s in live_sql():
        db.executescript(s + ";")
    db.executescript(io.open(MIGRATION, encoding="utf-8").read())
    db.commit()
    return db


def land(db, doc_id, crfn=None, parcels=(), refs=()):
    """EXACTLY what rd_walk does: shell insert, then one rd write. Nothing else."""
    d = {"type": "TEST", "at": "2026-08-27T00:00:00"}
    if crfn:
        d["crfn"] = crfn
    if parcels:
        d["parcels"] = [{"bbl": b, "partial": "ENTIRE LOT"} for b in parcels]
    if refs:
        d["references"] = list(refs)
    db.execute("INSERT OR IGNORE INTO navigation"
               "(id,recorded_details,rd_url,pdf,pdf_url,keyed_by,key)"
               " VALUES (?,'','','','','','')", (doc_id,))
    db.execute("UPDATE navigation SET recorded_details=? WHERE id=?",
               (json.dumps(d), doc_id))


def st(db, i):
    r = db.execute("SELECT keyed_by,key FROM navigation WHERE id=?", (i,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


FAILED = []


def check(name, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + name)
    if not ok:
        print("          got  %r" % (got,))
        print("          want %r" % (want,))
        FAILED.append(name)


db = build()
print("recursive_triggers =", db.execute("PRAGMA recursive_triggers").fetchone()[0])
trg = [r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")]
print("triggers:", ", ".join(trg))
print()

print("A. EDGE HARVEST - refs must appear with no hand insert")
land(db, "D1", crfn="1000000000001", parcels=["1000010001"])
land(db, "D2", crfn="1000000000002",
     refs=[{"doc_id": "D1", "crfn": "1000000000001"}])
n = db.execute("SELECT COUNT(*) FROM refs WHERE from_id='D2'").fetchone()[0]
check("D2's edges harvested from the rd json", n, 2)
check("D2 keyed off D1 by reference", st(db, "D2"), ("reference", "1000010001"))
print()

print("B. THE RACE - keying vs edge-harvest on the same event")
# D3 has NO parcels and one reference to an ALREADY-keyed doc. If key_on_rd
# wins the race, key_on_reference sees no edges; if refs_on_rd wins,
# key_on_reference resolves. Either way the outcome must be identical.
land(db, "D3", crfn="1000000000003", refs=[{"doc_id": "D1"}])
check("D3 resolves regardless of trigger order", st(db, "D3"),
      ("reference", "1000010001"))
print()

print("C. TARGET ARRIVES LATER - the direction that removes the 100% gate")
land(db, "D4", crfn="1000000000004", refs=[{"doc_id": "D5"}])
check("D4 parks (D5 not landed)", st(db, "D4"), ("pdf-pass", ""))
land(db, "D5", crfn="1000000000005", parcels=["2000020002"])
check("D4 resolves retroactively", st(db, "D4"), ("reference", "2000020002"))
print()

print("D. CRFN ROUTE - target named by crfn, not doc id")
land(db, "D6", crfn="1000000000006", refs=[{"crfn": "1000000000007"}])
check("D6 parks", st(db, "D6"), ("pdf-pass", ""))
land(db, "D7", crfn="1000000000007", parcels=["3000030003"])
check("D6 resolves via crfn", st(db, "D6"), ("reference", "3000030003"))
print()

print("E. MULTI-REFERENCE - two keyed targets")
land(db, "D8", crfn="1000000000008", parcels=["4000040004"])
land(db, "D9", crfn="1000000000009",
     refs=[{"doc_id": "D1"}, {"doc_id": "D8"}])
check("D9 carries both lots", st(db, "D9"),
      ("reference", "1000010001;4000040004"))
print()

print("F. MULTI-PARCEL TARGET - inherit a ';'-joined key whole")
land(db, "E1", crfn="1000000000021", parcels=["5000050005", "5000050006"])
land(db, "E2", crfn="1000000000022", refs=[{"doc_id": "E1"}])
check("E2 inherits both of E1's lots", st(db, "E2"),
      ("reference", "5000050005;5000050006"))
print()

print("G. file_nbr IS EVIDENCE, NOT A ROUTE")
land(db, "E3", crfn="1000000000023", refs=[{"file_nbr": "ABC-1234"}])
check("E3 stays parked on a file_nbr alone", st(db, "E3"), ("pdf-pass", ""))
n = db.execute("SELECT COUNT(*) FROM refs WHERE from_id='E3'").fetchone()[0]
check("but the edge is still recorded", n, 1)
print()

print("H. CHAIN - depth 3, leaf lands last")
land(db, "F1", crfn="1000000000031", refs=[{"doc_id": "F2"}])
land(db, "F2", crfn="1000000000032", refs=[{"doc_id": "F3"}])
land(db, "F3", crfn="1000000000033", refs=[{"doc_id": "F4"}])
land(db, "F4", crfn="1000000000034", parcels=["6000060006"])
check("F3 resolves", st(db, "F3"), ("reference", "6000060006"))
check("F2 resolves", st(db, "F2"), ("reference", "6000060006"))
check("F1 resolves (depth 3)", st(db, "F1"), ("reference", "6000060006"))
print()

print("I. CYCLE - mutual reference, no lot anywhere")
land(db, "G1", crfn="1000000000041", refs=[{"doc_id": "G2"}])
try:
    land(db, "G2", crfn="1000000000042", refs=[{"doc_id": "G1"}])
    check("G1 parks, no spin", st(db, "G1"), ("pdf-pass", ""))
    check("G2 parks, no spin", st(db, "G2"), ("pdf-pass", ""))
except sqlite3.Error as e:
    check("cycle survived", "ERR %s" % str(e)[:50], "no error")
print()

print("J. CYCLE TOUCHING A KEYED ROW")
land(db, "H1", crfn="1000000000051", refs=[{"doc_id": "H2"}])
land(db, "H2", crfn="1000000000052",
     refs=[{"doc_id": "H1"}, {"doc_id": "H3"}])
try:
    land(db, "H3", crfn="1000000000053", parcels=["7000070007"])
    check("H2 resolves through the cycle", st(db, "H2")[0], "reference")
except sqlite3.Error as e:
    check("keyed cycle survived", "ERR %s" % str(e)[:50], "no error")
print()

print("K. NO REGRESSION - pass 1 untouched")
land(db, "I1", crfn="1000000000061", parcels=["8000080008"])
check("parcels still win outright", st(db, "I1"), ("parcel", "8000080008"))
land(db, "I2", crfn="1000000000062")
check("no parcels, no refs -> pdf-pass", st(db, "I2"), ("pdf-pass", ""))
print()

print("L. LADDER INTEGRITY")
bad = db.execute("""SELECT id,keyed_by,key FROM navigation WHERE
      (keyed_by='pdf-pass' AND COALESCE(key,'')!='')
   OR (keyed_by IN ('parcel','reference') AND COALESCE(key,'')='')
   OR (COALESCE(keyed_by,'')='' AND COALESCE(key,'')!='')
   OR keyed_by NOT IN ('','parcel','reference','pdf-pass','pdf')""").fetchall()
check("no row violates key_rules", bad, [])

rows = db.execute("SELECT keyed_by, COUNT(*) FROM navigation "
                  "GROUP BY keyed_by ORDER BY 2 DESC").fetchall()
db.commit()
print()
print("  final routes: " + " · ".join("%s=%d" % (r[0] or "''", r[1]) for r in rows))
print("=" * 64)
if FAILED:
    print("FAILED %d: %s" % (len(FAILED), ", ".join(FAILED)))
    sys.exit(1)
print("ALL PASS - pass 2 works on rd_walk's write alone")
