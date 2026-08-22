"""READ THE ONE TABLE - the readability half of the sqlite flip (login:
"as long as it is readable then yes").

    python nav_view.py                       first 20 rows, console
    python nav_view.py --id 2026061801039001 one document's full row
    python nav_view.py --key 4017741405      one parcel's chronology
    python nav_view.py --head 1000 --csv     slice exported beside the db
    python nav_view.py --stats               fill counts with denominators
"""
import argparse
import csv
import json
import pathlib
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

ap = argparse.ArgumentParser()
ap.add_argument("--id")
ap.add_argument("--key")
ap.add_argument("--head", type=int, default=20)
ap.add_argument("--csv", action="store_true",
                help="write the result as a csv beside the db")
ap.add_argument("--stats", action="store_true")
a = ap.parse_args()

con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True)
COLS = ["id", "recorded_details", "rd_url", "pdf", "pdf_url", "keyed_by", "key"]

if a.stats:
    total = con.execute("SELECT COUNT(*) FROM navigation").fetchone()[0]
    for label, where in (
            ("recorded_details", "recorded_details != ''"),
            ("pdf", "pdf != ''"),
            ("key", "key != ''")):
        c = con.execute(f"SELECT COUNT(*) FROM navigation WHERE {where}"
                        ).fetchone()[0]
        print(f"  {label:<18} {c:>12,} / {total:,}  ({100*c/total:.2f}%)")
    sys.exit(0)

if a.id:
    row = con.execute("SELECT * FROM navigation WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit(f"{a.id}: not in the table")
    for c, v in zip(COLS, row):
        if c == "recorded_details" and v:
            print(f"{c}:")
            print(json.dumps(json.loads(v), indent=2))
        else:
            print(f"{c}: {v or '(empty)'}")
    sys.exit(0)

if a.key:
    rows = con.execute(
        "SELECT id, json_extract(recorded_details,'$.recorded') rec,"
        " json_extract(recorded_details,'$.type') type, pdf"
        " FROM navigation WHERE key=? OR key LIKE ? ORDER BY rec, id",
        (a.key, f"%{a.key}%")).fetchall()
    print(f"{a.key}: {len(rows)} document(s), oldest first")
    for did, rec, dt, pdf in rows:
        print(f"  {rec or '(no date)':<12} {dt or '?':<8} {did:<22}"
              f" {'pdf' if pdf else '-'}")
    sys.exit(0)

rows = con.execute(f"SELECT * FROM navigation LIMIT {a.head}").fetchall()
if a.csv:
    out = CP.NAV_DB.parent / "_working" / f"view_head{a.head}.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}")
else:
    for row in rows:
        print(" | ".join((v[:60] if isinstance(v, str) else str(v))
                         for v in row))
