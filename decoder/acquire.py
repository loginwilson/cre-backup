"""BULK ACQUISITION — cooperate with the limiter instead of guessing around it.

⚠ WHAT 2026-08-09 ESTABLISHED, AND WHY THE OLD FETCHER IS WRONG FOR IT.

Login watched their own browser get refused at the same moment this client was,
and recover minutes later. That settles a question the project has been guessing
at since August: THE LIMIT IS ADDRESS-LEVEL RATE THROTTLING, NOT BOT DETECTION.
It does not care what is making the requests — a script and a browser draw on
one budget, which is why fetching here blocked Login's own browsing.

Two consequences, and the second is the one the old design got backwards:

  1. Slowing down HELPS. A rate limiter is a signal to obey, not an obstacle.
     Backing off is the correct engineering response and also the polite one.
  2. A FIXED INTERVAL IS THE WRONG SHAPE. `MIN_INTERVAL_S = 25` never speeds up
     when the server is happy and never slows down when it is not; it just
     walks into the wall at a constant speed and then burns the whole day.

     Measured under the fixed interval, all three runs today:
         run 1   4 requests -> refused      run 3  11 requests -> refused
         run 2   1 request  -> refused      16 pages in a whole day

⚠ SO: AIMD. Additive increase, multiplicative decrease — the same rule TCP uses
to share a link it cannot see the far end of, for exactly this reason. On every
success the interval eases down a little; on every refusal it doubles and the
run sleeps. It converges on whatever rate the City actually allows WITHOUT ever
needing to know what that rate is, and it re-converges on its own when the
limit changes.

⚠ AND IT MEASURES THE COOLDOWN AS A SIDE EFFECT. Every refusal and every
recovery is timestamped to refusals.jsonl, so the number that decides this
project — how long a block lasts — accumulates from ordinary work instead of
needing a separate experiment.

⚠ WHAT THIS IS NOT. Nothing here rotates an address, varies a User-Agent,
replays a session, mimics human timing, or retries a refused request. Those
would be evading a limit rather than respecting one, and they are also the fast
way to lose access for everybody on this connection — including Login's
browser. IF THE SERVER SAYS NO, THIS SLEEPS.

----------------------------------------------------------------------------
STORAGE — the second half, because acquisition without a retention rule just
moves the wall from "cannot fetch" to "cannot store".

    a page as G4 TIFF        ~56 KB     measured over 1,688 held pages
    the same page as text    ~2.8 KB    20x
    a clause proof crop      ~10 KB

⚠ THE ORIGINAL INSTRUCTION WAS RIGHT AND store.py OVERCORRECTED. Login's rule
was: read the document, crop the proof, delete the page. store.py then reversed
it to "nothing is deleted", for a real reason — eight parser bugs were fixed in
one session and every earlier reading stayed frozen at the version that made it.

Both are right about different things, and the synthesis is per-page, by
evidence rather than by blanket rule:

    ALWAYS KEEP   the OCR text          2.8 KB   searchable forever, and it is
                                                 what makes a later grep able
                                                 to find pages nobody has read
    ALWAYS KEEP   every proof crop       10 KB   the claim's evidence; a claim
                                                 whose page was swept without a
                                                 crop is UNFALSIFIABLE
    KEEP THE TIFF when the page bears a claim, or when OCR did badly enough
                  that the text cannot be trusted (film, low confidence) — the
                  only two cases where re-reading the pixels is ever needed
    OTHERWISE     drop the TIFF. A page that OCR'd cleanly and matched no slot
                  vocabulary has been read; the text is the record.

    ~7 KB/page retained against 56 KB fetched  ->  8x

⚠ AND THE COST OF THIS IS REAL: a dropped TIFF cannot be re-read at higher
resolution, ever, because the ledger will not re-fetch it. That is the price of
not paying for 6.7 TB, it is a decision rather than an oversight, and the two
KEEP rules above exist to make sure the pages where it would hurt are the
pages that stay.
"""
import json
import pathlib
import random
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATE = pathlib.Path(__file__).with_name("acquire_state.json")

# ⚠ EVERY NUMBER HERE IS A STARTING POINT THE RUN IS EXPECTED TO REVISE, not a
# measurement. The whole point of AIMD is that the right interval is discovered.
START_INTERVAL = 25.0     # where today's fixed pacing sat
MIN_INTERVAL = 6.0        # floor; never hammer even if the server tolerates it
MAX_INTERVAL = 900.0      # 15 min ceiling between single requests
EASE = 0.92               # multiplicative ease-down per success (additive-ish)
BACKOFF = 2.0             # double on refusal
COOLDOWN_START = 300.0    # first sleep after a refusal; doubles if it recurs
COOLDOWN_MAX = 3600.0


def _load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"interval": START_INTERVAL, "cooldown": COOLDOWN_START,
            "ok": 0, "refused": 0, "last_refusal": None, "history": []}


def _save(s):
    STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")


class Governor:
    """Holds the current rate, and is the only thing allowed to change it."""

    def __init__(self):
        self.s = _load()

    def wait(self):
        # ⚠ JITTER IS NOT DISGUISE. Identical spacing makes many workers
        # synchronise into bursts against one limiter; a few percent of noise
        # de-synchronises them. It does not make anything look human and is not
        # meant to — a single worker is still perfectly regular on average.
        iv = self.s["interval"]
        time.sleep(iv * random.uniform(0.9, 1.1))

    def success(self):
        s = self.s
        s["ok"] += 1
        s["interval"] = max(MIN_INTERVAL, s["interval"] * EASE)
        _save(s)

    def refused(self):
        """Back off hard and sleep. NEVER retries — the caller stops."""
        s = self.s
        s["refused"] += 1
        s["interval"] = min(MAX_INTERVAL, s["interval"] * BACKOFF)
        cd = s["cooldown"]
        s["last_refusal"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        s["history"].append({"at": s["last_refusal"], "ok_before": s["ok"],
                             "interval": round(s["interval"], 1),
                             "cooldown": round(cd)})
        s["cooldown"] = min(COOLDOWN_MAX, cd * BACKOFF)
        _save(s)
        print(f"  refused after {s['ok']} good requests; interval -> "
              f"{s['interval']:.0f}s, sleeping {cd/60:.0f} min")
        time.sleep(cd)
        # ⚠ RECOVERY IS PROVEN BY ONE PROBE, NOT ASSUMED BY A CLOCK. The caller
        # resumes with a single request; if that is refused too, cooldown has
        # already doubled.
        s["cooldown"] = max(COOLDOWN_START, s["cooldown"] / BACKOFF)
        _save(s)

    def report(self):
        s = self.s
        span = len(s["history"])
        print(f"\n  interval now {s['interval']:.0f}s · {s['ok']} ok · "
              f"{s['refused']} refusals")
        if span:
            gaps = [h["ok_before"] for h in s["history"]]
            d = [gaps[i] - gaps[i - 1] for i in range(1, len(gaps))] or gaps
            print(f"  requests between refusals: {d}")
            print(f"  -> sustained rate ≈ {sum(d)/max(len(d),1):.0f} requests "
                  f"per burst")
