"""THE IMAGE POLICY — one module, both sources. pending -> probe daily -> terminal.

WHY ONE MODULE. The lag rules were baked into rc_daily.py alone, which made them a
Richmond feature instead of the system's image policy. ACRIS documents landed with
image_state NULL — not pending, not imageless, just unasked — and nothing would
ever have asked. A policy that lives in one consumer is a config; a policy that
every lander imports is a rule. (Same cure as corpus_paths.py: single source of
truth, unaddressable duplication becomes impossible.)

THE RULES — MEASURED, NOT INVENTED (rc_imagelag.py, 2026-08-18)
    Richmond: age 0 days 0/15 imaged · age 1 day 11/11 · ages 4-90 100%.
              Scans attach overnight — a STEP at ~24 h, not a decay curve.
    ACRIS:    400/400 imaged same-day — no lag, so its pending set drains on the
              first probe and stays ~one day's filings deep.

    RULE 1  A new document lands as image_state='pending'. The index is the
            event; the scan is evidence for a later phase. A missing scan is
            never a hole in the specification.
    RULE 2  A pending document is probed for image availability EACH DAILY RUN
            while it is <= TERMINAL_DAYS old — so a scan that attaches late
            (day 3, day 6) is still caught the morning it appears, not lost
            because a one-shot recheck already happened.
    RULE 3  TERMINAL STATE. Past TERMINAL_DAYS a still-pending document is
            reclassified 'imageless' and never asked for again. Without this the
            queue is unbounded — and the class is REAL: a 2000 Richmond
            AMENDMENT (instrument 73755) still reads "No Image Available At This
            Time" 26 years on. 'pending' and 'imageless' are INDISTINGUISHABLE
            on any single read; only age separates them.

⚠ A DOCUMENT WITH NO USABLE DATE MUST NOT BE IMMORTAL. Age comes from
recorded date, falling back to when WE first saw it — a record missing both
would sit pending forever, invisible, so classify() starts its clock the day it
is first asked about (the caller stamps first_seen).
"""
from __future__ import annotations

import datetime as dt

PENDING = "pending"
PRESENT = "present"
IMAGELESS = "imageless"

TERMINAL_DAYS = 7          # 7x the measured ~24 h Richmond lag; generous on purpose


def age_days(today, recorded_iso, first_seen_iso=None):
    """Days since the document's clock started, or None if no date is usable.
    recorded date is the real clock; first_seen is the fallback that keeps a
    dateless record from being immortal."""
    for s in (recorded_iso, first_seen_iso):
        if not s:
            continue
        try:
            return (today - dt.date.fromisoformat(s[:10])).days
        except ValueError:
            continue
    return None


def is_terminal(today, recorded_iso, first_seen_iso=None):
    """True when a still-pending document has aged past TERMINAL_DAYS and must
    be reclassified IMAGELESS. None-aged records are NOT terminal — the caller
    stamps first_seen to start their clock instead."""
    a = age_days(today, recorded_iso, first_seen_iso)
    return a is not None and a > TERMINAL_DAYS
