"""DID THE VLM PUT EACH ARTIFACT IN THE RIGHT TABLE? Scored against the hand key.

    python route_score.py --doc FT_1680008647768

⚠ WHAT THIS MEASURES THAT NOTHING ELSE DOES. Every score in this project asks
"was the value READ". This asks "was it PLACED" — whether `$4,000,000` landed in
`amount` and `REEL 586` in `recording_stamp`. Reading and placing are different
jobs done by different channels, and a pipeline that reads perfectly into the
wrong table is worthless downstream.

⚠ THREE OUTCOMES, NEVER TWO, BECAUSE THE FAILURES BELONG TO DIFFERENT CHANNELS.

    NOT IN OCR   no line contains the artifact at all. That is OCR's miss and
                 the router never had a chance — scoring it against the VLM
                 would blame the wrong channel.
    MISPLACED    the line exists and carries a region that is not the expected
                 one. This is the router's error, and the only one it owns.
    PLACED       expected region.

⚠ THE EXPECTED-REGION MAP IS AUTHORED BY ME AND IS THE WEAK LINK IN THIS FILE.
It is derived from the artifact `id` names in the keys, not from any model output,
but it is still a judgement and it is stated here rather than buried. Any id NOT in
the map is EXCLUDED from both numerator and denominator and reported as `unmapped` —
the same rule score.py applies to ambiguous artifacts. Guessing a mapping to raise a
number would make this measure itself.

⚠ AND AN ID MAY HAVE MORE THAN ONE HONEST HOME. `year` sits in the parties block on
a mortgage face but in the stamp on a backer, so the map holds a SET and either is
correct. A set of one is a claim; a set of everything would be no measure at all, so
sets are kept small and deliberate.
"""
from __future__ import annotations

import argparse, collections, json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
DEC = HERE.parent
sys.path.insert(0, str(HERE))

import score as S

KEYS = {"FT_1680008647768": "answer_key_testdoc.json",
        "BK_6730047100023": "answer_key_bookdoc.json",
        "2015022400608001": "answer_key_moderndoc.json"}

# ── the authored map. id -> the region(s) that would be CORRECT ──────────────
EXPECT = {}


def _m(regions, *ids):
    for i in ids:
        EXPECT[i] = set(regions)


_m(["recording_stamp"], "reel", "reel_page", "rec_book", "rec_page", "rec_tax",
   "rec_date", "register", "register_co", "instrument", "recorded")
_m(["parties"], "mortgagor", "mortgagee", "mortgagor_addr", "mortgagee_addr",
   "mortgagor_form", "partnership", "gen_partner", "to_party", "bank", "addr",
   "agency", "alias", "alias_phrase", "grantor", "grantee")
_m(["parties", "recording_stamp"], "doc_type", "year")
_m(["amount"], "amount_words", "amount_figs", "loan_no")
_m(["legal_description"], "begin", "street", "avenue", "borough", "county",
   "block", "lot", "dim_ns", "dim_ew", "metes")
_m(["schedule", "legal_description"], "schedule_a", "schedule")
_m(["notary"], "notary", "notary_no", "ack_day", "ack_month", "ack_year",
   "county_ack")
_m(["signature"], "signer1", "signer2")
_m(["covenants"], "rpl254", "receiver", "warrants", "assign_rents", "lien_law",
   "pmm", "simul", "nha", "escrow", "rider", "rider_tenant")


def line_hit(text, art):
    return S.found(S.norm(text), art) or S.pointed(S.norm(text), art)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--show", type=int, default=14)
    a = ap.parse_args()

    key = json.loads((DEC / KEYS[a.doc]).read_text(encoding="utf-8"))
    rdir = HERE / "out" / "_route" / a.doc
    routed = sorted(p for p in rdir.glob("p*.json")
                    if not p.name.endswith(".BEFORE.json"))
    if not routed:
        print(f"  no routed pages under {rdir}")
        return 1

    tot = collections.Counter()
    wrong, unmapped_ids = [], collections.Counter()
    conf = collections.Counter()          # (expected, got) -> n
    per_page = []
    for rf in routed:
        r = json.loads(rf.read_text(encoding="utf-8"))
        pg = r["page"]
        blk = key.get(pg + ".png") or {}
        arts = [x for x in (blk.get("artifacts") or [])
                if x.get("tier") == "CRITICAL" and not x.get("ambiguous")]
        if not arts:
            continue
        reg_of = {}
        for reg, ls in r["placed"].items():
            for i in ls:
                reg_of[i] = reg
        lines = {l["i"]: l["text"] for l in r["lines"]}
        p = collections.Counter()
        for art in arts:
            aid = art.get("id", "?")
            if aid not in EXPECT:
                unmapped_ids[aid] += 1
                p["unmapped"] += 1
                continue
            p["scored"] += 1
            hits = [i for i, t in lines.items() if line_hit(t, art)]
            if not hits:
                p["not_in_ocr"] += 1        # OCR's miss, not the router's
                continue
            got = {reg_of.get(i) for i in hits}
            want = EXPECT[aid]
            if got & want:
                p["placed"] += 1
                continue
            if got == {None}:
                p["unplaced_line"] += 1     # the router left that line UNREAD
                continue
            p["misplaced"] += 1
            g = sorted(x for x in got if x)
            wrong.append((pg, aid, sorted(want), g,
                          lines[hits[0]][:52], art.get("value", "")[:34]))
            for x in g:
                conf[(sorted(want)[0], x)] += 1
        tot.update(p)
        per_page.append((pg, p))

    print(f"PLACEMENT SCORE — {a.doc} · {len(per_page)} routed page(s) with keyed "
          f"CRITICAL artifacts\n")
    print(f"  {'page':<7}{'scored':>7}{'placed':>8}{'misplc':>8}"
          f"{'noOCR':>7}{'unpl':>6}{'unmapped':>10}")
    for pg, p in per_page:
        print(f"  {pg:<7}{p['scored']:>7}{p['placed']:>8}{p['misplaced']:>8}"
              f"{p['not_in_ocr']:>7}{p['unplaced_line']:>6}{p['unmapped']:>10}")
    n = tot["scored"]
    if not n:
        print("  nothing scorable")
        return 1
    print(f"  {'TOTAL':<7}{n:>7}{tot['placed']:>8}{tot['misplaced']:>8}"
          f"{tot['not_in_ocr']:>7}{tot['unplaced_line']:>6}{tot['unmapped']:>10}")

    reach = n - tot["not_in_ocr"]
    print(f"\n  placed / scored                 {tot['placed']}/{n}  "
          f"{tot['placed']/n:.1%}")
    if reach:
        print(f"  placed / REACHABLE (in OCR)     {tot['placed']}/{reach}  "
              f"{tot['placed']/reach:.1%}   <- what the ROUTER owns")
    print(f"  ⚠ excluded, id not in the authored map: {tot['unmapped']}")
    if unmapped_ids:
        print("    " + " ".join(f"{k}({v})" for k, v in unmapped_ids.most_common(12)))

    if wrong:
        print(f"\n  MISPLACED — every one, so the map can be argued with:")
        for pg, aid, want, got, txt, val in wrong[:a.show]:
            print(f"    {pg} {aid:<14} want={'/'.join(want):<24} got={'/'.join(got)}")
            print(f"        \"{val}\"  in line: {txt}")
        if len(wrong) > a.show:
            print(f"    … {len(wrong)-a.show} more")

    json.dump({"doc": a.doc, "pages": len(per_page), "totals": dict(tot),
               "placed_over_reachable": (tot["placed"] / reach) if reach else None,
               "unmapped_ids": dict(unmapped_ids),
               "misplaced": [{"page": p, "id": i, "want": w, "got": g,
                              "line": t, "value": v} for p, i, w, g, t, v in wrong],
               "confusions": {f"{k[0]}->{k[1]}": v for k, v in conf.most_common()}},
              open(HERE / f"_route_score_{a.doc}.json", "w"), indent=1)
    print(f"\nwrote _route_score_{a.doc}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
