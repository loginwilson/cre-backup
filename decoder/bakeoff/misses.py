"""WHAT EACH ENGINE ACTUALLY MISSED. Not how many - which ones, and whether fixable.

    python misses.py                      # every CRITICAL miss, grouped
    python misses.py --engine ppv6*       # one engine
    python misses.py --shared             # only artifacts EVERY engine missed

⚠ A COUNT DOES NOT TELL YOU WHETHER A GAP IS CLOSEABLE. "PP-OCRv6 scores 83% on
book" is an invitation to guess. The 14 artifacts behind that number are either
(a) POINTED - the engine put a box on the right region and got characters wrong,
which a second look repairs, or (b) ABSENT - it never surfaced the region at
all, which no re-read repairs because there is nothing to re-read. Those two
demand opposite fixes and the blended score cannot distinguish them.

⚠ AND AN ARTIFACT EVERY ENGINE MISSES IS A DIFFERENT FINDING ENTIRELY. If all
four independent engines miss the same field, the likely cause is the PAGE (ink
gone, stamp overlapping text, the region cropped at scan time) - not the
engines. Those are the candidates for UNRESOLVED / SOURCE ILLEGIBLE, and no
amount of configuration recovers them. Separating them is the difference between
a fixable gap and a floor.

⚠ OPEN vs CLOSED VOCABULARY decides whether a repair is even legitimate. A
doc_type drawn from a list we hold can be repaired from context. A name, a date,
a reel number cannot - correcting those is invention. This report labels the
artifact so the distinction survives into whatever fix follows.
"""
import argparse
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import score as S

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
DOCS = [("FT_1680008647768", "answer_key_testdoc.json", "film"),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book"),
        ("2015022400608001", "answer_key_moderndoc.json", "digital")]
ENGINES = ["tesseract", "rapidpool", "qwen", "ppv6*"]


def text(eng, doc, page):
    """ppv6* = the deployable config: rotated where a rotated run exists,
    upright otherwise. Anything else reads its own directory."""
    tags = ["ppv6-rot", "ppv6"] if eng == "ppv6*" else [eng]
    for t in tags:
        d = OUT / t / doc
        if not d.exists():
            continue
        stem = page[:-4] if page.endswith(".png") else page
        fs = sorted(d.glob(stem + "*.txt"))
        if fs:
            return " ".join(f.read_text(encoding="utf-8", errors="replace")
                            for f in fs)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=None)
    ap.add_argument("--shared", action="store_true")
    a = ap.parse_args()
    engines = [a.engine] if a.engine else ENGINES

    rows = []          # (label, page, artifact, {engine: status})
    for doc, kf, label in DOCS:
        key = {k: v for k, v in
               json.loads((HERE / "keys" / kf).read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        for page in sorted(key):
            hay = {e: S.norm(text(e, doc, page) or "") for e in ENGINES}
            if any(text(e, doc, page) is None for e in ENGINES):
                continue
            for art in key[page]["artifacts"]:
                if art["tier"] != "CRITICAL":
                    continue
                st = {}
                for e in ENGINES:
                    if S.found(hay[e], art):
                        st[e] = "ok"
                    elif S.pointed(hay[e], art):
                        st[e] = "POINTED"
                    else:
                        st[e] = "ABSENT"
                if any(v != "ok" for v in st.values()):
                    rows.append((label, page, art, st))

    shared = [r for r in rows if all(v != "ok" for v in r[3].values())]

    print(f"  {len(rows)} CRITICAL artifacts missed by at least one engine")
    print(f"  {len(shared)} missed by ALL {len(ENGINES)} - page-level, not engine-level\n")

    print("  ── MISSED BY EVERY ENGINE (candidates for SOURCE ILLEGIBLE) ──")
    if not shared:
        print("    none")
    for label, page, art, st in shared:
        pt = sum(1 for v in st.values() if v == "POINTED")
        print(f"    [{label:<7}] {page:<9} {art.get('field','?'):<18} "
              f"{'(' + str(pt) + ' pointed)' if pt else '(none pointed)'}")
        print(f"                          want: {str(art.get('value'))[:64]}")
    print()

    for e in engines:
        mine = [r for r in rows if r[3][e] != "ok"]
        ptd = [r for r in mine if r[3][e] == "POINTED"]
        abs_ = [r for r in mine if r[3][e] == "ABSENT"]
        solo = [r for r in mine
                if sum(1 for x in ENGINES if r[3][x] == "ok") >= len(ENGINES) - 1]
        print(f"  ── {e} ── {len(mine)} missed "
              f"({len(ptd)} POINTED = repairable, {len(abs_)} ABSENT = not)")
        print(f"     {len(solo)} that every other engine got right "
              f"-> configuration, not page")
        for label, page, art, st in mine:
            others = "".join("+" if st[x] == "ok" else "." for x in ENGINES)
            print(f"     {st[e]:<8} [{label:<7}] {page:<9} "
                  f"{art.get('field','?'):<18} others[{others}] "
                  f"{str(art.get('value'))[:38]}")
        print()

    print("  others[] = " + " ".join(ENGINES) + "   + got it, . missed it")
    print("  POINTED = right region, wrong characters -> a second look fixes it")
    print("  ABSENT  = never surfaced -> nothing to re-read, needs a different pass")


if __name__ == "__main__":
    main()
