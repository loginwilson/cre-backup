"""THE TABLE: every engine crossed against time and artifact recall.

⚠ ARTIFACTS, NOT WORDS. Word count has misled this project twice in one day.
A 51-word ACRIS cover page carries 12 artifacts; a 1,764-word film page may
carry fewer. And an engine can emit 900 fluent words of invention and score
higher on any length-based metric than one that returned 200 correct ones.

⚠ AND NOT CHARACTER ACCURACY EITHER. The pipeline does not consume the
characters — it consumes a BOX that a reasoning model then crops and reads.
Qwen wrote `1586` for `1686` on a reel stamp and that is nearly irrelevant,
because it put the field on the map where Tesseract emitted nothing at all.
So the question each artifact asks is: did this engine SURFACE this fact.

⚠ AMBIGUOUS ARTIFACTS ARE EXCLUDED FROM BOTH NUMERATOR AND DENOMINATOR. Where
the human reader could not resolve a handwritten block number or a struck-out
date, no engine is credited or penalised. Scoring an engine on something
unreadable measures luck.

    python score.py [bench_dir]
"""
import json
import pathlib
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BENCH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "render/live")
KEY = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "answer_key.json")
_tf = BENCH / "timings.json"
TIMES = json.loads(_tf.read_text(encoding="utf-8")) if _tf.exists() else {}
ENGINES = ["tesseract", "qwen", "qwenfast", "paddle", "rapid", "rapidpool"]
TIERS = ["CRITICAL", "MATERIAL", "ROUTINE"]
META = {}


def norm(s):
    """Case, whitespace, punctuation and curly-quote insensitive.

    ⚠ CURLY QUOTES AND HYPHEN VARIANTS ARE NOT ENGINE ERRORS. Word processors
    emit them, OCR renders them inconsistently, and a comparison that treats
    'Receiver's' vs 'Receivers' as a miss measures my tokenizer.
    """
    s = unicodedata.normalize("NFKD", s or "")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐-―]", "-", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    # ⚠ A DIGIT GLUED TO A LETTER IS NOT A WRONG READ, AND NOT SPLITTING IT
    # WOULD HAVE UNDER-CREDITED THE VLM EXACTLY WHERE IT BEATS TESSERACT.
    # Qwen returned `REEL / PAGE: 371PAGE 656` on the film page whose stamp
    # Tesseract could not see at all — a correct read of the single artifact
    # that justifies running a VLM. But it lands in the haystack as the token
    # `371page`, so ' reel 371 ' is not a substring and the bare alt '371'
    # (digits, exact-match-only) does not appear either. Scored as-is it is a
    # miss, and I would have reported that the VLM failed at the one thing it
    # demonstrably did.
    #
    # Applied to needle and haystack alike, so no engine gains an edge.
    s = re.sub(r"(?<=[0-9])(?=[a-z])", " ", s)
    s = re.sub(r"(?<=[a-z])(?=[0-9])", " ", s)
    return f" {re.sub(r'\s+', ' ', s).strip()} "


def found(hay, art):
    """TRANSCRIBED — the characters are right and the text is usable as-is.

    ⚠ WORD SPACING IS A FORMATTING ARTIFACT, NOT A READING FAILURE, AND
    PENALISING IT MISATTRIBUTED RAPIDOCR'S WHOLE MATERIAL SCORE. RapidOCR
    returns `THISMORTGAGE,madethe dayof ,1981` — every character correct, the
    spaces missing, because its detector merges adjacent text boxes. Scored on
    spaced tokens it "missed" THIS MORTGAGE, and it dropped to 57% on MATERIAL
    against Tesseract's 84% while actually reading MORE of the page.

    So the comparison is also made with all spacing removed from both sides.
    Applied to every engine identically, and only ever as an additional way to
    hit — it cannot turn a hit into a miss.
    """
    flat = re.sub(r"\s+", "", hay)
    for v in [art["value"]] + list(art.get("alts") or []):
        n = norm(v).strip()
        if not n:
            continue
        if n in hay:
            return True
        # ⚠ guard: only for artifacts long enough that a despaced match is not
        # coincidence. 'Lot 1' despaced is 'lot1', which is everywhere.
        f = re.sub(r"\s+", "", n)
        if len(f) >= 8 and f in flat:
            return True
    return False


def pointed(hay, art, thresh=0.62):
    """POINTED — the engine emitted SOMETHING recognisably at this artifact.

    ⚠ THIS IS THE METRIC THE PIPELINE ACTUALLY CONSUMES, AND SCORING WITHOUT IT
    PRODUCED A WRONG VERDICT. Tesseract scored 0/11 on a handwritten backer by
    exact match — yet it emitted `104-106 Charlles Sheee` for "104-106 Charlton
    Street" and `YECORLED ix NEW YORK CUUNTY` for "RECORDED IN NEW YORK COUNTY".
    Those are boxes in exactly the right places with mangled characters inside.
    A reasoning model handed that box crops it, magnifies it, and reads it
    correctly — so for the architecture it is a HIT, not a miss.

    ⚠ THE THRESHOLD IS THE WHOLE RISK. Too loose and every artifact "matches"
    something somewhere, which would flatter every engine equally and say
    nothing. 0.62 on a length-matched sliding window keeps `Charlles Sheee`
    ~ `Charlton Street` while rejecting unrelated text — and the gap between
    TRANSCRIBED and POINTED is reported so an implausibly large one is visible
    rather than hidden inside a single score.
    """
    from difflib import SequenceMatcher
    toks = hay.split()
    for v in [art["value"]] + list(art.get("alts") or []):
        v = norm(v).strip()
        if not v:
            continue
        if v in hay:
            return True
        # ⚠ FUZZY MATCHING ON A BARE NUMBER IS NOT EVIDENCE, IT IS COINCIDENCE,
        # AND IT PUT A FALSE 100% IN THIS TABLE. The book page scored 19/19
        # "pointed" including REEL 1118 / PAGE 1406 — but Tesseract never
        # emitted either string. A 4-digit artifact matches almost any 4-digit
        # token at a 0.62 ratio, and a mortgage page numbered 12-24 with dollar
        # amounts and dates is nothing but 4-digit tokens. Every reel stamp,
        # every year and every zip in this key was inflated the same way.
        #
        # A word survives OCR damage as a recognisable SHAPE ('Charlles Sheee'
        # is still Charlton Street). A number does not — 1406 and 1206 are
        # equally plausible readings of each other and of anything else. So
        # fuzzy is allowed only where there are >=3 consecutive letters to
        # carry that shape; anything else must match exactly.
        #
        # This makes the metric CONSERVATIVE on digits: a genuine "right box,
        # wrong digit" read now scores as a miss. That understates pointing,
        # which is the safe direction to be wrong in.
        if not re.search(r"[a-z]{3}", v):
            continue
        vt = v.split()
        k = len(vt)
        for i in range(0, max(1, len(toks) - k + 1)):
            win = " ".join(toks[i:i + k])
            if not win:
                continue
            # length guard: a 3-char window cannot "be" a 20-char artifact
            if abs(len(win) - len(v)) > max(6, len(v) * 0.5):
                continue
            if SequenceMatcher(None, win, v).ratio() < thresh:
                continue
            # ⚠ IF THE ARTIFACT CARRIES DIGITS, THE WINDOW MUST CARRY DIGITS TOO.
            # Without this, `REEL 586` was scored as POINTED against Tesseract's
            # `REEL i 765` — the word REEL alone cleared the 0.62 ratio while the
            # reel NUMBER, which is the entire join key, was never read. The
            # label is worthless: every film page in the corpus says REEL.
            #
            # Digits are not required to be CORRECT here, only present. `086`
            # for `586` still puts a box on the stamp for the reasoning model to
            # re-read, and that is what POINTED means. Reading nothing does not.
            if re.search(r"\d", v) and not re.search(r"\d", win):
                continue
            return True
    return False


def klass(fname):
    """SCAN CLASS FROM THE SOURCE PREFIX, not from the manifest's era label.

    ⚠ THE MANIFEST'S `era` IS WRONG ON AT LEAST ONE PAGE AND IT FLATTERS THE
    RESULT. `modern_1970s_MTGE_BK_7940114801404_p003` is labelled modern, but it
    is a 1970s bound-book scan — grey, skewed, with the reel stamp rotated 90
    degrees up the right edge. It is the hardest page in the set. Scoring it as
    'modern' drags the easy-case number down and lifts the film number, so both
    columns describe pages that do not exist.

    The prefix is a fact about the source, so that is what is used:
        FT_  microfilm            BK_  bound book          else  born-digital
    """
    # ⚠ THE FILENAME IS NOT ALWAYS THE SOURCE OF TRUTH. Single-document runs
    # write plain page names (p001.png), which carry no prefix — so a 1981
    # MICROFILM mortgage was being reported under 'digital', the easiest class,
    # inverting the one distinction this table exists to make. The manifest's
    # doc_id is authoritative when present.
    src = f"{(META.get(fname) or {}).get('doc_id', '')} {fname}"
    if "FT_" in src:
        return "film"
    if "BK_" in src:
        return "book"
    return "modern"


def main():
    if not KEY.exists():
        print("  no answer_key.json"); return
    key = {k: v for k, v in json.loads(KEY.read_text(encoding="utf-8")).items()
           if not k.startswith("_")}

    man = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    meta = {m["file"]: m for m in man}
    META.update(meta)

    # which engines actually have output on disk
    # ⚠ AN EMPTY OUTPUT DIRECTORY IS A CRASH, NOT A SCORE OF ZERO. bench_all
    # mkdirs before it runs, so a engine that died on startup (Paddle did,
    # inside oneDNN) leaves a directory full of nothing and lands in the table
    # as a confident 0% — indistinguishable from an engine that read every page
    # and got everything wrong. Those are opposite findings.
    live = [e for e in ENGINES
            if (BENCH / e).exists() and any((BENCH / e).glob("*.txt"))]
    dead = [e for e in ENGINES
            if (BENCH / e).exists() and not any((BENCH / e).glob("*.txt"))]
    if dead:
        print(f"  ⚠ no output (did not run / crashed): {', '.join(dead)}")
    if not live:
        print(f"  no engine output under {BENCH}"); return

    n_art = sum(len(v["artifacts"]) for v in key.values())
    n_amb = sum(len(v.get("ambiguous") or []) for v in key.values())
    print(f"  {len(key)} keyed pages · {n_art} artifacts scored · "
          f"{n_amb} ambiguous excluded")
    print(f"  engines with output: {', '.join(live)}\n")

    # ── per engine, per tier ─────────────────────────────────────────────
    tally = {e: {t: [0, 0] for t in TIERS} for e in live}
    ptally = {e: {t: [0, 0] for t in TIERS} for e in live}
    perpage = {e: {} for e in live}
    misses = {e: [] for e in live}

    for page, spec in key.items():
        for e in live:
            f = BENCH / e / (page + ".txt")
            hay = norm(f.read_text(encoding="utf-8", errors="replace")) if f.exists() else " "
            hit = 0
            for a in spec["artifacts"]:
                t = a["tier"]
                tally[e][t][1] += 1
                ptally[e][t][1] += 1
                ok = found(hay, a)
                pt = ok or pointed(hay, a)
                if ok:
                    tally[e][t][0] += 1
                    hit += 1
                if pt:
                    ptally[e][t][0] += 1
                elif t == "CRITICAL":
                    misses[e].append((page, a["id"], a["value"]))
            perpage[e][page] = (hit, len(spec["artifacts"]))

    print(f"  ── ARTIFACT RECALL ──\n")
    hdr = f"  {'engine':<12}" + "".join(f"{t[:8]:>12}" for t in TIERS) + f"{'ALL':>12}{'sec':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    rows = []
    for e in live:
        cells = ""
        th = tv = 0
        for t in TIERS:
            h, v = tally[e][t]
            th += h; tv += v
            cells += f"{f'{h}/{v}':>7}{f'{h/v*100:.0f}%' if v else '-':>5}"
        sec = (TIMES.get(e) or {}).get("sec")
        secs = f"{sec:.1f}" if sec else "-"
        print(f"  {e:<12}{cells}{f'{th}/{tv}':>7}{th/tv*100:>5.0f}%{secs:>8}")
        rows.append((e, th, tv))

    print(f"\n  ── PER PAGE (artifacts found / total) ──\n")
    w = max(len(p) for p in key) + 2
    print(f"  {'page':<{min(w,52)}}" + "".join(f"{e[:9]:>11}" for e in live))
    for page in key:
        line = f"  {page[:50]:<{min(w,52)}}"
        for e in live:
            h, v = perpage[e][page]
            ph = sum(1 for a in key[page]["artifacts"]
                     if found(norm((BENCH/e/(page+".txt")).read_text(encoding="utf-8",errors="replace")) if (BENCH/e/(page+".txt")).exists() else " ", a)
                     or pointed(norm((BENCH/e/(page+".txt")).read_text(encoding="utf-8",errors="replace")) if (BENCH/e/(page+".txt")).exists() else " ", a))
            line += f"{f'{h}/{ph}/{v}':>14}"
        print(line)

    # ⚠ THE AGGREGATE IS A FICTION AND THIS IS WHY IT MUST BE SPLIT.
    # 79% overall was 96% on modern laser print and 69% on microfilm. Film is
    # ~37% of the corpus and carries the pre-2003 lineage, so an average across
    # the two describes no page that actually exists.
    # ⚠ THE `ALL` COLUMN COMPARES ANSWERS TO TWO DIFFERENT QUESTIONS AND MUST
    # NOT BE READ AS A RANKING. Tesseract was asked to transcribe the page, so
    # it returns the boilerplate and scores on ROUTINE. Qwen was asked to list
    # named fields and skip everything else — which is the entire reason it is
    # fast enough to consider at all — so it returns no boilerplate and scores
    # ~12% on ROUTINE by design, not by failure. Averaging those together
    # produced 68% vs 43% and pointed at the wrong engine.
    #
    # CRITICAL is the tier both engines were genuinely asked for, and it is the
    # tier the pipeline breaks without: reel stamps, parties, doc ids, lots.
    print("\n  ── CRITICAL ONLY · the tier both engines were asked for ──\n")
    print(f"  {'engine':<12}{'film':>16}{'book':>16}{'digital':>16}{'ALL CRIT':>16}")
    print("  " + "-" * 74)
    for e in live:
        cells = ""
        gh = gv = 0
        for era in ("film", "book", "modern"):
            pgs = [p for p in key if klass(p) == era]
            h = v = 0
            for page in pgs:
                f = BENCH / e / (page + ".txt")
                hay = norm(f.read_text(encoding="utf-8", errors="replace")) if f.exists() else " "
                for a in key[page]["artifacts"]:
                    if a["tier"] != "CRITICAL":
                        continue
                    v += 1
                    if found(hay, a) or pointed(hay, a):
                        h += 1
            gh += h; gv += v
            cells += f"{f'{h}/{v}':>10}{h/v*100 if v else 0:>5.0f}%"
        print(f"  {e:<12}{cells}{f'{gh}/{gv}':>10}{gh/gv*100 if gv else 0:>5.0f}%")

    print("\n  ── BY ERA · transcribed / pointed ──\n")
    print(f"  {'engine':<12}{'era':<9}{'pages':>6}{'artifacts':>11}"
          f"{'transcribed':>14}{'pointed':>12}")
    for e in live:
        for era in ("modern", "film", "book"):
            pgs = [p for p in key if klass(p) == era]
            if not pgs: continue
            tv = th = pv = 0
            for page in pgs:
                f = BENCH / e / (page + ".txt")
                hay = norm(f.read_text(encoding="utf-8", errors="replace")) if f.exists() else " "
                for a in key[page]["artifacts"]:
                    tv += 1
                    if found(hay, a): th += 1
                    if found(hay, a) or pointed(hay, a): pv += 1
            print(f"  {e:<12}{era:<9}{len(pgs):>6}{tv:>11}"
                  f"{f'{th}/{tv}':>9}{th/tv*100:>5.0f}%{f'{pv}/{tv}':>8}{pv/tv*100:>4.0f}%")

    for e in live:
        if misses[e]:
            print(f"\n  ── {e.upper()} · CRITICAL artifacts MISSED ({len(misses[e])}) ──")
            for page, aid, val in misses[e][:14]:
                print(f"    {aid:<14}{str(val)[:34]:<36}{page[:34]}")

    print(f"\n  ⚠ recall here is 'did the engine surface the fact', not 'did it")
    print(f"    spell it right'. A box in the right place is what the pipeline")
    print(f"    consumes; the reasoning model reads the magnified crop.")


if __name__ == "__main__":
    main()
