"""Fetch the across-parcel sample. p002 + p003 per deed, budgeted and paced.

⚠ TWO PAGES, NOT ONE, AND THE REASON IS A CONFOUND. p001 is the ACRIS cover
sheet — county-generated, identical on all 17M documents, so it proves nothing.
But what sits on p002 is NOT constant: sometimes the grant, sometimes an
RP-5217 form, sometimes a continuation of the cover. Comparing one deed's grant
page against another's RP-5217 scores them far apart EVEN IF BOTH DOCUMENTS USE
THE SAME TEMPLATE — a false null, and a false null here would have killed a
true idea.

Taking two pages lets the comparison ask the honest question: does ANY body
page of A match ANY body page of B?
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

print(f"{len(docs)} deeds x 2 pages = {len(docs)*2} requests; "
      f"{fetch_budget.remaining()} left in today's budget")

done = 0
for stratum, d in docs:
    print(f"\n[{stratum}] {d}  bbl {s['bbl'].get(d,'?')}")
    try:
        got = fetch_pages.fetch_pages(d, OUT, [2, 3])
        done += len(got)
    except fetch_pages.AccessDenied as e:
        # ⚠ STOP. Do not retry, do not work around it. Whatever was fetched is
        # still a usable sample; a partial answer honestly obtained beats a
        # complete one that got us blocked.
        print(f"\n⚠ {e}")
        break
    except Exception as e:
        print(f"  ⚠ {type(e).__name__}: {str(e)[:120]} — skipping this deed")

print(f"\nfetched {done} pages into {OUT}/   "
      f"({fetch_budget.remaining()} budget left)")
