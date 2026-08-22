import sqlite3, sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = pathlib.Path("D:/acris/01-specification/page_counts.db")
print(f"  page_counts.db  {p.stat().st_size/1e9:.2f} GB")
c = sqlite3.connect("file:" + str(p).replace("\\", "/") + "?mode=ro", uri=True, timeout=600)
tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("  tables:", tabs)
for t in tabs:
    cols = [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')]
    n = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f"    {t:<18} {n:>12,}  cols={cols}", flush=True)
