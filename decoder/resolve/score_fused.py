"""SCORE THE SYSTEM, NOT THE ENGINES. The number that has never existed.

    python score_fused.py
    python score_fused.py --tier CRITICAL

⚠ EVERY ACCURACY FIGURE THIS PROJECT HAS IS PER-ENGINE. Qwen 98.8%, Paddle
96.5%, the whole scoreboard - each one measures a MODEL. Nothing has ever
measured what the PIPELINE outputs, which is the only number a downstream stage
actually consumes. This file computes it, using score.py's own normaliser and
artifact matcher so the comparison is like-for-like rather than a new metric
that flatters the new code.

⚠ THREE NUMBERS, AND REPORTING ONLY ONE WOULD MISLEAD IN EITHER DIRECTION.

    ACCEPTED   what both channels agreed on, verbatim. High trust, and it is
               the only text the system currently ASSERTS. Anything disputed
               was replaced with [UNRESOLVED], so a value the readers fought
               over is a MISS here even when one of them read it perfectly.

    +ESCALATE  accepted, plus the candidate readings from every open run. This
               is the CEILING: what the system could reach if a crop pass
               resolved every dispute correctly. It is not an achieved score
               and must never be quoted as one.

    ENGINE     each channel alone on the same pages, from the same key.

⚠ THE GAP BETWEEN ACCEPTED AND THE BEST ENGINE IS THE PRICE OF NOT GUESSING,
AND IT IS SUPPOSED TO BE POSITIVE. A single engine "hits" an artifact whenever
its own reading happens to be right, including where it was overruled by
nothing and checked by nothing. Fusion refuses to assert a contested value, so
it will score LOWER on recall and that is the design working, not failing. The
question this file answers is HOW MUCH lower - because if the price is large,
the thresholds in fuse.py are wrong, and if the ceiling is not above the best
engine, the second channel is not paying for itself.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
BAKE = HERE.parent / "bakeoff"
DEC = HERE.parent
sys.path.insert(0, str(BAKE))

import score as S   # reuse THE SAME normaliser and matcher the engines faced

EV = HERE / "_evidence"
KEYS = [("FT_1680008647768", "answer_key_testdoc.json", "film", 0.255),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book", 0.040),
        ("2015022400608001", "answer_key_moderndoc.json", "digital", 0.705)]


def page_arts(key, page, tier=None):
    blk = key.get(page) or key.get(page.replace(".png", "")) or {}
    arts = blk.get("artifacts") or []
    out = []
    for a in arts:
        if tier and a.get("tier") != tier:
            continue
        # ⚠ score.py excludes ambiguous artifacts from BOTH numerator and
        # denominator; scoring an engine on something no human could read
        # measures luck. Same rule here or the numbers are not comparable.
        if a.get("ambiguous") or a.get("tier") == "AMBIGUOUS":
            continue
        out.append(a)
    return out


def hit(hay, art):
    """TRANSCRIBED or POINTED, exactly as score.py defines them."""
    if S.found(hay, art):
        return "transcribed"
    if S.pointed(hay, art):
        return "pointed"
    return "miss"


def engine_text(engine, doc, page_stem):
    for name in (f"{page_stem}.txt", f"{page_stem}.png.txt"):
        f = BAKE / "out" / engine / doc / name
        if f.exists() and f.stat().st_size > 0:
            return f.read_text(encoding="utf-8", errors="replace")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="CRITICAL",
                    help="CRITICAL | MATERIAL | ROUTINE | ALL")
    # ⚠ MACHINE-READABLE OUTPUT EXISTS BECAUSE PARSING THE HUMAN TABLE BROKE.
    # The per-document rows and the corpus-weighted footer have different
    # column counts, so a positional parse read the footer as a document and
    # crashed. A caller that needs these numbers gets them as data.
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    a = ap.parse_args()
    tier = None if a.tier.upper() == "ALL" else a.tier.upper()
    say = (lambda *x, **k: None) if a.json else print

    say(f"  scoring tier={a.tier}   matcher=score.py (found + pointed)\n")
    grand = {}
    for doc, keyfile, cls, share in KEYS:
        recf = EV / f"{doc}.json"
        kf = DEC / keyfile
        if not recf.exists() or not kf.exists():
            say(f"  {doc:20} no evidence record or key - SKIPPED")
            continue
        rec = json.loads(recf.read_text(encoding="utf-8"))
        key = json.loads(kf.read_text(encoding="utf-8"))
        vlm, ocr = rec["channels"]["vlm"], rec["channels"]["ocr"]

        tot = {"accepted": 0, "ceiling": 0, vlm: 0, ocr: 0}
        # ⚠ COVERAGE IS NOT RECALL, AND CONFLATING THEM UNDERSTATED EVERY
        # ENGINE. A page an engine has no file for was being counted as a page
        # it read and failed. ppv6 has no p007 for the book doc — 18 of its 24
        # "misses" were a missing file, and it scored 71.1% instead of the
        # 90.8% it reads on pages it actually has. Denominators are now kept
        # per engine, and a missing page is reported as missing.
        seen = {vlm: 0, ocr: 0}
        n = 0
        # ⚠ SCORED ONLY ON PAGES THE KEY ACTUALLY COVERS. answer_key_moderndoc
        # says "PARTIAL KEY - 4 of 9 pages hand-read"; counting the unkeyed
        # pages as zero would invent a failure.
        for p in rec["pages"]:
            stem = p["page"]
            arts = page_arts(key, stem + ".png", tier)
            if not arts:
                continue
            n += len(arts)
            accepted = S.norm(p["accepted_text"])
            extra = " ".join(str(r.get(vlm) or "") + " " + str(r.get(ocr) or "")
                             for r in p["runs"] if r["status"] != "agreed")
            ceiling = S.norm(p["accepted_text"] + " " + extra)
            raw = {c: engine_text(c, doc, stem) for c in (vlm, ocr)}
            et = {c: S.norm(raw[c] or "") for c in (vlm, ocr)}
            for c in (vlm, ocr):
                if raw[c] is not None:
                    seen[c] += len(arts)
            for art in arts:
                if hit(accepted, art) != "miss":
                    tot["accepted"] += 1
                if hit(ceiling, art) != "miss":
                    tot["ceiling"] += 1
                for c in (vlm, ocr):
                    if et[c] and hit(et[c], art) != "miss":
                        tot[c] += 1
        if not n:
            say(f"  {doc:20} no {a.tier} artifacts on fused pages - SKIPPED")
            continue
        grand[doc] = (tot, n, cls, share, vlm, ocr, seen)
        say(f"  {doc}  ({cls}, {n} {a.tier} artifacts on keyed pages)")
        for c in (vlm, ocr):
            sn = seen[c]
            gap = (f"  ⚠ {n - sn} artifact(s) on pages this engine has NO FILE "
                   f"for — missing, not misread" if sn < n else "")
            r = f"{tot[c]/sn:>6.1%}" if sn else "     —"
            say(f"    {c:22} {tot[c]:>3}/{sn:<3} {r}   engine alone, "
                f"pages it has{gap}")
        say(f"    {'FUSED accepted':22} {tot['accepted']:>3}/{n}  "
              f"{tot['accepted']/n:>6.1%}   asserted, both channels agreed")
        say(f"    {'FUSED + escalation':22} {tot['ceiling']:>3}/{n}  "
              f"{tot['ceiling']/n:>6.1%}   CEILING if crops resolve perfectly")
        say()

    if not grand:
        return
    say("  " + "=" * 70)
    say("  CORPUS-WEIGHTED (film 25.5 / book 4.0 / digital 70.5)")
    # ⚠ WEIGHTED BY CORPUS SHARE, NOT BY THE SAMPLE'S OWN MIX. The sample is
    # 81% historical; blending on it would triple the apparent difficulty.
    for label in ["engine_vlm", "engine_ocr", "accepted", "ceiling"]:
        num = den = 0.0
        for doc, (tot, n, cls, share, vlm, ocr, seen) in grand.items():
            k = {"engine_vlm": vlm, "engine_ocr": ocr}.get(label, label)
            # ⚠ AN ENGINE IS RATED ON WHAT IT WAS SHOWN. Pages it has no file
            # for belong in a coverage report, not in its recall.
            d = seen[k] if label in ("engine_vlm", "engine_ocr") else n
            if not d:
                continue
            num += share * (tot[k] / d)
            den += share
        nm = {"engine_vlm": "best VLM alone", "engine_ocr": "OCR alone",
              "accepted": "FUSED accepted", "ceiling": "FUSED + escalation"}[label]
        say(f"    {nm:24} {num/den:>6.1%}")
    say()
    say("  Read the gap, not the rank: accepted BELOW the best engine is the")
    say("  price of refusing to assert a contested value. The ceiling ABOVE")
    say("  the best engine is what the second channel and the crops buy.")

    if a.json:
        out = {"tier": a.tier, "docs": {}, "weighted": {}}
        for doc, (tot, n, cls, share, vlm, ocr, seen) in grand.items():
            out["docs"][cls] = {"doc": doc, "n": n,
                                "vlm": tot[vlm] / n, "ocr": tot[ocr] / n,
                                "accepted": tot["accepted"] / n,
                                "ceiling": tot["ceiling"] / n}
        for label in ("accepted", "ceiling"):
            num = den = 0.0
            for doc, (tot, n, cls, share, vlm, ocr, seen) in grand.items():
                num += share * (tot[label] / n); den += share
            out["weighted"][label] = num / den
        print(json.dumps(out))


if __name__ == "__main__":
    main()
