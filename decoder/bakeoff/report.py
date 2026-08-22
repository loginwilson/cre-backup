"""THE MATRIX, plus the number that decides the architecture.

    python report.py

Scores every engine found under out/ against the three hand-read answer keys,
split by scan class, transcribed and pointed. Then does the thing the accuracy
table cannot do on its own: measures how much a SECOND proposer adds, and how
often the two disagree.

⚠ THE PAIRWISE SECTION IS THE ARCHITECTURE DECISION, NOT A CURIOSITY. The whole
question is whether cheap proposers earn their place or whether the 27B verifier
should just read all 148,238,970 pages itself. That turns on two measured
quantities and nothing else:

  COMPLEMENTARITY - does proposer B catch things proposer A missed? If the union
  of two 0.9B engines is barely better than the best one alone, the second is
  waste and one proposer is the answer.

  DISAGREEMENT RATE - on what fraction of pages do the two proposers differ
  enough to need adjudication? That fraction IS the verifier's workload, and the
  verifier is ~30x the cost per page. At 5% the cascade wins overwhelmingly; at
  80% the proposers are a rounding error in front of a full 27B pass and should
  be deleted.

⚠ AND DISAGREEMENT IS MEASURED ON ARTIFACTS, NOT ON RAW TEXT. Two engines will
differ on whitespace and line order on essentially every page, which would
report ~100% disagreement and mean nothing. What matters is whether they differ
on a fact the pipeline consumes.

⚠ THE 'union' ROW IS AN UPPER BOUND THE PIPELINE CANNOT REACH BY ITSELF. It
credits a fact if EITHER engine got it - which assumes something downstream
always picks the right one. That is exactly the verifier's job, so union is the
ceiling the verifier is being asked to hit, not a score any two-engine system
achieves for free.
"""
import itertools
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import score as S

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
KEYS = [
    ("FT_1680008647768", "answer_key_testdoc.json", "film 1981", 0.255),
    ("BK_6730047100023", "answer_key_bookdoc.json", "book 1967", 0.040),
    ("2015022400608001", "answer_key_moderndoc.json", "digital 2015", 0.705),
]


def load():
    docs = []
    for doc, keyf, label, share in KEYS:
        p = HERE / "keys" / keyf
        if not p.exists():
            continue
        key = {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        docs.append((doc, key, label, share))
    return docs


def text(eng, doc, page):
    """All orientations of one page, concatenated. Missing file -> empty."""
    d = OUT / eng / doc
    if not d.exists():
        return ""
    stem = page[:-4] if page.endswith(".png") else page
    return " ".join(f.read_text(encoding="utf-8", errors="replace")
                    for f in sorted(d.glob(stem + "*.txt")))


def engines():
    if not OUT.exists():
        return []
    return sorted(d.name for d in OUT.iterdir()
                  if d.is_dir() and any(d.rglob("*.txt")))


def hits(engs, doc, key):
    """-> {(page, artifact_id): (transcribed, pointed)} for the union of engs."""
    r = {}
    for page, spec in key.items():
        hay = S.norm(" ".join(text(e, doc, page) for e in engs))
        for a in spec["artifacts"]:
            if a["tier"] != "CRITICAL":
                continue
            ok = S.found(hay, a)
            r[(page, a["id"])] = (ok, ok or S.pointed(hay, a))
    return r


def pct(h, v):
    return f"{h}/{v} {h/v*100:>3.0f}%" if v else "-"


def main():
    docs = load()
    engs = engines()
    if not docs:
        print("  no answer keys under keys/"); return
    if not engs:
        print("  no engine output under out/ - run run.py first"); return

    runs = {}
    for e in engs:
        f = OUT / e / "run.json"
        runs[e] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    # ── per engine × scan class ──────────────────────────────────────────
    print("  ── CRITICAL artifacts · transcribed / pointed ──\n")
    hdr = f"  {'engine':<20}" + "".join(f"{lbl:>22}" for _, _, lbl, _ in docs) \
          + f"{'BLENDED':>12}{'s/pg':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    blended = {}
    for e in engs:
        cells = ""
        bt = bp = 0.0
        for doc, key, _, share in docs:
            h = hits([e], doc, key)
            v = len(h)
            t = sum(1 for a, b in h.values() if a)
            p = sum(1 for a, b in h.values() if b)
            cells += f"{pct(t, v):>13}{f'{p/v*100:>3.0f}%' if v else '-':>9}"
            if v:
                bt += share * t / v
                bp += share * p / v
        blended[e] = (bt, bp)
        spp = runs[e].get("sec_per_page")
        print(f"  {e:<20}{cells}{bt*100:>7.1f}%{bp*100:>5.0f}%"
              f"{(f'{spp:.1f}' if spp else '-'):>8}")

    print(f"\n  (each cell: transcribed / pointed.  BLENDED weights film 25.5%, "
          f"book 4.0%, digital 70.5%\n   by corpus page share, so it describes "
          f"the actual 148.2M-page mix.)")

    # ── does a second proposer earn its place ────────────────────────────
    if len(engs) >= 2:
        print("\n\n  ── PAIRS · what the second proposer adds ──\n")
        print(f"  {'pair':<40}{'best alone':>12}{'union':>10}{'gain':>8}"
              f"{'disagree':>10}{'both miss':>11}")
        print("  " + "-" * 89)
        for a, b in itertools.combinations(engs, 2):
            ta = tb = tu = v = 0
            dis = both_miss = 0
            for doc, key, _, _ in docs:
                ha, hb = hits([a], doc, key), hits([b], doc, key)
                hu = hits([a, b], doc, key)
                for k in hu:
                    v += 1
                    xa, xb = ha[k][0], hb[k][0]
                    ta += xa; tb += xb; tu += hu[k][0]
                    if xa != xb:
                        dis += 1
                    if not xa and not xb:
                        both_miss += 1
            best = max(ta, tb)
            print(f"  {a + ' + ' + b:<40}{best/v*100:>11.1f}%{tu/v*100:>9.1f}%"
                  f"{(tu-best)/v*100:>+7.1f}{dis/v*100:>9.1f}%{both_miss/v*100:>10.1f}%")

        # ⚠ THE ARTIFACT RATE IS NOT THE ESCALATION RATE AND USING IT WOULD
        # UNDERSTATE THE VERIFIER'S BILL BY A LOT. The verifier is handed a
        # PAGE, not a fact - it cannot re-read one artifact in isolation, it
        # loads the image. So a page with ONE disagreement among twelve
        # artifacts escalates in full, exactly like a page with twelve.
        #
        # 20% of artifacts disagreeing can mean anything from 20% of pages to
        # 100% of pages depending on whether the disagreements cluster. The
        # cost model consumes the PAGE number; the artifact number only says
        # how much work there is once the page is open.
        print("\n\n  ── PAIRS · PAGE-level escalation (what the verifier is billed for) ──\n")
        # ⚠ AND THE RAW 21-PAGE RATE IS WEIGHTED BACKWARDS FROM THE CORPUS.
        # This sample is 10 film + 7 book + 4 digital = 81% historical. The
        # actual corpus is 70.5% DIGITAL, the class where every engine already
        # scores ~100% and almost nothing escalates. Quoting the unweighted rate
        # prices the corpus as if it were all microfilm, which triples the
        # verifier's bill and would have argued for the wrong architecture.
        print(f"  {'pair':<28}{'film':>14}{'book':>14}{'digital':>14}"
              f"{'CORPUS-WTD':>13}")
        print("  " + "-" * 83)
        for a, b in itertools.combinations(engs, 2):
            cells = ""
            wtd = 0.0
            for doc, key, _, share in docs:
                ha, hb = hits([a], doc, key), hits([b], doc, key)
                npg = esc = 0
                for page in key:
                    ks = [k for k in ha if k[0] == page]
                    if not ks:
                        continue
                    npg += 1
                    esc += any(ha[k][0] != hb[k][0] for k in ks)
                cells += f"{f'{esc}/{npg}':>9}{esc/npg*100:>5.0f}%" if npg else f"{'-':>14}"
                if npg:
                    wtd += share * esc / npg
            print(f"  {a + ' + ' + b:<28}{cells}{wtd*100:>12.0f}%")

        print("\n  ⚠ THIS is the number the cost model needs, not the artifact rate"
              "\n    above. A page escalates whole: one disagreement among twelve"
              "\n    artifacts costs the same verifier pass as twelve."
              "\n  ⚠ CORPUS-WTD weights film 25.5% / book 4.0% / digital 70.5%."
              "\n    n=21 pages, so treat every cell as directional, not precise -"
              "\n    the digital column especially rests on 4 pages.")

        print("\n  disagree = one engine got the fact and the other did not."
              "\n              THIS IS THE VERIFIER'S WORKLOAD. Low means the cheap"
              "\n              cascade wins; high means the proposers are noise in"
              "\n              front of a full verifier pass and should be dropped."
              "\n  both miss = neither proposer surfaced it. No amount of"
              "\n              adjudication recovers these - they need a better"
              "\n              proposer or the last-resort model.")

    # ── what nothing catches ─────────────────────────────────────────────
    print("\n\n  ── MISSED BY EVERY ENGINE (transcribed) ──\n")
    n = 0
    for doc, key, label, _ in docs:
        hu = hits(engs, doc, key)
        rows = [(k, v) for k, v in hu.items() if not v[0]]
        if not rows:
            continue
        print(f"  {label}:")
        for (page, aid), (_, pt) in rows[:16]:
            val = next(x["value"] for x in key[page]["artifacts"] if x["id"] == aid)
            print(f"    {page:<11}{aid:<16}{str(val)[:34]:<36}"
                  f"{'POINTED' if pt else 'ABSENT'}")
            n += 1
        if len(rows) > 16:
            print(f"    ... and {len(rows)-16} more")
    if not n:
        print("  none - every CRITICAL artifact transcribed by at least one engine")

    print("\n  ⚠ POINTED means the box is right and the characters are wrong -")
    print("    recoverable by a verifier holding the image. ABSENT means nothing")
    print("    was emitted there at all, and no verifier can recover it.")


if __name__ == "__main__":
    main()
