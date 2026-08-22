"""BUILD THE MODE VOCABULARY — the emptiest axis, and the one holding up the rest.

⚠ WHY THIS COULD NOT BE DONE AT DOCUMENT LEVEL. ACRIS is a register of
TRANSACTIONS: of 21,612,352 documents essentially all of them transact. There is
no signals corpus and no observes corpus inside it — the biggest "signal" types
are CERT 55,876 and DECL 19,254, and both are recorded instruments that bind.
Scoring mode cues against that corpus would produce a beautiful number that means
nothing, because the corpus has one class. That is the same universe error this
project has already paid for three times: the query succeeds and answers a
narrower question than the one asked.

⚠ MODE IS A PROPERTY OF THE EVENT, AND ONE DOCUMENT EMITS SEVERAL EVENTS. The
correct unit is therefore the CLAUSE, not the document — and at clause level a
single deed genuinely carries all three:
    "Owner is the owner of record of the Premises"      observes
    "Owner does hereby grant and release unto Grantee"  transacts
    "Grantee intends to construct a building thereon"   signals

⚠ GROUND TRUTH WITHOUT HAND-LABELLING. Legal drafting is structurally honest:
RECITALS sit under WHEREAS and state facts; OPERATIVE language sits under NOW
THEREFORE and changes them. That convention is the label. It is not perfect — it
is INDEPENDENT of the cue words being tested, which is the only property that
makes it usable as truth.

⚠ THE TRAP THIS EXISTS TO CATCH. A signal can QUOTE a transaction: a lis pendens
recites the deed's own performative words. So a transacts cue inside a citation
context is measured SEPARATELY and never counted as agreement.
"""
from __future__ import annotations

import collections, glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

import lexicon

# ── structural ground truth — independent of every cue below ───────────────
RECITAL = re.compile(r"\bWHEREAS\b", re.I)
OPERATIVE = re.compile(r"\bNOW,?\s*THEREFORE\b|\bIN\s+CONSIDERATION\s+OF\b", re.I)

# ⚠ a citation context. A performative verb in here is QUOTED, not performed.
QUOTED = re.compile(r"\bthat\s+certain\b|\bpursuant\s+to\b|\bdated\s+as\s+of\b|"
                    r"\brecorded\s+(?:in|on|at)\b|\bset\s+forth\s+in\b|"
                    r"\bdescribed\s+in\b|\bCRFN\b|\breel\b", re.I)

CAND = {
 "transacts": [
  ("perform_grant",  r"do(?:es)?\s*hereby\s*(?:grant|convey|demise|mortgage|assign|"
                     r"release|remise|bargain|sell|transfer|quitclaim)"),
  ("hereby_verb",    r"\bhereby\s+(?:grants?|conveys?|assigns?|releases?|declares?|"
                     r"covenants?|agrees?|transfers?)\b"),
  ("witnesseth",     r"\bWITNESSETH\b|\bIN\s+WITNESS\s+WHEREOF\b"),
  ("executed",       r"\bexecuted\s+and\s+delivered\b|\bhas\s+caused\s+this\b"),
  ("consideration",  r"\bin\s+consideration\s+of\s+the\s+sum\b|\breceipt\s+whereof\b"),
 ],
 "observes": [
  ("is_owner",       r"\bis\s+the\s+(?:owner|holder|lessee|fee\s+owner)\s+of\b"),
  ("known_as",       r"\b(?:known\s+as|designated\s+as|identified\s+as)\b"),
  ("as_of_state",    r"\bas\s+of\s+the\s+date\s+hereof\b|\bpresently\b|\bcurrently\b"),
  ("balance_is",     r"\b(?:outstanding|unpaid|principal)\s+(?:balance|amount)\s+"
                     r"(?:is|of)\b|\bthere\s+(?:is|remains)\s+(?:now\s+)?(?:due|owing)\b"),
  ("was_recorded",   r"\bwas\s+(?:duly\s+)?recorded\b|\bhas\s+been\s+(?:duly\s+)?recorded\b"),
 ],
 "signals": [
  ("intends",        r"\bintends?\s+to\b|\bproposes?\s+to\b|\bcontemplates?\b|"
                     r"\banticipates?\b"),
  ("will_apply",     r"\b(?:will|shall)\s+(?:apply|seek|file|submit)\s+for\b"),
  ("conditional",    r"\bsubject\s+to\s+(?:obtaining|receipt\s+of|approval)\b|"
                     r"\bin\s+the\s+event\s+that\b|\bif\s+and\s+when\b"),
  ("upon_future",    r"\bupon\s+(?:completion|issuance|approval)\s+of\b"),
  ("estimated",      r"\bestimated\s+(?:cost|value|completion)\b|\bapproximately\b"),
 ],
}
CC = {m: [(n, re.compile(p, re.I)) for n, p in v] for m, v in CAND.items()}


def corpus():
    ty = json.load(open(os.path.join(HERE, "_doctype_of.json"), encoding="utf-8"))
    out, blank = {}, 0
    for f in glob.glob(os.path.join(HERE, "census_head", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        doc = str(d["doc_id"])
        t = " ".join((p.get("accepted_text") or "") for p in d.get("pages") or [])
        if len(t.strip()) < 200 or doc not in ty:
            blank += 1
            continue
        out[doc] = (ty[doc], t)
    return out, blank


def fires(clause):
    """{mode: [cue names]} for one clause."""
    return {m: [n for n, rx in pats if rx.search(clause)]
            for m, pats in CC.items()}


def main():
    c, dropped = corpus()
    print(f"corpus {len(c)} documents scored · {dropped} dropped\n")

    # ── every clause, with its structural label where one exists ──────────
    n_cl = 0
    truth = collections.Counter()
    agree = collections.defaultdict(collections.Counter)   # label -> mode fired
    percue = collections.defaultdict(collections.Counter)  # cue -> label
    collide = 0
    fired_any = 0
    quoted_perf = 0
    examples = collections.defaultdict(list)

    for doc, (t, text) in c.items():
        for clause, off in lexicon.clauses(text):
            n_cl += 1
            lab = ("recital" if RECITAL.search(clause) else
                   "operative" if OPERATIVE.search(clause) else None)
            f = fires(clause)
            hot = [m for m, v in f.items() if v]
            if hot:
                fired_any += 1
            if len(hot) > 1:
                collide += 1
            if f["transacts"] and QUOTED.search(clause):
                quoted_perf += 1
                if len(examples["quoted"]) < 3:
                    examples["quoted"].append((doc, clause[:150]))
            if lab:
                truth[lab] += 1
                for m in hot:
                    agree[lab][m] += 1
                for m, cues in f.items():
                    for cue in cues:
                        percue[cue][lab] += 1

    print(f"CLAUSES {n_cl:,} · at least one mode cue fired on {fired_any:,} "
          f"({100*fired_any/n_cl:.0f}%)")
    print(f"  ⚠ COLLISIONS (2+ modes on one clause) {collide:,} = "
          f"{100*collide/max(fired_any,1):.0f}% of fired clauses")
    print(f"  ⚠ QUOTED PERFORMATIVE (transacts cue inside a citation) {quoted_perf:,} = "
          f"{100*quoted_perf/max(fired_any,1):.0f}% of fired clauses\n")

    print(f"STRUCTURAL GROUND TRUTH — WHEREAS={truth['recital']:,} recital clauses · "
          f"NOW THEREFORE={truth['operative']:,} operative clauses")
    if not truth["recital"] or not truth["operative"]:
        print("  ⚠ ONE CLASS IS EMPTY — nothing can be measured. Stop.")
        return 1
    print(f"  {'label':<11}{'n':>7}   " + "".join(f"{m:>12}" for m in CAND))
    for lab in ("recital", "operative"):
        print(f"  {lab:<11}{truth[lab]:>7}   " +
              "".join(f"{100*agree[lab][m]//max(truth[lab],1):>11}%" for m in CAND))

    # ── which cues actually DISCRIMINATE ──────────────────────────────────
    print("\nPER-CUE — does it separate recital from operative?")
    print(f"  {'cue':<16}{'mode':<11}{'recital':>9}{'operative':>11}   verdict")
    keep, drop = [], []
    for m in CAND:
        for cue, _ in CAND[m]:
            r, o = percue[cue]["recital"], percue[cue]["operative"]
            tot = r + o
            if tot < 10:
                v, tag = "TOO RARE (n<10) — unread", "rare"
            else:
                want = "operative" if m == "transacts" else "recital"
                got = o if want == "operative" else r
                frac = got / tot
                if frac >= .70:
                    v, tag = f"separates ({frac*100:.0f}% {want})", "keep"
                elif frac <= .30:
                    v, tag = f"⚠ INVERTED ({(1-frac)*100:.0f}% the other way)", "drop"
                else:
                    v, tag = f"⚠ no separation ({frac*100:.0f}%)", "drop"
            (keep if tag == "keep" else drop).append((cue, m))
            print(f"  {cue:<16}{m:<11}{r:>9}{o:>11}   {v}")

    print(f"\n  KEEP {len(keep)}: " + ", ".join(c for c, _ in keep))
    print(f"  DROP {len(drop)}: " + ", ".join(c for c, _ in drop))

    if examples["quoted"]:
        print("\n⚠ QUOTED-PERFORMATIVE EXAMPLES — a transacts cue that is NOT a transaction:")
        for doc, ex in examples["quoted"]:
            print(f"   {doc}\n     {ex!r}")

    json.dump({"clauses": n_cl, "fired": fired_any, "collide": collide,
               "quoted_performative": quoted_perf,
               "truth": dict(truth),
               "agree": {k: dict(v) for k, v in agree.items()},
               "keep": [c for c, _ in keep], "drop": [c for c, _ in drop],
               "measured_against": "census_head, %d docs, clause-level, "
                                   "WHEREAS/NOW-THEREFORE structural labels" % len(c)},
              open(os.path.join(HERE, "_mode_vocab.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
