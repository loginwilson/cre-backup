"""WATCHDOG FOR A LONG VLM RUN. Detects a stall; does not merely report progress.

    python watch.py qwen35-2b --expect 26 --stall 420

⚠ "STILL RUNNING" AND "STALLED" LOOK IDENTICAL FROM THE OUTSIDE. This run has
already wedged twice: llama-server accepted a request, never answered, and the
client's socket timeout could not fire because the connection stayed open. From
the file system both states are the same - no new output. The difference is
whether the SERVER is still decoding tokens, which only its own log knows.

So this checks three independent things and prints them on one line:
  1. pages written        - progress
  2. seconds since write  - the stall clock
  3. server token counter - whether the GPU is doing anything at all

A page can legitimately take minutes at 22 tok/s. A page that is silent AND
whose server token counter has not moved is wedged, and that is worth waking
someone for.

⚠ IT NEVER KILLS ANYTHING. A watchdog that restarts a run destroys the evidence
of why it stalled - and the wedge is the thing being diagnosed. It reports.
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
LOG = pathlib.Path(r"C:\Users\smile\AppData\Local\Temp\claude"
                   r"\C--Users-smile\7c5a3ccb-a88e-40cd-a587-cc575cf7a400"
                   r"\scratchpad\llama.log")


def decoded(log):
    """Total tokens the server has decoded, from its own timing lines.
    A number that stops moving is the only proof of a wedge."""
    if not log.exists():
        return None
    try:
        tail = log.read_bytes()[-200_000:].decode("utf-8", "replace")
    except Exception:
        return None
    m = re.findall(r"n_decoded\s*=\s*(\d+)", tail)
    tasks = re.findall(r"task (\d+) \| processing task", tail)
    return (int(m[-1]) if m else 0, int(tasks[-1]) if tasks else -1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--expect", type=int, default=26)
    ap.add_argument("--stall", type=int, default=420,
                    help="seconds of no page AND no tokens before STALL")
    ap.add_argument("--every", type=int, default=45)
    a = ap.parse_args()

    out = HERE / "out" / a.tag
    last_n, last_change, last_tok, tok_change = -1, time.time(), None, time.time()
    t0 = time.time()
    while True:
        fs = [f for f in out.rglob("*.txt")] if out.exists() else []
        n = len(fs)
        newest = max((f.stat().st_mtime for f in fs), default=0)
        if n != last_n:
            last_n, last_change = n, time.time()
        d = decoded(LOG)
        if d and d != last_tok:
            last_tok, tok_change = d, time.time()

        quiet = time.time() - (newest or t0)
        tok_quiet = time.time() - tok_change
        zero = sum(1 for f in fs if f.stat().st_size == 0)
        state = "ok"
        if quiet > a.stall and tok_quiet > a.stall:
            state = "STALLED"
        elif quiet > a.stall:
            state = "slow-page(server still decoding)"

        print(f"  [{time.strftime('%H:%M:%S')}] {n:>2}/{a.expect}  "
              f"quiet {quiet:>5.0f}s  server_tokens {str(d):<12} "
              f"idle {tok_quiet:>5.0f}s  zero-byte {zero}  {state}", flush=True)

        if n >= a.expect:
            print(f"  DONE {n}/{a.expect} in {(time.time()-t0)/60:.1f} min")
            return
        if state == "STALLED":
            print(f"  ⚠ STALLED: no page for {quiet:.0f}s and the server has "
                  f"decoded no tokens for {tok_quiet:.0f}s. Not killed - "
                  f"restart llama-server before any diagnostic, because a held "
                  f"slot makes every later test time out.", flush=True)
        time.sleep(a.every)


if __name__ == "__main__":
    main()
