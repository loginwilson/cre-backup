import sqlite3, sys, time
sys.path.insert(0, r"C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
con.execute("PRAGMA busy_timeout=300000")
t = time.time()
rows = con.execute(
    "SELECT CASE WHEN keyed_by IS NULL OR keyed_by='' THEN '(BLANK)' ELSE keyed_by END,"
    " COUNT(*) FROM navigation WHERE recorded_details != '' GROUP BY 1").fetchall()
tot = sum(n for _k, n in rows)
print("THE GATE - every rd-landed row, by pass-1 verdict  (%.1f min scan)" % ((time.time()-t)/60), flush=True)
blank = 0
for k, n in sorted(rows, key=lambda r: -r[1]):
    print("  %-10s %14s   %6.2f%%" % (k, "{:,}".format(n), 100.0*n/tot), flush=True)
    if k == "(BLANK)": blank = n
print("  %-10s %14s" % ("TOTAL", "{:,}".format(tot)), flush=True)
print(flush=True)
print("UNKEYED WITH RD: %s  ->  %s" % ("{:,}".format(blank),
      "GATE PASSES - restart the fleet" if blank == 0 else "GATE FAILS"), flush=True)
