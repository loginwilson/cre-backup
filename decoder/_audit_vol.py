import sqlite3, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:D:/acris/01-specification/page_counts.db?mode=ro", uri=True, timeout=600)
n, tot, zero, mx = c.execute(
    "SELECT COUNT(*), SUM(n), SUM(CASE WHEN n=0 OR n IS NULL THEN 1 ELSE 0 END), MAX(n) FROM pages"
).fetchone()
print(f"  documents with a page count : {n:>14,}")
print(f"  TOTAL PAGES BEHIND THEM     : {tot:>14,}")
print(f"  zero-page (no image)        : {zero:>14,}")
print(f"  largest single document     : {mx:>14,} pages")
print(f"  mean pages/document         : {tot/max(n-zero,1):>14.1f}")
