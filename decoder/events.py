"""EVERY DOCUMENT DID SOMETHING — one plain-language event per instrument.

⚠ THE ERROR THIS FIXES, AND IT IS MINE, NOT THE DOCUMENTS'.

I reported 25 documents as "opened but yielded no claim" and defended it with
"a negative result is a result." That was a rationalisation. NOBODY PAYS TO
RECORD A DOCUMENT THAT SAYS NOTHING. Every one of those 25 is a real event:

    7  assignments moving the lien between named holders on dated instruments
       — literally the holder chain I "reconstructed" by reading schedules
       off page images, agent by agent
    5  title certifications naming every party in interest on the zoning lot
       and whether each SIGNED or WAIVED
    3  terminations, including Shanghai Commercial releasing its rents
       assignments in 2023
    2  zoning lot descriptions filed by the owner in 2015
    1  ⚠ MARRIOTT INTERNATIONAL — the Amended and Restated Right of First
       Refusal. An agent read all nine pages and I recorded nothing.

⚠ WHAT ACTUALLY HAPPENED: I was writing a NARRATIVE and skipping the routine.
The interesting findings got claims; the ordinary events that make the
timeline continuous did not. A ledger with only the interesting parts is not
a ledger — it is an article with citations.

⚠ AND THE FIX IS MECHANICAL, NOT INTERPRETIVE. The index already carries
party 1, party 2, type and date for every document. That is enough to state
what each instrument DID in one sentence a broker can read, with no page
opened and no judgment applied. A document may then earn MORE claims from a
specialist read — but it may never have ZERO.

    python events.py           the timeline, one line per document
    python events.py --patch   write an event claim for every document
"""
import collections
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IDX = pathlib.Path("acris_index_1008000049.json")
BBL = "1008000049"

# what each type DOES, as a sentence. party 1 -> party 2.
# ⚠ WRITTEN FOR A BROKER, NOT FOR A SCHEMA. "moved the mortgage to" beats
# "ASST", and the whole point of a decode is that the reader never has to
# learn the four-letter code.
VERB = {
 "DEED":  "sold the property to",
 "MTGE":  "borrowed against the property from",
 "AGMT":  "consolidated and restated its mortgage debt with",
 "ASST":  "sold the mortgage to",
 "AALR":  "transferred the rents assignment to",
 "AL&R":  "pledged the building's rents to",
 "TL&R":  "released its claim on the rents in favour of",
 "SAT":   "discharged the mortgage held against",
 # ⚠ DIRECTION MATTERS AND I HAD THIS BACKWARDS. ACRIS party 1 is the
 # GRANTOR side on every conveyance type — on a DEVR that is the lot
 # SELLING its unused floor area, not the developer buying it. Reading it
 # the wrong way makes the co-op look like the developer.
 "DEVR":  "sold development rights to",
 "EASE":  "granted or received an easement with",
 "ZONE":  "filed a zoning lot description covering the assembled lots",
 "CERT":  "certified who held every interest in the zoning lot",
 "SAGE":  "recorded an agreement affecting the property with",
 "SMIS":  "recorded a miscellaneous instrument affecting the property",
 "RPTT&RET": "filed a transfer-tax return on a sale to",
 "RPTT":  "filed a transfer-tax return on a sale to",
}


def load():
    d = json.loads(IDX.read_text(encoding="utf-8"))
    m = {r["document_id"]: r for r in d["master"]}
    # ⚠ KEEP EVERY PARTY, NOT THE FIRST. A document can have two grantors
    # or three lenders, and taking whichever row came back first silently
    # picks one and hides the rest.
    par = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in d["parties"]:
        par[p["document_id"]][p.get("party_type")].append(p.get("name", ""))
    return d["ids"], m, par


def sentence(doc, m, par):
    x = m.get(doc, {})
    t = (x.get("doc_type") or "?").upper()
    def side(n):
        v = [x.strip() for x in par.get(doc, {}).get(n, []) if x.strip()]
        if not v:
            return ""
        return v[0] if len(v) == 1 else f"{v[0]} (and {len(v)-1} other)"
    p1, p2 = side("1"), side("2")
    amt = x.get("document_amt")
    try:
        amt = float(amt)
    except (TypeError, ValueError):
        amt = None
    v = VERB.get(t, "recorded an instrument affecting the property")
    s = f"{p1 or 'a party'} {v}"
    if p2:
        s += f" {p2}"
    if amt and amt > 0:
        s += f", indexed at ${amt:,.0f}"
    return t, s


def main():
    ids, m, par = load()
    rows = []
    for d in ids:
        t, s = sentence(d, m, par)
        rows.append(((m.get(d, {}).get("document_date") or "")[:10], d, t, s))
    rows.sort()

    if "--patch" not in sys.argv:
        print(f"THE TIMELINE · {len(rows)} documents, one line each\n")
        for dt, d, t, s in rows:
            print(f"  {dt or '?':<11} {t:<9} {s[:96]}")
        print(f"\n  ⚠ EVERY LINE IS AN EVENT. None of these documents is empty.")
        print(f"    The index alone writes all {len(rows)} of them, free.")
        return

    # ---- write one event claim per document -----------------------------
    import claims as K
    have = {c["document_id"] for c in K.rows()}
    new = [r for r in rows if r[1] not in have]
    body = []
    for dt, d, t, s in new:
        esc = s.replace('"', "'")
        body.append(
            f' C("ev-{d[-8:]}", "{d}", "p001", "party_role",\n'
            f'   text="{esc[:150]}",\n'
            f'   eff="{dt or "1900-01-01"}", ev="index", ans=["IDENTIFY"],\n'
            f'   note="event claim generated from the ACRIS index — type '
            f'{t}. ⚠ Every recorded document did something; a document with '
            f'no claim is a decoder failure, not an empty instrument"),\n')
    p = pathlib.Path("claims.py")
    txt = p.read_text(encoding="utf-8")
    import re
    # ⚠ ANCHOR ON THE LAST SECTION HEADER THAT EXISTS, not a hard-coded
    # one. Earlier patches consumed the "2011" header and this silently
    # crashed — a patch script that assumes a landmark still exists is the
    # same class of error as trusting a stale summary.
    hdrs = list(re.finditer(r"^ # ---- .*$", txt, re.M))
    assert hdrs, "no section header found in claims.py"
    anchor = hdrs[-1].group(0)
    txt = txt.replace(anchor, "".join(body) + anchor, 1)
    p.write_text(txt, encoding="utf-8")
    print(f"wrote {len(new)} event claims — every document now has one")


main()
