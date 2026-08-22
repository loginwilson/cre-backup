"""COVER-PAGE FIELDS BECOME CLAIMS — the wiring that lets them become events.

    python cover_claims.py               # emit + verify, all DEVR
    python cover_claims.py --show
    from cover_claims import claims_for_doc

⚠ READING A FIELD IS NOT KNOWING IT. cover_read.py bound both BBLs, both
parties, the dates and the stamp on 25 of 25 covers — and the completeness pass
still scored the page 83% unclaimed, correctly, because none of it had entered
the claim layer. A field sitting in a JSON file is not evidence; it becomes
evidence when it carries provenance a machine can re-check and a resolver can
refuse.

⚠ TWO PROVENANCE FORMS, AND BOTH ARE MECHANICAL. claim_read.py's rule —
"the text at those offsets is re-read and compared byte-for-byte" — cannot be
weakened for spatially-bound values just because they are inconvenient:

    span   [start, end] into p001 accepted_text.   Verify: text[s:e] == quote
    box    [x, y, w, h] in p001 word boxes.        Verify: a word with that
                                                   token is still at that box

The box exists because the RETT figure was chosen by POSITION, not by matching
characters — there is no offset to quote. Re-running the boxes and asking
whether the token is still there is the same guarantee by different arithmetic.
A fabricated cover claim fails on both paths, on arithmetic, not on judgement.

⚠ AND THE PRICE IS `derived`, NEVER `read`. $1,565,500 is not printed anywhere
on the document — it is RETT / 0.004. facts.py's rule applies: a derived value
that does not record its derivation is indistinguishable from one read off the
page, and this one is worse than most, because RETT rounds consideration UP to
the next $500. It is a BOUND. Calling it a price hides that.

⚠ AND `absent_by_nature` IS A CLAIM, NOT A MISSING ROW. 16 of 25 covers print
the stamp as 0.00 — the document genuinely moved no money. That is a fact the
resolver needs; emitting nothing would make it identical to a page nobody read,
and every sum built on the difference would be wrong.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
OUT = HERE / "resolve" / "_claims"

from cover_fields import words, RETT_RATE, RPTT_RATE
from cover_read import read_cover

# Which cover field establishes which part of an event. The right-hand value is
# the `field` written to resolution.event_claim.
FIELD_OF = {
    "doc_type": "action",
    "document_date": "executed_date",
    "recorded_date": "recorded_date",
    "crfn": "source_ref",
    "parcel": "participant",
    "consideration": "quantity",
    "party_one": "participant",
    "party_two": "participant",
}


def claims_for_doc(doc_dir, flat_text):
    """Every claim this cover page supports. Never invents; may return few."""
    r = read_cover(doc_dir, flat_text)
    doc = r["doc"]
    out = []

    def add(kind, value, **kw):
        out.append({"doc_id": doc, "page": "p001", "kind": kind,
                    "value": value, "field": FIELD_OF.get(kind),
                    "confidence": "read", "status": "resolved",
                    "source": "acris", **kw})

    # ── flat fields: span provenance ────────────────────────────────────────
    t = flat_text or ""
    for k in ("doc_type", "document_date", "recorded_date", "crfn"):
        sp = r["_span"].get(k)
        if r.get(k) and sp:
            add(k, r[k], span=sp, quote=t[sp[0]:sp[1]],
                established_by="cover_flat")
    # ⚠ CRFN IS SPATIAL, NOT FLAT. Its label and its number sit in the right
    # column with the left column's "TOTAL: $0.00" landing between them, so the
    # flat regex finds it on 0 of 25 while the word boxes find it on 19.
    if r.get("crfn") and r.get("crfn_box") and "crfn" not in r["_span"]:
        add("crfn", r["crfn"], box=r["crfn_box"], quote=r["crfn"],
            established_by="cover_spatial")
    for lot in r["lots"]:
        add("parcel", f"{lot['borough']} block {lot['block']} lot {lot['lot']}",
            span=lot["span"], quote=lot["quote"],
            established_by="cover_flat",
            # ⚠ THE LOT IS KNOWN AND ITS SIDE IS NOT. The cover lists both
            # parcels and never says which sends and which receives. Recording a
            # guess here would put a direction into the lineage that no document
            # supports — and direction is the one field transcription scoring
            # cannot catch. Null role, and the event refuses on it.
            role=None, sign=0,
            incomplete=bool(lot["lot_missing"]))

    # ── spatial fields: box provenance ──────────────────────────────────────
    for k, box_k, q_k in (("rptt", "rptt_box", "rptt_quote"),
                          ("rett", "rett_box", "rett_quote")):
        if r.get(k) is not None and r.get(box_k):
            add(f"stamp_{k}", r[k], box=r[box_k], quote=r[q_k],
                established_by="cover_spatial",
                repaired=bool(r.get("money_repaired")))

    # ── the derived price ───────────────────────────────────────────────────
    if r.get("consideration"):
        src = r["consideration_from"]
        rate = RETT_RATE if src == "rett" else RPTT_RATE
        out.append({
            "doc_id": doc, "page": "p001", "kind": "consideration",
            "field": "quantity", "value": r["consideration"], "unit": "USD",
            "presence": "present", "confidence": "derived",
            "derivation": f"{src.upper()} {r[src]} / {rate}",
            # ⚠ A BOUND, NOT A PRICE. RETT rounds UP to the next $500, so the
            # true consideration lies in (value - 500, value].
            "bound": "upper", "established_by": f"derived_from_{src}",
            "source": "acris", "status": "resolved",
        })
    elif r.get("presence") == "absent_by_nature":
        out.append({
            "doc_id": doc, "page": "p001", "kind": "consideration",
            "field": "quantity", "value": None, "unit": "USD",
            "presence": "absent_by_nature", "confidence": "read",
            "derivation": "transfer-tax stamp printed 0.00",
            "established_by": "cover_spatial", "source": "acris",
            "status": "resolved",
        })
    return r, out


def verify(doc_dir, flat_text, claims):
    """Re-read every claim from its own evidence. Arithmetic, not judgement."""
    ok = bad = 0
    ws = None
    for c in claims:
        if "span" in c:
            s, e = c["span"]
            good = 0 <= s < e <= len(flat_text) and flat_text[s:e] == c["quote"]
        elif "box" in c:
            if ws is None:
                ws = words(pathlib.Path(doc_dir) / "p001.tif")
            x, y, w, h = c["box"]
            good = any(v["t"] == c["quote"] and v["x"] == x and v["y"] == y
                       for v in ws)
        else:
            # derived and absent_by_nature values quote nothing — they are
            # verified by their derivation existing, which is checked below.
            good = bool(c.get("derivation"))
        if good:
            ok += 1
        else:
            bad += 1
            c["status"] = "verification_failed"
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="devr_pages")
    ap.add_argument("--text", default="devr_text")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    flat = {}
    for f in (HERE / a.text).glob("*.json"):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for pg in rec.get("pages") or []:
            if str(pg.get("page")).lstrip("p0") == "1":
                flat[rec.get("doc_id", f.stem)] = pg.get("accepted_text") or ""

    docs = sorted(d for d in (HERE / a.dir).iterdir()
                  if d.is_dir() and (d / "p001.tif").exists() and d.name in flat)
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"COVER CLAIMS — {len(docs)} documents\n")
    kinds = collections.Counter()
    tot = tok = tobad = 0
    for d in docs:
        t = flat[d.name]
        _r, cl = claims_for_doc(d, t)
        ok, bad = verify(d, t, cl)
        (OUT / f"{d.name}.cover.jsonl").write_text(
            "".join(json.dumps(c) + "\n" for c in cl), encoding="utf-8")
        for c in cl:
            kinds[c["kind"]] += 1
        tot += len(cl); tok += ok; tobad += bad
        if a.show:
            print(f"  {d.name}  {len(cl):>2} claims  ok {ok:>2} bad {bad}")

    print("  CLAIMS BY KIND")
    for k, v in kinds.most_common():
        print(f"    {k:<20} {v:>4}")

    rate = 100 * tok / max(tot, 1)
    print(f"\n  VERIFICATION   {tok:,}/{tot:,}  {rate:.1f}%"
          f"{'   OK' if tobad == 0 else '   ⚠ FAILURES — EMITTER BUG'}")
    print("    span claims re-read byte-for-byte from p001 accepted_text;")
    print("    box claims re-read from freshly-recomputed word boxes.")
    print(f"\n  -> resolve/_claims/<doc>.cover.jsonl")
    return 0 if tobad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
