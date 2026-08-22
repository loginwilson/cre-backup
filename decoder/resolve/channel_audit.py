"""WHICH CHANNEL ACTUALLY READS WHICH ARTIFACT — the cross-tab that was never run.

    python channel_audit.py                  # CRITICAL tier, every engine on disk
    python channel_audit.py --tier ALL

⚠ WHY THIS BEFORE ANY MORE RESOLVER WORK. Every number in _score_upright.json and
_score_rotated.json is a MARGINAL rate: "Qwen got 98%", "Paddle got 47%". A pair of
marginals cannot tell you whether the two channels fail on the SAME artifacts or on
DIFFERENT ones, and that difference is the whole design. If they fail together the
second channel is not paying for itself; if they fail apart, every miss is
recoverable and the resolver — not the engines — is what is losing it.

⚠ THE SCORES ARE ANTI-CORRELATED BY ORIENTATION AND THAT IS THE SUSPECT. Upright:
VLM .980 / OCR .475. Rotated: VLM .549 / OCR .945. Each channel has one good
orientation and one crippled one, so every fusion so far has paired a strong reader
with a blind one and called the result a dispute.

⚠ ARTIFACT LEVEL, NOT TOKEN LEVEL. A token-level cross-orientation fuse was already
tried and LOST (18.1% agreement vs 49.6% same-orientation) because the two reading
orders do not align. Artifacts are what the data tables consume, and an artifact
does not care what order it was read in — only whether it is present. That is the
level this file measures.

⚠ AND COVERAGE IS NOT RECALL. Engines have different pages on disk. Every rate here
carries its denominator, and the pairwise section scores only pages BOTH channels
actually have, or the union is measuring absence as failure.
"""
from __future__ import annotations

import argparse, collections, itertools, json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
BAKE = HERE.parent / "bakeoff"
DEC = HERE.parent
sys.path.insert(0, str(BAKE))

import score as S

KEYS = [("FT_1680008647768", "answer_key_testdoc.json", "film", 0.255),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book", 0.040),
        ("2015022400608001", "answer_key_moderndoc.json", "digital", 0.705)]

# engines with too few pages cannot be compared and are reported, not scored
MIN_PAGES = 5


def channels():
    """⚠ AN ANGLE IS ITS OWN CHANNEL, NOT A VARIANT OF ONE. q35-rot carries
    p001.a0 / p001.a90 / p002.a270 alongside a bare p001 — pooling them would
    let a page read at 90° cover for the same page failing at 0°, which is
    exactly the blindness this audit exists to find. Each (engine, angle) is
    scored separately, and the bare file is angle ''."""
    out = collections.defaultdict(set)      # (engine, angle) -> nothing yet
    for ed in sorted((BAKE / "out").iterdir()):
        if not ed.is_dir():
            continue
        for f in ed.rglob("*.txt"):
            stem = f.name[:-4]
            if stem.endswith(".png"):
                stem = stem[:-4]
            parts = stem.split(".")
            ang = parts[1] if len(parts) > 1 and parts[1].startswith("a") else ""
            out[(ed.name, ang)].add(True)
    return sorted(out)


def engine_text(engine, angle, doc, stem):
    """⚠ NAMING VARIES BY RUN: p001.txt, p001.png.txt, p001.a90.txt. A missing
    file is ABSENT COVERAGE and returns None — never an empty string, which
    would score as a read page that found nothing."""
    base = f"{stem}.{angle}" if angle else stem
    for name in (f"{base}.txt", f"{base}.png.txt"):
        f = BAKE / "out" / engine / doc / name
        if f.exists() and f.stat().st_size > 0:
            return f.read_text(encoding="utf-8", errors="replace")
    return None


def arts_for(key, stem, tier):
    blk = key.get(stem + ".png") or key.get(stem) or {}
    if not isinstance(blk, dict):
        return []
    out = []
    for a in blk.get("artifacts") or []:
        if tier and a.get("tier") != tier:
            continue
        if a.get("ambiguous") or a.get("tier") == "AMBIGUOUS":
            continue
        out.append(a)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="CRITICAL")
    a = ap.parse_args()
    tier = None if a.tier.upper() == "ALL" else a.tier.upper()

    engines = [(e, a) for e, a in channels()]
    name_of = {(e, a): (f"{e}@{a}" if a else e) for e, a in engines}

    # ── the matrix: (doc, stem, i) -> {channel: hit} ──────────────────────
    hits = collections.defaultdict(dict)
    have = collections.defaultdict(set)          # channel -> {(doc, stem)}
    art_of = {}
    for doc, keyfile, cls, share in KEYS:
        kf = DEC / keyfile
        if not kf.exists():
            continue
        key = json.loads(kf.read_text(encoding="utf-8"))
        # ⚠ THE KEY CARRIES METADATA KEYS TOO (_doc, _note, _match_checks).
        # Reading those as pages threw; skipping them silently would be worse,
        # so pages are matched positively rather than by exclusion.
        stems = sorted({k[:-4] for k in key if k.endswith(".png")})
        for stem in stems:
            arts = arts_for(key, stem, tier)
            if not arts:
                continue
            for i, art in enumerate(arts):
                art_of[(doc, stem, i)] = (art, cls, share)
            for ea in engines:
                t = engine_text(ea[0], ea[1], doc, stem)
                if t is None:
                    continue
                e = name_of[ea]
                have[e].add((doc, stem))
                n = S.norm(t)
                for i, art in enumerate(arts):
                    hits[(doc, stem, i)][e] = (S.found(n, art) or S.pointed(n, art))
    engines = [name_of[ea] for ea in engines]

    if not art_of:
        print("  no keyed artifacts found")
        return 1

    live = [e for e in engines if len(have[e]) >= MIN_PAGES]
    skipped = [(e, len(have[e])) for e in engines if e not in live and have[e]]
    print(f"ARTIFACT CROSS-TAB — tier={a.tier} · {len(art_of)} keyed artifacts "
          f"across {len({(d,s) for d,s,_ in art_of})} pages\n")

    # ── marginals, each on ITS OWN coverage, denominator attached ─────────
    print(f"  {'engine':<20}{'pages':>6}{'hit':>6}{'of':>6}{'recall':>8}")
    print("  " + "-" * 46)
    rank = []
    for e in live:
        ids = [k for k in art_of if (k[0], k[1]) in have[e]]
        h = sum(1 for k in ids if hits[k].get(e))
        if not ids:
            continue
        rank.append((h / len(ids), e, h, len(ids), len(have[e])))
    for r, e, h, n, pg in sorted(rank, reverse=True):
        print(f"  {e:<20}{pg:>6}{h:>6}{n:>6}{r:>8.1%}")
    if skipped:
        print(f"\n  ⚠ too few pages to compare (reported, not scored): "
              + " ".join(f"{e}({n}pg)" for e, n in skipped))

    # ── the floor: what NO engine on disk reads ──────────────────────────
    nobody = [k for k in art_of if not any(hits[k].get(e) for e in live)]
    print(f"\nFLOOR — artifacts no engine on disk reads: {len(nobody)}/{len(art_of)} "
          f"({100*len(nobody)/len(art_of):.1f}%)")
    for k in nobody[:8]:
        art, cls, _ = art_of[k]
        v = str(art.get("value") or art.get("text") or art)[:58]
        print(f"    {k[0][:18]:<19}{k[1]:<6}{cls:<9}{v}")
    if len(nobody) > 8:
        print(f"    … and {len(nobody)-8} more")

    # ── PAIRS: does a second channel pay for itself? ──────────────────────
    # ⚠ SCORED ONLY WHERE BOTH HAVE THE PAGE. Otherwise the union is measuring
    # one engine's missing files as the other's contribution.
    print(f"\nPAIRS — union recall on pages BOTH have "
          f"(does the 2nd channel pay for itself?)")
    print(f"  {'pair':<38}{'pages':>6}{'A':>7}{'B':>7}{'union':>7}{'lift':>7}")
    print("  " + "-" * 72)
    rows = []
    for x, y in itertools.combinations([e for _, e, *_ in sorted(rank, reverse=True)], 2):
        both = have[x] & have[y]
        ids = [k for k in art_of if (k[0], k[1]) in both]
        if len(ids) < 10:
            continue
        hx = sum(1 for k in ids if hits[k].get(x))
        hy = sum(1 for k in ids if hits[k].get(y))
        hu = sum(1 for k in ids if hits[k].get(x) or hits[k].get(y))
        best = max(hx, hy)
        rows.append((hu / len(ids), (hu - best) / len(ids), x, y,
                     len(both), hx / len(ids), hy / len(ids), len(ids)))
    for u, lift, x, y, pg, rx, ry, n in sorted(rows, reverse=True)[:14]:
        print(f"  {x+' × '+y:<38}{pg:>6}{rx:>7.1%}{ry:>7.1%}{u:>7.1%}{lift:>+7.1%}")

    json.dump({"tier": a.tier, "artifacts": len(art_of),
               "engines": {e: {"pages": len(have[e]),
                               "hit": h, "of": n, "recall": r}
                           for r, e, h, n, _pg in rank},
               "floor": len(nobody),
               "pairs": [{"a": x, "b": y, "pages": pg, "n": n,
                          "a_recall": rx, "b_recall": ry,
                          "union": u, "lift_over_best": lift}
                         for u, lift, x, y, pg, rx, ry, n in sorted(rows, reverse=True)]},
              open(HERE / "_channel_audit.json", "w"), indent=1)
    print(f"\nwrote _channel_audit.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
