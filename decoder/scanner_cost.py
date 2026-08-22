"""IS TESSERACT THE RIGHT SCANNER? Measure the two things that decide it.

⚠ TESSERACT IS A READER BEING USED AS A SCANNER, AND THOSE WANT OPPOSITE THINGS.
A reader optimises PRECISION: it commits to one string per word and throws the
alternatives away. A scanner wants RECALL: it should over-report and let a later,
more expensive stage discriminate. Committing early is exactly the wrong bias for
stage 1, because a word Tesseract renders as "easernent" is not a near-miss to a
regex — it is silence. The claim is never seen, no crop is made, and nothing in
the output says a claim was missed.

So this measures the two numbers that actually decide whether to keep it:

  1. COST      wall-clock ms/page, re-run live, no cached timings
  2. SILENT LOSS  exact-regex hits vs fuzzy hits over the SAME text

⚠ THE SECOND NUMBER NEEDS NO GROUND TRUTH AND THAT IS WHY IT IS USABLE HERE.
OCR damage is small local edits, so a phrase Tesseract mangled is still within
edit distance 1-2 of the truth. Every fuzzy-only hit is a claim exact matching
would have dropped on the floor. The ratio is the scanner's silent loss rate,
measured on 537 real documents rather than argued about.

⚠ AND LOW CONFIDENCE IS REPORTED BESIDE IT. If the fuzzy-only hits sit at high
confidence, Tesseract was sure and wrong, which no threshold can catch.

    python scanner_cost.py            both measurements
    python scanner_cost.py --time     cost only (slower, runs tesseract live)
"""
import collections
import gzip
import json
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR = pathlib.Path("sample_ocr")
LEX = set()
PAGES = pathlib.Path("sample_pages")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ⚠ THE FRAMES, MINUS THE TOPIC WORDS. Bare "easement" fired 45 times in one
# EASE document and carried nothing — a frame whose rate equals the document's
# subject rate discriminates nothing. What survives is phrasing that states a
# RELATION, which is rare even inside a document about that relation.
FRAMES = [
    ("floor area",           r"floor\s+area"),
    ("development rights",   r"development\s+rights?"),
    ("zoning lot",           r"zoning\s+lot"),
    ("parties in interest",  r"part(?:y|ies)\s+in\s+interest"),
    ("zoning resolution",    r"zoning\s+resolution"),
    ("lot area",             r"lot\s+area"),
    ("air rights",           r"air\s+rights?"),
    ("party wall",           r"party\s+wall"),
    ("light and air",        r"light\s+and\s+air"),
    ("certificate of occ",   r"certificate\s+of\s+occupancy"),
    ("special permit",       r"special\s+permit"),
    ("restrictive decl",     r"restrictive\s+declaration"),
    ("single ownership",     r"single\s+ownership"),
    ("square feet",          r"square\s+feet"),
]

def variants(rx_src):
    """EVERY literal word sequence the regex accepts, not just the first.

    ⚠ THIS FUNCTION IS THE WHOLE MEASUREMENT AND THE FIRST VERSION WAS WRONG.
    It reduced `part(?:y|ies)` to "party", so the fuzzy pass hunted a phrase the
    regex was not hunting and reported -114 hits for `parties in interest`.
    A negative loss is impossible, which is the only reason the bug was visible;
    a frame with no alternation would have absorbed the same error silently.
    """
    s = rx_src.replace(r"\s+", " ")
    outs = [""]
    i = 0
    while i < len(s):
        m = re.match(r"\(\?:([^)]*)\)(\??)", s[i:])
        if m:
            alts = m.group(1).split("|")
            if m.group(2):
                alts = alts + [""]
            outs = [o + a for o in outs for a in alts]
            i += m.end()
            continue
        ch = s[i]
        if ch == "\\":
            i += 2; continue
        if s[i + 1:i + 2] == "?":                  # optional single char
            outs = [o + ch for o in outs] + list(outs)
            i += 2; continue
        outs = [o + ch for o in outs]
        i += 1
    return [tuple(w for w in o.split() if w) for o in dict.fromkeys(outs)]


def lev1(a, b):
    """Is edit distance <= 1? Cheap early-outs, no matrix."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:                                  # one substitution
        d = 0
        for x, y in zip(a, b):
            if x != y:
                d += 1
                if d > 1:
                    return False
        return True
    if la > lb:                                   # one deletion from a
        a, b, la, lb = b, a, lb, la
    i = j = 0
    skipped = False
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1; j += 1
        elif skipped:
            return False
        else:
            skipped = True; j += 1
    return True


# ⚠ CURLY QUOTES ARE NOT OCR DAMAGE. Word processors emit “ ” ‘ ’ and defined
# terms in these documents are ALWAYS quoted — `(the “Zoning Lot”)`. A stripper
# that only knows ASCII quotes turns every definition into a miss and then
# blames Tesseract for it.
STRIP = ".,;:()[]{}\"'`|“”‘’„«»–—-*"


def norm(t):
    return t.strip().lower().strip(STRIP)


# ── measurement 1 · silent loss ─────────────────────────────────────────
# ⚠ THE CORPUS IS ITS OWN DICTIONARY. `party wall` fuzzy-matched 373 times and
# 113 of those were "part will" / "party will" — 'each party will...', which is
# not a wall. Tolerant matching on two SHORT COMMON words is dominated by noise,
# while `development rights` had zero false positives because both words are
# long and rare. So tolerance has to be conditioned on distinctiveness, and the
# cheapest measure of that is how often the token occurs in this very corpus.
# A token seen thousands of times is a word Tesseract meant to write.
COMMON_AT = 200


def build_lexicon(docs):
    freq = collections.Counter()
    for p in docs:
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        for r in rows:
            freq.update(norm(w["t"]) for w in r["words"])
    return {t for t, n in freq.items() if n >= COMMON_AT}


def classify(got, seqs):
    """Why did the exact regex miss this? Three answers, only one is Tesseract's.

    ⚠ THE HEADLINE DEPENDS ENTIRELY ON THIS SPLIT. Lumping them together reads
    as "OCR loses 1.2%" when most of it is a bare regex refusing a plural or a
    curly quote — my defect, fixable for free, and nothing to do with the scan.
    """
    n = [norm(g) for g in got]
    for s in seqs:
        if tuple(n) == s:
            return "punct"                       # normalisation alone recovers it
        if len(n) == len(s) and all(
                a == b or a == b + "s" or a + "s" == b or a == b + "es"
                for a, b in zip(n, s)):
            return "morph"                       # plural / inflection
    return "ocr"                                 # genuine character damage


def loss():
    docs = sorted(OCR.glob("*.json.gz"))
    exact = collections.Counter()
    fuzzy = collections.Counter()
    kind = collections.defaultdict(collections.Counter)
    conf = collections.defaultdict(list)
    eg = collections.defaultdict(list)
    n_pages = n_words = 0

    global LEX
    LEX = build_lexicon(docs)
    targets = [variants(rx) for _, rx in FRAMES]

    for p in docs:
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        for r in rows:
            ws = r["words"]
            n_pages += 1
            n_words += len(ws)
            text = " ".join(w["t"] for w in ws)
            toks = [norm(w["t"]) for w in ws]

            for (lab, rx), seqs in zip(FRAMES, targets):
                exact[lab] += len(re.findall(rx, text, re.I))
                # ⚠ FUZZY OVER THE SAME TOKENS — not a second OCR pass. The
                # only variable is the matcher, so every extra hit is something
                # the text already contained and the regex declined to see.
                seen = set()
                for s in seqs:
                    k = len(s)
                    for i in range(len(toks) - k + 1):
                        if i in seen:
                            continue
                        if all(lev1(toks[i + j], s[j]) for j in range(k)):
                            seen.add(i)
                            fuzzy[lab] += 1
                            got = [ws[i + j]["t"] for j in range(k)]
                            if tuple(norm(g) for g in got) in seqs:
                                continue          # exact found it too
                            c = classify(got, seqs)
                            # ⚠ A REAL WORD IS NOT DAMAGE. If every token
                            # Tesseract wrote is common in this corpus, it wrote
                            # what it saw and the frame simply is not here.
                            if c == "ocr" and all(norm(g) in LEX for g in got):
                                c = "noise"
                            kind[lab][c] += 1
                            if c == "ocr":
                                conf[lab].append(
                                    statistics.mean(ws[i + j].get("c", 0)
                                                    for j in range(k)))
                                if len(eg[lab]) < 4:
                                    eg[lab].append((r["doc"], r["page"],
                                                    " ".join(got)))

    print(f"  {len(docs)} documents · {n_pages:,} pages · {n_words:,} OCR words\n")
    print(f"  lexicon: {len(LEX):,} tokens seen >={COMMON_AT}x = real words\n")
    print(f"  {'frame':<21}{'exact':>7}{'fuzzy':>7}  {'noise':>6}{'punct':>6}"
          f"{'morph':>7}{'OCR':>6}{'ocr loss':>10}{'conf':>7}")
    tot = collections.Counter()
    te = tf = 0
    for lab, _ in FRAMES:
        e, f = exact[lab], fuzzy[lab]
        te += e; tf += f
        k = kind[lab]
        tot.update(k)
        c = statistics.mean(conf[lab]) if conf[lab] else 0
        real = f - k['noise']
        print(f"  {lab:<21}{e:>7,}{f:>7,}  {k['noise']:>6,}{k['punct']:>6,}"
              f"{k['morph']:>7,}{k['ocr']:>6,}"
              f"{(k['ocr'] / real * 100 if real else 0):>9.1f}%"
              f"{(f'{c:.0f}' if c else '-'):>7}")
    treal = tf - tot['noise']
    print(f"  {'ALL':<21}{te:>7,}{tf:>7,}  {tot['noise']:>6,}{tot['punct']:>6,}"
          f"{tot['morph']:>7,}{tot['ocr']:>6,}"
          f"{(tot['ocr'] / treal * 100 if treal else 0):>9.1f}%")

    print(f"\n  punct  my tokenizer, not the scan — “Zoning Lot” with curly quotes")
    print(f"  morph  my regex, not the scan — 'zoning lots', 'certificates of'")
    print(f"  OCR    genuine character damage. THIS is the scanner's silent loss.")

    if eg:
        print(f"\n  ── THE ACTUAL OCR DAMAGE ──")
        for lab in sorted(eg, key=lambda k: -kind[k]['ocr']):
            print(f"    {lab}  ({kind[lab]['ocr']} of {fuzzy[lab]:,})")
            for doc, pg, got in eg[lab]:
                print(f"        {doc} p{pg:<3} {got!r}")


# ── measurement 2 · cost ────────────────────────────────────────────────
def cost(n=12):
    if not pathlib.Path(TESS).exists():
        print("  tesseract not found"); return
    tifs = []
    for d in sorted(x for x in PAGES.iterdir() if x.is_dir()):
        g = sorted(d.glob("*.tif"))
        if g:
            tifs.append(g[0])
        if len(tifs) >= n:
            break
    scratch = pathlib.Path(os.environ["TMP"]) / "scan"
    scratch.mkdir(parents=True, exist_ok=True)
    print(f"\n  ── COST · {len(tifs)} pages, tesseract run live ──")
    print(f"  {'page':<22}{'psm6 ms':>10}{'words':>8}")
    ms = []
    for t in tifs:
        t0 = time.time()
        r = subprocess.run([TESS, str(t), "stdout", "--psm", "6"],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        el = (time.time() - t0) * 1000
        ms.append(el)
        print(f"  {t.parent.name[:20]:<22}{el:>10.0f}{len(r.stdout.split()):>8,}")
    m = statistics.mean(ms)
    print(f"\n  mean {m:,.0f} ms/page")
    print(f"  133,988,962 instrument pages  ->  {133988962 * m / 1000 / 86400:,.0f} "
          f"core-days single-threaded")
    print(f"                                ->  {133988962 * m / 1000 / 86400 / 16:,.0f} "
          f"days on 16 cores")


if __name__ == "__main__":
    if "--time" in sys.argv:
        cost()
    else:
        loss()
        cost()
