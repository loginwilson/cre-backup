"""THE 50-DEED PULL. Run at Login's direction after they confirmed in their own
browser that ACRIS serves images normally.

⚠ WHAT CHANGED AND WHAT DELIBERATELY DID NOT.
    changed   the self-imposed block flag, which was POLICY not measurement.
              It burns the day on any refusal so a short block cannot be
              retried into a long one. Login checked the site directly; the
              refusal at request 5 did not persist.
    UNCHANGED the 25s interval, the daily cap, the permanent ledger, and the
              hard abort on refusal. Nothing rotates a user agent, replays a
              session, retries a refused request, or disguises what this is.
              If ACRIS says no again, this stops again.

WHAT THIS RUN IS FOR — two questions at once:
  1. WHERE DOES IT TRIP? The 2026-08-05 block landed near request 100; today's
     landed at 5 and did not persist. Neither is a limit; both are single
     observations. This run reports the number it reaches.
  2. It finishes the across-parcel fingerprint test, whose citywide and
     repeat-filer strata never ran.

⚠ TWO PAGES PER DEED, AND p002 IS OFTEN NOT THE DOCUMENT. The ACRIS cover runs
to 4 pages on a multi-party filing; coverpage.py detects the boundary, and any
deed whose sampled pages are both cover gets reported, not silently counted as
read.
"""
import json
import pathlib
import sys

import fetch_budget
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("fp_pages")
s = json.load(open("_fp_sample.json"))
docs = [(k, d) for k in ("A", "B", "C") for d in s[k]]

# top up to 50 from the same draw, so the strata stay labelled
extra = json.load(open("_fp_topup.json")) if pathlib.Path("_fp_topup.json").exists() else []
docs += [("A2", d) for d in extra]
docs = docs[:50]

print(f"{len(docs)} deeds x 2 pages = {len(docs)*2} requests")
print(f"{fetch_budget.remaining()} left in today's budget, 25s apart "
      f"(~{len(docs)*2*25/60:.0f} min)\n")

ok = blocked = 0
for i, (stratum, d) in enumerate(docs, 1):
    print(f"[{i:>2}/{len(docs)}] {stratum} {d}  bbl {s['bbl'].get(d,'?')}")
    # ⚠ COUNT PAGES ONE AT A TIME. The first version called fetch_pages with
    # [2,3] and added its RETURN VALUE — so when the refusal fired on page 3,
    # the exception unwound past the return and the page 2 that HAD arrived was
    # never counted. The run then reported "fetched 0 pages" while a 109 KB PNG
    # sat on disk. A counter that only updates on the happy path under-reports
    # exactly when the report matters most.
    try:
        for pg in (2, 3):
            ok += len(fetch_pages.fetch_pages(d, OUT, [pg]))
    except fetch_pages.AccessDenied as e:
        blocked = i
        print(f"\n⚠ REFUSED AT DEED {i}, after {ok} pages this run. {e}")
        break
    except Exception as e:
        print(f"  ⚠ {type(e).__name__}: {str(e)[:110]}")

print(f"\n{'='*70}")
print(f"fetched {ok} pages across {blocked-1 if blocked else len(docs)} deeds")
print(f"refused at deed {blocked}" if blocked else "COMPLETED WITHOUT REFUSAL")
print(f"{fetch_budget.remaining()} budget left")
