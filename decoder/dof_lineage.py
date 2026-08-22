"""DOF lot lineage — published, not inferred.

WHAT THIS REPLACES
    The spine has been INFERRING lot lineage by diffing PLUTO vintages, and
    condo unit lots by chaining a document's "f/k/a Lot 149" recital through
    PLUTO's appbbl. DOF publishes both outright.

    Socrata's `smk3-tmxj` is a blob download, not an API. The queryable copy is
    DOF's own ArcGIS service `DTM_ETL_DAILY_view` — a DAILY ETL, which also suits
    the monitoring cadence.

THE DIGITAL ALTERATION BOOK (DAB_*)
    DAB_LOT        BBL + Lot_Action (Dropped / Affected / Added) + TRANS_NUM
    DAB_BOOK_HEADER TRANS_NUM + Change_Date + Change_Type + Auth_for_Change
    77,904 entries, 2008-05-20 .. 2026-08-04.

    `Auth_for_Change` is free text but it CITES THE INSTRUMENT — CRFNs, deed
    dates, surveyor and survey date, DOB job numbers. That makes it a two-way
    join between a parcel's lineage and the documents this decoder reads:
    given a lot change, find the instrument; given an instrument, find what it
    did to the map.

WHY A CURRENT-STATE QUERY IS NOT ENOUGH
    MN 1540 lot 3 and lot 9003 are both absent from today's tax map. From that
    alone the conclusion drawn here was "the air lot was never minted" — WRONG.
    The book shows lot 9003 created 2012-12-21 under ZLDA CRFN 2012000483179
    (the very document decoded as 2012120600575002), merged back into lot 3 on
    2017-10-26, and lot 3 itself dropped the same day in a lot merger.
    **Absence from today's map does not mean never created.**
"""
import json, re, urllib.parse, urllib.request

SVC = ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services"
       "/DTM_ETL_DAILY_view/FeatureServer")
LAYERS = {"tax_lot": 0, "air_lot": 2, "condo": 3, "condo_unit": 4,
          "reuc_lot": 5, "sub_lot": 6, "dab_lot": 15, "dab_header": 9}


def _query(layer, where, out="*", limit=200, order=None):
    p = {"where": where, "outFields": out, "resultRecordCount": limit, "f": "json"}
    if order:
        p["orderByFields"] = order
    url = f"{SVC}/{LAYERS[layer]}/query?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=90) as f:
        return [feat["attributes"] for feat in (json.load(f).get("features") or [])]


CRFN_RE = re.compile(r"\b(\d{4}0{2}\d{7})\b")          # CRFN: yyyy + 9 digits
DOC_RE = re.compile(r"\b(\d{16})\b")                    # ACRIS document id
JOB_RE = re.compile(r"\b([A-Z]?\d{6,9})\s*(?=$|[^\d])") # DOB job / PW1 number


def cited_instruments(auth_text):
    """Pull the instrument citations out of Auth_for_Change free text.

    The field is prose, but it is prose written by a clerk recording WHY the map
    changed, and it names the paper: CRFNs, deed dates, the surveyor and survey
    date, DOB job numbers. Extracting the identifiers turns lineage into a join.
    """
    t = auth_text or ""
    out = {"crfns": sorted(set(CRFN_RE.findall(t))),
           "doc_ids": sorted(set(DOC_RE.findall(t))),
           "survey_dates": sorted(set(re.findall(r"Survey Date:\s*([\d/]{8,10})", t, re.I))),
           "surveyors": [s.strip() for s in re.findall(r"Survey by:\s*([^\n]{3,60}?)\s{2,}", t)],
           # ⚠ WIDENED 2026-08-06 after measuring all 77,930 non-empty
           # Auth_for_Change texts. The old pattern was r"PW\s*1\s*#\s*(\d+)" —
           # it required the literal "PW1 #", and the clerks do not write it that
           # way consistently:
           #     "PW 1 # 320625383, 321196228"   "PW1: 220580556"
           #     "DOB NB No. s 321531115 , 321531124"
           #   old pattern            1,658 / 77,930   2.13% of texts
           #   bare 9-digit boro-lead 6,068 / 77,930   7.79%   (3.7x)
           # And the bare form is nearly clean: of 3,710 distinct candidates,
           # 3,648 resolve to a real job in ic3t-wcy2 — 98.3%. The old pattern
           # was finding only 27.6% of the citations that actually resolve.
           # ⚠ The ~1.7% that do not resolve are not necessarily junk:
           # ic3t-wcy2 has a hard floor at 2000-01-01, so a pre-2000 job number
           # is real and simply absent from that feed. Check ipu4-2q9a /
           # bty7-2jhb before calling a non-resolving number false.
           "dob_jobs": sorted(set(re.findall(r"\b([1-5]\d{8})\b", t))),
           "dob_now_jobs": sorted(set(re.findall(r"\b([BMQSX]\d{8})\b", t))),
           "instrument_kinds": sorted({k.lower() for k in
                                       re.findall(r"\b(Zelda|ZLDA|Deed|Easement|Declaration|"
                                                  r"Apportionment|Merger)\b", t, re.I)})}
    # "Zelda" is DOF's own spelling of ZLDA — normalise so a search finds both
    if "zelda" in out["instrument_kinds"]:
        out["instrument_kinds"] = sorted(set(out["instrument_kinds"]) - {"zelda"} | {"zlda"})
    return out


def history(bbl):
    """Everything DOF's alteration book records about one lot, oldest first.

    Returns [] for a lot the book has never touched — which means "no recorded
    alteration since 2008", NOT "no history". The book starts 2008-05-20.
    """
    acts = {}
    for r in _query("dab_lot", f"BBL='{bbl}'"):
        acts.setdefault(r["TRANS_NUM"], []).append(r.get("Lot_Action"))
    rows = _query("dab_header", f"BBL='{bbl}'", order="Change_Date")
    seen, out = set(), []
    for h in rows:
        tn = h.get("TRANS_NUM")
        if tn in seen:
            continue
        seen.add(tn)
        auth = h.get("Auth_for_Change") or ""
        out.append({
            "bbl": bbl, "trans_num": tn, "change_date": h.get("Change_Date"),
            "change_type": h.get("Change_Type"),
            "lot_actions": sorted(set(acts.get(tn, []))),
            "new_block": h.get("Block_N"), "new_lot": h.get("Lot_N"),
            "authority": auth, "cites": cited_instruments(auth)})
    # a transaction can name the lot in DAB_LOT without a header row for it
    for tn, actions in acts.items():
        if tn not in seen:
            out.append({"bbl": bbl, "trans_num": tn, "change_date": None,
                        "change_type": None, "lot_actions": sorted(set(actions)),
                        "authority": None, "cites": None,
                        "note": "lot action recorded with no header row for this BBL"})
    return sorted(out, key=lambda r: (r["change_date"] or "", r["trans_num"]))


def condo_units(base_bbl=None, unit_bbl=None):
    """Unit lot <-> parent, PUBLISHED. Replaces chaining an 'f/k/a Lot N'
    recital through PLUTO's appbbl.

    Block-wide resolution is unsafe: MN block 1446 carries THREE condos
    (514/lot 35, 1521/lot 41, 950/lot 149), so resolving by block would sweep in
    49 unrelated unit lots. Always key on the base BBL or the unit BBL.
    """
    if base_bbl:
        return _query("condo_unit", f"CONDO_BASE_BBL='{base_bbl}'", limit=2000)
    if unit_bbl:
        return _query("condo_unit", f"UNIT_BBL='{unit_bbl}'")
    raise ValueError("give base_bbl or unit_bbl — a block is not a key here")


def volumes(parent_bbl):
    """Air lots and subterranean lots carved off a parent — the vertical
    counterpart to a subdivision, and the map's record of the airspace parcels
    this decoder meets in ZLDAs."""
    return {"air": _query("air_lot", f"PARENT_BBL='{parent_bbl}'"),
            "sub": _query("sub_lot", f"PARENT_BBL='{parent_bbl}'")}


def by_instrument(crfn):
    """Reverse join: which lots did this recorded instrument change?

    Auth_for_Change is free text, so this is a LIKE scan — matches are evidence,
    a non-match is not proof the instrument changed nothing.
    """
    rows = _query("dab_header", f"Auth_for_Change LIKE '%{crfn}%'", limit=200)
    return [{"bbl": r.get("BBL"), "change_date": r.get("Change_Date"),
             "change_type": r.get("Change_Type"), "trans_num": r.get("TRANS_NUM"),
             "authority": r.get("Auth_for_Change")} for r in rows]


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "1015400003"
    print(f"DOF alteration-book history for {target}\n")
    for h in history(target):
        print(f"  {h['change_date'] or '(no date)'}  trans {h['trans_num']}  "
              f"{h['change_type'] or ''}  actions={h['lot_actions']}")
        if h.get("authority"):
            print(f"      {h['authority'][:150]}")
        c = h.get("cites") or {}
        cited = {k: v for k, v in c.items() if v}
        if cited:
            print(f"      cites: {cited}")
    v = volumes(target)
    print(f"\n  air lots: {len(v['air'])}   subterranean lots: {len(v['sub'])}")

def history_batch(bbls, chunk=60):
    """history() for many BBLs in a handful of requests instead of two each.

    151 lots queried one at a time is ~300 requests. Batched with `BBL IN (...)`
    it is ~6. Same answer, and the difference between a courteous client and one
    that gets throttled — a lesson learned the expensive way on ACRIS the same
    day this was written.
    """
    bbls = [str(int(b)) for b in bbls]
    acts, headers = {}, {}
    for i in range(0, len(bbls), chunk):
        part = bbls[i:i + chunk]
        where = "BBL IN (" + ",".join(f"'{b}'" for b in part) + ")"
        for r in _query("dab_lot", where, limit=4000):
            acts.setdefault(r["BBL"], {}).setdefault(r["TRANS_NUM"], []).append(
                r.get("Lot_Action"))
        for h in _query("dab_header", where, limit=4000, order="Change_Date"):
            headers.setdefault(h["BBL"], []).append(h)

    out = {}
    for b in bbls:
        rows, seen = [], set()
        for h in headers.get(b, []):
            tn = h.get("TRANS_NUM")
            if tn in seen:
                continue
            seen.add(tn)
            auth = h.get("Auth_for_Change") or ""
            rows.append({"bbl": b, "trans_num": tn, "change_date": h.get("Change_Date"),
                         "change_type": h.get("Change_Type"),
                         "lot_actions": sorted(set((acts.get(b) or {}).get(tn, []))),
                         "new_block": h.get("Block_N"), "new_lot": h.get("Lot_N"),
                         "authority": auth, "cites": cited_instruments(auth)})
        for tn, actions in (acts.get(b) or {}).items():
            if tn not in seen:
                rows.append({"bbl": b, "trans_num": tn, "change_date": None,
                             "change_type": None, "lot_actions": sorted(set(actions)),
                             "authority": None, "cites": None,
                             "note": "lot action with no header row for this BBL"})
        out[b] = sorted(rows, key=lambda r: (r["change_date"] or "", r["trans_num"]))
    return out
