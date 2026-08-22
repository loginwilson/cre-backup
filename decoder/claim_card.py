"""THE CLAIM, rendered — value + terms + proof + citation, with components.

LOGIN, 2026-08-06:

    claim
      ├─ VALUE   53,578 sf received from lots 53/55/56
      ├─ TERM    granted with a light/air/view easement, plan review 10 days,
      │          30-day cure, entry license
      ├─ PROOF   [22 KB crop of Exhibit D]
      └─ CITE    2010102601040006 p038 · read

    "something like this should break down how each unit adds up to 53,578 to
     be clear."

⚠ THE COMPONENT BREAKDOWN IS NOT COSMETIC

    "53,578 sf from lots 53/55/56" is three transactions wearing one number.
    Split into components it becomes checkable — and one of the three lots is
    burdened by an easement the other two are not:

        23,864  from lot 53   ⚠ also grants a light/air/VIEW easement
        15,070  from lot 55
        14,644  from lot 56
        ------
        53,578  ✓ reconciles to the chart's own TOTAL column

    A reader who sees only the total cannot tell that lots 55 and 56 gave up
    floor area and nothing else. I recorded exactly that error this morning —
    an easement invented on two parcels — and a component view would have made
    it visible immediately, because the easement would have had nowhere to sit.

    So: components are rendered wherever a claim has them, and they must SUM to
    the parent. The sum is checked, not asserted.
"""
import csv, pathlib, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent


def _wrap(s, n):
    words, line, out = s.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out[:4]


# ⚠ the CITE must say WHAT KIND of instrument, not just its number. "deed
# 2010102601040006 p038" is locatable; a bare id is a lookup for the reader.
# TRUE type where the index lies — this parcel's EASE was twice a ZLDA.
DOCTYPE = {
 "2010102601040006": "ZLDA (indexed DEVR)",
 "2012122701550003": "ZLDA (indexed DEVR)",
 "2013052101674004": "ZLDA (indexed DEVR)",
 "2013052101674008": "ZLDA (indexed DEVR)",
 "2013080901116002": "ZLDA (indexed EASE)",
 "2013080901116001": "declaration (indexed SMIS)",
 "2013080901116003": "deed",
 "2019071700601003": "ZLDA-split (indexed EASE)",
 "2023110100486009": "mortgage",
 "2023110100486010": "CEMA (indexed AGMT)",
 "2023110100486001": "deed",
 "2020081400407001": "mortgage",
 "2014112601161004": "mortgage",
 "2013081200922003": "CEMA (indexed AGMT)",
 "2003110900238001": "CEMA (indexed AGMT)",
 "2007062101109001": "deed",
 "FT_1320008495632": "deed",
 "FT_1570006671557": "deed",
 "FT_1710006669171": "mortgage",
 "FT_1980000345898": "mortgage",
 "2015041300292001": "confirmation (indexed DEVR)",
}
L49 = "1008000049"

# parent claim -> component claims that must sum to it
COMPONENTS = {
    "c2010-rights": ["c2010-l53", "c2010-l55", "c2010-l56"],
    "c2019-l49env": [],      # 85,270 own + 56,659 acquired — see note
}
# where components are not separate claims, the arithmetic is declared here so
# the card can still show the build-up and CHECK it
DERIVED_PARTS = {
    "c2019-l49env": [("own land at FAR 10 (8,527 sf x 10)", 85_270),
                     ("acquired rights retained after the split", 56_659)],
    "c2013c-balance": [("envelope before the lot 20 airspace", 254_261),
                       ("lot 20 airspace above elev. 130 ft", 14_703)],
}


def load():
    sys.path.insert(0, str(HERE))
    import claims as K
    cl = {c["claim_id"]: c for c in K.rows()}
    proofs = {}
    pp = HERE / f"acris_proof_{L49}.csv"
    if pp.exists():
        for r in csv.DictReader(open(pp, encoding="utf-8")):
            proofs[(r["document_id"], r["page"])] = r
    terms = defaultdict(list)
    tp = HERE / f"acris_terms_{L49}.csv"
    if tp.exists():
        for r in csv.DictReader(open(tp, encoding="utf-8")):
            terms[r["document_id"]].append(r)
    slots = defaultdict(list)
    ip = HERE / "doctype_term_instance.csv"
    if ip.exists():
        for r in csv.DictReader(open(ip, encoding="utf-8")):
            if r["status"] == "PRESENT":
                slots[r["document_id"]].append(r)
    return cl, proofs, terms, slots


def card(cid, cl, proofs, terms, slots):
    c = cl.get(cid)
    if not c:
        return
    unit = c["unit"] or ""
    val = (f"${c['value_num']:,.2f}" if unit == "USD"
           else f"{c['value_num']:,.0f} {unit}".strip()) if c["value_num"] is not None \
          else (c["value_text"] or "")[:70]
    print(f"\n{'='*74}\nCLAIM  {cid}    {c['effective']}\n{'='*74}")
    print(f"  VALUE   {val}")
    if c["value_num"] is not None and c["value_text"]:
        print(f"          {c['value_text'][:66]}")

    # ---- components, and the check that they sum -------------------------
    parts = [(cl[p]["subject_bbl"], cl[p]["value_num"], cl[p].get("verbatim"))
             for p in COMPONENTS.get(cid, []) if p in cl]
    if parts:
        tot = 0
        for i, (subj, n, note) in enumerate(parts):
            tot += n or 0
            lead = "├─" if i < len(parts) - 1 else "└─"
            lot = subj[-3:].lstrip("0")
            flag = ""
            # does this component's lot carry a term the others do not?
            if any(t["burdened_bbl"] == subj for tl in terms.values() for t in tl):
                flag = "  ⚠ also burdened"
            print(f"          {lead} {n:>9,.0f} from lot {lot}{flag}")
        ok = "OK" if round(tot) == round(c["value_num"] or 0) else "MISMATCH"
        print(f"             {'':>9} {'-'*9}")
        print(f"             {tot:>9,.0f}  {ok} — reconciles to the chart's TOTAL")
    elif cid in DERIVED_PARTS:
        tot = 0
        ps = DERIVED_PARTS[cid]
        for i, (label, n) in enumerate(ps):
            tot += n
            lead = "├─" if i < len(ps) - 1 else "└─"
            print(f"          {lead} {n:>9,.0f}  {label}")
        ok = "OK" if round(tot) == round(c["value_num"] or 0) else "MISMATCH"
        print(f"             {'':>9} {'-'*9}")
        print(f"             {tot:>9,.0f}  {ok}")

    # ---- terms attached to the same instrument ---------------------------
    sl = slots.get(c["document_id"], [])
    tm = terms.get(c["document_id"], [])
    # ⚠ RENDER THE SENTENCE, NOT THE SLOT NAME. A slot name is an index key.
    # "alteration_restriction" tells a reader nothing about who is bound or
    # what they may not do; "lot 53 MUST NOT alter or rebuild if the work
    # would encroach into lot 49's band..." tells them everything.
    def sentence(actor, mod, act, obj, consent, contingent=False):
        if not actor:
            return None
        head = f"{actor} {mod} {act}"
        out = [f"          · {head}"]
        if obj:
            for chunk in _wrap(obj, 62):
                out.append(f"              {chunk}")
        if consent:
            out.append(f"              can be released by: {consent}")
        if contingent:
            out.append(f"              ⚠ NOT YET BINDING — sits in an unexecuted form")
        return chr(10).join(out)

    shown = []
    for s in sl:
        line = sentence(s.get("actor"), s.get("modality"), s.get("action"),
                        s.get("object"), s.get("consent_of"))
        if line:
            shown.append(line)
        elif s.get("value_text"):
            shown.append(f"          · [{s['slot']}] {s['value_text'][:58]}"
                         + chr(10) + "              ⚠ not yet written as a sentence")
    for tr in tm:
        line = sentence(tr.get("actor"), tr.get("modality"), tr.get("action"),
                        tr.get("object"), tr.get("consent_of"),
                        tr.get("status") == "CONTINGENT")
        if line:
            shown.append(line)
    if shown:
        print(f"  TERM    what this instrument obliges, in the same breath:")
        for line in shown[:5]:
            print(line)
        if len(shown) > 5:
            print(f"          ...and {len(shown)-5} more obligations")
    else:
        print(f"  TERM    none extracted from this instrument yet")

    # ---- proof -----------------------------------------------------------
    pr = proofs.get((c["document_id"], c["page"]))
    if pr:
        prec = "REGION" if float(pr["x1"]) - float(pr["x0"]) < 0.999 else "PAGE"
        warn = ("  ⚠ UNEXECUTED FORM" if pr["instrument_status"] == "FORM" else "")
        print(f"  PROOF   {pr['storage_path']}  "
              f"{int(pr['bytes'])/1024:.0f} KB · {prec}{warn}")
        print(f"          {pr['caption'][:62]}")
    else:
        print(f"  PROOF   none — this claim came from the index, not a page")
    dt = DOCTYPE.get(c["document_id"], "?")
    print(f"  CITE    {dt}  {c['document_id']}"
          f"{' ' + c['page'] if c['page'] else ''} · {c['evidence']}"
          + (f" · about lot {c['subject_bbl'][-3:].lstrip('0')}"
             if c["subject_bbl"] != L49 else ""))


def main():
    cl, proofs, terms, slots = load()
    for cid in ["c2023-mtge", "c2013-gs"]:
        card(cid, cl, proofs, terms, slots)

    n = len(cl)
    withp = sum(1 for c in cl.values()
                if (c["document_id"], c["page"]) in proofs)
    print(f"\n\n{'='*74}")
    print(f"  {withp} of {n} claims carry a proof · "
          f"{n-withp} are index-sourced and correctly have none")
    tot = sum(int(r["bytes"]) for r in proofs.values())
    print(f"  {len(proofs)} proof images · {tot/1024:.0f} KB for the whole parcel")


if __name__ == "__main__":
    main()
