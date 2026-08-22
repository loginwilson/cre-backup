"""A request budget for ACRIS images — stay under the limit instead of finding it.

WHY THIS EXISTS
    On 2026-08-05 this project was cut off mid-session by the ACRIS bandwidth
    notice. The cause was not volume in the abstract; it was a technique. A
    byte-size "scan" fetched 15-page ranges to locate one exhibit, when the
    decodes already recorded the exact page. ~7x the requests for the same
    answer, and ACRIS charges for requests.

    The alternative to a $8,670 image subscription is a few days of polite
    fetching — but only if "polite" is enforced by code rather than intended.

WHAT IT ENFORCES
    * a HARD daily ceiling, persisted, that survives restarts
    * a minimum interval between requests
    * a permanent (doc_id, page) ledger — a page is NEVER fetched twice, across
      sessions, forever. The image is scrap; the KNOWLEDGE that it was read is not.
    * an abort on the bandwidth notice that also BURNS the rest of the day's
      budget, so a refusal cannot be retried into a longer block.

The ledger is the quiet win. Re-reading a document you already decoded costs
nothing but a lookup, which is what makes an incremental, day-by-day harvest
practical instead of a single heroic run that gets cut off half way.
"""
import json, pathlib, time
from datetime import date

STATE = pathlib.Path(__file__).with_name("fetch_budget_state.json")
# ⚠ MEASURED TRIP POINT, not a guess.
#
# On 2026-08-05 the block landed at request ~98, after:
#     14 requests of TARGETED fetching   — no problem at all
#     83 requests of RANGE SCANNING      — the block landed here
#     97 total in roughly 90 minutes
#
# Two things follow, and the second is the one that matters:
#
#  1. The trip point is somewhere near 100 requests in ~90 minutes. We do not
#     know whether the limit is per-session, per-hour or per-day, and we CANNOT
#     find out without tripping it again. So assume the tightest reading.
#  2. A cap of 100/day would sit EXACTLY on the number that got us blocked.
#     Halve it, and spread it across a day rather than 90 minutes.
#
# 50/day at 25s apart is ~21 minutes of activity in a 24-hour window — half the
# observed trip point, in a window 16x longer. Raise ONLY after a clear week
# with no refusal, and RECORD the date of the change so a later block can be
# attributed to it rather than guessed at.
# RAISED 2026-08-06 at Login's direction, to find the real ceiling instead of
# assuming the tightest reading of a single observation. What changed and what
# deliberately did NOT:
#
#   raised   the daily cap, 50 -> 600. The old number was a guess dressed as a
#            measurement, and guessing low costs real work.
#   KEPT     the 25s interval. Pacing is what actually reduces load on their
#            servers, and it is slower than a person clicking through a
#            document. Removing it would be the thing that caused trouble.
#   KEPT     the hard abort on refusal, which now genuinely fires (the detector
#            was structurally incapable of firing until 2026-08-06).
#
# So this is a CALIBRATION, not a charge at the limit: same gentle rate, longer
# run, instant stop the moment ACRIS says no.
DAILY_CAP = 600          # was 50; raising to locate the ceiling empirically
MIN_INTERVAL_S = 25.0    # UNCHANGED — the rate is the politeness, not the total


def _load():
    if STATE.exists():
        s = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        s = {"day": None, "used": 0, "fetched": {}, "blocked_until_day": None}
    today = date.today().isoformat()
    if s.get("day") != today:
        s["day"], s["used"] = today, 0
    return s


def _save(s):
    STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")


def already_have(doc_id, page):
    """Has this page ever been fetched? Persisted across sessions."""
    return str(page) in (_load()["fetched"].get(doc_id) or [])


def remaining():
    s = _load()
    if s.get("blocked_until_day") == s["day"]:
        return 0
    return max(0, DAILY_CAP - s["used"])


def note_fetch(doc_id, page):
    s = _load()
    s["used"] += 1
    s["fetched"].setdefault(doc_id, [])
    if str(page) not in s["fetched"][doc_id]:
        s["fetched"][doc_id].append(str(page))
    _save(s)


def note_blocked():
    """A refusal burns the day. Retrying into a block is how a short limit
    becomes a long one, and it is also just rude."""
    s = _load()
    s["blocked_until_day"] = s["day"]
    s["used"] = DAILY_CAP
    _save(s)


def plan(wanted):
    """[(doc_id, page)] -> what to fetch today, what is already held, what waits.

    Never returns more than the budget allows, and never returns a page the
    ledger has already seen.
    """
    s = _load()
    held, todo = [], []
    for doc_id, page in wanted:
        if str(page) in (s["fetched"].get(doc_id) or []):
            held.append((doc_id, page))
        else:
            todo.append((doc_id, page))
    budget = remaining()
    return {"already_held": held, "fetch_today": todo[:budget],
            "deferred": todo[budget:], "budget_remaining": budget,
            "blocked_today": s.get("blocked_until_day") == s["day"]}


def pace():
    time.sleep(MIN_INTERVAL_S)


if __name__ == "__main__":
    s = _load()
    pages = sum(len(v) for v in s["fetched"].values())
    print(f"day {s['day']}  used {s['used']}/{DAILY_CAP}  remaining {remaining()}")
    print(f"ledger: {pages} pages across {len(s['fetched'])} documents (never re-fetched)")
    if s.get("blocked_until_day") == s["day"]:
        print("BLOCKED today — budget burned deliberately; resume tomorrow")
    print(f"\nat {DAILY_CAP}/day: 1,490 pages (the $/sf tape) = "
          f"{1490/DAILY_CAP:.1f} days; 3,002 pages (all DEVR) = {3002/DAILY_CAP:.1f} days")
    print("compare: ACRIS 30-day image subscription $8,670 citywide / $1,820 Manhattan")
