"""FIND RICHMOND'S DETAIL-FETCH CEILING — measured, warm, and stopped on refusal.

⚠ WARM, NOT COLD. The only trip this project ever caused was conc 16 COLD in a
burst. Each level here reuses per-worker sessions that have already completed a
search, and levels run in ascending order so a degradation shows before the next
step rather than after it.
⚠ ANY Refused ABORTS THE WHOLE SWEEP. No retry, no rotation.
"""
import sys, time, threading, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from concurrent.futures import ThreadPoolExecutor
import rc_sync as RS, rc_source as RC

seed = RS.Window("08/17/2026", "08/17/2026")
pool = [r["internal_id"] for r in seed.rows()]
prev = None
for CONC in (56, 80, 112):
    tl = threading.local()
    ids = (pool * 4)[:CONC * 8]
    bad = [0]

    def one(i):
        try:
            if not hasattr(tl, "w"):
                tl.w = RS.Window("08/17/2026", "08/17/2026")
            return 1 if tl.w.detail(i) else 0
        except RC.Refused:
            bad[0] = -1
            return 0
        except Exception:
            bad[0] += 1
            return 0

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=CONC) as ex:
        ok = sum(ex.map(one, ids))
    el = time.time() - t0
    rate = len(ids) / el
    if bad[0] == -1:
        print(f"  conc {CONC}: REFUSED — stopping, no retry.")
        break
    gain = f"{rate/prev:.2f}x" if prev else "—"
    print(f"  conc {CONC:>2}: {len(ids):>3} docs · {ok} ok · {bad[0]} err · "
          f"{el:>5.1f}s · {rate:>4.1f} doc/s ({gain} vs prev) -> "
          f"2,426,404 = {2426404/rate/3600:>5.0f} h", flush=True)
    if bad[0] > len(ids) * 0.05:
        print("    error rate > 5% — treating this as the ceiling, stopping.")
        break
    prev = rate
