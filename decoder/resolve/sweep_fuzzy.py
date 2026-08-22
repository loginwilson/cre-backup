"""CALIBRATE THE SUB-BLOCK ACCEPTANCE GATE AGAINST THE ANSWER KEYS.

    python sweep_fuzzy.py
    python sweep_fuzzy.py --values 1.0,0.95,0.9,0.85,0.8,0.7,0.6

⚠ THE OBJECTIVE IS NOT "ACCEPT MORE". Accepting more text cannot inflate this
score - a wrong reading does not match an artifact, so it buys nothing. What a
too-low gate DOES buy is damage to the ceiling: pair two tokens that were never
the same word and the correct reading stops being offered to escalation at all.
So the gate is right where `accepted` has risen as far as it can WITHOUT
`ceiling` falling. Watch both columns; the second one is the safety rail.

⚠ AND ACCEPTED CAN NEVER EXCEED CEILING. If a sweep ever prints one, the two
are not measuring the same artifact set and the run is void, not interesting.
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

DOCS = [("FT_1680008647768", "film"), ("BK_6730047100023", "book"),
        ("2015022400608001", "digital")]
OCR = {"2015022400608001": "ppbox", "FT_1680008647768": "ppv6",
       "BK_6730047100023": "ppv6"}


def run(cmd):
    return subprocess.run([sys.executable] + cmd, cwd=HERE,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--values", default="1.0,0.95,0.9,0.85,0.8,0.75,0.7,0.6")
    ap.add_argument("--tier", default="CRITICAL")
    a = ap.parse_args()
    vals = [float(x) for x in a.values.split(",")]

    print(f"  sweeping FUZZY over {vals}   tier={a.tier}\n")
    print(f"  {'fuzzy':>6} | {'film acc':>8} {'film ceil':>9} | "
          f"{'book acc':>8} {'book ceil':>9} | {'digi acc':>8} {'digi ceil':>9} | "
          f"{'WTD acc':>8} {'WTD ceil':>8}")
    print("  " + "-" * 96)
    rows = []
    for v in vals:
        for doc, _ in DOCS:
            r = run(["fuse.py", "--doc", doc, "--vlm", "q35-fair",
                     "--ocr", OCR[doc], "--fuzzy", str(v)])
            if r.returncode != 0:
                print(f"  fuse failed at fuzzy={v} on {doc}:\n{r.stderr[-400:]}")
                return
        r = run(["score_fused.py", "--tier", a.tier, "--json"])
        if r.returncode != 0:
            print(f"  score failed at fuzzy={v}: {r.stderr[-400:]}")
            return
        j = json.loads(r.stdout.strip().splitlines()[-1])
        d, w = j["docs"], j["weighted"]
        acc = {k: v2["accepted"] for k, v2 in d.items()}
        ceil = {k: v2["ceiling"] for k, v2 in d.items()}
        wa, wc = w["accepted"], w["ceiling"]
        print(f"  {v:>6} | {acc.get('film',0):>7.1%} {ceil.get('film',0):>9.1%} | "
              f"{acc.get('book',0):>7.1%} {ceil.get('book',0):>9.1%} | "
              f"{acc.get('digital',0):>7.1%} {ceil.get('digital',0):>9.1%} | "
              f"{wa:>7.1%} {wc:>8.1%}", flush=True)
        rows.append({"fuzzy": v, "accepted": acc, "ceiling": ceil,
                     "weighted_accepted": wa, "weighted_ceiling": wc})
    (HERE / "_sweep_fuzzy.json").write_text(json.dumps(rows, indent=1),
                                            encoding="utf-8")
    print(f"\n  -> {HERE / '_sweep_fuzzy.json'}")
    print("  Pick the LOWEST fuzzy at which ceiling has not fallen.")


if __name__ == "__main__":
    main()
