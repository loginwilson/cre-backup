"""SCORE EVERY ENGINE ON THE PAGES THEY ALL HAVE. Nothing else is a comparison.

    python score_common.py

⚠ A PAGE ONE ENGINE NEVER PRODUCED IS NOT A PAGE THAT ENGINE SCORED ZERO ON.
This project has now made that mistake three times - Paddle crashing to an empty
directory and landing in the table as a confident 0%, four vision calls dying on
a context overflow and producing "the pixels are worth -3.3 points", and 150
document tasks vanishing behind return_exceptions into a clean summary. So the
scored set is the INTERSECTION of pages every listed engine actually wrote, and
what was dropped is printed rather than absorbed.

⚠ AND THE PER-CLASS SPLIT IS NOT COSMETIC. 79% overall was 96% on modern laser
print and 69% on microfilm; film is ~25.5% of the corpus and carries the pre-2003
lineage, so a single blended number describes no page that exists. Blending is
done by CORPUS page share (film 25.5 / book 4.0 / digital 70.5), not by the
sample's own mix, which is 81% historical and would triple the apparent
difficulty.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import score as S

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
KEYS = [("FT_1680008647768", "answer_key_testdoc.json", "film", 0.255),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book", 0.040),
        ("2015022400608001", "answer_key_moderndoc.json", "digital", 0.705)]
# ⚠ AN IN-PROGRESS RUN IS NOT AN ENGINE. Passing a half-finished run through
# this table collapsed the intersection to ONE page and reported rapidpool as
# "best" on the strength of a single digital cover page. Engines are named
# explicitly on the command line so a run that is still writing cannot silently
# redefine what everything else is measured on.
ENGINES = sys.argv[1:] or ["tesseract", "rapidpool", "qwen", "ppv6"]


def text(eng, doc, page):
    d = OUT / eng / doc
    if not d.exists():
        return None
    stem = page[:-4] if page.endswith(".png") else page
    fs = sorted(d.glob(stem + "*.txt"))
    if not fs:
        return None
    return " ".join(f.read_text(encoding="utf-8", errors="replace") for f in fs)


def main():
    live = [e for e in ENGINES if (OUT / e).exists() and any((OUT / e).rglob("*.txt"))]
    docs = []
    for doc, kf, label, share in KEYS:
        p = HERE / "keys" / kf
        if p.exists():
            k = {x: v for x, v in json.loads(p.read_text(encoding="utf-8")).items()
                 if not x.startswith("_")}
            docs.append((doc, k, label, share))

    # intersection
    common, dropped = {}, []
    for doc, key, label, _ in docs:
        ok = []
        for page in key:
            missing = [e for e in live if text(e, doc, page) is None]
            (ok if not missing else dropped).append(page if not missing
                                                    else (label, page, missing))
            if not missing:
                pass
        common[doc] = [p for p in key if all(text(e, doc, p) is not None for e in live)]
    dropped = [d for d in dropped if isinstance(d, tuple)]

    n_all = sum(len(k) for _, k, _, _ in docs)
    n_use = sum(len(v) for v in common.values())
    print(f"  engines: {', '.join(live)}")
    print(f"  scoring {n_use} of {n_all} pages (intersection)")
    for label, page, miss in dropped:
        print(f"    ⚠ dropped {label} {page} - not produced by: {', '.join(miss)}")
    print()

    hdr = f"  {'engine':<14}" + "".join(f"{l:>17}" for _, _, l, _ in docs) + \
          f"{'BLENDED':>11}{'ptd':>7}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    rows = []
    for e in live:
        cells, bt, bp = "", 0.0, 0.0
        for doc, key, label, share in docs:
            pgs = common[doc]
            h = p = v = 0
            for page in pgs:
                hay = S.norm(text(e, doc, page) or "")
                for a in key[page]["artifacts"]:
                    if a["tier"] != "CRITICAL":
                        continue
                    v += 1
                    ok = S.found(hay, a)
                    h += ok
                    p += ok or S.pointed(hay, a)
            cells += f"{f'{h}/{v}':>11}{h/v*100 if v else 0:>6.0f}%"
            if v:
                bt += share * h / v
                bp += share * p / v
        print(f"  {e:<14}{cells}{bt*100:>10.1f}%{bp*100:>6.0f}%")
        rows.append((e, bt))

    print(f"\n  transcribed = characters correct · ptd = pointed (right box,")
    print(f"  wrong characters - recoverable by a model that looks again)")
    best = max(rows, key=lambda r: r[1])
    print(f"\n  best blended: {best[0]} at {best[1]*100:.1f}%")


if __name__ == "__main__":
    main()
