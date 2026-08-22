"""THE EXTRACTION RESOLVER. Several channels in, ONE evidence record out.

    python fuse.py --doc BK_6730047100023 --vlm q35-fair --ocr ppv6
    python fuse.py --all --vlm q35-fair --ocr ppv6

This is the joint the pipeline was missing. Three channels already existed and
produced three different shapes; nothing combined them, so `claims.py` was
reading ONE engine's .txt and calling it the document. Every accuracy number
this project has measured was per-engine for that reason - there has never been
a number for what the SYSTEM reads, only for what a model reads.

⚠ THIS LAYER DOES NOT REASON, AND THAT IS THE WHOLE DESIGN.
It settles CHARACTERS, not meaning. No party is given a role here, no amount is
interpreted, no document type is decided. Those are resolution's job and they
are downstream of this file. The output is the evidence record: what the page
says, how firmly that was established, and where the reading is still open.
Mixing the two is how a transcription defect becomes a semantic fact with
provenance attached.

⚠ NEVER ALIGN ON LINES. THE CHANNELS DO NOT AGREE ON WHAT A LINE IS.
Measured on FT_1680008647768 p003: the VLM returned 9 lines (one per
paragraph); Paddle returned the SAME 4,500 characters as ONE line. A
line-aligned fuser scored 0.0% agreement with ZERO disputed runs across all
three eras - not a low score, an impossible one, and the shape of the failure
(everything "single channel", nothing merely disagreeing) is what exposed it.
Line breaks are a layout artefact of each engine and change with rotation and
preprocessing. Tokens are what both channels actually claim to have read, so
tokens are the unit of comparison.

⚠ AGREEMENT IS THE UNIT OF CONFIDENCE, NOT A MODEL'S SELF-REPORT.
A model's own confidence is an opinion about its own output. Two channels that
read the page independently and land on the same characters is evidence. So
`established_by = image_agreement` is a stronger claim than any single engine's
logprob, and it is the only status this file marks accepted outright.

⚠ DISAGREEMENT IS NOT RESOLVED HERE. IT IS RECORDED.
The tempting shortcut is to keep the better engine's run and move on - Qwen3.5
blends 98.8% against Paddle's 96.5%, so "trust Qwen" wins most of the time and
is wrong exactly where it matters. A disputed run is where the page is hard,
which is where the value that matters usually sits. Both readings are kept,
accepted stays null, and the run is handed up for escalation. Silently picking
a winner would convert the system's one honest uncertainty signal into a
confident wrong answer.

⚠ THE INDEX IS ATTACHED, NEVER MERGED.
It did not read the page. It corroborates fields the source already holds in
machine-readable form, and it lives in its own block so that no downstream
reader can mistake a recorded value for a read one.
"""
from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "bakeoff" / "out"

VERSION = "fuse/1.1-token"

# A disputed run longer than this is not one misread phrase - it is a stretch
# where the channels diverged structurally (one read a stamp block the other
# skipped). Kept, but labelled differently, because the remedies differ: a
# short run is a crop for escalation, a long one is a page to re-read.
RUN_SPLIT = 12

# ⚠ 1.0 DISABLES SUB-BLOCK ACCEPTANCE (the original, fully conservative
# behaviour). Lower values accept a token pair inside a replace block when the
# two channels are close enough, and CALIBRATION IS THE ONLY WAY TO SET IT:
# accepting more can never inflate the answer-key score, because wrong text
# does not match an artifact - so a rise in `accepted` is a real gain, and a
# fall in `ceiling` is real damage.
FUZZY = 1.0

TOKEN = re.compile(r"\S+")
# Rotation writes one file per angle: pNNN.a0 / .a90 / .a180 / .a270.
# They are the SAME PAGE read at different orientations.
ANGLE_SUFFIX = re.compile(r"\.a\d{1,3}$")


def norm(tok: str) -> str:
    """Comparison key ONLY.

    ⚠ NEVER STORE THIS. Normalising for comparison is correct; storing the
    normalised form silently edits the document - it lowercases a name, eats
    the spacing in "16 feet 3 inches", and the evidence record then disagrees
    with the image it claims to represent. Accepted text is always a channel's
    own rendering, verbatim.
    """
    t = tok.replace("’", "'").replace("“", '"').replace("”", '"')
    t = t.replace("—", "-").replace("–", "-")
    t = re.sub(r"[^0-9a-zA-Z]+", "", t).lower()
    return t


def page_key(name: str) -> str:
    """⚠ p001.txt AND p001.png.txt ARE THE SAME PAGE.

    The VLM runner writes `p001.txt`; the Paddle runner writes `p001.png.txt`.
    Joining on the raw filename returns an EMPTY intersection, which reads as
    "these engines share no pages" rather than as the naming bug it is - a
    silent zero that would have made this whole file look like it worked.

    ⚠ AND SO ARE p001.a0, p001.a90 AND p001.a270 — THIS COST A FALSE QUALITY
    COLLAPSE. The rotation runner writes one file PER ANGLE (`pNNN.a{angle}.txt`).
    Stripping only file extensions left each angle as its own "page", so the VLM's
    `p001.a90` never met Paddle's `p001`. Measured on the rotation evidence:
    BK went to 11 "pages" with 3 having both channels, FT to 18 with 5, and the
    agreement rate read 0.18 / 0.26 — a catastrophic-looking regression that was
    entirely a join failure. Nothing about the reading had changed.

    The guard above fires only on an EMPTY intersection. A PARTIAL one survives
    it and is worse, because a plausible-but-wrong number invites explanation
    instead of investigation.
    """
    n = name
    for suf in (".txt", ".png", ".tif", ".tiff", ".jpg"):
        while n.endswith(suf):
            n = n[: -len(suf)]
    return ANGLE_SUFFIX.sub("", n)


def load_channel(engine: str, doc: str) -> dict[str, str]:
    d = OUT / engine / doc
    if not d.is_dir():
        return {}
    out = {}
    for f in sorted(d.glob("*.txt")):
        # ⚠ A ZERO-BYTE FILE IS A FAILED READ, NOT AN EMPTY PAGE. The harness
        # has written these on HTTP 200 before. Treated as an empty string it
        # would count as "this channel read the page and saw nothing".
        if f.stat().st_size == 0:
            continue
        out[page_key(f.name)] = f.read_text(encoding="utf-8", errors="replace")
    return out


def tokens(text: str):
    """Surface forms plus their character offset in this channel's own text.

    The offset is what lets a disputed run be pointed at later - and, once the
    OCR channel carries boxes, what ties that run to a pixel region.
    """
    return [(m.group(), m.start()) for m in TOKEN.finditer(text)]


def fuse_page(a_toks, b_toks, a_name, b_name):
    """Align two token streams and emit AGREED and DISPUTED runs."""
    ka = [norm(t) for t, _ in a_toks]
    kb = [norm(t) for t, _ in b_toks]
    sm = difflib.SequenceMatcher(a=ka, b=kb, autojunk=False)
    runs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            if i2 == i1:
                continue
            runs.append({
                "status": "agreed",
                "established_by": "image_agreement",
                "accepted": " ".join(t for t, _ in a_toks[i1:i2]),
                "n_tokens": i2 - i1,
                # ⚠ THE TOKEN SPAN IS THE ADDRESS, NOT THE CHAR OFFSET.
                # Locating a run on the image means walking the OCR channel's
                # own recognition items, which are counted in tokens. Deriving
                # that back from a character offset works until one channel
                # changes its spacing, and then it is wrong silently.
                "span": {a_name: [i1, i2], b_name: [j1, j2]},
                "offsets": {a_name: a_toks[i1][1], b_name: b_toks[j1][1]},
            })
        elif FUZZY < 1.0 and (i2 - i1) == (j2 - j1) and (i2 - i1) > 0:
            # ⚠ A REPLACE BLOCK IS ATOMIC BY DEFAULT AND THAT IS WHAT HOLDS
            # `accepted` DOWN. difflib reports a 20-token replace as one event,
            # so 18 tokens both channels read identically are buried with the 2
            # they fought over, and all 20 land in the escalation queue.
            # Measured: book asserted only 54.2% of its CRITICAL artifacts while
            # its ceiling was 97.6% - the readings were present, just not
            # separable.
            #
            # ⚠ ONLY WHEN THE TWO SIDES ARE THE SAME LENGTH. Positional pairing
            # across different lengths is exactly the mistake that manufactured
            # false disputes from reading-order differences; an equal-length
            # block is the one case where token k on each side is the same word
            # on the page rather than an assumption about it.
            #
            # ⚠ AND ACCEPTING A FUZZY PAIR MEANS PICKING A RENDERING. The VLM's
            # is taken, because it is the stronger reader on this corpus - which
            # is a policy, not a fact, so it is gated by FUZZY and the gate is
            # calibrated against the answer keys rather than chosen.
            for k in range(i2 - i1):
                av1, bv1 = a_toks[i1 + k][0], b_toks[j1 + k][0]
                na, nb = norm(av1), norm(bv1)
                sim = (1.0 if na == nb else
                       difflib.SequenceMatcher(a=na, b=nb).ratio())
                if sim >= FUZZY:
                    runs.append({
                        "status": "agreed", "established_by": "image_agreement",
                        "accepted": av1, "n_tokens": 1, "fuzzy": round(sim, 3),
                        "span": {a_name: [i1 + k, i1 + k + 1],
                                 b_name: [j1 + k, j1 + k + 1]},
                        "offsets": {a_name: a_toks[i1 + k][1],
                                    b_name: b_toks[j1 + k][1]}})
                else:
                    runs.append({
                        "status": "disputed", "established_by": "unresolved",
                        "accepted": None, "n_tokens": 1, "scale": "phrase",
                        "similarity": round(sim, 3), a_name: av1, b_name: bv1,
                        "span": {a_name: [i1 + k, i1 + k + 1],
                                 b_name: [j1 + k, j1 + k + 1]},
                        "offsets": {a_name: a_toks[i1 + k][1],
                                    b_name: b_toks[j1 + k][1]}})
        else:
            av = " ".join(t for t, _ in a_toks[i1:i2])
            bv = " ".join(t for t, _ in b_toks[j1:j2])
            n = max(i2 - i1, j2 - j1)
            runs.append({
                # ⚠ "one channel read nothing here" and "the two read this
                # differently" are DIFFERENT FINDINGS and must not collapse:
                # the first is a coverage gap, the second is a character
                # dispute. Only the second is evidence the page is hard.
                "status": "disputed" if (av and bv) else "single_channel",
                "established_by": "unresolved",
                "accepted": None,
                "n_tokens": n,
                "scale": "phrase" if n <= RUN_SPLIT else "block",
                a_name: av or None,
                b_name: bv or None,
                "span": {a_name: [i1, i2], b_name: [j1, j2]},
                "offsets": {
                    a_name: a_toks[i1][1] if i2 > i1 else None,
                    b_name: b_toks[j1][1] if j2 > j1 else None,
                },
            })
    return runs


def reconcile(runs, a_name, b_name):
    """Separate ORDER ARTEFACTS from real gaps. Page-local, no geometry needed.

    ⚠ difflib ASSUMES BOTH CHANNELS EMIT TOKENS IN THE SAME ORDER. THEY DO NOT.
    The VLM follows reading order; Paddle follows layout detection. On a form
    with stacked fields they emit the same content in different sequence, and a
    monotonic aligner cannot match them - so it reports the leftovers as
    disagreements. Measured on 2015022400608001 p002: the VLM's "1112" and
    Paddle's "1112" are the SAME field, but they landed in different runs, and
    the fuser dutifully reported "10140 vs 1112" and "1112 vs Queens" as two
    character disputes. Neither is a dispute. Both are one shift.

    ⚠ THE TEST FOR IT IS THE ONE QUESTION THAT MATTERS DOWNSTREAM: is this text
    MISSING from the other channel, or merely somewhere else in it? A token
    that turns up unmatched on BOTH sides of the page was read by both readers
    - it is an alignment failure, not evidence about the page. Only what
    survives that filter is a real gap, and only a real gap is worth a crop.

    ⚠ CLASSIFIED PER SIDE, NEVER PER RUN. In the p002 case Paddle's side is an
    order artefact while the VLM's side ("10140") is genuinely unmatched. Judge
    the run as a whole and one of those two facts is destroyed.
    """
    from collections import Counter
    ua, ub = Counter(), Counter()
    for r in runs:
        if r["status"] == "agreed":
            continue
        for t in TOKEN.findall(r.get(a_name) or ""):
            ua[norm(t)] += 1
        for t in TOKEN.findall(r.get(b_name) or ""):
            ub[norm(t)] += 1
    shared = ua & ub          # Counter intersection = min count on each side

    ledger = {"order_artifact": sum(shared.values()) * 2,
              f"{a_name}_only": sum((ua - shared).values()),
              f"{b_name}_only": sum((ub - shared).values())}

    for r in runs:
        if r["status"] == "agreed":
            continue
        at = [norm(t) for t in TOKEN.findall(r.get(a_name) or "")]
        bt = [norm(t) for t in TOKEN.findall(r.get(b_name) or "")]
        a_else = [t for t in at if shared.get(t)]
        b_else = [t for t in bt if shared.get(t)]
        r["elsewhere"] = {a_name: len(a_else), b_name: len(b_else)}
        r["unmatched"] = {a_name: [t for t in at if not shared.get(t)],
                          b_name: [t for t in bt if not shared.get(t)]}
        # Every token on both sides turns up in the other channel: pure shift.
        if at and bt and len(a_else) == len(at) and len(b_else) == len(bt):
            r["status"] = "unaligned"
            r["established_by"] = "unresolved"
        elif not r["unmatched"][a_name] and not r["unmatched"][b_name]:
            r["status"] = "unaligned"
            r["established_by"] = "unresolved"
    return ledger


def fuse_doc(doc, vlm, ocr, index_path=None):
    A, B = load_channel(vlm, doc), load_channel(ocr, doc)
    keys = sorted(set(A) | set(B))
    shared = sorted(set(A) & set(B))
    # ⚠ AN EMPTY INTERSECTION IS THE NAMING BUG, NOT A RESULT.
    if keys and not shared:
        raise SystemExit(
            f"  {doc}: {len(A)} {vlm} pages and {len(B)} {ocr} pages share NO "
            f"page key. That is the p001 / p001.png join, not a real gap.\n"
            f"    {vlm}: {sorted(A)[:3]}\n    {ocr}: {sorted(B)[:3]}")

    pages = []
    tok_agreed = tok_disputed = tok_single = tok_unaligned = 0
    gaps = {vlm: 0, ocr: 0}
    for k in keys:
        at, bt = tokens(A.get(k, "")), tokens(B.get(k, ""))
        if not at or not bt:
            # ⚠ ONE CHANNEL SILENT IS NOT AGREEMENT. Whatever the other read
            # stands UNACCEPTED: nothing corroborated it.
            only, toks = (vlm, at) if at else (ocr, bt)
            runs = ([{"status": "single_channel", "established_by": "unresolved",
                      "accepted": None, "n_tokens": len(toks), "scale": "block",
                      only: " ".join(t for t, _ in toks)}] if toks else [])
        else:
            runs = fuse_page(at, bt, vlm, ocr)
        ledger = reconcile(runs, vlm, ocr)
        for r in runs:
            if r["status"] == "agreed":
                tok_agreed += r["n_tokens"]
            elif r["status"] == "disputed":
                tok_disputed += r["n_tokens"]
            elif r["status"] == "unaligned":
                tok_unaligned += r["n_tokens"]
            else:
                tok_single += r["n_tokens"]
        pa = sum(r["n_tokens"] for r in runs if r["status"] == "agreed")
        pt = sum(r["n_tokens"] for r in runs)
        pages.append({
            "page": k,
            "channels_present": [n for n, d in ((vlm, A), (ocr, B)) if k in d],
            "token_agreement": round(pa / pt, 4) if pt else None,
            # ⚠ THE ACCEPTED TEXT KEEPS SAYING [UNRESOLVED]. It is an honest
            # record of the page, not a best-effort reconstruction of it. A
            # gap that quietly closes here is a gap nobody downstream can see.
            "accepted_text": " ".join(
                r["accepted"] if r["accepted"] is not None else "[UNRESOLVED]"
                for r in runs),
            "token_ledger": ledger,
            "runs": runs,
        })
        gaps[vlm] += ledger.get(f"{vlm}_only", 0)
        gaps[ocr] += ledger.get(f"{ocr}_only", 0)

    total = tok_agreed + tok_disputed + tok_single + tok_unaligned
    rec = {
        "doc_id": doc,
        "extractor_version": VERSION,
        "channels": {"vlm": vlm, "ocr": ocr,
                     "structured_record": bool(index_path)},
        "pages": pages,
        "coverage": {
            "pages_total": len(keys),
            "pages_both_channels": len(shared),
            # ⚠ THE DENOMINATOR IS PRINTED ON PURPOSE. A bare "98%" with no
            # count underneath it is how this project has been fooled before.
            "tokens_total": total,
            "tokens_agreed": tok_agreed,
            "tokens_disputed": tok_disputed,
            # Both channels read it; the aligner could not line them up. NOT a
            # disagreement about the page, and NOT worth a crop.
            "tokens_unaligned": tok_unaligned,
            "tokens_single_channel": tok_single,
            "agreement_rate": round(tok_agreed / total, 4) if total else None,
            # ⚠ THE ONLY HONEST ANSWER TO "WHAT DID EACH READER MISS".
            # A token counted here appears in ONE channel and NOWHERE in the
            # other. For the OCR side that is settled - Paddle carries a box,
            # so pixels exist and the VLM genuinely missed real text. For the
            # VLM side it is NOT settled: with no coordinates, "Paddle missed
            # it" and "the VLM invented it" look identical from the text alone,
            # and only a crop of the anchored region can tell them apart.
            "unmatched_tokens": gaps,
        },
        # Attached, never merged. See the module docstring.
        "structured_record": (json.loads(pathlib.Path(index_path)
                                         .read_text(encoding="utf-8"))
                              if index_path else None),
    }
    return rec


def escalation_queue(rec):
    """Every run this document cannot settle from the image alone.

    ⚠ NOT FILTERED BY IMPORTANCE HERE. What is material is a judgement about
    MEANING, and meaning is not this layer's business. Extraction says "these
    runs are open"; resolution decides which of them are worth a frontier model.
    """
    q = []
    for p in rec["pages"]:
        for i, r in enumerate(p["runs"]):
            if r["status"] in ("disputed", "single_channel"):
                q.append({"doc_id": rec["doc_id"], "page": p["page"],
                          "run_index": i, **r})
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--vlm", default="q35-fair")
    ap.add_argument("--ocr", default="ppv6")
    ap.add_argument("--index", default=None)
    ap.add_argument("--fuzzy", type=float, default=1.0,
                    help="accept a token pair inside a replace "
                         "block at >= this similarity (1.0 = off)")
    a = ap.parse_args()
    global FUZZY
    FUZZY = a.fuzzy

    if a.all:
        docs = sorted(set(p.name for p in (OUT / a.vlm).iterdir() if p.is_dir())
                      & set(p.name for p in (OUT / a.ocr).iterdir() if p.is_dir()))
    else:
        docs = [a.doc]
    if not docs or docs == [None]:
        raise SystemExit("  need --doc or --all")

    outdir = HERE / "_evidence"
    outdir.mkdir(exist_ok=True)
    print(f"  extraction resolver {VERSION}   vlm={a.vlm}  ocr={a.ocr}\n")
    for doc in docs:
        rec = fuse_doc(doc, a.vlm, a.ocr, a.index)
        q = escalation_queue(rec)
        c = rec["coverage"]
        (outdir / f"{doc}.json").write_text(json.dumps(rec, indent=1),
                                            encoding="utf-8")
        (outdir / f"{doc}.escalate.json").write_text(json.dumps(q, indent=1),
                                                     encoding="utf-8")
        phrase = sum(1 for r in q if r.get("scale") == "phrase")
        g = c["unmatched_tokens"]
        print(f"  {doc}")
        print(f"    pages  {c['pages_total']:>3}   both channels {c['pages_both_channels']:>3}")
        print(f"    tokens {c['tokens_total']:>5}   agreed {c['tokens_agreed']:>5} "
              f"({c['agreement_rate']:.1%})")
        print(f"      disputed  {c['tokens_disputed']:>5}   "
              f"unaligned {c['tokens_unaligned']:>5} (both read it, order differs)   "
              f"one-channel {c['tokens_single_channel']:>5}")
        print(f"      genuinely unmatched: " +
              "   ".join(f"{k} {v}" for k, v in g.items()))
        print(f"    escalation queue: {len(q)} runs ({phrase} phrase-scale)\n")
    print(f"  -> {outdir}")


if __name__ == "__main__":
    main()
