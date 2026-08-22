import sqlite3, sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
p = pathlib.Path(CP.SPEC_DB)
print(f"  SPECIFICATION DB: {p}")
print(f"    size {p.stat().st_size/1e9:.2f} GB   drive {p.drive}")
c = sqlite3.connect("file:" + str(p).replace("\\", "/") + "?mode=ro", uri=True, timeout=900)
print("\n  COMPONENTS")
for t in ("document", "parcel", "parcel_document", "party_document",
          "reference_document", "remark_document", "rc_binding"):
    t0 = time.time()
    try:
        n = c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"    {t:<20} {n:>14,}   ({time.time()-t0:.0f}s)", flush=True)
    except Exception as e:
        print(f"    {t:<20} MISSING/ERR {type(e).__name__}", flush=True)
c.close()
