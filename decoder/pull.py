"""START, PAUSE, RESUME AND INSPECT THE ACQUISITION. One control surface.

    ACRIS_CORPUS_ROOT=D:/acris python pull.py --status
    ACRIS_CORPUS_ROOT=D:/acris python pull.py --pause
    ACRIS_CORPUS_ROOT=D:/acris python pull.py --resume

⚠ WHY A PAUSE IS SAFE AT ANY MOMENT. The ledger records a document only once every page
of it has landed, so stopping mid-document loses that document's pages and nothing else —
the next run re-fetches it from page 1. There is no partial state to corrupt and no
cleanup to perform. Close the laptop if you have to.

⚠ PAUSE IS THE SAME FLAG AS A REFUSAL, DELIBERATELY. `_STOP` means "do not fetch", and
the watchdog must not restart the driver in either case. The file records WHY, so a
morning reader can tell an outage from a decision.

⚠ RESUME COSTS NOTHING AND SKIPS NOTHING. Parcels already whole are skipped by reading
their manifests; documents already fetched are skipped by the ledger. Restarting is a
few seconds of bookkeeping, not lost work.
"""
from __future__ import annotations

import argparse, datetime, json, os, subprocess, sqlite3, sys, pathlib, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import corpus_paths as CP

# ⚠ --lo 1, NOT 8. The old floor excluded 357,749 parcels (28.6% of every parcel in the
# corpus) to save a little per-parcel overhead, and carried no comment saying so — the
# exclusion was invisible in every log line it ever printed. A parcel with 3 documents is
# still a parcel with 3 documents.
# ⚠ --hi 300 IS LOAD-BEARING and must not simply be removed. The pool is ordered
# n_docs DESC, so dropping it makes the walk OPEN with the 80,234-document parcel, and
# --docs-cap truncates anything above it — a half-built parcel puts the hole in the
# middle of an ordered chronology.
#
# ⚠ THE 640 PARCELS ABOVE 300 NEED NO NEW SCRIPT — overnight.py already takes the band.
# Run them as their own pass, batch 1 so one giant cannot starve four slots, and a cap
# that clears the largest parcel in the corpus (80,234 documents, bbl 1010090037):
#
#   ACRIS_CORPUS_ROOT=D:/acris python overnight.py --procs 4 --conc 20 --batch 1 --docs-cap 100000 --pool 1000 --boro "" --lo 301 --hi 999999 --until 23:59
#
# ⚠ 17 of those exceed the 6000 cap used by the main walk, holding 479,525 links — more
# than half the whole tail. Running them under the main config would half-build every one.
# ⚠ 4 PROCS IS A MEMORY LIMIT, NOT A THROUGHPUT CHOICE. Tried 8 x 10 on 2026-08-18
# (same 80 connections, more slots, to absorb the 17x pages-per-parcel spread). Each
# worker costs ~163 MB, so 8 workers took the box from 4.6 GB to 0.71 GB free — below
# the 0.8 GB point CLAUDE.md records as where this machine thrashes, with Windows
# MemCompression already running to cope. Reverted after 5 minutes.
# ⚠ RETESTED 09:19-09:34 once headroom was freed: 8x10 measured 62.9 pg/s against a
# 75.0 baseline, and spent 2 minutes under the 1.0 GB line. The window caught the
# revert so the true rate is >62.9 — but it had to beat 75.0 and no reading gets it
# there. With 2026-08-17's independent 8x10 ~90 vs 4x20 93.8, TWO tests now agree.
# ⚠ QUESTION CLOSED — do not open it a third time.
# ⚠ THE MEASUREMENT TRAP, if anyone does: at conc 10 each process finishes its batch
# later, so ledger commits are RARER under 8x10 and ANY fixed window is biased
# against it — it showed '0 parcels done' at 6 min. And summing worker write_bytes
# as a commit-independent workaround returns NEGATIVE rates when workers are
# replaced mid-window (measured -183 pg/s). Neither method is trustworthy here.
# ⚠ CHECK THE MEMORY BUDGET BEFORE RAISING --procs. 16 GB total, and Claude + a browser
# routinely hold 2-3 GB of it; the headroom for workers is ~1.5 GB, i.e. about 8
# processes with nothing else running and 4 in practice. Connections are the ACRIS
# limit; PROCESSES are this laptop's limit. They are different ceilings.
DEFAULT = ["--procs", "4", "--conc", "20", "--batch", "5", "--docs-cap", "6000",
           "--pool", "40000", "--boro", "", "--lo", "1", "--hi", "300"]


def procs():
    import psutil
    out = {}
    for p in psutil.process_iter(["name", "cmdline"]):
        if p.info.get("name") != "python.exe":
            continue
        cl = " ".join(str(x) for x in (p.info.get("cmdline") or []))
        if "process_iter" in cl:            # ⚠ never count the probe itself
            continue
        for tag in ("overnight.py", "acquire_async.py", "watchdog.py"):
            if tag in cl:
                out.setdefault(tag, []).append(p)
    return out


RATE_FLOOR_MIN = 15          # ⚠ never quote a rate on a shorter window — see rate()


def rate(c, window_min=30):
    """pages/s over the last `window_min`, or None with a reason.

    ⚠ THE WINDOW ENDS AT max(at), NOT AT NOW — and that is what makes this honest.
    The ledger commits once per process (~4 lumps/minute), so measuring "pages in the
    last 30 minutes of wall clock" reads near-zero between flushes and enormous across
    one. The SAME healthy run read 29.5 / 41.8 / 75.0 / 89.4 / 110.5 pg/s on 2026-08-18
    from window placement alone. But `at` is stamped PER DOCUMENT AT FETCH TIME, not at
    commit time, so the timestamps inside the ledger are accurate even though its growth
    is lumpy. Anchoring to max(at) measures the fetching, not the committing.

    ⚠ STILL REFUSES UNDER RATE_FLOOR_MIN. A short window can sit entirely inside one
    parcel's burst. Returning None is the point: no number beats a wrong one."""
    row = c.execute("SELECT MAX(at) FROM doc WHERE status='ok'").fetchone()
    if not row or not row[0]:
        return None, "no ok rows"
    end = datetime.datetime.fromisoformat(row[0])
    start = end - datetime.timedelta(minutes=window_min)
    pg, n, lo = c.execute(
        "SELECT COALESCE(SUM(got),0), COUNT(*), MIN(at) FROM doc "
        "WHERE status='ok' AND at > ?", (start.isoformat(timespec="seconds"),)).fetchone()
    if not n:
        return None, "no documents in window"
    span = (end - datetime.datetime.fromisoformat(lo)).total_seconds()
    if span < RATE_FLOOR_MIN * 60:
        return None, (f"only {span/60:.1f} min of data in window — under the "
                      f"{RATE_FLOOR_MIN} min floor, refusing to quote a rate")
    return (pg / span, f"{pg:,} pages over {span/60:.1f} min ending {end:%H:%M}")


def pct(a, b):
    return f"{100.0*a/b:6.3f}%" if b else "    n/a"


def status():
    CP.ensure()
    ps = procs()
    for tag in ("overnight.py", "acquire_async.py", "watchdog.py"):
        print(f"  {tag:<18} {len(ps.get(tag, []))} running")
    print(f"  _STOP present      {CP.STOP.exists()}"
          + (f"  ({CP.STOP.read_text(encoding='utf-8').strip()})" if CP.STOP.exists() else ""))

    import denominators
    d = denominators.load()
    if not d:
        print("  ⚠ NO DENOMINATORS CACHE — run: python denominators.py --build")
        print("    (every % below would otherwise be against a number nobody chose)")

    if not CP.LEDGER.exists():
        return
    c = sqlite3.connect(f"file:{CP.LEDGER}?mode=ro", uri=True)

    print()
    print("  LEDGER")
    for s, n, pg in c.execute("SELECT status, COUNT(*), COALESCE(SUM(got),0) "
                              "FROM doc GROUP BY 1 ORDER BY 2 DESC"):
        print(f"    {s:<8} {n:>10,} documents  {pg:>12,} pages")
    ok_n, ok_pg = c.execute("SELECT COUNT(*), COALESCE(SUM(got),0) FROM doc "
                            "WHERE status='ok'").fetchone()

    # ⚠ THREE AXES, BECAUSE THEY DISAGREE AND THE DISAGREEMENT IS THE INFORMATION.
    # Documents and pages diverge (a 300-page mortgage is one document); parcels diverge
    # from both (a parcel is complete only when its WHOLE chronology has landed, so it
    # trails documents badly early on). Reporting one number hides which is the constraint.
    if d:
        print()
        print("  PROGRESS — every rate against its own denominator")
        print(f"    documents  {ok_n:>10,} / {d['acris_keyed']:>11,} parcel-keyed ACRIS"
              f"   {pct(ok_n, d['acris_keyed'])}")
        print(f"               {ok_n:>10,} / {d['acris_spec']:>11,} ACRIS in spec"
              f"          {pct(ok_n, d['acris_spec'])}")
        print(f"    pages      {ok_pg:>10,} / {d['pages_estimate']:>11,} ESTIMATE"
              f"             {pct(ok_pg, d['pages_estimate'])}")
        pc = parcels_complete_cached()
        if pc is None:
            print("    parcels    (not counted — run: python pull.py --recount-parcels)")
        else:
            n_done, when = pc
            print(f"    parcels    {n_done:>10,} / {d['parcels_with_acris']:>11,} holding"
                  f" an ACRIS doc  {pct(n_done, d['parcels_with_acris'])}")
            print(f"               ⚠ parcel count cached {when} — recount to refresh")
        print(f"    ⚠ {d['acris_unkeyed']:,} ACRIS documents are NOT parcel-keyed and "
              f"cannot be reached by this walk at all")

    r, why = rate(c)
    print()
    if r is None:
        print(f"  RATE       none quoted — {why}")
    else:
        print(f"  RATE       {r:.1f} pg/s   ({why})")
        if d:
            left = max(0, d["pages_estimate"] - ok_pg)
            print(f"             {left/r/86400:.1f} days of 24/7 fetching remain "
                  f"at this rate ({left:,} pages)")

    # ⚠ THE LAG SPLIT IS PART OF STATUS, NOT A SEPARATE AUDIT. An `empty` row inside the
    # image lag window is NOT proof of an image-less document — it is a document whose
    # scan may still attach (image_policy.TERMINAL_DAYS). Showing the split here is what
    # stops those being read as settled. See parcel_folder.empty_ids().
    try:
        import parcel_folder
        term, pend = parcel_folder.empty_ids()
        print()
        print(f"  IMAGE LAG  {len(term):,} terminal (index is the record) · "
              f"{len(pend):,} PENDING re-ask (inside "
              f"{__import__('image_policy').TERMINAL_DAYS}-day window)")
        if pend:
            print(f"             ⚠ those {len(pend)} must not be written off — their "
                  f"parcels stay outstanding until the window closes")
    except Exception as e:
        print(f"  IMAGE LAG  unavailable ({type(e).__name__}: {e})")
    c.close()

    log = CP.log("overnight")
    if log.exists():
        last = [l for l in log.read_text(encoding="utf-8", errors="replace").splitlines()
                if "pg/s" in l]
        if last:
            print()
            print(f"  last log line      {last[-1].strip()}")


PARCEL_CACHE = CP.STATE / "parcels_complete.json"


def parcels_complete_cached():
    if not PARCEL_CACHE.exists():
        return None
    try:
        j = json.loads(PARCEL_CACHE.read_text(encoding="utf-8"))
        return j["complete"], j["at"]
    except (ValueError, KeyError):
        return None


def recount_parcels():
    """⚠ EXPENSIVE (reads every _INDEX.md — ~6 min on the One Touch), hence cached and
    never run from --status. A parcel is complete only when NOTHING is outstanding, and
    outstanding is TWO markers: `not acquired` and `pending scan`. Testing only the first
    retired parcels whose scan had not attached yet — see overnight.py."""
    CP.ensure()
    OUTSTANDING = ("| not acquired |", "| pending scan |")
    done = seen = 0
    t = time.time()
    for f in CP.BYPARCEL.rglob("_INDEX.md"):
        seen += 1
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not any(m in txt for m in OUTSTANDING):
            done += 1
    at = datetime.datetime.now().isoformat(timespec="seconds")
    PARCEL_CACHE.write_text(json.dumps({"complete": done, "manifests": seen, "at": at}),
                            encoding="utf-8")
    print(f"  {done:,} complete of {seen:,} manifests on disk  ({time.time()-t:.0f}s)")


def pause(why):
    CP.ensure()
    CP.STOP.write_text(f"paused by hand {datetime.datetime.now():%Y-%m-%d %H:%M} — {why}",
                       encoding="utf-8")
    killed = 0
    for tag, ps in procs().items():
        for p in ps:
            try:
                p.kill(); killed += 1
            except Exception:
                pass
    print(f"  paused · {killed} processes stopped · _STOP written")
    print("  ⚠ nothing to clean up: a half-fetched document is simply re-fetched next run")


def resume(until):
    CP.ensure()
    if CP.STOP.exists():
        CP.STOP.unlink()
    for f in (CP.pid_file("overnight"), CP.pid_file("watchdog")):
        if f.exists():
            f.unlink()
    env = dict(os.environ, ACRIS_CORPUS_ROOT=str(CP.ROOT))
    for script, extra in (("overnight.py", DEFAULT + ["--until", until]),
                          ("watchdog.py", ["--until", until, "--every", "180",
                                           "--args", " ".join(DEFAULT)])):
        with open(CP.log(pathlib.Path(script).stem + "_run"), "a", encoding="utf-8") as lg:
            subprocess.Popen([sys.executable, "-u", str(HERE / script)] + extra,
                             stdout=lg, stderr=lg, env=env, cwd=str(HERE))
    print(f"  resumed until {until} · skips whole parcels and fetched documents automatically")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--recount-parcels", action="store_true",
                    help="re-walk every _INDEX.md and cache the complete-parcel count "
                         "(~6 min; --status reads the cache)")
    ap.add_argument("--pause", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--why", default="not stated")
    ap.add_argument("--until", default="23:00")
    a = ap.parse_args()
    if a.pause:
        pause(a.why)
    elif a.resume:
        resume(a.until)
    elif a.recount_parcels:
        recount_parcels()
    else:
        status()


if __name__ == "__main__":
    main()
