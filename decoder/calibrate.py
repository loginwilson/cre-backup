"""RECORD A LOCKED CONFIG UNDER ITS PHASE — locally first, Supabase when it exists.

    python calibrate.py --list
    python calibrate.py --list --phase extraction
    python calibrate.py --push          # send anything not yet in Supabase

⚠ WRITES LOCALLY FIRST, ON PURPOSE. `_calibrations.json` is the source of truth
and never depends on the table existing, the network being up, or a migration
having been run. Losing a measurement because a DDL had not been applied yet
would be the exact failure this file exists to prevent.

⚠ EVERY ROW CARRIES ITS EVIDENCE OR IT IS REFUSED. value + measured_how +
measured_on + failure_if_wrong. A bare number is an invitation to "improve" it:
WORKERS=5 reads like a shy default until you know that 8 measured SLOWER THAN
SERIAL because the API throttles a burst.

⚠ ALTERNATIVES ARE RECORDED, NOT JUST THE WINNER. The losing settings are what
stop the next person re-running the same sweep — and one of them here is a
hypothesis of mine that the measurement killed (raising the OCR detector side
length made it slower AND read fewer characters).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
STORE = HERE / "_calibrations.json"
ENV = pathlib.Path(r"C:\dev\acris-decoder.env")

REQUIRED = ("phase", "component", "setting", "value",
            "measured_how", "measured_on", "failure_if_wrong")

# ── the calibrations locked so far ──────────────────────────────────────────
SEED = [
 # ---- EXTRACTION · the OCR channel -------------------------------------
 {"phase": "extraction", "source": "acris", "component": "rapidocr",
  "setting": "intra_op_num_threads", "value": "8  (os.cpu_count())",
  "measured_how": "shipped config.yaml sets -1, which onnxruntime does NOT read "
                  "as 'all cores'. Same page, same image: -1 = 24.54s, 8 = 18.79s.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "-1 runs effectively single-threaded on 8 cores. The tell "
                      "is that halving the image barely changes the time.",
  "alternatives": {"-1 (shipped default)": "24.54s", "8 + inter 1": "18.79s"},
  "locked": True},

 {"phase": "extraction", "source": "acris", "component": "rapidocr",
  "setting": "use_dml", "value": "true",
  "measured_how": "3 DEVR pages, warmed, identical preprocessing: CPU 11.41s/page "
                  "vs DirectML 6.01s/page. Character output IDENTICAL (7,602).",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "left false (the shipped default) the run is ~1.9x slower "
                      "for byte-identical text. DmlExecutionProvider must be in "
                      "onnxruntime.get_available_providers() or it silently "
                      "falls back to CPU.",
  "alternatives": {"CPU": "11.41s/page", "DirectML": "6.01s/page"},
  "locked": True},

 {"phase": "extraction", "source": "acris", "component": "rapidocr",
  "setting": "limit_side_len", "value": "736  (the shipped default — keep it)",
  "measured_how": "swept 736/1280/1600 on the same page. 736=15.17s/2345 chars, "
                  "1280=15.88s/2191, 1600=19.30s/2086. Higher is SLOWER AND READS "
                  "FEWER CHARACTERS.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "raising it looks like a quality improvement and is the "
                      "opposite. ⚠ This killed my own hypothesis that the "
                      "detector resolution was the bottleneck — it was thread "
                      "config and the execution provider.",
  "alternatives": {"736": "15.17s / 2345 ch", "1280": "15.88s / 2191 ch",
                   "1600": "19.30s / 2086 ch"},
  "locked": True},

 {"phase": "extraction", "source": "acris", "component": "rapidocr",
  "setting": "page_preprocessing",
  "value": "open -> convert('L') -> LANCZOS resize to 1600 max side -> RGB",
  "measured_how": "load+convert+resize measured at 0.08s total against 18.2s of "
                  "inference — preprocessing is NOT the cost. Source pages are "
                  "8.5 MP bilevel (PIL mode '1').",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "feeding mode '1' straight to the reader wastes memory; "
                      "and chasing preprocessing for speed optimises 0.4% of the "
                      "runtime.",
  "locked": True},

 {"phase": "extraction", "source": "acris", "component": "paddleocr",
  "setting": "status", "value": "BLOCKED — hangs in PaddleOCR() constructor",
  "measured_how": "pp_doc.py --limit 4 produced ZERO output and sat at ~0% CPU "
                  "for 3+ minutes; killed. No model cache under ~/.paddlex or "
                  "~/.paddleocr, so it hangs fetching PP-OCRv6 weights, not on "
                  "inference.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "a hang with no output reads as a slow job rather than a "
                      "failed one. RapidOCR (onnxruntime) is the working CPU/DML "
                      "path today; Paddle needs its weights cached before it can "
                      "be compared at all.",
  "locked": False},

 # ---- SPECIFICATION · how the map and index were pulled ------------------
 {"phase": "specification", "source": "acris", "component": "pull_index_fast",
  "setting": "WORKERS", "value": "5",
  "measured_how": "A/B with ALTERNATING arm order, median of 3, identical id "
                  "sets: 4.38x over serial. 8 workers measured ~= serial.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "8 looks like tuning and costs ~4x because the API "
                      "throttles a burst. ⚠ The FIRST A/B said parallel was 3.7x "
                      "SLOWER — the parallel arm ran first and tripped the "
                      "throttle. Alternate arm order or the API will lie.",
  "alternatives": {"serial": "1.0x", "5": "4.38x", "8": "~= serial"},
  "locked": True},

 {"phase": "specification", "source": "acris", "component": "pull_index_fast",
  "setting": "overfull_partition_strategy", "value": "keyset advance",
  "measured_how": "blind range splitting 8,645 rows/s and NON-TERMINATING; "
                  "keyset advance 52,559 rows/s and provably progresses "
                  "(last > first >= lo). references 8,699,896 rows in 2.8m.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "a document cannot be separated from itself: one "
                      "document_id with >= LIMIT rows makes every child as big "
                      "as its parent. Parties froze at exactly 31,898,850 for "
                      "10 minutes while requests climbed and the queue DRAINED — "
                      "every health signal except the row count looked normal.",
  "alternatives": {"blind subdivide": "8,645 rows/s, hangs",
                   "keyset advance": "52,559 rows/s"},
  "locked": True},

 {"phase": "specification", "source": "acris", "component": "pull_index_fast",
  "setting": "LIMIT", "value": "50000",
  "measured_how": "honoured by Socrata; partition bounds come from a LOCAL "
                  "histogram of 9,148 id prefixes (13s, zero planning queries).",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "a page returning exactly LIMIT is indistinguishable from "
                      "a truncated one, so it must never be kept as-is.",
  "locked": True},

 {"phase": "specification", "source": "acris", "component": "socrata",
  "setting": "$order", "value": ":id  (always, on any paged read)",
  "measured_how": "$offset without $order silently drops AND duplicates rows "
                  "while the COUNT stays correct.",
  "measured_on": "2026-08-06",
  "failure_if_wrong": "silent row loss that no count can detect. Fixed in shared "
                      "bulk.py, so it affected every decoder.",
  "locked": True},

 {"phase": "specification", "source": "acris", "component": "selection_daily",
  "setting": "watermark_seed", "value": "dataset_stamp from a CLEAN audit only",
  "measured_how": "the audit wrote _selection_cross_state.json while the daily "
                  "read _selection_daily_state.json, so the daily refused every "
                  "night with 'run selection_cross.py first' — which had already "
                  "run and passed.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "seeding from wall-clock (checked_at, naive local) instead "
                      "of the dataset stamp (UTC) silently skips the EDT offset "
                      "— four hours of updates, once, invisibly.",
  "locked": True},

 {"phase": "specification", "source": "acris", "component": "document_map",
  "setting": "no_image_gate", "value": "gate on source_document, NOT no_image",
  "measured_how": "no_image is TRUE for total_pages=0 but FALSE for "
                  "total_pages=-1, though neither has an image. 8 of 8 sampled "
                  "-1 documents were sitting in acquisition_pending.",
  "measured_on": "2026-08-14",
  "failure_if_wrong": "~174,000 image-less documents get requested; ACRIS serves "
                      "its placeholder as HTTP 200, so nothing errors and the run "
                      "records 174,000 successful fetches of a placeholder.",
  "locked": True},
]


def env():
    e = {}
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"')
    return e["ACRIS_SUPABASE_URL"].rstrip("/"), e["ACRIS_SUPABASE_SERVICE_KEY"]


def load():
    if STORE.exists():
        return json.loads(STORE.read_text(encoding="utf-8"))
    return []


def save(rows):
    STORE.write_text(json.dumps(rows, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--phase", default=None)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    rows = load()
    if not rows:
        for r in SEED:
            miss = [k for k in REQUIRED if not r.get(k)]
            if miss:
                # ⚠ REFUSE, never store a half-calibration.
                print(f"  ⚠ REFUSED {r.get('component')}.{r.get('setting')} — "
                      f"missing {miss}")
                continue
            rows.append(r)
        save(rows)
        print(f"  seeded {len(rows)} calibrations -> {STORE.name}\n")

    if a.push:
        url, key = env()
        body = [{k: v for k, v in r.items()} for r in rows]
        req = urllib.request.Request(f"{url}/rest/v1/calibration", method="POST",
                                     data=json.dumps(body).encode())
        req.add_header("apikey", key)
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Prefer", "return=minimal")
        try:
            urllib.request.urlopen(req, timeout=120)
            print(f"  pushed {len(body)} calibrations to Supabase")
        except Exception as e:
            detail = ""
            try:
                detail = e.read().decode()[:200]
            except Exception:
                pass
            print(f"  ⚠ PUSH FAILED: {e}\n    {detail}")
            print("    Local store is unaffected — run migrations/003 first.")
        return 0

    shown = [r for r in rows if not a.phase or r["phase"] == a.phase]
    phase = None
    for r in shown:
        if r["phase"] != phase:
            phase = r["phase"]
            print(f"\n  ── {phase.upper()} " + "─" * (58 - len(phase)))
        lock = "🔒" if r.get("locked") else "⚠ "
        print(f"  {lock} {r['component']}.{r['setting']} = {r['value']}")
        print(f"       measured  {r['measured_how'][:110]}")
        print(f"       if wrong  {r['failure_if_wrong'][:110]}")
    print(f"\n  {len(shown)} calibrations   ·   store: {STORE.name}")
    print("  ⚠ Not yet in Supabase — run migrations/003_calibration.sql, "
          "then `python calibrate.py --push`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
