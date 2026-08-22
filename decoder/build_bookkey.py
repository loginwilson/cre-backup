"""HAND-READ ANSWER KEY for BK_6730047100023 - a 1967 BOOK-era FHA mortgage.

Read from the 1800px renders before any OCR touched the document, same rule as
the film key.

⚠ BOOK DOES NOT SAY 'REEL'. The stamp is `REC. 471 PAGE 23` - a record/liber
number, not a reel. Any decoder that hunts for the film-era phrasing will find
nothing on 1.7M book documents, which is 829k deeds and 539k mortgages of core
chain of title.

⚠ AND THE BLOCK AND LOT EXIST ONLY AS HANDWRITING on this document - margin
scrawl on p1 and `Sec 24 Blk 8110 Lot 30` sideways on the backer. Nothing typed
carries the parcel key. Every one of those is listed ambiguous, so no engine is
credited or penalised for them, but it means OCR alone cannot parcel-match this
mortgage at all.

Structure: 7 pages, 5 unique. REC. 471 pages 23,24,24,25,26,27,27.
"""
import collections
import json
import pathlib

def A(i, t, v, alts=None):
    return {"id": i, "tier": t, "value": v, "alts": alts or []}

K = collections.OrderedDict()
K["_doc"] = "BK_6730047100023"
K["_note"] = "HAND-READ from 1800px renders before any OCR ran."
K["_summary"] = (
    "MTGE recorded 1967-07-10, REC. 471 pages 23-27, Kings County. $21,000 FHA "
    "mortgage from MICHAEL and ROMULDA WINNICKI (738 Sheffield Ave, Brooklyn) to "
    "SPRINGFIELD EQUITIES LTD (88-22 161st St, Jamaica). Premises on the easterly "
    "side of East 92nd Street, 100 ft south of Avenue B, Brooklyn - a 100 x 20 lot "
    "sharing a party wall. Block 8110 Lot 30 Section 24, HANDWRITTEN ONLY. Loan "
    "4-19230, recording tax $105, title by American Title Insurance Co, mortgage "
    "assigned/held via Peninsula National Bank, Inwood NY. Purchase-money first "
    "mortgage recorded simultaneously with the deed.")
K["_structure"] = ("p1 first page+legal (pg23) | p2,p3 DUPLICATE rider (pg24, stamp "
                   "ROTATED 90) | p4 covenants 1-12 (pg25) | p5 covenants 13-20 (pg26) "
                   "| p6,p7 DUPLICATE backer (pg27, bottom half ROTATED 90)")
K["_match_checks"] = [
    "$21,000 x 0.5% = $105 -> equals the RECORDING TAX stamp on the backer",
    "metes and bounds CLOSES: E 100ft, S 20ft, W 100ft, N 20ft (a 100x20 rectangle)",
    "p1 margin scrawl 'LOT 30' = backer 'Lot 30'; both handwritten, neither typed",
    "acknowledged 1967-07-06 < recorded 1967-07-10 (JUL 10 1967 register stamp)",
    "map recorded=1967-07-10 -> backer stamp JUL-10-67",
]

K["p001.png"] = {"kind": "mortgage first page + legal description (REC 471 pg 23)", "artifacts": [
    A("rec_book", "CRITICAL", "REC. 471", ["REC 471", "471"]),
    A("rec_page", "CRITICAL", "23"),
    A("title", "CRITICAL", "MORTGAGE"),
    A("form_no", "MATERIAL", "FORM NO. 2159", ["2159"]),
    A("exec_date", "CRITICAL", "6th"),
    A("exec_month", "CRITICAL", "July"),
    A("year", "CRITICAL", "1967"),
    A("mortgagor1", "CRITICAL", "MICHAEL WINNICKI"),
    A("mortgagor2", "CRITICAL", "ROMULDA WINNICKI"),
    A("wife", "MATERIAL", "his wife"),
    A("mortgagor_addr", "CRITICAL", "738 Sheffield Avenue"),
    A("mortgagee", "CRITICAL", "SPRINGFIELD EQUITIES LTD", ["SPRINGFIELD EQUITIES"]),
    A("mortgagee_addr", "CRITICAL", "88-22", ["88-22 161st Street"]),
    A("mortgagee_st", "CRITICAL", "161st Street"),
    A("mortgagee_city", "MATERIAL", "Jamaica, New York"),
    A("amount_words", "CRITICAL", "TWENTY ONE THOUSAND", ["TWENTY ONE"]),
    A("amount_figs", "CRITICAL", "21,000.00", ["$21,000.00"]),
    A("borough", "CRITICAL", "Brooklyn"),
    A("county", "CRITICAL", "Kings"),
    A("begin", "CRITICAL", "BEGINNING at a point", ["BEGINNING"]),
    A("street", "CRITICAL", "East 92nd Street", ["92nd Street"]),
    A("avenue", "CRITICAL", "Avenue B"),
    A("dim_100", "CRITICAL", "100 feet"),
    A("dim_20", "CRITICAL", "20 feet"),
    A("party_wall", "CRITICAL", "party wall"),
    A("corp", "MATERIAL", "a corporation organized"),
    A("witnesseth", "ROUTINE", "WITNESSETH"),
    A("state_ny", "ROUTINE", "State of New York")],
    "ambiguous": [
    {"id": "hw_block", "note": "handwritten 'BL 8110' in margin, middle digits overwritten"},
    {"id": "hw_lot", "note": "handwritten 'LOT 30' in margin"},
    {"id": "hw_105", "note": "handwritten '105 od' margin scrawl"},
    {"id": "hw_initials", "note": "circled handwritten initials lower left, illegible"}]}

_rider = [
    A("rec_book", "CRITICAL", "REC. 471", ["REC 471", "471"]),
    A("rec_page", "CRITICAL", "24"),
    A("rider", "CRITICAL", "RIDER SHEET ATTACHED TO AND MADE PART OF MORTGAGE",
      ["RIDER SHEET"]),
    A("awards", "MATERIAL", "award and awards"),
    A("municipal", "MATERIAL", "Municipal or State authorities", ["Municipal"]),
    A("water_rates", "MATERIAL", "water rates"),
    A("sewer_rents", "MATERIAL", "sewer rents"),
    A("pmm", "CRITICAL", "purchase money first mortgage"),
    A("simul", "CRITICAL", "recorded simultaneously with the deed",
      ["simultaneously with the deed"]),
    A("bed_street", "MATERIAL", "land lying in the bed of the street",
      ["bed of the street"]),
    A("center_lines", "ROUTINE", "center lines thereof"),
    A("acquittances", "ROUTINE", "receipts and acquittances")]
_rider_amb = [{"id": "hw_initials", "note": "handwritten initials M.W. / R.W. at foot"}]

K["p002.png"] = {"kind": "RIDER SHEET (pg 24) - stamp ROTATED 90 on the right edge",
                 "artifacts": list(_rider), "ambiguous": list(_rider_amb)}
K["p003.png"] = {"kind": "RIDER SHEET duplicate of p002 (pg 24) - stamp ROTATED 90",
                 "artifacts": list(_rider), "ambiguous": list(_rider_amb)}

K["p004.png"] = {"kind": "FHA covenants 1-12 (pg 25), dense small print", "artifacts": [
    A("rec_book", "CRITICAL", "REC. 471", ["REC 471", "471"]),
    A("rec_page", "CRITICAL", "25"),
    A("covenants", "ROUTINE", "further covenants with the Mortgagee"),
    A("nha", "CRITICAL", "National Housing Act"),
    A("hud", "CRITICAL", "Housing and Urban Development"),
    A("one_twelfth", "MATERIAL", "one-twelfth (1/12)", ["one-twelfth"]),
    A("one_half", "MATERIAL", "one-half (1/2) per centum", ["per centum"]),
    A("ground_rents", "MATERIAL", "ground rents"),
    A("late_charge", "MATERIAL", "late charge"),
    A("two_cents", "MATERIAL", "two cents"),
    A("fifteen", "MATERIAL", "fifteen (15) days", ["fifteen 15 days"]),
    A("warrants", "CRITICAL", "warrants the title to the premises"),
    A("first_lien", "CRITICAL", "valid first lien on the premises", ["first lien"]),
    A("one_parcel", "MATERIAL", "sold in one parcel"),
    A("assign_rents", "CRITICAL", "will not assign the rents", ["assign the rents"]),
    A("lien_law", "CRITICAL", "Lien Law of the State of New York", ["Lien Law"]),
    A("amortization", "MATERIAL", "amortization of the principal"),
    A("ten_days", "ROUTINE", "ten (10) days", ["ten 10 days"]),
    A("twenty_days", "ROUTINE", "twenty (20) days", ["twenty 20 days"])],
    "ambiguous": []}

K["p005.png"] = {"kind": "FHA covenants 13-20 (pg 26), incl. the race-restriction clause",
                 "artifacts": [
    A("rec_book", "CRITICAL", "REC. 471", ["REC 471", "471"]),
    A("rec_page", "CRITICAL", "26"),
    A("insurance", "MATERIAL", "loss by fire and other hazards", ["loss by fire"]),
    A("loss_payable", "MATERIAL", "loss payable clauses"),
    A("ninety", "CRITICAL", "ninety days"),
    A("aforesaid", "MATERIAL", "aforesaid"),
    A("nha", "CRITICAL", "National Housing Act"),
    A("race_clause", "CRITICAL", "on the basis of race, color, or creed",
      ["race, color, or creed"]),
    A("attorneys", "MATERIAL", "attorneys' fees", ["attorneys fees"]),
    A("thirty", "MATERIAL", "thirty (30) days", ["thirty 30 days"]),
    A("surrender", "MATERIAL", "surrender possession"),
    A("dispossess", "MATERIAL", "usual summary proceedings"),
    A("receiver", "CRITICAL", "appointment of a receiver"),
    A("foreclose", "MATERIAL", "action to foreclose"),
    A("eligibility", "CRITICAL", "not be eligible for insurance",
      ["eligible for insurance"]),
    A("feminine", "ROUTINE", "feminine gender")],
    "ambiguous": []}

_backer = [
    A("rec_book", "CRITICAL", "REC. 471", ["REC 471", "471"]),
    A("rec_page", "CRITICAL", "27"),
    A("witness", "ROUTINE", "IN WITNESS WHEREOF"),
    A("signer1", "CRITICAL", "MICHAEL WINNICKI"),
    A("signer2", "CRITICAL", "ROMULDA WINNICKI"),
    A("presence", "ROUTINE", "In presence of"),
    A("state", "ROUTINE", "STATE OF NEW YORK"),
    A("county_ack", "CRITICAL", "COUNTY OF NASSAU", ["NASSAU"]),
    A("ack_day", "CRITICAL", "6th"),
    A("ack_month", "CRITICAL", "July"),
    A("ack_year", "CRITICAL", "sixty seven"),
    A("notary", "CRITICAL", "SIDERMAN", ["DAVID S. SIDERMAN"]),
    A("notary_county", "MATERIAL", "Qualified in Nassau County", ["Nassau County"]),
    A("notary_exp", "MATERIAL", "March 30, 1969"),
    # --- everything below is in the ROTATED backer block ---
    A("serial", "MATERIAL", "24495"),
    A("loan_no", "CRITICAL", "4-19230", ["4 - 19230", "19230"]),
    A("instrument", "CRITICAL", "Mortgage"),
    A("to_party", "CRITICAL", "SPRINGFIELD EQUITIES LTD", ["SPRINGFIELD EQUITIES"]),
    A("rec_tax", "CRITICAL", "RECORDING TAX"),
    A("bank", "CRITICAL", "Peninsula National Bank", ["Peninsula National"]),
    A("bank_addr", "MATERIAL", "165 Sheridan Boulevard", ["Sheridan Boulevard"]),
    A("bank_city", "MATERIAL", "Inwood, New York", ["Inwood"]),
    A("title_co", "CRITICAL", "AMERICAN TITLE INSURANCE", ["AMERICAN TITLE"]),
    A("title_div", "MATERIAL", "GUARANTEED TITLE DIVISION", ["GUARANTEED TITLE"]),
    A("rec_date", "CRITICAL", "JUL 10 1967", ["JUL-10-67", "JUL 10"]),
    A("register", "CRITICAL", "OFFICE OF CITY REGISTER", ["CITY REGISTER"]),
    A("register_co", "CRITICAL", "Kings County"),
    A("recorded", "ROUTINE", "RECORDED"),
    A("seal", "ROUTINE", "Witness my hand and official seal", ["official seal"]),
    A("nha_form", "MATERIAL", "National Housing Act"),
    A("sections", "MATERIAL", "Sections 203 and 222", ["203 and 222"]),
    A("loc_ver", "ROUTINE", "LOC. VER.", ["LOC VER"])]
_backer_amb = [
    {"id": "hw_sec_blk_lot", "note": "handwritten sideways 'Sec 24 / Blk 8110 / Lot 30' - the ONLY parcel key in the document and it is handwriting"},
    {"id": "hw_rec_tax_amt", "note": "handwritten '$105' over the RECORDING TAX stamp"},
    {"id": "hw_serial_no", "note": "SERIAL NO. handwritten, overprinted"},
    {"id": "sig_mortgagors", "note": "both mortgagor signatures cursive"},
    {"id": "sig_witness", "note": "witness signature cursive, illegible"},
    {"id": "sig_register", "note": "City Register signature cursive, illegible"},
    {"id": "hw_rr", "note": "'R & R' sideways annotation, meaning unclear"}]

K["p006.png"] = {"kind": "backer + acknowledgement (pg 27) - bottom half ROTATED 90",
                 "artifacts": list(_backer), "ambiguous": list(_backer_amb)}
K["p007.png"] = {"kind": "backer duplicate of p006 (pg 27) - bottom half ROTATED 90",
                 "artifacts": list(_backer), "ambiguous": list(_backer_amb)}

p = pathlib.Path("answer_key_bookdoc.json")
p.write_text(json.dumps(K, indent=1, ensure_ascii=False), encoding="utf-8")
pages = [k for k in K if not k.startswith("_")]
na = sum(len(K[k]["artifacts"]) for k in pages)
nm = sum(len(K[k].get("ambiguous") or []) for k in pages)
tc = collections.Counter(a["tier"] for k in pages for a in K[k]["artifacts"])
print(f"  {p}")
print(f"  {len(pages)} pages | {na} artifacts | {nm} ambiguous excluded")
print(f"  {dict(tc)}\n")
for k in pages:
    c = collections.Counter(a["tier"] for a in K[k]["artifacts"])
    print(f"    {k}  {len(K[k]['artifacts']):>3} art "
          f"({c['CRITICAL']}C/{c['MATERIAL']}M/{c['ROUTINE']}R)  "
          f"{len(K[k].get('ambiguous') or []):>2} amb")
