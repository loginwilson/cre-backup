# Is it bot detection or throttling?

The ACRIS refusal page names both causes in one sentence — *"detection of
automated scripts/robots … or having exceeded the bandwidth limits"* — and is
byte-identical (25,103 b) every time. **The page will never tell us which.** So
it has to come from behaviour.

⚠ **This is a diagnostic, not a step toward defeating either one.** If the
answer is bot detection, the response is to stop using this channel — not to
look less like a bot. Nothing in this file changes a User-Agent, replays a
session, varies timing to look human, or rotates anything.

---

## They differ in four observable ways

| | throttling | bot detection |
|---|---|---|
| **another client, same IP, same moment** | also blocked | unaffected |
| **slowing down** | raises the trip point | changes nothing |
| **trip point** | tracks requests or bytes | tracks *pattern* |
| **recovery** | fixed cooldown | may need a new session |

## What is already known

    2026-08-05   14 targeted requests   fine
                 83 range-scan requests -> blocked at ~97 total
    2026-08-09   run 1: refused at request 5
                 run 2: refused at request 2
                 run 3: refused at request 12      16 pages all day
                 Login's browser: working normally throughout

⚠ **The last line is the strongest evidence available and it points at
detection.** Volume throttling is imposed on an address. If this client is
refused at request 2 while a browser on the same connection loads documents
freely, the limiter is distinguishing *clients*, not counting *requests*.

⚠ **But it is not yet proof, because the two were never observed at the same
instant** — and a refusal that lasts minutes could easily have lapsed before
the browser was tried. THAT is the gap TEST 1 closes.

⚠ **Also note what changed between the two dates.** In August the block took 97
requests and followed range scanning — a very machine-shaped access pattern.
Today it takes 1–12 requests with ordinary targeted fetching. Either the
threshold moved, or this client carries state from August. Those are different
worlds and the tests below separate them.

---

## TEST 1 — the decisive one. Costs one request.

Simultaneity is the whole point; run these inside the same minute.

1. the script issues **one** request and is refused (confirms the state)
2. **within 60 seconds**, Login loads any ACRIS document image in the browser

        browser WORKS      -> client discrimination. Bot detection.
        browser REFUSED    -> address-level. Throttling.

Nobody has to disguise anything. It is two observers looking at one server.

## TEST 2 — does slowing down help? Costs ~6 requests/hour.

One request every 10 minutes, unattended, recording success or refusal.

    trip point rises with spacing   -> rate limiting
    still trips at ~5-12 requests   -> counting or pattern, and pacing is
                                       irrelevant

⚠ **This also yields the number that decides the whole project** — how long the
cooldown runs. 12 pages per 5 minutes and a watchlist is easy; 12 per day and
retail acquisition is finished. Right now that is a guess, and three different
plans follow from three possible answers.

## TEST 3 — free. Read the refusal's headers.

Costs nothing: the next refusal already happening gets recorded rather than
discarded. `429` with `Retry-After`, or any `X-RateLimit-*`, is a limiter
announcing itself. A `200` carrying HTML — which is what we get — is
characteristic of a filter that would rather not say. Capturing status,
headers and elapsed time turns each future refusal into evidence instead of
just an abort.
