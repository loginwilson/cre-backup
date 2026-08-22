"""CLAIMS — the atomic decode. One row per thing a document says.

See DECODE_SHAPE.md for why the claim is the atom. In short: the Brick Farms
ZLDA states eight facts across five pages destined for five different tables, so
neither "one row per document" nor "one row per event" can hold a decode.

EVERY CLAIM CARRIES:
    where it came from   document_id + page, never null
    what kind it is      predicate, from a closed vocabulary
    what it is ABOUT     subject_bbl, which is often NOT the filing parcel
    when the thing happened   effective   ← the narrative orders by this
    when the record said so   stated      ← the audit orders by this
    how it was established    evidence: read | derived | index

⚠ THE POINT OF THIS FILE (Login, 2026-08-06): "you are coming to decoded
conclusions and storing them in a table so that you aren't just recalling what
you know. You have it recorded and accurate."

    A conclusion held in prose is re-derived every time it is used, by whoever
    is reading, from memory. A conclusion held as a claim is stated once, cited
    once, graded once, and every later use is a lookup. The difference showed up
    today: the same file said the Horne chart was unread while quoting the
    $202.00/BSF that only that chart produces.
"""
import csv, json, pathlib, re, sys
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
L49 = "1008000049"

DDL = """
create table if not exists acris_claims (
  claim_id     text primary key,
  bbl          text not null,          -- the parcel this claim is FILED under
  subject_bbl  text not null,          -- what it is ABOUT (often different)
  document_id  text not null,
  page         text,                   -- null only for index-sourced claims
  predicate    text not null,
  value_num    numeric,
  value_text   text,
  unit         text,
  -- ⚠ GEOMETRY. Added 2026-08-06 after acris_claims FAILED the extent test in
  -- DECODE_EXACTNESS.md. A claim about a volume stored only as a scalar makes
  -- a whole-lot height plane and a 20-ft band indistinguishable. Null on the
  -- ~85% of claims that are money or parties — nullable, not absent, because
  -- "this fact has no geometry" and "we did not record its geometry" must not
  -- look the same. Where a geometric claim leaves these null, the row is
  -- INCOMPLETE and geometry_gaps() reports it.
  region_scope text,       -- WHOLE_LOT | BAND | PORTION | VOLUME_ABOVE
  v_from       numeric,    -- lower bound of the affected volume
  v_to         numeric,    -- null = unlimited above
  v_datum      text,       -- curb level | Manhattan Topo Bureau datum | ...
  h_extent     numeric,    -- band depth in feet
  h_from       text,       -- the line it is measured from
  duration     text,       -- PERPETUAL | TERM | DURING_CONSTRUCTION | n/a
  parties      jsonb,
  effective    date,                   -- when the thing HAPPENED
  stated       date,                   -- when the document said it
  answers      text[] not null,
  evidence     text not null,          -- read | derived | index
  verbatim     text,
  derivation   text,
  supersedes   text references acris_claims(claim_id),
  updated_at   timestamptz default now()
);
create index if not exists acris_claims_subject on acris_claims(subject_bbl, effective);
create index if not exists acris_claims_pred on acris_claims(predicate);
create index if not exists acris_claims_doc on acris_claims(document_id);
create index if not exists acris_claims_answers on acris_claims using gin(answers);

create table if not exists acris_claim_edges (
  from_claim text not null references acris_claims(claim_id),
  to_claim   text not null references acris_claims(claim_id),
  relation   text not null,   -- FINANCES ENABLES SUPERSEDES CORROBORATES
                              -- CONTRADICTS SAME_BATCH CROSS_REFERENCES
  basis      text not null,   -- stated | inferred
  confidence text,
  note       text,
  primary key (from_claim, to_claim, relation)
);

-- ⚠ the gap between the two time axes, as a queryable finding
create or replace view acris_recording_lag as
select bbl, document_id, predicate, effective, stated,
       (stated - effective) as lag_days
from acris_claims
where effective is not null and stated is not null and stated <> effective
order by (stated - effective) desc;
"""

# ---------------------------------------------------------------------------
# THE VALUE KIND OF EVERY PREDICATE — declared, and enforced at build time.
#
# LOGIN, 2026-08-06: "you need to know what reports are NUMERICAL and what are
# TEXT. I think that may be what is tripping up your decoder. Some are terms in
# a document and others are cited numbers like a dollar amount or SF."
#
# That was the defect. The vocabulary said what each predicate MEANS and never
# what KIND of value it carries, so C() accepted a number, a sentence, or both
# for any predicate — and nothing checked. The result: `unit_cap` held the
# number 7 with its enforceability nowhere; `easement` held a paragraph with no
# structure; `cross_reference` held a pointer treated like prose.
#
# FIVE KINDS, and the kind decides the validation AND where the substance lives:
#
#   QUANTITY    a measured number. MUST have value_num and a unit. The unit is
#               not decoration — 130 without ft, or 2.8 without %, is not a fact.
#   IDENTIFIER  a pointer into a record: CRFN, reel/page, title number. Text,
#               but NOT prose — it resolves to another document, and must never
#               be paraphrased.
#   PARTY       a named entity or person with the capacity it acted in.
#   TERM_REF    an obligation or prohibition. The claim only ANNOUNCES it; the
#               substance is the deontic row in acris_terms (actor/modality/
#               action/consent_of). A term summarised into value_text is the
#               failure this whole distinction exists to prevent.
#   ASSERTION   a plain statement with neither number nor structure —
#               "the cover page says APARTMENT BUILDING".
#
# ⚠ THE TRAP THIS FIXES, BOTH WAYS:
#   things that LOOK numeric but are terms   — a 7-unit cap is a number whose
#       force is a covenant; the number without CONSENT_OF is useless
#   things that LOOK textual but are pointers — a CRFN is not a description
# ---------------------------------------------------------------------------
PREDICATES = {
 # predicate: (kind, meaning)
 "conveyance":            ("PARTY",      "title passed from one party to another"),
 "consideration":         ("QUANTITY",   "the price actually paid, however established"),
 "consideration_recited": ("QUANTITY",   "the nominal sum the instrument states"),
 "mortgage":              ("QUANTITY",   "new money lent"),
 "consolidation":         ("QUANTITY",   "existing debt rolled forward, no new money"),
 "tax_paid":              ("QUANTITY",   "a transfer or mortgage tax stamp"),
 "tax_rate":              ("QUANTITY",   "the rate that stamp implies"),
 "rights_transferred":    ("QUANTITY",   "development rights moved between lots"),
 "rights_retained":       ("QUANTITY",   "development rights a seller kept"),
 "rights_generated":      ("QUANTITY",   "floor area a lot generates at the applicable FAR"),
 "envelope_balance":      ("QUANTITY",   "a lot's allowable floor area after an event"),
 "far_implied":           ("QUANTITY",   "the FAR the document's arithmetic implies"),
 "lot_area":              ("QUANTITY",   "land area in square feet"),
 "unit_cap":              ("QUANTITY",   "a recorded limit on dwelling units — the NUMBER; "
                                         "its enforceability is a TERM in acris_terms"),
 "easement":              ("TERM_REF",   "a burden for light, air, or access — substance in acris_terms"),
 "zoning_lot_members":    ("TERM_REF",   "the lots comprising one zoning lot, and the restriction that follows"),
 "cross_reference":       ("IDENTIFIER", "the instrument points at another instrument"),
 "reel_page":             ("IDENTIFIER", "the pre-CRFN filing location"),
 "party_role":            ("PARTY",      "a named party and the capacity it acted in"),
 "person":                ("PARTY",      "a natural person, with the role that names them"),
 "subdivision":           ("ASSERTION",  "one tax lot became more than one"),
 "property_type":         ("ASSERTION",  "the use the cover page declares"),
 "boundary_origin":       ("ASSERTION",  "the survey or partition a description derives from"),
 "defect":                ("ASSERTION",  "something wrong with the record itself"),
 "unresolved":            ("ASSERTION",  "a question the documents raise and do not answer"),
}
KIND = {k: v[0] for k, v in PREDICATES.items()}


def validate_kinds(claims):
    """Enforce the declared kind. Returns a list of violations, never raises.

    ⚠ Run against the existing 107 claims this found real breaches — see the
    report. The point is not that the claims were unusable; it is that nothing
    had ever CHECKED, so any of them could have been.
    """
    bad = []
    for c in claims:
        k = KIND.get(c["predicate"])
        n, txt, u = c.get("value_num"), c.get("value_text"), c.get("unit")
        if k == "QUANTITY":
            if n is None:
                bad.append((c["claim_id"], k, "QUANTITY with no value_num"))
            elif not u:
                bad.append((c["claim_id"], k, "QUANTITY with no unit — "
                            f"'{n:g}' of what?"))
        elif k == "IDENTIFIER":
            if not txt:
                bad.append((c["claim_id"], k, "IDENTIFIER with no value_text"))
            elif n is not None:
                bad.append((c["claim_id"], k, "IDENTIFIER carrying a number"))
        elif k == "TERM_REF":
            if n is not None:
                bad.append((c["claim_id"], k, "TERM_REF carrying a number — "
                            "the substance belongs in acris_terms"))
        elif k in ("PARTY", "ASSERTION"):
            if not txt:
                bad.append((c["claim_id"], k, f"{k} with no value_text"))
            if n is not None and k == "PARTY":
                bad.append((c["claim_id"], k, "PARTY carrying a number"))
    return bad


# ---------------------------------------------------------------------------
# THE LOT 49 CLAIM SET.
# Each tuple: (id, subject_bbl, doc, page, predicate, num, text, unit,
#              effective, stated, evidence, verbatim/derivation)
# subject "" means the filing parcel (lot 49).
# ---------------------------------------------------------------------------
def C(cid, doc, page, pred, num=None, text=None, unit=None, eff=None,
      stated=None, ev="read", subject="", note=None, parties=None, ans=None,
      scope=None, vfrom=None, vto=None, vdatum=None, hext=None, hfrom=None,
      dur=None, supersedes=None):
    return dict(claim_id=cid, bbl=L49, subject_bbl=subject or L49,
                document_id=doc, page=page, predicate=pred, value_num=num,
                value_text=text, unit=unit, parties=parties,
                region_scope=scope, v_from=vfrom, v_to=vto, v_datum=vdatum,
                h_extent=hext, h_from=hfrom, duration=dur,
                effective=eff, stated=stated or eff, answers=ans or [],
                evidence=ev, verbatim=note if ev == "read" else None,
                derivation=note if ev == "derived" else None,
                # ⚠ SUPERSESSION IS A RELATION, NOT A FIELD.
                # This column carries only the 1:1 cases; one
                # claim here replaces FOUR, which needs EDGES.
                supersedes=supersedes)

CLAIMS = [
 # ---- 1816 / 1971 -------------------------------------------------------
 C("c1816-boundary", "FT_1320008495632", "p001", "boundary_origin",
   text="Partition map filed Dec 1816 by Commissioners of Partition, separating "
        "Jacob Horn's portion from Matthew Dikeman's",
   eff="1816-12-01", stated="1971-10-04", ans=["PARCEL"],
   note="cited by every legal description of this parcel 1971-2013"),
 C("c1971-conveyance", "FT_1320008495632", "p001", "conveyance",
   text="112 WEST 25 REALTY CORP -> 112 WEST 25 COMPANY (co-partnership)",
   eff="1971-10-04", stated="1971-10-27", ans=["TITLE", "PARTY"]),
 C("c1971-recital", "FT_1320008495632", "p001", "consideration_recited",
   num=10, unit="USD", eff="1971-10-04", ans=["VALUE"],
   note="'In consideration of Ten Dollars' — the recital trap, 54 years ago"),
 # ⚠ SPLIT 2026-08-06 by the kind check. This was ONE claim typed
 # `cross_reference` (an IDENTIFIER) carrying $127,795.81 — a number and a
 # pointer fused into a single row. Nothing could use it: a debt query would
 # miss it because the predicate is not a QUANTITY, and a reference walk would
 # choke on the number. It is two facts and it is now two claims.
 C("c1971-mtge-ref", "FT_1320008495632", "p001", "cross_reference",
   text="subject to an existing GREENWICH SAVINGS BANK mortgage",
   eff="1971-10-04", ans=["ENCUMBER"]),
 C("c1971-mtge-bal", "FT_1320008495632", "p001", "consolidation",
   num=127_795.81, unit="USD",
   text="unpaid balance of the Greenwich Savings Bank mortgage taken subject to",
   eff="1971-10-04", ans=["ENCUMBER", "CAPITAL"],
   note="the ONLY real number on a deed that recites Ten Dollars"),
 C("c1971-reel", "FT_1320008495632", "p001", "reel_page", text="Reel 220 p836",
   eff="1971-10-27", ans=["IDENTIFY"]),
 C("c1971-area", "FT_1320008495632", "p001", "lot_area", num=15_642, unit="sf",
   eff="1971-10-04", ev="derived", ans=["PARCEL"],
   note="metes-and-bounds closure over six courses; closure error 0.167 ft. "
        "Resurveyed by 2010 to 15,639 sf (error 0.062) — a resurvey, not a "
        "boundary change"),
 C("c1971-counsel", "FT_1320008495632", "p001", "party_role",
   text="Abraham I. Kirschenbaum, Esq., 370 Seventh Avenue — counsel to both sides",
   eff="1971-10-04", ans=["PARTY"]),

 # ---- 1990 --------------------------------------------------------------
 C("c1990-mtge", "FT_1980000345898", None, "mortgage", num=1_000_000, unit="USD",
   eff="1990-07-05", ev="index", ans=["ENCUMBER", "CAPITAL"]),
 # ⚠ THE 1990 LENDER, filled from the ACRIS PARTIES dataset (636b-3b5g) while
 # building the ledger — not from any page. I had carried this as "(lender not
 # read)" all session while treating the 1990 mortgage as the root of a 33-year
 # chain. The index's party table answered it at zero cost; I had simply never
 # queried it. A source can be under-used as well as over-trusted.
 C("c1990-lender", "FT_1980000345898", None, "party_role",
   text="APPLE BANK FOR SAVINGS — mortgagee", eff="1990-07-05", ev="index",
   ans=["PARTY", "CAPITAL"]),
 C("c1999-assign", "FT_1810006667281", None, "party_role",
   text="APPLE BANK FOR SAVINGS assigns to QUEENS COUNTY SAVINGS BANK",
   eff="1999-06-29", ev="index", ans=["PARTY", "CAPITAL"],
   note="closes the chain: Apple Bank 1990 -> Queens County Savings Bank 1999 "
        "-> (QCSB renamed New York Community Bank) 2003 CEMA -> ... -> MetLife "
        "2023. The 33-year debt lineage now has every holder named"),
 C("c1990-reel", "FT_1980000345898", None, "reel_page",
   text="Reel 1707 Page 1285", eff="1990-07-05", ev="index", ans=["ENCUMBER"],
   note="the root every later consolidation cross-references"),

 # ---- 1998 deed — the event two ledger drafts missed --------------------
 C("c1998-conveyance", "FT_1570006671557", "p002", "conveyance",
   text="112 WEST 25 COMPANY -> EDELMAN FAMILY LIMITED PARTNERSHIP",
   eff="1998-11-23", stated="1999-06-29", ans=["TITLE", "PARTY"],
   note="Bargain and Sale with Covenant, Title No. 380-LY-8710"),
 C("c1998-partners", "FT_1570006671557", "p002", "person",
   text="Norman Edelman and Rita Edelman, co-partners of 112 West 25 Company, "
        "residing 1201 South Ocean Drive, Hollywood, Florida",
   eff="1998-11-23", ans=["PARTY"]),
 C("c1998-counsel", "FT_1570006671557", "p002", "person",
   text="Glen S. Edelman, Esq., Mandell Mandell & Edelman, 3000 Marcus Avenue, "
        "Lake Success NY — record-and-return party",
   eff="1998-11-23", ans=["PARTY"],
   note="the same person who signs the 2007 sale for the seller"),
 C("c1998-notary", "FT_1570006671557", "p002", "person",
   text="Mark J. Mandell, Notary Public No. 41-4518276, Queens County",
   eff="1998-11-23", ans=["PARTY"]),
 C("c1998-reel", "FT_1570006671557", "p002", "reel_page", text="Reel 2903 p1236",
   eff="1999-06-29", ans=["IDENTIFY"]),

 # ---- 1998 mortgage -----------------------------------------------------
 C("c1998-mtge", "FT_1710006669171", None, "mortgage", num=226_378.12, unit="USD",
   text="Edelman Family LP borrows from QUEENS COUNTY SAVINGS BANK, Flushing",
   eff="1998-11-24", stated="1999-06-29", ans=["ENCUMBER", "CAPITAL", "PARTY"]),
 C("c1998-mrt", "FT_1710006669171", None, "tax_rate", num=0.020000, unit="rate",
   eff="1998-11-24", ev="derived", ans=["CAPITAL"],
   note="handwritten margin 'MT $4527.56' / $226,378.12 = 2.0000% EXACTLY. "
        "Proves the modern 2.800% table cannot be applied backwards"),

 # ---- 2003 CEMA — also missed by two drafts -----------------------------
 C("c2003-cema", "2003110900238001", "p001", "consolidation",
   num=969_656.99, unit="USD",
   text="NEW YORK COMMUNITY BANK / EDELMAN FAMILY LP",
   eff="2003-10-28", stated="2003-11-28", ans=["ENCUMBER", "CAPITAL", "PARTY"],
   note="Taxable Mortgage Amount $0.00, Exemption 255 — no new money"),
 C("c2003-xref", "2003110900238001", "p001", "cross_reference",
   text="MANHATTAN Year 1990 Reel 1707 Page 1285", eff="2003-10-28",
   ans=["ENCUMBER"]),
 C("c2003-use", "2003110900238001", "p001", "property_type",
   text="APARTMENT BUILDING", eff="2003-10-28", ans=["ASBUILT", "OCCUPY"],
   note="what stood here before the hotel — the only ACRIS statement of prior use"),
 C("c2003-defect", "2003110900238001", "p001", "defect",
   text="cover says 'PAGE 1 OF 17'; field says 'Document Page Count: 15'; "
        "20 images are served", eff="2003-11-28", ans=["IDENTIFY"]),


 # ---- 1971: the round trip -----------------------------------------------
 C("c1971-roundtrip", "FT_1330008495633", "p001", "conveyance",
   text="TWO DEEDS, ONE ROUND TRIP. 112 West 25 Realty Corp conveyed to 112 "
        "West 25 Company on 1971-10-04 (Reel 220 p836); the Company conveyed "
        "it straight back to the Corp on 1971-10-09 (Reel 220 p838). Both "
        "recorded 1971-10-27 at 10:55, consecutive document numbers 12697 and "
        "12698, both bearing $00.00 transfer tax",
   eff="1971-10-09", stated="1971-10-27",
   parties=["112 WEST 25 REALTY CORP", "112 WEST 25 COMPANY (a co-partnership: "
            "David Gleicher, Anna Gleicher, David Lippel, Jennie Lippel)"],
   ans=["TITLE"],
   note="on the face of the record title ends that day back in 112 WEST 25 "
        "REALTY CORP - yet the 1998 grantor is 112 WEST 25 COMPANY"),
 C("c1971-greenwich", "FT_1320008495632", "p001", "consolidation",
   num=127_795.81, unit="USD",
   text="both 1971 deeds are taken SUBJECT TO 'a mortgage held by the "
        "Greenwich Savings Bank in the present unpaid principal amount of "
        "$127,795.81' - taken subject to, with no assumption language",
   eff="1971-10-04", ans=["CAPITAL", "TITLE"],
   note="the oldest debt figure in the record for this parcel"),
 C("c1816-partition", "FT_1320008495632", "p001", "boundary_origin",
   text="the metes and bounds derive from 'the partition map filed December, "
        "1816' - the boundary authority for this parcel is 209 years old",
   eff="1816-12-01", stated="1971-10-04", ans=["PARCEL"],
   note="recited identically in both 1971 deeds"),

 # ---- 1990: the root -----------------------------------------------------
 C("c1990-tax-actual", "FT_1980000345898", "p001", "tax_paid",
   num=22_500.00, unit="USD",
   text="the 1990 mortgage tax ACTUALLY PAID was $22,500.00 - witnessed "
        "TWICE: handwritten in the left margin of p001 as 'M.T. $22,500 -' "
        "and machine-stamped on the p026 recording backer as 'MTGETX 297509 "
        "$22,500.00', with 'Includes Special $2,500 -' written in the tax box",
   eff="1990-07-05", ans=["CAPITAL"],
   note="$22,500 / $1,000,000 = 2.25%, of which the Special component is "
        "$2,500 = 0.25%. Two independent witnesses on the same instrument"),
 C("c2003-affidavit-overstates", "2003110900238001", "p019", "defect",
   text="⚠ THE 2003 SECTION-255 EXEMPTION AFFIDAVIT CLAIMS 'Mortgage tAx paid "
        "$27,500.00' AGAINST THE 1990 MORTGAGE - $5,000 MORE THAN THE 1990 "
        "INSTRUMENT ITSELF RECORDS AS PAID ($22,500.00, twice witnessed)",
   eff="2003-11-28", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ the affidavit's own arithmetic ($27,500.00 + $4,527.56) is what "
        "justified recording $969,656.99 of consolidated debt at $0.00 tax. "
        "The agent cropped and enlarged the handwriting to confirm it reads "
        "27,500. This is a live exposure, not a transcription doubt - the "
        "exemption is supported by a figure the underlying record contradicts"),
 C("c1998-tax-decomp", "FT_1710006669171", "p009", "tax_rate",
   num=2.000, unit="percent",
   text="the 1998 mortgage tax decomposes into the full statutory stack on "
        "the endorsement: County (basic) 1132 + City (Addt'l) 2264 + Spec "
        "Addt'l 566 + TASF nil + MTA 566 + NYCTA nil = TOTAL 4528, against "
        "$226,378.12 = 0.500 + 1.000 + 0.250 + 0.250 = 2.000% exactly",
   eff="1999-06-29", ans=["CAPITAL"],
   note="two independent witnesses again: the p001 margin note 'MT / "
        "$4527.56' carries the unrounded cents, the p009 endorsement carries "
        "the rounded total AND the components. 1998 was 2.000%; by 2007 the "
        "same commercial rate is 2.800%"),
 C("c1990-rate-absent", "FT_1980000345898", "p014", "unresolved",
   text="⚠ THE 1990 ROOT MORTGAGE STATES NO INTEREST RATE AND NO MATURITY. "
        "Both are expressly delegated to a Note that was never recorded - "
        "p014 says only 'the Applicable Interest Rate as defined in the Note' "
        "and 'the Maturity Date as defined in the Note'. Prepayment too: 'If "
        "permitted by the Note, the Debt may be prepaid'",
   eff="1990-06-01", ans=["CAPITAL"],
   note="⚠ THE OFF-REGISTER STRUCTURE IS 35 YEARS OLD ON THIS PARCEL. The "
        "same move Anglo Irish makes in 2007, MetLife in 2023 and Deutsche "
        "Bank in 2025 - the operative economics in an unrecorded agreement - "
        "is already here in 1990. What the lien actually inherits forward is "
        "not a rate but a POSITION AND A MAXIMUM"),
 C("c1990-fixed", "FT_1980000345898", "p013", "unresolved",
   text="what the 1990 mortgage DOES fix numerically: default rate 'twenty "
        "four (24%) percent per annum' and a late charge of 'five (5%) "
        "percent' after ten days",
   eff="1990-06-01", ans=["CAPITAL"],
   note="the punitive numbers are recorded; the actual price of the money is "
        "not"),
 C("c1990-recourse", "FT_1980000345898", "p003", "unresolved",
   text="the 1990 mortgage is RECOURSE - no exculpation or non-recourse "
        "clause appears anywhere in paragraphs 1 through 48. It contemplates "
        "a Guarantor (para 20(e) defines the term, para 15 requires Guarantor "
        "balance sheets) but NO GUARANTY IS IN THE RECORDED PACKAGE",
   eff="1990-06-01", ans=["CAPITAL"],
   note="see c2003-nonrecourse - the flip happens thirteen years later"),
 C("c1990-dueonsale", "FT_1980000345898", "p008", "easement",
   text="the 1990 due-on-sale clause is unusually wide: consent needed for "
        "sale, installment sale, master lease, transfer of more than 10% of "
        "corporate stock, change or resignation of a general partner, AND "
        "'the removal or resignation of the managing agent' - consent 'in its "
        "sole discretion', and 'Mortgagee shall not be required to "
        "demonstrate any actual impairment of its security'",
   eff="1990-06-01", ans=["ENCUMBRANCE", "TITLE"],
   note="carve-out at 9(d): partnership interests may pass on death to "
        "immediate family of the deceased general partner. The Edelman "
        "family carve-out survives into the 1998 CEMA and the 2003 "
        "modification"),
 C("c1990-asbestos", "FT_1980000345898", "p018", "easement",
   text="the property is covered by an asbestos report - 'the report prepared "
        "by Enviro-Probe, Inc., dated February 27, 1990' - and para 35 "
        "requires the property be 'kept free of Asbestos' except as that "
        "report discloses. Para 36's environmental indemnity 'shall survive "
        "any termination, satisfaction, assignment, entry of a judgment of "
        "foreclosure or delivery of a deed in lieu of foreclosure'",
   eff="1990-06-01", ans=["ENCUMBRANCE"],
   note="an obligation that outlives the lien itself. Also the only "
        "environmental fact in the entire ACRIS record for this parcel"),

 # ---- the tenancy that closes a twelve-year loop --------------------------
 C("c1995-lease", "FT_1730006667273", "p001", "unresolved",
   text="THE OPERATING TENANCY, recorded nowhere else: the owner 'did, by "
        "Lease Agreement dated May 1, 1995 ... demise and lease to LMG "
        "REALTY, L.L.C., and which LMG REALTY, L.L.C. did, by Sublease "
        "Agreement, sublease to STEVE AND AL'S GARAGE, INC.'",
   eff="1995-05-01", stated="1998-11-24",
   parties=["LMG REALTY, L.L.C. (lessee)",
            "STEVE AND AL'S GARAGE, INC. (sublessee, the actual occupant)"],
   ans=["TENANCY", "INCOME"],
   note="⚠ THIS CLOSES A TWELVE-YEAR LOOP. LMG Realty L.L.C. is the same "
        "party paid $2,300,000 in 2007 for the assignment of its sublease "
        "(see c2007-2p3m-answer). The 2007 buyer was buying OUT the 1995 "
        "leasehold in order to merge the estates and develop. A parking "
        "garage occupied this site - which is why the deed showed no "
        "development-rights language and the property was worth assembling"),
 C("c1998-collat-lease", "FT_1730006667273", "p002", "easement",
   text="the lessor MUST NOT, without written consent, 'Cancel or surrender "
        "said LEASE', 'Modify said LEASE ... so as to decrease the term', or "
        "'Consent to an Assignment ... which will relieve LESSOR and/or "
        "LESSEE of liability' - and 'any of the above acts, if done without "
        "the written consent of ASSIGNEE, shall be null and void'",
   eff="1998-11-24", ans=["ENCUMBRANCE", "TENANCY"],
   note="the lender locked the 1995 LMG lease in place. Any 2007 buyer had to "
        "clear this to collapse the estates"),

 # ---- 1998: the seven-month lag, explained -------------------------------
 C("c1998-lag-explained", "FT_1370006667337", "p012", "defect",
   text="THE SEVEN-MONTH LAG WAS DEFECTIVE PAPERWORK, NOT AN ESCROW. Two "
        "documents carry the reviewer's handwritten rejection notes - 'Need a "
        "complete recital for consol.' and 'Need Back Sheets' on the "
        "collateral assignment p006, and 'Need Back Sheet' with an arrow on "
        "the CEMA p012, plus a struck title number '380-NY-8675' hand-"
        "corrected to 8710",
   eff="1999-06-29", ans=["IDENTIFY"],
   note="the deed was acknowledged 1998-11-23, one day BEFORE the refinance "
        "closed. The whole package then walked in together on 1999-06-29 "
        "within three minutes - 10:15 deed, 10:16 mortgage + cancellation + "
        "assignment + collateral assignment, 10:17 CEMA - all six sharing "
        "cashier receipt 63875. ⚠ THE LAG IS THE PACKAGE'S, NOT THE DEED'S. "
        "An event-date timeline built on recording dates puts this entire "
        "1998 transaction in 1999"),
 C("c1998-recital-defect", "FT_1570006671557", "p001", "defect",
   text="⚠ the 1998 deed recites 'the same as conveyed to the party of the "
        "first part by deed from 112 West 25 Realty Corp. dated October 9, "
        "1971 and recorded October 27, 1971 in Reel 220, Page 836' - but Reel "
        "220 p836 is DATED OCTOBER 4. The deed dated October 9 is at Reel 220 "
        "p838 AND IT RUNS THE OPPOSITE WAY, Company to Realty Corp",
   eff="1999-06-29", ans=["TITLE", "IDENTIFY"],
   note="⚠ the recital fuses the date of one instrument with the reel/page of "
        "the other, and the 1971 RETURN-LEG DEED IS NOT ACCOUNTED FOR "
        "ANYWHERE IN THE 1998 CONVEYANCE. Whether the Oct 9 deed was "
        "intended, delivered, or superseded cannot be determined from these "
        "instruments. This is very likely the ancestor of the 'NOTE: Recites "
        "incorrect legal description' flag that rides forward to today"),
 C("c1998-apple-balance", "FT_1810006667281", "p003", "consideration",
   num=798_621.88, unit="USD",
   text="Queens County Savings Bank paid $798,621.88 for Apple Bank's 1990 "
        "mortgage, and the section 275 affidavit swears 'There is presently "
        "outstanding under the Mortgage the principal sum of $798,621.88' - "
        "consideration equals the outstanding balance exactly",
   eff="1998-09-28", stated="1999-06-29", ans=["CAPITAL"],
   note="the acquire-the-paper move, 1998 edition - executed nine months "
        "before it was recorded. 'without recourse for any reason whatsoever "
        "against the Assignor'"),
 C("c1998-cema-typo", "FT_1370006667337", "p001", "defect",
   text="⚠ the 1998 CEMA's own consolidation figure disagrees with itself on "
        "one line: 'ONE MILLION TWENTY-FIVE THOUSAND AND 00/100 "
        "($1,035,000.00)' - words say 1,025,000, numerals say 1,035,000",
   eff="1998-11-24", ans=["CAPITAL"],
   note="$1,025,000.00 is stated correctly three other times (p001, p003 "
        "twice) and corroborated by the handwritten 'MTge Amt. 1,025,000.00' "
        "on the collateral assignment p001. Under NY construction the WORDS "
        "control. Recorded as a defect, not repaired"),
 C("c1998-interlineations", "FT_1370006667337", "p006", "defect",
   text="TWO INITIALLED HANDWRITTEN INTERLINEATIONS CHANGE THE DEAL and "
        "appear in no typed text: '* AND MANAGE THE LEASES' inserted into the "
        "rent-assignment clause (p006, widening the lender's power) and "
        "'REASONABLE' inserted into 'in its sole ^ determination' on cure "
        "extensions (p010, narrowing it)",
   eff="1998-11-24", ans=["ENCUMBRANCE", "INCOME"],
   note="⚠ no OCR or text-layer extraction finds these. They are only "
        "visible by looking at the page"),
 C("c1990-cancel-narrow", "FT_1260006667226", "p001", "defect",
   text="⚠ the 1999 instrument indexed SAGE DOES NOT SATISFY A MORTGAGE. It "
        "cancels only 'that certain Agreement for the Assignment of Leases "
        "... recorded July 5, 1990 in Reel 1707, page 1311'. The $1,000,000 "
        "mortgage at Reel 1707 p1285 was NOT discharged - it was assigned and "
        "consolidated forward",
   eff="1999-06-29", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ a satisfaction-keyed reader would mark the 1990 debt as closed "
        "here. It is still alive today inside the $123,000,000 lien. Also: "
        "the execution date is hand-corrected 'November' to 'October' with "
        "'SO IN ORIGINAL' stamped, and the notary's stamp reads 'Commission "
        "Expires April 24, 1998' - which PREDATES the October 28, 1998 "
        "acknowledgment"),

 # ---- 2003: the recourse flip --------------------------------------------
 C("c2003-nonrecourse", "2003110900238001", "p013", "easement",
   text="THE DEBT BECAME NON-RECOURSE IN 2003. Para 27: 'the covenants, "
        "obligations and liabilities of the party of the second part ... "
        "shall not be the personal liability of the party of the second part "
        "... and the sole remedies ... shall be to proceed against the "
        "premises, except for environmental issues'",
   eff="2003-10-28", stated="2003-11-28", ans=["CAPITAL"],
   note="⚠ the 1990 and 1998 debt was RECOURSE. This modification - which "
        "'does not create any additional indebtedness' and paid $0.00 tax - "
        "quietly moved the borrower's personal exposure to zero with a single "
        "environmental carve-out. A pure-dollars reading sees nothing happen "
        "in 2003"),
 C("c2003-balance", "2003110900238001", "p003", "consolidation",
   num=969_656.99, unit="USD",
   text="'as of November 1, 2003, is indebted ... in the sum of "
        "($969,656.99) Dollars', consolidated as 'a valid single first "
        "mortgage lien'",
   eff="2003-11-01", ans=["CAPITAL"],
   note="rate reset to 5.50% fixed through 2010-09-30, then Prime + 2.50% "
        "with a 5.50% floor and 16.00% cap; $5,505.61 monthly; maturity "
        "2015-12-01 - unchanged from the 1998 CEMA"),
 C("c2003-proptype", "2003110900238001", "p001", "property_type",
   text="the 2003 cover page declares the property type 'APARTMENT BUILDING' "
        "- while the only recorded tenancy is a parking garage (Steve and "
        "Al's Garage, Inc.) and the 1990 mortgage's dwelling-type box is "
        "circled 'OVER 6'",
   eff="2003-11-28", ans=["IDENTIFY"],
   note="⚠ cover-page property type is a filer's checkbox, not a survey. The "
        "2007 batch declares the same parcel 'COMMERCIAL REAL ESTATE'"),
 C("c1990-legal-conflict", "FT_1980000345898", "p023", "defect",
   text="⚠ TWO DIFFERENT METES FOR THE SAME LOT. The 1990 Exhibit A reads '82 "
        "feet 8-3/4 inches' and '114 feet 10 inches'; the 1998 deed and the "
        "2003 Schedule A read 'about 82 feet 10 inches' and '114 feet 6 "
        "inches more or less'",
   eff="1990-06-01", ans=["PARCEL"],
   note="not resolvable from these documents. A candidate ancestor for the "
        "'incorrect legal description' flag carried forward through six "
        "generations of consolidation"),
 # ---- 2007 --------------------------------------------------------------
 C("c2007-conveyance", "2007062101109001", "p001", "conveyance",
   text="EDELMAN FAMILY LP -> 112-118 WEST 25TH LLC (c/o Extell Development)",
   eff="2007-06-20", stated="2007-06-29", ans=["TITLE", "PARTY"]),
 C("c2007-price", "2007062101109001", "p001", "consideration", num=42_700_000,
   unit="USD", eff="2007-06-20", ans=["VALUE"]),
 C("c2007-signer", "2007062101109001", None, "person",
   text="Glen S. Edelman signs for the seller", eff="2007-06-20", ans=["PARTY"]),
 C("c2007-defect", "2007062101109001", "p003", "defect",
   text="page 3 is scanned upside down — a page a text pipeline drops silently",
   eff="2007-06-29", ans=["IDENTIFY"]),
 C("c2007-unres", "2007062101109002", None, "unresolved",
   num=2_300_000, unit="USD",
   text="RPTT&RET companion carries $2,300,000 in the index; corresponds to "
        "nothing about a $42.7M sale. PAGE NOT READ.",
   eff="2007-06-20", ev="index", ans=["VALUE"]),
 C("c2007-mtge", "2007062101109004", None, "mortgage", num=38_311_288, unit="USD",
   eff="2007-06-20", ev="index", ans=["ENCUMBER", "CAPITAL"]),
 C("c2007-pos", "2007062101109005", None, "consolidation", num=39_229_334,
   unit="USD", eff="2007-06-20", ev="index", ans=["CAPITAL"]),


 C("c2007-2p3m-answer", "2007062101109002", "p001", "consideration",
   num=2_300_000, unit="USD",
   text="the $2,300,000 is the price of a SECOND, SEPARATE conveyance closing "
        "the same day - the assignment of the SUBLEASE from LGM Realty, "
        "L.L.C. to 112-118 West 25th LLC. It is NOT a component of the "
        "$42,700,000 fee purchase and must never be added to it",
   eff="2007-06-20", stated="2007-06-29", ev="derived",
   parties=["LMG REALTY, LLC (grantor, as indexed; spelled LGM Realty, "
            "L.L.C. in the mortgage exhibit)", "112-118 WEST 25TH LLC"],
   ans=["VALUE", "TENANCY"],
   note="THREE INDEPENDENT PROOFS. (1) the grantor is not the seller of the "
        "fee - doc ...002 p001 names LMG REALTY LLC; the deed ...001 p001 "
        "names EDELMAN FAMILY LIMITED PARTNERSHIP. (2) both stamps "
        "reconstruct $2,300,000 from two different taxing authorities at two "
        "different rates: NYC RPTT $60,375.00 / 2.625% and NYS RETT "
        "$9,200.00 / 0.4%. (3) the instrument is NAMED at doc ...004 p015 "
        "Exhibit A-2 item 4: 'Assignment and Assumption of Sublease dated as "
        "of June 20, 2007 by and between LGM Realty, L.L.C., as assignor, "
        "and 112-118 West 25th LLC, as assignee'",
   supersedes="c2007-unres"),
 C("c2007-pagecount0", "2007062101109002", "p001", "defect",
   text="'Document Page Count: 0' - this is a TAX-RETURN-ONLY filing with no "
        "recordable instrument attached, which is exactly how a leasehold or "
        "economic-interest transfer is reported when the transfer instrument "
        "itself is never recorded",
   eff="2007-06-29", ans=["IDENTIFY", "VALUE"],
   note="THIS IS WHY THE INDEX LOOKED BROKEN - a $2.3M figure floating with "
        "no document behind it. The tax stamps are the entire evidentiary "
        "content. A decoder that requires a document body drops it silently"),
 C("c2007-merger", "2007062101109004", "p015", "unresolved",
   text="Exhibit A-2 shows the buyer collapsing THREE ESTATES on 2007-06-20 - "
        "the fee (deed, $42.7M), the prime lease (item 3, Edelman assignor), "
        "and the sublease (item 4, LGM, $2.3M) - ending at item 5, a 'Second "
        "Amendment to Lease ... by and between 112-118 West 25th LLC, as "
        "landlord, and 112-118 West 25th LLC, as tenant': a merger of "
        "estates in one owner",
   eff="2007-06-20", ans=["TITLE", "TENANCY"],
   note="the landlord and the tenant are the same LLC. This is why the site "
        "could later be developed - a split fee/leasehold cannot be"),
 C("c2007-facility", "2007062101109006", "p003", "unresolved",
   num=67_258_543, unit="USD",
   text="the LOAN is $67,258,543 but the RECORDED LIEN on lot 49 is capped at "
        "$39,229,334 - doc ...006 p003 prints both in adjacent recitals, the "
        "single reconciliation point for the whole batch",
   eff="2007-06-20", ans=["CAPITAL"],
   note="~$28.0M OF THE BORROWING IS SECURED ELSEWHERE AND IS INVISIBLE IN "
        "THIS PROPERTY'S RECORD. Anyone sizing outstanding debt from recorded "
        "face amounts understates this borrower's exposure. The CEMA's own "
        "p007 recital calls $67,258,543 'the outstanding aggregate principal "
        "amount of the Original Notes', which sits badly against Schedule B "
        "(notes of $1,000,000 + $226,378.12) and against the sworn 255 "
        "affidavit at p038 ($39,229,334) - read it as the new facility"),
 C("c2007-deed-bare", "2007062101109001", "p002", "unresolved",
   text="the $42,700,000 deed has NO 'subject to' clause, NO Schedule B of "
        "permitted exceptions, and NO reference to tenancies, liens or the "
        "mortgage. It is a bare Bargain and Sale Deed with Covenant Against "
        "Grantor's Acts carrying exactly two covenants: the grantor's-acts "
        "covenant and the Lien Law 13 trust-fund covenant",
   eff="2007-06-20", ans=["TITLE"],
   note="AND IT SAYS NOTHING ABOUT DEVELOPMENT RIGHTS, AIR RIGHTS, FAR OR "
        "ZONING LOTS - unusual for a through-block Chelsea assemblage parcel, "
        "and worth knowing before anyone represents that the record discloses "
        "encumbrances. The only 'together with' language is the standard "
        "streets-to-centerline clause"),
 C("c2007-throughblock", "2007062101109001", "p002", "unresolved",
   text="the deed's own legal description says the parcel is 'known as and by "
        "the street numbers 112-118 West 25th Street AND 113-117 West 24th "
        "Street' - a through-block parcel, though ACRIS indexes it only under "
        "the 25th Street address",
   eff="2007-06-20", ans=["PARCEL", "ENVELOPE"],
   note="the 24th Street half is what becomes lot 50 in the 2019 subdivision. "
        "An address-keyed search on 113-117 West 24th Street never finds this "
        "deed - one more reason the BBL, not the address, is the spine"),
 C("c2007-anglo-balance", "2007062101109003", "p004", "consideration",
   num=918_046.14, unit="USD",
   text="Anglo Irish Bank paid $918,046.14 for the assignment of the two "
        "consolidated 1990s mortgages, and the instrument states that is "
        "exactly 'the principal amount now due and owing'",
   eff="2007-06-20", ans=["CAPITAL"],
   note="consideration EQUALS outstanding balance - the purest form of the "
        "acquire-the-paper move. $1,000,000 (1990 Apple Bank) + $226,378.12 "
        "(1998 Queens County) had amortised to this"),
 C("c2007-gaptax", "2007062101109004", "p001", "tax_paid",
   num=1_072_716.41, unit="USD",
   text="$1,072,716.41 of mortgage recording tax paid on the $38,311,287.86 "
        "gap - fully taxable, no exemption claimed",
   eff="2007-06-29", ans=["CAPITAL"],
   note="1-CENT DISCREPANCY, both on-face: the cover page reads "
        "$1,072,716.41; the CEMA's own Schedule C at doc ...005 p036 reports "
        "the same payment as $1,072,716.40"),
 C("c2007-loanagt-governs", "2007062101109005", "p026", "unresolved",
   text="section 5.23: 'In the event of any inconsistency between the terms "
        "of the Mortgage and the terms of the Loan Agreement, the terms of "
        "the Loan Agreement shall govern' - and the Loan Agreement is "
        "UNRECORDED",
   eff="2007-06-20", ans=["CAPITAL"],
   note="THE RECORDED INSTRUMENTS ARE DELIBERATELY HOLLOW. The interest rate "
        "is not in the record (5.17 says only that it is variable, 'as more "
        "particularly set forth in the Loan Agreement'). 'Event of Default' "
        "is used throughout all four recorded loan documents and DEFINED IN "
        "NONE of them. Acceleration triggers, alteration and demolition "
        "consent, and lease-modification bars are all ABSENT from the record. "
        "This is the 2007 ancestor of the same off-register structure "
        "MetLife uses in 2023 and Deutsche Bank in 2025"),
 C("c2007-groundlease-lock", "2007062101109005", "p026", "unresolved",
   text="the borrower 'will not subordinate or consent to the subordination "
        "of the Ground Lease' - an absolute bar - and must exercise every "
        "renewal option on the lender's demand, with the lender appointed "
        "irrevocable attorney-in-fact to do it if the borrower will not",
   eff="2007-06-20", ans=["ENCUMBRANCE", "TENANCY"],
   note="a power of attorney 'coupled with an interest' over the leasehold "
        "estate. The lender may also enter the Leasehold Parcel to cure "
        "ground-lease defaults, repayable in 5 days at the Default Rate"),
 C("c2007-exhibit-mislabel", "2007062101109004", "p007", "defect",
   text="section 1.1 defines 'Ground Lease' as 'those certain documents "
        "listed in Schedule A-3 attached hereto', but the document actually "
        "annexed is captioned 'EXHIBIT A-2 / Ground Lease' at p015. There is "
        "no Schedule A-3",
   eff="2007-06-20", ans=["IDENTIFY"],
   note="the exhibit that resolves the $2,300,000 question is the one the "
        "definition points at by the wrong name"),
 # ---- 2010 air rights ---------------------------------------------------
 C("c2010-rights", "2010102601040006", "p038", "rights_transferred", num=53_578,
   unit="sf", eff="2010-10-14", stated="2010-11-16",
   ans=["ENVELOPE", "VALUE"],
   note="Exhibit D 'ALLOCATION OF DEVELOPMENT RIGHTS'; excess column, "
        "lots 53+55+56 = 23,864 + 15,070 + 14,644"),
 C("c2010-price", "2010102601040006", "p001", "consideration", num=5_000_000,
   unit="USD", eff="2010-10-14", ev="derived", ans=["VALUE"],
   note="ACRIS indexes this DEVR at $0. RPTT $131,250 / 2.625% = $5,000,000 and "
        "RETT $20,000 / 0.4% = $5,000,000 — two independent stamps agreeing"),
 C("c2010-rate", "2010102601040006", "p038", "tax_rate", num=93.32, unit="USD/sf",
   eff="2010-10-14", ev="derived", ans=["VALUE"],
   note="$5,000,000 / 53,578 sf"),
 C("c2010-far", "2010102601040006", "p038", "far_implied", num=10.0, unit="FAR",
   eff="2010-10-14", ev="derived", ans=["ENVELOPE"],
   note="246,540 generated / 24,654 sf of land. NOT PLUTO's current 12.0 — the "
        "applicable rule changed between then and now"),
 C("c2010-balance", "2010102601040006", "p038", "envelope_balance", num=209_968,
   unit="sf", eff="2010-10-14", ans=["ENVELOPE"]),
 C("c2010-ease", "2010102601040006", "p038", "easement",
   # ⚠ CORRECTED from p008 (the covenant) after this claim was first written
   # from p038 (the chart). The FUNCTION VIEW is what exposed it: the stale
   # claim and the corrected doctype term rendered side by side under ENVELOPE,
   # saying different things about the same easement. Three errors:
   #   "light and air"                    -> LIGHT, AIR AND VIEW
   #   "the lot line shared with lot 49"  -> the REAR LOT LINE, 20 ft NORTH
   #   "over the seller lots"             -> the 120 OWNER (lot 53) ALONE
   text="perpetual easement for LIGHT, AIR AND VIEW granted by the 120 Owner "
        "(lot 53) alone, from the rear lot line extending 20 ft north, "
        "beginning 23 ft above curb level",
   subject="1008000053",
   eff="2010-10-14", ans=["ENCUMBER", "ENVELOPE"],
   scope="BAND", vfrom=23, vdatum="curb level (as defined in the Zoning Resolution)",
   hext=20, hfrom="the REAR LOT LINE of the 120 Owner Land, extending north",
   dur="PERPETUAL",
   note="120 Owner hereby grants to Developer a perpetual easement for light, "
        "air and view ... beginning at the rear lot line ... extending a "
        "distance of twenty (20') feet to the north ... beginning at a height "
        "of twenty-three (23') feet above curb level"),
 C("c2010-l53", "2010102601040006", "p038", "rights_transferred", num=23_864,
   unit="sf", subject="1008000053", eff="2010-10-14", ans=["ENVELOPE"],
   note="120 W 25th: generated 40,770, retained 16,906, excess 23,864"),
 C("c2010-l55", "2010102601040006", "p038", "rights_transferred", num=15_070,
   unit="sf", subject="1008000055", eff="2010-10-14", ans=["ENVELOPE"],
   note="124 W 25th: generated 24,690, retained 9,620, excess 15,070"),
 C("c2010-l56", "2010102601040006", "p038", "rights_transferred", num=14_644,
   unit="sf", subject="1008000056", eff="2010-10-14", ans=["ENVELOPE"],
   note="126 W 25th: generated 24,690, retained 10,046, excess 14,644"),


 # ---- ⚠ the ZLDA itself is not here --------------------------------------
 C("c2010-zlda-missing", "2010102601040003", "p004", "defect",
   text="⚠ THE 2010 ZONING LOT DEVELOPMENT AND EASEMENT AGREEMENT IS NOT IN "
        "THIS CORPUS. All four recorded documents name it - 'that certain "
        "Zoning Lot Development and Easement Agreement (the ZLDA), dated as "
        "of the date hereof, made by and among Developer and Owner' - and "
        "none contains it. The batch CRFNs run 2010000384308, 384309, "
        "384310, 384311, all filed 2010-11-16 15:35; the ZLDA is 384312, the "
        "next number in the sequence",
   eff="2010-10-14", stated="2010-11-16", ev="derived",
   ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ RETRACTED — FALSE. The 2010 ZLDA is on disk as document"
        "2010102601040006, 110 pages. Eleven claims in this very ledger"
        "already cite it, including the 53,578 sf transfer. The"
        "CRFN-sequence reasoning was sound and the conclusion was still"
        "wrong, because I inferred from a sequence instead of checking"
        "the directory"),
 C("c2010-declaration-defers", "2010102601040003", "p004", "zoning_lot_members",
   text="the recorded Declaration of Zoning Lot Restrictions does only four "
        "things: it identifies Lot 49 as 'Developer Land' and Lots 53, 55 and "
        "56 as 'Owner Land', declares the combined parcel 'one zoning lot' "
        "under Section 12-10(d) of the Zoning Resolution, consents to "
        "enlargement, and annexes metes-and-bounds. It defers ALL easement "
        "substance to the ZLDA",
   eff="2010-10-14", stated="2010-11-16", subject="1008000053",
   ans=["ENVELOPE", "PARCEL"],
   note="⚠ THE DECLARATION IS THE ANNOUNCEMENT; THE ZLDA IS THE DEAL. A "
        "decoder that reads declarations and skips ZLDAs learns which lots "
        "were merged and nothing about what moved between them"),
 C("c2010-banks-bound-unsigned", "2010102601040004", "p003", "unresolved",
   text="TWO LENDERS BOUND THEIR LIENS TO A DOCUMENT NEITHER EVER SIGNED. New "
        "York Community Bank and Anglo Irish Bank each recorded a waiver "
        "making its mortgage 'subject and subordinate to the Zoning Lot "
        "Development and Easement Agreement dated as of October 14, 2010 ... "
        "which is intended to be recorded prior hereto or simultaneously "
        "herewith'",
   eff="2010-10-14", stated="2010-11-16", ans=["CONSENT", "ENCUMBRANCE"],
   note="⚠ CONSENT GIVEN IN ADVANCE, TO TERMS NOT YET RECORDED. The clearest "
        "instance of the rule I got wrong on the 2013 declaration: DO NOT "
        "INFER OWNERSHIP OR AGREEMENT FROM WHO SIGNED. Anglo Irish signed in "
        "Dublin before an Irish notary commissioned for life"),
 C("c2010-devrights-price", "2010110900202001", "p001", "consideration",
   num=5_000_000, unit="USD",
   text="the 2010 transfer from 120-22 W 25 STREET LLC to 112-118 WEST 25TH "
        "LLC carries 'NYC Real Property Transfer Tax: $131,250.00' and 'NYS "
        "Real Estate Transfer Tax: $0.00'. $131,250 / 2.625% = $5,000,000",
   eff="2010-10-14", stated="2010-11-09", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="⚠ BUNDLED, NOT PER-LOT. p002 adds a SECOND grantor, 124-26 W 25 "
        "STREET LLC, to the same property-data block covering Lots 53, 55, 56 "
        "AND 49 together - so this is one tax figure across multiple lots and "
        "two grantor LLCs, with no per-lot breakout. ⚠ AND THE NYS RETT IS "
        "$0.00, so unlike every other priced transfer in this corpus there is "
        "NO SECOND WITNESS to the $5,000,000. Treat it as a single-source "
        "derivation"),
 C("c2009-lot53-price", "2009122400274001", "p001", "consideration",
   num=5_242_000, unit="USD", subject="1008000053",
   text="the December 2009 fee acquisition of Lot 53 by 120-22 W 25 STREET "
        "LLC from 120 WEST 25TH STREET REALTY COMPANY, L.L.C. of Hurst, "
        "Texas: 'NYC Real Property Transfer Tax: $137,602.50' and 'NYS Real "
        "Estate Transfer Tax: $20,968.00'",
   eff="2009-12-17", stated="2009-12-24", ev="derived", ans=["VALUE", "TITLE"],
   note="TWO INDEPENDENT WITNESSES AGREE: $137,602.50 / 2.625% = $5,242,000 "
        "and $20,968.00 / 0.400% = $5,242,000. ⚠ SO THE ADJOINING LOT COST "
        "$5,242,000 IN FEE TEN MONTHS BEFORE ITS DEVELOPMENT RIGHTS MOVED FOR "
        "roughly $5,000,000 BUNDLED. The seller was an out-of-state LLC"),
 C("c2009-deed-truncated", "2009122400274001", "p001", "defect",
   text="⚠ TRUNCATED 1 OF 5. The cover page declares 'Document Page Count: 4' "
        "and 'PAGE 1 OF 5'; the folder holds ONE image. The granting clause, "
        "the full legal description, the habendum and every signature page "
        "are not on disk",
   eff="2009-12-24", ans=["IDENTIFY", "TITLE"],
   note="⚠ FOURTH CONFIRMED TRUNCATION. Everything I know about this "
        "conveyance comes from its tax stamps. That is enough to derive the "
        "price and nothing else"),
 C("c2010-005-truncated", "2010102601040005", "p001", "defect",
   text="⚠ TRUNCATED 8 OF 9. The cover page header reads 'PAGE 1 OF 9'; the "
        "folder holds eight images",
   eff="2010-11-16", ans=["IDENTIFY"],
   note="⚠ FIFTH CONFIRMED TRUNCATION. This is the Anglo Irish subordination "
        "- one page of a lender's consent instrument is simply absent"),
 C("c2010-legal-conflict-again", "2010102601040003", "p008", "defect",
   text="⚠ THE SAME BOUNDARY CONFLICT, TWENTY YEARS ON. Document ...002 p005 "
        "gives the course as 'about 82 feet 10 inches'; document ...003 p008, "
        "Exhibit A 'Developer Land', gives the identical course on the "
        "identical lot as '82 feet 8 3/4 inches'",
   eff="2010-10-14", ans=["PARCEL", "IDENTIFY"],
   note="⚠ INDEPENDENT CORROBORATION of c1990-legal-conflict. The 1990 "
        "mortgage said 82'8-3/4\" and 114'10\"; the 1998 deed and 2003 "
        "schedule said 82'10\" and 114'6\". BOTH VARIANTS ARE STILL IN "
        "CIRCULATION IN 2010, in two documents recorded the same minute. "
        "This is the live ancestor of the 'NOTE: Recites incorrect legal "
        "description' flag that rides forward into the current lien"),

 # ---- the Marriott ROFR, read in full ------------------------------------
 C("c2014-rofr-terms", "2014080700619001", "p004", "easement",
   text="Marriott's right of first refusal is 'to purchase the real estate ... "
        "upon the terms contained in Section 17.4, Section 17.5 and Section "
        "17.6 of the Agreement' - the Agreement being a FRANCHISE AGREEMENT "
        "dated July 14, 2014 which is not attached, not recorded, and not in "
        "this corpus",
   eff="2014-07-14", stated="2014-08-13", ans=["ENCUMBRANCE", "TITLE"],
   note="⚠ THE TRIGGER MECHANICS - what counts as a sale event - LIVE IN THE "
        "UNATTACHED SECTION 17.4. The recorded memorandum gives notice that a "
        "right exists and withholds every term that would let you price it. "
        "The same off-register structure as the mortgages, applied to an "
        "option instead of a loan"),
 C("c2014-rofr-duration", "2014080700619001", "p004", "easement",
   text="'The Right of First Refusal will terminate upon the termination of "
        "the Agreement; provided that in the event of an early termination "
        "of the Agreement, the Right of First Refusal WILL SURVIVE such early "
        "termination in accordance with the provisions of Section 17.6'",
   eff="2014-07-14", ans=["ENCUMBRANCE"],
   note="⚠ A VARIABLE DURATION, NOT A TERM OF YEARS. It can outlive the "
        "franchise that created it, on terms not in the record. No notice "
        "period for exercise appears anywhere in the eight pages. And no "
        "'successors and assigns' clause was found - though p004 calls the "
        "rights 'real estate rights in the Premises' for which 'damages are "
        "not an adequate remedy', which is how it runs with the land in "
        "substance"),
 C("c2014-rofr-conditional", "2014080700619001", "p004", "easement",
   text="the subordination has THREE conditions, all of which must hold: "
        "Marriott's rights 'will only be subordinate to the exercise of the "
        "rights of Lenders ... only if and for so long as: (i) the Lender is "
        "not a Competitor or Affiliate of a Competitor ... (ii) any such "
        "mortgage ... is and remains validly recorded and in full force and "
        "effect; and (iii) the indebtedness underlying such mortgage complies "
        "with the requirements of Section 5.2 of the Agreement'",
   eff="2014-07-14", ans=["ENCUMBRANCE", "PRIORITY"],
   note="⚠ CONDITION (iii) IS NEW AND I HAD ONLY TWO. The 2014 bank "
        "subordination recited conditions (i) and (ii); the underlying "
        "memorandum adds a THIRD - the debt itself must comply with Section "
        "5.2 of an unrecorded franchise agreement. So whether Marriott's ROFR "
        "sits ahead of or behind a $123,000,000 lien turns partly on a "
        "document nobody outside the deal can read"),
 C("c2014-rofr-counterparts", "2014080700619001", "p005", "defect",
   text="the memorandum is executed IN COUNTERPARTS and neither page is "
        "complete: p005 carries Marriott's signature (Kip W. Vreeland, Chief "
        "Officer, Full Service Franchising) with the franchisee block BLANK; "
        "p006 is the mirror image, Jeffrey Lam signed with the franchisor "
        "block blank",
   eff="2014-07-14", ans=["CONSENT", "IDENTIFY"],
   note="⚠ NEITHER PAGE ALONE PROVES AGREEMENT AND A READER WHO OPENS ONE "
        "SEES AN UNSIGNED FORM. Both notarial certificates are complete. Also "
        "⚠ Jeffrey Lam's acknowledgment is dated JUNE 18, 2014 - a month "
        "BEFORE the memorandum's own stated date of July 14, 2014"),
 C("c2014-rofr-exhibit-garbled", "2014080700619001", "p008", "defect",
   text="⚠ Exhibit 1's metes and bounds are badly corrupted against every "
        "other copy of this description: 'THENCE southerly parallel with the "
        "westerly side of 6th Avenue 18 feet' (elsewhere 114 feet 6 inches), "
        "'THENCE westerly parallel with the northerly side of 42th Street 75 "
        "feet' (there is no 42th Street; it is 24th), and 'THENCE northerly "
        "... 100 feet and 10 inches' (elsewhere 197 feet 6 inches)",
   eff="2014-08-13", ans=["PARCEL", "IDENTIFY"],
   note="⚠ THE ONLY RECORDED DESCRIPTION OF WHAT MARRIOTT'S OPTION COVERS IS "
        "INTERNALLY IMPOSSIBLE. Recorded as found; not repaired"),
 C("c2010-declaration-signdate", "2010102601040003", "p006", "defect",
   text="the Declaration is dated 'this 14th day of October, 2010' but its "
        "acknowledgment is dated 'the 11th day of December, 2009' - a "
        "ten-month gap consistent with a reused signature page",
   eff="2010-10-14", ans=["IDENTIFY"],
   note="⚠ THIRD DATE ANOMALY OF THE SESSION, all the same species: the 2013 "
        "spreader notarized eight days before its own execution date, the "
        "Marriott memorandum acknowledged a month early, and this one ten "
        "months. ⚠ AN ACKNOWLEDGMENT DATE IS NOT AN EVENT DATE and should "
        "never be used as one"),
 # ---- 2012 Horne --------------------------------------------------------
 C("c2012-rights", "2012122701550003", "p043", "rights_transferred", num=22_845,
   unit="sf", subject="1008000023", eff="2012-12-19", stated="2013-01-08",
   ev="derived", ans=["ENVELOPE", "VALUE"],
   note="THE QUANTITY IS STATED NOWHERE. Developer allocation 209,968 (2010 "
        "chart) -> 232,813 (this chart); the difference IS the purchase"),
 C("c2012-price", "2012122701550003", "p001", "consideration", num=4_614_690,
   unit="USD", eff="2012-12-19", ev="derived", ans=["VALUE"],
   note="RPTT $121,135.61 / 2.625% = $4,614,689.90 exact; RETT $18,460 / 0.4% = "
        "$4,615,000 which is the $500-rounded window, not a disagreement"),
 C("c2012-rate", "2012122701550003", "p043", "tax_rate", num=202.00, unit="USD/sf",
   eff="2012-12-19", ev="derived", ans=["VALUE"],
   note="$4,614,690 / 22,845 = $202.00 EXACT TO THE CENT — the tell that the "
        "parties negotiated per square foot"),
 C("c2012-balance", "2012122701550003", "p043", "envelope_balance", num=232_813,
   unit="sf", eff="2012-12-19", ans=["ENVELOPE"]),
 C("c2012-seller", "2012122701550003", "p043", "party_role",
   text="THE HORNE BUILDING OWNERS CORP, 127 W 24th — a residential CO-OP BOARD, "
        "fee owner of lot 23", subject="1008000023",
   eff="2012-12-19", ans=["PARTY"]),


 # ---- ⚠ the ground lease, named and dated --------------------------------
 C("c2012-groundlease", "2012101500666007", "p005", "unresolved",
   text="THE 1995 LEASE IS THE GROUND LEASE. Recital I: Borrower owns '(i) "
        "the Land and the Improvements ... (ii) the leasehold estate in the "
        "Land pursuant to that certain Lease dated as of May 1, 1995 between "
        "Borrower (AS SUCCESSOR-IN-INTEREST TO 112 WEST 25 COMPANY), as "
        "landlord, and Borrower (AS SUCCESSOR-IN-INTEREST TO LMG REALTY, "
        "L.L.C.), as tenant, as amended by a First Amendment dated as of June "
        "1, 1997, a Second Amendment dated as of June 1, 2007, and a Third "
        "Amendment dated as of November 30, 2008'",
   eff="1995-05-01", stated="2012-10-05", ans=["TENANCY", "TITLE"],
   note="⚠ THE SAME ENTITY IS BOTH LANDLORD AND TENANT, AND THE RECITAL SAYS "
        "SO IN TERMS. This closes the loop three ways: the 1998 collateral "
        "assignment named the LMG lease (c1995-lease); the 2007 batch bought "
        "LMG's sublease for $2,300,000 (c2007-2p3m-answer) and amended the "
        "lease the same day; and here in 2012 the merger is recited as "
        "settled fact. ⚠ THE THIRD AMENDMENT, 2008-11-30, IS AN EVENT I HAD "
        "NO RECORD OF AT ALL - none of the amendments is recorded"),
 C("c2012-fee-and-leasehold", "2012101500666006", "p004", "unresolved",
   text="the 2012 gap mortgage is titled a 'FEE AND LEASEHOLD MORTGAGE' and "
        "recites the same 1995 lease - so the lender took BOTH estates as "
        "collateral rather than relying on the merger",
   eff="2012-10-05", ans=["TENANCY", "DEBT"],
   note="⚠ A LENDER THAT MORTGAGES BOTH SIDES OF A MERGED LEASE IS INSURING "
        "AGAINST THE MERGER BEING UNDONE. Compare the 2007 CEMA's absolute "
        "bar on subordinating the ground lease and its irrevocable power of "
        "attorney to exercise renewals - three lenders in a row treat this "
        "leasehold as a live risk, not a formality"),
 C("c2012-no-garage", "2012101500666007", "p005", "unresolved",
   text="STEVE AND AL'S GARAGE, INC. appears NOWHERE in 110 pages of the 2012 "
        "batch, and neither does the 2007 sublease assignment",
   eff="2012-10-05", ans=["TENANCY"],
   note="the sublessee named in 1998 is gone from the record by 2012 and no "
        "instrument records its departure. ⚠ A TENANCY CAN LEAVE THE RECORD "
        "WITHOUT LEAVING A DOCUMENT - the only trace of the occupant is in "
        "the collateral assignment that pledged its rent"),

 # ---- ⚠ a $1,000 conflict inside one instrument --------------------------
 C("c2012-tax-conflict", "2012101500666007", "p044", "defect",
   text="⚠ THE SAME TAX FIGURE APPEARS FOUR TIMES IN ONE FILING AND ONE COPY "
        "DISAGREES BY $1,000. Schedule 1 attached to the mortgage (p044, "
        "cursive) reads '$46,001.60'. Schedule A attached to the bundled "
        "section 255 affidavit (p049, block print) reads '$45,001.60'. The "
        "gap mortgage's own typed cover-page total is $45,001.60, and "
        "document ...008 Schedule A (p022) also reads $45,001.60",
   eff="2012-10-31", ans=["DEBT", "IDENTIFY"],
   note="three of four agree; the outlier is handwritten. The agent confirmed "
        "it by pixel-level zoom rather than guessing. NOT REPAIRED - and note "
        "$45,001.60 / $1,607,226.43 = 2.800%, so the typed figure is the "
        "arithmetically correct one. ⚠ THE HANDWRITTEN FIGURES ARE WHERE THIS "
        "CORPUS BREAKS, EVERY TIME: the 2003 and 2014 prior-tax affidavits, "
        "the 2013 and 2014 new-money splits, and now this"),
 C("c2012-nooffset", "2012101500666007", "p004", "unresolved",
   text="recital E: 'The outstanding principal indebtedness evidenced by the "
        "Existing Notes and secured by the Existing Mortgages is $39,000,000 "
        "and Borrower represents and warrants that BORROWER HAS NO OFFSETS, "
        "DEFENSES OR COUNTERCLAIMS under or with respect to any of its "
        "obligations' - speaking as of October 5, 2012",
   eff="2012-10-05", ans=["DEBT", "PRIORITY"],
   note="a no-offset representation, not a no-default one, but dated and "
        "sworn. Together with the 2013 spreader's no-default rep these are "
        "the only two dated borrower representations found in the corpus"),
 C("c2012-consolidation-only", "2012101500666007", "p006", "consolidation",
   num=39_000_000, unit="USD",
   text="'the Existing Mortgages are hereby COMBINED AND CONSOLIDATED so that "
        "together they shall hereafter constitute in law but one mortgage, a "
        "single lien covering the Property ... and securing the principal sum "
        "of up to $39,000,000.00 and ... are hereby amended and restated in "
        "their entirety'. Maximum principal stated twice, words and numerals "
        "agreeing both times",
   eff="2012-10-05", stated="2012-10-31", ans=["DEBT"],
   note="⚠ NOT A SPREADER. Recital H lists 'spread' only among FUTURE "
        "modification possibilities. Second control case against the 2014 "
        "'NINETEEN MILLION ($48,000,000.00)' defect - 2012 and 2013 are both "
        "internally consistent, 2014 is not"),
 C("c2012-lot20-plane", "2012101500666008", "p017", "easement",
   text="the Lot 20 benefit is expressly bounded by a PLANE: 'TOGETHER WITH "
        "the benefits of that certain easement for light and air over Tax Lot "
        "20 (LOWER LIMITING PLANE) set forth in that certain Zoning Lot "
        "Development and Easement Agreement dated as of 2/14/2008 by and "
        "between 351 E 61 Realty LLC -and- 135 West 24th Buyer LLC, recorded "
        "on 2/26/2008 under CRFN 2008000078652'",
   eff="2008-02-14", stated="2012-10-31", subject="1008000020",
   vdatum="lower limiting plane (elevation not stated in this instrument)",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ 'LOWER LIMITING PLANE' MEANS LOT 49 OWNS AIR ABOVE AN ELEVATION "
        "AND SOMEONE ELSE OWNS BELOW IT - the cover page confirms it, listing "
        "Lot 20 as 'Fee above a plane'. ⚠ THE ELEVATION ITSELF IS NOT IN THIS "
        "DOCUMENT. It is in CRFN 2008000078652, and the parties to that 2008 "
        "agreement are NEITHER of this parcel's owners - a right lot 49 "
        "enjoys was created by two strangers four years earlier"),
 C("c2012-lots-listed", "2012101500666008", "p002", "zoning_lot_members",
   text="the cover page lists Block 800 Lot 49 as FEE, Lot 20 as 'Fee above a "
        "plane', and Lots 21, 22, 23, 53, 55 and 56 as 'DEVELOPMENT RIGHTS' "
        "parcels - three different species of interest on one cover page",
   eff="2012-10-31", ans=["ENVELOPE", "PARCEL"],
   note="⚠ AND SEVERAL OF THOSE LOTS' OWN PROPERTY TYPES READ 'APARTMENT "
        "BUILDING'. A decoder that treats every lot on a cover page as "
        "collateral would report this lender as holding liens on seven "
        "apartment buildings. It holds a fee, a fee above a plane, and six "
        "bundles of transferred floor area"),
 C("c2012-exhibit-asymmetry", "2012101500666008", "p016", "defect",
   text="⚠ document ...008's Exhibit A describes ONLY Parcel 1 (Lot 49) and "
        "Parcel 2 (part of Lot 20) by metes and bounds - there is NO legal "
        "description for Lots 21, 22, 23, 53, 55 or 56, although the cover "
        "page of the same instrument lists all of them as subject "
        "development-rights parcels",
   eff="2012-10-31", ans=["PARCEL", "IDENTIFY"],
   note="the companion mortgage ...007 does carry full Exhibit B-1/B-2 "
        "descriptions for those lots. ⚠ TWO INSTRUMENTS RECORDED THE SAME "
        "MINUTE, ONE DESCRIBING SIX LOTS THE OTHER ONLY NAMES"),
 C("c2012-loanagt-controls", "2012101500666008", "p010", "unresolved",
   text="section 5.1 'Conflict of Terms': 'In case of any conflict between "
        "the terms of this Assignment and the terms of the Loan Agreement, "
        "the terms of the Loan Agreement shall prevail' - and the mortgage "
        "itself contains NO parallel clause",
   eff="2012-10-05", ans=["DEBT", "IDENTIFY"],
   note="⚠ THE CONFLICT CLAUSE IS IN THE ASSIGNMENT, NOT THE MORTGAGE. "
        "Reading only the mortgage would show a self-contained instrument. "
        "The rate is deferred too - 'The Loan secured by this Mortgage is a "
        "VARIABLE INTEREST RATE LOAN, as more particularly set forth in the "
        "Loan Agreement' (...006 p011), with no maturity date either"),
 C("c2012-condemnation-split", "2012101500666007", "p009", "easement",
   text="condemnation proceeds are pledged in the MORTGAGE - 'All proceeds "
        "of any of the foregoing, including, without limitation, proceeds of "
        "insurance and condemnation awards' - but are ABSENT from the "
        "assignment of leases and rents' own property clause at ...008 items "
        "(a) through (i)",
   eff="2012-10-05", ans=["INCOME", "ENCUMBRANCE"],
   note="the same split found in 2014 and 2015. ⚠ A CONSISTENT DRAFTING "
        "CONVENTION ACROSS THREE LENDERS: condemnation rides with the "
        "mortgage, rents ride with the assignment. Worth encoding as an "
        "expectation rather than rediscovering each time"),
 C("c2012-prenotarized", "2012101500666007", "p035", "defect",
   text="the notary acknowledgments are dated JULY 5 and JULY 17, 2012 while "
        "the mortgage itself is dated OCTOBER 5, 2012 and recorded October "
        "31 - signature pages executed and notarized three months before the "
        "instrument's own date",
   eff="2012-07-17", stated="2012-10-31", ans=["IDENTIFY"],
   note="⚠ FOURTH DATE ANOMALY, ALL THE SAME SPECIES: the 2010 declaration "
        "acknowledged ten months early, the 2014 Marriott memorandum a month "
        "early, the 2013 spreader eight days early, and now this three months "
        "early. ⚠ AN ACKNOWLEDGMENT DATE IS NOT AN EVENT DATE AND MUST NEVER "
        "SEED A TIMELINE - this is now proven on four separate instruments"),
 C("c2012-devrights-pledged", "2012101500666007", "p006", "easement",
   text="section 1.01 items 2-3 grant 'Development Rights' as collateral: "
        "'The Development Rights Parcels or Excess Development Rights "
        "attributable thereto and, AS THEY ARE ACQUIRED BY BORROWER, the "
        "Excess Development Rights attributable to the Future Development "
        "Rights Parcels' - split across Exhibit B-1 (owned) and Exhibit B-2 "
        "(future)",
   eff="2012-10-05", ans=["ENVELOPE", "DEBT"],
   note="⚠ THE B-1 / B-2 SPLIT IS THE 2012 INVENTION and it is genuinely "
        "informative: B-1 is floor area already acquired, B-2 is floor area "
        "the borrower intends to acquire. The 2013 spreader drops the split "
        "back to a contingent catch-all (c2013-devrights-contingent). The "
        "lender's own exhibits record an ASSEMBLAGE STILL IN PROGRESS"),
 # ---- 2013 Brick Farms --------------------------------------------------
 C("c2013a-rights", "2013052101674004", "p040", "rights_transferred", num=10_726,
   unit="sf", subject="1008000022", eff="2013-05-17", stated="2013-06-19",
   ans=["ENVELOPE", "VALUE"],
   note="lot 22 generated 28,625, retained 17,899, excess 10,726"),
 C("c2013a-price", "2013052101674004", "p001", "consideration", num=1_450_000,
   unit="USD", eff="2013-05-17", ev="derived", ans=["VALUE"]),
 C("c2013a-rate", "2013052101674004", "p040", "tax_rate", num=135.19, unit="USD/sf",
   eff="2013-05-17", ev="derived", ans=["VALUE"], note="$1,450,000 / 10,726"),
 C("c2013a-balance", "2013052101674004", "p040", "envelope_balance", num=243_539,
   unit="sf", eff="2013-05-17", ev="derived", ans=["ENVELOPE"],
   note="232,813 + 10,726 = 243,539, matching the chart's own after-transfer row"),
 C("c2013a-ease", "2013052101674004", "p042", "easement",
   # ⚠ CORRECTED - I dropped "view" AGAIN. The 2010 easement had the same
   # slip and was fixed hours earlier; this one repeated it from the Exhibit F
   # description. VIEW is a separate protected interest and omitting it
   # understates the burden every time.
   text="perpetual easement for LIGHT, AIR AND VIEW over the whole of lot 22 "
        "above a fixed horizontal plane at 130 ft above the Manhattan "
        "Topographical Bureau datum (2.75 ft above USC&GS mean sea level, "
        "Sandy Hook). No mechanism exists to raise the plane",
   subject="1008000022", eff="2013-05-17",
   ans=["ENCUMBER", "ENVELOPE"],
   scope="WHOLE_LOT", vfrom=130,
   vdatum="Manhattan Highways/Topographic Bureau datum, 2.75 ft above NGVD 1929",
   hfrom="the entire lot 22 parcel", dur="PERPETUAL",
   note="the tower buys protected exposure, not only floor area"),
 C("c2013a-seller", "2013052101674004", "p032", "party_role",
   text="BRICK FARMS COOPERATIVE LTD, 131 W 24th, c/o Forest City Ratner — "
        "fee owner of lot 22", subject="1008000022", eff="2013-05-17",
   ans=["PARTY"]),
 C("c2013a-signer", "2013052101674004", "p025", "person",
   text="David L. Berliner, Vice President, signs for Brick Farms",
   eff="2013-05-17", ans=["PARTY"]),
 C("c2013a-buyer", "2013052101674004", "p024", "person",
   text="Marc Kwestel, Vice President, signs for 112-118 West 25th LLC",
   eff="2013-05-17", ans=["PARTY"]),
 C("c2013a-mortgagee", "2013052101674004", "p033", "party_role",
   text="RIDGEWOOD SAVINGS BANK, mortgagee on lot 22, consents",
   subject="1008000022", eff="2013-05-17", ans=["PARTY", "ENCUMBER"]),
 C("c2013a-members", "2013052101674004", "p033", "zoning_lot_members",
   text="Block 800 lots 49, 56, 55, 53, 23 and 22", eff="2013-05-17",
   ans=["ENVELOPE"]),
 C("c2013a-ubs", "2013052101674004", "p032", "party_role",
   text="UBS REAL ESTATE SECURITIES INC — mortgagee, assignee of leases and "
        "rents, and secured party on lot 49", eff="2013-05-17",
   ans=["PARTY", "ENCUMBER", "CAPITAL"]),

 # ---- 2013 133 West 24th ------------------------------------------------
 C("c2013b-rights", "2013052101674008", "p041", "rights_transferred", num=10_722,
   unit="sf", subject="1008000021", eff="2013-05-17", stated="2013-06-19",
   ans=["ENVELOPE", "VALUE"]),
 C("c2013b-price", "2013052101674008", "p001", "consideration", num=1_340_250,
   unit="USD", eff="2013-05-17", ev="derived", ans=["VALUE"],
   note="RPTT $35,181.56 / 2.625% exact"),
 C("c2013b-rate", "2013052101674008", "p041", "tax_rate", num=125.00, unit="USD/sf",
   eff="2013-05-17", ev="derived", ans=["VALUE"],
   note="$1,340,250 / 10,722 = $125.00 EXACT — the second exact-to-the-cent "
        "unit price on this block"),
 C("c2013b-balance", "2013052101674008", "p041", "envelope_balance", num=254_261,
   unit="sf", eff="2013-05-17", ans=["ENVELOPE"]),
 C("c2013b-cap", "2013052101674008", "p041", "unit_cap", num=7, unit="dwelling units",
   subject="1008000021", eff="2013-05-17", ans=["ENCUMBER", "OCCUPY"],
   note="lot 21 capped in perpetuity — the seller's own future constrained"),
 C("c2013b-signer", "2013052101674008", "p025", "person",
   text="Jonathan Pressman, board member, signs for 133 West 24th Street Corp",
   eff="2013-05-17", ans=["PARTY"]),
 C("c2013b-wf", "2013052101674008", "p033", "party_role",
   text="WELLS FARGO BANK NA as CMBS trustee, mortgagee on lot 21, consents",
   subject="1008000021", eff="2013-05-17", ans=["PARTY", "ENCUMBER"]),

 # ---- 2013 self-dealing airspace + final declaration + sale -------------
 C("c2013c-rights", "2013080901116002", "p040", "rights_transferred", num=14_703,
   unit="sf", subject="1008000020", eff="2013-08-07", stated="2013-08-27",
   ans=["ENVELOPE"],
   scope="VOLUME_ABOVE", vfrom=130,
   vdatum="Manhattan Highways/Topographic Bureau datum, 2.75 ft above NGVD 1929",
   hfrom="the entire lot 20 parcel (2,912 sf footprint)", dur="PERPETUAL",
   note="airspace above lot 20 (135 W 24th) above elevation 130 ft; 'Lower "
        "Parcel Land' 2,912 sf. One entity in two capacities, so zero tax"),
 C("c2013c-balance", "2013080901116002", "p040", "envelope_balance", num=268_964,
   unit="sf", eff="2013-08-07", ans=["ENVELOPE"],
   note="chart totals 390,160 across all lots and reconciles"),
 C("c2013c-unres", "2013080901116002", "p040", "unresolved",
   text="the PRICE of the lot 20 airspace is recorded against LOT 20, not here — "
        "$/sf for this transfer cannot be computed from lot 49's record",
   eff="2013-08-07", ans=["VALUE"]),
 C("c2013c-decl", "2013080901116001", "p003", "zoning_lot_members",
   # ⚠ CORRECTED. I wrote "single declarant, because Extell now controls every
   # rights interest" — inferring a fact about OWNERSHIP from a fact about
   # SIGNATURES. p006 says the opposite outright: six other owners are bound
   # "without their signatures hereto, by reason of their prior consent."
   text="Declaration of Zoning Lot Restrictions over EIGHT lots (49, 20, 21, "
        "22, 23, 53, 55, 56). ONE signature — but seven other fee owners and "
        "four mortgagees still held their interests. They are bound by ADVANCE "
        "WAIVER given in the earlier declarations, not by having sold out",
   eff="2013-08-07", ans=["ENVELOPE", "ENCUMBER", "CONSENT"],
   note="INDEXED AS 'SMIS'. The zoning lot in final form. The keystone is "
        "paragraph 4 of each May declaration, by which each owner waived its "
        "right to execute any future amended or replacement declaration"),
 C("c2013-sale", "2013080901116003", "p001", "conveyance",
   text="112-118 WEST 25TH LLC (Extell) -> LAM GEN 25 LLC",
   eff="2013-08-07", stated="2013-08-27", ans=["TITLE", "PARTY"]),
 C("c2013-price", "2013080901116003", "p001", "consideration", num=67_500_000,
   unit="USD", eff="2013-08-07", ev="derived", ans=["VALUE"],
   note="body recites Ten Dollars; RPTT $1,771,875 / 2.625% and RETT $270,000 / "
        "0.4% both resolve to $67,500,000 exactly"),
 C("c2013-gs", "2013081200922004", "p001", "party_role",
   text="GOLDMAN SACHS BANK USA — leases and rents assigned, $40,500,000",
   eff="2013-08-07", ans=["PARTY", "CAPITAL", "ENCUMBER"]),


 # ---- defects that would break a JOIN, not just a number ----------------
 C("c2013-phantom-party", "2013081200922005", "p001", "defect",
   text="⚠ the ACRIS cover page indexes PARTY TWO as '112-229 WEST 28TH LLC' "
        "while the instrument itself terminates an assignment made by "
        "'112-118 WEST 25TH LLC'. A phantom entity on a different street",
   eff="2013-08-28", ans=["PARTY", "IDENTIFY"],
   note="⚠ and the cover page's own text says it CONTROLS FOR INDEXING. A "
        "name-keyed join returns an entity that has nothing to do with this "
        "parcel — exactly the silent failure the signature ladder was built to "
        "avoid. Never join on the indexed name alone"),
 C("c2013-pagecount", "2013081200922004", "p017", "defect",
   text="the cover page states 'Document Page Count: 15' but 21 images exist — "
        "a 4-page section 255 affidavit sits OUTSIDE the stated count",
   eff="2013-08-28", ans=["IDENTIFY"],
   note="⚠ AND IT IS THE RICHEST PAGE IN THE BATCH: p021 is the only place "
        "stating the 2012 mortgage's tax paid ($45,001.60) and the only place "
        "laying out all six mortgage positions in sequence. A pipeline that "
        "caps at the stated page count loses it entirely"),
 C("c2025-truncated", "2025101700864003", "p001", "defect",
   text="⚠ THE $3,000,000 DEUTSCHE BANK MORTGAGE IS TRUNCATED ON DISK. Its "
        "cover page declares 'PAGE 1 OF 14' and a 12-page body; only p001 and "
        "p002 were extracted. Pages 3-14 — the granting clause, the gap "
        "recital, the legal description and the signatures — do not exist",
   eff="2025-10-23", ans=["IDENTIFY"],
   note="⚠ A FETCH DEFECT, NOT A RECORDING DEFECT. The cover page's own "
        "'PAGE 1 OF N' is a free integrity check that would have caught it. "
        "Assert count(pages) == N at extraction for every document"),
 C("c2013-kings-venue", "2013081200922002", "p008", "defect",
   text="the gap mortgage's venue clause names the COUNTY OF KINGS for a "
        "Manhattan property, while the assignment of rents executed the same "
        "day names the County of New York",
   eff="2013-08-07", ans=["IDENTIFY"],
   note="a template artifact, but it is what the recorded instrument says"),
 C("c2013-unrecorded-zlda", "2013081200922002", "p013", "unresolved",
   text="the schedule recites the lot 20 light-and-air easement as 'that "
        "certain zoning lot development and easement agreement TO BE RECORDED' "
        "— it had no CRFN as at 2013-08-07",
   subject="1008000020", eff="2013-08-07", ans=["ENVELOPE"],
   note="⚠ a gap in any development-rights chain assembled from CRFNs alone"),

 # ---- the 2013 spreader — and the correction to what I said it did -------
 C("c2013-spreader-scope", "2013081200922003", "p005", "unresolved",
   text="⚠ THE SPREADER DOES NOT REACH ANY ADDITIONAL TAX LOT. Section 4: the "
        "liens 'are hereby consolidated and coordinated so that together they "
        "shall hereafter constitute in law but one mortgage, a single, first "
        "lien upon the Premises securing the Indebtedness, and, as so "
        "consolidated and coordinated, ARE HEREBY SPREAD OVER THOSE PORTIONS "
        "OF THE PROPERTY NOT ALREADY COVERED THEREBY'",
   eff="2013-08-07", stated="2013-08-28", ans=["DEBT", "PARCEL"],
   note="⚠ CORRECTS MY OWN FRAMING. I called this 'the only true spreader in "
        "the chain' and briefed the agent that a spreader extends a lien onto "
        "ADDITIONAL LAND. It does not. 'Property' is Schedule C's defined "
        "term and 'Premises' is the single parcel in Schedule A - the spread "
        "is over interests in the SAME land the lien already sat on "
        "(fixtures, easements, after-acquired estates), not over new lots. "
        "The word 'spreader' in the title is doing less work than it looks"),
 C("c2013-devrights-contingent", "2013081200922003", "p022", "easement",
   text="development rights enter only as a FUTURE-ACQUISITION catch-all: "
        "'All additional lands, estates and development rights hereafter "
        "acquired by Mortgagor for use in connection with the Land and the "
        "development of the Land ... which may, from time to time, BY "
        "SUPPLEMENTAL MORTGAGE OR OTHERWISE be expressly made subject to the "
        "lien of this Security Instrument'",
   eff="2013-08-07", ans=["ENVELOPE", "DEBT"],
   note="⚠ CONTINGENT, NOT PRESENT. Contrast the companion assignment "
        "2013081200922001 p003, which splits '(i) the real property as "
        "described on Exhibit B-1 AND (ii) the development rights "
        "attributable to the real property as described on Exhibit B-2' into "
        "two parallel scheduled exhibits. The SPREADER has no such "
        "bifurcation - here the rights are boilerplate appurtenance plus a "
        "hook for a later supplemental mortgage. Two instruments in the same "
        "batch treat development rights completely differently"),
 C("c2013-consistent", "2013081200922003", "p052", "consolidation",
   num=40_500_000, unit="USD",
   text="the maximum principal secured is stated FOUR TIMES and every "
        "instance agrees - p004, p005, p006 and Schedule C section 16.7: 'the "
        "maximum amount of principal indebtedness secured by this Security "
        "Instrument at the time of execution hereof or which under any "
        "contingency may become secured ... is $40,500,000.00'",
   eff="2013-08-07", ans=["DEBT"],
   note="⚠ THE CONTROL CASE FOR THE 2014 DEFECT. Same law firm, same "
        "borrower, same lender family, fifteen months apart - this one is "
        "internally consistent four times over, and the 2014 instrument says "
        "'NINETEEN MILLION ... ($48,000,000.00)' twice. The 2014 error is a "
        "template failure, not house style. (This document has its own typo - "
        "'FORTY MILLION FIVE HUDNRED THOUSAND' at p004 - but the numerals "
        "and the intent agree)"),
 C("c2013-nodefault", "2013081200922003", "p005", "unresolved",
   text="section 1(b): 'As of the date hereof, there are no defaults or "
        "events of default under the Existing Notes and Mortgages, nor has "
        "any event occurred that would be a default thereunder with the "
        "passage of time, the giving of notice, or both' - speaking as of "
        "the stated execution date, August 7, 2013",
   eff="2013-08-07", ans=["DEBT", "PRIORITY"],
   note="⚠ THE ONLY DATED NO-DEFAULT REPRESENTATION FOUND IN THE CORPUS SO "
        "FAR. The 2014 CEMA has no representations article at all. A "
        "no-default rep with an as-of date is the single most useful sentence "
        "in a mortgage for reconstructing whether a borrower was in trouble - "
        "and it exists here and nowhere else"),
 C("c2013-firstlien", "2013081200922003", "p005", "unresolved",
   text="'a single, FIRST lien upon the Premises securing the Indebtedness'",
   eff="2013-08-07", ans=["PRIORITY"],
   note="an express first-lien statement. PRIORITY has been the thinnest "
        "function all session because instruments so rarely state their own "
        "rank on the face"),
 C("c2013-offrecord-mechanism", "2013081200922003", "p032", "unresolved",
   text="⚠ THERE IS NO 'THE LOAN AGREEMENT SHALL CONTROL' SENTENCE ANYWHERE "
        "IN 61 PAGES. The off-record mechanism here is different and quieter: "
        "whole CATEGORIES are defined by reference out. Section 4.4: the "
        "lender 'is expressly and primarily relying on the truth and accuracy "
        "of the warranties and representations set forth in ARTICLE 4 OF THE "
        "LOAN AGREEMENT'; section 14: 'All capitalized terms not defined "
        "herein shall have the respective meanings set forth in the Loan "
        "Agreement'; notices go to 'Section 8.12 of the Loan Agreement'",
   eff="2013-08-07", ans=["DEBT", "IDENTIFY"],
   note="⚠ A DISTINCTION WORTH KEEPING. I have been recording 'the unrecorded "
        "agreement controls' as one pattern. There are TWO: an express "
        "conflict clause (2007, 2014, 2023, 2025) and this - definitional "
        "hollowing, where no clause asserts priority but 'Event of Default' "
        "is used throughout Article 7 and DEFINED NOWHERE in the recorded "
        "text. The second is harder to spot and has the same effect"),
 C("c2013-norate", "2013081200922003", "p045", "unresolved",
   text="NO interest rate and NO maturity date appear in any of the 61 pages. "
        "'Maturity Date' is used only as an undefined cross-reference - 'not "
        "less than six (6) months prior to the stated Maturity Date' - and "
        "'Default Rate' likewise recurs with no numeric rate ever stated",
   eff="2013-08-07", ans=["DEBT"],
   note="61 pages, $40,500,000, and the price of the money is not in any of "
        "them. Consistent with 1990, 2007, 2014, 2023 and 2025"),
 C("c2013-notary-before", "2013081200922003", "p053", "defect",
   text="⚠ BOTH NOTARIZATIONS PREDATE THE INSTRUMENT. The mortgage "
        "acknowledgment (p053) and the section 255 affidavit jurat (p059) are "
        "each dated 'the 30 day of July, 2013' - EIGHT DAYS BEFORE the "
        "execution date the instrument recites for itself, 'made as of August "
        "7, 2013' (p004)",
   eff="2013-07-30", stated="2013-08-28", ans=["IDENTIFY"],
   note="⚠ compare the 1999 cancellation, where the notary's commission had "
        "EXPIRED before the acknowledgment date. Two instruments, fourteen "
        "years apart, both with acknowledgment dates that cannot be right. "
        "The 'as of' convention explains it but does not cure it"),
 C("c2013-onesided-again", "2013081200922003", "p053", "defect",
   text="only the mortgagor executes - the agent found NO Goldman Sachs Bank "
        "USA signature block in 61 pages",
   eff="2013-08-07", ans=["IDENTIFY", "CONSENT"],
   note="the same one-sided execution as the 2014 assignment of rents. A "
        "lender that never signs is normal for a mortgage and worth knowing "
        "before treating a signature block as evidence of who agreed"),
 C("c2013-handwritten-advance", "2013081200922003", "p004", "defect",
   text="a handwritten note sits beneath the typed WHEREAS clause reciting "
        "the $40,500,000 aggregate: '$1,500,000 was advanced to me'. A second "
        "handwritten annotation on the schedule at item 4(a) reads 'dated "
        "7/29/2013 by assignment of Mortgage to be recorded together "
        "herewith. unpaid principal $39,000,000.00 further assigned to "
        "Goldman Sachs Bank'",
   eff="2013-08-07", ans=["DEBT", "IDENTIFY"],
   note="⚠ THE NEW-MONEY SPLIT IS HANDWRITTEN AGAIN. $39,000,000 existing + "
        "$1,500,000 new = $40,500,000, and BOTH components exist only as "
        "marginalia - exactly as in 2014, where $40,500,000 + $7,500,000 = "
        "$48,000,000 was also only in handwriting. No OCR or text extraction "
        "finds either. THE MONEY IS IN THE MARGIN, TWICE"),
 C("c2013-pagecount-over", "2013081200922003", "p001", "defect",
   text="⚠ THE STATED PAGE COUNTS ARE ONE SHORT OF THE FILES ON DISK. The "
        "cover says 'Document Page Count: 53' with a banner 'PAGE 1 OF 55'; a "
        "second supporting-document cover at p057 says 'PAGE 1 OF 1' and "
        "lists a 4-page section 255 affidavit. 55 + 1 + 4 = 60. There are 61 "
        "images. The unaccounted page is p056, a continuation of the Exhibit "
        "A easement description covering Tax Lots 22, 23, 53, 55 and 56",
   eff="2013-08-28", ans=["IDENTIFY", "ENVELOPE"],
   note="⚠ MY INTEGRITY CHECK ONLY TESTS FOR TOO FEW PAGES. This is the "
        "opposite defect and it would have passed silently. An UNACCOUNTED "
        "page is as much a signal as a missing one - and this particular "
        "unaccounted page is the one listing the burdened lots"),
 C("c2013-easements-appurtenant", "2013081200922003", "p055", "easement",
   text="Exhibit A carries the light-and-air easements as APPURTENANT RIGHTS, "
        "not as land: 'TOGETHER WITH an easement for light and air over ... "
        "Tax Lot 20 ... Tax Lot 21 ...' and continuing to Lots 22, 23, 53, 55 "
        "and 56",
   eff="2013-08-07", subject="1008000053", ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ AN APPURTENANT EASEMENT IS NOT A FEE INTEREST. The seven burdened "
        "lots are NOT mortgaged - the lien reaches lot 49's RIGHT to light "
        "and air over them. A reader who treats the easement schedule as a "
        "collateral schedule overstates what the lender can foreclose on"),

 # ---- ⚠ the plane, contradicted -----------------------------------------
 C("c2013-plane-upper", "2013052101674002", "p009", "easement",
   subject="1008000020",
   text="⚠ THE SAME 130-FOOT PLANE, CALLED THE OPPOSITE THING. Here the "
        "excess development rights taken from Lot 20 are 'ALL that portion of "
        "the below described parcel LYING BELOW AN UPPER LIMITING PLANE drawn "
        "at an elevation of 130 feet above the datum level used by the "
        "topographical bureau, Borough of Manhattan, which is 2.78 feet above "
        "National Geodetic Survey vertical datum 1929'",
   eff="2013-05-17", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ CONTRADICTS HOW I READ c2012-lot20-plane AND c2019-lot20-elevation. "
        "The 2012 mortgage says 'Tax Lot 20 (LOWER limiting plane)'; the 2019 "
        "declaration splits Lot 20 into a Lower Parcel BELOW a LOWER limiting "
        "plane at 130 ft and an Air Space Parcel ABOVE it; this 2013 waiver "
        "describes the transferred rights as lying BELOW an UPPER limiting "
        "plane at the same 130 ft. The ELEVATION and DATUM are consistent "
        "across all three - the SIDE is not. ⚠ I WROTE THAT LOT 49 'OWNS AIR "
        "ABOVE AN ELEVATION'. THAT IS NOT ESTABLISHED. A limiting plane is "
        "named from the perspective of the estate being described, and I "
        "inferred a direction from a single adjective. Recorded as an open "
        "contradiction, not resolved"),

 # ---- ⚠ the ZLDAs are missing, again ------------------------------------
 C("c2013-zldas-missing", "2013052101674007", "p003", "defect",
   text="⚠ THE LOT 21 ZLDA AND THE LOT 22 ZLDA ARE BOTH ABSENT. Each is dated "
        "May 15, 2013 and each is named repeatedly across four of these "
        "documents - the Lot 22 ZLDA 'between Brick Farms Cooperative Ltd. "
        "and 112-118 West 25th LLC', the Lot 21 ZLDA 'between 133 West 24th "
        "Street Corporation and 112-118 West 25th LLC' - and neither is in "
        "the corpus",
   eff="2013-05-15", stated="2013-05-21", ev="derived",
   ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ RETRACTED — FALSE. The lot 21 and lot 22 ZLDAs are on disk as"
        "2013052101674008 (41 pages) and 2013052101674004 (45 pages),"
        "together with the lot 23 ZLDA (2012122701550003, 55 pages) and"
        "the lot 20 ZLDA (2013080901116002, 40 pages). ⚠ THIS CLAIM"
        "CARRIED THE 'FIFTH AND SIXTH INSTANCES' TALLY THAT MADE THE"
        "PATTERN LOOK PROVEN. A count of false instances is not"
        "corroboration"),
 C("c2013-nosquarefeet", "2013052101674007", "p021", "unresolved",
   text="⚠ ZERO SQUARE-FOOTAGE FIGURES IN 122 PAGES ACROSS TEN DOCUMENTS. No "
        "lot area, no floor area generated, transferred or retained, no "
        "envelope balance, no FAR and no price. Every dimensional figure is a "
        "linear metes-and-bounds course in feet and inches",
   eff="2013-05-21", ans=["ENVELOPE"],
   note="⚠ SCOPE ERROR. 'Zero square-footage figures' is true of the TEN"
        "DECLARATION AND WAIVER DOCUMENTS the agent was given, and false"
        "of the corpus — the ZLDAs on disk carry every transfer figure,"
        "and the envelope chain closes to the square foot from them. The"
        "structural lesson stands (declarations merge lots, ZLDAs move"
        "floor area); the coverage claim attached to it did not"),
 C("c2013-zlda-2007date", "2013052101674003", "p003", "cross_reference",
   text="⚠ CRFN 2010000384312 IS DATED FEBRUARY 2, 2007 - the recital reads "
        "'ZLDA dated February 2, 2007 ... recorded ... at CRFN 2010000384312' "
        "covering the Lots 53, 55 and 56 unused development rights",
   eff="2007-02-02", stated="2013-05-21", ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ SIGNED IN 2007, RECORDED IN 2010 - a three-and-a-half-year lag on "
        "the instrument that moved the first tranche of development rights "
        "onto this lot. The 2010 batch documents all bear an October 14, 2010 "
        "ZLDA date, so either two ZLDAs exist or the recital is describing an "
        "earlier agreement the 2010 one replaced. Not resolvable from what I "
        "hold - and the document that would resolve it is the one missing"),

 # ---- the merger sequence, dated -----------------------------------------
 C("c2013-merger-sequence", "2013052101674007", "p003", "zoning_lot_members",
   text="THE ASSEMBLAGE, IN ORDER. Lots 53, 55 and 56 merged into lot 49 by "
        "the 2010 Declaration (CRFN 2010000384309). Lot 23 joined by "
        "Declaration CRFN 2013000007932 with ZLDA CRFN 2013000007933, "
        "recorded 2013-01-08. Lot 22 (Brick Farms Cooperative Ltd) joined "
        "2013-05-17. Lot 21 (133 West 24th Street Corporation) joined last, "
        "completing the seven-lot Combined Zoning Lot",
   eff="2013-05-17", stated="2013-05-21", ans=["ENVELOPE", "PARCEL"],
   note="lots 20, 21, 22, 23, 53, 55, 56 assembled onto 49 across three "
        "years, one or two lots at a time, each requiring its own "
        "declaration, its own title certification and its own mortgagee "
        "waiver. Lot 50 does not exist yet - it is still part of lot 49"),
 C("c2013-brickfarms-ratner", "2013052101674003", "p001", "party_role",
   text="BRICK FARMS COOPERATIVE LTD is 'c/o FOREST CITY RATNER COMPANIES', "
        "and 133 West 24th Street Corporation is a separate cooperative; the "
        "2010 sellers 120-22 W 25 Street LLC and 124-26 W 25 Street LLC are "
        "'c/o SABET MANAGEMENT DEVELOPMENT COMPANY'",
   eff="2013-05-17", subject="1008000022",
   parties=["BRICK FARMS COOPERATIVE LTD (c/o Forest City Ratner Companies)",
            "133 WEST 24TH STREET CORPORATION",
            "THE HORNE BUILDING OWNERS CORP",
            "112-118 WEST 25TH LLC (c/o Extell Development Company)"],
   ans=["CONSENT", "TITLE"],
   note="⚠ THE AIR-RIGHTS SELLERS ARE RESIDENTIAL CO-OPS AND ONE IS A FOREST "
        "CITY RATNER ENTITY. A co-op selling its unused development rights is "
        "a board decision, not an owner decision - which is why every one of "
        "these needs a signed declaration from an 'Authorized Board Member "
        "and Shareholder' rather than a deed"),
 C("c2013-wellsfargo-waiver", "2013052101674006", "p003", "unresolved",
   text="WELLS FARGO BANK MINNESOTA, N.A., as Trustee for the Registered "
        "Holders of Credit Suisse First Boston Mortgage Securities Corp. "
        "Commercial Mortgage Pass-Through Certificates, Series 2000-C1, "
        "waived its right to execute the Declaration and subordinated its "
        "July 20, 1999 mortgage on Lot 21 to the Lot 21 ZLDA",
   eff="2013-05-17", subject="1008000021", ans=["CONSENT", "PRIORITY"],
   note="⚠ A CMBS TRUST HAD TO SIGN OFF ON THE AIR-RIGHTS SALE. The consent "
        "chain reaches certificateholders in a 2000-vintage securitisation "
        "for a lien recorded fourteen years earlier. UBS gave the parallel "
        "waiver on lot 49's own mortgage, signed by Henry Chung and Siho Ham"),
 C("c2013-enlargement-preconsent", "2013052101674007", "p005", "easement",
   text="paragraph 4: the Owner 'shall, by executing this Declaration be "
        "deemed AUTOMATICALLY AND WITHOUT ANY FURTHER ACTION ON ITS PART to "
        "have consented to and waived its right to execute an amended or "
        "replacement Declaration' if the Developer later adds parcels - and "
        "'shall, WITHIN TEN (10) BUSINESS DAYS after receiving a request "
        "therefore from Developer ... execute all documents and instruments "
        "required to confirm the incorporation of such Additional Parcels'",
   eff="2013-05-17", subject="1008000021", ans=["CONSENT", "ENVELOPE"],
   note="⚠ A VARIABLE OBLIGATION TRIGGERED BY NOTICE. This is how the "
        "assemblage kept growing without renegotiating with every prior "
        "seller: each co-op pre-consents to the next merger it knows nothing "
        "about. It is also why the 2019 nine-lot restructuring needed so few "
        "new signatures"),
 C("c2013-deed-vs-survey-early", "2013052101674007", "p021", "boundary_origin",
   text="Schedule A already prints both conventions in 2013: '82 feet 10 "
        "inches (deed) (82 feet 8 3/4 inches - survey)'",
   eff="2013-05-21", ans=["PARCEL"],
   note="⚠ CORROBORATES c2019-deed-vs-survey SIX YEARS EARLIER. The "
        "distinction was documented in 2013 and I still carried it as an "
        "unresolved defect through the 1990, 1998, 2003 and 2010 reads. The "
        "answer was sitting in a title certification the whole time"),
 C("c2013-signer-uncertain", "2013052101674003", "p008", "defect",
   text="⚠ TWO SIGNER NAMES I AM NOT ASSERTING. On the Lot 22 declaration the "
        "cursive signature block and the notary block do not clearly agree - "
        "the notary page, which is the more legible, reads 'personally "
        "appeared JONATHAN PRESSMAN'. On the Wells Fargo waiver the signature "
        "block appears to read 'Mindy G. Vit[to]' while the notary block "
        "reads 'Mindy Goldstein'",
   eff="2013-05-17", ans=["CONSENT", "IDENTIFY"],
   note="⚠ RECORDED AS UNCERTAIN ON PURPOSE. Jonathan Pressman definitely "
        "signed the LOT 21 declaration as 'Authorized Board Member and "
        "Shareholder' of 133 West 24th Street Corporation; whether the same "
        "person also signed for Brick Farms on lot 22 is not established. A "
        "name is a reach-ladder rung and a wrong one is worse than a blank"),
 C("c2011-servicing-chain", "2011112200806001", "p001", "cross_reference",
   text="the four 2011 documents are pure servicing transfers on lot 49's own "
        "mortgage and its assignment of rents: Irish Bank Resolution "
        "Corporation Limited to LSREF2 Clover Trust 2011 (CRFN 2011000425485 "
        "and ...488), then LSREF2 to Wells Fargo (CRFN 2011000425491 and "
        "...493), against CRFN 2007000336516 and 2007000336517",
   eff="2011-11-08", stated="2011-12-06", ans=["DEBT"],
   note="⚠ THE MORTGAGE AND THE RENTS ASSIGNMENT MOVE AS A PAIR, each needing "
        "its own instrument. Four documents, 29 pages, and ZERO substantive "
        "content - no floor area, no easement, no terms. ⚠ THE COST OF "
        "READING THEM WAS THE ONLY WAY TO LEARN THEY WERE EMPTY, which is an "
        "argument for doc-type triage before page-level reading"),

 C("c2013-plane-RESOLVED", "2013052101674002", "p010", "easement",
   subject="1008000020",
   text="RESOLVED BY LOOKING AT THE PAGE. Lot 20 heading, then: 'ALL that "
        "portion of the below described parcel LYING BELOW AN UPPER LIMITING "
        "PLANE drawn at an elevation of 130 feet above the datum level used "
        "by the topographical bureau, Borough of Manhattan, which is 2.78 "
        "feet above National Geodetic Survey vertical datum 1929 (United "
        "Coast and Geodetic Survey), mean sea level Sandy Hook, New Jersey.' "
        "LOT 49 TOOK THE DEVELOPMENT RIGHTS OF THE PORTION OF LOT 20 BELOW "
        "130 FEET",
   eff="2013-05-17", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   hext="lot 20 footprint: 125 ft on West 24th Street beginning 425 ft "
        "westerly of Sixth Avenue, 116 ft 5 in deep",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ I ASSERTED THE OPPOSITE. I wrote that lot 49 'owns air ABOVE an "
        "elevation'. It is BELOW. 130 feet is the UPPER limit of the volume "
        "conveyed, and the three instruments never disagreed - the 2019 "
        "Lower Parcel / Air Space split says the same thing from the other "
        "side, and the 2012 mortgage's bare '(lower limiting plane)' is a "
        "shorthand parenthetical in an exhibit. ⚠ AND THE CITE WAS WRONG: "
        "the agent reported p009, which is Lot 56's metes and bounds. The "
        "quote was accurate and the page was off by one - a discrepancy no "
        "amount of re-reading my notes could surface, because my notes were "
        "the thing in doubt. PROOF CROP proofs/9534509cfd4986d7.png, 16.7 KB, "
        "cut wide enough to include the 'Lot 20' heading so the plane cannot "
        "be misattributed to another lot"),

 C("c2013-lot22-price", "2013052101674004", "p001", "consideration",
   num=1_450_000, unit="USD", subject="1008000022",
   text="LOT 22 AIR RIGHTS: cover stamps 'NYC Real Property Transfer Tax: "
        "$38,062.50' and 'NYS Real Estate Transfer Tax: $5,800.00'. $5,800 / "
        "0.400% = $1,450,000, and $38,062.50 / 2.625% agrees within "
        "rounding. Against 10,726 sf that is about $135 PER BUILDABLE FOOT",
   eff="2013-05-17", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="⚠ SELLER IS BRICK FARMS COOPERATIVE LTD, a residential co-op. "
        "Bilateral - one co-op, one developer, one stamp pair, NOT bundled",
   supersedes="c2013-zldas-missing"),
 C("c2013-lot21-price", "2013052101674008", "p001", "consideration",
   num=1_340_500, unit="USD", subject="1008000021",
   text="LOT 21 AIR RIGHTS: 'NYC Real Property Transfer Tax: $35,181.56' and "
        "'NYS Real Estate Transfer Tax: $5,362.00'. $5,362 / 0.400% = "
        "$1,340,500. Against 10,722 sf that is about $125 PER BUILDABLE FOOT",
   eff="2013-05-17", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="seller 133 West 24th Street Corporation. ⚠ TWO COMPARABLE SALES TEN "
        "DAYS APART AT $135 AND $125 A FOOT - the first real air-rights comps "
        "on this block. The 2010 bundle across lots 53/55/56 was $93/sf"),
 C("c2013-lot20-internal", "2013080901116002", "p001", "defect",
   subject="1008000020",
   text="⚠ THE LOT 20 TRANSFER IS NOT A SALE. The cover names "
        "'GRANTOR/SELLER: 112-118 WEST 25TH LLC' and 'GRANTEE/BUYER: 112-118 "
        "WEST 25TH LLC' - the same entity - and Marc Kwestel signs BOTH "
        "signature blocks as Vice President. Both transfer taxes read $0.00",
   eff="2013-08-07", ans=["VALUE", "TITLE"],
   note="⚠ NO PRICE EXISTS TO FIND HERE. The real acquisition from an "
        "unrelated party - 351 E 61 REALTY LLC, the physical building owner - "
        "happened in the 2008 Lot 20 ZLDA at CRFN 2008000078652. A $0/$0 "
        "stamp pair is a POSITIVE FINDING: it identifies an internal "
        "reassignment rather than an unpriced sale"),
 C("c2013-plane-both-sides", "2013080901116002", "p036", "easement",
   subject="1008000020", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan",
   text="THE 130-FOOT PLANE, BOTH SIDES QUOTED OUT OF ONE DOCUMENT. p029, "
        "Airspace Parcel: 'ALL that portion ... LYING ABOVE a lower limiting "
        "plane drawn at an elevation of 130 feet'. p036, Lower Parcel: 'ALL "
        "that portion ... LYING BELOW an upper limiting plane drawn at an "
        "elevation of 130 feet'",
   eff="2013-08-07", ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ THERE WAS NEVER A CONTRADICTION. One plane, two parcels, each "
        "described from its own side - 'upper limiting' bounds the parcel "
        "below it, 'lower limiting' bounds the parcel above it. ⚠ AND LOT 49 "
        "GOT BOTH THINGS: the 14,703 sf of Excess Development Rights come "
        "from the LOWER parcel (Exhibit D p040) while the light/air/view "
        "easement is granted ABOVE the plane. You buy the floor area the "
        "lower owner cannot use AND the guarantee that nobody builds over it. "
        "My 'owns air above an elevation' was right about the easement and "
        "wrong about the rights"),
 C("c2012-lot23-plane", "2012122701550003", "p008", "easement",
   subject="1008000023", vfrom=155.24,
   vdatum="Datum Level = 2.75 ft above US Coast and Geodetic Survey, mean "
          "sea level Sandy Hook NJ",
   dur="perpetual",
   text="'Owner hereby grants to Developer a perpetual easement for LIGHT, "
        "AIR AND VIEW above the Lower Limiting Plane' - lot 23's plane sits "
        "at 155.24 FEET above Datum Level",
   eff="2012-12-19", ans=["ENCUMBRANCE", "ENVELOPE"],
   note="⚠ EVERY LOT HAS ITS OWN PLANE: lot 23 at 155.24 ft, lot 21 at 150 "
        "ft, lot 22 at 130 ft, lot 20 at 130 ft. Not one blanket height "
        "across the block. And lot 23's plane is VARIABLE - it can be RAISED "
        "if the owner acquires bonus rights and undertakes an Alteration"),
 C("c2013-datum-conflict", "2013080901116002", "p004", "defect",
   text="⚠ THE SAME INSTRUMENT GIVES THE DATUM TWO VALUES. Body section I.E "
        "at p004: 'which is 2.75 FEET above the United States Coast and "
        "Geodetic Survey Datum'. Exhibits at p029 and p036: 'which is 2.78 "
        "FEET above National Geodetic Survey vertical datum 1929'",
   eff="2013-08-07", ans=["PARCEL", "IDENTIFY"],
   note="⚠ 0.03 FEET AND A DIFFERENT DATUM STANDARD, INSIDE ONE RECORDED "
        "DOCUMENT. Immaterial at 130 feet, but it proves the body and the "
        "exhibits were drafted from different sources - and the exhibits are "
        "what a surveyor would actually use"),
 C("c-pagecount-rule", "2013052101674004", "p001", "unresolved",
   text="THE COVER-PAGE COUNTER RULE, measured on four documents: 'Document "
        "Page Count' is ALWAYS EXACTLY 2 LESS than 'PAGE 1 OF N', and PAGE 1 "
        "OF N always matches the files on disk. 55/53, 45/43, 41/39, 40/38",
   eff="2013-05-21", ev="derived", ans=["IDENTIFY"],
   note="⚠ THE 2-PAGE GAP IS THE COVER SHEET AND ITS CONTINUATION. Document "
        "Page Count describes the INSTRUMENT; PAGE 1 OF N describes the FILED "
        "SUBMISSION. ⚠ CONFLATING THEM IS EXACTLY WHAT PRODUCED FIVE FALSE "
        "TRUNCATION POSITIVES out of my own integrity check. Always store "
        "PAGE 1 OF N"),
 C("c-forms-drop-view", "2012122701550003", "p045", "defect",
   text="⚠ THE ANNEXED FORMS DROP 'VIEW', TWICE MORE. Exhibit G in both the "
        "lot 23 and the lot 22 agreements is an UNEXECUTED blank 'Form of "
        "Light and Air Easement' whose body says only 'unrestricted LIGHT AND "
        "AIR' - while the operative grant in each agreement's own section II "
        "says 'light, air AND VIEW'",
   eff="2012-12-19", ans=["ENCUMBRANCE", "IDENTIFY"],
   note="⚠ FOUR INSTANCES ACROSS FOUR AGREEMENTS - 2010, 2012, and both 2013 "
        "sets. THE OPERATIVE TEXT GRANTS VIEW AND EVERY ANNEXED FORM OMITS "
        "IT. A systematic drafting divergence, not a typo, and it decides "
        "whether a neighbour may build something that blocks the view without "
        "blocking light"),
 C("c2013-psa-unrecorded", "2013052101674004", "p012", "unresolved",
   text="the price MECHANISM is stated while the price is not: Developer may "
        "buy future upzoning rights 'AT THE SAME PRICE PER SQUARE FOOT PAID "
        "FOR THE ACQUISITION OF THE EXCESS DEVELOPMENT RIGHTS', confirming a "
        "per-square-foot price exists in an unrecorded Development Rights "
        "Purchase and Sale Agreement",
   eff="2013-05-17", ans=["VALUE"],
   note="⚠ THE DOCUMENT ADMITS THE NUMBER EXISTS AND DECLINES TO STATE IT. "
        "Every ZLDA references that PSA and none attaches it; the "
        "'Confirmation of Termination' exhibit that would name it is an "
        "unexecuted blank. THE TAX STAMP REMAINS THE ONLY WITNESS"),
 C("c2013-construction-easement", "2013080901116002", "p016", "easement",
   subject="1008000020",
   text="section XIII grants Developer a Construction Easement over the Lower "
        "Parcel 'for the purpose of providing construction protection ... and "
        "of facilitating the safe and timely construction of and necessary "
        "support for the Developer Building' - foundation support, "
        "underpinning, fencing, protective sheds and bridges over the "
        "neighbour's roof and facade, plus maintenance of all of it. Entry "
        "needs 5 days notice except in an Emergency Situation",
   eff="2013-08-07", ans=["ENCUMBRANCE", "PERMIT"],
   note="⚠ THE ONLY CONSTRUCTION EASEMENT IN THE SET - absent from the lot "
        "21, 22 and 23 agreements, which the agent read end to end. Lot 20 is "
        "the neighbour lot 49 actually had to build against"),
 C("c2023-owner-agreement", "2023102700753001", "p006", "cross_reference",
   text="THE MISSING CONVEYANCE IS NAMED. Recital F of the Second Amended and "
        "Restated Memorandum of Right of First Refusal: the parties execute "
        "it 'to document FRANCHISEE'S TRANSFER OF ITS FEE OWNERSHIP OF THE "
        "REAL PROPERTY TO OWNER', and Recital D names the instrument - 'an "
        "OWNER AGREEMENT dated October 16, 2023'",
   eff="2023-10-16", ans=["TITLE"],
   note="⚠ THIS CLOSES ONE OF THE TWO GENUINELY MISSING ACRIS FACTS. Lam Gen "
        "25 LLC transferred the fee to Chelsea 25 Hotel LLC by an Owner "
        "Agreement, not a deed - which is why no deed was ever found. ⚠ AND "
        "IT WAS HIDING IN A DOCUMENT TYPED 'SUNDRY MISCELLANEOUS'. The Owner "
        "Agreement itself is still not in the corpus"),
 C("c2025-maxsecured", "2025101700864004", "p025", "consolidation",
   num=85_000_000, unit="USD",
   text="section 15.02(c), all-caps in the original: 'THE MAXIMUM AMOUNT OF "
        "PRINCIPAL INDEBTEDNESS SECURED BY THIS MORTGAGE ... IS EIGHTY-FIVE "
        "MILLION AND NO/100 DOLLARS ($85,000,000.00)' - against a "
        "$123,000,000 consolidated lien at section 15.02(g)",
   eff="2025-10-16", ans=["DEBT"],
   note="⚠ THE $85,000,000 I HAD BEEN RECONSTRUCTING IS STATED OUTRIGHT, "
        "under RPL 254. Three figures coexist and all are true of different "
        "things: $123,000,000 consolidated lien, $120,000,000 unpaid balance "
        "of the existing mortgages, $85,000,000 MAXIMUM ACTUALLY SECURED. "
        "Words and numerals agree at every occurrence"),
 C("c2020-collateral", "2020081400407001", "p021", "easement",
   text="the 2020 assignment of rents is COLLATERAL, not absolute: 'The "
        "Mortgagee hereby WAIVES THE RIGHT TO ENTER upon the Property for the "
        "purpose of collecting the Rents, and the Mortgagor SHALL HAVE A "
        "LICENSE to collect and receive the Rents, until an Event of Default "
        "shall have occurred'",
   eff="2020-08-05", ans=["INCOME", "ENCUMBRANCE"],
   note="⚠ CONFIRMS THE STRUCTURAL DIFFERENCE I FLAGGED. The 2025 Deutsche "
        "Bank assignment says 'present, absolute assignment ... and not an "
        "assignment for additional security only'; this one waives entry "
        "until default. Absolute puts the rents outside the borrower's estate "
        "from day one; collateral does not"),
 C("c2018-splitter-severs", "2018113000347001", "p011", "consolidation",
   num=25_500_000, unit="USD",
   text="Schedule B: 'The lien of the mortgages as consolidated shall remain "
        "a lien in the principal amount of $25,500,000.00 made by Lam Gen 25 "
        "LLC ... (Block: 800, Lot: 49) ... as Parcel 1' and a 'Split "
        "Replacement Mortgage ... in the principal amount of $22,500,000.00 "
        "made by LG Chelsea LLC ... (Block: 800, Lot: 50) ... as Parcel 2'",
   eff="2018-11-19", ans=["DEBT", "PARCEL"],
   note="⚠ A FULL SEVERANCE, NOT AN ALLOCATION. Lot 49 keeps the ORIGINAL "
        "mortgage with Lam Gen 25 still as mortgagor; lot 50 gets a BRAND NEW "
        "instrument with LG Chelsea substituted. No cross-liability either "
        "way. Independently corroborated by the 2025 schedule item 6C: "
        "'Splits Mortgages into two liens: $22,500,000.00, not affecting "
        "premises and $25,500,000.00, affecting premises'"),
 C("c2020-hotel-manager", "2020081400407001", "p019", "party_role",
   text="'income statements for the operation of the RENAISSANCE NEW YORK "
        "CHELSEA HOTEL (the Hotel) ... managed by REAL HOSPITALITY GROUP, LLC "
        "(the Hotel Manager) ... Management Agreement dated MARCH 1, 2018'",
   eff="2018-03-01", stated="2020-08-14",
   parties=["REAL HOSPITALITY GROUP, LLC (hotel manager)",
            "MARRIOTT INTERNATIONAL, INC. (franchisor)"],
   ans=["TENANCY", "PERMIT"],
   note="⚠ THE OPERATOR, NAMED AT LAST, AND IT IS NOT MARRIOTT. Marriott is "
        "the FRANCHISOR under a July 14, 2014 agreement; Real Hospitality "
        "Group actually runs the building under a separate March 2018 "
        "management agreement. Two different relationships that a franchise "
        "flag on a building hides"),
 C("c2026-foreign-docs", "2026052800492001", "p001", "defect",
   text="⚠ TWO DOCUMENTS IN THIS PARCEL'S FOLDER ARE NOT THIS PARCEL. "
        "2026052800492001 is a POWER OF ATTORNEY covering 'BROOKLYN 7027 54 "
        "Entire Lot 3735 OCEANIC AVENUE' between EKATERINA and OLGA "
        "YUMAKAEVA. 2026062301264001 is a POWER OF ATTORNEY covering "
        "'BROOKLYN 2350 1016 Entire Lot 214 85 NORTH 3 STREET' between ELI "
        "and SABRINA WACHT",
   eff="2026-06-01", ans=["IDENTIFY"],
   note="⚠ FOREIGN DOCUMENTS IN THE PARCEL FOLDER, AND I REPORTED THEM TO THE "
        "USER AS 'NEW 2026 ACTIVITY ON THIS PARCEL'. Neither mentions Block "
        "800, lot 49, or any party in this chain. ⚠ NO CHECK I BUILT ASKS "
        "'IS THIS DOCUMENT EVEN THIS PARCEL'S?' - every one asks whether a "
        "document is complete and read. The cover page prints its own "
        "borough, block and lot; one page gates the entire pipeline. Both "
        "folders are also short, 3 of 9 and 1 of 10"),
 C("c2023-folder-mismatch", "2023102700777001", "p003", "defect",
   text="⚠ A FOLDER HOLDING A DIFFERENT DOCUMENT'S BODY. Pages p001-p002 are "
        "the cover for 2023102700777001 ('SUNDRY AGREEMENT', Document Page "
        "Count 11). Pages p003-p013 are the complete cover AND body of "
        "2023102700753001 ('SUNDRY MISCELLANEOUS', its own PAGE 1 OF 11) - a "
        "different document ID. The actual body of 777001 was never fetched",
   eff="2023-10-27", ans=["IDENTIFY"],
   note="⚠ AND A PAGE-COUNT CHECK PASSES: 13 files against 13 claimed. The "
        "document is still wrong. Counting pages cannot detect a substituted "
        "body - only reading the document ID printed on each cover can"),
 # ---- 2014 — the NAME rung ----------------------------------------------
 C("c2014-mtge", "2014112601161004", "p001", "mortgage", num=7_500_000, unit="USD",
   eff="2014-11-25", stated="2014-12-02", ans=["ENCUMBER", "CAPITAL"]),
 C("c2014-person", "2014112601161004", "p007", "person",
   text="JEFFREY LAM, appearing personally before notary Helen Eng, Queens County",
   eff="2014-11-25", ans=["PARTY"],
   note="the deed gives an entity; the mortgage jurat gives the human"),
 C("c2014-lot20", "2014112601161004", "p008", "cross_reference",
   text="Lot 20 ZLDA recorded 2008-02-26, CRFN 2008000078652",
   subject="1008000020", eff="2008-02-26", stated="2014-11-25",
   ans=["ENVELOPE", "PARCEL"],
   note="THE ASSEMBLAGE'S FIRST INSTRUMENT — two years before Sabetfard, and "
        "indexed only against lot 20. Effective 2008, learned of in 2014"),


 # ---- the debt chain, from Exhibit A of the 2014 assignment --------------
 C("c1990-lender-b", "2014112601161003", "p006", "party_role",
   text="APPLE BANK FOR SAVINGS — the original 1990 mortgagee, lending "
        "$1,000,000 to 112 West 25 Company",
   eff="1990-07-05", stated="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ the root lender, named at last. Mortgage tax paid $22,500. Apple "
        "Bank assigned to Queens County Savings Bank on 1999-06-29"),
 C("c1999-cema", "2014112601161003", "p006", "consolidation",
   num=1_025_000, unit="USD",
   text="the 1990 and 1998 mortgages consolidated into ONE lien",
   eff="1999-06-29", stated="2014-11-25", ans=["CAPITAL"],
   note="Reel 2903 Pg 1311 — the first consolidation on this parcel"),
 C("c2007-lender", "2014112601161003", "p006", "party_role",
   text="ANGLO IRISH BANK CORPORATION PLC — the 2007 acquisition lender",
   eff="2007-06-29", stated="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ gap mortgage $38,311,287.86, tax paid $1,072,716.41, consolidated "
        "to $39,229,334. Anglo Irish was nationalised in 2009 and its loan "
        "book liquidated — which is why this loan changes hands six times"),
 C("c2011-workout", "2014112601161003", "p006", "party_role",
   text="IRISH BANK RESOLUTION CORP (f/k/a Anglo Irish) assigns to LSREF2 "
        "CLOVER TRUST 2011 — a Lone Star vehicle",
   eff="2011-12-06", stated="2014-11-25", ans=["CAPITAL", "DISTRESS"],
   note="⚠ THE DISTRESSED WORKOUT I MISSED ENTIRELY. My ledger called the 2011 "
        "batch 'servicing — no money moves; the lender changes hands'. True, "
        "and it misses that this is the Irish banking collapse reaching a "
        "Chelsea development site. Then Clover -> Wells Fargo (2011) -> Clover "
        "again (2012) -> UBS (2012) -> Goldman (2013) -> Shanghai (2014). "
        "SIX HOLDERS IN SEVEN YEARS"),
 C("c2014-exit", "2014112601161003", "p004", "party_role",
   text="GOLDMAN SACHS BANK USA assigns its whole position to SHANGHAI "
        "COMMERCIAL BANK LTD, NEW YORK BRANCH, without recourse and without "
        "representation or warranty",
   eff="2014-11-25", ans=["CAPITAL", "PARTY"],
   note="⚠ CORRECTS MY LENDER TIMELINE. Shanghai Commercial arrived in 2014, "
        "not 2020 — so it was the lender through the 2015 construction stack "
        "and the 2020 facility too. Goldman signed its exit documents on "
        "2014-11-18 and they sat in escrow a week"),
 C("c2014-position", "2014112601161003", "p008", "consolidation",
   num=40_500_000, unit="USD",
   text="the assigned position, as presently reduced",
   eff="2014-11-25", ans=["CAPITAL"]),
 C("c2014-gap", "2014112601161004", "p002", "mortgage", num=7_500_000,
   unit="USD",
   text="⚠ THE INSTRUMENT CALLS ITSELF A GAP MORTGAGE — ACRIS types it MTGE",
   eff="2014-11-25", ans=["CAPITAL", "ENCUMBER"],
   note="taxed on its FULL FACE, $210,000 = 2.800%, no exemption claimed and "
        "the cross-reference block left blank. $40.5M assigned + $7.5M gap = "
        "the $48,000,000 consolidated lien. THE PATTERN REPEATS: 2007 gap "
        "$38.3M, 2012 gap $1,607,226, 2013 gap $1.5M, 2014 gap $7.5M — every "
        "refinancing on this parcel is gap-plus-consolidation, which is how "
        "$514M of face conceals $28M of money"),
 C("c2014-demand", "2014112601161004", "p005", "unresolved",
   text="the gap mortgage accelerates ON DEMAND — 'the whole of the principal "
        "sum shall become due upon the demand of the Mortgagee' — with NO "
        "event-of-default list, no Lien Law §13 trust covenant, no due-on-sale, "
        "no junior-debt bar, no escrows and no reporting",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ not a lax lender — a SHORT-FORM statutory gap mortgage. The "
        "protective machinery lives in the $48,000,000 Consolidated, Amended "
        "and Restated Mortgage recorded the same day. Any covenant analysis "
        "stopping at the gap mortgage understates the lender's position badly"),

 # ---- Marriott ----------------------------------------------------------
 C("c2014-marriott", "2014112601161002", "p003", "party_role",
   text="MARRIOTT INTERNATIONAL INC holds a recorded RIGHT OF FIRST REFUSAL to "
        "purchase the property, under a Franchise Agreement dated 2014-07-14",
   eff="2014-11-25", ans=["TITLE", "PARTY", "OCCUPY"],
   note="⚠ A LIVE CONSTRAINT ON ANY SALE, and it sat in a document ACRIS types "
        "'SUNDRY AGREEMENT'. Memorandum recorded 2014-08-13 CRFN 2014000269549, "
        "amended 2016 CRFN 2016000203717, second amended and restated 2023"),
 C("c2014-rofr-sub", "2014112601161002", "p003", "unresolved",
   text="Marriott's ROFR is subordinate to the lender's mortgage ONLY 'if and "
        "for so long as (i) the Mortgage remains validly recorded and in full "
        "force and effect; and (ii) the Bank is not a Competitor or Affiliate "
        "of a Competitor'",
   eff="2014-11-25", ans=["TITLE", "CAPITAL"],
   note="⚠ CONDITIONAL SUBORDINATION. If the loan is ever sold to a hotel "
        "competitor, Marriott's ROFR springs back AHEAD of the lien. Neither "
        "'Competitor' nor 'Affiliate' is defined here — both are pushed to the "
        "UNRECORDED Franchise Agreement"),
 C("c2014-hotel", "2014112601161002", "p003", "property_type",
   text="'any mortgage securing construction and project financing between "
        "Franchisee and the Bank for the future construction of a HOTEL to be "
        "located on the Property'",
   eff="2014-11-25", ans=["ASBUILT", "PERMIT"],
   note="⚠ THE EARLIEST DOCUMENTARY STATEMENT THAT A HOTEL WAS THE PROJECT — "
        "November 2014, ten months before the construction loan. ACRIS never "
        "records that a building exists, but it records what one is FOR"),

 # ---- the 2023 unwind ---------------------------------------------------
 C("c2023-facilities", "2023110100486002", "p002", "cross_reference",
   text="the three 2023 terminations retire rent assignments securing FOUR "
        "named Shanghai Commercial facilities: the Land Loan (2014, CRFN "
        "2014000397949), the Land, Building and Project Loans (2015, CRFN "
        "2015000330175), and the Bridge Loan (2020, CRFN 2020000234175)",
   eff="2023-10-16", ans=["CAPITAL"],
   note="⚠ confirms the 2015 stack was genuinely a BUILDING and PROJECT loan, "
        "and that the 2020 money was a BRIDGE — both from the same lender"),
 C("c2023-rerecord", "2023102700777001", "p003", "defect",
   text="this instrument is a RE-RECORDING of 2023102700753001, whose own "
        "cover pages are bound inside it as pages 3-4. The earlier filing "
        "carries NO borough/block/lot on its cover, so it may not index to "
        "Block 800 Lot 49 at all",
   eff="2023-10-31", ans=["IDENTIFY"],
   note="⚠ a document inventory counting both will DOUBLE-COUNT the Marriott "
        "memorandum"),

 # ---- ⚠ THE DRIFT: the same tax payment, three different figures ---------
 C("c-taxcredit-drift", "2014112601161005", "p029", "defect",
   text="⚠ FOUR INSTRUMENTS STATE THE TAX PAID ON THE SAME 1990 MORTGAGE "
        "AND TWO OF THEM ARE WRONG. The 1990 "
        "instrument itself records $22,500.00 (margin note p001 AND machine "
        "stamp p026). The 2003 section-255 affidavit claims $27,500.00. The "
        "2014 section-255 affidavit claims $28,000.00",
   eff="2014-12-02", ev="derived", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ EACH FIGURE IS THE BASIS OF AN EXEMPTION FROM PAYING TAX AGAIN. "
        "The 1998 mortgage drifts too: the instrument endorsement says "
        "$4,528.00 (components summing exactly), the 2003 affidavit says "
        "$4,527.56, the 2014 affidavit says $4,641.20. OBSERVATION, NOT "
        "PROOF OF INTENT: $28,000 is exactly 2.800% of $1,000,000 - the 2014 "
        "commercial rate, not the 1990 one - and $27,500 is exactly 2.750%. "
        "Both later figures look RECOMPUTED at the then-current rate rather "
        "than READ off the original instrument. The $4,641.20 does not fit "
        "that pattern and is unexplained. ALL FIGURES ARE HANDWRITTEN. "
        "⚠ NO SINGLE DOCUMENT REVEALS THIS - it only appears by crossing the "
        "microfilm read against the 2014 read"),

 # ---- 2014: the Shanghai Commercial arrival ------------------------------
 C("c2014-split", "2014112601161005", "p004", "consolidation",
   num=7_500_000, unit="USD",
   text="the $48,000,000 is $40,500,000 EXISTING plus $7,500,000 NEW - and "
        "both figures appear ONLY IN HANDWRITING. p004 margin: 'New money # "
        "7,500,000 is forwarded to me.' p022 beside Schedule items 5A and 5B: "
        "'Current unpaid principal $40,500,000.00'",
   eff="2014-11-25", stated="2014-12-02", ans=["CAPITAL"],
   note="⚠ THE TYPED TEXT SAYS $48,000,000.00 EVERYWHERE AND WOULD READ AS "
        "$48M OF NEW LENDING TO ANYONE WHO SKIPS THE MARGINALIA. The tax "
        "record proves the split: taxable $0.00 / exemption 255 / MRT $0.00 "
        "on this instrument, with $210,000 (= 2.800% x $7,500,000) paid on "
        "the companion gap mortgage 2014112601161004"),
 C("c2014-nineteen-million", "2014112601161005", "p014", "defect",
   text="⚠ 'THE MAXIMUM AMOUNT OF PRINCIPAL INDEBTEDNESS SECURED BY THIS "
        "MORTGAGE ... IS NINETEEN MILLION AND 00/100 DOLLARS "
        "($48,000,000.00)' - the words and the figures disagree by "
        "$29,000,000, and the SAME defect is recorded a second time in the "
        "companion assignment of rents at 2014112601161006 p003",
   eff="2014-12-02", ans=["CAPITAL"],
   note="⚠ a template carry-over from an unrelated $19M deal that survived "
        "two rounds of review and got recorded TWICE. Under NY construction "
        "the WRITTEN WORDS normally prevail over figures - so as recorded, "
        "the maximum-principal clause of the operative lien is internally "
        "contradictory on $29,000,000. Not repaired here; recorded as a "
        "defect. Compare the 1998 CEMA's own words/numerals conflict "
        "(c1998-cema-typo) - the same class of error, sixteen years apart"),
 C("c2014-lender", "2014112601161005", "p001", "party_role",
   text="the 2014 lender is SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH - "
        "'a banking corporation organized under laws of the Hong Kong Special "
        "Administrative Region of the People's Republic of China'. Goldman "
        "Sachs Bank USA is the OUTGOING holder, assigning out at Schedule "
        "item 5B",
   eff="2014-11-25", stated="2014-12-02",
   parties=["SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH (mortgagee)",
            "LAM GEN 25 LLC (mortgagor)",
            "GOLDMAN SACHS BANK USA (outgoing holder)"],
   ans=["CAPITAL", "PARTY"],
   note="any debt-stack read still showing Goldman on this lot after "
        "2014-12-02 is stale. Shanghai Commercial holds it for nine years, "
        "until the 2023 MetLife assignment"),
 C("c2014-loanagt-controls", "2014112601161005", "p014", "unresolved",
   text="section 8.07: 'Wherever there is any conflict or inconsistency "
        "between any terms or provisions of this Mortgage and the Loan "
        "Agreement, the terms and provisions of the Loan Agreement shall "
        "control' - and Article 1 sends every undefined term there too",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ NOTHING ECONOMIC IS ON THE RECORD. No rate, no maturity, no "
        "first-lien representation, NO REPRESENTATIONS ARTICLE AT ALL, no "
        "no-default representation, no spreader. This mortgage is a LIEN "
        "NOTICE, NOT A TERMS DOCUMENT. Section 8.04 refers to 'INTEREST ... "
        "AT THE RATES SET FORTH IN THE LOAN AGREEMENT' without stating them. "
        "The unbroken line runs 1990 -> 2007 -> 2014 -> 2023 -> 2025"),
 C("c2014-devrights-mortgaged", "2014112601161005", "p005", "easement",
   text="section 3.01(c) mortgages 'air rights and development rights' along "
        "with the fee - the transferred floor area is itself collateral",
   eff="2014-11-25", ans=["ENVELOPE", "CAPITAL"],
   note="⚠ THE LOT'S DEVELOPMENT RIGHTS ARE BORROWED AND THEN PLEDGED. "
        "Exhibit A ties five separate zoning-lot development and easement "
        "agreements into this parcel - Tax Lot 20 (CRFN 2008000078652), Lot "
        "21 (2013000241549), Lot 22 (2013000241545), Lot 23 (2013000007933), "
        "and Lots 53/55/56 (2010000384312). Any buildable-SF read on this lot "
        "must clear all five AND this lien"),
 C("c2014-alr-absolute", "2014112601161006", "p004", "easement",
   text="'IT IS THE INTENTION OF ASSIGNOR AND ASSIGNEE THAT THE FOREGOING "
        "ASSIGNMENT ESTABLISH A PRESENT AND ABSOLUTE TRANSFER ... This "
        "Agreement is an absolute assignment to Assignee and not an "
        "assignment as security' - with a licence back that revokes "
        "automatically on default, 'without the necessity of the appointment "
        "of a receiver and whether or not Assignee has taken possession'",
   eff="2014-11-25", ans=["INCOME", "ENCUMBRANCE"],
   note="the assignment reaches security deposits, lease TERMINATION fees, "
        "loss-of-rents insurance proceeds, and 'all claims and sums paid as "
        "damages ... with respect to a rejection of a Lease in bankruptcy'. "
        "⚠ CONDEMNATION PROCEEDS ARE NOT IN THE GRANT - they appear only at "
        "p010 section 15 as something whose collection does not waive a "
        "default. Condemnation is carried by the mortgage, not by this"),
 C("c2014-lease-lock", "2014112601161006", "p008", "easement",
   text="section 11: without prior written consent the borrower shall not "
        "(a) enter into or extend any Lease, (b) cancel, terminate or accept "
        "surrender, (c) reduce rent or accept rent more than one month in "
        "advance, (d) materially modify, or (e) consent to assignment or "
        "subletting unless the tenant remains liable - and any such act 'at "
        "the option of Assignee ... shall be of no force or effect and shall "
        "constitute an Event of Default'",
   eff="2014-11-25", ans=["ENCUMBRANCE", "TENANCY"],
   note="⚠ ONE GAP: 'subordinate' is NOT among the prohibitions, and the "
        "agent found no subordination bar anywhere in p003-p016. The 2007 "
        "CEMA had an absolute ground-lease subordination bar; this one does "
        "not"),
 C("c2014-note-lien-gap", "2014112601161005", "p023", "defect",
   text="⚠ Exhibit C item (4) states a $67,258,543 consolidated NOTE against "
        "a same-day $39,229,334 consolidated MORTGAGE - the 2007 note/lien "
        "gap, carried forward on the face of a 2014 instrument and still "
        "unreconciled seven years later",
   eff="2014-11-25", ans=["CAPITAL"],
   note="INDEPENDENT CORROBORATION of c2007-facility, found by a different "
        "agent in a different document seven years downstream. Also in the "
        "same exhibit: the 2007 gap note is $38,311,287.14 in Exhibit C but "
        "$38,311,287.86 in Exhibit B - a 72-cent disagreement inside one "
        "instrument"),
 C("c2014-onesided", "2014112601161006", "p016", "defect",
   text="the assignment of leases and rents is EXECUTED ONE-SIDED - only the "
        "assignor signs. There is no assignee signature block anywhere in "
        "p003 to p016, notwithstanding section 31 contemplating signature 'by "
        "or on behalf of each of the parties hereto'",
   eff="2014-11-25", ans=["IDENTIFY"],
   note="also: same signer, same day, same room, TWO NOTARIES - Suchuan "
        "Wangyu took the mortgage acknowledgment, Helen Eng took the "
        "assignment and both section 255 affidavits. Wangyu's commission "
        "expired 2014-12-06, eleven days after the acknowledgment and four "
        "days after recording - valid, but the tightest date in the file"),
 C("c2014-alr-termination", "2014112601161006", "p012", "easement",
   text="section 20: the assignment 'shall be released and terminated as, "
        "when and to the extent the Security Instrument is released and "
        "discharged WITHOUT THE NEED TO EXECUTE AND DELIVER FURTHER "
        "INSTRUMENTS' - a standalone recorded satisfaction is optional and "
        "borrower-funded",
   eff="2014-11-25", ans=["INCOME", "IDENTIFY"],
   note="⚠ TERMINATION IS AUTOMATIC AND DERIVATIVE, SO IT LEAVES NO RECORD. "
        "A reader watching for a recorded satisfaction of the assignment will "
        "never see one. And 'indefeasibly paid in full' means a later "
        "preference clawback reanimates the obligation - the indemnity at "
        "section 28 and expenses at section 27 are not carved out of the "
        "release"),

 # ---- ⚠ the correction to my own drift claim -----------------------------
 C("c2013-taxcredit-correct", "2013081200922004", "p020", "tax_paid",
   num=22_500.00, unit="USD",
   text="⚠ THE 2013 SCHEDULE HAS THE PRIOR-TAX FIGURES RIGHT. It states the "
        "1990 mortgage tax as $22,500.00 and the 1998 as $4,528.00 - both "
        "matching the original instruments exactly - alongside "
        "$1,072,716.41 (2007) and $45,001.60 (2012)",
   eff="2013-08-28", ans=["CAPITAL"],
   note="⚠ THIS CORRECTS c-taxcredit-drift, WHICH I RECORDED AN HOUR AGO "
        "SAYING THE FIGURES DRIFT 'EACH HIGHER THAN THE LAST'. THEY DO NOT. "
        "The sequence is $22,500 (1990 instrument) -> $27,500 (2003 "
        "affidavit, WRONG) -> $22,500 (2013 schedule, RIGHT) -> $28,000 "
        "(2014 affidavit, WRONG). It is not a drift and not a trend - it is "
        "two wrong affidavits with a correct one between them. My "
        "recomputed-at-current-rate hypothesis survives for 2003 and 2014 "
        "but explains nothing about why 2013 got it right. I found this by "
        "crossing a THIRD agent against the two that produced the original "
        "claim"),

 # ---- the structural rule: why a termination AND an assignment ----------
 C("c-tlr-assignment-grammar", "2014112601161001", "p003", "unresolved",
   text="WHY EVERY REFINANCING HERE HAS BOTH A TERMINATION AND AN "
        "ASSIGNMENT: a MORTGAGE LIEN can be assigned forward and preserved, "
        "which is what avoids the tax. AN ASSIGNMENT OF LEASES AND RENTS "
        "CANNOT BE - it is a present, absolute transfer to a NAMED assignee, "
        "with no mechanism to slide a different assignee into it. So the "
        "outgoing lender must terminate its AL&R and the incoming lender "
        "must take a fresh one, same day",
   eff="2014-12-02", ev="derived", ans=["CAPITAL", "INCOME"],
   note="⚠ A REUSABLE DECODE RULE, not a fact about this lot. It predicts the "
        "shape of every lender change in the corpus: ASST (tax $0) + small "
        "GAP MTGE (taxed on new money only) + CEMA (exemption 255, tax $0) + "
        "TL&R (kills the old rents assignment) + new AL&R (exemption 255). "
        "Both 2013 and 2014 follow it exactly. In 2014 the OUTGOING lender "
        "is Goldman - the same party that was the INCOMING lender in 2013"),
 C("c2013-275-sworn", "2013081200922001", "p012", "unresolved",
   text="THE BORROWER CERTIFIED THE TAKEOUT STRUCTURE UNDER OATH. The RPL "
        "section 275 statement has exactly one box ticked: '[X] b. Assignment "
        "of the existing mortgage(s) to a new lender in a transaction in "
        "which the assigned mortgage(s) will be consolidated with a new "
        "mortgage securing additional monies advanced by the new lender.' "
        "The alternative box - 'no new monies will be advanced' - is unticked",
   eff="2013-08-07", stated="2013-08-28", ans=["CAPITAL"],
   note="⚠ EVIDENCE, NOT INFERENCE. The tax-efficient structure I derived "
        "from the pattern of stamps is stated on the face of the record and "
        "sworn to by Jeffrey Wai Hung Lam as Manager"),
 C("c-275-posture-flip", "2014112601161003", "p004", "defect",
   text="⚠ THE SAME ECONOMIC MOVE, TWO DIFFERENT COMPLIANCE POSTURES. The "
        "2013 assignment FILED a section 275 statement under oath. The 2014 "
        "assignment DISCLAIMS it: 'THIS ASSIGNMENT is not subject to the "
        "requirements of Section 275 of the Real Property Tax Law because it "
        "is an assignment within the secondary mortgage market'",
   eff="2014-12-02", ans=["CAPITAL", "IDENTIFY"],
   note="fifteen months apart, identical transaction shape. Also note the "
        "2014 text says 'Real Property TAX Law' - section 275 is in the Real "
        "Property Law"),

 # ---- ⚠ the hotel was planned before the construction loan --------------
 C("c2014-marriott-hotel", "2014112601161002", "p003", "unresolved",
   text="⚠ THE HOTEL PLAN IS DATED NOVEMBER 2014, TEN MONTHS BEFORE THE "
        "CONSTRUCTION LOAN. Marriott's subordination defines the Bank's "
        "mortgage to reach 'any mortgage or security deed securing "
        "construction and project financing between Franchisee and the Bank "
        "FOR THE FUTURE CONSTRUCTION OF A HOTEL TO BE LOCATED ON THE "
        "PROPERTY'",
   eff="2014-11-25", stated="2014-12-02", ans=["PERMIT", "CAPITAL"],
   note="⚠ THIS DOCUMENT TELLS YOU WHAT THE MONEY IS FOR - a Marriott-"
        "franchised hotel, with the 2015 Building Loan and Project Loan "
        "already contemplated in the November 2014 subordination. The "
        "underlying Memorandum of Right of First Refusal is dated 2014-07-14, "
        "recorded 2014-08-13, Document ID 2014080700619001. ⚠ An instrument "
        "ACRIS types as 'SAGE / SUNDRY AGREEMENT' is the single best evidence "
        "of development intent in the whole record"),
 C("c2014-marriott-condition", "2014112601161002", "p003", "easement",
   text="Marriott's right of first refusal is subordinate to the mortgage "
        "'if and for so long as: (i) the Mortgage remains validly recorded "
        "and in full force and effect; and (ii) the Bank is not a Competitor "
        "or Affiliate of a Competitor' - and the subordination 'relates only "
        "to Marriott's real estate rights ... is not a subordination of the "
        "Franchise Agreement'",
   eff="2014-11-25", ans=["ENCUMBRANCE", "TITLE"],
   note="⚠ A CONDITIONAL SUBORDINATION THAT CAN SWITCH OFF. If the lien is "
        "ever assigned to a hotel competitor, Marriott's ROFR climbs back "
        "ahead of the mortgage. Every subsequent assignment in this chain - "
        "MetLife 2023, Deutsche Bank 2025 - is silently tested against that "
        "condition"),

 # ---- the chain is 23 years and 11 holders -------------------------------
 C("c-chain-eleven", "2013081200922001", "p005", "cross_reference",
   text="ONE UNBROKEN LIEN, ELEVEN HOLDERS, 1990 TO 2014: Apple Bank For "
        "Savings -> Queens County Savings Bank -> New York Community Bank -> "
        "Anglo Irish Bank Corporation PLC -> Irish Bank Resolution Corp -> "
        "LSREF2 Clover Trust 2011 -> Wells Fargo Bank NA -> LSREF2 Clover "
        "Trust 2011 (back again) -> UBS Real Estate Securities -> Goldman "
        "Sachs Bank USA -> Shanghai Commercial Bank",
   eff="2013-08-07", ans=["CAPITAL", "PARTY"],
   note="⚠ THE ROOT IS REEL 1707 PAGE 1285, THE 1990 APPLE BANK MORTGAGE - "
        "not the 1999 entries, which are 1998 instruments recorded late. Both "
        "the 2013 and the 2014 cover pages carry that 1990 reel/page as their "
        "PRIMARY cross-reference. Continue the chain past this batch and it "
        "reaches MetLife (2023) and Deutsche Bank (2025): THIRTEEN HOLDERS, "
        "THIRTY-FIVE YEARS, ONE LIEN"),
 C("c2013-lsref-roundtrip", "2013081200922001", "p006", "defect",
   text="⚠ LSREF2 CLOVER TRUST 2011 APPEARS TWICE IN THE CHAIN. It assigns to "
        "Wells Fargo on 2011-11-08 (CRFN 2011000425491) and takes it back "
        "from Wells Fargo on 2012-10-05 (CRFN 2012000427965)",
   eff="2012-10-05", ans=["CAPITAL", "PARTY"],
   note="a holder-count that treats parties as unique understates the "
        "assignment count. Compare the 1971 deed round trip - the same shape, "
        "forty years earlier, on title rather than debt"),

 # ---- defects in the supporting documents --------------------------------
 C("c2013-tlr-indexdefect", "2013081200922005", "p001", "defect",
   text="⚠ THE COVER PAGE NAMES THE WRONG PARTY. p001 indexes 'PARTY TWO: "
        "112-229 WEST 28TH LLC'; the instrument itself at p003 names "
        "'112-118 WEST 25TH LLC'",
   eff="2013-08-28", ans=["IDENTIFY"],
   note="⚠ the cover page controls for indexing, so a NAME-KEYED search for "
        "this termination against the correct borrower MISSES IT. Same class "
        "as the 2018 splitter indexed to lot 50 - the operative instrument "
        "hides behind a bad cover page"),
 C("c2014-tlr-drafting", "2014112601161001", "p003", "defect",
   text="the operative sentence terminates 'that certain TERMINATION OF "
        "Assignment of Leases and Rents' - the word 'Termination' sits where "
        "'Assignment' belongs, so as written it terminates the wrong "
        "instrument type",
   eff="2014-12-02", ans=["IDENTIFY", "INCOME"],
   note="intent is recoverable because the identifying CRFN 2013000344224 "
        "that follows is unambiguous. Recorded as a defect, not repaired"),
 C("c2014-gap-thin", "2014112601161004", "p005", "unresolved",
   text="⚠ THE 2014 GAP MORTGAGE ACCELERATES ON DEMAND WITH NO TRIGGER AT "
        "ALL: 'That the whole of the principal sum evidenced by said note "
        "shall become due upon the demand of the Mortgagee.' Seven paragraphs "
        "total, against twenty-two in the 2013 Goldman gap",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ ABSENT from the 2014 gap and PRESENT in the 2013 one: alteration "
        "and demolition consent, the bar on rent more than one month in "
        "advance, the Lien Law section 13 trust-fund covenant, junior-"
        "financing and transfer bars, financial reporting. All of it moved "
        "into the unrecorded Loan Agreement between 2013 and 2014. THE RECORD "
        "GOT THINNER AS THE DEBT GOT BIGGER"),
 C("c2013-devrights-collateral", "2013081200922001", "p003", "easement",
   text="the 2013 assignment reaches the mortgages 'affecting (i) the real "
        "property as described on Exhibit B-1 ... AND (ii) THE DEVELOPMENT "
        "RIGHTS ATTRIBUTABLE TO THE REAL PROPERTY AS DESCRIBED ON EXHIBIT "
        "B-2' - development rights are itemised as SEPARATE collateral, in "
        "their own exhibit",
   eff="2013-08-07", ans=["ENVELOPE", "CAPITAL"],
   note="Exhibit B-1/B-2 at p007-p011 records the light-and-air easement over "
        "Tax Lot 53 under CRFN 2010000384312 and covers Block 800 Lot 23. The "
        "purchased air rights are pledged from 2013 onward"),
 C("c2013-termination-fees", "2013081200922004", "p006", "easement",
   text="section 5(g): 'any termination fees payable under a Lease for the "
        "early termination or surrender thereof shall be paid JOINTLY to the "
        "Assignor and the Lender' - and section 5(m) bars letting any Lease "
        "become subordinate to any lien other than the lender's",
   eff="2013-08-07", ans=["INCOME", "ENCUMBRANCE"],
   note="the 2013 Goldman AL&R bars subordination of leases; the 2014 "
        "Shanghai AL&R does NOT (see c2014-lease-lock). A covenant present in "
        "one generation and absent in the next"),
 # ---- 2015 --------------------------------------------------------------
 C("c2015-confirm", "2015041300292001", "p001", "cross_reference",
   text="confirms the 2010 ZLDA (CRFN 2010000384312) to the new owner",
   eff="2015-03-31", stated="2015-06-18", ans=["ENVELOPE"],
   note="a DEVR with ZERO TAX is a confirmation, not a transfer — counting it "
        "as a fifth purchase would have inflated the assemblage"),
 # ⚠ THE $65,710,000 SUM CLAIM WAS REMOVED 2026-08-06. It coexisted with the
 # two component claims (m2015a $31,930,000 + m2015b $33,780,000), so the
 # CAPITAL narrative listed the same borrowing three times — the exact
 # double-count this whole design exists to prevent, committed in the claim
 # table and caught only when the functional view put all three on adjacent
 # lines. AN AGGREGATE IS NEVER A CLAIM; it is a view over claims. The
 # construction total is now sum(mortgage) for 2015-09-02, computed once.
 C("c2015-pledge", "2015091001439005", None, "consolidation", num=113_710_000,
   unit="USD", eff="2015-09-02", ev="index", ans=["CAPITAL"]),


 C("c2015-notours", "2015091001439001", "p003", "defect",
   text="⚠ THIS DOCUMENT IS NOT LAM'S AND NOT ABOUT LOT 49'S FINANCING. It is "
        "a zoning-lot waiver and subordination by CAPITAL ONE, N.A. — lender "
        "to the NEIGHBOURING lots 53, 55 and 56. Neither Lam Gen 25 LLC nor "
        "Shanghai Commercial Bank appears anywhere in it",
   subject="1008000053", eff="2015-08-12", ans=["CONSENT", "ENVELOPE"],
   note="⚠ swept into the construction-loan batch by recording date. Anything "
        "treating a batch as one borrower's financing stack would record "
        "Capital One as a Lam lender. Capital One took NYCB's position on the "
        "Sabetfard lots on 2014-05-13"),
 C("c2015-omnibus", "2015091001439002", "p003", "unresolved",
   text="⚠ its own title is OMNIBUS MODIFICATION OF LOAN DOCUMENTS — it "
        "consolidates NOTHING. The $48,000,000 consolidation happened on "
        "2014-11-25 (CRFN 2014000397948); this instrument MODIFIES that "
        "existing lien",
   eff="2015-09-02", ans=["CAPITAL"],
   note="which is why it carries exemption 255 and $0 tax — no new debt"),
 C("c2015-maturity", "2015091001439002", "p005", "cross_reference",
   text="the construction-era Maturity Date is 2018-09-02, extendable once by "
        "six months for a fee of 0.25% of the facility loans",
   eff="2015-09-02", ans=["CAPITAL"],
   note="the only maturity date recorded anywhere on this parcel"),
 C("c2015-release", "2015091001439002", "p006", "unresolved",
   text="⚠ THE 2018 SPLIT WAS DESIGNED IN 2015. The Omnibus Modification "
        "creates a PREPAYMENT RELEASE of 113-117 West 24th Street for the "
        "greater of $22,500,000 or its pro-rata buildable-SF share, "
        "conditioned on recording a ZLDA between the remaining property and "
        "the release parcel",
   eff="2015-09-02", ans=["CAPITAL", "PARCEL", "ENVELOPE"],
   note="⚠ THE 2018 SPLITTER MOVED EXACTLY $22,500,000 TO LOT 50, AND THE 2019 "
        "ZLDA IS THE REQUIRED AGREEMENT. Three instruments across four years "
        "executing one 2015 plan — invisible unless all three are read"),
 C("c2015-floorarea", "2015091001439002", "p006", "envelope_balance",
   num=143_434, unit="sf",
   text="a covenanted FLOOR: the buildable floor area appurtenant to the "
        "Remaining Property may never fall below 143,434 sf",
   eff="2015-09-02", ans=["ENVELOPE", "CAPITAL"],
   note="⚠ a LENDER-IMPOSED MINIMUM ENVELOPE, and it is close to lot 49's "
        "post-split 141,929 sf. The two figures differ by 1,505 sf and both "
        "are recorded — worth reconciling"),
 C("c2015-alr-sum", "2015091001439005", "p003", "consolidation",
   num=113_710_000, unit="USD",
   text="the AL&R's own caption block sums the three facilities: Agreement "
        "$48,000,000 + Building Loan $31,930,000 + Project Loan $33,780,000 = "
        "Total Amount $113,710,000",
   eff="2015-09-02", ans=["CAPITAL", "INCOME"],
   note="⚠ THE ONE PLACE ON THIS PARCEL WHERE SUMMING IS CORRECT — and the "
        "instrument does the summing itself, on its own title page. A single "
        "rent pledge securing three facilities at once"),

 C("c2015-alr-restatement", "2015091001439005", "p016", "unresolved",
   text="the §255 affidavit says it outright: the assignment of rents 'is "
        "given for purposes of further securing THE SAME PRINCIPAL "
        "INDEBTEDNESS as is secured by (i) that certain Consolidated, Amended "
        "and Restated Mortgage ... (ii) that certain Building Loan Mortgage "
        "... and (iii) that certain Project Loan Mortgage' and 'does not "
        "create or secure any new or further indebtedness'",
   eff="2015-09-02", ans=["CAPITAL", "INCOME"],
   note="⚠ THE DEFINITIVE PROOF OF THE NON-ADDITIVITY RULE, stated by the "
        "document about itself. $113,710,000 is the TOTAL LIEN across three "
        "facilities; $65,710,000 is the NEW MONEY advanced that day. Both are "
        "correct statements of DIFFERENT THINGS, and the affidavit is what "
        "distinguishes them"),
 C("c2014-crfn-conflict", "2015091001439002", "p004", "defect",
   text="⚠ two instruments in the same batch cite the 2014 consolidated "
        "mortgage differently: the Omnibus Modification says 'recorded on "
        "December 12, 2014 as CRFN 2014000397948'; the assignment of rents "
        "says 'recorded on December 2, 2014 as CRFN 2014000397947'",
   eff="2015-09-02", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ different DATE and different CRFN for what both describe as the "
        "same instrument. 2014000397947 is the $7.5M gap mortgage; ...948 is "
        "the consolidation — so the AL&R's affidavit cites the wrong one. "
        "Every other schedule in the corpus gives 12-2-14 and ...948"),

 # ---- the 2015 construction covenants — recorded late, see module docstring
 C("c2015-lienlaw13", "2015091001439003", "p014", "easement",
   text="the Building Loan Mortgage carries the Lien Law section 13 "
        "trust-fund covenant: the borrower 'shall receive the advances "
        "secured hereby and shall hold the right to receive such advances as "
        "a trust fund to be applied first for the purpose of paying the cost "
        "of any improvement ... before using any part of the total of the "
        "same for any other purpose'",
   eff="2015-09-02", ans=["PERMIT", "CAPITAL"],
   note="the covenant exists specifically to police CONSTRUCTION advances. "
        "Present in identical words in the Project Loan Mortgage at "
        "2015091001439004 p014. ⚠ NO Lien Law section 22 building loan "
        "CONTRACT is referenced in any page read - section 22 requires the "
        "contract to be FILED, and it is not in this batch"),
 C("c2015-progress", "2015091001439003", "p017", "easement",
   text="section K.3: 'As soon as available, but not later than the first day "
        "of each calendar month and/or upon request, the Mortgagor shall "
        "provide to the Mortgagee, a progress report of the construction on "
        "the Premises'",
   eff="2015-09-02", ans=["PERMIT"],
   note="⚠ A MONTHLY CONSTRUCTION-PROGRESS OBLIGATION IS THE CLEAREST "
        "RECORDED PROOF THAT THIS IS A REAL BUILD, not an inference from "
        "timing. But the reports themselves are private - the record tells "
        "you they exist and never what they said"),
 C("c2015-demo-consent", "2015091001439003", "p016", "easement",
   text="section H.2: the borrower 'shall not remove or demolish nor alter "
        "the design or structural character of any building now or hereafter "
        "erected upon the Premises without the prior written consent of the "
        "Mortgagee which consent shall not be unreasonably withheld or "
        "delayed' - conditioned on a no-default certificate, evidence the "
        "value will not be diminished, and additional security during works",
   eff="2015-09-02", ans=["ENCUMBRANCE", "PERMIT"],
   note="the reasonableness qualifier matters: most consents in this corpus "
        "are 'sole and absolute discretion'"),
 C("c2015-junior-bar", "2015091001439003", "p018", "easement",
   text="section L.4: 'There shall be no junior financing or junior mortgage/"
        "liens with respect to the Premises (other than for the benefit of "
        "the Mortgagee) without the prior written consent of the Mortgagee, "
        "which consent shall be in the Mortgagee's sole and absolute "
        "discretion'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "CAPITAL"],
   note="with a matching bar on further borrowed money at L.1 and on "
        "transferring substantially all assets at L.2. This is what makes "
        "the 2018 splitter and the 2020 bridge loan lender-consented events "
        "rather than borrower choices"),
 C("c2015-trusts", "2015091001439003", "p017", "person",
   text="section K.1-K.4 requires annual tax returns 'of Mortgagor, and of "
        "each Guarantor and each of six named Trusts, prepared by a CPA' - "
        "the Raymond Lam 2012 Delaware Trust, the Teresa Lam 2012 Delaware "
        "Trust, the Jonathan Lam 2012 Delaware Trust, the Jeffrey Lam trust, "
        "the John Lam 2012 Trust and the Winnie Lam 2015 Trust",
   eff="2015-09-02",
   parties=["Raymond Lam (grantor)", "Teresa Lam (grantor)",
            "Jonathan Lam (grantor)", "Mui Hing Won Lam (grantor)",
            "Kin Chung Lam (grantor)", "Richard Tang (trust committee)",
            "Keith Lam (trust committee)", "Joann Lee (trust committee)"],
   ans=["PARTY", "CAPITAL"],
   note="⚠ THE REACH LADDER'S BEST RUNG ON THIS PARCEL. The deed gives an "
        "entity; the mortgage gives natural persons AND the family trust "
        "structure behind it. Note the document spells one person two ways "
        "on the SAME PAGE - 'Mui Hing Won Lam' as grantor of the John Lam "
        "trust and 'Mui Hing Wong Lam' as committee member of the Winnie Lam "
        "trust. Likely one person; recorded as the document has it"),
 C("c2015-appraisal", "2015091001439003", "p017", "easement",
   text="section J gives the lender 'the right, from time to time, upon "
        "reasonable notice to the Mortgagor, to conduct or cause to be "
        "conducted an appraisal or appraisals of the Premises, the cost of "
        "which shall be paid by the Mortgagor'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "VALUE"],
   note="⚠ APPRAISALS EXIST FOR THIS PARCEL AND ARE BORROWER-FUNDED. They "
        "are never recorded. A recurring shape in this corpus: the record "
        "proves a valuation happened and withholds the number"),
 C("c2015-receiver", "2015091001439003", "p028", "easement",
   text="section G: on default 'the Mortgagee shall be entitled to the "
        "appointment of a receiver of the rents, issues and profits of the "
        "Premises without the necessity of proving either inadequacy of the "
        "security or insolvency of the Mortgagor'",
   eff="2015-09-02", ans=["ENCUMBRANCE", "INCOME"],
   note="section H adds that on a sale of less than all the premises 'this "
        "Mortgage shall continue as a lien on the remaining portion' - which "
        "is the clause the 2018 splitter operates against"),
 C("c2015-casualty-draw", "2015091001439003", "p012", "easement",
   text="casualty proceeds are released on construction-style draw mechanics: "
        "requisitions certified by 'a licensed A.I.A. architect'; 'No payment "
        "made prior to the final completion of work shall exceed ninety "
        "percent (90%) of the value of the work performed'; released 'not "
        "more than once a month' subject to safeguards 'the Mortgagee then "
        "requires in connection with construction loans for similar projects'",
   eff="2015-09-02", ans=["PERMIT", "CAPITAL"],
   note="⚠ THIS GOVERNS INSURANCE PROCEEDS, NOT LOAN ADVANCES. I nearly "
        "recorded it as the draw schedule. The actual draw schedule, the "
        "completion date and any description of the building live in the "
        "UNRECORDED Building Loan Agreement and are not obtainable from these "
        "documents"),
 C("c2015-title-policy", "2015091001439003", "p008", "cross_reference",
   text="Loan Title Insurance Policy No. 2730732-94145650, issued by Federal "
        "Standard Abstract, Inc. as agent for Fidelity National Title "
        "Insurance Company - with a SEPARATE policy (number ending 720) for "
        "the Project Loan Mortgage",
   eff="2015-09-02", ans=["TITLE"],
   note="two policies for two lien positions on the same land, same day"),
 C("c2015-releaseparcel", "2015091001439002", "p005", "easement",
   text="section 1.6, replacing Article 3: the borrower 'shall have the right "
        "to secure the release of the lien of the Mortgage (the "
        "'Prepayment Release') from the parcel commonly known as 113-117 West "
        "24th Street, New York, New York (the 'Release Parcel')'",
   eff="2015-09-02", ans=["CAPITAL", "PARCEL"],
   note="⚠ THE 2019 SUBDIVISION WAS DESIGNED IN 2015. This clause names the "
        "24th Street half as a RELEASE PARCEL four years before it becomes "
        "lot 50. The 2018 splitter moved $22,500,000 onto it; this clause is "
        "why that was possible"),
 C("c2015-crossdefault", "2015091001439002", "p005", "easement",
   text="section 1.5: 'The occurrence of any Default or Event of Default "
        "under the Building Loan Documents or the Project Loan Documents "
        "shall constitute a Default or Event of Default under the Land Loan "
        "Agreement and the Land Loan Documents'",
   eff="2015-09-02", ans=["CAPITAL"],
   note="the three facilities are cross-defaulted, so the $48M land loan and "
        "the $65.71M of construction money stand or fall together. Maturity "
        "moved to 2018-09-02 with one six-month extension option at a 0.25% "
        "fee, conditioned on extending the other facilities too"),
 C("c2015-lien-positions", "2015091001439003", "p008", "unresolved",
   text="the Building Loan Mortgage 'warrants that this Mortgage is and shall "
        "be maintained as a valid SECOND lien on the Premises'; the Project "
        "Loan Mortgage at 2015091001439004 p008 warrants a valid THIRD lien - "
        "both behind the pre-existing $48,000,000 Land Loan Mortgage",
   eff="2015-09-02", ans=["PRIORITY", "CAPITAL"],
   note="⚠ THE ONLY EXPLICIT LIEN-POSITION LADDER IN THE ENTIRE CORPUS. "
        "PRIORITY has been the thinnest function all session because almost "
        "nothing else states its rank on the face of the instrument"),
 C("c2015-recourse-absent", "2015091001439003", "p003", "unresolved",
   text="NO exculpation, non-recourse or limitation-of-liability clause "
        "appears in the Building Loan Mortgage - the agent read p003 through "
        "p035. A COMPLETION GUARANTY 'in favor of the Mortgagee dated of even "
        "date herewith' is referenced at p006 and is NOT recorded",
   eff="2015-09-02", ans=["CAPITAL"],
   note="⚠ ABSENT here is not the same as non-recourse. A completion guaranty "
        "implies separate guarantor exposure that the record cannot size. "
        "Contrast 2003, where non-recourse was granted expressly"),
 # ---- 2019 subdivision --------------------------------------------------
 C("c2019-subdiv", "2019071700601003", "p044", "subdivision",
   text="'the Lot 50 Land and Lot 49 Land previously constituted a single tax "
        "lot... formerly designated as Lot 49'",
   eff="2019-05-20", stated="2019-07-22", ans=["PARCEL", "IDENTIFY"]),
 C("c2019-l49area", "2019071700601003", "p044", "lot_area", num=8_527, unit="sf",
   eff="2019-05-20", ans=["PARCEL"]),
 C("c2019-l50area", "2019071700601003", "p044", "lot_area", num=7_112, unit="sf",
   subject="1008000050", eff="2019-05-20", ans=["PARCEL"]),
 C("c2019-l49env", "2019071700601003", "p044", "envelope_balance", num=141_929,
   unit="sf", eff="2019-05-20", ans=["ENVELOPE"],
   note="8,527 land x FAR 10 = 85,270 self-generated + 56,659 acquired"),
 C("c2019-l50env", "2019071700601003", "p044", "envelope_balance", num=127_035,
   unit="sf", subject="1008000050", eff="2019-05-20", ans=["ENVELOPE"],
   note="7,112 x 10 = 71,120 + 55,915 acquired. ⚠ THE MOVEMENT OUT OF LOT 49 IS "
        "THE FULL 127,035, not the 55,915 acquired share — a subdivision moves "
        "land and rights together"),
 # ---- from the WHEREAS clauses, p006 — four findings ---------------------
 C("c2016-delivery-pluto", "2019071700601003", "p006", "unresolved",
   text="PLUTO records yearbuilt 2016 for this lot — NOT an ACRIS fact, kept "
        "here only so the contradiction has two ends to hang from",
   eff="2016-01-01", stated="2019-05-20", ev="index", ans=["ASBUILT"]),
 C("c2019-permit", "2019071700601003", "p006", "cross_reference",
   text="DOB Permit Application No. 121187214 — the Lot 49 Building Permit "
        "Application", eff="2019-05-20", ans=["PERMIT", "ASBUILT"],
   note="⚠ A DIRECT CROSS-LANE JOIN KEY. ACRIS names a DOB job number; the DOB "
        "decoder can attach to it without any name matching"),
 C("c2019-demolished", "2019071700601003", "p006", "unresolved",
   text="'Lot 49 Owner has DEMOLISHED an existing building on the Lot 49 Land "
        "and intends to construct a new building' — and the same is said of "
        "Lot 50. As of May 2019 BOTH lots are cleared sites awaiting "
        "construction",
   eff="2019-05-20", ans=["ASBUILT", "PERMIT"],
   note="⚠ CONTRADICTS the '2016 — the 40-storey hotel opens' line, which came "
        "from PLUTO yearbuilt and never from a document. Either PLUTO's "
        "yearbuilt is wrong, or it describes a building not on this lot, or my "
        "reading of the 2015 construction loan as THIS tower was wrong. "
        "UNRESOLVED — and only the DOB lane can settle it"),
 C("c2019-zoninglot", "2019071700601003", "p006", "zoning_lot_members",
   text="the COMBINED ZONING LOT survives the tax-lot split — lots 49 and 50 "
        "remain one zoning lot 'as the same may be further enlarged or "
        "subdivided'", eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ TWO TAX LOTS, ONE ZONING LOT. The 2013 eight-lot declaration was "
        "not undone by the subdivision"),
 C("c2019-independence", "2019071700601003", "p006", "party_role",
   text="the parties intend each to exercise its rights in future 'WITHOUT "
        "HAVING TO SEEK ANY CONSENT, APPROVAL OR OTHER ACTION FROM THE OTHER'",
   eff="2019-05-20", ans=["CONSENT"],
   note="the two Lam entities deliberately decoupled — the CONSENT answer for "
        "anyone dealing with either lot"),
 C("c2019-lot20-crfn", "2019071700601003", "p006", "cross_reference",
   text="Lot 20 Declaration CRFN 2013000343072 and Lot 20 ZLDA CRFN "
        "2013000343073, both dated 2013-08-07, recorded 2013-08-27",
   subject="1008000020", eff="2013-08-07", stated="2019-05-20",
   ans=["ENVELOPE"],
   note="⚠ DISCREPANCY WITH c2014-lot20, which took a Lot 20 ZLDA at CRFN "
        "2008000078652 dated 2008-02-26 from the 2014 mortgage's Exhibit A. "
        "Either lot 20 has TWO ZLDAs five years apart, or one of the two "
        "readings is wrong. Both are recorded; neither is discarded"),
 C("c2019-additional", "2019071700601003", "p006", "zoning_lot_members",
   text="either owner may add an 'Additional Parcel' — development rights, "
        "volumes of air, or land contiguous for at least TEN LINEAR FEET, "
        "within Block 800", eff="2019-05-20", ans=["ENVELOPE"],
   note="the assemblage is drafted to keep growing"),
 C("c2019-person", "2019071700601003", "p044", "person",
   text="Jeffrey Lam signs for BOTH LG CHELSEA LLC and LAM GEN 25 LLC",
   eff="2019-05-20", ans=["PARTY"],
   note="one signatory on both sides = one control across the split"),
 C("c2019-contra", "2018113000347001", None, "unresolved",
   text="lot 50 carries its own ACRIS legals in 2018 (2018070201269001, "
        "2018113000347002-005), so the TAX LOT was divided BEFORE the 2019 "
        "instrument that describes the split. The actual division date is a DOF "
        "tax-map question, not an ACRIS one",
   eff="2018-11-19", ev="index", ans=["PARCEL"]),


 # ---- the 2018 splitter — the correction that halves lot 49's debt -------
 C("c2018-splitter", "2018113000347001", "p003", "unresolved",
   text="⚠ THIS IS A MORTGAGE AND NOTE SPLITTER AGREEMENT, NOT A "
        "CONSOLIDATION. It severs the $48,000,000 lien into $25,500,000 on "
        "LOT 49 and $22,500,000 on LOT 50, the latter assumed by LG Chelsea "
        "LLC",
   eff="2018-11-19", stated="2018-12-03", ans=["CAPITAL", "PARCEL"],
   note="⚠ I carried $48,000,000 as lot 49's position from 2018 to 2023. It "
        "was $25,500,000. Overstated by $22,500,000 for five years"),
 C("c2018-l49position", "2018113000347001", "p011", "consolidation",
   num=25_500_000, unit="USD",
   text="lot 49's actual mortgage position after the 2018 split",
   eff="2018-11-19", ans=["CAPITAL"],
   note="Schedule B: 'shall remain a lien in the principal amount of "
        "$25,500,000.00 ... (Block: 800, Lot: 49)'"),
 C("c2018-l50position", "2018113000347001", "p011", "consolidation",
   num=22_500_000, unit="USD", subject="1008000050",
   text="the severed lien that moved to lot 50, assumed by LG Chelsea LLC",
   eff="2018-11-19", ans=["CAPITAL"]),
 C("c2018-indexdefect", "2018113000347001", "p001", "defect",
   text="⚠ RETRACTED IN PART, AND THE CITY FIXED IT. The cover page did index "
        "this splitter to MANHATTAN 800 LOT 50 — but the ACRIS index carries "
        "a REMARK against the document reading 'BLOCK CORRECTION. CORRECTED "
        "TO ADD LOT 49. LOT 49 WAS INADVERTENTLY OMITTED AT THE TIME OF "
        "RECORDING. UPDATED 8/19/20.' The correction is dated 2020-08-19",
   eff="2018-12-03", ans=["IDENTIFY", "DEBT"],
   note="⚠ I SPENT AN AGENT AND TWENTY PAGES DISCOVERING THIS AND WROTE THAT "
        "'a BBL-keyed pull can miss the operative event for a parcel's "
        "debt'. THAT IS NO LONGER TRUE and has not been since 2020 — the "
        "index now returns lot 49 for this document, which is exactly why it "
        "appeared in the 96-document manifest. ⚠ THE ACRIS REMARKS DATASET "
        "(9p4w-7npp) CARRIES THIS IN ONE LINE, FREE, AND I NEVER PULLED IT "
        "until the extraction was redone properly. The defect was real in "
        "2018; the claim that it still hides the instrument was mine, and "
        "wrong"),

 # ---- the 2015 construction stack, confirmed and named -------------------
 C("c2015-building", "2015091001439003", "p001", "mortgage", num=31_930_000,
   unit="USD",
   text="BUILDING LOAN MORTGAGE — the instrument's own name — affecting Tax "
        "Lots 49 AND 50",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "PERMIT"],
   note="mortgage tax paid $894,040 = 2.800% on the full face, no exemption. "
        "Confirms this is genuinely new money, not a restatement"),
 C("c2015-project", "2015091001439004", "p001", "mortgage", num=33_780_000,
   unit="USD", text="PROJECT LOAN MORTGAGE — the instrument's own name",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "PERMIT"],
   note="mortgage tax paid $945,840 = 2.800% on the full face. Building Loan + "
        "Project Loan both taxed in full, so the $65,710,000 total is real. "
        "⚠ 'the construction loan' was never an inference — the instruments "
        "say Building and Project Loan outright"),

 # ---- MetLife arrives by assignment --------------------------------------
 C("c2023-assignments", "2025101700864005", "p026", "cross_reference",
   text="SHANGHAI COMMERCIAL BANK assigned ALL FOUR facilities to METLIFE "
        "COMMERCIAL MORTGAGE ORIGINATOR LLC on 2023-10-16 — CRFN 2023000287577 "
        "(the consolidated mortgages), 578 (building loan), 579 (project "
        "loan), 580 (the 2020 mortgage)",
   eff="2023-10-16", ans=["CAPITAL", "PARTY"],
   note="⚠ MetLife did not refinance out an incumbent — it BOUGHT the paper, "
        "then added a $25,490,000 gap and consolidated to $120,000,000. The "
        "same acquire-gap-consolidate pattern as 2007, 2012, 2013 and 2014"),

 # ---- the 2025 lender -----------------------------------------------------
 C("c2025-lender", "2025101700864005", "p004", "party_role",
   text="DEUTSCHE BANK AG, NEW YORK BRANCH, as administrative agent for a "
        "lender group — the 2025 lender",
   eff="2025-10-16", ans=["CAPITAL", "PARTY"],
   note="⚠ I recorded the 2025 event with no lender named. Deutsche Bank took "
        "a $3,000,000 gap mortgage (tax $84,000) and the whole position "
        "consolidated to $123,000,000. Borrower is now LAM GEN 25 LLC AND "
        "CHELSEA 25 HOTEL LLC jointly"),
 C("c2025-absolute", "2025101700864005", "p006", "unresolved",
   text="the 2025 assignment of rents is a PRESENT, ABSOLUTE assignment — "
        "'not an assignment for additional security only' — with a revocable "
        "licence back that terminates automatically on an Event of Default, "
        "without notice",
   eff="2025-10-16", ans=["INCOME", "CAPITAL"],
   note="⚠ structurally different from the 2020 Shanghai assignment, which was "
        "expressly collateral. An absolute assignment puts the rents outside "
        "the borrower's estate from day one"),
 C("c2025-unrecorded", "2025101700864005", "p010", "unresolved",
   text="'In case of any conflict between the terms of this Assignment and the "
        "terms of the Loan Agreement, the terms of the Loan Agreement shall "
        "prevail' — and the Loan Agreement, Cash Management Agreement and "
        "Clearing Account Agreement are all UNRECORDED",
   eff="2025-10-16", ans=["CAPITAL"],
   note="⚠ the same off-register structure as MetLife. Every borrower-side "
        "leasing covenant — amendment, termination, prepaid rent, major-lease "
        "consent — is absent from the recorded text and pulled in wholesale by "
        "reference. The public record cannot tell you what the borrower may do "
        "with its leases"),
 C("c2019-blanket-zlda", "2025101700864005", "p015", "cross_reference",
   text="CRFN 2019000231248, recorded 2019-07-22 — a zoning lot development "
        "and easement agreement covering ALL NINE lots: 20, 21, 22, 23, 49, "
        "50, 53, 55 and 56",
   eff="2019-07-22", stated="2025-10-16", ans=["ENVELOPE"],
   note="the easement schedule every later lender recites"),

 # ---- ⚠ THE ELEVATION, WITH ITS DATUM ------------------------------------
 C("c2019-lot20-elevation", "2019071700601001", "p007", "easement",
   subject="1008000020",
   text="LOT 20 IS SPLIT AT 130 FEET. 'LOT 20, LOWER PARCEL - All that certain "
        "plot, piece or parcel of land, LYING BELOW a lower limiting plane "
        "drawn at an elevation of 130 FEET above the datum level used by the "
        "Topographical Bureau, Borough of Manhattan, which is 2.78 feet above "
        "National Geodetic Survey vertical datum 1929 ... mean sea level "
        "Sandy Hook New Jersey' - and 'LOT 20, AIR SPACE PARCEL ... LYING "
        "ABOVE' the same plane",
   eff="2019-07-22", vfrom=130.0, vto=None,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   hext="the Lot 20 footprint, 116 feet 5 inches deep from West 24th Street, "
        "beginning 425 feet westerly",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ THE NUMBER I HAVE BEEN MISSING ALL SESSION. Every prior instrument "
        "said 'lower limiting plane' and none gave the elevation. ⚠ THE AIR "
        "SPACE PARCEL HAS NO STATED CEILING - it is open-ended upward. And "
        "the datum is doubly specified, city bureau AND national geodetic, "
        "which is what makes 130 feet a locatable plane rather than a number. "
        "Recorded identically in 2019071700601002 p016"),

 # ---- ⚠ Marriott waived --------------------------------------------------
 C("c2019-marriott-waived", "2019071700601001", "p003", "unresolved",
   text="MARRIOTT WAIVED AND SUBORDINATED ITS RIGHT OF FIRST REFUSAL: 'THIS "
        "WAIVER AND SUBORDINATION OF ROFR is made as of the 18th day of June "
        "2019, by Marriott International, Inc.' - signed by Kip W. Vreeland, "
        "Senior Vice President, Full Service Franchising",
   eff="2019-06-18", stated="2019-07-22", ans=["ENCUMBRANCE", "CONSENT"],
   note="⚠ THIS PARTLY ANSWERS THE OPEN MARRIOTT QUESTION. The 2014 "
        "subordination was CONDITIONAL on three things and I flagged that no "
        "later paperwork addressed the conditions. This 2019 waiver is a "
        "fresh, specific consent to the zoning-lot restructuring - but it is "
        "scoped to THAT event. It does not cure the conditions for the 2023 "
        "MetLife or 2025 Deutsche Bank assignments, which remain unaddressed"),
 C("c2019-franchise-named", "2019071700601001", "p003", "unresolved",
   text="the franchise is named at last: a RENAISSANCE HOTEL Franchise "
        "Agreement dated July 14, 2014 with Lam Gen 25 LLC as Franchisee, and "
        "Lam Gen 25 is 'a party in interest ... with respect to the combined "
        "zoning lot'",
   eff="2014-07-14", stated="2019-07-22", ans=["TENANCY", "PERMIT"],
   note="the 2014 memorandum named no brand - 'Renaissance' appeared only in "
        "a file-reference footer, and in the 2023 paperwork only as a running "
        "page footer. ⚠ HERE IT IS IN OPERATIVE TEXT for the first time"),
 C("c2019-zlda-date", "2019071700601001", "p003", "cross_reference",
   text="'Franchisee is party to a Zoning Lot and Development Easement "
        "Agreement DATED AS OF MAY 20, 2019 (the ZLDA) with LG CHELSEA LLC "
        "(the Lot 50 Owner)' - while the ZLDA recorded at CRFN 2019000231248 "
        "carries a recording date of 2019-07-22",
   eff="2019-05-20", stated="2019-07-22", ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ execution 2019-05-20, mortgagee waiver 2019-05-20, Marriott waiver "
        "2019-06-18, recording 2019-07-22. FOUR DATES, ONE TRANSACTION. And "
        "the ZLDA ITSELF IS STILL NOT IN THE CORPUS - third instance of the "
        "operative instrument being the missing one, after the 2010 ZLDA and "
        "the 2023 CEMA"
        "⚠ CORRECTION: I wrote 'the ZLDA ITSELF IS STILL NOT IN THE"
        "CORPUS'. It is on disk as 2019071700601003, 44 pages"),
 C("c2019-ninelots", "2019071700601002", "p003", "zoning_lot_members",
   text="the Combined Zoning Lot is 'designated as Lots 20, 21, 22, 23, 49, "
        "50, 53, 55 and 56 in Block 800' - 120 West 25th (53), 124 West 25th "
        "(55), 126 West 25th (56), 127 West 24th (23), 131 West 24th (22), "
        "133 West 24th (21), 135 West 24th (20), plus lots 49 and 50",
   eff="2019-05-20", stated="2019-07-22", ans=["ENVELOPE", "PARCEL"],
   note="assembled by FIVE declarations recorded over three years: CRFN "
        "2010000384309 (2010-10-14), 2013000007932 (2012-12-19), "
        "2013000241544 and 2013000241548 (both 2013-05-17), and a fifth. ⚠ "
        "NOTE 2010000384309 IS THE DECLARATION, NOT THE ZLDA AT ...312 - the "
        "assemblage is documented by the announcements while the deals stay "
        "off the record"),
 C("c2019-shanghai-waived", "2019071700601002", "p003", "unresolved",
   text="'THIS WAIVER AND SUBORDINATION OF MORTGAGE is made as of the 20th "
        "day of May, 2019, by SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH' "
        "- subordinating BOTH the Lot 49 Mortgage and the Lot 50 Mortgage to "
        "the zoning-lot declaration",
   eff="2019-05-20", stated="2019-07-22", ans=["CONSENT", "PRIORITY"],
   note="the lender consented to the subdivision that split its own "
        "collateral. Signed by Timothy Chan and Chiu Nam Wu - the same two "
        "officers who signed the 2014 Marriott subordination"),

 # ---- ⚠ THE BROWNFIELD, absent from every debt document ------------------
 C("c2020-cleanup", "2020061600455001", "p002", "easement",
   text="⚠ AN ENVIRONMENTAL RESTRICTIVE COVENANT. 'DECLARATION OF COVENANTS "
        "AND RESTRICTIONS' made by LAM GEN 25 LLC, tied to a VOLUNTARY "
        "CLEANUP AGREEMENT DATED FEBRUARY 10, 2016 with the NYC OFFICE OF "
        "ENVIRONMENTAL REMEDIATION. ACRIS types it 'SUNDRY MISCELLANEOUS'",
   eff="2016-02-10", stated="2020-06-16", ans=["ENCUMBRANCE", "PERMIT"],
   note="⚠ NOTHING IN THE ENTIRE DEBT RECORD HINTS AT THIS. Not one mortgage, "
        "assignment or CEMA from 2015 through 2025 mentions contamination, "
        "remediation or OER - and the only prior environmental fact in the "
        "corpus is a 1990 asbestos report. A covenant that runs with the land "
        "and constrains use, recorded under the junk doc-type again, exactly "
        "like the Marriott subordination. ⚠ MY BRIEF CALLED THIS DOCUMENT "
        "'the 2020 bridge loan'. It has no lender, no loan amount and no "
        "assignment of rents anywhere in 19 pages"),
 C("c2020-loan", "2020081400407002", "p003", "mortgage", num=5_000_000,
   unit="USD",
   text="the actual 2020 loan: 'WHEREAS, Assignee is loaning Assignor the "
        "principal sum of $5,000,000 (the Loan)' from SHANGHAI COMMERCIAL "
        "BANK LTD., NEW YORK BRANCH",
   eff="2020-08-05", stated="2020-08-14", ans=["DEBT"],
   note="⚠ the companion MORTGAGE is Document ID 2020081400407001 and IS NOT "
        "IN THE CORPUS. Fourth instance of the operative instrument missing"
        "⚠ CORRECTION: I wrote the companion mortgage 'IS NOT IN THE"
        "CORPUS'. It is on disk as 2020081400407001, 38 pages"),
 C("c2020-tax-conflict", "2020081400407002", "p013", "defect",
   text="⚠ THE COVER PAGE CLAIMS AN EXEMPTION AND THE AFFIDAVIT'S OWN MARGIN "
        "SAYS THE TAX WAS PAID. Cover p001: 'Taxable Mortgage Amount: $0.00' "
        "and 'Exemption: 255'. The section 255 affidavit at p013 carries a "
        "handwritten note under the $5,000,000 indebtedness recital: "
        "'Mortgage Tax Paid $140,000.00'",
   eff="2020-08-14", ans=["DEBT", "IDENTIFY"],
   note="$140,000 / $5,000,000 = 2.800% exactly - the correct commercial rate "
        "on the full principal. So the handwriting describes tax paid on the "
        "COMPANION MORTGAGE (which is not in the corpus) while THIS "
        "instrument is the exempt assignment of rents. Most likely a "
        "cross-reference, not a contradiction - but both are on the record "
        "and I am not repairing either. ⚠ HANDWRITING, AGAIN"),
 C("c2020-hybrid-assignment", "2020081400407002", "p006", "easement",
   text="⚠ THE 2020 ASSIGNMENT NEVER SAYS 'ABSOLUTE' OR 'COLLATERAL' - "
        "neither word appears in its sixteen sections. The granting clause "
        "reads absolute ('Assignor intending hereby to assign to Assignee ALL "
        "OF THE LANDLORD'S INTEREST in said Leases') but section 6 is "
        "collateral in structure: rents are 'received and collected by "
        "Assignor AS A TRUST FUND for the sums secured by the Mortgage'",
   eff="2020-08-05", ans=["INCOME", "ENCUMBRANCE"],
   note="⚠ I HAVE BEEN CLASSIFYING THESE BINARILY - absolute versus "
        "collateral - and treating the label as the fact. This one refuses "
        "the label and has to be read structurally. The 2025 Deutsche Bank "
        "assignment is expressly absolute, the 2020 Shanghai one is not: "
        "that difference is real and I would have missed it by keyword"),
 C("c2019-broken-exhibits", "2019071700601002", "p010", "defect",
   text="⚠ TWO EXHIBITS ARE EMPTY PLACEHOLDERS AS RECORDED. Exhibit B (Lot "
        "49, p010) and Exhibit D (Lot 50, p013) each read only 'ALL that "
        "certain plot, piece or parcel of land ... bounded and described as "
        "follows: BEGINNING' followed by blank space, with the footer 'Error! "
        "Unknown document property name.'",
   eff="2019-07-22", ans=["PARCEL", "IDENTIFY"],
   note="a Word autofill failure recorded into the permanent land record. The "
        "substantive boundary text does survive elsewhere in the same "
        "instrument under different headers, so the description is "
        "recoverable - but the LABELLED exhibits for both subdivided lots are "
        "blank"),
 C("c2019-deed-vs-survey", "2019071700601002", "p010", "boundary_origin",
   text="the 2019 metes and bounds reconcile the old conflict explicitly: "
        "'THENCE South 0 degrees 0 minutes 4.9 seconds East, 82.73 feet (82 "
        "FEET 10 INCHES ON DEED)'",
   eff="2019-07-22", ans=["PARCEL"],
   note="⚠ A SURVEYED DISTANCE AND A DEED DISTANCE, PRINTED SIDE BY SIDE. "
        "82.73 surveyed feet = 82 feet 8.76 inches, which is the 1990 "
        "mortgage's '82 feet 8-3/4 inches'. So BOTH figures in the "
        "thirty-five-year conflict are right: 8-3/4 inches is the survey and "
        "10 inches is the deed. ⚠ THIS RESOLVES c1990-legal-conflict and "
        "c2010-legal-conflict-again - not a defect at all, but two "
        "measurement conventions that no instrument bothered to distinguish "
        "until 2019"),
 # ---- 2020 --------------------------------------------------------------
 C("c2020-mtge", "2020081400407001", "p001", "mortgage", num=5_000_000, unit="USD",
   text="SHANGHAI COMMERCIAL BANK", eff="2020-08-05", stated="2020-08-19",
   ans=["ENCUMBER", "CAPITAL", "PARTY"]),
 C("c2020-rate", "2020081400407001", "p001", "tax_rate", num=0.028, unit="rate",
   eff="2020-08-05", ev="derived", ans=["CAPITAL"],
   note="$140,000 / $5,000,000 = 2.800%, all seven components to the cent"),
 C("c2020-person", "2020081400407001", "p001", "person",
   text="Jeffrey Lam, Manager", eff="2020-08-05", ans=["PARTY"]),
 C("c2020-affidavit", "2020081400407001", "p037", "unresolved",
   text="section 255-a affidavit swears 'not more than six residential dwelling "
        "units' on a 40-storey hotel PLUTO records with unitsres = 0. The box "
        "did NOT change the tax; whether it was appropriate is a legal question "
        "the documents do not answer", eff="2020-08-05", ans=["OCCUPY"]),

 # ---- 2023 --------------------------------------------------------------
 C("c2023-reorg", "2023110100486001", "p001", "conveyance",
   text="LAM GEN 25 LLC -> CHELSEA 25 HOTEL LLC", eff="2023-10-16",
   stated="2023-11-06", ans=["TITLE", "PARTY"],
   note="$0 consideration, ALL taxes $0, same address both sides — an entity "
        "reorganisation, NOT a sale"),
 C("c2023-mtge", "2023110100486009", "p001", "mortgage", num=25_490_000,
   unit="USD", text="METROPOLITAN LIFE INSURANCE CO", eff="2023-10-16",
   ans=["ENCUMBER", "CAPITAL", "PARTY"],
   note="taxable IN FULL; tax $713,720 = 2.800%. THE ONLY NEW MONEY in an "
        "eleven-document batch whose face sums to $265,490,000"),
 C("c2023-cons", "2023110100486010", "p001", "consolidation", num=120_000_000,
   unit="USD", eff="2023-10-16", ans=["CAPITAL"],
   note="taxable $0, exemption 255"),
 C("c2023-xref", "2023110100486010", "p001", "cross_reference",
   text="MANHATTAN Year 1990 Reel 1707 Page 1285", eff="2023-10-16",
   ans=["ENCUMBER"], note="33 years of rolled-forward debt"),


 # ---- ⚠ THE LIEN IS NOT THE DEBT --------------------------------------
 C("c2025-outstanding", "2025101700864004", "p004", "consolidation",
   num=85_000_000, unit="USD",
   text="THE ACTUAL OUTSTANDING PRINCIPAL — 'The outstanding principal "
        "indebtedness evidenced by the Existing Notes and secured by the "
        "Existing Mortgages is $85,000,000.00'",
   eff="2025-10-16", ans=["CAPITAL"],
   note="⚠ I HAVE BEEN REPORTING $123,000,000 AS 'THE POSITION TODAY' ALL DAY. "
        "That is the LIEN. The DEBT is $85,000,000, leaving roughly $38,000,000 "
        "of undrawn capacity. For a broker that is the difference between an "
        "over-levered asset and one with room — and it is stated in the "
        "instrument's own recitals"),
 C("c2025-maxconflict", "2025101700864004", "p025", "defect",
   text="⚠ THREE DIFFERENT MAXIMUM/OUTSTANDING FIGURES ON ONE INSTRUMENT: the "
        "recorded mortgage §15.02(c) caps the secured principal at "
        "$85,000,000; the Section 255 affidavit sworn the same day by the same "
        "signatory swears the maximum is $123,000,000; and the same affidavit "
        "states the unpaid balance of the existing mortgage as $120,000,000",
   eff="2025-10-16", ans=["CAPITAL"],
   note="do not report a single 'maximum secured' for this parcel — the record "
        "contradicts itself on its face"),
 C("c2025-borrower", "2025101700864004", "p004", "party_role",
   text="a TWO-ENTITY fee/operating-lease structure: CHELSEA 25 HOTEL LLC as "
        "fee owner and LAM GEN 25 LLC as operating lessee, both signing "
        "through LG 25 HOTEL DE LLC (Delaware) as managing member, by Jeffrey "
        "Lam, Manager",
   eff="2025-10-16", ans=["TITLE", "PARTY", "CAPITAL"],
   note="the 2023 'reorganisation' created an opco/propco split, not a simple "
        "rename. Lam Gen 25 did not disappear — it became the operating lessee"),
 C("c2025-devrights-collateral", "2025101700864004", "p006", "unresolved",
   text="the mortgage expressly pledges 'air rights and development rights "
        "(including, without limitation, all rights under the ZLDA), excess or "
        "unused zoning floor area development rights, abatements, zoning floor "
        "area bonuses, zoning incentives or awards (including designation or "
        "availability of additional zoning floor area pursuant to the NYC "
        "Zoning Resolution)'",
   eff="2025-10-16", ans=["ENVELOPE", "CAPITAL"],
   note="⚠ FUTURE ZONING BONUSES ARE ALREADY COLLATERAL. The 54.52% share of "
        "any future bonus rights allocated by the 2019 split is pledged to "
        "Deutsche Bank before it exists. ⚠ and 'the ZLDA' is used as a defined "
        "term that is never defined in the recorded text"),
 C("c2025-nofirstlien", "2025101700864004", "p017", "unresolved",
   text="⚠ NO first-lien representation anywhere in the recorded mortgage. "
        "Articles I-XV contain no 'valid first lien' covenant; priority "
        "representations live in Article 3 of the UNRECORDED Loan Agreement",
   eff="2025-10-16", ans=["CAPITAL"],
   note="the 2013 Goldman CEMA stated 'a single, FIRST LIEN' outright. This one "
        "does not — so PRIORITY on this parcel today cannot be established from "
        "the public record"),

 C("c2023-reconcile", "2023110100486005", "p003", "consolidation",
   num=94_510_000, unit="USD",
   text="the four assigned tranches at their STATED OUTSTANDING BALANCES: Land "
        "$25,500,000 + Building $31,930,000 + Project $33,780,000 + Bridge "
        "$3,300,000 = $94,510,000; plus MetLife's new $25,490,000 gap = "
        "$120,000,000 exactly",
   eff="2023-10-16", ev="derived", ans=["CAPITAL"],
   note="⚠ EVERY DOLLAR OF THE 2023 CEMA IS ACCOUNTED FOR. These reconcile "
        "because each assignment recites its tranche's OUTSTANDING BALANCE as "
        "the consideration, not its face. The same chain's FACE amounts sum to "
        "$146,344,892, which is meaningless"),
 C("c2023-chelsea-gap", "2023110100486005", "p012", "unresolved",
   text="⚠ the §275 affidavits swear CHELSEA 25 HOTEL LLC is 'the mortgagor', "
        "but Chelsea 25 Hotel LLC appears in NO mortgage, assignment or "
        "modification anywhere in the Exhibit A lien history",
   eff="2023-10-16", ans=["TITLE", "CAPITAL"],
   note="it enters by the same-day $0 deed, which is outside the assignment "
        "batch. Nothing in these four instruments establishes how it joined "
        "the chain"),
 C("c2023-truncated", "2023110100486008", "p001", "defect",
   text="⚠ ANOTHER TRUNCATED DOCUMENT: the Bridge Loan assignment declares "
        "'PAGE 1 OF 9' and only 3 images exist. Its entire Exhibit A is "
        "missing, so the assigned mortgage is identified ONLY by the cover "
        "page cross-reference CRFN 2020000234174",
   eff="2023-11-06", ans=["IDENTIFY", "CAPITAL"],
   note="⚠ THIRD CONFIRMED TRUNCATION (with 2025101700864003 at 2 of 14 and "
        "2023110100486007 at 8 of 9). This is a SYSTEMATIC FETCH DEFECT, not "
        "three coincidences. The $120,000,000 reconciliation has one link "
        "resting on a cover page alone"),
 C("c1998-defect-carried", "2023110100486005", "p006", "defect",
   text="the lien schedule carries its own warning on the 1998 Edelman "
        "mortgage: 'NOTE: Recites incorrect legal description.'",
   eff="1998-11-24", stated="2023-10-16", ans=["IDENTIFY", "PARCEL"],
   note="⚠ NEVER CURED. It has been consolidated forward through SIX "
        "generations of instruments — 1999, 2007, 2012, 2013, 2014, 2018 — "
        "into the lien MetLife then sold to Deutsche Bank. A 27-year-old "
        "defect still riding in the current lien"),

 # ---- ⚠ the operative instrument was never fetched -----------------------
 C("c2023-cema-missing", "2025101700864002", "p011", "defect",
   text="⚠ THE $120,000,000 CONSOLIDATED MORTGAGE ITSELF IS NOT IN THIS "
        "CORPUS. It is CRFN 2023000287582, recorded 2023-11-06, and no "
        "folder on disk holds it. Every figure I have for the current lien "
        "comes from OTHER instruments RECITING it - the companion assignment "
        "of rents, the section 255 affidavit, and the 2025 assignment's "
        "Exhibit B",
   eff="2023-11-06", stated="2025-10-23", ev="derived", ans=["DEBT", "IDENTIFY"],
   note="⚠ RETRACTED — FALSE. I recorded that the $120,000,000 CEMA (CRFN"
        "2023000287582) was not in this corpus. IT IS ON DISK as document"
        "2023110100486010, 45 pages, and had never been opened. What"
        "remains true and useful: I misnamed 2023110100486011 as 'the"
        "2023 CEMA' when its own cover page reads ASSIGNMENT OF LEASES"
        "AND RENTS"),

 # ---- ⚠ Chelsea 25 Hotel LLC — answered, and the answer is a hole --------
 C("c2023-chelsea-entry", "2023110100486011", "p019", "unresolved",
   text="CHELSEA 25 HOTEL LLC ENTERS THE CHAIN EXACTLY ONCE, AT ITEM 10: "
        "'Gap Mortgage dated as of October 16, 2023, made by Chelsea 25 Hotel "
        "LLC and Lam Gen 25 LLC to MetLife Commercial Mortgage Originator, "
        "LLC, in the principal amount of $25,490,000.00 (Mortgage Tax Paid: "
        "$713,720.00)'. It appears in NONE of items 1 through 9, which run "
        "112 West 25 Company (1990) to Edelman Family LP (1998) to 112-118 "
        "West 25th LLC (2007, 2012) to Lam Gen 25 LLC (2013-2020)",
   eff="2023-10-16", stated="2023-11-06", ans=["TITLE", "DEBT"],
   note="⚠ IT BECOMES A MORTGAGOR BY SIGNING A NEW MORTGAGE, NOT BY TAKING "
        "TITLE. No recorded deed or conveyance anywhere in this corpus shows "
        "Chelsea 25 Hotel LLC acquiring the fee from its predecessors. "
        "Confirmed independently by two firms two years apart - Dentons in "
        "2023 (p019) and Nelson Mullins in 2025 (2025101700864002 p010), "
        "same CRFN 2023000287581. ⚠ HOW IT HOLDS FEE TITLE IS STILL "
        "UNANSWERED and the instrument that would answer it is not here"),
 C("c2023-chelsea-swears", "2023110100486006", "p008", "defect",
   text="⚠ the section 275 affidavit swears 'That I am the Manager of CHELSEA "
        "25 HOTEL LLC ... and LAM GEN 25 LLC ... THE MORTGAGOR UNDER THE "
        "MORTGAGE WHICH IS BEING ASSIGNED' - but the mortgage being assigned "
        "is the 2015 Building Loan Mortgage 'made by LAM GEN 25 LLC' ALONE. "
        "Chelsea 25 Hotel LLC is not a party to that 2015 instrument on its "
        "face",
   eff="2023-10-12", stated="2023-11-06", ans=["TITLE", "IDENTIFY"],
   note="sworn the same week as the gap mortgage that first brings Chelsea 25 "
        "into privity. By October 2023 the drafters treat Chelsea 25 Hotel "
        "LLC and Lam Gen 25 LLC as ONE 'Mortgagor' unit - fee plus leasehold "
        "- even on instruments that predate Chelsea 25 entirely"),
 C("c2023-operating-lessee", "2023110100486011", "p003", "unresolved",
   text="the recorded text names LAM GEN 25 LLC as the 'OPERATING LESSEE' and "
        "CHELSEA 25 HOTEL LLC as the borrower - the security instrument is "
        "'executed by Assignor and LAM GEN 25 LLC ... (Operating Lessee)' and "
        "the loan agreement is 'executed by and between Assignor and "
        "Assignee, AND JOINED BY THE OPERATING LESSEE'",
   eff="2023-10-16", ans=["TENANCY", "TITLE"],
   note="⚠ THIS IS THE STRUCTURE. A fee owner and an operating lessee, both "
        "signing. It is the standard hotel split - propco holds the real "
        "estate, opco holds the operating lease and the franchise. It also "
        "explains the 2007 estate merger in reverse: the estates were merged "
        "to build, then re-split to operate"),

 # ---- 2025: MetLife was PAID IN FULL -------------------------------------
 C("c2025-metlife-paid", "2025101700864001", "p002", "unresolved",
   text="MetLife 'having received FULL PAYMENT of the obligations mentioned "
        "in and secured by that certain Assignment of Leases described on "
        "SCHEDULE I ... does hereby consent that said Assignment of Leases be "
        "terminated' - dated 2025-10-16",
   eff="2025-10-16", stated="2025-10-23", ans=["DEBT", "INCOME"],
   note="⚠ METLIFE WAS TAKEN OUT, NOT MERELY ASSIGNED. The same day it "
        "assigns the mortgages to Deutsche Bank it also terminates its rents "
        "assignment for full payment. This is the terminate-and-rebuild "
        "grammar again (c-tlr-assignment-grammar), now on its fourth "
        "observed cycle: 2013, 2014, 2023, 2025"),
 C("c2025-db-norecourse", "2025101700864002", "p004", "unresolved",
   text="MetLife assigns to Deutsche Bank 'without recourse ... without "
        "covenant, warranty or representation ... including but not limited "
        "to, the enforceability or collectability' - representing only that "
        "it owns the debt, was authorised to assign, and made no prior "
        "conflicting assignment",
   eff="2025-10-16", stated="2025-10-23", ans=["DEBT", "PRIORITY"],
   note="⚠ NO BORROWER-DEFAULT REPRESENTATION ANYWHERE. Across all six "
        "documents and 53 pages, nothing asserts the borrower is not "
        "currently in default. The only sworn statements are 'no new "
        "indebtedness', 'no reloans or readvances' and 'not acting as a "
        "nominee'. Compare the 2013 spreader, which DID carry a dated "
        "no-default representation - the record got weaker over twelve years"),
 C("c2025-275-artifact", "2025101700864002", "p004", "defect",
   text="⚠ two sentences that contradict each other in the same paragraph: "
        "'This Assignment is not subject to the requirements of Section 275 "
        "of the Real Property Law. The assignee set forth on the assignment "
        "of mortgage TO WHICH THIS AFFIDAVIT IS ATTACHED is not acting as a "
        "nominee of the mortgagor' - leftover section 275 affidavit "
        "boilerplate pasted into a document that disclaims section 275, and "
        "there is no affidavit attached",
   eff="2025-10-23", ans=["IDENTIFY"],
   note="a drafting artifact, not a representation. Third instance of the "
        "same species this session, with the 2014 'NINETEEN MILLION' template "
        "carry-over and the 2014 'Termination of Assignment' word swap"),
 C("c2023-gap-tax", "2023110100486011", "p013", "tax_paid",
   num=713_720.00, unit="USD",
   text="'secures additional indebtedness ... in the amount of $25,490,000.00 "
        "... upon which a mortgage tax of $713,720.00 is being paid "
        "simultaneously ... and consolidates the Existing Mortgage with the "
        "Gap Mortgage to form a single lien in the consolidated amount of "
        "$120,000,000.00'",
   eff="2023-11-06", ans=["DEBT", "VALUE"],
   note="$713,720 / $25,490,000 = 2.800% exactly - the commercial rate, paid "
        "on the new money only, with the other $94,510,000 exempt under 255. "
        "The same grammar as 1998, 2007, 2012, 2013, 2014 and 2015"),
 C("c2023-firstlien", "2023110100486011", "p003", "unresolved",
   text="'Loan: A first mortgage loan in an amount of $120,000,000.00 from "
        "Assignee to Assignor'",
   eff="2023-10-16", ans=["PRIORITY", "DEBT"],
   note="an express first-lien statement in the DEFINED TERMS of the "
        "companion instrument - not in the mortgage, which is not in the "
        "corpus"),
 C("c2023-norate-again", "2023110100486011", "p003", "unresolved",
   text="NO interest rate and NO maturity date appear in any of the 53 pages "
        "across all six 2023 and 2025 documents. The Note is defined only as "
        "being 'in the amount of the Loan'",
   eff="2023-10-16", ans=["DEBT"],
   note="⚠ THIRTY-FIVE YEARS UNBROKEN. 1990, 2007, 2013, 2014, 2023, 2025 - "
        "every generation of this lien states its size and withholds its "
        "price. A decoder that expects to find a rate in ACRIS will never "
        "find one on this parcel"),
 C("c2025-marriott-silent", "2025101700864002", "p001", "unresolved",
   text="NO mention of Marriott, a franchise agreement, or a right of first "
        "refusal appears anywhere in the 2023 or 2025 paperwork - all 53 "
        "pages read. 'Renaissance Chelsea' appears only as a running page "
        "footer, not as a party or a contractual reference",
   eff="2025-10-23", ans=["ENCUMBRANCE", "TENANCY"],
   note="⚠ THE 2014 SUBORDINATION IS CONDITIONAL - Marriott's ROFR is "
        "subordinate only 'for so long as ... the Bank is not a Competitor or "
        "Affiliate of a Competitor'. Two lender changes have since occurred "
        "and NEITHER addresses that condition on the record. ⚠ The running "
        "footer is the only trace in the current paperwork that this is a "
        "branded hotel at all"),
 C("c2023-lender-chain-end", "2025101700864002", "p004", "party_role",
   text="the current holder is DEUTSCHE BANK AG, NEW YORK BRANCH, taking "
        "assignment from MetLife Commercial Mortgage Originator LLC on "
        "2025-10-16, recorded 2025-10-23 as CRFN 2025000287678",
   eff="2025-10-16", stated="2025-10-23",
   parties=["DEUTSCHE BANK AG, NEW YORK BRANCH (assignee)",
            "METLIFE COMMERCIAL MORTGAGE ORIGINATOR, LLC (assignor)",
            "Brett Ulrich (Senior Director, MetLife Commercial Mortgage "
            "Income Fund GP, LLC - signs for the assignor)"],
   ans=["DEBT", "CONSENT"],
   note="THIRTEEN HOLDERS, THIRTY-FIVE YEARS, ONE LIEN: Apple Bank -> Queens "
        "County Savings -> New York Community -> Anglo Irish -> Irish Bank "
        "Resolution -> LSREF2 Clover Trust -> Wells Fargo -> LSREF2 Clover "
        "Trust -> UBS -> Goldman Sachs -> Shanghai Commercial -> MetLife -> "
        "Deutsche Bank"),
 C("ev-00345899", "FT_1990000345899", "p001", "party_role",
   text="112 WEST 25 COMPANY sold the mortgage to APPLE BANK FOR SAVINGS",
   eff="1900-01-01", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ASST. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01040002", "2010102601040002", "p001", "party_role",
   text="COMMONWEALTH LAND TITLE INSURANCE COMPANY certified who held every interest in the zoning lot",
   eff="2010-10-14", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type CERT. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00841001", "2011112200841001", "p001", "party_role",
   text="LSREF2 CLOVER TRUST 2011 sold the mortgage to WELLS FARGO NATIONAL ASSOCIATION",
   eff="2011-11-08", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ASST. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00888001", "2011112200888001", "p001", "party_role",
   text="IRISH BANK RESOLUTION CORPORATION LIMITED transferred the rents assignment to LSREF2 CLOVER TRUST 2011",
   eff="2011-11-08", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type AALR. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00913001", "2011112200913001", "p001", "party_role",
   text="LSREF2 CLOVER TRUST 2011 transferred the rents assignment to WELLS FARGO BANK NATIONAL ASSOCIATION",
   eff="2011-11-08", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type AALR. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00666002", "2012101500666002", "p001", "party_role",
   text="WELLS FARGO BANK, NATIONAL ASSOCIATION transferred the rents assignment to LSRFEF2 CLOVER TRUST 2011",
   eff="2012-10-05", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type AALR. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00666003", "2012101500666003", "p001", "party_role",
   text="LSRFEF2 CLOVER TRUST 2011 released its claim on the rents in favour of 112-118 WEST 25TH LLC",
   eff="2012-10-05", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type TL&R. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00666004", "2012101500666004", "p001", "party_role",
   text="WELLS FARGO BANK, NATIONAL ASSOCIATION sold the mortgage to LSRFEF2 CLOVER TRUST 2011",
   eff="2012-10-05", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ASST. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00666005", "2012101500666005", "p001", "party_role",
   text="LSRFEF2 CLOVER TRUST 2011 sold the mortgage to UBS REAL ESTATE SECURITIES INC.",
   eff="2012-10-05", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ASST. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01550001", "2012122701550001", "p001", "party_role",
   text="COMMONWEALTH LAND TITLE TITLE INSURANCE COMPANY certified who held every interest in the zoning lot",
   eff="2012-12-07", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type CERT. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01550004", "2012122701550004", "p001", "party_role",
   text="UBS REAL ESTATE SECURITIES INC. recorded an agreement affecting the property with",
   eff="2012-12-14", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type SAGE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01550002", "2012122701550002", "p001", "party_role",
   text="THE HORNE BUILDING OWNERS CORP. (and 1 other) recorded an agreement affecting the property with",
   eff="2012-12-19", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type SAGE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01674001", "2013052101674001", "p001", "party_role",
   text="COMMONWEALTH LAND TITLE INSURANCE COMPANY certified who held every interest in the zoning lot",
   eff="2013-05-17", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type CERT. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01674005", "2013052101674005", "p001", "party_role",
   text="COMMONWEALTH LAND TITLE INSURANCE COMPANY certified who held every interest in the zoning lot",
   eff="2013-05-17", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type CERT. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00681001", "2015043000681001", "p001", "party_role",
   text="LAM GEN 25 LLC (and 1 other) recorded an agreement affecting the property with",
   eff="2015-04-29", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type SAGE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01826001", "2015051301826001", "p001", "party_role",
   text="LAM GEN 25 LLC filed a zoning lot description covering the assembled lots",
   eff="2015-05-12", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ZONE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00388001", "2015052900388001", "p001", "party_role",
   text="FIDELITY NATIONAL TITLE INSURANCE COMPANY OF NY certified who held every interest in the zoning lot",
   eff="2015-05-22", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type CERT. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01338001", "2015101301338001", "p001", "party_role",
   text="LAM GEN 25 LLC filed a zoning lot description covering the assembled lots",
   eff="2015-10-12", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ZONE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-01066001", "2016060801066001", "p001", "party_role",
   text="MARRIOTT INTERNATIONAL, INC. recorded an agreement affecting the property with",
   eff="2016-05-13", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type SAGE. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00486003", "2023110100486003", "p001", "party_role",
   text="SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH released its claim on the rents in favour of LAM GEN 25 LLC",
   eff="2023-10-16", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type TL&R. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00486004", "2023110100486004", "p001", "party_role",
   text="SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH released its claim on the rents in favour of LAM GEN 25 LLC",
   eff="2023-10-16", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type TL&R. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),
 C("ev-00486007", "2023110100486007", "p001", "party_role",
   text="SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH sold the mortgage to METLIFE COMMERCIAL MORTGAGE ORIGINATOR LLC",
   eff="2023-10-16", ev="index", ans=["IDENTIFY"],
   note="event claim generated from the ACRIS index — type ASST. ⚠ Every recorded document did something; a document with no claim is a decoder failure, not an empty instrument"),

 C("c2010-zlda-price", "2010102601040006", "p001", "consideration",
   num=5_000_000, unit="USD",
   text="THE 2010 AIR-RIGHTS PRICE. The ZLDA cover page is typed "
        "'DEVELOPMENT RIGHTS' and carries two PREPAID stamps: NYC RPTT "
        "$131,250.00 (Ref# 2010000376481) and NYS RETT $20,000.00 (Ref# "
        "3801156). $131,250 / 2.625% = $5,000,000 and $20,000 / 0.400% = "
        "$5,000,000",
   eff="2010-10-14", stated="2010-11-16", ev="derived",
   ans=["VALUE", "ENVELOPE"],
   note="TWO INDEPENDENT WITNESSES. BUNDLED across lots 53, 55 and 56 - one "
        "stamp pair for the whole four-lot transaction, no per-lot breakout. "
        "$5,000,000 / 53,578 sf = $93.32 per buildable square foot, against "
        "$135 and $125 a foot for lots 22 and 21 three years later"),
 C("c2010-price-hidden", "2010102601040006", "p096", "defect",
   text="⚠ THE PRICE IS KEPT OFF THE RECORD BY DESIGN. Exhibit H is a "
        "'Memorandum of DEVELOPMENT RIGHTS PURCHASE AND SALE AGREEMENT' "
        "dated December 2009 which states no price - 'reference should be "
        "made to the Contract' - and Exhibit I is a prepared 'Termination of "
        "Memorandum' that releases even that notice at closing",
   eff="2010-10-14", ans=["VALUE", "IDENTIFY"],
   note="⚠ A MEMORANDUM GIVES NOTICE A CONTRACT EXISTS WHILE RECORDING NONE "
        "OF ITS TERMS, AND THE TERMINATION ERASES THE NOTICE. So the ONLY "
        "route to an air-rights price in this corpus is the tax stamp. Both "
        "exhibits are UNEXECUTED blank forms",
   supersedes="c2010-zlda-missing"),
 C("c2010-lav-easement", "2010102601040006", "p008", "easement",
   subject="1008000053", vfrom=23.0, vdatum="curb level", dur="perpetual",
   hext="20 feet north of the lot 53 rear lot line",
   text="'120 Owner hereby grants to Developer a perpetual easement for "
        "LIGHT, AIR AND VIEW above the portion of the 120 Owner Land "
        "beginning at the rear lot line and extending ... a distance of "
        "TWENTY (20') FEET to the north of such rear lot line, beginning at "
        "a height of TWENTY-THREE (23') FEET above curb level' - with 120 "
        "Owner permitted to keep its existing building in the easement area",
   eff="2010-10-14", ans=["ENCUMBRANCE", "ENVELOPE"],
   note="⚠ ONE-DIRECTIONAL: lot 53 burdened, lot 49 benefited, NOT mutual. "
        "And the grant is from 120 Owner (lot 53) ONLY - no light/air/view "
        "grant from 124-26 W 25 Street LLC for lots 55 or 56 exists anywhere "
        "in the 110 pages"),
 C("c2010-form-drops-view", "2010102601040006", "p093", "defect",
   text="⚠ THE UNEXECUTED FORM DROPS 'VIEW' AND CHANGES THE METRICS. Exhibit "
        "F, 'Form of Light and Air Easement', says only 'The right to "
        "unrestricted light and air over Parcel A' with no view, and "
        "references Manhattan Datum before demolition versus 23 feet above "
        "curb after",
   eff="2010-10-14", ans=["ENCUMBRANCE", "IDENTIFY"],
   note="the operative body text and the annexed form disagree on what was "
        "granted. The form binds only 'if requested in writing by Developer' "
        "- contingent, not live"),
 C("c2010-pagecount-three", "2010102601040006", "p001", "defect",
   text="⚠ THREE DIFFERENT PAGE COUNTS, NONE AGREEING. The cover header says "
        "'PAGE 1 OF 116', a separate field says 'Document Page Count: 114', "
        "and 110 images exist on disk",
   eff="2010-11-16", ans=["IDENTIFY"],
   note="⚠ my integrity check assumes ONE authoritative count per cover. "
        "This document has two that disagree with each other AND with disk"),

 C("c2019-chart", "2019071700601003", "p044", "envelope_balance",
   num=390_160, unit="sf",
   text="the 2019 Development Rights Chart, Exhibit D row 6 'Allocation of "
        "Development Rights After Transfer (sf)': Lot 49 Land 141,929 · Lot "
        "50 Land 127,035 · TOTAL across all nine combined-lot parcels 390,160",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ THE NINE-LOT TOTAL IS 390,160 sf, NOT 268,964. My chain closed "
        "141,929 + 127,035 = 268,964 and that is the LOT 49 + LOT 50 SHARE; "
        "the other seven lots retain 121,196 sf between them. A separate row "
        "5 gives 'Lot 49/50 Excess Development Rights' of 56,659 (lot 49) and "
        "55,915 (lot 50) — excess-only, a different scope, not a conflict"),
 C("c2019-upzoning", "2019071700601003", "p015", "easement",
   text="upzoning and downzoning reallocate by formula: on an Upzoning 'Lot "
        "50 Owner shall be entitled to 45.48% of the Development Rights "
        "resulting from such Upzoning ... and Lot 49 Owner shall be entitled "
        "to 54.52%'. The trigger is 'a validly enacted amendment of the "
        "Zoning Resolution', or a casualty following a Downzoning",
   eff="2019-05-20", ans=["ENVELOPE"],
   note="⚠ A VARIABLE ENVELOPE. Any future rezoning of this block splits "
        "45.48/54.52 automatically. Section III otherwise bars cross-draw: "
        "each owner 'shall retain all rights in and to' its own rights, so "
        "neither lot may borrow from the other in normal operation"),
 C("c2019-nonarms", "2019071700601003", "p001", "defect",
   text="the 2019 subdivision paid ZERO transfer tax — NYC RPTT $0.00 and NYS "
        "RETT $0.00 — because grantor LAM GEN 25 LLC and grantee LG CHELSEA "
        "LLC are both 'c/o Lam Generation LLC' and Jeffrey Lam signed for "
        "BOTH as Authorized Signatory",
   eff="2019-05-20", ans=["VALUE", "TITLE"],
   note="⚠ COMMONLY-CONTROLLED ALLOCATION, NOT A SALE. So no price can be "
        "derived here — the stamp arithmetic that works on every arm's-length "
        "transfer in this corpus returns nothing, and that is the correct "
        "answer rather than a failure. ⚠ Only ONE of the two acknowledgment "
        "blocks on p025 was notarised"),

 C("c2013-lam-purchase", "2013080901116003", "p001", "consideration",
   num=67_500_000, unit="USD",
   text="LAM GEN 25 LLC BOUGHT THE PARCEL FOR $67,500,000 on 2013-08-07. "
        "Cover tax block: 'NYC Real Property Transfer Tax: $1,771,875.00' "
        "and 'NYS Real Estate Transfer Tax: $270,000.00'. $1,771,875 / "
        "2.625% = $67,500,000 and $270,000 / 0.400% = $67,500,000",
   eff="2013-08-07", stated="2013-08-27", ev="derived",
   parties=["112-118 WEST 25TH LLC (grantor)", "LAM GEN 25 LLC (grantee)"],
   ans=["VALUE", "TITLE"],
   note="⚠ THE ACQUISITION PRICE I NEVER HAD. I recorded the 2007 purchase "
        "at $42,700,000 and the 2023 recapitalisation at $120,000,000 and "
        "never knew what Lam paid. TWO WITNESSES AGREE EXACTLY and the ACRIS "
        "index carries the same figure. ⚠ THE DOCUMENT WAS NEVER READ BY ANY "
        "AGENT — it was not on the hand-built work list. $67.5M in 2013 "
        "against $42.7M in 2007 is the assemblage premium: six years and "
        "seven air-rights purchases later"),
 C("c2023-chelsea-DEED", "2023110100486001", "p001", "conveyance",
   text="⚠ THE DEED INTO CHELSEA 25 HOTEL LLC EXISTS. Cover page: "
        "'GRANTOR/SELLER: LAM GEN 25 LLC' and 'GRANTEE/BUYER: CHELSEA 25 "
        "HOTEL LLC', MANHATTAN 800 49 Entire Lot, recorded 11-06-2023 10:10, "
        "CRFN 2023000287573",
   eff="2023-10-16", stated="2023-11-06",
   parties=["LAM GEN 25 LLC (grantor)", "CHELSEA 25 HOTEL LLC (grantee)"],
   ans=["TITLE"],
   note="⚠ RETRACTS MY CONCLUSION THAT NO DEED EXISTS. I told the user the "
        "fee moved by an 'Owner Agreement dated October 16, 2023' because a "
        "franchise memorandum recited that phrase and no deed had been "
        "found. The deed was in the index the whole time, eight pages, in "
        "the same batch three agents read around. ⚠ NONE OF THEM WAS GIVEN "
        "486001 — the hand-built work list was the defect, exactly as it was "
        "for the five 'missing' instruments. The Owner Agreement is real and "
        "is a SEPARATE instrument; it did not replace the deed"),
 C("c2023-chelsea-zero", "2023110100486001", "p001", "tax_paid",
   num=0.0, unit="USD",
   text="the deed into Chelsea 25 Hotel LLC paid ZERO transfer tax — 'NYC "
        "Real Property Transfer Tax: $0.00' and 'NYS Real Estate Transfer "
        "Tax: $0.00' — with only a $250.00 filing fee and $52.00 recording "
        "fee",
   eff="2023-11-06", ans=["VALUE", "TITLE"],
   note="⚠ A $0/$0 STAMP PAIR IS A POSITIVE FINDING, NOT A MISSING PRICE. It "
        "identifies a commonly-controlled transfer — LG 25 Hotel DE LLC is "
        "the managing member of BOTH Lam Gen 25 and Chelsea 25 Hotel, and "
        "Jeffrey Lam signs for both. So the propco/opco split was an "
        "internal reorganisation ahead of the MetLife financing, not a sale, "
        "and NO PRICE EXISTS TO FIND. Saying so is the answer"),

 C("c2013-deed-recital", "2013080901116003", "p002", "consideration_recited",
   num=10, unit="USD",
   text="'WITNESSETH, that Grantor, in consideration of TEN DOLLARS ($10.00) "
        "and other valuable consideration paid by Grantee, the receipt and "
        "sufficiency of which are hereby acknowledged, does hereby grant and "
        "release unto Grantee'",
   eff="2013-08-07", ans=["VALUE"],
   note="⚠ THE TRAP, CONFIRMED AT SCALE. $10 recited against $67,500,000 of "
        "stamps on the same document — a 6,750,000x error for anyone reading "
        "the grant instead of the cover. Proof "
        "proofs/51ee410748d55a7a.png"),
 C("c2013-deed-nocovenants", "2013080901116003", "p002", "unresolved",
   text="⚠ THIS DEED IS A 'BARGAIN AND SALE DEED WITHOUT COVENANTS' — the "
        "title says so outright. Its ONLY covenant is the statutory Lien Law "
        "section 13 trust-fund clause: Grantor 'will receive the "
        "consideration for this conveyance and will hold the right to "
        "receive such consideration as a trust fund'",
   eff="2013-08-07", ans=["TITLE"],
   note="⚠ MATERIALLY WEAKER THAN THE 2007 DEED ON THE SAME LAND, which was "
        "a 'Bargain and Sale Deed WITH Covenant Against Grantor's Acts'. "
        "Extell gave Lam LESS warranty than Edelman gave Extell — the "
        "grantor does not even promise it has not itself encumbered the "
        "property. Two deeds, six years apart, that read identically as "
        "prose and differ where it counts. Proof "
        "proofs/ea19b03e1ce47ddc.png"),
 C("c2013-deed-devrights", "2013080901116003", "p002", "easement",
   text="the grant expressly carries the assemblage: 'TOGETHER with any "
        "rights of way, appendages, appurtenances, easements, sidewalks, "
        "alleys, gores or strips of land adjoining or appurtenant to the "
        "above described premises and used in conjunction therewith, ANY "
        "DEVELOPMENT RIGHTS APPURTENANT to the above described premises'",
   eff="2013-08-07", ans=["ENVELOPE", "TITLE"],
   note="⚠ THE 2007 DEED SAID NOTHING ABOUT DEVELOPMENT RIGHTS — I recorded "
        "that absence as a finding. By 2013 the assemblage existed (53,578 "
        "sf in 2010, 22,845 in 2012, three more transfers in 2013) and the "
        "deed conveys it explicitly. THE DEED LANGUAGE TRACKS WHAT THE "
        "PARCEL HAD BECOME. Proof proofs/288af62f05938866.png"),
 C("c2013-deed-prior", "2013080901116003", "p002", "cross_reference",
   text="'The premises herein described are intended to be the same, no "
        "more, no less, as that described in: Deed recorded in "
        "CRFN2007000336512'",
   eff="2013-08-07", ans=["TITLE"],
   note="a clean prior-deed recital pointing at the 2007 Edelman-to-Extell "
        "conveyance — ⚠ CONTRAST THE 1998 DEED, whose recital fused the date "
        "of one 1971 instrument with the reel/page of another running the "
        "opposite way. Proof proofs/2b600143b0830623.png"),
 C("c2013-deed-nosubject", "2013080901116003", "p002", "unresolved",
   text="⚠ NO 'SUBJECT TO' CLAUSE AND NO SCHEDULE OF PERMITTED EXCEPTIONS. "
        "The whole grant was read: parties, witnesseth, the Exhibit A "
        "reference, the two TOGETHER-WITH clauses, habendum, Lien Law 13, "
        "signature line. Nothing is taken subject to",
   eff="2013-08-07", ans=["TITLE", "ENCUMBRANCE"],
   note="⚠ THE SAME ABSENCE AS THE 2007 DEED. A $67,500,000 conveyance of a "
        "parcel carrying seven air-rights agreements, a Marriott franchise "
        "ROFR and a $40,500,000 mortgage discloses NONE of it. ABSENT is a "
        "finding here, not a gap — anyone representing that the deed shows "
        "the encumbrances is wrong twice over"),
 C("c2013-deed-handwritten", "2013080901116003", "p002", "defect",
   text="the transfer tax is written by hand in the left margin — 'TT "
        "270,000' — alongside the typed body",
   eff="2013-08-07", ans=["VALUE", "IDENTIFY"],
   note="⚠ IT CORROBORATES THE COVER STAMP ($270,000 NYS RETT) AND NO OCR "
        "REACHES IT. Fifth instance on this parcel of a material figure "
        "existing only as handwriting — after the 2003 and 2014 prior-tax "
        "affidavits, the 2013 and 2014 new-money splits, and the 2012 "
        "$1,000 schedule conflict"),
 # ---- 2025 --------------------------------------------------------------
 C("c2025-mtge", "2025101700864003", None, "mortgage", num=3_000_000, unit="USD",
   eff="2025-10-16", stated="2025-10-23", ev="index", ans=["CAPITAL", "ENCUMBER"]),
 C("c2025-cons", "2025101700864004", None, "consolidation", num=123_000_000,
   unit="USD", eff="2025-10-16", ev="index", ans=["CAPITAL"],
   note="the position today"),

 # =======================================================================
 # ADDED BY THE DIFF, 2026-08-06. The first run found 24 figures asserted in
 # the prose with no backing claim. Most were REAL FACTS I had buried inside
 # another claim's note instead of claiming them — a tax stamp written as
 # prose is not queryable, cannot be checked, and cannot be superseded when
 # a rate table is corrected. That is precisely the failure this table
 # exists to prevent, committed inside the table itself on the first pass.
 # =======================================================================

 # the tax stamps — each one is a MEASUREMENT, and every derived price
 # depends on it. They belong in the table, not in a parenthesis.
 C("t1998-mrt", "FT_1710006669171", None, "tax_paid", num=4_527.56, unit="USD",
   text="mortgage recording tax, handwritten margin note 'MT $4527.56'",
   eff="1998-11-24", ans=["CAPITAL"]),
 C("t2010-rptt", "2010102601040006", "p001", "tax_paid", num=131_250.00,
   unit="USD", text="NYC RPTT", eff="2010-10-14", ans=["VALUE"]),
 C("t2010-rett", "2010102601040006", "p001", "tax_paid", num=20_000.00,
   unit="USD", text="NYS RETT", eff="2010-10-14", ans=["VALUE"]),
 C("t2012-rptt", "2012122701550003", "p001", "tax_paid", num=121_135.61,
   unit="USD", text="NYC RPTT", eff="2012-12-19", ans=["VALUE"]),
 C("t2012-rett", "2012122701550003", "p001", "tax_paid", num=18_460.00,
   unit="USD", text="NYS RETT — implies $4,615,000, the $500-rounded window",
   eff="2012-12-19", ans=["VALUE"]),
 C("t2013b-rptt", "2013052101674008", "p001", "tax_paid", num=35_181.56,
   unit="USD", text="NYC RPTT", eff="2013-05-17", ans=["VALUE"]),
 C("t2013-rptt", "2013080901116003", "p001", "tax_paid", num=1_771_875.00,
   unit="USD", text="NYC RPTT on the $67.5M sale", eff="2013-08-07",
   ans=["VALUE"]),
 C("t2013-rett", "2013080901116003", "p001", "tax_paid", num=270_000.00,
   unit="USD", text="NYS RETT, margin note 'TT 270,000'", eff="2013-08-07",
   ans=["VALUE"]),
 C("t2020-mrt", "2020081400407001", "p001", "tax_paid", num=140_000.00,
   unit="USD", text="mortgage recording tax", eff="2020-08-05", ans=["CAPITAL"]),
 C("t2023-mrt", "2023110100486009", "p001", "tax_paid", num=713_720.00,
   unit="USD", text="mortgage recording tax, all seven components verified",
   eff="2023-10-16", ans=["CAPITAL"]),

 # the consolidation POSITIONS — the answer to "what debt is on it", which
 # the first pass stated in prose and never claimed
 C("p2012-pos", "2012101500666007", None, "consolidation", num=39_000_000,
   unit="USD", eff="2012-10-05", ev="index", ans=["CAPITAL"]),
 C("p2013-pos", "2013081200922003", None, "consolidation", num=40_500_000,
   unit="USD", eff="2013-08-07", ev="index", ans=["CAPITAL"]),
 C("p2014-pos", "2014112601161005", None, "consolidation", num=48_000_000,
   unit="USD", eff="2014-11-25", ev="index", ans=["CAPITAL"]),
 C("p2018-pos", "2018113000347001", None, "consolidation", num=48_000_000,
   unit="USD", eff="2018-11-19", ev="index", ans=["CAPITAL"],
   note="⚠ LOWER than the 2015 pledge of $113,710,000 — the construction loan "
        "was retired after the hotel opened. A falling position is a finding, "
        "not an error, but it is only visible because both are claimed"),

 # the small mortgages, asserted in prose and never claimed
 C("m2012-new", "2012101500666006", None, "mortgage", num=1_607_226, unit="USD",
   eff="2012-10-05", ev="index", ans=["CAPITAL", "ENCUMBER"]),
 C("m2013-new", "2013081200922002", None, "mortgage", num=1_500_000, unit="USD",
   eff="2013-08-07", ev="index", ans=["CAPITAL", "ENCUMBER"]),

 # the construction loan is TWO instruments. Claiming only the $65,710,000
 # sum hid which document carries which half.
 C("m2015a", "2015091001439003", None, "mortgage", num=31_930_000, unit="USD",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "ENCUMBER"]),
 C("m2015b", "2015091001439004", None, "mortgage", num=33_780_000, unit="USD",
   eff="2015-09-02", ev="index", ans=["CAPITAL", "ENCUMBER"]),

 # the lot 20 airspace footprint, previously only inside a note
 C("c2013c-lower", "2013080901116002", "p040", "lot_area", num=2_912, unit="sf",
   subject="1008000020", eff="2013-08-07", ans=["PARCEL"],
   note="'Lower Parcel Land' — the footprint under the transferred airspace"),
]

# causality — never stated by any document, so always labelled inferred
EDGES = [
 ("c2007-2p3m-answer", "c2007-unres", "SUPERSEDES", "read",
  "the $2,300,000 is the sublease assignment price, proven three ways; the earlier claim says the figure corresponds to nothing and the page was not read"),
 ("c2013-taxcredit-correct", "c-taxcredit-drift", "CORRECTS", "read",
  "the prior-tax figures do not drift upward — the 2013 schedule has them right, so it is two wrong affidavits with a correct one between them"),
 ("c2013-plane-both-sides", "c2013-plane-upper", "SUPERSEDES", "read",
  "both sides of the 130-foot plane quoted from one document"),
 ("c2013-plane-both-sides", "c2012-lot20-plane", "SUPERSEDES", "read",
  "the bare '(lower limiting plane)' parenthetical is the loosest of three descriptions of the same plane"),
 ("c2013-plane-both-sides", "c2019-lot20-elevation", "SUPERSEDES", "read",
  "the 2019 Lower Parcel / Air Space split describes the same plane from the other side"),
 ("c2013-plane-both-sides", "c2013-plane-RESOLVED", "CORRECTS", "read",
  "⚠ MY OWN FIRST RESOLUTION WAS HALF RIGHT. Lot 49 took the development rights from BELOW the plane AND a light/air/view easement ABOVE it — both, not one"),
 ("c2013-deed-vs-survey-early", "c1990-legal-conflict", "RETRACTS", "read",
  "not a defect — '82 feet 10 inches (deed) (82 feet 8 3/4 inches - survey)' are two measurement conventions printed side by side"),
 ("c2013-deed-vs-survey-early", "c2010-legal-conflict-again", "RETRACTS", "read",
  "same conventions, same non-defect"),
 ("c2019-deed-vs-survey", "c2013-deed-vs-survey-early", "CORROBORATES", "read",
  "the 2019 survey prints both conventions again, six years later"),
 ("c2013-lot22-price", "c2013-zldas-missing", "RETRACTS", "read",
  "⚠ the ZLDAs were never missing — they were on disk the whole time and carry the prices"),
 ("c2010-price-hidden", "c2010-zlda-missing", "RETRACTS", "read",
  "⚠ the 2010 ZLDA is document 2010102601040006, 110 pages, on disk"),
 ("c2023-owner-agreement", "c2023-chelsea-entry", "SUPERSEDES", "read",
  "the conveyance is named: an Owner Agreement dated October 16, 2023, not a deed"),
 ("c2023-owner-agreement", "c2023-cema-missing", "RETRACTS", "read",
  "⚠ the $120,000,000 CEMA is document 2023110100486010, 45 pages, on disk"),
 ("c2018-splitter-severs", "c2018-indexdefect", "CORRECTS", "read",
  "the City corrected the indexing in 2020 — the remark reads 'CORRECTED TO ADD LOT 49 ... UPDATED 8/19/20', so a BBL pull no longer misses it"),
 ("c2025-maxsecured", "c2023-reconcile", "CORROBORATES", "read",
  "the $85,000,000 reconstructed from balances is stated outright under RPL 254 in the 2025 mortgage"),
 ("c2007-mtge", "c2007-price", "FINANCES", "inferred", "same batch, same day"),
 ("c2010-rights", "c2013-price", "ENABLES", "inferred",
  "the assembled envelope is what was sold in 2013"),
 ("c2012-rights", "c2013-price", "ENABLES", "inferred", ""),
 ("c2013a-rights", "c2013-price", "ENABLES", "inferred", ""),
 ("c2013b-rights", "c2013-price", "ENABLES", "inferred", ""),
 ("c2013c-rights", "c2013-price", "ENABLES", "inferred", ""),
 ("m2015a", "c2019-subdiv", "ENABLES", "inferred",
  "the tower was built before the site was divided. ⚠ REPOINTED from the "
  "removed $65,710,000 aggregate claim — deleting a claim orphans its edges, "
  "and the assert caught it. Referential integrity is why edges are a table "
  "and not a sentence"),
 ("c2003-xref", "c1990-reel", "CROSS_REFERENCES", "stated", "reel and page"),
 ("c2023-xref", "c1990-reel", "CROSS_REFERENCES", "stated", "reel and page"),
 ("c2015-confirm", "c2010-rights", "CROSS_REFERENCES", "stated", "CRFN"),
 ("c2019-contra", "c2019-subdiv", "CONTRADICTS", "stated",
  "2018 lot 50 filings predate the instrument that describes the split"),
 ("c2014-lot20", "c2010-rights", "CONTRADICTS", "inferred",
  "'the 2010 ZLDA began the assemblage' is false — lot 20's is 2008"),
 ("c2019-demolished", "c2016-delivery-pluto", "CONTRADICTS", "stated",
  "a 2019 instrument says lot 49 was a cleared site; PLUTO says built 2016"),
 ("c1971-area", "c2019-l49area", "SUPERSEDES", "stated",
  "15,642 -> 15,639 by resurvey, then 8,527 by subdivision"),
]


WHOLE_LOT_BY_NATURE = {"lot_area", "rights_transferred", "rights_retained",
                       "rights_generated", "unit_cap", "boundary_origin"}


def rows():
    """Claims, with whole-lot geometry made EXPLICIT rather than left null.

    ⚠ THIS IS A DEFAULT AND IT IS DECLARED, NOT SILENT. A lot area, a rights
    transfer, and a unit cap all apply to the entire parcel — there is no band
    or elevation to record. But leaving region_scope null would make them
    indistinguishable from the easement rows whose geometry we simply had not
    written down yet, which is the exact confusion DECODE_EXACTNESS.md forbids.

    So the default is applied here, stamped `derivation`, and reported. If a
    future document says a rights transfer came from PART of a lot — which
    happens on through-block splits — the explicit value overrides this and the
    stamp disappears.
    """
    out = []
    for c in CLAIMS:
        c = dict(c)
        if c["predicate"] in WHOLE_LOT_BY_NATURE and not c.get("region_scope"):
            c["region_scope"] = "WHOLE_LOT"
            c["h_from"] = "the entire parcel"
            c["duration"] = c.get("duration") or "PERPETUAL"
            c["derivation"] = ((c.get("derivation") or "") +
                               " [region defaulted to WHOLE_LOT: this predicate "
                               "has no sub-lot geometry by nature]").strip()
        out.append(c)
    return out


def chronology(claims, axis="effective"):
    """Order by when things HAPPENED, not when the record learned of them."""
    return sorted(claims, key=lambda c: (c[axis] or "9999", c["document_id"]))


def render_narrative(claims):
    """Prose as a FUNCTION of claims. Never written beside them — see
    DECODE_SHAPE.md section 3 for the failure that forced this."""
    T = {
     "conveyance":  "{text}",
     "consideration": "for ${num:,.0f}",
     "rights_transferred": "{num:,.0f} sf of development rights move",
     "envelope_balance": "envelope now {num:,.0f} sf",
     "mortgage": "borrows ${num:,.0f}",
     "consolidation": "position consolidated at ${num:,.0f}",
     "subdivision": "{text}",
     "easement": "easement: {text}",
     "unit_cap": "capped at {num:.0f} dwelling units",
     "person": "{text}",
     "unresolved": "UNRESOLVED — {text}",
    }
    out = []
    for c in chronology(claims):
        t = T.get(c["predicate"])
        if not t:
            continue
        try:
            s = t.format(num=c["value_num"], text=c["value_text"] or "")
        except (TypeError, ValueError):
            continue
        if not s.strip() or s.strip() == "":
            continue
        subj = "" if c["subject_bbl"] == L49 else f" [lot {c['subject_bbl'][-3:].lstrip('0')}]"
        out.append(f"{c['effective']}  {s}{subj}   ({c['document_id']}"
                   f"{' ' + c['page'] if c['page'] else ''}, {c['evidence']})")
    return out


FUNCTIONS = [
 ("ENVELOPE", "WHAT CAN BE BUILT",
  "Every instrument that moved, granted, or restricted floor area. This is the "
  "one narrative that cannot be reconstructed from zoning alone — the Zoning "
  "Resolution gives the RULE, these documents give what was actually bought, "
  "sold and given up under it."),
 ("CAPITAL", "THE MONEY BEHIND IT",
  "Borrowings, consolidations and positions. Read chronologically this is a "
  "single 33-year chain; read as face amounts it is nonsense."),
 ("ENCUMBER", "WHAT IS RECORDED AGAINST IT",
  "Mortgages, easements, declarations and caps. The register of everything a "
  "buyer would inherit."),
 ("TITLE", "WHO HAS CONTROLLED IT",
  "The chain of ownership, and where it changes hands without changing hands."),
 ("VALUE", "WHAT IT HAS BEEN WORTH",
  "Prices actually paid, and the tax stamps they were recovered from."),
 ("PARTY", "WHO THE PEOPLE ARE",
  "Entities from deeds, humans from mortgage jurats, consenting lenders from "
  "certifications — the reach ladder as the record supplies it."),
 ("PARCEL", "WHAT THE LOT ITSELF IS",
  "Boundary, area, and lineage — including the two occasions the parcel's own "
  "identity changed."),
]


def render_by_function(claims):
    """The narrative organised by FUNCTION, not by date.

    LOGIN, 2026-08-06: "a standard timeline following ACRIS chronologically, but
    then an organised approach on the FUNCTION it serves in a narrative — all
    the capital implications, the envelope implications, the encumbrance
    implications. The function of the documents and their decoded results is the
    bread and butter."

    Both readings come from the same claims. Chronological answers "what
    happened here"; functional answers "what do I need to know about X". A
    document appears in as many sections as it has answers — the Brick Farms
    ZLDA is in ENVELOPE, VALUE, ENCUMBER and PARTY, because it genuinely does
    four things and filing it under one would lose three.
    """
    out = []
    for key, title, blurb in FUNCTIONS:
        sel = [c for c in chronology(claims) if key in c["answers"]]
        if not sel:
            continue
        out.append((key, title, blurb, sel))
    return out


GEOMETRIC = {"easement", "unit_cap", "rights_transferred", "lot_area",
             "boundary_origin"}


def geometry_gaps(claims):
    """Claims whose PREDICATE implies a region but which record none.

    ⚠ This is the check that would have caught the constraint bug before it
    shipped. A geometric fact with null geometry is not "no geometry" — it is an
    unrecorded one, and the two must never look alike.

    rights_transferred and lot_area are listed as geometric because a quantity
    of floor area is bounded by SOMETHING; where that something is just "the
    lot", scope=WHOLE_LOT says so explicitly rather than by silence.
    """
    return [c for c in claims
            if c["predicate"] in GEOMETRIC and not c.get("region_scope")]


def diff_against_prose(claims, path="LOT49_EVENTS.md"):
    """THE TEST. Every number in the prose must be backed by a claim.

    ⚠ A CLEAN DIFF WOULD BE THE BAD RESULT. The hand-written ledger is known to
    contain omissions and one wrong date; if the claim set reproduces it exactly,
    the claim set inherited them rather than being derived independently.
    """
    txt = (HERE / path).read_text(encoding="utf-8")
    # dollar figures and sf figures the prose asserts
    prose_nums = set()
    for m in re.finditer(r"\$([\d,]{4,})", txt):
        prose_nums.add(float(m.group(1).replace(",", "")))
    for m in re.finditer(r"\b([\d]{1,3}(?:,\d{3})+)\s*sf\b", txt):
        prose_nums.add(float(m.group(1).replace(",", "")))
    # ⚠ MATCH ON THE INTEGER PART. The first run reported $127,795.81 as both
    # "unbacked in prose" and "unnarrated in claims" — the prose writes
    # $127,795.81 and the regex captured 127,795 while the claim held
    # 127795.81. A diff that flags the SAME number on both sides is not
    # reporting a gap, it is reporting its own rounding. Three of the 24
    # "findings" in the first run were this.
    claim_nums = {int(c["value_num"]) for c in claims if c["value_num"]}
    prose_ints = {int(n) for n in prose_nums}

    # aggregates are computed FROM claims by a view; they are correctly absent
    # from the claim table and must not be reported as gaps
    # Figures the PROSE states as sums. Each must be reproducible from claims —
    # 65,710,000 is sum(mortgage) for 2015-09-02, and it lives here rather than
    # as a claim precisely because claiming it alongside its two components
    # listed the same borrowing three times in the CAPITAL narrative.
    AGGREGATES = {97_871, 112_574, 12_404_940, 28_490_000, 265_490_000,
                  148_344_892, 1_309_388_157, 268_964, 156_390, 65_710_000}

    # ±1 tolerance: prose ROUNDS ($969,657) where int() TRUNCATES (969,656).
    # Same cent figure, two renderings — a difference of presentation, not of
    # fact, and reporting it as a gap would train everyone to ignore the report.
    def near(n, pool):
        return any(abs(n - m) <= 1 for m in pool)

    unbacked = sorted(n for n in prose_ints
                      if not near(n, claim_nums) and n >= 1000 and n not in AGGREGATES)
    unnarrated = sorted(n for n in claim_nums
                        if not near(n, prose_ints) and n >= 1000 and n not in AGGREGATES)
    return unbacked, unnarrated


def main():
    cl = rows()
    ids = [c["claim_id"] for c in cl]
    assert len(ids) == len(set(ids)), "duplicate claim_id"
    bad_pred = {c["predicate"] for c in cl} - set(PREDICATES)
    assert not bad_pred, f"predicate not in vocabulary: {bad_pred}"

    from collections import Counter as _C
    kc = _C(KIND[c["predicate"]] for c in cl)
    print("  by KIND: " + ", ".join(f"{k} {v}" for k, v in kc.most_common()))
    viol = validate_kinds(cl)
    if viol:
        print(f"\n  X {len(viol)} KIND VIOLATIONS — a value stored as the "
              f"wrong sort of thing:")
        for cid, k, why in viol:
            print(f"      {cid:<18} [{k}] {why}")
    else:
        print("  every claim matches its predicate's declared kind OK")
    for f, t, *_ in EDGES:
        assert f in ids and t in ids, f"edge references unknown claim: {f}->{t}"

    print(f"CLAIMS {len(cl)}  ·  EDGES {len(EDGES)}  ·  "
          f"predicates used {len({c['predicate'] for c in cl})}/{len(PREDICATES)}")
    from collections import Counter
    print("  by evidence: " + ", ".join(
        f"{k} {v}" for k, v in Counter(c["evidence"] for c in cl).most_common()))
    subj = Counter(c["subject_bbl"] for c in cl)
    print(f"  claims ABOUT another parcel: "
          f"{sum(v for k, v in subj.items() if k != L49)} across "
          f"{len([k for k in subj if k != L49])} lots — "
          "unfileable without subject_bbl")

    # the two time axes
    lag = [(c, (date.fromisoformat(c["stated"]) - date.fromisoformat(c["effective"])).days)
           for c in cl if c["effective"] and c["stated"] and c["stated"] != c["effective"]]
    lag.sort(key=lambda x: -x[1])
    print(f"\nTWO TIME AXES — {len(lag)} claims where the record learned of a fact "
          f"AFTER it happened:")
    for c, d in lag[:5]:
        print(f"  {d:>5} days  {c['effective']} -> {c['stated']}  "
              f"{c['claim_id']:<16} {c['predicate']}")

    print("\nCHRONOLOGY BY effective_date (first 6) — note what moves:")
    for line in render_narrative(cl)[:6]:
        print("  " + line)

    gaps = geometry_gaps(cl)
    print("\nGEOMETRY — claims whose predicate implies a region:")
    withg = [c for c in cl if c.get("region_scope")]
    print(f"  {len(withg)} carry a recorded region · {len(gaps)} do NOT")
    for c in withg:
        v = f"above {c['v_from']:g} ft" if c["v_from"] else "—"
        h = f"{c['h_extent']:g} ft band" if c["h_extent"] else c["region_scope"]
        print(f"    {c['claim_id']:<16} {c['region_scope']:<13} {v:<15} {h:<14}"
              f"{(c['v_datum'] or '')[:34]}")
    if gaps:
        print(f"  ⚠ MISSING GEOMETRY — recorded as a scalar, region unknown:")
        for c in gaps[:12]:
            print(f"    {c['claim_id']:<16} {c['predicate']:<19} "
                  f"{c['document_id']} {c['page'] or ''}")

    ub, un = diff_against_prose(cl)
    print(f"\n=== DIFF vs the hand-written ledger ===")
    print(f"  numbers asserted in prose with NO backing claim: {len(ub)}")
    for n in ub:
        print(f"     {n:>15,.0f}")
    print(f"  claims recorded but NOT narrated: {len(un)}")
    for n in un:
        print(f"     {n:>15,.0f}")

    for name, data in (("acris_claims", cl), ("acris_claim_edges",
        [dict(from_claim=a, to_claim=b, relation=r, basis=s, note=n)
         for a, b, r, s, n in EDGES])):
        p = HERE / f"{name}_{L49}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
        print(f"\n  wrote {p.name} ({len(data)} rows)")
    return cl


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL)
        sys.exit(0)
    main()
