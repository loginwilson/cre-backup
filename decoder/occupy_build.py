"""BUILD THE OCCUPY VOCABULARY BY MEASURING IT, one candidate pattern at a time.

⚠ WHY NOT JUST WRITE THE PATTERNS. Because that is how the debt vocabulary got to
16% on MTGE and stayed there: the words I expect a mortgage to use and the words
mortgages actually use are different sets, and nothing tells you which you wrote
until you count. Every candidate below is scored SEPARATELY, on the lease family
and on four types that must NOT be leases, before any of it enters lexicon.py.

⚠ TWO NUMBERS PER PATTERN, NEVER ONE.
    recall     — of the lease family, how many does it find
    leak       — of DEED/MTGE/EASE/DEVR, how many does it wrongly claim
A pattern with 90% recall and 60% leak is worse than useless: it would relabel a
third of ACRIS as leases and every check downstream would still pass.

⚠ LEAK IS NOT AUTOMATICALLY AN ERROR. A mortgage really does assign leases and
rents; a deed really is taken subject to existing tenancies. Those are HIDDEN
FUNCTIONS, which is the thing this project exists to catch. So leak is reported
per type and read, not thresholded blindly — a pattern that leaks into MTGE and
nowhere else is telling us something true.
"""
from __future__ import annotations

import json, glob, os, re, sys, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

LEASE = {"LEAS", "MLEA", "ASSTO", "TERL", "SUBL"}
CONTROL = {"DEED", "MTGE", "EASE", "DEVR"}

# ── candidates ───────────────────────────────────────────────────────────
# Grouped by what they claim to be evidence OF, because a lease that is being
# TERMINATED still fires "demised premises" — the function is OCCUPY either way
# and the direction is a separate reading.
CAND = [
 ("demise",        r"\bdemise[ds]?\b|\bdemised\s*premises\b"),
 ("lessor_lessee", r"\blessor\b|\blessee\b"),
 ("landlord_tenant", r"\blandlord\b|\btenant\b"),
 ("hereby_lease",  r"hereby\s*(?:demise[sd]?\s*(?:and\s*)?)?leases?\s*(?:and\s*demise[sd]?\s*)?(?:unto|to)\b"),
 ("leasehold",     r"\bleasehold\b"),
 ("quiet_enjoy",   r"quiet\s*enjoyment"),
 ("term_years",    r"term\s*of\s*(?:\w+\s*){0,3}years?\b|for\s*a\s*term\s*commencing"),
 ("commence_expire", r"commencement\s*date|expiration\s*date|lease\s*year"),
 ("rent",          r"\bbase\s*rent\b|\bfixed\s*rent\b|\bannual\s*rent\b|\bminimum\s*rent\b"),
 ("renewal",       r"option\s*to\s*(?:renew|extend)|renewal\s*(?:term|option)"),
 ("premises",      r"\bthe\s*premises\b"),
 ("ground_lease",  r"\bground\s*lease\b|\bnet\s*lease\b"),
 ("sublet",        r"\bsublease\b|\bsublet\b|\bsubtenant\b"),
 ("surrender",     r"\bsurrender\b|\bvacate\b|\bpossession\s*of\s*the\s*premises\b"),
 ("memo_lease",    r"memorandum\s*of\s*lease"),
 ("assign_lease",  r"assign\w*\s*of\s*(?:the\s*)?lease|assigns?\s*(?:the\s*)?lease"),
 ("terminate",     r"terminat\w+\s*of\s*(?:the\s*)?lease|lease\s*is\s*(?:hereby\s*)?terminated"),
 ("subordinate",   r"subordinat\w+\s*(?:of|to)\s*(?:the\s*)?(?:lease|mortgage)"),
]
CC = [(n, re.compile(p, re.I)) for n, p in CAND]


def corpus():
    """doc_id -> (doc_type, head text). Empty reads dropped, never scored."""
    ty = json.load(open(os.path.join(HERE, "_doctype_of.json"), encoding="utf-8"))
    out, blank, untyped = {}, 0, 0
    for f in glob.glob(os.path.join(HERE, "census_head", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        doc = str(d["doc_id"])
        t = " ".join((p.get("accepted_text") or "") for p in d.get("pages") or [])
        if len(t.strip()) < 200:
            blank += 1
            continue
        if doc not in ty:
            untyped += 1
            continue
        out[doc] = (ty[doc], t)
    return out, blank, untyped


def main():
    c, blank, untyped = corpus()
    n = collections.Counter(t for t, _ in c.values())
    lease_n = sum(n[t] for t in LEASE)
    ctrl_n = sum(n[t] for t in CONTROL)
    print(f"corpus {len(c)} scored · {blank} failed reads dropped · {untyped} untyped")
    print(f"  lease family : {lease_n:>4}  " +
          " ".join(f"{t}={n[t]}" for t in sorted(LEASE) if n[t]))
    print(f"  control      : {ctrl_n:>4}  " +
          " ".join(f"{t}={n[t]}" for t in sorted(CONTROL) if n[t]))
    if not lease_n:
        print("\n  ⚠ NO LEASE DOCUMENTS HELD — nothing can be measured. Stop.")
        return 1
    print()

    hdr = (f"  {'pattern':<16}{'recall':>8}{'leak':>7}   " +
           "".join(f"{t:>7}" for t in sorted(LEASE) if n[t]) + "  | " +
           "".join(f"{t:>7}" for t in sorted(CONTROL) if n[t]))
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    rows = []
    for name, rx in CC:
        hit = collections.Counter()
        for t, txt in c.values():
            if rx.search(txt):
                hit[t] += 1
        lh = sum(hit[t] for t in LEASE)
        ch = sum(hit[t] for t in CONTROL)
        rec = lh / lease_n
        leak = ch / ctrl_n if ctrl_n else 0.0
        rows.append((rec, leak, name, hit))
        line = f"  {name:<16}{rec*100:>7.0f}%{leak*100:>6.0f}%   "
        line += "".join(f"{(100*hit[t]//n[t] if n[t] else 0):>6}%"
                        for t in sorted(LEASE) if n[t])
        line += "  | " + "".join(f"{(100*hit[t]//n[t] if n[t] else 0):>6}%"
                                 for t in sorted(CONTROL) if n[t])
        print(line)

    print()
    # ⚠ A GLOBAL RECALL THRESHOLD SELECTS AGAINST TYPE-SPECIFIC VOCABULARY, which
    # is the one thing census.py's own docstring says a function's vocabulary IS.
    # First pass kept 3 patterns and threw away `terminate` (22% overall, 100% of
    # TERL, 0% leak) and `assign_lease` (23% overall, 100% of ASSTO, 2% leak).
    # Both are PERFECT readers of one sub-type, discarded for being bad readers of
    # the other four. Keep on EITHER global reach or per-type mastery.
    print("  KEEP = leak <= 15% AND (recall >= 25% overall OR >= 50% of any one type)")
    def mastery(hit):
        return max((hit[t] / n[t] for t in LEASE if n[t]), default=0)
    keep = [r for r in rows if r[1] <= .15 and (r[0] >= .25 or mastery(r[3]) >= .50)]
    keep.sort(reverse=True)
    print("  " + (", ".join(r[2] for r in keep) if keep else "nothing qualifies"))

    # union coverage of the kept set — the only number that matters for the detector
    if keep:
        ks = [dict(CAND)[r[2]] for r in keep]
        rx = re.compile("|".join(f"(?:{p})" for p in ks), re.I)
        lh = sum(1 for t, txt in c.values() if t in LEASE and rx.search(txt))
        ch = sum(1 for t, txt in c.values() if t in CONTROL and rx.search(txt))
        print(f"\n  UNION  recall {lh}/{lease_n} = {100*lh/lease_n:.0f}%"
              f"   ·  leak {ch}/{ctrl_n} = {100*ch/ctrl_n:.0f}%")
        miss = [(d, t) for d, (t, txt) in c.items() if t in LEASE and not rx.search(txt)]
        if miss:
            mc = collections.Counter(t for _, t in miss)
            print(f"  MISSED {len(miss)}: " + " ".join(f"{k}={v}" for k, v in mc.most_common()))
            print("    " + " ".join(d for d, _ in miss[:8]))
        json.dump({"keep": [r[2] for r in keep],
                   "recall": lh / lease_n, "leak": ch / ctrl_n if ctrl_n else None,
                   "measured_against": {"lease": dict(n), "n": len(c)}},
                  open(os.path.join(HERE, "_occupy_vocab.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
