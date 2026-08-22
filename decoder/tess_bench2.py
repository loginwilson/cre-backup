"""RAISING THE 18,000 — without adding a second pass.

⚠ THE PHANTOM THAT ALMOST GOT REPORTED. `--oem 0` measured 346,405 pg/hr in the
previous benchmark, a 19x win. It was Tesseract failing instantly: Tesseract 5
ships LSTM-only traineddata, the legacy engine had no model to load, and it
returned 0 characters on every page. The only reason it was not written down as
a breakthrough is that RECALL SITS IN THE SAME TABLE AS SPEED. Any arm here
that gets faster without keeping 25/25 is doing the same thing.

WHAT IS BEING TESTED, and why each might matter

  BATCHING       every page currently spawns a fresh tesseract.exe. Windows
                 process creation is ~20-40 ms; at ~5 pages/sec that is a real
                 slice. Tesseract accepts a FILE LIST and does many pages in
                 one process, so the spawn is paid once per batch.

  NO DICTIONARY  Tesseract loads system and frequency word lists and uses them
                 to correct its own output. That is effort spent making text
                 read nicely for a human. The consumer here is a phrase
                 matcher, which wants raw characters — and legal boilerplate is
                 full of words no English dictionary helps with anyway.

  OVERSUBSCRIBE  8 procs on 8 cores leaves cores idle during file I/O and
                 process teardown. 12 and 16 test whether there is slack.

⚠ THE ARMS ARE SCORED ON THE SAME 25 KNOWN FACTS as every previous run, and any
arm that loses even one is reported as a loss regardless of its speed. A single
missed claim is a fact that silently never existed.
"""
import concurrent.futures as cf
import os
import pathlib
import statistics
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import trigger_probe as TP

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TIFS = sorted(pathlib.Path("devr_pages/2014093000267001").glob("*.tif"))
SCRATCH = pathlib.Path(os.environ["TMP"]) / "tessb2"
SCRATCH.mkdir(parents=True, exist_ok=True)

NODICT = ["-c", "load_system_dawg=0", "-c", "load_freq_dawg=0",
          "-c", "load_punc_dawg=0", "-c", "load_number_dawg=0",
          "-c", "load_unambig_dawg=0", "-c", "load_bigram_dawg=0"]
QUIET = ["-c", "tessedit_do_invert=0"]


def _env():
    return {**os.environ, "OMP_THREAD_LIMIT": "1"}


def single(args):
    """One page, one process — the current approach."""
    t, extra = args
    r = subprocess.run([TESS, str(t), "stdout", "--psm", "6"] + QUIET + extra,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=_env())
    return {int(t.stem[1:]): TP.norm(r.stdout or "")}


def batch(args):
    """⚠ MANY PAGES, ONE PROCESS. Tesseract separates pages in its output with
    a form feed (\\f), so the mapping back to page numbers survives — but only
    if the list order is preserved, which is why the split is zipped against
    the same list that was written."""
    tifs, extra = args
    lst = SCRATCH / f"l{os.getpid()}_{id(tifs)}.txt"
    lst.write_text("\n".join(str(t) for t in tifs), encoding="utf-8")
    r = subprocess.run([TESS, str(lst), "stdout", "--psm", "6"] + QUIET + extra,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=_env())
    parts = (r.stdout or "").split("\f")
    out = {}
    for t, p in zip(tifs, parts):
        out[int(t.stem[1:])] = TP.norm(p)
    return out


def recall(text):
    h = m = 0
    miss = []
    for pg, slots in TP.TRUTH.items():
        for s in slots:
            if any(TP.norm(p) in text.get(pg, "") for p in TP.TRIGGERS.get(s, [])):
                h += 1
            else:
                m += 1
                miss.append(f"p{pg}:{s}")
    return h, h + m, miss


def arm(label, mode, workers, extra=(), per=None):
    extra = list(extra)
    t0 = time.time()
    out = {}
    if mode == "single":
        jobs = [(t, extra) for t in TIFS]
        with cf.ThreadPoolExecutor(workers) as ex:
            for d in ex.map(single, jobs):
                out.update(d)
    else:
        per = per or max(1, len(TIFS) // workers)
        chunks = [TIFS[i:i + per] for i in range(0, len(TIFS), per)]
        jobs = [(c, extra) for c in chunks]
        with cf.ThreadPoolExecutor(workers) as ex:
            for d in ex.map(batch, jobs):
                out.update(d)
    el = time.time() - t0
    h, n, miss = recall(out)
    rate = len(TIFS) / el * 3600
    ch = statistics.mean(len(v) for v in out.values()) if out else 0
    flag = "" if h == n else "   <-- LOST FACTS"
    print(f"  {label:<38}{rate:>10,.0f} pg/hr{h:>5}/{n}{ch:>8.0f} ch{flag}", flush=True)
    if miss:
        print(f"      MISSED: {', '.join(miss[:6])}{' ...' if len(miss) > 6 else ''}")
    return rate, h == n


def main():
    print(f"{len(TIFS)} pages · every arm scored on the same 25 known facts\n")
    print(f"  {'arm':<38}{'speed':>16}{'recall':>7}{'text':>12}")
    print("  " + "-" * 76)
    res = {}
    res["baseline 8x1page"] = arm("psm6, 8 procs, 1 page each", "single", 8)
    res["nodict 8x1page"] = arm("psm6, 8 procs, NO DICTIONARIES", "single", 8, NODICT)
    res["batch 8"] = arm("psm6, 8 procs, BATCHED", "batchy", 8)
    res["batch 8 nodict"] = arm("psm6, 8 procs, BATCHED + no dict", "batchy", 8, NODICT)
    res["batch 12 nodict"] = arm("psm6, 12 procs, BATCHED + no dict", "batchy", 12, NODICT)
    res["batch 16 nodict"] = arm("psm6, 16 procs, BATCHED + no dict", "batchy", 16, NODICT)

    base = res["baseline 8x1page"][0]
    print("\n  vs current best (8 procs, 1 page per process):")
    for k, (r, ok) in res.items():
        print(f"    {k:<22}{r/base:>6.2f}x{'' if ok else '   INVALID - lost facts'}")
    good = [(r, k) for k, (r, ok) in res.items() if ok]
    if good:
        best = max(good)
        print(f"\n  FASTEST AT FULL RECALL: {best[1]}  ({best[0]:,.0f} pg/hr)")
        print(f"    42,310 DEVR pages       -> {42310/best[0]*60:.0f} min")
        print(f"    1.4M pages (rare types) -> {1_400_000/best[0]:.0f} h")
        print(f"    140.2M pages (corpus)   -> {140_200_000/best[0]/24:.0f} days")


if __name__ == "__main__":
    main()
