"""PROOF CROPS — the pixels a claim was read from, attached to the claim.

LOGIN, 2026-08-06:

    "A claim of receiving blank sf from lot blank with an attached photo of the
     table from the ZLDA. I think that's a cool way to source — linking the
     cropped proof to the terms/value claim."

    The card stops asking to be trusted. Beside "+53,578 sf from lots 53/55/56"
    sits the actual Exhibit D chart, in the original type. A broker reads the
    decode and the source in one glance, and can see for themselves that the
    excess column really does total 53,578.

MEASURED, not estimated (this parcel, 2026-08-06):
    full page, 300 dpi PNG          130 KB   (the average across 1,659 pages)
    full page, 1-bit 200 dpi         87 KB
    CLAIM CROP, 1-bit 200 dpi        18 KB   ← legible, verified by eye

    At ~3 proofs per document that is ~54 KB of proof per document against
    1.4 MB of full imagery — a 26x reduction, and the proof is the part a user
    actually looks at.

⚠ WHAT A CROP IS NOT

    A crop proves the CLAIM. It does not prove the CONTEXT, and today produced
    two failures that no crop could have caught:

      1. The 2010 easement was decoded from the chart at p038. The corrections
         — light/air/VIEW, measured from the REAR LOT LINE, granted by LOT 53
         ALONE — came from p008, a page nobody had cropped because nobody knew
         anything was there.

      2. Five lot-22 terms were taken from EXHIBIT G — an UNEXECUTED BLANK FORM
         ("made this ___ day of ___, 201_"). ⚠ A CROP OF A CLAUSE IN A BLANK
         FORM IS VISUALLY IDENTICAL TO A CROP OF AN EXECUTED ONE. The thing that
         makes it contingent is elsewhere in the instrument.

    So every proof crop carries `instrument_status` alongside it, and the crop
    is stored WITH a page-level context flag rather than as a free-floating
    picture. The crop is evidence for the reader; it is not a substitute for the
    page when a trap is found.
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

DDL = """
create table if not exists acris_proof (
  proof_id     text primary key,        -- sha256 of the cropped bytes
  claim_id     text,                    -- the claim this proves
  term_key     text,                    -- or the term (burdened_bbl:seq)
  document_id  text not null,
  page         text not null,
  -- the crop box as FRACTIONS of the page, so it survives any re-render at a
  -- different resolution. Absolute pixels would break the moment the archival
  -- copy is re-encoded.
  x0 real not null, y0 real not null, x1 real not null, y1 real not null,
  caption      text not null,           -- what the reader is looking at
  bytes        int not null,
  dpi          int not null default 200,
  bit_depth    int not null default 1,
  -- ⚠ a crop cannot show whether the instrument was signed. Carried here so a
  -- proof can never be shown without its execution status.
  instrument_status text not null default 'EXECUTED',  -- EXECUTED | FORM | UNKNOWN
  storage_path text not null
);
create index if not exists acris_proof_claim on acris_proof(claim_id);
create index if not exists acris_proof_doc on acris_proof(document_id, page);
"""

# (claim_id, doc, page, box as page fractions, caption, instrument status)
PROOFS = [
 ("c2010-rights", "2010102601040006", "p038", (0.02, 0.13, 1.00, 0.60),
  "Exhibit D — ALLOCATION OF DEVELOPMENT RIGHTS. The 'excess' row totals "
  "53,578 sf across lots 53, 55 and 56.", "EXECUTED"),
 ("c2012-rights", "2012122701550003", "p043", (0.02, 0.13, 1.00, 0.62),
  "Exhibit D — the developer's after-transfer allocation of 232,813 sf. The "
  "22,845 sf purchase is the difference from the 2010 chart's 209,968.",
  "EXECUTED"),
 ("c2013a-rights", "2013052101674004", "p040", (0.05, 0.10, 0.96, 0.60),
  "Exhibit D (landscape) — lot 22 generated 28,625, retained 17,899, "
  "excess 10,726.", "EXECUTED"),
 ("c2019-l49env", "2019071700601003", "p044", (0.02, 0.11, 1.00, 0.64),
  "Exhibit D — the split: lot 49 keeps 141,929 sf, lot 50 takes 127,035.",
  "EXECUTED"),
 ("c2020-mtge", "2020081400407001", "p001", (0.05, 0.60, 0.55, 0.92),
  "Cover page FEES AND TAXES block — $140,000 of mortgage tax on $5,000,000, "
  "which is the 2.800% commercial rate.", "EXECUTED"),
 # ⚠ the one that must never be shown without its status
 ("term:1008000022:2", "2013052101674004", "p044", (0.10, 0.10, 0.92, 0.50),
  "Exhibit G ¶2 — DOB consent required to modify or terminate. ⚠ THIS SITS IN "
  "AN UNEXECUTED FORM; it binds only once the confirming easement is requested "
  "and signed.", "FORM"),
]


# ⚠ CROP BOXES ERR WIDE, ALWAYS.
# The first pass on the 2010 chart used a 0.06-0.95 box and clipped both the
# row labels and the TOTAL column — so the proof showed the numbers but not
# what they were called or what they summed to. A proof that cuts off the
# total is a worse proof than none, because it looks complete. Bytes are not
# the scarce resource here; 15 KB vs 22 KB is nothing against a wrong read.


def crop(doc, page, box, dpi_scale=0.667):
    from PIL import Image
    src = PAGES / doc / f"{page}.png"
    if not src.exists():
        return None, None
    im = Image.open(src)
    w, h = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    c = c.resize((max(1, int(c.width * dpi_scale)),
                  max(1, int(c.height * dpi_scale))), Image.LANCZOS).convert("1")
    b = io.BytesIO()
    c.save(b, "PNG", optimize=True)
    return b.getvalue(), c.size


# ---------------------------------------------------------------------------
# AUTO-PROOF: every citable claim gets a proof. Where the exact region on the
# page is known it is cropped; where it is not, the FULL PAGE is stored and
# flagged PAGE so the imprecision is visible rather than implied.
#
# ⚠ precision is recorded, never assumed:
#   REGION  a hand-set box around the specific table or clause
#   PAGE    the whole page — honest, legible, and a standing invitation to
#           refine. A PAGE proof is NOT a failure; it is a proof that has not
#           been narrowed yet, and saying so is the point.
# ---------------------------------------------------------------------------
def auto_proofs():
    import claims as K
    known = {(d, pg): (box, cap, st)
             for _, d, pg, box, cap, st in PROOFS}
    seen, out = set(), []
    for c in K.rows():
        if not c["page"] or c["evidence"] == "index":
            continue
        key = (c["document_id"], c["page"])
        if key in seen:
            out.append((c["claim_id"], key))
            continue
        seen.add(key)
        out.append((c["claim_id"], key))
    return seen


def main():
    OUT.mkdir(exist_ok=True)
    rows, total = [], 0
    for cid, doc, page, box, cap, status in PROOFS:
        data, dims = crop(doc, page, box)
        if data is None:
            print(f"  MISSING {doc}/{page}")
            continue
        dg = hashlib.sha256(data).hexdigest()
        path = OUT / f"{dg[:16]}.png"
        path.write_bytes(data)
        total += len(data)
        is_term = cid.startswith("term:")
        rows.append(dict(proof_id=dg, claim_id=None if is_term else cid,
                         term_key=cid[5:] if is_term else None,
                         document_id=doc, page=page,
                         x0=box[0], y0=box[1], x1=box[2], y1=box[3],
                         caption=cap, bytes=len(data), dpi=200, bit_depth=1,
                         instrument_status=status,
                         storage_path=str(path.relative_to(HERE))))
        flag = "  ⚠ FORM" if status == "FORM" else ""
        print(f"  {cid:<22} {doc} {page}  {dims[0]}x{dims[1]}  "
              f"{len(data)/1024:>5.0f} KB{flag}")

    print(f"\n  {len(rows)} proofs · {total/1024:.0f} KB total · "
          f"{total/len(rows)/1024:.0f} KB average")

    # what this means at scale, from measured numbers
    PER_DOC = 3
    DOCS_CITY = 17_036_716
    avg = total / len(rows)
    print(f"\nSCALE, at {PER_DOC} proofs per document")
    print(f"  citywide proofs   {DOCS_CITY*PER_DOC/1e6:,.0f} million · "
          f"{DOCS_CITY*PER_DOC*avg/1024**4:,.2f} TB")
    print(f"  vs full imagery   16.7 TB  ->  "
          f"{16.7/(DOCS_CITY*PER_DOC*avg/1024**4):.0f}x smaller")
    print(f"  a 7,030-lot territory (~84k docs)  "
          f"{84_000*PER_DOC*avg/1024**3:,.1f} GB")

    # ---- every remaining citable page gets a full-page proof ----------
    import claims as K
    have = {(r["document_id"], r["page"]) for r in rows}
    link = []
    for c in K.rows():
        if not c["page"] or c["evidence"] == "index":
            continue
        key = (c["document_id"], c["page"])
        link.append((c["claim_id"], key))
        if key in have:
            continue
        data, dims = crop(c["document_id"], c["page"], (0.0, 0.0, 1.0, 1.0))
        if data is None:
            continue
        have.add(key)
        dg = hashlib.sha256(data).hexdigest()
        (OUT / f"{dg[:16]}.png").write_bytes(data)
        total += len(data)
        rows.append(dict(proof_id=dg, claim_id=None, term_key=None,
                         document_id=c["document_id"], page=c["page"],
                         x0=0.0, y0=0.0, x1=1.0, y1=1.0,
                         caption=f"full page — region not yet narrowed",
                         bytes=len(data), dpi=200, bit_depth=1,
                         instrument_status="UNKNOWN",
                         storage_path=str((OUT / f"{dg[:16]}.png").relative_to(HERE))))
    idx = {(r["document_id"], r["page"]): r["proof_id"] for r in rows}
    lk = [dict(claim_id=cid, proof_id=idx[k]) for cid, k in link if k in idx]
    with open(HERE / f"acris_claim_proof_{L49}.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["claim_id", "proof_id"])
        w.writeheader(); w.writerows(lk)
    reg = sum(1 for r in rows if (r["x1"]-r["x0"]) < 0.999)
    print(f"\n  PROOF COVERAGE: {len(rows)} proofs backing {len(lk)} claim links")
    print(f"    {reg} narrowed to a REGION · {len(rows)-reg} still full PAGE")
    print(f"    {total/1024:.0f} KB total for the parcel")

    p = HERE / f"acris_proof_{L49}.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {p.name} and {len(rows)} images to proofs/")
    forms = [r for r in rows if r["instrument_status"] == "FORM"]
    if forms:
        print(f"\n  ⚠ {len(forms)} proof(s) are crops of an UNEXECUTED FORM.")
        print("    The pixels look exactly like an executed covenant. The card")
        print("    must render instrument_status beside the image, always.")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
