"""THE EVENT CONTRACT. One graph, two traversals, direction first-class.

This is the layer the rest of the resolver is written against. The extractor
above it can change completely - Paddle, Qwen, Kimi, a future 27B - and the
lineage code below it does not move, because both only ever touch this shape.

    CANONICAL TEXT -> CLAIMS -> EVENTS -> ROLES+DIRECTION+EFFECT
                   -> FUNCTIONAL LINEAGES -> CHRONOLOGY + FUNCTION -> STATE

⚠ ONE GRAPH, NOT TWO DATASETS. Chronology and functional lineage are TRAVERSALS
of the same events, not separate stores:

    chronology:  date     -> event -> function -> effect
    function:    function -> event -> direction/effect -> date

Duplicating the events to serve both views guarantees they drift, and a parcel
history that disagrees with its own financing history is worse than either alone.

⚠ DIRECTION IS FIRST-CLASS AND CANNOT BE RECONSTRUCTED LATER. `parcels: [A, B]`
on a transfer has already destroyed the thing that matters. One event writes TWO
directional effects - A sends 42,500 SF, B receives 42,500 SF - so each parcel's
lineage reads correctly from its own side. Every instrument in this corpus has a
polarity: grantor->grantee, borrower/lender, burdened->benefited,
assignor->assignee, releasing->released, fee owner->ground lessee.

⚠ AND THIS IS EXACTLY WHAT TRANSCRIPTION SCORING CANNOT SEE. An engine that emits
both `SPRINGFIELD EQUITIES LTD` and `Peninsula National Bank` scores 2/2 whether
or not it knows which is mortgagor. Swap them and the debt lineage inverts -
borrower becomes lender - with full provenance and perfect citations. Transcription
at 96% with roles inverted is worse than 90% with roles right, which is why role
assignment is validated HERE rather than trusted from the extractor.

⚠ EVERY VALUE CARRIES HOW IT WAS ESTABLISHED. `resolved_from` distinguishes a
value the pixels showed from one the ACRIS index supplied from one a model
inferred. The canonical text stays an honest record of the page - if the image
was unreadable it says [UNCLEAR] and keeps saying it - while the semantic value
may still be complete via an independent structured source. Those are different
claims about the world and collapsing them is how a $0 microfilm mortgage becomes
a fact.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# FUNCTIONS - the lineages an event can participate in.
# ⚠ An event may touch MORE THAN ONE. "Conveyed subject to the obligations of
# the 1994 zoning lot agreement" is an ownership event that also links into the
# zoning lineage; modelling it as ownership-only loses the encumbrance.
# --------------------------------------------------------------------------
FUNCTIONS = (
    "ownership",          # fee title
    "financing",          # mortgages, notes, modifications, satisfactions
    "development_rights", # TDR/ZLDA/DEVR pools
    "zoning",             # ZLDA, restrictive declarations, variances
    "easement",           # rights over land
    "leasehold",          # ground leases, subleases
    "restriction",        # covenants, party wall, environmental
)

# ⚠ ROLE IS THE DIRECTION, AND IT IS PER-PARTICIPANT. A single event assigns a
# role to EACH side; the pair is what makes the transfer readable from either
# parcel. Never store a bare party list.
ROLES = (
    "grantor", "grantee",                 # deeds
    "mortgagor", "mortgagee",             # debt: borrower / lender
    "assignor", "assignee",
    "releasing", "released",
    "sending_parcel", "receiving_parcel", # development rights
    "burdened", "benefited",              # easements
    "lessor", "lessee",
    "nominee",                            # ⚠ MERS is a NOMINEE, not a lender.
                                          # Treating it as mortgagee poisons the
                                          # financing chain across the corpus.
)

# ⚠ EFFECT IS WHAT CHANGED, SIGNED. "transfer" is not an effect; "-42,500 SF on
# the sender / +42,500 SF on the receiver" is. State is recovered by applying
# effects in date order, so an unsigned effect cannot be resolved.
EFFECTS = (
    "created", "increased", "decreased", "transferred_out", "transferred_in",
    "encumbered", "released", "modified", "extinguished", "assumed",
)

# How a value came to be known. Kept per-FIELD, not per-event.
RESOLVED_FROM = (
    "image",        # the pixels established it (OCR / VLM agreement)
    "index",        # ACRIS structured record supplied it
    "escalation",   # a vision model resolved a disputed span
    "unresolved",   # SOURCE ILLEGIBLE - the pixels do not establish it
)


def event(*, event_id, date, action, functions, effects, document_id, page,
          acts_on=None, governing=None, quantity=None, unit=None,
          resolved_from="image", confidence=None, claims=None):
    """Build one validated event.

    `effects` is a list of {party_or_parcel, role, effect, quantity?} - at least
    one entry, and for any transfer BOTH sides must be present.
    """
    if action is None or not str(action).strip():
        raise ValueError("event needs an action")
    for f in functions:
        if f not in FUNCTIONS:
            raise ValueError(f"unknown function {f!r}; extend FUNCTIONS "
                             f"deliberately rather than passing free text")
    if not effects:
        raise ValueError("an event with no effects changes no state and is not "
                         "an event - it is a mention")
    for e in effects:
        if e.get("role") not in ROLES:
            raise ValueError(f"unknown role {e.get('role')!r} - direction must "
                             f"be explicit, never inferred downstream")
        if e.get("effect") not in EFFECTS:
            raise ValueError(f"unknown effect {e.get('effect')!r}")
    # ⚠ A TRANSFER WITH ONE SIDE IS A HALF-RECORDED FACT. It will read correctly
    # from one parcel and be invisible from the other, which is precisely the
    # failure the two-sided model exists to prevent.
    outs = {"transferred_out", "decreased"}
    ins = {"transferred_in", "increased"}
    kinds = {e["effect"] for e in effects}
    if (kinds & outs) and not (kinds & ins):
        raise ValueError("transfer records a sender but no receiver")
    if (kinds & ins) and not (kinds & outs):
        raise ValueError("transfer records a receiver but no sender")
    if resolved_from not in RESOLVED_FROM:
        raise ValueError(f"unknown provenance {resolved_from!r}")
    # ⚠ A FACT WITHOUT document_id + page CANNOT BE CHECKED and this project has
    # already ruled that such facts refuse to exist.
    if not document_id or page is None:
        raise ValueError("every event needs document_id and page")
    return {
        "event_id": event_id, "date": date, "action": action,
        "functions": list(functions), "effects": list(effects),
        "acts_on": acts_on,          # the prior object/event this modifies
        "governing": governing,      # instrument that controls it (ZLDA #7)
        "quantity": quantity, "unit": unit,
        "document_id": document_id, "page": page,
        "resolved_from": resolved_from, "confidence": confidence,
        "claims": list(claims or []),
    }


def chronology(events, bbl=None):
    """TIME primary, function as attribute. 'What happened to this property?'"""
    rows = [e for e in events
            if bbl is None or any(x.get("party_or_parcel") == bbl
                                  for x in e["effects"])]
    return sorted(rows, key=lambda e: (e["date"] or "", e["event_id"]))


def lineage(events, function, bbl=None):
    """FUNCTION primary, date as attribute, and read FROM ONE SIDE.

    ⚠ THE SAME EVENT READS DIFFERENTLY FROM EACH PARCEL, which is the whole
    point: Lot 17 shows "SENT 42,500 SF -> Lot 22", Lot 22 shows "RECEIVED
    42,500 SF <- Lot 17". Returning the raw event to both would make one of them
    wrong.
    """
    out = []
    for e in sorted(events, key=lambda x: (x["date"] or "", x["event_id"])):
        if function not in e["functions"]:
            continue
        mine = [x for x in e["effects"]
                if bbl is None or x.get("party_or_parcel") == bbl]
        if not mine:
            continue
        for m in mine:
            other = [x for x in e["effects"] if x is not m]
            out.append({"date": e["date"], "action": e["action"],
                        "role": m["role"], "effect": m["effect"],
                        "quantity": m.get("quantity", e.get("quantity")),
                        "counterparty": other[0].get("party_or_parcel")
                                        if other else None,
                        "acts_on": e["acts_on"], "governing": e["governing"],
                        "document_id": e["document_id"], "page": e["page"],
                        "resolved_from": e["resolved_from"]})
    return out


def state(events, function, bbl):
    """Apply signed effects in date order. The present is a REPLAY, not a field.

    ⚠ AN UNRESOLVED QUANTITY MUST NOT BE TREATED AS ZERO. A missing SF figure is
    not "no square feet transferred" - it is an unknown, and silently summing it
    as 0 produces a confident wrong balance. Unknowns are counted and reported
    alongside the total so the number is never mistaken for complete.
    """
    total, unknown, applied = 0.0, 0, []
    for row in lineage(events, function, bbl):
        q = row.get("quantity")
        if row["effect"] in ("increased", "transferred_in", "created"):
            sign = 1
        elif row["effect"] in ("decreased", "transferred_out", "extinguished"):
            sign = -1
        else:
            applied.append(row); continue
        if q is None:
            unknown += 1
        else:
            total += sign * float(q)
        applied.append(row)
    return {"bbl": bbl, "function": function, "net": total,
            "unknown_quantities": unknown, "events": len(applied),
            "complete": unknown == 0}
