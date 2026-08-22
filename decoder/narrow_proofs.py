"""Narrow PAGE proofs — mechanically by ink, semantically by reading.

⚠ TWO OPERATIONS, AND THEY ARE NOT THE SAME THING

    TRIM    crop to the INK BOUNDING BOX. Mechanical, semantic-free, safe: it
            removes only pixels that are blank. Saves bytes. Does NOT focus the
            reader on the claim — a trimmed page is still a whole page.

    REGION  a box around the specific table or clause the claim was read from.
            Requires having READ the page. Focuses the reader. This is what a
            proof is actually for.

    Reporting a TRIM as a REGION would be the same class of error as reporting
    a fetch as a read. `precision` records which one happened.

⚠ THE TRIM MUST NOT EAT THE MARGINS

    The 1998 mortgage's entire value is a HANDWRITTEN MARGIN NOTE — "MT
    $4527.56" — which is exactly 2.0000% of principal and the only proof of the
    era's tax rate. A trim that assumed "content lives in the text block" would
    delete the evidence. So the bounding box is computed over ALL ink, margins
    included, then padded outward.
"""
import csv, hashlib, io, pathlib, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
PAGES = HERE / "pages_out"
OUT = HERE / "proofs"
L49 = "1008000049"

# Regions I can set because I have READ the page and know where the claim sits.
# doc/page -> (box, caption)
SEMANTIC = {
 ("2023110100486009", "p005"): ((0.06, 0.16, 0.97, 0.62),
   "sections 10-13 — foreclosure in one parcel, the lender's cost lien, the "
   "rents assignment and the five acceleration triggers"),
 ("2023110100486009", "p006"): ((0.06, 0.10, 0.97, 0.60),
   "sections 14-19 — Lien Law trust fund, LIMITED RECOURSE, the $25,490,000 "
   "maximum secured, and the clause making the unrecorded Loan Agreement "
   "control"),
 ("2013081200922003", "p005"): ((0.06, 0.10, 0.97, 0.70),
   "sections 1(b)-5 — no-default representation, the $40,500,000 "
   "consolidation, the LIEN SPREADER and Schedule C superseding all prior "
   "terms"),
 ("2013081200922003", "p021"): ((0.06, 0.06, 0.97, 0.42),
   "Schedule C granting clause (b)-(d) — AFTER-ACQUIRED development rights, "
   "and air rights named as collateral"),
 ("2019071700601003", "p006"): ((0.06, 0.60, 0.97, 0.97),
   "WHEREAS clauses — both lots DEMOLISHED and awaiting construction, and DOB "
   "Permit Application No. 121187214"),
 ("2019071700601003", "p008"): ((0.06, 0.28, 0.97, 0.72),
   "definitions G-N — Development Rights, the Construction Easement, the "
   "four-limb Emergency Situation, and the 54.52% bonus split"),
 ("2010102601040006", "p008"): ((0.06, 0.10, 0.97, 0.72),
   "section II.A.1-3 — the rights conveyance, the light/air/VIEW easement "
   "granted by the 120 Owner alone, and the alteration restriction"),
 ("2010102601040006", "p009"): ((0.06, 0.08, 0.97, 0.62),
   "section II.A.3-4 — 10-business-day plan review, the violation covenant, "
   "the 30-day cure period and the entry licence"),
 ("2003110900238001", "p001"): ((0.04, 0.20, 0.98, 0.95),
   "cover page — $969,656.99 consolidated, taxable $0 under exemption 255, "
   "cross-referencing 1990 Reel 1707 Page 1285, property type APARTMENT "
   "BUILDING"),
 ("FT_1570006671557", "p002"): ((0.04, 0.20, 0.98, 0.80),
   "the 1998 conveyance — 112 West 25 Company to Edelman Family LP, signed by "
   "Norman and Rita Edelman as co-partners"),
 ("2013080901116002", "p040"): ((0.02, 0.10, 1.00, 0.62),
   "Exhibit D — the lot 20 airspace transfer, envelope 254,261 -> 268,964"),
 ("2013052101674008", "p041"): ((0.02, 0.10, 1.00, 0.62),
   "Exhibit D — lot 21 transfers 10,722 sf; developer after transfer 254,261"),
}

PAD = 0.012          # fraction of page padded back after the ink bbox

# ---------------------------------------------------------------------------
# ⚠ THE COVER PAGE IS A FORM, SO ITS REGIONS ARE A TEMPLATE.
#
# Trimming to ink removed only ~11% from cover pages, because a cover page is
# ink edge to edge. But every ACRIS RECORDING AND ENDORSEMENT COVER PAGE has
# the same blocks in the same places — so the region does not need reading, it
# needs KNOWING THE FORM. Which block to crop depends on what the claim says:
# a consideration claim wants FEES AND TAXES; a party claim wants PARTIES.
#
# This is the same move as the doc-type term menu, applied to geometry:
# codify the TYPE once, then every instance is a lookup.
# ---------------------------------------------------------------------------
COVER_BLOCKS = {
 "fees":     ((0.03, 0.60, 0.99, 0.97), "FEES AND TAXES block"),
 "parties":  ((0.03, 0.47, 0.99, 0.68), "PARTIES block"),
 "property": ((0.03, 0.28, 0.99, 0.50), "PROPERTY DATA block"),
 "header":   ((0.03, 0.05, 0.99, 0.30), "document id, type, date and presenter"),
}
# claim predicate -> which block proves it
PREDICATE_BLOCK = {
 "consideration": "fees", "consideration_recited": "fees",
 "mortgage": "fees", "consolidation": "fees", "tax_paid": "fees",
 "tax_rate": "fees",
 "conveyance": "parties", "party_role": "parties", "person": "parties",
 "property_type": "property", "lot_area": "property",
 "reel_page": "header", "cross_reference": "header", "defect": "header",
}


def ink_box(im):
    """Bounding box of ALL non-white pixels, margins included."""
    g = im.convert("L")
    # anything not near-white is ink; scanner noise is handled by the pad
    bw = g.point(lambda v: 0 if v > 232 else 255, "1")
    bb = bw.getbbox()
    if not bb:
        return (0.0, 0.0, 1.0, 1.0)
    w, h = im.size
    x0, y0, x1, y1 = bb
    return (max(0.0, x0 / w - PAD), max(0.0, y0 / h - PAD),
            min(1.0, x1 / w + PAD), min(1.0, y1 / h + PAD))


def render(doc, page, box, scale=0.667):
    from PIL import Image
    src = PAGES / doc / f"{page}.png"
    if not src.exists():
        return None, None, None
    im = Image.open(src)
    w, h = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    c = c.resize((max(1, int(c.width * scale)), max(1, int(c.height * scale))),
                 Image.LANCZOS).convert("1")
    b = io.BytesIO()
    c.save(b, "PNG", optimize=True)
    return b.getvalue(), c.size, im


def _cover_block(doc):
    """Which cover-page block proves this document's claims?

    Chosen from the claims that actually cite p001 of this document. Where the
    claims want different blocks, the widest wins — a proof that shows too much
    is honest; one that shows the wrong block is not.
    """
    import claims as K
    want = set()
    for c in K.rows():
        if c["document_id"] == doc and c["page"] == "p001":
            b = PREDICATE_BLOCK.get(c["predicate"])
            if b:
                want.add(b)
    if not want:
        return None
    order = ["fees", "parties", "property", "header"]
    return sorted(want, key=lambda b: order.index(b))[0]


def main():
    from PIL import Image
    pp = HERE / f"acris_proof_{L49}.csv"
    rows = list(csv.DictReader(open(pp, encoding="utf-8")))
    before = sum(int(r["bytes"]) for r in rows)
    sem = trim = kept = 0

    for r in rows:
        full = (float(r["x1"]) - float(r["x0"])) > 0.999
        if not full:
            kept += 1
            continue
        key = (r["document_id"], r["page"])
        if key in SEMANTIC:
            box, cap = SEMANTIC[key]
            prec = "REGION"
            sem += 1
        elif r["page"] == "p001" and _cover_block(r["document_id"]):
            blk = _cover_block(r["document_id"])
            box, what = COVER_BLOCKS[blk]
            cap = f"cover page — {what}"
            prec = "REGION"
            sem += 1
        else:
            src = PAGES / r["document_id"] / f"{r['page']}.png"
            if not src.exists():
                continue
            box = ink_box(Image.open(src))
            cap = "whole page, trimmed to its ink — region not yet narrowed"
            prec = "TRIMMED"
            trim += 1
        data, dims, _ = render(r["document_id"], r["page"], box)
        if data is None:
            continue
        old = pathlib.Path(HERE / r["storage_path"])
        dg = hashlib.sha256(data).hexdigest()
        new = OUT / f"{dg[:16]}.png"
        new.write_bytes(data)
        if old.exists() and old != new:
            old.unlink()
        r.update(proof_id=dg, x0=box[0], y0=box[1], x1=box[2], y1=box[3],
                 caption=cap, bytes=len(data),
                 storage_path=str(new.relative_to(HERE)))
        r["precision"] = prec

    for r in rows:
        r.setdefault("precision",
                     "REGION" if (float(r["x1"]) - float(r["x0"])) < 0.999
                     else "PAGE")

    after = sum(int(r["bytes"]) for r in rows)
    fn = list(rows[0].keys())
    with open(pp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn, restval="")
        w.writeheader(); w.writerows(rows)

    by = {}
    for r in rows:
        by.setdefault(r["precision"], []).append(int(r["bytes"]))
    print(f"NARROWING {len(rows)} proofs\n")
    print(f"  {sem} narrowed to a SEMANTIC REGION (pages I have read)")
    print(f"  {trim} TRIMMED to their ink bounding box (mechanical)")
    print(f"  {kept} already regions\n")
    for k in sorted(by):
        v = by[k]
        print(f"  {k:<9} {len(v):>3} proofs · avg {sum(v)/len(v)/1024:>5.0f} KB "
              f"· {sum(v)/1024:>6.0f} KB total")
    print(f"\n  {before/1024:,.0f} KB -> {after/1024:,.0f} KB  "
          f"({100*(before-after)/before:.0f}% smaller)")
    print(f"  average proof now {after/len(rows)/1024:.0f} KB")
    print(f"\n  ⚠ TRIMMED IS NOT NARROWED. A trimmed page has had blank pixels")
    print("    removed; it still shows the whole page. Only REGION focuses the")
    print("    reader on the clause the claim came from, and only reading the")
    print("    page can produce one.")
    terr = 84_000 * (len(rows) / 35) * (after / len(rows)) / 1024 ** 3
    print(f"\n  territory projection (7,030 lots, ~84k docs): {terr:,.1f} GB")


if __name__ == "__main__":
    main()
