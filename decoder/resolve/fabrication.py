"""CAN THE VLM'S FABRICATIONS BE CAUGHT STRUCTURALLY, WITHOUT A SECOND MODEL?

    python fabrication.py
    python fabrication.py --vlm q35-fair

⚠ WHY THIS EXISTS. Under the settled architecture OCR transcribes, the VLM reasons
about where text belongs, and the index confirms the few fields it is authoritative
for. Nobody duplicates anybody — so the old agreement test between two transcribers
is gone, and with it the ONLY guard that ever caught the VLM inventing. The record is
specific: Qwen emitted `**Document Title**`, `**Header**`, `**Signature Block**` —
layout labels never printed on the page — and Paddle caught it purely because an OCR
engine reports DETECTED REGIONS and structurally cannot invent a phrase.

⚠ THE GUARD THAT SURVIVES THE REDESIGN. OCR is a SUPPORT SET. A token the VLM emits
that no OCR pass at any angle produced is UNSUPPORTED. That is decidable by string
comparison — no model, no threshold, no second opinion.

⚠ AND THE FALSE POSITIVE IS THE WHOLE DIFFICULTY, SO IT IS MEASURED, NOT ASSUMED.
"unsupported" has two causes and they are opposite in meaning:

    FABRICATED   the VLM invented it. Nothing on the page says it.
    OCR MISS     the VLM read real text every OCR pass failed to detect. A WIN.

Calling the second one fabrication would suppress exactly the readings that make the
VLM worth running. So every unsupported token is checked against the HAND KEY: if the
key contains it, the VLM was right and OCR was blind. That converts a plausible rule
into a measured precision.

⚠ DENOMINATORS TRAVEL. Rates are per (vlm-run, doc) with the token count attached.
"""
from __future__ import annotations

import argparse, collections, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
BAKE = HERE.parent / "bakeoff"
DEC = HERE.parent
sys.path.insert(0, str(BAKE))

import score as S
import channel_audit as C

KEYS = [("FT_1680008647768", "answer_key_testdoc.json", "film"),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book"),
        ("2015022400608001", "answer_key_moderndoc.json", "digital")]

# every OCR run on disk contributes support — the widest possible support set,
# because a NARROW support set manufactures false fabrications.
OCR_RUNS = ["ppv6", "ppbox", "ppv6-rot", "ppv6-s1440", "rapidpool", "tesseract"]
VLM_RUNS = ["q35-fair", "qwen", "qwen35-2b", "qwen35-2b-tok1024",
            "qwen35-2b-tok2560", "qwen4b-fair", "q35-rot", "q35-strict"]

TOK = re.compile(r"[a-z0-9$#%/.,\-']+")
# ⚠ A SHORT TOKEN CANNOT BE JUDGED. "of", "1", "a" collide across any two texts,
# so their support is meaningless in both directions and they are excluded from
# BOTH numerator and denominator — the same rule score.py applies to ambiguous
# artifacts.
MIN_LEN = 3


def toks(text):
    return [t for t in TOK.findall(S.norm(text or "")) if len(t) >= MIN_LEN]


def support_for(doc, stem):
    """Union of every OCR token at every angle, for one page."""
    sup, runs = set(), []
    for e in OCR_RUNS:
        for ang in ("", "a0", "a90", "a270"):
            t = C.engine_text(e, ang, doc, stem)
            if t is None:
                continue
            runs.append(f"{e}@{ang}" if ang else e)
            sup |= set(toks(t))
    return sup, runs


def loops(text, min_run=4, min_rep=4):
    """DEGENERATE DECODE LOOPS — the hallucination that actually happened.

    ⚠ FOUND ON q35-fair BK p006: a 250-long consecutive integer run
    92395…92644, each paired with `JUL-10-67`. Page 7 shows the source — the
    page carries ONE genuine recording stamp (`92334 JUL-10-67 92335`) and the
    model latched onto it and re-emitted it 250 times with a counter. Not a
    misreading; an autoregressive loop.

    ⚠ THIS IS DETECTABLE WITHOUT ANY MODEL OR ANY SUPPORT SET, which matters
    because it is the ONE failure mode that scales with page difficulty and
    silently triples a document's token count. Two signatures:

        counter  a long monotonic run of consecutive integers. Documents do not
                 count. Ledgers list, but they do not emit 250 in sequence.
        ngram    the same short phrase repeated far past any legal boilerplate.
    """
    t = toks(text)
    out = []
    nums = [int(x) for x in t if x.isdigit() and 2 <= len(x) <= 7]
    best, cur = [], []
    for a, b in zip(nums, nums[1:]):
        if b == a + 1:
            cur = (cur or [a]) + [b]
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    if len(cur) > len(best):
        best = cur
    if len(best) >= min_run:
        out.append(("counter", len(best), f"{best[0]}…{best[-1]}"))
    for n in (3, 4):
        c = collections.Counter(tuple(t[i:i + n]) for i in range(len(t) - n + 1))
        if not c:
            continue
        g, k = c.most_common(1)[0]
        if k >= min_rep and len(set(g)) > 1:
            out.append((f"{n}gram", k, " ".join(g)[:46]))
    return out


def key_text(key, stem):
    """Everything the hand key says is on this page — the arbiter."""
    blk = key.get(stem + ".png") or key.get(stem) or {}
    if not isinstance(blk, dict):
        return ""
    out = []
    for a in blk.get("artifacts") or []:
        for f in ("value", "text", "note"):
            if a.get(f):
                out.append(str(a[f]))
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vlm", default=None, help="one run, else all")
    ap.add_argument("--show", type=int, default=12)
    a = ap.parse_args()
    vlms = [a.vlm] if a.vlm else VLM_RUNS

    print("VLM FABRICATION AUDIT — is an unsupported token decidable?\n")
    rows = []
    samples = collections.defaultdict(list)
    for vlm in vlms:
        if not (BAKE / "out" / vlm).exists():
            continue
        n_tok = n_uns = n_rescued = 0
        pages = 0
        # ⚠ THE ARBITER IS WEAK AND THE CUT BY CLASS IS HOW WE WORK AROUND IT.
        # The hand keys list CRITICAL ARTIFACTS, not full page text, so a common
        # word the VLM read and OCR missed cannot be rescued by the key and is
        # scored as fabrication. That inflates the flag on film and book, where
        # OCR genuinely misses prose. On DIGITAL both engines score 100% on
        # artifacts and the text is born-digital, so OCR misses are near zero and
        # unsupported ≈ actually invented. Digital is therefore the only column
        # here that reads as a fabrication rate; film and book read as an upper
        # bound. Splitting digits from words matters for the same reason — a
        # disputed AMOUNT is not the same finding as an invented LABEL.
        per_cls = collections.defaultdict(lambda: [0, 0, 0, 0])  # tok,uns,dig,word
        for doc, kf, cls in KEYS:
            key = json.loads((DEC / kf).read_text(encoding="utf-8"))
            for stem in sorted(x[:-4] for x in key if x.endswith(".png")):
                vt = C.engine_text(vlm, "", doc, stem)
                if vt is None:
                    continue
                sup, runs = support_for(doc, stem)
                if not sup:
                    continue          # no OCR to support against — not judgeable
                pages += 1
                kt = set(toks(key_text(key, stem)))
                tv = toks(vt)
                n_tok += len(tv)
                per_cls[cls][0] += len(set(tv))
                for t in set(tv):
                    if t in sup:
                        continue
                    n_uns += 1
                    per_cls[cls][1] += 1
                    per_cls[cls][2 if any(c.isdigit() for c in t) else 3] += 1
                    # ⚠ THE KEY IS THE ARBITER, NOT THE OCR.
                    if t in kt:
                        n_rescued += 1        # VLM right, OCR blind — a WIN
                        samples[(vlm, "OCR-MISS")].append((doc, stem, t))
                    else:
                        samples[(vlm, "UNSUPPORTED")].append((doc, stem, t))
        if n_tok:
            rows.append((vlm, pages, n_tok, n_uns, n_rescued, dict(per_cls)))

    print(f"  {'vlm run':<20}{'pg':>4}{'tokens':>8}{'unsup':>7}{'rate':>7}"
          f"{'key-backed':>12}{'precision':>11}")
    print("  " + "-" * 69)
    for vlm, pg, nt, nu, nr, pc in sorted(rows, key=lambda r: r[3] / max(r[2], 1)):
        prec = (nu - nr) / nu if nu else 0.0
        print(f"  {vlm:<20}{pg:>4}{nt:>8,}{nu:>7}{nu/nt:>7.1%}{nr:>12}"
              f"{prec:>11.1%}")
    print("\n  rate       = share of distinct VLM tokens no OCR pass at any angle saw")
    print("  key-backed = unsupported BUT in the hand key — the VLM was right,")
    print("               OCR was blind. Flagging these would suppress real reads.")
    print("  ⚠ precision here is an UPPER BOUND ON FABRICATION, not a fabrication")
    print("    rate: the keys list CRITICAL ARTIFACTS only, so ordinary prose the")
    print("    VLM read and OCR missed cannot be rescued and is scored as invented.")

    print("\n  BY DOCUMENT CLASS — digital is the only honest column")
    print(f"  {'vlm run':<20}{'class':<9}{'distinct':>9}{'unsup':>7}{'rate':>7}"
          f"{'digits':>8}{'words':>7}")
    print("  " + "-" * 68)
    for vlm, pg, nt, nu, nr, pc in sorted(rows):
        for cls in ("digital", "book", "film"):
            if cls not in pc:
                continue
            t, u, d, w = pc[cls]
            if not t:
                continue
            print(f"  {vlm:<20}{cls:<9}{t:>9,}{u:>7}{u/t:>7.1%}{d:>8}{w:>7}")

    print(f"\n⚠ WHAT THE FLAG ACTUALLY CATCHES — read these, do not trust the rate")
    for (vlm, kind), got in sorted(samples.items()):
        if kind != "UNSUPPORTED" or not got:
            continue
        uniq = sorted({t for _d, _s, t in got})
        print(f"\n  {vlm} — {len(uniq)} distinct unsupported")
        print(f"    {' · '.join(uniq[:a.show])}")

    json.dump({"min_token_len": MIN_LEN, "ocr_support_runs": OCR_RUNS,
               "rows": [{"vlm": v, "pages": p, "tokens": t, "unsupported": u,
                         "key_backed": r,
                         "precision": (u - r) / u if u else None}
                        for v, p, t, u, r, _pc in rows],
               "unsupported_samples": {f"{k[0]}|{k[1]}": sorted({t for _d, _s, t in v})[:60]
                                       for k, v in samples.items()}},
              open(HERE / "_fabrication.json", "w"), indent=1)
    print("\nwrote _fabrication.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
