"""ALL THREE PASSES + THE LOT LEDGER, ON rd_walk'S WRITE ALONE.

Live schema and live triggers are read out of Legal Instruments.db; the three
migrations are applied on top; then documents land exactly the way rd_walk
lands them - one UPDATE of recorded_details - and every edge, key, route and
ledger row must be produced by triggers with nothing inserted by hand.

The cases that matter are the ones where a pass could quietly do the WRONG
thing rather than nothing: a weak route overwriting a strong one, a party
route smuggling a lot, a multi-lot document's quantities looking distributable.
"""
import sqlite3, os, sys, json, io

LIVE = "D:/CRE Decoding System/Legal Instruments.db"
SCRATCH = "passes.db"
MIGRATIONS = ["pass2_migration.sql", "lot_ledger.sql", "pass3_migration.sql"]


def build():
    if os.path.exists(SCRATCH):
        os.remove(SCRATCH)
    src = sqlite3.connect("file:" + LIVE.replace(" ", "%20") + "?mode=ro",
                          uri=True, timeout=10)
    ddl = [r[0] for r in src.execute(
        "SELECT sql FROM sqlite_master WHERE tbl_name='navigation' AND sql IS NOT NULL "
        "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 ELSE 2 END")]
    src.close()
    db = sqlite3.connect(SCRATCH)
    db.execute("PRAGMA recursive_triggers = ON")
    for s in ddl:
        db.executescript(s + ";")
    for m in MIGRATIONS:
        db.executescript(io.open(m, encoding="utf-8").read())
    db.commit()
    return db


def land(db, doc_id, typ="DEED", crfn=None, parcels=(), refs=(), parties=()):
    d = {"type": typ, "at": "2026-08-27T00:00:00"}
    if crfn:
        d["crfn"] = crfn
    if parcels:
        d["parcels"] = [{"bbl": b} for b in parcels]
    if refs:
        d["references"] = list(refs)
    if parties:
        d["parties"] = [{"panel": str(i + 1), "name": n}
                        for i, n in enumerate(parties)]
    db.execute("INSERT OR IGNORE INTO navigation"
               "(id,recorded_details,rd_url,pdf,pdf_url,keyed_by,key)"
               " VALUES (?,'','','','','','')", (doc_id,))
    db.execute("UPDATE navigation SET recorded_details=? WHERE id=?",
               (json.dumps(d), doc_id))


def st(db, i):
    r = db.execute("SELECT keyed_by,key FROM navigation WHERE id=?", (i,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def lots(db, i):
    return sorted(r[0] for r in
                  db.execute("SELECT bbl FROM doc_lot WHERE doc_id=?", (i,)))


FAILED = []


def check(name, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + name)
    if not ok:
        print("          got  %r" % (got,))
        print("          want %r" % (want,))
        FAILED.append(name)


db = build()
print("triggers:", ", ".join(r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")))
print()

print("PASS 1 - the document names its own lots")
land(db, "P1", typ="DEED", crfn="1000000000001", parcels=["1000010001"])
check("route parcel", st(db, "P1"), ("parcel", "1000010001"))
check("ledger row created", lots(db, "P1"), ["1000010001"])
print()

print("LEDGER - the multi-lot case an equality seek on `key` MISSES")
land(db, "P2", typ="DEED", crfn="1000000000002",
     parcels=["2000020001", "2000020002", "2000020003"])
check("key is the joined string", st(db, "P2")[1],
      "2000020001;2000020002;2000020003")
check("ledger splits it into 3 seekable rows", lots(db, "P2"),
      ["2000020001", "2000020002", "2000020003"])
n = db.execute("SELECT COUNT(*) FROM navigation WHERE key='2000020002'").fetchone()[0]
check("...and `key` equality finds NONE of them", n, 0)
n = db.execute("SELECT COUNT(*) FROM doc_lot WHERE bbl='2000020002'").fetchone()[0]
check("...while the ledger finds it", n, 1)
check("marked collective (quantities must NOT distribute)",
      db.execute("SELECT collective FROM doc_lot WHERE doc_id='P2' LIMIT 1").fetchone()[0], 1)
check("single-lot doc NOT marked collective",
      db.execute("SELECT collective FROM doc_lot WHERE doc_id='P1'").fetchone()[0], 0)
print()

print("PASS 2 - a cited document names the lots")
land(db, "P3", typ="SATISFACTION OF MORTGAGE", crfn="1000000000003",
     refs=[{"doc_id": "P1"}])
check("route reference, inherits P1's lot", st(db, "P3"),
      ("reference", "1000010001"))
check("ledger followed", lots(db, "P3"), ["1000010001"])
print()

print("PASS 2 - target lands later (no 100%-completion gate)")
land(db, "P4", typ="ASSIGNMENT, MORTGAGE", crfn="1000000000004",
     refs=[{"doc_id": "P5"}])
check("parks", st(db, "P4"), ("pdf-pass", ""))
land(db, "P5", typ="MORTGAGE", crfn="1000000000005", parcels=["3000030003"])
check("resolves retroactively", st(db, "P4"), ("reference", "3000030003"))
check("ledger caught up", lots(db, "P4"), ["3000030003"])
print()

print("PASS 3 - the subject is a PERSON, not a parcel")
land(db, "P6", typ="FEDERAL LIEN-IRS", crfn="1000000000006",
     parties=["SMITH, JOHN A", "UNITED STATES OF AMERICA"])
check("route party", st(db, "P6")[0], "party")
check("!! key stays EMPTY - no lot is claimed", st(db, "P6")[1], "")
check("subjects recorded", sorted(
    r[0] for r in db.execute("SELECT value FROM doc_subject WHERE doc_id='P6'")),
    ["SMITH, JOHN A", "UNITED STATES OF AMERICA"])
check("NO ledger row - a person is not a lot", lots(db, "P6"), [])
print()

print("PASS 3 - does NOT fire when the type does name a parcel")
land(db, "P7", typ="POWER OF ATTORNEY", crfn="1000000000007",
     parcels=["4000040004"], parties=["DOE, JANE"])
check("parcel wins outright", st(db, "P7"), ("parcel", "4000040004"))
print()

print("PASS 3 - a non-statutory parcel-less row is NOT keyed to its parties")
land(db, "P8", typ="AGREEMENT", crfn="1000000000008",
     parties=["SMITH, JOHN A"])
check("stays pdf-pass (AGREEMENT is not a person-subject type)",
      st(db, "P8"), ("pdf-pass", ""))
print()

print("LADDER - a weak route may never overwrite a strong one")
land(db, "P9", typ="DEED", crfn="1000000000009", parcels=["5000050005"])
db.execute("UPDATE navigation SET keyed_by='reference', key='9999999999' "
           "WHERE id='P9'")
r = db.execute("SELECT route FROM doc_lot WHERE doc_id='P9' AND bbl='5000050005'").fetchone()
check("original parcel attachment kept its route", r[0], "parcel")
print()

print("GUARD - a party route may never smuggle a lot in")
try:
    db.execute("UPDATE navigation SET keyed_by='party', key='1000010001' "
               "WHERE id='P6'")
    check("ABORTed", "no error raised", "ABORT")
except sqlite3.IntegrityError as e:
    ok = "SUBJECT IS A PERSON" in str(e)
    check("ABORTed with the reason", ok, True)
print()

print("SELECT A BBL - the query the whole decode stage stands on")
rows = db.execute("SELECT doc_id, route, type, collective FROM v_lot_docs "
                  "WHERE bbl='1000010001' ORDER BY doc_id").fetchall()
check("lot 1000010001 returns both its documents",
      [(r[0], r[1]) for r in rows], [("P1", "parcel"), ("P3", "reference")])
print("          " + " · ".join("%s %s/%s" % (r[0], r[1], r[2][:18]) for r in rows))
print()

print("LADDER BOARD")
for route, meaning, n in db.execute(
        "SELECT route, meaning, docs FROM v_key_ladder ORDER BY meaning"):
    print("   %-10s %-46s %s" % (route or "''", meaning, n))

db.commit()
print()
print("=" * 66)
if FAILED:
    print("FAILED %d: %s" % (len(FAILED), ", ".join(FAILED)))
    sys.exit(1)
print("ALL PASS - three passes + ledger, on rd_walk's write alone")
