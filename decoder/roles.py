"""PARTICIPANTS AND THEIR ROLES — the piece that turns a lead into an event.

    from roles import participants
    participants(text) -> [{party, role, kind, span, quote}, ...]

⚠ WITHOUT THIS THERE ARE NO EVENTS, ONLY LEADS. An event must say what changed,
FOR WHOM, and in which direction. Until 2026-08-14 claim_read.py extracted money,
dates, CRFN, area and parcel — and no participants at all — so all 1,104 envelope
detections across 21 DEVR documents were unbindable by construction. Direction is
what makes the conservation check possible, and direction lives here.

⚠ ENTITY IS NOT PERSON, AND THE PERSON IS THE POINT. The ACRIS index gives you
"123 MAIN ST LLC" and stops. Only the instrument says "by John Smith, its
Managing Member" — the thread that links one single-purpose entity to the next
deal. So `kind` distinguishes them and BOTH are kept: the entity is the party to
the instrument, the person is who acted for it.

⚠ DIRECTION IS CARRIED BY THE ROLE, NOT INFERRED LATER. grantor/grantee,
mortgagor/mortgagee, sender/receiver — each role maps to a sign. A bare party
list has already destroyed the thing that matters, and no downstream step can
recover it.

⚠ AND ROLE IS THE ONE FIELD TRANSCRIPTION SCORING CANNOT CHECK. Swap grantor and
grantee and the characters score 100% while the lineage runs backwards. The ACRIS
PARTIES index (party_type) is the only independent witness — which is why every
role read here is a CANDIDATE until the index corroborates it.

⚠ OCR DROPS SPACES IN EXACTLY THIS REGION. Measured on DEVR:
"NOTARYPUBLIC,STATEOFNEWYORK", "FIRSTAMERICANTITLEINSURANCECOMPANY". Every
pattern tolerates missing whitespace or it reads a signed document as unsigned.
"""
from __future__ import annotations

import re

# ── role language → (role, sign) ────────────────────────────────────────────
# sign: -1 gives up / conveys away · +1 receives · 0 neither (witness, notary)
ROLE_PATTERNS = [
    (r"\bgrantor\b",                       "grantor",    -1),
    (r"\bgrantee\b",                       "grantee",    +1),
    (r"\bmortgagor\b",                     "mortgagor",  -1),
    (r"\bmortgagee\b",                     "mortgagee",  +1),
    (r"\bassignor\b",                      "assignor",   -1),
    (r"\bassignee\b",                      "assignee",   +1),
    (r"\bparty\s+of\s+the\s+first\s+part\b",  "grantor", -1),
    (r"\bparty\s+of\s+the\s+second\s+part\b", "grantee", +1),
    # Development-rights language. ⚠ In a DEVR the sides are usually named by
    # what they own, not by "grantor/grantee" — this is why the generic deed
    # vocabulary alone finds nothing in an envelope document.
    (r"\bgranting\s+(?:party|parcel|lot|site)\b", "sender",   -1),
    (r"\bsending\s+(?:party|parcel|lot|site)\b",  "sender",   -1),
    (r"\breceiving\s+(?:party|parcel|lot|site)\b", "receiver", +1),
    (r"\bdevelopment\s+parcel\b",          "receiver",   +1),
    (r"\btransferor\b",                    "sender",     -1),
    (r"\btransferee\b",                    "receiver",   +1),
    (r"\bdeclarant\b",                     "declarant",   0),
]
ROLES = [(re.compile(p, re.I), r, s) for p, r, s in ROLE_PATTERNS]

# ── who acted ───────────────────────────────────────────────────────────────
# ⚠ The acknowledgment names the PERSON. Measured as the near-universal marker
# across 25 DEVR documents (81 "STATE OF", 81 "acknowledg", 29 "personally
# appeared") where "By:" appeared only 10 times.
PERSON = re.compile(
    r"personally\s*(?:appeared|came)\s+([A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){0,3})")
BY_LINE = re.compile(r"\bBY[:,]\s*([A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){0,3})")
TITLE = re.compile(
    r"\b(managing\s*member|member|manager|president|vice\s*president|"
    r"secretary|treasurer|attorney[\-\s]*in[\-\s]*fact|authorized\s*signator\w*)\b",
    re.I)

# ⚠ An entity is recognised by its SUFFIX, and OCR eats the spaces before it.
ENTITY = re.compile(
    r"\b([A-Z][A-Za-z0-9&.,'\- ]{2,60}?\s*"
    r"(?:LLC|L\.L\.C\.|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO\.|"
    r"L\.P\.|LP|LTD|LIMITED|ASSOCIATES|PARTNERSHIP|TRUST|N\.A\.))\b")


def participants(text, base=0):
    """Every participant this text supports, with role, sign and span.

    ⚠ EVERY RETURN CARRIES A SPAN so the claim can be verified byte-for-byte,
    and `role_established_by` is always "text" here — never "index". The index
    corroborates a role; it does not read one out of a document.
    """
    out = []
    for rx, role, sign in ROLES:
        for m in rx.finditer(text or ""):
            out.append({"role": role, "sign": sign, "kind": "role_label",
                        "party": None, "span": [base + m.start(), base + m.end()],
                        "quote": m.group(0), "role_established_by": "text"})
    for rx, kind in ((PERSON, "person"), (BY_LINE, "person")):
        for m in rx.finditer(text or ""):
            out.append({"role": None, "sign": 0, "kind": kind,
                        "party": m.group(1).strip(),
                        "span": [base + m.start(1), base + m.end(1)],
                        "quote": m.group(0), "role_established_by": "text"})
    for m in ENTITY.finditer(text or ""):
        out.append({"role": None, "sign": 0, "kind": "entity",
                    "party": " ".join(m.group(1).split()),
                    "span": [base + m.start(1), base + m.end(1)],
                    "quote": m.group(1), "role_established_by": "text"})
    for m in TITLE.finditer(text or ""):
        out.append({"role": None, "sign": 0, "kind": "title",
                    "party": m.group(1).strip(),
                    "span": [base + m.start(1), base + m.end(1)],
                    "quote": m.group(1), "role_established_by": "text"})
    return out


def signed_effects(parts):
    """Roles that carry a direction — the rows event_participant needs.

    ⚠ A TRANSFER WITH ONLY ONE SIGN IS INCOMPLETE BY CONSTRUCTION, not a
    low-confidence result. Callers must treat a one-sided transfer as a LEAD.
    """
    return [p for p in parts if p["kind"] == "role_label" and p["sign"] != 0]


def balanced(parts):
    s = {p["sign"] for p in signed_effects(parts)}
    return (-1 in s) and (+1 in s)
