"""THE VOCABULARY PROPOSAL LOOP — the bridge from fused evidence to a schema.

    python vocab_propose.py                  # propose from resolved events
    python vocab_propose.py --review         # the queue, with its evidence
    python vocab_propose.py --adopt action:transfer --why "..."
    python vocab_propose.py --freeze         # cut a version before a run

⚠ THE SCHEMA IS THE *EVENT* SCHEMA — ONE FIELD LIST, NOT ONE PER DOCUMENT TYPE.
Charter p7: "A schema is simply the agreed list of fields every event carries...
every layer after Resolution reads events rather than documents. Fix the field
list and the models that produce those fields can be replaced without touching
anything downstream." So `function` is a VALUE, not a schema. DEVR, AIRRIGHT,
easement and a ZLDA filed as AGMT are the same shape with different values, which
is exactly why they can all land in one parcel's envelope lineage.

⚠ WHAT THE CHARTER LEAVES OPEN IS WHAT THIS FILE EXISTS TO CLOSE. p7: "Two things
still have to be settled for each field: the values it may take — the full list of
permitted actions, roles and functions — and how the system decides that two
documents describe this same transfer rather than two different ones."
This closes the FIRST. Identity/dedup is not attempted here and is not pretended.

⚠ PROPOSALS ARE REVIEWED, NEVER ADOPTED AUTOMATICALLY. Charter p7: "a new action
or role is added only when an existing one cannot carry the meaning, so the
vocabulary grows by necessity rather than by drift." A loop that auto-adopts what
it sees does not build a vocabulary, it launders whatever the extractor happened
to emit into a standard — and every later disagreement becomes unarguable because
the standard already agrees with the defect.

⚠ EVERY PROPOSED TERM CARRIES ITS EVIDENCE. A term with no passage behind it is a
guess with a name. Same rule as the rest of the system: a fact refuses to exist
without document_id and page.

⚠ FREEZE BEFORE A PRODUCTION RUN. Charter p7: "Each version of the schema and its
guardrails is frozen before a production run, so any result can be traced back to
the rules that produced it." --freeze writes an immutable version file; results
record which version produced them.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
VOCAB_DIR = HERE / "vocab"
CURRENT = VOCAB_DIR / "current.json"
PROPOSALS = VOCAB_DIR / "_proposals.json"

EVENTS = HERE / "resolve" / "_events.json"
LEADS = HERE / "resolve" / "_leads.json"

# The four controlled fields the charter names. `effect` is included because a
# signed effect with an uncontrolled verb cannot be summed, and summing is what
# makes the conservation check possible.
FIELDS = ("action", "function", "role", "effect")


def load_vocab():
    if CURRENT.exists():
        return json.loads(CURRENT.read_text(encoding="utf-8"))
    # ⚠ AN EMPTY VOCABULARY IS THE HONEST STARTING STATE. On the first run every
    # term is a proposal, which is correct: nothing has been reviewed yet.
    return {"version": 0, "frozen_at": None,
            "terms": {f: {} for f in FIELDS}}


def load_events():
    if not EVENTS.exists():
        return []
    return json.loads(EVENTS.read_text(encoding="utf-8"))


def harvest(events):
    """Every controlled value the resolver actually emitted, with its evidence.

    ⚠ EVIDENCE IS THE EVENT IT CAME FROM, NOT A COUNT. "seen 12 times" cannot be
    reviewed; "seen in BK_6730047100023 as mortgagor" can.
    """
    seen = {f: collections.defaultdict(list) for f in FIELDS}
    for ev in events:
        eid = ev.get("event_id", "?")
        if ev.get("action"):
            seen["action"][ev["action"]].append((eid, ev.get("action")))
        for fn in ev.get("functions") or []:
            seen["function"][fn].append((eid, fn))
        for eff in ev.get("effects") or []:
            if eff.get("role"):
                seen["role"][eff["role"]].append(
                    (eid, (eff.get("party_or_parcel") or "")[:70]))
            if eff.get("effect"):
                seen["effect"][eff["effect"]].append(
                    (eid, (eff.get("party_or_parcel") or "")[:70]))
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--adopt", default=None, help="field:term")
    ap.add_argument("--why", default=None,
                    help="which existing term could NOT carry the meaning")
    ap.add_argument("--freeze", action="store_true")
    a = ap.parse_args()

    VOCAB_DIR.mkdir(exist_ok=True)
    vocab = load_vocab()

    # ---- adopt -------------------------------------------------------------
    if a.adopt:
        if ":" not in a.adopt:
            print("  --adopt takes field:term, e.g. action:transfer")
            return 2
        field, term = a.adopt.split(":", 1)
        if field not in FIELDS:
            print(f"  unknown field {field!r}; expected one of {FIELDS}")
            return 2
        # ⚠ REFUSE A BARE ADOPTION. The charter's rule is that a term is added
        # only when an existing one CANNOT carry the meaning. Recording that
        # reason is what makes the vocabulary reviewable a year from now.
        if not a.why:
            print("  ⚠ --why is required: name the existing term that could not\n"
                  "    carry this meaning, and why. A term adopted without a\n"
                  "    reason is drift with a timestamp.")
            return 2
        props = json.loads(PROPOSALS.read_text(encoding="utf-8")) \
            if PROPOSALS.exists() else {}
        ev = (props.get(field, {}).get(term, {}) or {}).get("evidence", [])
        vocab["terms"].setdefault(field, {})[term] = {
            "adopted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "why": a.why,
            "first_seen_in": ev[:3],
        }
        CURRENT.write_text(json.dumps(vocab, indent=1), encoding="utf-8")
        print(f"  adopted {field}:{term}\n    why: {a.why}")
        return 0

    # ---- freeze ------------------------------------------------------------
    if a.freeze:
        v = int(vocab.get("version", 0)) + 1
        vocab["version"] = v
        vocab["frozen_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        CURRENT.write_text(json.dumps(vocab, indent=1), encoding="utf-8")
        (VOCAB_DIR / f"v{v}.json").write_text(
            json.dumps(vocab, indent=1), encoding="utf-8")
        n = sum(len(t) for t in vocab["terms"].values())
        print(f"  froze v{v} — {n} terms -> vocab/v{v}.json")
        print("  ⚠ record this version on every run it governs, or a result\n"
              "    cannot be traced back to the rules that produced it.")
        return 0

    # ---- propose -----------------------------------------------------------
    events = load_events()
    print("VOCABULARY PROPOSAL LOOP\n")
    print(f"  vocabulary   v{vocab.get('version', 0)}"
          f"  ({sum(len(t) for t in vocab['terms'].values())} terms adopted)")
    print(f"  events read  {len(events):,}   <- resolve/_events.json")

    if not events:
        print("\n  NO EVENTS. Nothing to propose from — this loop reads what the\n"
              "  resolver produced, it does not read documents itself.")
        return 1

    seen = harvest(events)
    props = {}
    known_n = new_n = 0
    for field in FIELDS:
        adopted = vocab["terms"].get(field, {})
        for term, ev in sorted(seen[field].items()):
            if term in adopted:
                known_n += 1
                continue
            new_n += 1
            props.setdefault(field, {})[term] = {
                "count": len(ev),
                "evidence": [{"event_id": e, "passage": p} for e, p in ev[:5]],
            }
    PROPOSALS.write_text(json.dumps(props, indent=1), encoding="utf-8")

    print(f"\n  already adopted   {known_n}")
    print(f"  PROPOSED (new)    {new_n}")
    for field in FIELDS:
        if field not in props:
            continue
        print(f"\n  {field.upper()}")
        for term, meta in sorted(props[field].items(),
                                 key=lambda x: -x[1]["count"]):
            print(f"    {term:<26} x{meta['count']:<4} "
                  f"{meta['evidence'][0]['event_id']}")
            if a.review:
                for e in meta["evidence"]:
                    print(f"        {e['event_id']:<26} {e['passage']}")

    # ⚠ THE DENOMINATOR. A proposal list built from 3 documents is a proposal
    # list built from 3 documents, and saying so is the difference between a
    # vocabulary and a coincidence.
    docs = {e.get("event_id", "").rsplit("-", 1)[0] for e in events}
    print(f"\n  ⚠ PROPOSED FROM {len(docs)} DOCUMENT(S): {sorted(docs)}")
    print("    A vocabulary proposed from this few documents is a starting\n"
          "    point, not a standard. Adopt nothing that only one document\n"
          "    motivated unless you can say why no existing term carries it.")
    print(f"\n  queue -> {PROPOSALS.relative_to(HERE)}"
          f"   ({new_n} awaiting review)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
