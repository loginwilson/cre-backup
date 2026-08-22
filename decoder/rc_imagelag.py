"""HOW LONG AFTER RECORDING DOES A RICHMOND IMAGE APPEAR? — measure, don't schedule.

    ACRIS_CORPUS_ROOT=D:/acris python rc_imagelag.py --recent      last ~90 days
    ACRIS_CORPUS_ROOT=D:/acris python rc_imagelag.py --era         1998..now, yearly

WHY THIS EXISTS. `pending` (scan not attached YET) and `structurally imageless`
(no scan will ever come) are INDISTINGUISHABLE ON ANY SINGLE READ - both show
"No Image Available At This Time". Without a measured lag curve there is no
terminal state, so a pending queue retries forever and an imageless document
looks like a permanent hole in the specification. The curve supplies the only
honest boundary: the age past which "still pending" stops meaning "wait".

METHOD. For each target date: open a ONE-DAY date-range window, take a RANDOM
sample of its documents (never the first K - the page is ordered by instrument,
which is submission-batch order, so the head of the list is a biased subset),
re-POST each through the window for its detail page, and read the published
marker. No image is ever requested: presence is stated on the detail page.

⚠ THE DETAIL PAGE IS SESSION-GUARDED - it must be re-POSTed through the SAME
window that produced the row. A GET returns a 2,180-byte UNAUTHORIZED shell at
HTTP 200 that parses to an empty document. rc_source raises on that shape.

⚠ EVERY RATE CARRIES ITS DENOMINATOR. A day with 3 documents sampled is not
evidence about that day; the table prints n for every row and refuses to
summarise a bucket with fewer than MIN_N observations.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import re
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import rc_source as RC
import rc_sync as RS

OUT = HERE / "_rc_imagelag.jsonl"
K = 8                      # documents sampled per target date
MIN_N = 5                  # below this a bucket prints but is not summarised

_ROW = re.compile(
    r'<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*<td[^>]*>([^<]*)</td>\s*'
    r'<td[^>]*>([^<]*)</td>.*?name="ViewDetailsButton" value="(\d+)"[^>]*>\s*'
    r'(\d{4,9})\s*</button>', re.S)


def rows_of(html):
    return [{"book": m.group(1).strip(), "page": m.group(2).strip(),
             "recorded": m.group(3).strip(), "doc_type": m.group(4).strip(),
             "internal_id": m.group(5), "instrument": m.group(6)}
            for m in _ROW.finditer(html)]


def sample_date(day, k=K):
    """-> list of observations for one calendar day, or [] if nothing recorded."""
    ds = day.strftime("%m/%d/%Y")
    w = RS.Window(ds, ds)
    rows = rows_of(w.html)
    if not rows:
        return []
    picked = random.sample(rows, min(k, len(rows)))
    obs = []
    for r in picked:
        try:
            d = w.detail(r["internal_id"])
        except RC.Unauthorized:
            raise
        except Exception as e:
            obs.append({**r, "image_state": "ERROR:" + type(e).__name__})
            continue
        obs.append({**r, "image_state": (d or {}).get("image_state", "unknown"),
                    "day_docs": len(rows)})
    return obs


def report(all_obs, today):
    buckets = {}
    for o in all_obs:
        if o["image_state"].startswith("ERROR"):
            continue
        try:
            rec = dt.datetime.strptime(o["recorded"], "%m/%d/%Y").date()
        except ValueError:
            continue
        age = (today - rec).days
        b = buckets.setdefault(age, {"present": 0, "pending": 0, "unknown": 0})
        b[o["image_state"]] = b.get(o["image_state"], 0) + 1
    print(f"\n  {'age(d)':>7} {'n':>4} {'present':>8} {'pending':>8}  {'% imaged':>9}")
    for age in sorted(buckets):
        b = buckets[age]
        n = b["present"] + b["pending"] + b["unknown"]
        pct = f"{100*b['present']/n:.0f}%" if n >= MIN_N else f"n<{MIN_N}"
        print(f"  {age:>7} {n:>4} {b['present']:>8} {b['pending']:>8}  {pct:>9}")
    return buckets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recent", action="store_true")
    ap.add_argument("--era", action="store_true")
    ap.add_argument("--k", type=int, default=K)
    a = ap.parse_args()
    today = dt.date.today()

    if a.recent:
        targets = [today - dt.timedelta(days=d)
                   for d in (0, 1, 2, 3, 4, 5, 6, 7, 9, 11, 14, 18, 21, 30, 45, 60, 90)]
    elif a.era:
        targets = [dt.date(y, 6, 15) for y in range(1998, today.year + 1, 2)]
    else:
        sys.exit("  pass --recent or --era")

    all_obs = []
    t0 = time.time()
    with OUT.open("a", encoding="utf-8") as f:
        for i, day in enumerate(targets, 1):
            try:
                # ⚠ AN EMPTY DAY IS A CALENDAR FACT, NOT A FINDING. June 15 lands on a
                # weekend in ~2 years of 7 and nothing records; a target that returns []
                # silently costs a whole era from the sample. Walk forward to the next
                # day that actually recorded something.
                obs = []
                for slip in range(5):
                    obs = sample_date(day + dt.timedelta(days=slip), a.k)
                    if obs:
                        if slip:
                            print(f"    ({day} empty - used +{slip}d)")
                        break
            except RC.Unauthorized as e:
                print(f"  UNAUTHORIZED at {day} - {e}"); break
            except RC.Refused:
                print(f"  REFUSED at {day} - STOPPING, no retry."); break
            except Exception as e:
                print(f"  {day}  {type(e).__name__} - skipped"); continue
            for o in obs:
                o["observed"] = today.isoformat()
                f.write(json.dumps(o) + "\n")
            f.flush()
            all_obs += obs
            pres = sum(o["image_state"] == "present" for o in obs)
            pend = sum(o["image_state"] == "pending" for o in obs)
            print(f"  {day}  age {(today-day).days:>3}d  sampled {len(obs):>2}"
                  f"  present {pres:>2}  pending {pend:>2}"
                  f"   [{i}/{len(targets)}]")
    report(all_obs, today)
    print(f"\n  {len(all_obs):,} observations · {(time.time()-t0)/60:.1f} min -> {OUT}")


if __name__ == "__main__":
    main()
