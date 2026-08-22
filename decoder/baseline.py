"""The as-of-right envelope — computed, so that RELIEF becomes a number.

THE GAP THIS CLOSES

    An entitlement is a DEPARTURE from a district's rules. "The Board granted
    232,985.77 square feet" is not an entitlement fact on its own — it becomes
    one only beside "the district allowed 102,341.60". Measured across ~2,900
    decoded BSA resolutions, both halves were present on **34 documents**:

        envelope_limited     552 facts    the grant, usually stated
        envelope_permitted   112 facts    the baseline, usually NOT

    The baseline is missing because most resolutions — especially the bulletin
    format, which is 68% of the corpus — recite WHICH rule was violated without
    reciting the number it sets. The DOB objection says "contrary to ZR 23-141
    in that the proposed FAR exceeds the permitted .50"; plenty of others say
    only "contrary to bulk regulations".

    But the baseline was never really missing. It is arithmetic:

        as-of-right floor area  =  district FAR  ×  zoning lot area

    and BOTH inputs are stated in the document. So this is not more retrieval.
    It is the reading already done, finished.

⚠ WHAT MAKES THIS A FACT AND NOT A GUESS

    `facts.Fact` refuses a derived value without a derivation, and it is right
    to. Every row emitted here carries:

        confidence = "derived"
        derivation = the district read on page N, the FAR from the ZR table,
                     the lot area read on page M, and the multiplication

    The citation is the BSA document and the page where the INPUTS were read,
    because that is where a person is walked back to in order to check it. The
    ZR section is named in the derivation, not substituted for the citation.

⚠ WHERE IT REFUSES TO COMPUTE, AND WHY THAT MATTERS MORE THAN WHERE IT DOES

    * SPECIAL DISTRICT — "R3-2 (SSRD)" is the Special South Richmond
      Development District, and a special district OVERRIDES the underlying
      bulk. Computing from R3-2 there would produce a confident wrong number.
    * NARROW vs WIDE STREET — R6 is 2.43 FAR on a narrow street and 3.00 on a
      wide one. The resolution rarely says which. Where they differ and the
      street is unknown, BOTH are recorded and neither is asserted.
    * SPLIT LOTS — a lot in two districts has no single FAR.
    * NO LOT AREA — without the denominator there is no floor area, only an FAR.

    A refusal is written down as a reason, never as a silent absence.
"""
import json, pathlib, re, sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import facts as F
import sink

REF = json.load(open(pathlib.Path(__file__).with_name("zoning_reference.json"),
                     encoding="utf-8"))
DISTRICTS = REF["districts"]

# a district string in the wild is not a district code. Measured over the BSA
# corpus: R-4, R 3-2, R3-X, R4-A, R3-1(SSRD), C1-2/R3-2, M1-5B ...
SPECIAL = re.compile(r"\(([A-Z]{2,6})\)|\b(SSRD|SRD|MX|EC|C4-\d+D)\b")
USES = ("residential", "community_facility", "commercial", "manufacturing")


def normalise(raw):
    """A district string -> (codes, flags). Never guesses past ambiguity."""
    s = (raw or "").strip().upper()
    flags = []
    sp = SPECIAL.search(s)
    if sp:
        flags.append(f"special_district:{sp.group(1) or sp.group(2)}")
        s = SPECIAL.sub("", s)
    s = s.replace(" ", "")
    parts = [p for p in re.split(r"[/,&+]", s) if p]
    codes = []
    for p in parts:
        p = p.strip(".")
        # R-4 -> R4 ; R3-X -> R3X ; R4-A -> R4A
        p = re.sub(r"^([A-Z])-(\d)", r"\1\2", p)
        p = re.sub(r"^([A-Z]\d)-([A-Z])$", r"\1\2", p)
        if p in DISTRICTS:
            codes.append(p)
        elif p:
            flags.append(f"unknown_district:{p}")
    if len(codes) > 1:
        flags.append("multiple_districts")
    return codes, flags


def far_for(code, use="residential"):
    """FAR for a district and use. Returns (narrow, wide) — they differ in the
    R6/R7/R8 range and the difference is not decorative: R6 is 2.43 vs 3.00."""
    d = DISTRICTS.get(code) or {}
    if use == "residential":
        return d.get("residential_narrow"), d.get("residential_wide")
    v = d.get(use)
    return v, v


def underlying_residential(codes):
    """A commercial overlay (C1-x / C2-x) mapped over a residence district takes
    the RESIDENTIAL FAR of the district beneath it — so 'C1-2/R3-2' is an R3-2
    for residential purposes. Picking the C district would be wrong by a lot."""
    res = [c for c in codes if c.startswith("R")]
    return res[0] if res else (codes[0] if codes else None)


def compute(decoded):
    """One decoded BSA resolution -> the as-of-right envelope it departed from.

    Returns a dict that ALWAYS says what happened: `values` when it computed,
    `refused` with a reason when it did not.
    """
    raw = decoded.get("district_stated") or (decoded.get("index") or {}).get("zoning_district")
    src = ("document" if decoded.get("district_stated") else "index")
    env = decoded.get("envelope") or {}
    la = (env.get("lot_area") or {})
    lot_area, la_page = la.get("value"), la.get("page")

    out = {"district_raw": raw, "district_source": src, "lot_area": lot_area,
           "lot_area_page": la_page, "values": {}, "refused": []}
    if not raw:
        out["refused"].append("no zoning district stated anywhere")
        return out
    codes, flags = normalise(raw)
    out["district_codes"], out["flags"] = codes, flags
    if not codes:
        out["refused"].append(f"district {raw!r} not in the ZR reference")
        return out
    if any(f.startswith("special_district") for f in flags):
        out["refused"].append(
            f"{[f for f in flags if f.startswith('special_district')][0]} — a "
            f"special district overrides the underlying bulk; computing from "
            f"the base district would be confidently wrong")
        return out
    if "multiple_districts" in flags and len(
            {underlying_residential(codes)}) > 1:
        out["refused"].append("split lot — no single district FAR applies")
        return out

    code = underlying_residential(codes)
    out["district_used"] = code
    narrow, wide = far_for(code, "residential")
    if narrow is None and wide is None:
        out["refused"].append(f"{code} has no residential FAR in the reference "
                              f"(likely a manufacturing or special district)")
    elif narrow == wide:
        out["values"]["far"] = {"value": narrow, "street": "same either way"}
    else:
        out["values"]["far_narrow_street"] = {"value": narrow, "street": "narrow"}
        out["values"]["far_wide_street"] = {"value": wide, "street": "wide"}
        out["refused"].append(
            f"narrow/wide street unknown — {code} is {narrow} FAR on a narrow "
            f"street and {wide} on a wide one; both recorded, neither asserted")
    for use in ("community_facility", "commercial"):
        v, _ = far_for(code, use)
        if v:
            out["values"][f"far_{use}"] = {"value": v, "street": "n/a"}

    if lot_area:
        for k, rec in list(out["values"].items()):
            if rec["value"]:
                out["values"][k]["floor_area"] = round(rec["value"] * lot_area, 2)
    else:
        out["refused"].append("no lot area stated — FAR known, floor area not")
    return out


def to_facts(decoded, base, run_id=None, emit=True):
    """Emit ONLY the unambiguous baseline. Ambiguity is recorded, not averaged."""
    out = []
    if not base.get("values"):
        return out
    # an unresolved narrow/wide split means there is no single baseline to state
    if any("narrow/wide" in r for r in base.get("refused", [])):
        return out
    cal = decoded.get("calendar")
    page = base.get("lot_area_page") or decoded.get("district_page") or 1
    bs, prov = _bbls(decoded)
    la, code = base.get("lot_area"), base.get("district_used")

    def add(f):
        f["bsa_parser"] = "baseline/1"
        f["bbl_provenance"] = prov
        out.append(f)
        if emit:
            sink.emit(f, run_id)

    for key, rec in base["values"].items():
        if not rec.get("value"):
            continue
        param = {"far": "far", "far_community_facility": "far_community_facility",
                 "far_commercial": "far_commercial"}.get(key)
        if not param:
            continue
        add(F.Fact("envelope_permitted", document_id=cal, page=page, bbls=bs,
                   source="BSA", happened=_iso(decoded.get("adopted")),
                   recorded=_iso(decoded.get("filed_cert")),
                   value=rec["value"], unit="ratio", parameter=param,
                   confidence="derived",
                   derivation=(f"district {base['district_raw']!r} read from the "
                               f"{base['district_source']} -> {code}; ZR district "
                               f"FAR table gives {rec['value']} for "
                               f"{param.replace('far_','') or 'residential'} use"),
                   verbatim=f"as-of-right {param} for {code}"))
        if rec.get("floor_area"):
            add(F.Fact("envelope_permitted", document_id=cal, page=page, bbls=bs,
                       source="BSA", happened=_iso(decoded.get("adopted")),
                       recorded=_iso(decoded.get("filed_cert")),
                       value=rec["floor_area"], unit="sf",
                       parameter=param.replace("far", "floor_area").replace(
                           "floor_area_", "") if param != "far" else "floor_area",
                       confidence="derived",
                       derivation=(f"{rec['value']} FAR ({code}, ZR district FAR "
                                   f"table) x {la:,.2f} sf zoning lot area read "
                                   f"on p{base.get('lot_area_page')} = "
                                   f"{rec['floor_area']:,.2f} sf"),
                       verbatim=f"as-of-right floor area for {code}"))
    return out


def _bbls(d):
    import bsa
    return bsa.bbls(d)


def _iso(s):
    import bsa
    return bsa._isoish(s)


def validate(decodes):
    """⚠ THE CHECK THAT DECIDES WHETHER ANY OF THIS IS TRUSTWORTHY.

    On the documents where the Board RECITED its own baseline, the computed one
    must reproduce it. That is a free, independent test of the arithmetic
    against the authority — and if it fails, the computed baselines everywhere
    else are wrong in the same way and must not be emitted.
    """
    rows = []
    for d in decodes:
        env = d.get("envelope") or {}
        stated = (env.get("permitted") or {})
        if not stated:
            continue
        b = compute(d)
        for param in ("far", "floor_area"):
            s = stated.get(param)
            if not s:
                continue
            got = None
            v = b["values"].get("far")
            if v:
                got = v["value"] if param == "far" else v.get("floor_area")
            if got is None:
                continue
            ok = abs(got - s["value"]) <= max(0.02, s["value"] * 0.02)
            rows.append({"calendar": d.get("calendar"), "parameter": param,
                         "stated": s["value"], "computed": got,
                         "district": b.get("district_used"),
                         "verdict": "MATCH" if ok else "DIVERGE"})
    return rows


if __name__ == "__main__":
    import bsa
    decodes = [json.loads(l) for l in
               open("bsa_decodes.jsonl", encoding="utf-8")]
    print(f"{len(decodes):,} decoded resolutions on disk\n")
    v = validate(decodes)
    c = Counter(r["verdict"] for r in v)
    print(f"VALIDATION against the Board's own recited baseline: {dict(c)}")
    for r in v[:12]:
        print(f"   {r['verdict']:<8} {r['calendar']:<14} {r['parameter']:<11}"
              f" stated {r['stated']:>12,.2f}  computed {r['computed']:>12,.2f}"
              f"  [{r['district']}]")
    print()
    ref = Counter()
    got = 0
    for d in decodes:
        b = compute(d)
        if b["values"] and not any("narrow/wide" in x for x in b["refused"]):
            got += 1
        for r in b["refused"]:
            ref[r.split(" —")[0].split(" (")[0][:60]] += 1
    print(f"baseline computable on {got:,} of {len(decodes):,} decoded resolutions")
    print("refusals, by reason:")
    for k, n in ref.most_common(10):
        print(f"   {n:>6,}  {k}")
