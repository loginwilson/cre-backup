"""THE LIVE EDGE IN ~30 REQUESTS — gallop, bisect, confirm. Never walk.

    ACRIS_CORPUS_ROOT=D:/acris python crfn_monitor.py

Answers one question: what is the highest CRFN ACRIS has issued right now?
From that, the delta is ARITHMETIC — no sweep, no index traversal, no walk.

    live_edge - highest_landed  =  documents outstanding

⚠ WHY NOT WALK. live_crfn.py --walk asks one request per number and costs
1,550/day at steady state. The edge is a boundary, not a corpus: galloping to it
and bisecting finds it in O(log n) — ~30 requests however far it has moved.

⚠ A BLANK IS NOT THE EDGE. The counter has genuine holes (11 measured in July,
all verified unissued). A single blank could be a hole rather than the end, so
the edge is only accepted when the candidate RESOLVES and CONFIRM_BLANKS
consecutive numbers above it do not. Terminating on the first blank is the same
mistake as terminating on a short page - a derived signal, not the server's.

⚠ CONTROL FIRST. A malformed request returns the same empty page as a genuine
absence. If the known-good watermark does not resolve, this refuses to report
anything at all. That guard already caught a probe that reported all 11 July
holes AND the control as absent.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import live_crfn as LC
import live_delta as LD

QUEUE = HERE / "_live_delta_queue.jsonl"
STATE = HERE / "_crfn_edge.json"
CONFIRM_BLANKS = 8


def landed_watermark():
    mx = 0
    with QUEUE.open(encoding="utf-8") as f:
        for l in f:
            c = str(json.loads(l).get("crfn") or "").strip()
            if c.isdigit():
                mx = max(mx, int(c))
    return mx


def main():
    calls = [0]

    def resolves(s, n):
        calls[0] += 1
        return LC.parse_detail(LC.detail_html(s, n)) is not None

    wm = landed_watermark()
    print(f"CRFN LIVE EDGE\n  highest landed  {wm}")
    s = LD.Session().open().open_crfn()

    if not resolves(s, wm):
        sys.exit(f"  ⚠ CONTROL {wm} did not resolve — probe unproven, reporting "
                 f"NOTHING. A malformed request looks exactly like an empty one.")
    print(f"  control {wm} resolves — probe OK")

    # ── GALLOP: double until a number does not resolve ────────────────────
    lo, step = wm, 1
    while True:
        probe = wm + step
        if resolves(s, probe):
            lo = probe
            step *= 2
            print(f"    gallop +{step//2:<6} {probe} resolves")
        else:
            hi = probe
            print(f"    gallop +{step:<6} {probe} blank -> edge in ({lo}, {hi})")
            break
        if step > 1 << 20:
            sys.exit("  ⚠ gallop ran away — refusing to continue")

    # ── BISECT: narrow to the last resolving number ───────────────────────
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if resolves(s, mid):
            lo = mid
        else:
            hi = mid
    print(f"  bisected candidate edge: {lo}")

    # ⚠ CONFIRM — a hole would bisect to a false edge. Require consecutive
    # blanks above the candidate before believing it.
    blanks = sum(0 if resolves(s, lo + k) else 1
                 for k in range(1, CONFIRM_BLANKS + 1))
    ok = blanks == CONFIRM_BLANKS
    print(f"  confirm: {blanks}/{CONFIRM_BLANKS} consecutive blanks above -> "
          f"{'EDGE CONFIRMED' if ok else '⚠ NOT THE EDGE (a hole, keep going)'}")

    span = lo - wm
    print(f"\n  ── THE DELTA ──")
    print(f"  highest landed crfn   {wm:,}")
    print(f"  live edge crfn        {lo:,}")
    print(f"  span outstanding      {span:,}   (issued numbers not yet held)")
    print(f"  probe cost            {calls[0]} requests")
    STATE.write_text(json.dumps(
        {"watermark": wm, "edge": lo, "span": span, "confirmed": ok,
         "requests": calls[0], "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
        indent=1), encoding="utf-8")
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
