"""BUILD THE SIGNALS VOCABULARY from BSA resolutions — the corpus ACRIS does not have.

⚠ WHY BSA AND NOT DOB. Three sources were considered and only one can teach
vocabulary:
    DOB NOW    structured filing rows over Socrata. Those rows ARE signals-mode
               events — a filing is an intention — but they carry no prose, so
               there is nothing to learn a vocabulary FROM.
    DOB BIS    document access is REFUSED at the Akamai edge. Not retried.
    BSA        10,467 decisions already cached on disk. A resolution RECITES the
               application before granting it, so one document carries the
               proposal and the decision side by side.

⚠ THE GROUND TRUTH IS THE AGENT, NOT THE VERB. In a BSA resolution the APPLICANT
proposes and the BOARD resolves. Who is acting is structurally independent of the
cue words being tested, which is the only property that makes it usable as truth
— the same discipline as WHEREAS/NOW-THEREFORE in mode_build.py.

⚠ AND IT IS CHECKED AGAINST ACRIS. A signals cue that also fires on deeds and
mortgages has learned "legal English", not "intention". The control is the same
666-document census used everywhere else.
"""
from __future__ import annotations

import collections, glob, json, os, random, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

import lexicon

SAMPLE = int(os.environ.get("SAMPLE", 300))

# ── ground truth: who is acting in this clause ────────────────────────────
APPLICANT = re.compile(r"\b(?:the\s+)?applicants?\b|\bthe\s+owners?\b|"
                       r"\bpetitioners?\b", re.I)
BOARD = re.compile(r"\bthe\s+Board\b|\bit\s+is\s+Resolved\b|\bthis\s+Board\b|"
                   r"\bResolved\s+that\b", re.I)

CAND = [
 ("seeks",        r"\bseeks?\b|\brequests?\b|\bapplies\s+for\b"),
 ("proposes",     r"\bproposes?\b|\bproposed\b"),
 ("intends",      r"\bintends?\s+to\b|\bcontemplates?\b|\banticipates?\b"),
 ("would_will",   r"\bwould\s+(?:be|have|permit|allow|result)\b|"
                  r"\bwill\s+(?:be|have|permit|allow|result)\b"),
 ("to_permit",    r"\bto\s+permit\b|\bto\s+allow\b"),
 ("application",  r"\bapplication\b|\bpetition\b"),
 ("submitted",    r"\bsubmitt?ed\b|\brepresents?\s+that\b|\bstates?\s+that\b|"
                  r"\basserts?\s+that\b"),
 ("if_granted",   r"\bif\s+granted\b|\bin\s+the\s+event\s+that\b|\bif\s+and\s+when\b"),
 ("upon_future",  r"\bupon\s+(?:completion|issuance|approval|obtaining)\s+of\b|"
                  r"\bsubject\s+to\s+(?:obtaining|receipt\s+of|approval)\b"),
 ("estimated",    r"\bestimated\b|\bapproximately\b|\bprojected\b"),
 # the decision side, as a contrast set — these must NOT look like signals
 ("resolved",     r"\bResolved\s+that\b|\bhereby\s+(?:grants?|denies|approves?)\b"),
 ("board_finds",  r"\bfinds?\s+that\b|\bdetermines?\s+that\b|\bconcludes?\s+that\b"),
]
CC = [(n, re.compile(p, re.I)) for n, p in CAND]


def bsa_texts(n):
    """Text from cached BSA PDFs. Already on disk — nothing is fetched."""
    from pypdf import PdfReader
    files = sorted(glob.glob(os.path.join(HERE, "bsa_cache", "*.pdf")))
    random.Random(11).shuffle(files)
    out, bad = {}, 0
    for f in files:
        if len(out) >= n:
            break
        try:
            t = "\n".join((p.extract_text() or "") for p in PdfReader(f).pages)
        except Exception:
            bad += 1
            continue
        # ⚠ AN EMPTY READ IS NOT A READ — scanned-only decisions are dropped,
        # never scored as "no signals language".
        if len(t.strip()) < 400:
            bad += 1
            continue
        out[os.path.basename(f)[:-4]] = t
    return out, bad


def acris_texts():
    ty = json.load(open(os.path.join(HERE, "_doctype_of.json"), encoding="utf-8"))
    out = {}
    for f in glob.glob(os.path.join(HERE, "census_head", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        doc = str(d["doc_id"])
        t = " ".join((p.get("accepted_text") or "") for p in d.get("pages") or [])
        if len(t.strip()) >= 200 and doc in ty:
            out[doc] = t
    return out


def main():
    bsa, bad = bsa_texts(SAMPLE)
    if not bsa:
        print("  ⚠ NO READABLE BSA TEXT — stop.")
        return 1
    acris = acris_texts()
    print(f"BSA      {len(bsa)} decisions read · {bad} dropped (unreadable or scan-only)")
    print(f"CONTROL  {len(acris)} ACRIS documents\n")

    lab = collections.Counter()
    per = collections.defaultdict(collections.Counter)
    ctrl_cl = 0
    ctrl = collections.Counter()
    ex = collections.defaultdict(list)

    for cal, text in bsa.items():
        for cl, _ in lexicon.clauses(text):
            a, b = APPLICANT.search(cl), BOARD.search(cl)
            # ⚠ a clause naming BOTH is discarded, not guessed at
            side = ("applicant" if a and not b else
                    "board" if b and not a else None)
            if not side:
                continue
            lab[side] += 1
            for n, rx in CC:
                if rx.search(cl):
                    per[n][side] += 1
                    if side == "applicant" and len(ex[n]) < 2:
                        ex[n].append(cl.strip()[:120])

    for doc, text in acris.items():
        for cl, _ in lexicon.clauses(text):
            ctrl_cl += 1
            for n, rx in CC:
                if rx.search(cl):
                    ctrl[n] += 1

    print(f"GROUND TRUTH — applicant-agent clauses {lab['applicant']:,} · "
          f"board-agent {lab['board']:,}")
    print(f"CONTROL      — {ctrl_cl:,} ACRIS clauses\n")

    hdr = (f"  {'cue':<14}{'applic':>8}{'board':>7}{'lean':>7}"
           f"{'ACRIS':>8}{'leak':>7}   verdict")
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    keep, drop = [], []
    for n, _ in CAND:
        a, b = per[n]["applicant"], per[n]["board"]
        tot = a + b
        lean = a / tot if tot else 0
        leak = ctrl[n] / ctrl_cl if ctrl_cl else 0
        if tot < 15:
            v, tag = "too rare (n<15) — unread", "rare"
        elif leak > .02:
            v, tag = f"⚠ LEAKS into ACRIS — legal English, not intention", "drop"
        elif lean >= .70:
            v, tag = f"separates ({lean*100:.0f}% applicant)", "keep"
        elif lean <= .30:
            v, tag = f"decision-side ({(1-lean)*100:.0f}% board) — contrast set", "contrast"
        else:
            v, tag = f"⚠ no separation ({lean*100:.0f}%)", "drop"
        (keep if tag == "keep" else drop).append((n, tag))
        print(f"  {n:<14}{a:>8}{b:>7}{lean*100:>6.0f}%{ctrl[n]:>8}{leak*100:>6.1f}%   {v}")

    k = [n for n, t in keep]
    print(f"\n  KEEP {len(k)}: " + (", ".join(k) if k else "nothing"))
    print("  DROP/other: " + ", ".join(f"{n}({t})" for n, t in drop))

    if k:
        rx = re.compile("|".join(f"(?:{dict(CAND)[n]})" for n in k), re.I)
        hit = sum(1 for cal, t in bsa.items() if rx.search(t))
        cl_hit = sum(1 for doc, t in acris.items() if rx.search(t))
        print(f"\n  UNION  fires on {hit}/{len(bsa)} BSA decisions "
              f"({100*hit/len(bsa):.0f}%)")
        print(f"         fires on {cl_hit}/{len(acris)} ACRIS documents "
              f"({100*cl_hit/len(acris):.0f}%)  <- document-level leak")
        for n in k[:4]:
            if ex[n]:
                print(f"\n  {n}: {ex[n][0]!r}")

    json.dump({"keep": k, "drop": [n for n, _ in drop],
               "truth": dict(lab), "control_clauses": ctrl_cl,
               "measured_against": f"BSA {len(bsa)} cached decisions, "
                                   f"applicant/board agent labels; control = "
                                   f"{len(acris)} ACRIS census documents"},
              open(os.path.join(HERE, "_signals_vocab.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
