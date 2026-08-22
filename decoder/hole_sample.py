"""WHY THE SPECIFICATION DOES NOT MATCH LIVE STATE — measure, do not estimate.

Takes the CRFN numbers inside our own live window that we do NOT hold, samples
them evenly, looks each up, and classifies what it actually is:

    REAL+PARCEL  a real-property document with parcels -> WE MISSED IT
    PERSONAL     no parcel block -> UCC / federal lien, a DIFFERENT INDEX
    UNISSUED     resolves to nothing -> genuinely never issued

⚠ EVENLY SPACED, NOT RANDOM. The sweep failures are clustered by type and
borough, so a sample drawn from one region of the counter would misattribute the
whole window. Even spacing covers the range and is reproducible.
"""
from __future__ import annotations
import argparse, json, pathlib, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import live_crfn as LC, live_delta as LD

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=40)
a = ap.parse_args()

held = set()
for l in (HERE / "_live_delta_queue.jsonl").open(encoding="utf-8"):
    v = str(json.loads(l).get("crfn") or "").strip()
    if v.isdigit():
        held.add(int(v))
lo, hi = min(held), max(held)
holes = [n for n in range(lo, hi + 1) if n not in held]
print(f"  window {lo}..{hi}  span {hi-lo+1:,}  held {len(held):,}  holes {len(holes):,}")

step = max(1, len(holes) // a.n)
sample = holes[::step][:a.n]
print(f"  sampling {len(sample)} evenly (every {step}th hole)\n")

s = LD.Session().open().open_crfn()
ctrl = max(held)
if LC.parse_detail(LC.detail_html(s, ctrl)) is None:
    sys.exit("  ⚠ CONTROL failed — refusing to classify anything")
print(f"  control {ctrl} resolves — probe OK\n")

cls = {"REAL+PARCEL": [], "PERSONAL": [], "UNISSUED": []}
for i, n in enumerate(sample, 1):
    try:
        d = LC.parse_detail(LC.detail_html(s, n))
    except Exception as e:
        print(f"    {n} ERROR {type(e).__name__} — skipped"); continue
    if d is None:
        cls["л" if False else "UNISSUED"].append((n, "", ""))
    elif d["bbls"]:
        cls["REAL+PARCEL"].append((n, d["doc_type"], d["bbls"][0]))
    else:
        cls["PERSONAL"].append((n, d["doc_type"], ""))
    if i % 10 == 0:
        print(f"    {i}/{len(sample)}")

print(f"\n  ── SAMPLE OF {sum(len(v) for v in cls.values())} HOLES ──")
tot = sum(len(v) for v in cls.values()) or 1
for k, v in cls.items():
    print(f"  {k:12} {len(v):>3}  ({100*len(v)/tot:5.1f}%)  -> "
          f"~{round(len(holes)*len(v)/tot):,} of {len(holes):,}")
for k in ("REAL+PARCEL", "PERSONAL"):
    if cls[k]:
        print(f"\n  {k} examples:")
        for n, t, b in cls[k][:6]:
            print(f"    {n}  {t[:38]:<38} {b}")
(HERE / "_hole_sample.json").write_text(json.dumps(
    {"holes": len(holes), "sampled": tot,
     "classes": {k: len(v) for k, v in cls.items()},
     "examples": {k: v[:20] for k, v in cls.items()}}, indent=1), encoding="utf-8")
