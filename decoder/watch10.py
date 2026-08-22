"""RATE AND HEALTH OVER A FIXED WINDOW — for the 10-minute check-in.

⚠ MEASURE FROM THE LEDGER, over a WINDOW. The driver's own running average is polluted
by whatever happened at start-up (the 4-minute skip-scan pinned it at 16 pg/s while the
true rate was 110). A cumulative average answers "how has it gone"; a windowed rate
answers "is it working NOW", which is the question a check-in asks.
"""
import sqlite3, time, sys, os, psutil, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LED = "D:/acris/00-run/state/ledger.sqlite"
LOG = pathlib.Path("D:/acris/00-run/logs/overnight_run.log")
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 600

# ⚠ DENOMINATORS ARE MANDATORY — a rate without one says nothing about progress.
# parcels/documents are exact counts from parcel_spec.db.
# PAGES is measured, not guessed: page_counts.db holds hid_TotalPages for 16,901,071 of
# 17,049,742 documents (99.13%) summing to 148,798,851 pages, mean 8.80/doc. Extrapolating
# that mean over the missing 0.87% gives the figure below. The docs' older "148.2M" was an
# estimate; this one is derived from the register's own page counts.
# ⚠ DERIVED AT RUNTIME, NOT HARDCODED. These were literals until 2026-08-18, when the
# live sync added +12,063 documents and every percentage silently began measuring against
# a corpus that had moved. A denominator that cannot grow reports progress that is not
# real — and the drift is invisible because the number still looks like a number.
def _totals():
    try:
        c = sqlite3.connect("file:D:/acris/01-specification/parcel_spec.db?mode=ro", uri=True)
        par = c.execute("SELECT COUNT(*) FROM parcel").fetchone()[0]
        doc = c.execute("SELECT COUNT(*) FROM document").fetchone()[0]
        c.close()
        # pages: mean pages/doc from page_counts.db, extrapolated over all documents.
        pc = pathlib.Path("D:/acris/01-specification/page_counts.db")
        if pc.exists():
            c = sqlite3.connect(f"file:{pc}?mode=ro", uri=True)
            n, s = c.execute("SELECT COUNT(*), SUM(n) FROM pages").fetchone()
            c.close()
            pages = int(s / n * doc) if n else 150_107_766
        else:
            pages = 150_107_766
        return par, doc, pages
    except Exception:
        return 1_250_935, 17_049_742, 150_107_766      # last known good


TOT_PARCELS, TOT_DOCS, TOT_PAGES = _totals()


def parcels():
    """⚠ DIR ENUMERATION ONLY — never read _INDEX.md here. Counting 7,201 lot dirs costs
    0.3 s; reading each manifest is what makes the driver's skip-scan take minutes, and a
    checkpoint must not compete with the workers for the same USB drive."""
    BY = pathlib.Path("D:/acris/02-acquisition/by-parcel")
    n = 0
    try:
        for boro in BY.iterdir():
            if not boro.is_dir():
                continue
            for blk in boro.iterdir():
                if blk.is_dir():
                    n += sum(1 for _ in blk.iterdir())
    except OSError:
        pass
    return n


def snap():
    c = sqlite3.connect(f"file:{LED}?mode=ro", uri=True)
    r = c.execute("SELECT COUNT(*), COALESCE(SUM(got),0), COALESCE(SUM(bytes),0) "
                  "FROM doc WHERE status='ok'").fetchone()
    c.close()
    return r


def procs():
    """⚠ MATCH THE INTERPRETER RUNNING THE SCRIPT, NOT ANY LINE MENTIONING IT. The first
    version substring-matched the whole command line, so bash wrappers and this very
    checkpoint counted as drivers — it reported `driver 4` when exactly one driver was
    running, which reads as the duplicate-breeding failure the PID guard exists to stop.
    A monitor that cries wolf about duplicates is worse than none."""
    n = {"overnight.py": 0, "acquire_async.py": 0, "watchdog.py": 0}
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if not (p.info.get("name") or "").lower().startswith("python"):
                continue
            cl = p.info.get("cmdline") or []
            if len(cl) < 2:
                continue
            script = pathlib.Path(str(cl[1]) if str(cl[1]) != "-u" else
                                  (cl[2] if len(cl) > 2 else "")).name
            if script in n:
                n[script] += 1
        except Exception:
            continue
    return n


def main():
    d0, p0, b0 = snap(); q0 = parcels(); t0 = time.time()
    time.sleep(WINDOW)
    d1, p1, b1 = snap(); q1 = parcels(); dt = time.time() - t0
    vm = psutil.virtual_memory()
    st = procs()
    stop = pathlib.Path("D:/acris/00-run/state/_STOP")
    last = [l for l in LOG.read_text(encoding="utf-8", errors="replace").splitlines() if "pg/s" in l]

    print(f"RATE      {(p1-p0)/dt:.1f} pg/s over {dt/60:.1f} min   ({(d1-d0)/dt*60:.0f} docs/min)")
    gb = b1 / 1e9
    proj = gb / (p1 / TOT_PAGES) / 1000 if p1 else 0
    print(f"TOTAL     {q1:>9,} parcels {100*q1/TOT_PARCELS:>6.2f}%   of {TOT_PARCELS:,}")
    print(f"          {d1:>9,} docs    {100*d1/TOT_DOCS:>6.2f}%   of {TOT_DOCS:,}")
    print(f"          {p1:>9,} pages   {100*p1/TOT_PAGES:>6.2f}%   of {TOT_PAGES:,}")
    print(f"          {gb:>9,.1f} GB stored          (corpus projects to ~{proj:.1f} TB)")
    print(f"GAINED    +{q1-q0:,} parcels · +{d1-d0:,} docs · +{p1-p0:,} pages · +{(b1-b0)/1e9:.2f} GB")
    if (p1 - p0) > 0:
        days = (TOT_PAGES - p1) / ((p1 - p0) / dt) / 86400
        print(f"ETA       {days:.0f} days at this rate, 24/7")
    print(f"PROCS     driver {st['overnight.py']} · workers {st['acquire_async.py']} · watchdog {st['watchdog.py']}")
    print(f"RAM       {vm.percent:.0f}% used · {vm.available/1e9:.1f} GB free"
          + ("   ⚠ THRASH RISK" if vm.available < 1.5e9 else ""))
    print(f"REFUSALS  {'⚠ STOPPED: ' + stop.read_text(encoding='utf-8') if stop.exists() else 'none'}")
    if last:
        print(f"DRIVER    {last[-1].strip()}")


if __name__ == "__main__":
    main()
