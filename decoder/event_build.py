"""THE EVENT ASSEMBLER — claims + participants become events, or they become leads.

    python event_build.py              # assemble from devr_text/
    python event_build.py --show       # print each event
    python event_build.py --leads      # why the refusals refused

⚠ AN EVENT MUST NAME WHAT CHANGED, FOR WHOM, AND IN WHICH DIRECTION. Anything
short of that is a LEAD, not a low-confidence event. Charter p5: "If nothing
changes, there is no function and no event." This file is the only place that
decides which of the two a document produced, and it refuses rather than
degrades.

⚠ THE INDEX SUPPLIES THE PARTY, THE TEXT SUPPLIES THE SPAN. Measured 2026-08-14
over 25 DEVR documents: roles read from text alone made 4/25 constructible;
index party_type made 25/25, with 74 of 76 index names located in the OCR text.
So party identity is not extracted and then matched — the known answer is
SEARCHED FOR, which survives the space-dropping that mangles OCR entity names
("NYCPARTNERSHIPHOUSINGDEVELOPMENTFUNDCOMPANY").

⚠ EVERY VALUE CARRIES ITS ORIGIN. A quantity from a cover-page stamp and a
quantity from an exhibit are different evidence, and document_amt is 0 for every
DEVR — so `established_by` is never optional.

⚠ THE party_type MAPPING IS AN ASSUMPTION UNDER TEST, NOT A FACT. type 1 is
treated as the giving side and type 2 as the receiving side. Where the text also
carries an explicit role label, the two are CROSS-CHECKED and any disagreement
is reported as a possible ROLE INVERSION — the one failure transcription scoring
structurally cannot see, because swapping grantor and grantee scores 100% on
characters while reversing the lineage.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lexicon
import roles as R

HERE = pathlib.Path(__file__).parent
SRC = HERE / "devr_text"
OUT = HERE / "resolve" / "_events_built.json"
PARTIES = "https://data.cityofnewyork.us/resource/636b-3b5g.json"

MONEY = re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)")
AREA = re.compile(r"([\d,]+(?:\.\d+)?)\s*(square\s+feet|sq\.?\s*ft\.?|BSF|SF)\b", re.I)
DATE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b")

# ⚠ ASSUMPTION UNDER TEST — see module docstring.
TYPE_ROLE = {"1": ("sender", -1), "2": ("receiver", +1)}

# ── direction, read from the text near a party ──────────────────────────────
# ⚠ SIGNS, NOT LABELS. The first version compared role WORDS: text said
# "mortgagee", index implied "receiver", and it reported a role inversion on 10
# of 25 documents. Both are +1. Comparing vocabularies instead of directions
# produces an alarm that fires on everything and is therefore ignored — worse
# than no check at all.
SIGN_WORDS = [
    (r"\bgrantor\b|\bmortgagor\b|\bassignor\b|\btransferor\b|\bseller\b"
     r"|\bparty\s+of\s+the\s+first\s+part\b|\bgranting\s+(?:party|parcel|lot)\b"
     r"|\bsending\s+(?:party|parcel|lot)\b", -1),
    (r"\bgrantee\b|\bmortgagee\b|\bassignee\b|\btransferee\b|\bpurchaser\b"
     r"|\bparty\s+of\s+the\s+second\s+part\b|\breceiving\s+(?:party|parcel|lot)\b"
     r"|\bdevelopment\s+parcel\b", +1),
]
SIGN_RX = [(re.compile(p, re.I), s) for p, s in SIGN_WORDS]

# The verbs that actually move something. A quantity outside one of these
# clauses is a number on a page, not a transfer.
GRANT_VERB = re.compile(
    r"\b(grant(?:s|ed|ing)?|convey(?:s|ed|ing)?|transfer(?:s|red|ring)?|"
    r"assign(?:s|ed|ing)?|sever(?:s|ed|ing)?|declare(?:s|d)?)\b", re.I)

WINDOW = 300   # chars either side of a party mention


def sign_near(text, pos):
    """The direction word closest to a party mention, or None.

    ⚠ CLOSEST, NOT FIRST. A deed names both sides within a paragraph; taking the
    first match would assign every party the same sign.
    """
    lo, hi = max(0, pos - WINDOW), min(len(text), pos + WINDOW)
    win, best = text[lo:hi], None
    for rx, s in SIGN_RX:
        for m in rx.finditer(win):
            d = abs((lo + m.start()) - pos)
            if best is None or d < best[0]:
                best = (d, s, m.group(0))
    return best


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def index_parties(doc_ids):
    out = collections.defaultdict(list)
    for i in range(0, len(doc_ids), 40):
        chunk = doc_ids[i:i + 40]
        q = urllib.parse.urlencode({
            "$select": "document_id,name,party_type",
            "$where": "document_id in('%s')" % "','".join(chunk),
            "$limit": "1000"})
        for r in json.load(urllib.request.urlopen(f"{PARTIES}?{q}", timeout=180)):
            out[r["document_id"]].append((r.get("name", ""), r.get("party_type")))
    return out


def locate(needle_key, hay_key):
    """Where the index's name sits in the page text. -1 if absent.

    ⚠ TOLERATES A TRUNCATED TAIL because OCR frequently clips the final token of
    a long entity name; it does NOT tolerate a fuzzy middle, which would let one
    entity match another on a shared prefix.
    """
    p = hay_key.find(needle_key)
    if p < 0 and len(needle_key) > 12:
        p = hay_key.find(needle_key[:int(len(needle_key) * 0.8)])
    return p


def operative_spans(text):
    """(start, end) of every clause that fires a function AND moves something.

    ⚠ A QUANTITY OUTSIDE ONE OF THESE IS NOT A TRANSFER AMOUNT. Before this,
    every number on the page became an event quantity: 182 "considerations"
    across 25 documents, most of them page numbers, section refs and $0.00
    taxable-amount boxes on the cover page.
    """
    out = []
    for clause, off in lexicon.clauses(text):
        if lexicon.fire(clause, "function") and GRANT_VERB.search(clause):
            out.append((off, off + len(clause)))
    return out


# ⚠ THE ACTION IS PRINTED ON THE COVER PAGE AND I WAS INFERRING IT WRONGLY.
# Until 2026-08-14 this file set action="transfer" whenever the `envelope`
# function fired. Every document in the sample is stamped
# "Document Type: DEC OF DEVELOPMENT RIGHTS" — a DECLARATION. A declaration
# records and restricts; a transfer conveys. Nine events carried the wrong verb,
# and the inference looked reasonable precisely because envelope really had
# fired. The document says what it is; stop guessing from the vocabulary in it.
ACTION_OF = {
    "DEC OF DEVELOPMENT RIGHTS": "declare",
    "DECLARATION": "declare",
    "DEED": "convey",
    "MTGE": "secure",
    "AGMT": "agree",
    "ASST": "assign",
    "SAT": "discharge",
}


def action_from_type(doc_type):
    """⚠ MATCH WITH THE SPACES REMOVED. The cover prints
    "DEC OF DEVELOPMENT RIGHTS", but OCR renders it "DEC OFDEVELOPMENTRIGHTS" on
    13 of 25 documents — the same space-loss roles.py documents on the notarial
    block. Comparing on whitespace-normalised text still failed on those 13, and
    they fell back to the inferred action, so half the sample kept the wrong verb
    while the fix was already in place for the other half."""
    if not doc_type:
        return None
    u = re.sub(r"[^A-Z0-9]", "", doc_type.upper())
    for k, v in ACTION_OF.items():
        if re.sub(r"[^A-Z0-9]", "", k) in u:
            return v
    return None


def exhibits_all():
    """⚠ QUANTITIES COME FROM exhibit_read.py, WHICH KNOWS WHICH REGION IT IS IN.
    This file used to run one AREA regex over the whole document concatenated
    into a single string, then try to bind each hit to a clause. That lost the
    PAGE (so no claim could cite one), lost the REGION (so "the SF is in an
    exhibit, not the grant" could not be acted on), and its unit pattern
    required whitespace inside "square feet" — which OCR removes, so
    "8248squarefeet" was invisible."""
    p = HERE / "resolve" / "_exhibits.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def parcel_sides_all():
    """⚠ PARCELS COME FROM THE LEGALS INDEX, NOT THE COVER PAGE. Measured
    2026-08-14: 71 parcels in legals against 46 read off the 25 covers, and the
    page printed "Additional Properties on Continuation Page" on only 5 of the
    13 documents where it was short. Building the parcel population from the
    page loses 35% of it AND reports no warning on more than half the losses.
    The cover claim is still the better PROVENANCE — it has a span into a page
    someone can look at — so both are kept and the source is recorded."""
    p = HERE / "_parcel_sides.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def cover_claims_for(doc):
    """Cover-page claims already emitted and verified by cover_claims.py."""
    p = HERE / "resolve" / "_claims" / f"{doc}.cover.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l]


def build(doc, text, parties, cover=(), sides=(), exh=None):
    fns = lexicon.fire(text, "function")
    tk = norm(text)
    ops = operative_spans(text)

    # ⚠ QUANTITIES BIND BY REGION, NOT BY DISTANCE. Measured 2026-08-14 over 25
    # DEVR documents: the median area figure sits 1,364 chars from the nearest
    # operative clause and the median money figure 4,343 — only 1 of 23 and 1 of
    # 108 respectively fall INSIDE one. That is not a threshold problem, it is
    # the document's anatomy: the grant is in the instrument body, the SF is in
    # an EXHIBIT, and the price is on the ACRIS cover page. Three regions, one
    # fact. Binding by proximity cannot work and tuning the radius only trades
    # missed area against admitted noise.
    clause_spans = [(off, off + len(c), c) for c, off in lexicon.clauses(text)]

    def region_of(a):
        for s0, e0, c in clause_spans:
            if s0 <= a <= e0:
                return lexicon.fire(c, "region"), c
        return [], ""

    # Stamp language — the only money on a DEVR that is a price.
    STAMP = re.compile(r"RPTT|RETT|transfer\s*tax|consideration|purchase\s*price",
                       re.I)

    def binds(kind, a, b):
        regs, clause = region_of(a)
        if kind == "area":
            # the granted figure: an envelope clause, or an exhibit
            return ("exhibit" in regs
                    or bool(lexicon.fire(clause, "function"))
                    or any(s <= a and b <= e for s, e in ops))
        # consideration: cover page AND stamp language, or an operative clause
        return (("cover_page" in regs and bool(STAMP.search(clause)))
                or any(s <= a and b <= e for s, e in ops))

    # ── participants, with direction read from the text where possible ──────
    participants, unlocated = [], 0
    agree = disagree = untested = 0
    for name, ptype in parties:
        role, sign = TYPE_ROLE.get(str(ptype), (None, 0))
        pos = locate(norm(name), tk)
        if pos < 0:
            unlocated += 1
        # ⚠ THE CONVENTION IS TESTED PER PARTY, NOT PER DOCUMENT. Map the
        # located party back into raw text to look for a direction word beside
        # it. norm() strips characters, so the normalised offset is only an
        # approximation of the raw one — scaled here, and treated as a hint.
        ev_sign = ev_word = None
        if pos >= 0 and tk:
            approx = int(pos * len(text) / max(len(tk), 1))
            near = sign_near(text, approx)
            if near:
                _, ev_sign, ev_word = near
        if ev_sign is None:
            untested += 1
        elif ev_sign == sign:
            agree += 1
        else:
            disagree += 1
        participants.append({
            "party": name, "role": role, "sign": sign, "party_type": ptype,
            "text_sign": ev_sign, "text_word": ev_word,
            # ⚠ VALUE FROM THE INDEX, LOCATION FROM THE TEXT.
            "established_by": "index" if pos < 0 else "index+text",
            "located": pos >= 0,
        })

    # ⚠ INVERSION IS A SIGN DISAGREEMENT, NOT A VOCABULARY DIFFERENCE.
    inversion = (f"{disagree} of {agree+disagree} parties: index sign contradicts "
                 f"the direction word beside them in the text") if disagree else None

    # ── quantities, bound to the clause that moves them ─────────────────────
    quantities, unbound = [], 0
    seen = set()
    # ⚠ AREA NOW ARRIVES PRE-ATTRIBUTED AND IS NOT RE-BOUND. exhibit_read.py
    # already knows the page and the region; re-testing it against clause
    # geometry here would discard exhibit figures for sitting outside an
    # operative clause, which is precisely where the charter says they live.
    for q in (exh or {}).get("quantities", []):
        k = (q["kind"], q["value_num"])
        if k in seen:
            continue
        seen.add(k)
        quantities.append({
            "kind": q["kind"], "value_num": q["value_num"], "unit": q["unit"],
            "presence": "present", "established_by": q["established_by"],
            "page": q["page"], "region": q["region"], "exhibit": q["exhibit"],
            "span": q["span"], "quote": q["quote"]})
    for rx, kind, unit in ((MONEY, "consideration", "USD"),):
        for m in rx.finditer(text):
            a, b = (m.start(), m.end())
            val = m.group(1).replace(",", "")
            if not binds(kind, a, b):
                unbound += 1
                continue
            # ⚠ DEDUPE BY VALUE WITHIN A DOCUMENT. The granted figure is
            # restated in recitals and exhibits; three copies of 6,152 SF is one
            # transfer, not three.
            k = (kind, val)
            if k in seen:
                continue
            seen.add(k)
            quantities.append({
                "kind": kind, "value_num": val,
                "unit": (m.group(2).upper() if kind == "area" else unit),
                "presence": "present", "established_by": "text_operative",
                "span": [a, b], "quote": m.group(0)})

    # ── the cover page, promoted ────────────────────────────────────────────
    ck = {c["kind"]: c for c in cover}
    on_cover = {c["value"] for c in cover if c["kind"] == "parcel"}
    # legals is the population; the cover claim is the better provenance
    parcels = [{"value": f"{s_['borough']} block {s_['block']} lot {s_['lot']}",
                "role": s_["role"], "sign": s_["sign"],
                "status": s_["status"], "address": s_.get("address"),
                "established_by": "legals_index"
                                  + ("+cover_page" if
                                     f"{s_['borough']} block {s_['block']} lot {s_['lot']}"
                                     in on_cover else ""),
                "side_established_by": s_.get("established_by"),
                "incomplete": s_["lot"] is None}
               for s_ in sides]
    doc_type = (ck.get("doc_type") or {}).get("value")
    executed = (ck.get("document_date") or {}).get("value")

    # ⚠ THE PRICE ARRIVES FROM A DIFFERENT REGION AND IT DOES NOT NEED BINDING.
    # The body-text binder demands a money figure sit in an operative clause; on
    # a DEVR none does, which is why consideration bound 0 of 108 times. The
    # stamp is not in a clause at all — it is a field on a form, bound by
    # POSITION on the cover page, and it arrives already carrying its own
    # verified provenance. Re-binding it against clause geometry would discard
    # the only price the document has.
    cons = ck.get("consideration")
    if cons:
        quantities.append({
            "kind": "consideration", "value_num": cons.get("value"),
            "unit": "USD", "presence": cons.get("presence", "present"),
            "established_by": cons.get("established_by"),
            "confidence": cons.get("confidence"),
            "derivation": cons.get("derivation"),
            "bound": cons.get("bound"),
            "page": "p001",
        })

    signs = {p["sign"] for p in participants}
    # ⚠ A QUANTITY WHOSE PRESENCE IS `absent_by_nature` IS NOT A QUANTITY.
    # 16 of 25 covers stamp the tax at 0.00 — a real fact, and the reason the
    # claim exists — but an event cannot be established on "no money moved".
    real_q = [q for q in quantities if q.get("presence", "present") == "present"]
    reasons = []
    if not fns:
        reasons.append("no function changed")
    if not (-1 in signs and +1 in signs):
        reasons.append("not two-sided — no opposing signed effects")
    if not real_q:
        reasons.append("no quantity")
    # ⚠ A MIS-FILED DOCUMENT IS NOT A READER FAILURE. 12 of 25 covers say
    # "DEC OF DEVELOPMENT RIGHTS" over a PARTY WALL DECLARATION OF RESTRICTIONS.
    # No right moves, so no square footage exists, so "no quantity" is the
    # correct answer — and lumping it in with genuine extraction gaps would have
    # sent someone to build an extractor for numbers that are not there.
    _t = re.sub(r"[^A-Z]", "", ((exh or {}).get("instrument_title") or "").upper())
    if _t and not any(w in _t for w in ("DEVELOPMENT", "ZONINGLOT")):
        reasons.append(f"mis-filed — instrument is a "
                       f"{(exh or {}).get('instrument_title')}")
    if not parcels:
        reasons.append("no parcel")

    # ⚠ ESTABLISHED AND CONSERVABLE ARE TWO DIFFERENT QUESTIONS, AND COLLAPSING
    # THEM COSTS EITHER TRUTH OR SIGNAL. The charter's test for an event is
    # "what changed, FOR WHOM, and in which direction" — the parties satisfy all
    # three, because party_type carries the sign. But CONSERVATION ("SF leaving
    # equals SF arriving") is a test on PARCELS, and the cover page lists both
    # lots without ever saying which sends and which receives.
    #
    # First wiring put this in refused_because and every one of the 25 documents
    # refused — a true statement that destroyed the distinction between "we
    # cannot tell what this document did" and "we know what it did and cannot
    # yet balance it across lots". Guessing the side from list order is the
    # other failure and it is worse: direction is the one field transcription
    # scoring cannot catch, so a wrong guess propagates silently forever.
    open_q = []
    psigns = {p["sign"] for p in parcels if p.get("role")}
    sided = sum(1 for p in parcels if p.get("role"))
    if parcels and not psigns >= {-1, 1}:
        # ⚠ TWO DIFFERENT FAILURES AND THE FIRST WORDING CONFLATED THEM. It read
        # "parcel sides incomplete (5/5 sided)" — every parcel sided and still
        # refused, which reads as a bug. It is not: all five landed on the SAME
        # side. A document with three senders and no receiver cannot be balanced
        # no matter how completely it is read, and that needs a different fix
        # (find the missing counterparty) than a document with unsided lots.
        open_q.append(
            f"only one side present ({'sender' if -1 in psigns else 'receiver'}) "
            f"— counterparty parcel not identified"
            if sided == len(parcels) and psigns else
            f"parcel sides unresolved ({sided}/{len(parcels)} sided) "
            f"— conservation cannot run")
    if any(p.get("incomplete") for p in parcels):
        open_q.append("a parcel is missing its lot number")
    if cover and (ck.get("consideration") or {}).get("bound") == "upper":
        open_q.append("consideration is an UPPER BOUND (RETT rounds up to $500)")

    ev = {
        "event_id": f"{doc}-e1",
        "source": "acris", "source_ref": doc,
        "action": action_from_type(doc_type)
                  or ("transfer" if "envelope" in fns else (fns[0] if fns else None)),
        "action_established_by": "cover_page" if action_from_type(doc_type)
                                 else "inferred_from_function",
        "doc_type": doc_type,
        # ⚠ WHAT IT WAS FILED AS vs WHAT IT SAYS IT IS. 12 of 25 disagree.
        "instrument_title": (exh or {}).get("instrument_title"),
        "exhibits": (exh or {}).get("exhibits", []),
        "executed_date": executed,
        "recorded_date": (ck.get("recorded_date") or {}).get("value"),
        "crfn": (ck.get("crfn") or {}).get("value"),
        "functions": fns,
        "participants": participants,
        "parcels": parcels,
        "parcels_on_cover": len(on_cover),
        "quantities": quantities[:12],
        "n_quantities": len(quantities),
        "unbound_quantities": unbound,
        "convention": {"agree": agree, "disagree": disagree,
                       "untested": untested},
        "unlocated_parties": unlocated,
        "role_inversion": inversion,
        "established": not reasons,
        "refused_because": reasons,
        # ⚠ CONSERVABLE IS THE GATE THE LINEAGE ACTUALLY NEEDS. An established
        # event says what happened; only a conservable one can be checked with
        # "SF leaving equals SF arriving", which is the closure test this whole
        # system is built to run.
        "conservable": not reasons and psigns >= {-1, 1},
        "open_questions": open_q,
    }
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--leads", action="store_true")
    a = ap.parse_args()

    files = sorted(SRC.glob("*.json"))
    if not files:
        print("  no text — run devr_sweep.py first")
        return 1
    docs = [f.stem for f in files]
    print(f"EVENT ASSEMBLER — {len(docs)} documents\n")
    idx = index_parties(docs)
    sides = parcel_sides_all()
    exhibits = exhibits_all()
    if not sides:
        print("  ⚠ no _parcel_sides.json — run parcel_sides.py first; every\n"
              "    event will refuse for want of a parcel.\n")

    events, leads = [], []
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        text = " ".join(p.get("accepted_text") or "" for p in rec["pages"])
        ev = build(rec["doc_id"], text, idx.get(rec["doc_id"], []),
                   cover_claims_for(rec["doc_id"]),
                   sides.get(rec["doc_id"], []),
                   exhibits.get(rec["doc_id"]))
        (events if ev["established"] else leads).append(ev)

    OUT.write_text(json.dumps({"events": events, "leads": leads}, indent=1),
                   encoding="utf-8")

    print(f"  EVENTS established   {len(events):>4}/{len(docs)}")
    print(f"  LEADS (refused)      {len(leads):>4}/{len(docs)}")
    cons = sum(1 for e in events if e["conservable"])
    print(f"  of which CONSERVABLE {cons:>4}/{len(docs)}  "
          f"(parcel sides known — the closure test can run)")
    act = collections.Counter(f"{e['action']} [{e['action_established_by']}]"
                              for e in events + leads)
    print("\n  ACTION")
    for k, v in act.most_common():
        print(f"    {k:<44} {v}")
    oq = collections.Counter(q for e in events + leads for q in e["open_questions"])
    if oq:
        print("\n  OPEN QUESTIONS (event stands; this part is not settled)")
        for k, v in oq.most_common():
            print(f"    {k:<58} {v}")

    why = collections.Counter(r for l in leads for r in l["refused_because"])
    if why:
        print("\n  why refused")
        for k, v in why.most_common():
            print(f"    {k:<44} {v}")

    inv = [e for e in events + leads if e["role_inversion"]]
    print(f"\n  ⚠ ROLE INVERSION SUSPECTED   {len(inv)}")
    for e in inv[:5]:
        print(f"    {e['source_ref']}  {e['role_inversion']}")
    checked = sum(1 for e in events + leads
                  if R.signed_effects(R.participants('')) or True)
    print(f"    (the check is silent where the text carried no role label — "
          f"silence is not a pass)")

    unl = sum(e["unlocated_parties"] for e in events + leads)
    tot = sum(len(e["participants"]) for e in events + leads)
    print(f"\n  parties: {tot} total · {tot-unl} located in text · {unl} index-only")

    q = collections.Counter(qq["kind"] for e in events + leads for qq in e["quantities"])
    ub = sum(e["unbound_quantities"] for e in events + leads)
    print(f"  quantities BOUND to an operative clause: "
          + " · ".join(f"{k} {v}" for k, v in q.items()))
    print(f"  quantities discarded (not in an operative clause): {ub}")

    if a.show:
        for e in events[:6]:
            print(f"\n  {e['event_id']}  action={e['action']}  "
                  f"functions={e['functions']}")
            for p in e["participants"]:
                print(f"      {p['role'] or '?':<9} {p['sign']:+d}  "
                      f"{p['party'][:44]:<46} [{p['established_by']}]")
            for qq in e["quantities"][:3]:
                # a value_num of None is not missing data — it is
                # presence=absent_by_nature, printed as 0.00 on the cover
                v = ("—" if qq["value_num"] is None else f"{qq['value_num']}")
                print(f"      qty {qq['kind']:<14} {v:>12} "
                      f"{qq['unit']}  [{qq['established_by']}]"
                      + (f"  {qq['presence']}"
                         if qq.get("presence", "present") != "present" else ""))
    if a.leads:
        for l in leads[:10]:
            print(f"    {l['source_ref']}  {l['refused_because']}")

    print(f"\n  -> {OUT.relative_to(HERE)}")
    print("  ⚠ 25 documents of ONE type, 12 of them one filing split across "
          "sequential\n    instruments. Effective sample is ~14, not 25.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
