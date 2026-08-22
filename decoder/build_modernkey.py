"""HAND-READ ANSWER KEY for 2015022400608001 - a 2015 DIGITAL-era HRA mortgage.

PARTIAL: 4 of 9 pages hand-read (p1 cover, p2 HRA sheet, p3 instrument, p9
affidavit). p4-p8 are not keyed and are excluded from scoring.

⚠ DIGITAL ERA MEANS A CLEAN SCAN, NOT TYPED CONTENT - and that assumption was
wrong in my head until I read this document. On the instrument and the affidavit
the date, borrower, address, the amount in WORDS and in FIGURES, the county and
the block/lot are ALL HANDWRITTEN. Only the boilerplate and the metes-and-bounds
are typed.

⚠ SO THE WORDS-vs-FIGURES CHECKSUM DOES NOT FIRE HERE. Both renderings of
$50,000 are handwriting. What rescues the digital era is the ACRIS COVER PAGE,
which restates every operative fact in clean type. The cover page is the
redundant witness, not the instrument.

⚠ AND THE TAX IS LEGITIMATELY ZERO. The City is exempt under 20 NYCRR 644.1(a),
exemption code 255, recording fee EXEMPT. A tax-reconciliation check would read
that as a failure when nothing is wrong.
"""
import collections
import json
import pathlib


def A(i, t, v, alts=None):
    return {"id": i, "tier": t, "value": v, "alts": alts or []}


K = collections.OrderedDict()
K["_doc"] = "2015022400608001"
K["_note"] = ("PARTIAL KEY - 4 of 9 pages hand-read. p4-p8 not keyed, excluded "
              "from scoring.")
K["_summary"] = (
    "MTGE recorded 2015-03-06, CRFN 2015000076576. $50,000 HRA public-assistance "
    "lien: DARLENE EPPS to NYC COMMISSIONER OF SOCIAL SERVICES. Queens BLOCK 10140 "
    "LOT 1112 UNIT 17C, 107-28 Guy R Brewer Blvd, single residential condo unit. "
    "Exempt from mortgage recording tax under 20 NYCRR 644.1(a).")

K["p001.png"] = {"kind": "ACRIS cover page - fully typed, the redundant witness", "artifacts": [
    A("agency", "ROUTINE", "DEPARTMENT OF FINANCE"),
    A("office", "ROUTINE", "OFFICE OF THE CITY REGISTER"),
    A("cover", "CRITICAL", "RECORDING AND ENDORSEMENT COVER PAGE"),
    A("doc_id", "CRITICAL", "2015022400608001"),
    A("doc_date", "CRITICAL", "11-18-2014"),
    A("prep_date", "ROUTINE", "02-24-2015"),
    A("doc_type", "CRITICAL", "MORTGAGE"),
    A("page_count", "MATERIAL", "Document Page Count"),
    A("presenter", "CRITICAL", "COMMISSIONER OF SOCIAL SERVICES"),
    A("presenter_addr", "CRITICAL", "250 CHURCH STREET"),
    A("presenter_zip", "MATERIAL", "10013"),
    A("phone", "MATERIAL", "929-252-2481"),
    A("email", "MATERIAL", "HRA.NYC.GOV"),
    A("borough", "CRITICAL", "QUEENS"),
    A("block", "CRITICAL", "10140"),
    A("lot", "CRITICAL", "1112"),
    A("unit", "CRITICAL", "17C"),
    A("entire_lot", "MATERIAL", "Entire Lot"),
    A("address", "CRITICAL", "GUY R BREWER"),
    A("prop_type", "CRITICAL", "RESIDENTIAL CONDO UNIT"),
    A("mortgagor_label", "MATERIAL", "MORTGAGOR"),
    A("mortgagor", "CRITICAL", "DARLENE EPPS"),
    A("mortgagor_city", "MATERIAL", "JAMAICA"),
    A("mortgagee_label", "MATERIAL", "MORTGAGEE"),
    A("mtg_amount", "CRITICAL", "50,000.00"),
    A("exemption", "CRITICAL", "255"),
    A("rec_fee", "CRITICAL", "EXEMPT"),
    A("recorded", "CRITICAL", "03-06-2015"),
    A("crfn", "CRITICAL", "2015000076576"),
    A("xref", "ROUTINE", "CROSS REFERENCE DATA"),
    A("fees", "ROUTINE", "FEES AND TAXES"),
    A("prop_data", "ROUTINE", "PROPERTY DATA")],
    "ambiguous": [
    {"id": "barcode", "note": "barcode glyph strip above the printed string"},
    {"id": "reg_sig", "note": "City Register signature, cursive"}]}

K["p002.png"] = {"kind": "HRA cover sheet - printed header, handwritten fills", "artifacts": [
    A("form_no", "MATERIAL", "LR-205k"),
    A("agency", "CRITICAL", "Human Resources Administration", ["HUMAN RESOURCES"]),
    A("bureau", "MATERIAL", "BUREAU OF ELIGIBILITY VERIFICATION"),
    A("admin", "MATERIAL", "ENFORCEMENT ADMINISTRATION"),
    A("unit", "MATERIAL", "REAL PROPERTY UNIT"),
    A("addr", "CRITICAL", "SCHERMERHORN"),
    A("city", "MATERIAL", "BROOKLYN"),
    A("zip", "MATERIAL", "11201"),
    A("title", "CRITICAL", "BOND AND MORTGAGE"),
    A("mortgagee", "CRITICAL", "Commissioner of Social Services"),
    A("district", "MATERIAL", "New York Social District"),
    A("return", "CRITICAL", "KINDLY RECORD AND RETURN TO"),
    A("return_unit", "MATERIAL", "Liens And Recovery"),
    A("return_addr", "MATERIAL", "250 Church St"),
    A("tax_map", "MATERIAL", "Tax Map of the County")],
    "ambiguous": [
    {"id": "hw_name", "note": "Darlene Epps handwritten across the top"},
    {"id": "hw_block", "note": "Block 10140 handwritten"},
    {"id": "hw_lot", "note": "Lot 1112 handwritten"},
    {"id": "hw_county", "note": "Queens handwritten"}]}

K["p003.png"] = {"kind": "instrument - printed boilerplate + metes, handwritten operative fields",
                 "artifacts": [
    A("title", "CRITICAL", "BOND AND MORTGAGE"),
    A("form_no", "MATERIAL", "LR-205k"),
    A("mortgagee", "CRITICAL", "Commissioner of Social Services"),
    A("mortgagee_addr", "CRITICAL", "180 Water Street"),
    A("ss_law", "CRITICAL", "Social Services Law"),
    A("witnesseth", "ROUTINE", "Witnesseth"),
    A("redeem", "MATERIAL", "expiration of one year"),
    A("begin", "CRITICAL", "BEGINNING at a point"),
    A("street", "CRITICAL", "Guy Brewer Boulevard"),
    A("avenue", "CRITICAL", "107th Avenue"),
    A("width70", "MATERIAL", "70 feet wide"),
    A("width60", "MATERIAL", "60 feet wide"),
    A("dist", "CRITICAL", "193.60"),
    A("dim1", "CRITICAL", "115.00"),
    A("dim2", "CRITICAL", "145.58"),
    A("note_block", "CRITICAL", "10140"),
    A("note_lot", "CRITICAL", "1112"),
    A("tax_map", "MATERIAL", "Borough of Queens"),
    A("page_of", "ROUTINE", "Page 2 of 5")],
    "ambiguous": [
    {"id": "hw_date", "note": "11-18 and 14 handwritten"},
    {"id": "hw_borrower", "note": "Darlene Epps handwritten"},
    {"id": "hw_addr", "note": "address handwritten across three lines"},
    {"id": "hw_amt_words", "note": "Fifty Thousand Dollars and 00/100 HANDWRITTEN"},
    {"id": "hw_amt_figs", "note": "50,000.00 HANDWRITTEN"},
    {"id": "hw_county", "note": "Queens / NY / NY handwritten"},
    {"id": "hw_desc", "note": "Single Residential Condo Unit handwritten"}]}

K["p009.png"] = {"kind": "tax exemption affidavit - printed form, handwritten fills",
                 "artifacts": [
    A("form_no", "MATERIAL", "W-2-548"),
    A("agency", "CRITICAL", "Human Resources Administration", ["HUMAN RESOURCES"]),
    A("title", "CRITICAL", "Tax Exemption Affidavit"),
    A("state", "ROUTINE", "STATE OF NEW YORK"),
    A("county", "MATERIAL", "COUNTY OF NEW YORK"),
    A("commissioner", "MATERIAL", "Steven Banks"),
    A("officer2", "MATERIAL", "Ghartey"),
    A("officer3", "MATERIAL", "Boodanian"),
    A("addr", "CRITICAL", "250 Church Street"),
    A("zip", "MATERIAL", "10013"),
    A("phone", "MATERIAL", "929 252 3020"),
    A("municipal", "MATERIAL", "Municipal Corporation"),
    A("oblige", "CRITICAL", "Department of Social Services"),
    A("reg_cite", "CRITICAL", "644.1", ["20 NYCRR SECTION 644.1"]),
    A("exempt", "CRITICAL", "Exempt from Paying"),
    A("wherefore", "ROUTINE", "WHEREFORE"),
    A("declared", "MATERIAL", "exempt from taxation"),
    A("notary", "CRITICAL", "DONNA A. HESS", ["DONNA A HESS"]),
    A("notary_no", "CRITICAL", "01HE6221160"),
    A("notary_county", "MATERIAL", "Qualified in New York County"),
    A("notary_exp", "MATERIAL", "April 26"),
    A("signature_lbl", "ROUTINE", "SIGNATURE"),
    A("affirmed", "ROUTINE", "Affirmed before me")],
    "ambiguous": [
    {"id": "hw_deponent", "note": "Aaron Stewart handwritten"},
    {"id": "hw_date_instr", "note": "11-18-14 handwritten"},
    {"id": "hw_obligor", "note": "Darlene Epps handwritten"},
    {"id": "hw_principal", "note": "50,000.00 handwritten"},
    {"id": "hw_premises", "note": "107-28 Guy R Brewer handwritten"},
    {"id": "hw_block_lot", "note": "Block 10140 Lot 1112 handwritten"},
    {"id": "hw_affirm_date", "note": "24th Day of February 2015 handwritten"},
    {"id": "sig", "note": "deponent and notary signatures cursive"}]}

p = pathlib.Path("answer_key_moderndoc.json")
p.write_text(json.dumps(K, indent=1, ensure_ascii=False), encoding="utf-8")
pages = [k for k in K if not k.startswith("_")]
na = sum(len(K[k]["artifacts"]) for k in pages)
nm = sum(len(K[k].get("ambiguous") or []) for k in pages)
tc = collections.Counter(a["tier"] for k in pages for a in K[k]["artifacts"])
print(f"  {p}")
print(f"  {len(pages)} pages | {na} artifacts | {nm} ambiguous excluded")
print(f"  {dict(tc)}")
