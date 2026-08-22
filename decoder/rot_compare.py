"""UPRIGHT vs ROTATED — does rotation buy enough text to be worth the time?

    python rot_compare.py

⚠ CHARS ALONE CANNOT ANSWER THIS. More text is not automatically better: the
Arc iGPU produced a config that was 3x slower AND read half the characters,
while a model can emit fluent invention that scores well on any length metric.
So this reports THREE things per document — characters, trigger hits, and
agreement — because they can move in opposite directions.

⚠ THE REAL QUESTION IS TRIGGERS, NOT VOLUME. This sweep exists to learn which
operative language appears in a document type. A trigger that never fires looks
identical whether the phrase is absent or the page was never read — so if
rotation lights up `envelope` or `ownership` where upright did not, that is the
whole answer regardless of the character count.

⚠ MEASURED PRIOR ON THE KEYED BENCH (resolve/_score_*.json):
    film  upright OCR 0.475 -> rotated 0.945
    book  upright OCR 0.513 -> rotated 0.880
    digital        1.000    -> 1.000
So expect a large win on film/book pages and NO win on digital. If a document
shows no difference, that is evidence about its ERA, which is itself useful.
"""
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

TRIGGERS = {
    "ownership": [r"do(?:es)?\s+hereby\s+grant", r"grant,?\s+bargain",
                  r"sell\s+and\s+convey", r"remise,?\s+release", r"quitclaim"],
    "financing": [r"to\s+secure\s+the\s+payment", r"principal\s+sum\s+of",
                  r"releases?\s+and\s+discharges?", r"do(?:es)?\s+hereby\s+assign"],
    "envelope": [r"development\s+rights", r"floor\s+area\s+ratio",
                 r"unused\s+development", r"transferable\s+development",
                 r"zoning\s+lot"],
    "encumbrance": [r"subject\s+to", r"excepting\s+and\s+reserving",
                    r"together\s+with\s+all", r"easement",
                    r"covenants?\s+running\s+with"],
    "boundary": [r"\bthence\b", r"point\s+or\s+place\s+of\s+beginning",
                 r"feet\s+to\s+a\s+point"],
    "cover_page": [r"recording\s+and\s+endorsement", r"document\s+type:?",
                   r"mortgage\s+amount:?", r"fees\s+and\s+taxes", r"\bCRFN\b"],
}
TRIG = {f: [re.compile(p, re.I) for p in ps] for f, ps in TRIGGERS.items()}


def load(d):
    out = {}
    p = HERE / d
    if not p.exists():
        return out
    for f in sorted(p.glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        out[rec["doc_id"]] = " ".join(
            pg.get("accepted_text") or "" for pg in rec.get("pages") or [])
    return out


def hits(text):
    return {f: sum(len(p.findall(text)) for p in pats) for f, pats in TRIG.items()}


def main():
    up, rot = load("devr_text"), load("devr_text_rot90")
    if not up or not rot:
        print(f"  upright docs {len(up)} · rotated docs {len(rot)} — "
              f"both passes must finish first")
        return 1

    common = sorted(set(up) & set(rot))
    print(f"UPRIGHT vs ROTATED — {len(common)} DEVR documents\n")

    tu = tr = 0
    hu = {f: 0 for f in TRIG}
    hr = {f: 0 for f in TRIG}
    better = worse = same = 0
    rows = []
    for d in common:
        a, b = up[d], rot[d]
        tu += len(a); tr += len(b)
        ha, hb = hits(a), hits(b)
        for f in TRIG:
            hu[f] += ha[f]; hr[f] += hb[f]
        delta = (len(b) - len(a)) / max(len(a), 1) * 100
        if delta > 10: better += 1
        elif delta < -10: worse += 1
        else: same += 1
        rows.append((d, len(a), len(b), delta))

    print("  PER DOCUMENT — characters")
    for d, a, b, delta in rows:
        mark = "  ROT+" if delta > 10 else ("  ROT-" if delta < -10 else "      ")
        print(f"    {d:<22} {a:>7,} -> {b:>7,}  {delta:+6.1f}%{mark}")

    print(f"\n  rotation better (>+10%)  {better}")
    print(f"  no real change           {same}")
    print(f"  rotation worse (<-10%)   {worse}")
    print(f"\n  TOTAL CHARS   upright {tu:,}   rotated {tr:,}   "
          f"{(tr-tu)/max(tu,1)*100:+.1f}%")

    print(f"\n  TRIGGER HITS — the thing that actually matters")
    print(f"    {'function':<14} {'upright':>9} {'rotated':>9}   verdict")
    for f in TRIG:
        a, b = hu[f], hr[f]
        if a == 0 and b == 0:
            v = "⚠ NEVER FIRES — untested either way"
        elif a == 0:
            v = "⚠ ROTATION UNLOCKED IT"
        elif b == 0:
            v = "⚠ rotation lost it"
        else:
            v = f"{(b-a)/a*100:+.0f}%"
        print(f"    {f:<14} {a:>9,} {b:>9,}   {v}")

    print("\n  ⚠ 25 documents of ONE type. A trigger that never fires here has "
          "been\n    tested on DEVR alone — that is not evidence it is wrong.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
